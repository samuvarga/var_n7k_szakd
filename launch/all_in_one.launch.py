import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _get_package_share_or_none(package_name):
    try:
        return get_package_share_directory(package_name)
    except Exception:
        return None


def _launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory('var_n7k_szakd')
    nav2_bringup_dir = _get_package_share_or_none('nav2_bringup')

    actions = []

    if nav2_bringup_dir is None:
        actions.append(
            LogInfo(
                msg=(
                    'nav2_bringup is not installed, so this launch starts '
                    'the roboworks simulation only.'
                )
            )
        )
    else:
        slam_mapping = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_share, 'launch_slam_mapping.launch.py')
            ),
            launch_arguments={
                'world_name': LaunchConfiguration('world_name'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'autostart': LaunchConfiguration('autostart'),
                'params_file': LaunchConfiguration('params_file'),
            }.items(),
        )
        actions.append(slam_mapping)
    return actions


def generate_launch_description():
    nav2_bringup_dir = _get_package_share_or_none('nav2_bringup')
    pkg_share = get_package_share_directory('var_n7k_szakd')
    default_slam_params = os.path.join(pkg_share, 'config', 'slam_toolbox_params.yaml')

    declare_world_name_cmd = DeclareLaunchArgument(
        'world_name',
        default_value='roboworks_world',
        description='Gazebo world name used by the robot spawn launch',
    )
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='Use simulation clock',
    )
    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='True',
        description='Automatically start Nav2 nodes',
    )
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=default_slam_params,
        description='SLAM Toolbox parameter file used for mapping',
    )
    return LaunchDescription([
        declare_world_name_cmd,
        declare_use_sim_time_cmd,
        declare_autostart_cmd,
        declare_params_file_cmd,
        OpaqueFunction(function=_launch_setup),
    ])
