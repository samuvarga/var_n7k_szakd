#!/usr/bin/env python3
"""
DWB Command Velocity Smoother Node
===================================
Applies exponential moving average smoothing to DWB output cmd_vel commands.
This reduces oscillation and provides smooth steering transitions.

Based on Simple Pursuit smoothing principle:
  smoothed_value = alpha * previous + (1-alpha) * current
  
Default alpha = 0.5 (50% weight to previous)
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class CmdVelSmoother(Node):
    def __init__(self):
        super().__init__('cmd_vel_smoother')
        
        # Declare and get smoothing factor parameter
        self.declare_parameter('smoothing_factor', 0.5)
        self.smoothing_factor = self.get_parameter('smoothing_factor').get_parameter_value().double_value
        
        # Subscribers and publishers
        self.subscription = self.create_subscription(
            Twist, 
            'input_cmd_vel', 
            self.cmd_vel_callback, 
            qos_profile=rclpy.qos.QoSProfile(depth=1)
        )
        
        self.publisher = self.create_publisher(
            Twist, 
            'output_cmd_vel', 
            qos_profile=rclpy.qos.QoSProfile(depth=1)
        )
        
        # Smoothed state variables
        self.smooth_linear_x = 0.0
        self.smooth_linear_y = 0.0
        self.smooth_linear_z = 0.0
        self.smooth_angular_x = 0.0
        self.smooth_angular_y = 0.0
        self.smooth_angular_z = 0.0
        
        self.get_logger().info(
            f"CmdVelSmoother initialized with smoothing_factor={self.smoothing_factor}"
        )
        self.get_logger().info(
            f"  Subscribing to: 'input_cmd_vel'\n"
            f"  Publishing to: 'output_cmd_vel'\n"
            f"  Formula: smoothed = {self.smoothing_factor} * prev + {1.0-self.smoothing_factor} * current"
        )
    
    def cmd_vel_callback(self, msg: Twist):
        """
        Apply exponential moving average smoothing to cmd_vel.
        
        Smoothing formula (EMA):
          smoothed(t) = alpha * smoothed(t-1) + (1-alpha) * current(t)
          
        With alpha=0.5:
          smoothed(t) = 0.5 * smoothed(t-1) + 0.5 * current(t)
        """
        k = self.smoothing_factor
        
        # Apply smoothing to linear velocities
        self.smooth_linear_x = k * self.smooth_linear_x + (1.0 - k) * msg.linear.x
        self.smooth_linear_y = k * self.smooth_linear_y + (1.0 - k) * msg.linear.y
        self.smooth_linear_z = k * self.smooth_linear_z + (1.0 - k) * msg.linear.z
        
        # Apply smoothing to angular velocities
        self.smooth_angular_x = k * self.smooth_angular_x + (1.0 - k) * msg.angular.x
        self.smooth_angular_y = k * self.smooth_angular_y + (1.0 - k) * msg.angular.y
        self.smooth_angular_z = k * self.smooth_angular_z + (1.0 - k) * msg.angular.z
        
        # Create and publish smoothed message
        smoothed_msg = Twist()
        smoothed_msg.linear.x = self.smooth_linear_x
        smoothed_msg.linear.y = self.smooth_linear_y
        smoothed_msg.linear.z = self.smooth_linear_z
        smoothed_msg.angular.x = self.smooth_angular_x
        smoothed_msg.angular.y = self.smooth_angular_y
        smoothed_msg.angular.z = self.smooth_angular_z
        
        self.publisher.publish(smoothed_msg)


def main(args=None):
    rclpy.init(args=args)
    smoother = CmdVelSmoother()
    try:
        rclpy.spin(smoother)
    except KeyboardInterrupt:
        pass
    finally:
        smoother.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
