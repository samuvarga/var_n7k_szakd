"""Measure relative odometry drift against Gazebo ground truth."""

import math
import threading
import time
from collections import deque

import rclpy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_msgs.msg import TFMessage


def yaw_from_quaternion(quaternion):
    return math.atan2(
        2.0 * (quaternion.w * quaternion.z + quaternion.x * quaternion.y),
        1.0 - 2.0 * (quaternion.y * quaternion.y + quaternion.z * quaternion.z),
    )


def angle_delta(first, second):
    return math.atan2(math.sin(first - second), math.cos(first - second))


def pose_from_message(message):
    pose_field = message.pose
    pose = pose_field.pose if hasattr(pose_field, 'pose') else pose_field
    return (
        pose.position.x,
        pose.position.y,
        yaw_from_quaternion(pose.orientation),
    )


class InteractiveDriftMonitor(Node):
    """Report relative pose errors after each RViz initial pose."""

    def __init__(self):
        super().__init__('interactive_drift_monitor')
        self.lock = threading.Lock()
        self.latest = {
            'raw': None,
            'filtered': None,
            'amcl': None,
            'gt': None,
            'map_odom': None,
        }
        self.samples = {
            name: deque(maxlen=200)
            for name in ('raw', 'filtered', 'amcl', 'gt')
        }
        self.declare_parameter('ground_truth_model', 'roboworks')
        self.declare_parameter('ground_truth_transform_index', 0)
        self.declare_parameter('ground_truth_sync_tolerance', 0.15)
        self.ground_truth_model = self.get_parameter('ground_truth_model').value
        self.ground_truth_transform_index = self.get_parameter(
            'ground_truth_transform_index'
        ).value
        self.ground_truth_sync_tolerance = self.get_parameter(
            'ground_truth_sync_tolerance'
        ).value
        self.last_ground_truth_warning = 0.0
        self.anchor = None
        self.awaiting_initial_pose = False
        self.last_gt_wall = time.monotonic()
        self.received_gt = False
        self.measurement_started_wall = None
        self.last_report_wall = 0.0
        self.last_path_poses = None
        self.path = {'gt': 0.0, 'raw': 0.0, 'filtered': 0.0, 'amcl': 0.0}
        self.stats = {
            name: {
                'max_error': 0.0,
                'final_error': 0.0,
                'max_yaw': 0.0,
                'samples': 0,
            }
            for name in ('raw', 'filtered', 'amcl')
        }
        self.goal_count = 0

        self.create_subscription(Odometry, '/odom', self.raw_callback, 20)
        self.create_subscription(
            Odometry,
            '/odometry/filtered',
            self.filtered_callback,
            20,
        )
        self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self.amcl_callback,
            20,
        )
        self.create_subscription(
            TFMessage,
            '/world/roboworks_world/dynamic_pose/info',
            self.ground_truth_callback,
            20,
        )
        self.create_subscription(TFMessage, '/tf', self.tf_callback, 50)
        self.create_subscription(
            PoseWithCovarianceStamped,
            '/initialpose',
            self.initial_pose_callback,
            10,
        )
        self.create_subscription(PoseStamped, '/goal_pose', self.goal_callback, 10)
        threading.Thread(target=self.watchdog_loop, daemon=True).start()

        print('DRIFT MONITOR: varakozas a 2D Pose Estimate-re...', flush=True)
        print(
            'DRIFT MONITOR: a meres az initial pose utan indul, '
            'a Gazebo leallasa lezárja.',
            flush=True,
        )

    def raw_callback(self, message):
        self.set_pose('raw', message)

    def filtered_callback(self, message):
        self.set_pose('filtered', message)

    def amcl_callback(self, message):
        self.set_pose('amcl', message)

    def set_pose(self, name, message):
        pose = pose_from_message(message)
        with self.lock:
            self.latest[name] = pose
            sample_time = time.monotonic()
            self.samples[name].append((sample_time, pose))
            self.try_arm_locked(sample_time)

    def ground_truth_callback(self, message):
        transform = self._find_ground_truth_transform(message)
        if transform is None:
            return

        quaternion = transform.transform.rotation
        pose = (
            transform.transform.translation.x,
            transform.transform.translation.y,
            yaw_from_quaternion(quaternion),
        )
        with self.lock:
            self.latest['gt'] = pose
            sample_time = time.monotonic()
            self.samples['gt'].append((sample_time, pose))
            self.last_gt_wall = time.monotonic()
            self.received_gt = True
            self.try_arm_locked(sample_time)
            if self.anchor is None:
                return

            synchronized = self._synchronized_poses_locked(sample_time)
            if synchronized is None:
                return
            self.update_path_locked(synchronized)
            self.update_stats_locked(synchronized)
            now = time.monotonic()
            if now - self.last_report_wall >= 3.0:
                self.report_locked(now)
                self.last_report_wall = now

    def _find_ground_truth_transform(self, message):
        index = int(self.ground_truth_transform_index)
        if 0 <= index < len(message.transforms):
            return message.transforms[index]

        now = time.monotonic()
        if now - self.last_ground_truth_warning >= 5.0:
            self.get_logger().warning(
                'Ground truth transform index %d is unavailable in dynamic_pose/info'
                % index
            )
            self.last_ground_truth_warning = now
        return None

    def _synchronized_poses_locked(self, stamp):
        synchronized = {'gt': self.latest['gt']}
        for name in ('raw', 'filtered', 'amcl'):
            if not self.samples[name]:
                return None
            closest_stamp, closest_pose = min(
                self.samples[name],
                key=lambda sample: abs(sample[0] - stamp),
            )
            if abs(closest_stamp - stamp) > self.ground_truth_sync_tolerance:
                return None
            synchronized[name] = closest_pose
        return synchronized

    def tf_callback(self, message):
        with self.lock:
            for transform in message.transforms:
                if (
                    transform.header.frame_id.lstrip('/') == 'map'
                    and transform.child_frame_id.lstrip('/') == 'odom'
                ):
                    quaternion = transform.transform.rotation
                    self.latest['map_odom'] = (
                        transform.transform.translation.x,
                        transform.transform.translation.y,
                        yaw_from_quaternion(quaternion),
                    )
                    return

    def initial_pose_callback(self, _message):
        with self.lock:
            self.awaiting_initial_pose = True
            self.anchor = None
            self.last_path_poses = None
            for name in self.samples:
                self.samples[name].clear()
                self.latest[name] = None
            self.path = {name: 0.0 for name in self.path}
            for values in self.stats.values():
                values.update(max_error=0.0, final_error=0.0, max_yaw=0.0, samples=0)
            print(
                'DRIFT MONITOR: 2D Pose Estimate erkezett, '
                'gyujtom a kezdo mintakat...',
                flush=True,
            )
            self.try_arm_locked(time.monotonic())

    def goal_callback(self, message):
        with self.lock:
            self.goal_count += 1
            goal_yaw = yaw_from_quaternion(message.pose.orientation)
            print(
                'DRIFT MONITOR: 2D Goal #%d: x=%.3f y=%.3f yaw=%.1f deg'
                % (
                    self.goal_count,
                    message.pose.position.x,
                    message.pose.position.y,
                    math.degrees(goal_yaw),
                ),
                flush=True,
            )

    def try_arm_locked(self, stamp):
        required = ('gt', 'raw', 'filtered', 'amcl')
        if not self.awaiting_initial_pose:
            return
        synchronized = self._synchronized_poses_locked(stamp)
        if synchronized is None:
            return

        self.anchor = synchronized
        self.anchor['map_odom'] = self.latest['map_odom']
        self.last_path_poses = synchronized.copy()
        self.awaiting_initial_pose = False
        self.measurement_started_wall = time.monotonic()
        print(
            'DRIFT MONITOR: MERES ELINDULT. '
            'A relativ hibat 3 masodpercenkent irom.',
            flush=True,
        )

    def update_path_locked(self, current_poses):
        for name in self.path:
            current = current_poses.get(name)
            previous = self.last_path_poses[name]
            if current is None or previous is None:
                continue
            self.path[name] += math.hypot(
                current[0] - previous[0], current[1] - previous[1]
            )
            self.last_path_poses[name] = current

    def update_stats_locked(self, current_poses):
        ground_truth = current_poses['gt']
        ground_truth_anchor = self.anchor['gt']
        ground_truth_relative = (
            ground_truth[0] - ground_truth_anchor[0],
            ground_truth[1] - ground_truth_anchor[1],
            angle_delta(ground_truth[2], ground_truth_anchor[2]),
        )
        for name, values in self.stats.items():
            current = current_poses[name]
            current_anchor = self.anchor[name]
            current_relative = (
                current[0] - current_anchor[0],
                current[1] - current_anchor[1],
                angle_delta(current[2], current_anchor[2]),
            )
            error = math.hypot(
                current_relative[0] - ground_truth_relative[0],
                current_relative[1] - ground_truth_relative[1],
            )
            yaw_error = abs(
                math.degrees(
                    angle_delta(current_relative[2], ground_truth_relative[2])
                )
            )
            values['max_error'] = max(values['max_error'], error)
            values['final_error'] = error
            values['max_yaw'] = max(values['max_yaw'], yaw_error)
            values['samples'] += 1

    def report_locked(self, now):
        elapsed = now - self.measurement_started_wall
        line = 'DRIFT t=%6.1fs goals=%d' % (elapsed, self.goal_count)
        for name, label in (
            ('raw', 'raw'),
            ('filtered', 'ekf'),
            ('amcl', 'amcl'),
        ):
            values = self.stats[name]
            line += ' | %s=%.3fm max=%.3fm yaw=%.2fdeg' % (
                label,
                values['final_error'],
                values['max_error'],
                values['max_yaw'],
            )
        if self.latest['map_odom'] and self.anchor['map_odom']:
            current = self.latest['map_odom']
            initial = self.anchor['map_odom']
            line += ' | map->odom shift=%.3fm' % math.hypot(
                current[0] - initial[0], current[1] - initial[1]
            )
        print(line, flush=True)

    def watchdog_loop(self):
        while rclpy.ok():
            if self.received_gt and time.monotonic() - self.last_gt_wall > 5.0:
                print(
                    'DRIFT MONITOR: 5 masodperce nincs ground truth; '
                    'a teszt veget ert.',
                    flush=True,
                )
                rclpy.shutdown()
                return
            time.sleep(1.0)

    def print_summary(self):
        with self.lock:
            print('\n===== DRIFT MERES OSSZEGZES =====', flush=True)
            if self.anchor is None:
                print('Nem erkezett 2D Pose Estimate, nincs meres.', flush=True)
                return
            for name, label in (
                ('raw', 'nyers odom'),
                ('filtered', 'EKF odom'),
                ('amcl', 'AMCL'),
            ):
                values = self.stats[name]
                print(
                    '%s: vegso %.4f m, maximum %.4f m, max yaw %.3f deg, '
                    'mintak %d'
                    % (
                        label,
                        values['final_error'],
                        values['max_error'],
                        values['max_yaw'],
                        values['samples'],
                    ),
                    flush=True,
                )
            print(
                'ut-hossz: ground truth %.4f m | nyers %.4f m | EKF %.4f m | AMCL %.4f m'
                % (
                    self.path['gt'],
                    self.path['raw'],
                    self.path['filtered'],
                    self.path['amcl'],
                ),
                flush=True,
            )
            print('elkuldott 2D Goal-ok: %d' % self.goal_count, flush=True)
            print('=================================', flush=True)


def main():
    rclpy.init()
    node = InteractiveDriftMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.print_summary()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()