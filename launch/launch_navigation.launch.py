import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _require_map(context):
    if not LaunchConfiguration('map').perform(context):
        return [Shutdown(reason='Navigation requires map:=/absolute/path/to/map.yaml')]
    return []


def generate_launch_description():
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
        default_value=os.path.join(pkg_share, 'config', 'nav2_params.yaml'),
        description='Nav2 parameter file for localization and navigation',
    )

    declare_map_cmd = DeclareLaunchArgument(
        'map',
        default_value='',
        description=(
            'Map YAML used for localization. Pass an exported SLAM map with '
            'map:=/absolute/path/to/map.yaml.'
        ),
    )

    declare_world_name_cmd = DeclareLaunchArgument(
        'world_name',
        default_value='roboworks_world',
        description='Gazebo world name used by the robot spawn launch',
    )

    declare_world_file_cmd = DeclareLaunchArgument(
        'world_file',
        default_value='roboworks_world.sdf',
        description='World SDF filename installed in the package world directory',
    )

    roboworks_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'roboworks_sim.launch.py')
        ),
        launch_arguments={
            'world_name': LaunchConfiguration('world_name'),
            'world_file': LaunchConfiguration('world_file'),
        }.items(),
    )

    rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch_rviz.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'start_delay': '0.0',
        }.items(),
    )

    bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'nav2_navigation.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': LaunchConfiguration('params_file'),
            'autostart': LaunchConfiguration('autostart'),
        }.items(),
    )

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'nav2_localization_nodes.launch.py')
        ),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': LaunchConfiguration('params_file'),
            'map': LaunchConfiguration('map'),
            'autostart': LaunchConfiguration('autostart'),
        }.items(),
    )

    return LaunchDescription([
        declare_use_sim_time_cmd,
        declare_autostart_cmd,
        declare_params_file_cmd,
        declare_map_cmd,
        declare_world_name_cmd,
        declare_world_file_cmd,
        OpaqueFunction(function=_require_map),
        roboworks_sim,
        localization,
        bringup,
        rviz,
    ])
