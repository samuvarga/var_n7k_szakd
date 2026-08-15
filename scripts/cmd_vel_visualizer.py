#!/usr/bin/env python3
"""
CMD_VEL Visualizer for RViz
============================
Visualizes both raw DWB output and smoothed commands in RViz.
- Raw (DWB output): RED arrows
- Smoothed output: GREEN arrows

Shows steering angle and velocity magnitude as arrows from the robot.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from visualization_msgs.msg import MarkerArray, Marker
from geometry_msgs.msg import Point, Quaternion
import math


class CmdVelVisualizer(Node):
    def __init__(self):
        super().__init__('cmd_vel_visualizer')
        
        # Subscribers
        self.sub_raw = self.create_subscription(
            Twist,
            'input_raw_cmd_vel',  # /cmd_vel
            self.callback_raw,
            qos_profile=rclpy.qos.QoSProfile(depth=1)
        )
        
        self.sub_smooth = self.create_subscription(
            Twist,
            'input_smooth_cmd_vel',  # /model/roboworks/cmd_vel_smooth
            self.callback_smooth,
            qos_profile=rclpy.qos.QoSProfile(depth=1)
        )
        
        # Publisher
        self.marker_pub = self.create_publisher(
            MarkerArray,
            'cmd_vel_visualization',
            qos_profile=rclpy.qos.QoSProfile(depth=1)
        )
        
        # Storage for latest values
        self.raw_twist = Twist()
        self.smooth_twist = Twist()
        
        self.get_logger().info(
            "CmdVelVisualizer initialized\n"
            "  Subscribing to: 'input_raw_cmd_vel' (DWB output - RED)\n"
            "                  'input_smooth_cmd_vel' (Smoothed - GREEN)\n"
            "  Publishing to: 'cmd_vel_visualization' (RViz MarkerArray)"
        )
    
    def callback_raw(self, msg: Twist):
        """Store raw DWB output"""
        self.raw_twist = msg
        self.publish_markers()
    
    def callback_smooth(self, msg: Twist):
        """Store smoothed output"""
        self.smooth_twist = msg
        self.publish_markers()
    
    def publish_markers(self):
        """Create and publish markers for both raw and smoothed commands"""
        markers = MarkerArray()
        
        # Raw DWB output - RED
        raw_marker = self.create_arrow_marker(
            twist=self.raw_twist,
            marker_id=0,
            color=(1.0, 0.0, 0.0, 0.8),  # Red
            label="RAW (DWB)",
            offset_x=0.0,
            offset_y=0.15
        )
        markers.markers.append(raw_marker)
        
        # Smoothed output - GREEN
        smooth_marker = self.create_arrow_marker(
            twist=self.smooth_twist,
            marker_id=1,
            color=(0.0, 1.0, 0.0, 0.8),  # Green
            label="SMOOTH",
            offset_x=0.0,
            offset_y=-0.15
        )
        markers.markers.append(smooth_marker)
        
        # Text labels
        text_marker = self.create_text_marker(
            marker_id=2,
            raw_twist=self.raw_twist,
            smooth_twist=self.smooth_twist
        )
        markers.markers.append(text_marker)
        
        self.marker_pub.publish(markers)
    
    def create_arrow_marker(self, twist, marker_id, color, label, offset_x, offset_y):
        """
        Create an arrow marker representing cmd_vel command.
        
        Arrow direction = steering angle (angular.z)
        Arrow length = linear velocity (linear.x)
        """
        marker = Marker()
        marker.header.frame_id = "base_link"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.id = marker_id
        marker.type = Marker.ARROW
        marker.action = Marker.MODIFY
        
        # Position with offset (to separate raw and smooth arrows)
        marker.pose.position.x = offset_x
        marker.pose.position.y = offset_y
        marker.pose.position.z = 0.2
        
        # Rotation based on steering angle (angular.z)
        steering_angle = twist.angular.z
        # Convert steering angle to quaternion rotation around Z axis
        q_w = math.cos(steering_angle / 2.0)
        q_z = math.sin(steering_angle / 2.0)
        marker.pose.orientation.w = q_w
        marker.pose.orientation.z = q_z
        
        # Scale: length = linear velocity, width/height = fixed
        velocity = twist.linear.x
        arrow_length = abs(velocity) * 0.5 if abs(velocity) > 0.01 else 0.1
        marker.scale.x = arrow_length  # Length
        marker.scale.y = 0.1            # Width
        marker.scale.z = 0.1            # Height
        
        # Color
        marker.color.r = color[0]
        marker.color.g = color[1]
        marker.color.b = color[2]
        marker.color.a = color[3]
        
        # Text label
        marker.text = label
        
        # Lifetime
        marker.lifetime.sec = 1
        
        return marker
    
    def create_text_marker(self, marker_id, raw_twist, smooth_twist):
        """Create a text marker showing values"""
        marker = Marker()
        marker.header.frame_id = "base_link"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.id = marker_id
        marker.type = Marker.TEXT_VIEW_FACING
        marker.action = Marker.MODIFY
        
        marker.pose.position.x = 0.0
        marker.pose.position.y = 0.0
        marker.pose.position.z = 0.5
        marker.pose.orientation.w = 1.0
        
        # Text content
        marker.text = (
            f"RAW   | v:{raw_twist.linear.x:.2f} ω:{raw_twist.angular.z:.2f}\n"
            f"SMOOTH| v:{smooth_twist.linear.x:.2f} ω:{smooth_twist.angular.z:.2f}"
        )
        
        marker.scale.z = 0.15  # Text size
        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        marker.color.a = 1.0
        
        marker.lifetime.sec = 1
        
        return marker


def main(args=None):
    rclpy.init(args=args)
    visualizer = CmdVelVisualizer()
    try:
        rclpy.spin(visualizer)
    except KeyboardInterrupt:
        pass
    finally:
        visualizer.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
