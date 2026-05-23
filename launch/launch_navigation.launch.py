import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    bringup_dir = get_package_share_directory('nav2_bringup')
    pkg_share = get_package_share_directory('var_n7k_szakd')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='Use simulation clock',
    )

    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='True',
        description='Automatically start the Nav2 stack',
    )

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(bringup_dir, 'params', 'nav2_params.yaml'),
        description='Nav2 parameter file for localization and navigation',
    )

    declare_map_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(bringup_dir, 'maps', 'tb3_sandbox.yaml'),
        description='Map file used for localization and navigation',
    )

    declare_world_name_cmd = DeclareLaunchArgument(
        'world_name',
        default_value='roboworks_world',
        description='Gazebo world name used by the robot spawn launch',
    )

    roboworks_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'roboworks_sim.launch.py')
        ),
        launch_arguments={
            'world_name': LaunchConfiguration('world_name'),
        }.items(),
    )

    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'slam': 'False',
            'map': LaunchConfiguration('map'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': LaunchConfiguration('params_file'),
            'autostart': LaunchConfiguration('autostart'),
            'use_composition': 'False',
            'use_intra_process_comms': 'False',
            'use_respawn': 'False',
        }.items(),
    )

    return LaunchDescription([
        declare_use_sim_time_cmd,
        declare_autostart_cmd,
        declare_params_file_cmd,
        declare_map_cmd,
        declare_world_name_cmd,
        roboworks_sim,
        bringup,
    ])
