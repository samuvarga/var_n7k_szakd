# `var_n7k_szakd`

WheeltEc `roboworks` Ackermann robot szimulációja ROS 2 Jazzy és Gazebo Sim
Harmonic környezetben. A csomag külön indítási lehetőséget biztosít a
szimulációhoz, a SLAM térképezéshez és a mentett térképes navigációhoz.

## Magyar útmutató

### Követelmények

- Ubuntu 24.04 / WSL 2
- ROS 2 Jazzy
- Gazebo Sim 8 (Harmonic)
- Python 3

A munkakönyvtár:

```bash
cd /mnt/c/Users/samuv/ros2_ws
```

Minden új terminálban töltsd be a környezetet:

```bash
source /opt/ros/jazzy/setup.bash
source /mnt/c/Users/samuv/ros2_ws/install/setup.bash
```

### Build

```bash
cd /mnt/c/Users/samuv/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select var_n7k_szakd --symlink-install
source install/setup.bash
```

### Csak a Gazebo indítása

Ez csak a Gazebo Sim világot indítja el, robot nélkül:

```bash
ros2 launch var_n7k_szakd launch_gazebo.launch.py
```

### A robot és a szimuláció indítása

Alapértelmezett világ:

```bash
ros2 launch var_n7k_szakd roboworks_sim.launch.py
```

City pálya:

```bash
ros2 launch var_n7k_szakd roboworks_sim.launch.py \
	world_file:=roboworks_city_world.sdf
```

Maze pálya:

```bash
ros2 launch var_n7k_szakd roboworks_sim.launch.py \
	world_file:=roboworks_maze_world.sdf
```

Ez a launch elindítja a Gazebo Simet, a robotot, a bridge-eket, az
odometriát és a szükséges TF-eket.

### SLAM térképezés

Ne indítsd el előtte külön a `roboworks_sim.launch.py` fájlt. A SLAM launch
már maga indítja a szimulációt, a robotot, a SLAM Toolboxot és az RViz2-t.

Alapértelmezett világ:

```bash
ros2 launch var_n7k_szakd launch_slam_mapping.launch.py
```

City pálya:

```bash
ros2 launch var_n7k_szakd launch_slam_mapping.launch.py \
	world_file:=roboworks_city_world.sdf
```

Maze pálya:

```bash
ros2 launch var_n7k_szakd launch_slam_mapping.launch.py \
	world_file:=roboworks_maze_world.sdf
```

### Kézi robotirányítás

Új terminálban töltsd be a ROS környezetet, majd indítsd a teleop csomagot:

```bash
source /opt/ros/jazzy/setup.bash
source /mnt/c/Users/samuv/ros2_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
	--ros-args -r cmd_vel:=/model/roboworks/cmd_vel
```

Fontos billentyűk:

```text
i       előre
,       hátra
j       balra
l       jobbra
k       megállás
q/z     maximális sebesség növelése/csökkentése
w/x     lineáris sebesség növelése/csökkentése
e/c     szögsebesség növelése/csökkentése
```

Teleop nélkül kézi parancs is küldhető:

```bash
ros2 topic pub --rate 10 /model/roboworks/cmd_vel \
	geometry_msgs/msg/Twist \
	"{linear: {x: 0.2}, angular: {z: 0.0}}"
```

A kézi parancs leállítása: `Ctrl+C`.

### Térkép mentése

SLAM után a térkép mentése:

```bash
ros2 run nav2_map_server map_saver_cli -f /home/$USER/roboworks_map
```

City pálya térképe:

```bash
ros2 run nav2_map_server map_saver_cli -f /home/$USER/roboworks_city_map
```

Maze pálya térképe:

```bash
ros2 run nav2_map_server map_saver_cli -f /home/$USER/roboworks_maze_map
```

A mentés két fájlt hoz létre, például:

```text
/home/$USER/roboworks_city_map.yaml
/home/$USER/roboworks_city_map.pgm
```

### Navigáció mentett térképpel

A navigációhoz mindig add meg a világban elkészített megfelelő térképet.

Alapértelmezett világ:

```bash
ros2 launch var_n7k_szakd launch_navigation.launch.py \
	map:=/home/$USER/roboworks_map.yaml
```

City pálya:

```bash
ros2 launch var_n7k_szakd launch_navigation.launch.py \
	world_file:=roboworks_city_world.sdf \
	map:=/home/$USER/roboworks_city_map.yaml
```

Maze pálya:

```bash
ros2 launch var_n7k_szakd launch_navigation.launch.py \
	world_file:=roboworks_maze_world.sdf \
	map:=/home/$USER/roboworks_maze_map.yaml
```

Navigáció indítása után az RViz-ben:

1. Válaszd a `2D Pose Estimate` eszközt.
2. Add meg a robot kezdeti helyét és irányát.
3. Küldj célt a `Nav2 Goal` eszközzel.

