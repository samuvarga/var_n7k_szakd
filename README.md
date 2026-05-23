# `var_n7k_szakd` package
ROS 2 python package.  [![Static Badge](https://img.shields.io/badge/ROS_2-Humble-34aec5)](https://docs.ros.org/en/humble/)
## Packages and build

It is assumed that the workspace is `~/ros2_ws/`.

### Clone the packages
``` r
cd ~/ros2_ws/src
```
``` r
git clone https://github.com/samuvarga/var_n7k_szakd
```

### Build ROS 2 packages
``` r
cd ~/ros2_ws
```
``` r
colcon build --packages-select var_n7k_szakd --symlink-install && . install/setup.bash
```

<details>
<summary> Don't forget to source before ROS commands.</summary>

``` bash
source ~/ros2_ws/install/setup.bash
```
</details>

### Run Gazebo only
``` r
ros2 launch var_n7k_szakd launch_gazebo.launch.py
```

### Run the roboworks world with the robot
``` r
ros2 launch var_n7k_szakd roboworks_sim.launch.py
```

### Run everything from one launch file
``` r
ros2 launch var_n7k_szakd all_in_one.launch.py
```

### Run RViz with the lidar display
``` r
ros2 launch var_n7k_szakd launch_rviz.launch.py
```

### Run SLAM mapping with slam_toolbox
``` r
ros2 launch var_n7k_szakd launch_slam_mapping.launch.py
```

### Run navigation on a saved map
``` r
ros2 launch var_n7k_szakd launch_navigation.launch.py map:=/full/path/to/map.yaml
```

The SLAM launch uses `slam_toolbox` through `nav2_bringup`'s `slam_launch.py`.
The navigation launch uses `nav2_bringup`'s `bringup_launch.py`.
The `all_in_one.launch.py` file starts the roboworks-based simulation, spawns the robot, bridges the expected `tf`, `joint_states`, `odom`, `cmd_vel`, `scan`, and `clock` topics, and launches the Nav2 stack.
