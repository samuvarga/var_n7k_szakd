from typing import Optional

import rclpy
from builtin_interfaces.msg import Time
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


def _stamp_from_msg(msg: Odometry) -> Time:
    if msg.header.stamp.sec != 0 or msg.header.stamp.nanosec != 0:
        return msg.header.stamp
    return Time(sec=0, nanosec=0)


def _ensure_monotonic_stamp(stamp: Time, last_stamp: Optional[Time]) -> Time:
    if last_stamp is None:
        return stamp

    if (stamp.sec, stamp.nanosec) < (last_stamp.sec, last_stamp.nanosec):
        return Time(sec=last_stamp.sec, nanosec=last_stamp.nanosec)
    return stamp


def _build_transform(msg: Odometry, parent_frame: str, child_frame: str) -> TransformStamped:
    transform = TransformStamped()
    transform.header.stamp = _stamp_from_msg(msg)
    transform.header.frame_id = parent_frame
    transform.child_frame_id = child_frame
    transform.transform.translation.x = msg.pose.pose.position.x
    transform.transform.translation.y = msg.pose.pose.position.y
    transform.transform.translation.z = msg.pose.pose.position.z
    transform.transform.rotation = msg.pose.pose.orientation
    return transform


class OdomTfBroadcaster(Node):
    def __init__(self):
        super().__init__('odom_tf_broadcaster')
        self.declare_parameter('odom_topic', '/model/roboworks/odometry')
        self.declare_parameter('parent_frame', 'odom')
        self.declare_parameter('child_frame', 'base_footprint')

        odom_topic = self.get_parameter('odom_topic').value
        self.parent_frame = self.get_parameter('parent_frame').value
        self.child_frame = self.get_parameter('child_frame').value

        self.tf_broadcaster = TransformBroadcaster(self)
        self.subscription = self.create_subscription(
            Odometry,
            odom_topic,
            self.odom_callback,
            10,
        )
        self._last_publish_time: Optional[Time] = None

    def _next_stamp(self) -> Time:
        stamp = self.get_clock().now().to_msg()
        stamp = _ensure_monotonic_stamp(stamp, self._last_publish_time)
        self._last_publish_time = stamp
        return stamp

    def odom_callback(self, msg: Odometry) -> None:
        transform = _build_transform(msg, self.parent_frame, self.child_frame)
        if transform.header.stamp.sec == 0 and transform.header.stamp.nanosec == 0:
            transform.header.stamp = self._next_stamp()
        else:
            transform.header.stamp = _ensure_monotonic_stamp(
                transform.header.stamp, self._last_publish_time)
            self._last_publish_time = transform.header.stamp
        self.tf_broadcaster.sendTransform(transform)


def main(args=None):
    rclpy.init(args=args)
    node = OdomTfBroadcaster()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
