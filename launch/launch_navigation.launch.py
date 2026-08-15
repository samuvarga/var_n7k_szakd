import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, Shutdown, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml


def _require_map(context):
    if not LaunchConfiguration('map').perform(context):
        return [Shutdown(reason='Navigation requires map:=/absolute/path/to/map.yaml')]
    return []


def generate_launch_description():
    package_share = get_package_share_directory('var_n7k_szakd')
    nav2_share = get_package_share_directory('nav2_bringup')

    use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='True', description='Use simulation clock')
    autostart = DeclareLaunchArgument(
        'autostart', default_value='True', description='Automatically start Nav2')
    params_file = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(package_share, 'config', 'nav2_params.yaml'),
        description='Nav2 parameter file')
    map_file = DeclareLaunchArgument(
        'map', default_value='', description='Absolute path to a saved map YAML')
    world_name = DeclareLaunchArgument(
        'world_name', default_value='roboworks_world', description='Gazebo world name')
    world_file = DeclareLaunchArgument(
        'world_file', default_value='roboworks_world.sdf', description='World SDF filename')

    # Configured params for Nav2 (used by costmap servers)
    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=LaunchConfiguration('params_file'),
            root_key='',
            param_rewrites={},
            convert_types=True,
        ),
        allow_substs=True,
    )

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_share, 'launch', 'roboworks_sim.launch.py')),
        launch_arguments={
            'world_name': LaunchConfiguration('world_name'),
            'world_file': LaunchConfiguration('world_file'),
        }.items(),
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_share, 'launch', 'navigation_no_collision.launch.py')),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'params_file': LaunchConfiguration('params_file'),
            'autostart': LaunchConfiguration('autostart'),
            'use_composition': 'False',
        }.items(),
    )

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_share, 'launch', 'localization_launch.py')),
        launch_arguments={
            'map': LaunchConfiguration('map'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': LaunchConfiguration('autostart'),
            'params_file': LaunchConfiguration('params_file'),
            'use_composition': 'False',
            'use_respawn': 'False',
            'container_name': 'nav2_localization_container',
        }.items(),
    )

    # Global Costmap Server - publishes /global_costmap/costmap for RViz inflation aura
    # Must be in the 'global_costmap' namespace to match nav2_params.yaml structure
    global_costmap = GroupAction(
        actions=[
            PushRosNamespace('global_costmap'),
            Node(
                package='nav2_costmap_2d',
                executable='nav2_costmap_2d',
                name='global_costmap',
                output='screen',
                parameters=[configured_params],
                remappings=[
                    ('tf', 'tf'),
                    ('tf_static', 'tf_static'),
                ]
            ),
        ]
    )

    # Local Costmap Server - publishes /local_costmap/costmap for RViz
    # Must be in the 'local_costmap' namespace to match nav2_params.yaml structure
    local_costmap = GroupAction(
        actions=[
            PushRosNamespace('local_costmap'),
            Node(
                package='nav2_costmap_2d',
                executable='nav2_costmap_2d',
                name='local_costmap',
                output='screen',
                parameters=[configured_params],
                remappings=[
                    ('tf', 'tf'),
                    ('tf_static', 'tf_static'),
                ]
            ),
        ]
    )

    rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_share, 'launch', 'launch_rviz.launch.py')),
        launch_arguments={'use_sim_time': LaunchConfiguration('use_sim_time')}.items()
    )

    # CMD_VEL Smoother Node
    # Applies exponential moving average smoothing to DWB output
    # to reduce oscillation and smooth steering transitions
    # Subscribes to /cmd_vel (DWB raw)
    # Publishes to /cmd_vel_smoothed (smoothed for Gazebo bridge)
    cmd_vel_smoother = Node(
        package='var_n7k_szakd',
        executable='ros2_cmd_vel_smoother',
        name='cmd_vel_smoother',
        parameters=[{'smoothing_factor': 0.15}],
    )

    # CMD_VEL Visualizer Node
    # Visualizes raw (RED) and smoothed (GREEN) commands in RViz
    # Shows arrows for steering angle and velocity magnitude
    # Subscribes to /cmd_vel (raw) and /cmd_vel_smoothed (smoothed)
    # Publishes to /cmd_vel_markers (RViz MarkerArray)
    cmd_vel_visualizer = Node(
        package='var_n7k_szakd',
        executable='cmd_vel_visualizer',
        name='cmd_vel_visualizer',
    )

    return LaunchDescription([
        use_sim_time,
        autostart,
        params_file,
        map_file,
        world_name,
        world_file,
        OpaqueFunction(function=_require_map),
        simulation,
        localization,
        global_costmap,
        local_costmap,
        navigation,
        cmd_vel_smoother,
        cmd_vel_visualizer,
        rviz,
    ])
