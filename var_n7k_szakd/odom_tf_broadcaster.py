import rclpy
from builtin_interfaces.msg import Time
from copy import deepcopy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


def _stamp_from_msg(msg: Odometry) -> Time:
    if msg.header.stamp.sec != 0 or msg.header.stamp.nanosec != 0:
        return msg.header.stamp
    return Time(sec=0, nanosec=0)


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
        self.declare_parameter('output_odom_topic', '/odom')
        self.declare_parameter('parent_frame', 'odom')
        self.declare_parameter('child_frame', 'base_link')
        self.declare_parameter('publish_tf', True)

        odom_topic = self.get_parameter('odom_topic').value
        output_odom_topic = self.get_parameter('output_odom_topic').value
        self.parent_frame = self.get_parameter('parent_frame').value
        self.child_frame = self.get_parameter('child_frame').value
        self.publish_tf = self.get_parameter('publish_tf').value

        self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_publisher = self.create_publisher(Odometry, output_odom_topic, 10)
        self.subscription = self.create_subscription(
            Odometry,
            odom_topic,
            self.odom_callback,
            10,
        )

    def odom_callback(self, msg: Odometry) -> None:
        normalized_msg = deepcopy(msg)
        normalized_msg.header.frame_id = self.parent_frame
        normalized_msg.child_frame_id = self.child_frame
        self.odom_publisher.publish(normalized_msg)

        if self.publish_tf:
            transform = _build_transform(msg, self.parent_frame, self.child_frame)
            self.tf_broadcaster.sendTransform(transform)


def main(args=None):
    rclpy.init(args=args)
    node = OdomTfBroadcaster()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
