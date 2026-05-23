import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_share = get_package_share_directory('var_n7k_szakd')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    declare_world_name_cmd = DeclareLaunchArgument(
        'world_name',
        default_value='wheeltec_world',
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
        default_value=os.path.join(nav2_bringup_dir, 'params', 'nav2_params.yaml'),
        description='Nav2 parameter file',
    )
    declare_map_cmd = DeclareLaunchArgument(
        'map',
        default_value=''
,
        description='Map yaml file for localization mode',
    )
    declare_use_rviz_cmd = DeclareLaunchArgument(
        'use_rviz',
        default_value='True',
        description='Open RViz',
    )
    declare_use_localization_cmd = DeclareLaunchArgument(
        'use_localization',
        default_value='True',
        description='Enable localization/navigation stack',
    )
    declare_graph_cmd = DeclareLaunchArgument(
        'graph',
        default_value='',
        description='Route graph file used by Nav2 route server',
    )

    wheeltec_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'wheeltec_sim.launch.py')
        ),
        launch_arguments={
            'world_name': LaunchConfiguration('world_name'),
        }.items(),
    )

    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'namespace': '',
            'slam': 'True',
            'map': LaunchConfiguration('map'),
            'keepout_mask': '',
            'speed_mask': '',
            'graph': LaunchConfiguration('graph'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': LaunchConfiguration('params_file'),
            'autostart': LaunchConfiguration('autostart'),
            'use_composition': 'False',
            'use_intra_process_comms': 'False',
            'use_respawn': 'False',
            'use_localization': LaunchConfiguration('use_localization'),
            'use_keepout_zones': 'False',
            'use_speed_zones': 'False',
        }.items(),
    )

    rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'rviz_launch.py')
        ),
        condition=IfCondition(LaunchConfiguration('use_rviz')),
        launch_arguments={
            'namespace': '',
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'rviz_config': os.path.join(nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz'),
        }.items(),
    )

    return LaunchDescription([
        declare_world_name_cmd,
        declare_use_sim_time_cmd,
        declare_autostart_cmd,
        declare_params_file_cmd,
        declare_map_cmd,
        declare_use_rviz_cmd,
        declare_use_localization_cmd,
        declare_graph_cmd,
        wheeltec_sim,
        nav2_bringup,
        rviz,
    ])
