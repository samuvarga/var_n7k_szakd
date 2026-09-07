#!/usr/bin/env python3
"""Publish the rolling local costmap boundary for RViz."""

from geometry_msgs.msg import Point
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from visualization_msgs.msg import Marker


class LocalCostmapBoundaryVisualizer(Node):
    """Draw the local costmap window around the filtered odometry pose."""

    def __init__(self):
        super().__init__('local_costmap_boundary_visualizer')

        self.declare_parameter('width', 6.0)
        self.declare_parameter('height', 6.0)
        self.declare_parameter('frame_id', 'odom')
        self.declare_parameter('odom_topic', '/odometry/filtered')
        self.declare_parameter('publish_rate', 10.0)

        self.width = self.get_parameter('width').value
        self.height = self.get_parameter('height').value
        self.frame_id = self.get_parameter('frame_id').value
        odom_topic = self.get_parameter('odom_topic').value
        publish_rate = self.get_parameter('publish_rate').value

        self.robot_x = None
        self.robot_y = None
        self.marker_publisher = self.create_publisher(
            Marker, '/local_costmap/bounds', 10)
        self.odom_subscription = self.create_subscription(
            Odometry, odom_topic, self.odom_callback, 10)
        self.timer = self.create_timer(1.0 / publish_rate, self.publish_boundary)

    def odom_callback(self, message):
        """Store the current robot position in the odometry frame."""
        self.robot_x = message.pose.pose.position.x
        self.robot_y = message.pose.pose.position.y

    def publish_boundary(self):
        """Publish a rectangle centered on the current robot position."""
        if self.robot_x is None or self.robot_y is None:
            return

        half_width = self.width / 2.0
        half_height = self.height / 2.0
        marker = Marker()
        marker.header.frame_id = self.frame_id
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'local_costmap'
        marker.id = 0
        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.08
        marker.color.r = 1.0
        marker.color.g = 0.85
        marker.color.b = 0.0
        marker.color.a = 0.95

        corners = (
            (-half_width, -half_height),
            (half_width, -half_height),
            (half_width, half_height),
            (-half_width, half_height),
            (-half_width, -half_height),
        )
        for offset_x, offset_y in corners:
            point = Point()
            point.x = self.robot_x + offset_x
            point.y = self.robot_y + offset_y
            point.z = 0.25
            marker.points.append(point)

        self.marker_publisher.publish(marker)


def main(args=None):
    rclpy.init(args=args)
    visualizer = LocalCostmapBoundaryVisualizer()
    try:
        rclpy.spin(visualizer)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        visualizer.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