### Folyamatok leállítása

Normál esetben minden launch terminálban `Ctrl+C` elegendő. Beragadt
folyamatok esetén:

```bash
pkill -9 -f 'gz sim|parameter_bridge|robot_state_publisher|odom_tf_broadcaster|static_transform_publisher|slam_toolbox|rviz2|amcl|lifecycle_manager|controller_server|planner_server|map_server|bt_navigator|collision_monitor' 2>/dev/null || true
```
## English guide

### Requirements

- Ubuntu 24.04 / WSL 2
- ROS 2 Jazzy
- Gazebo Sim 8 (Harmonic)
- Python 3

Workspace:

```bash
cd /mnt/c/Users/samuv/ros2_ws
```

Source the environment in every new terminal:

```bash
source /opt/ros/jazzy/setup.bash
source /mnt/c/Users/samuv/ros2_ws/install/setup.bash
```

### Build

```bash
cd /mnt/c/Users/samuv/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select var_n7k_szakd --symlink-install
source install/setup.bash
```

### Start Gazebo only

This starts Gazebo Sim without the robot:

```bash
ros2 launch var_n7k_szakd launch_gazebo.launch.py
```

### Start the robot simulation

Default world:

```bash
ros2 launch var_n7k_szakd roboworks_sim.launch.py
```

City world:

```bash
ros2 launch var_n7k_szakd roboworks_sim.launch.py \
	world_file:=roboworks_city_world.sdf
```

Maze world:

```bash
ros2 launch var_n7k_szakd roboworks_sim.launch.py \
	world_file:=roboworks_maze_world.sdf
```

This launch starts Gazebo Sim, the robot, the bridges, odometry and the
required TF publishers.

### SLAM mapping

Do not start `roboworks_sim.launch.py` separately. The SLAM launch already
starts the simulation, robot, SLAM Toolbox and RViz2.

Default world:

```bash
ros2 launch var_n7k_szakd launch_slam_mapping.launch.py
```

City world:

```bash
ros2 launch var_n7k_szakd launch_slam_mapping.launch.py \
	world_file:=roboworks_city_world.sdf
```

Maze world:

```bash
ros2 launch var_n7k_szakd launch_slam_mapping.launch.py \
	world_file:=roboworks_maze_world.sdf
```

### Manual control

In a new terminal, source ROS and start the teleoperation node:

```bash
source /opt/ros/jazzy/setup.bash
source /mnt/c/Users/samuv/ros2_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
	--ros-args -r cmd_vel:=/model/roboworks/cmd_vel
```

Important keys:

```text
i       forward
,       reverse
j       turn left
l       turn right
k       stop
q/z     increase/decrease maximum speed
w/x     increase/decrease linear speed
e/c     increase/decrease angular speed
```

The teleoperation command can also be sent manually:

```bash
ros2 topic pub --rate 10 /model/roboworks/cmd_vel \
	geometry_msgs/msg/Twist \
	"{linear: {x: 0.2}, angular: {z: 0.0}}"
```

Stop the manual command with `Ctrl+C`.

### Save a map

After SLAM mapping:

```bash
ros2 run nav2_map_server map_saver_cli -f /home/$USER/roboworks_map
```

City map:

```bash
ros2 run nav2_map_server map_saver_cli -f /home/$USER/roboworks_city_map
```

Maze map:

```bash
ros2 run nav2_map_server map_saver_cli -f /home/$USER/roboworks_maze_map
```

Each command creates a YAML map file and a PGM image, for example:

```text
/home/$USER/roboworks_city_map.yaml
/home/$USER/roboworks_city_map.pgm
```

### Navigation with a saved map

Always use a map created in the same world as the selected `world_file`.

Default world:

```bash
ros2 launch var_n7k_szakd launch_navigation.launch.py \
	map:=/home/$USER/roboworks_map.yaml
```

City world:

```bash
ros2 launch var_n7k_szakd launch_navigation.launch.py \
	world_file:=roboworks_city_world.sdf \
	map:=/home/$USER/roboworks_city_map.yaml
```

Maze world:

```bash
ros2 launch var_n7k_szakd launch_navigation.launch.py \
	world_file:=roboworks_maze_world.sdf \
	map:=/home/$USER/roboworks_maze_map.yaml
```

After starting navigation in RViz2:

1. Select `2D Pose Estimate`.
2. Set the robot's initial position and orientation.
3. Send a goal with `Nav2 Goal`.

### Stop running processes

Normally, press `Ctrl+C` in each launch terminal. If processes remain:

```bash
pkill -9 -f 'gz sim|parameter_bridge|robot_state_publisher|odom_tf_broadcaster|static_transform_publisher|slam_toolbox|rviz2|amcl|lifecycle_manager|controller_server|planner_server|map_server|bt_navigator|collision_monitor' 2>/dev/null || true
```

