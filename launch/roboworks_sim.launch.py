import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('var_n7k_szakd')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world_file = PathJoinSubstitution([
        pkg_share,
        'world',
        LaunchConfiguration('world_file'),
    ])
    robot_sdf = os.path.join(pkg_share, 'robot_description', 'roboworks', 'model.sdf')
    robot_urdf = os.path.join(pkg_share, 'robot_description', 'roboworks', 'model.urdf')

    declare_world_name_cmd = DeclareLaunchArgument(
        'world_name',
        default_value='roboworks_world',
        description='Gazebo world name used by ros_gz_sim create',
    )

    declare_world_file_cmd = DeclareLaunchArgument(
        'world_file',
        default_value='roboworks_world.sdf',
        description='World SDF filename installed in the package world directory',
    )

    declare_robot_name_cmd = DeclareLaunchArgument(
        'robot_name',
        default_value='roboworks',
        description='Entity name of the robot in Gazebo',
    )

    declare_x_cmd = DeclareLaunchArgument('x', default_value='0.0')
    declare_y_cmd = DeclareLaunchArgument('y', default_value='0.0')
    declare_z_cmd = DeclareLaunchArgument('z', default_value='0.12')
    declare_roll_cmd = DeclareLaunchArgument('R', default_value='0.0')
    declare_pitch_cmd = DeclareLaunchArgument('P', default_value='0.0')
    declare_yaw_cmd = DeclareLaunchArgument('Y', default_value='0.0')

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': ['-r -v 4 ', world_file],
        }.items(),
    )

    # prefer URDF if available (RViz/robot_state_publisher expects URDF), fall back to SDF
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'robot_description': open(robot_urdf, 'r', encoding='utf-8').read() if os.path.exists(robot_urdf) else open(robot_sdf, 'r', encoding='utf-8').read()},
        ],
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        parameters=[{
            'world': LaunchConfiguration('world_name'),
            'file': robot_sdf,
            'name': LaunchConfiguration('robot_name'),
            'x': LaunchConfiguration('x'),
            'y': LaunchConfiguration('y'),
            'z': LaunchConfiguration('z'),
            'R': LaunchConfiguration('R'),
            'P': LaunchConfiguration('P'),
            'Y': LaunchConfiguration('Y'),
        }],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='roboworks_bridge',
        output='screen',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            '/model/roboworks/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/model/roboworks/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/world/roboworks_world/model/roboworks/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        remappings=[
            ('/world/roboworks_world/model/roboworks/joint_state', 'joint_states'),
        ],
    )

    odom_tf_broadcaster = Node(
        package='var_n7k_szakd',
        executable='odom_tf_broadcaster',
        name='odom_tf_broadcaster',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'odom_topic': '/model/roboworks/odometry'},
            {'parent_frame': 'odom'},
            {'child_frame': 'base_footprint'},
        ],
    )

    base_footprint_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_footprint_tf',
        output='screen',
        arguments=['0', '0', '0', '0', '0', '0', 'base_footprint', 'base_link'],
        parameters=[{'use_sim_time': True}],
    )

    base_link_lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_lidar_tf',
        output='screen',
        arguments=[
            '0.25', '0', '0.094', '0', '0', '0',
            'base_link',
            'lidar_link',
        ],
        parameters=[{'use_sim_time': True}],
    )

    lidar_sensor_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='lidar_sensor_tf',
        output='screen',
        arguments=[
            '0', '0', '0', '0', '0', '0',
            'lidar_link',
            'roboworks/lidar_link/gpu_lidar',
        ],
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        declare_world_name_cmd,
        declare_world_file_cmd,
        declare_robot_name_cmd,
        declare_x_cmd,
        declare_y_cmd,
        declare_z_cmd,
        declare_roll_cmd,
        declare_pitch_cmd,
        declare_yaw_cmd,
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
        odom_tf_broadcaster,
        base_footprint_tf,
        base_link_lidar_tf,
        lidar_sensor_tf,
    ])