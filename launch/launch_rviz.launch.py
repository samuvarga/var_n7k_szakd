import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('var_n7k_szakd')
    default_rviz_config = os.path.join(pkg_share, 'rviz', 'roboworks_lidar.rviz')

    rviz_config = LaunchConfiguration('rviz_config')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='Use simulation clock in RViz',
    )

    declare_rviz_config_cmd = DeclareLaunchArgument(
        'rviz_config',
        default_value=default_rviz_config,
        description='Full path to rviz config file to use',
    )

    declare_start_delay_cmd = DeclareLaunchArgument(
        'start_delay',
        default_value='25.0',
        description='Delay before starting RViz in seconds',
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
    )

    return LaunchDescription([
        declare_use_sim_time_cmd,
        declare_rviz_config_cmd,
        declare_start_delay_cmd,
        rviz,
    ])