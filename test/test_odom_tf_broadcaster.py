import unittest

from builtin_interfaces.msg import Time
from geometry_msgs.msg import Point, Pose, PoseWithCovariance, Quaternion, TransformStamped
from nav_msgs.msg import Odometry

from var_n7k_szakd.odom_tf_broadcaster import _build_transform, _ensure_monotonic_stamp


class OdomTfBroadcasterTest(unittest.TestCase):
    def test_build_transform_uses_odometry_header_stamp(self) -> None:
        odom_msg = Odometry()
        odom_msg.header.stamp = Time(sec=42, nanosec=123456789)
        odom_msg.pose.pose = Pose(
            position=Point(x=1.0, y=2.0, z=0.0),
            orientation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
        )
        odom_msg.pose = PoseWithCovariance(pose=odom_msg.pose.pose)

        transform = _build_transform(odom_msg, 'odom', 'base_footprint')

        self.assertEqual(transform.header.frame_id, 'odom')
        self.assertEqual(transform.child_frame_id, 'base_footprint')
        self.assertEqual(transform.header.stamp.sec, 42)
        self.assertEqual(transform.header.stamp.nanosec, 123456789)
        self.assertEqual(transform.transform.translation.x, 1.0)
        self.assertEqual(transform.transform.translation.y, 2.0)
        self.assertEqual(transform.transform.translation.z, 0.0)

    def test_ensure_monotonic_stamp_clamps_backwards_time(self) -> None:
        last_stamp = Time(sec=10, nanosec=0)
        incoming_stamp = Time(sec=9, nanosec=500000000)

        clamped_stamp = _ensure_monotonic_stamp(incoming_stamp, last_stamp)

        self.assertEqual(clamped_stamp.sec, 10)
        self.assertEqual(clamped_stamp.nanosec, 0)


if __name__ == '__main__':
    unittest.main()
