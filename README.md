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

### Odom drift mérés Open Worldon

A mérő a Gazebo ground truth pozíciójához hasonlítja a nyers odometriát és az
EKF által szűrt odometriát. Az eredmény időbélyeges CSV-fájl, amely közvetlenül
felhasználható diagram készítéséhez.

Az összehasonlítható méréshez mindig friss szimulációt indíts, és használd az
Open Worldot:

```bash
world_file:=roboworks_open_world.sdf
```

A pálya két szakaszból áll:

- 0–10 s: előrehaladás nagy ívű bal kanyarban, `linear.x=0.2`,
  `angular.z=0.15`
- 10–20 s: előrehaladás kisebb ívű jobb kanyarban, `linear.x=0.2`,
  `angular.z=-0.45`

Ez a 10. másodpercnél irányváltást hoz létre, ezért a mérés jól mutatja,
hogyan reagál a nyers és az EKF-es odometria a megváltozott kanyarodásra.

Először építsd újra a csomagot:

```bash
cd /mnt/c/Users/samuv/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select var_n7k_szakd --symlink-install
source install/setup.bash
```

#### EKF nélkül

1. Terminál 1-ben indítsd az Open World szimulációt raw odom TF-fel:

   ```bash
   ros2 launch var_n7k_szakd roboworks_sim.launch.py \
     world_file:=roboworks_open_world.sdf \
     publish_odom_tf:=True
   ```

2. Terminál 2-ben indítsd a loggert:

   ```bash
   ros2 run var_n7k_szakd interactive_drift_monitor --ros-args \
     -p measure_filtered:=False \
     -p measure_amcl:=False \
     -p duration:=20.0 \
     -p output_csv:=/tmp/odom_drift_open_world_20s_no_ekf.csv
   ```

3. Terminál 3-ban küldd el a kezdőpozíciót, majd indítsd a két egymás utáni
   10 másodperces vezérlési szakaszt:

   ```bash
   ros2 topic pub --once /initialpose \
     geometry_msgs/msg/PoseWithCovarianceStamped \
     "{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}"
   sleep 1
   timeout 10s ros2 topic pub --rate 10 /model/roboworks/cmd_vel \
     geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.15}}"
   timeout 10s ros2 topic pub --rate 10 /model/roboworks/cmd_vel \
     geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: -0.45}}"
   ```

#### EKF-fel

1. Állítsd le az előző szimulációt, majd Terminál 1-ben indíts friss Open
   World szimulációt raw odom TF nélkül:

   ```bash
   ros2 launch var_n7k_szakd roboworks_sim.launch.py \
     world_file:=roboworks_open_world.sdf \
     publish_odom_tf:=False
   ```

2. Terminál 2-ben indítsd az EKF-et:

   ```bash
   ros2 run robot_localization ekf_node --ros-args \
     -p use_sim_time:=True \
     --params-file /mnt/c/Users/samuv/ros2_ws/src/var_n7k_szakd/config/ekf.yaml
   ```

3. Terminál 3-ban indítsd a 20 másodperces loggert:

   ```bash
   ros2 run var_n7k_szakd interactive_drift_monitor --ros-args \
     -p measure_filtered:=True \
     -p measure_amcl:=False \
     -p duration:=20.0 \
     -p output_csv:=/tmp/odom_drift_open_world_20s_ekf.csv
   ```

4. Terminál 4-ben küldd el ugyanazt a kezdőpozíciót és ugyanazt a két
   vezérlési szakaszt:

   ```bash
   ros2 topic pub --once /initialpose \
     geometry_msgs/msg/PoseWithCovarianceStamped \
     "{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}"
   sleep 1
   timeout 10s ros2 topic pub --rate 10 /model/roboworks/cmd_vel \
     geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.15}}"
   timeout 10s ros2 topic pub --rate 10 /model/roboworks/cmd_vel \
     geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: -0.45}}"
   ```

A logger automatikusan leáll 20 másodperc után. A CSV oszlopai:

- `time_s`: eltelt idő másodpercben
- `raw_drift_m`: nyers odom helyzetdriftje méterben
- `filtered_drift_m`: EKF-es helyzetdrift méterben
- `raw_drift_yaw_deg` és `filtered_drift_yaw_deg`: irányhiba fokban

Az EKF nélküli mérés fájlja csak a `raw_*` oszlopokat tartalmazza. A két
méréshez használt CSV-k:

```text
/tmp/odom_drift_open_world_20s_no_ekf.csv
/tmp/odom_drift_open_world_20s_ekf.csv
```

A mérés során kapott példaértékek:

| Idő | EKF nélkül | EKF-fel |
|---:|---:|---:|
| 0 s | 0,000 m | 0,000 m |
| 6 s | 0,000 m | 0,000 m |
| 9 s | 0,0156 m | 0,0004 m |
| 10 s | 0,0234 m | 0,0040 m |
| 15 s | 0,0499 m | 0,0121 m |
| 18 s | 0,0797 m | 0,0117 m |
| 20 s | 0,2077 m | 0,0014 m |

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

### Odom drift measurement in Open World

The measurement node compares raw odometry and EKF-filtered odometry with the
Gazebo ground-truth pose. It writes timestamped CSV files that can be used
directly to create plots.

For comparable results, start a fresh simulation for each run and use the Open
World:

```bash
world_file:=roboworks_open_world.sdf
```

The trajectory has two sections:

- 0–10 s: forward motion through a wide left turn, `linear.x=0.2`,
  `angular.z=0.15`
- 10–20 s: forward motion through a tighter right turn, `linear.x=0.2`,
  `angular.z=-0.45`

The steering direction changes at 10 seconds, making it possible to compare
how raw and EKF-filtered odometry react to the change in curvature.

Build the package before measuring:

```bash
cd /mnt/c/Users/samuv/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select var_n7k_szakd --symlink-install
source install/setup.bash
```

#### Without EKF

1. In terminal 1, start a fresh Open World simulation with the raw odometry
   TF enabled:

   ```bash
   ros2 launch var_n7k_szakd roboworks_sim.launch.py \
     world_file:=roboworks_open_world.sdf \
     publish_odom_tf:=True
   ```

2. In terminal 2, start the logger:

   ```bash
   ros2 run var_n7k_szakd interactive_drift_monitor --ros-args \
     -p measure_filtered:=False \
     -p measure_amcl:=False \
     -p duration:=20.0 \
     -p output_csv:=/tmp/odom_drift_open_world_20s_no_ekf.csv
   ```

3. In terminal 3, publish the initial pose and then run the two consecutive
   10-second control sections:

   ```bash
   ros2 topic pub --once /initialpose \
     geometry_msgs/msg/PoseWithCovarianceStamped \
     "{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}"
   sleep 1
   timeout 10s ros2 topic pub --rate 10 /model/roboworks/cmd_vel \
     geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.15}}"
   timeout 10s ros2 topic pub --rate 10 /model/roboworks/cmd_vel \
     geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: -0.45}}"
   ```

#### With EKF

1. Stop the previous simulation. In terminal 1, start a fresh Open World
   simulation without the raw odometry TF:

   ```bash
   ros2 launch var_n7k_szakd roboworks_sim.launch.py \
     world_file:=roboworks_open_world.sdf \
     publish_odom_tf:=False
   ```

2. In terminal 2, start the EKF:

   ```bash
   ros2 run robot_localization ekf_node --ros-args \
     -p use_sim_time:=True \
     --params-file /mnt/c/Users/samuv/ros2_ws/src/var_n7k_szakd/config/ekf.yaml
   ```

3. In terminal 3, start the 20-second logger:

   ```bash
   ros2 run var_n7k_szakd interactive_drift_monitor --ros-args \
     -p measure_filtered:=True \
     -p measure_amcl:=False \
     -p duration:=20.0 \
     -p output_csv:=/tmp/odom_drift_open_world_20s_ekf.csv
   ```

4. In terminal 4, publish the same initial pose and run the same two control
   sections:

   ```bash
   ros2 topic pub --once /initialpose \
     geometry_msgs/msg/PoseWithCovarianceStamped \
     "{header: {frame_id: map}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}"
   sleep 1
   timeout 10s ros2 topic pub --rate 10 /model/roboworks/cmd_vel \
     geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: 0.15}}"
   timeout 10s ros2 topic pub --rate 10 /model/roboworks/cmd_vel \
     geometry_msgs/msg/Twist "{linear: {x: 0.2}, angular: {z: -0.45}}"
   ```

The logger stops automatically after 20 seconds. CSV columns:

- `time_s`: elapsed time in seconds
- `raw_drift_m`: raw odometry position drift in metres
- `filtered_drift_m`: EKF-filtered position drift in metres
- `raw_drift_yaw_deg` and `filtered_drift_yaw_deg`: orientation error in degrees

The no-EKF run contains only the `raw_*` columns. The CSV files used for the
measurement are:

```text
/tmp/odom_drift_open_world_20s_no_ekf.csv
/tmp/odom_drift_open_world_20s_ekf.csv
```

Example values from the measurement:

| Time | Without EKF | With EKF |
|---:|---:|---:|
| 0 s | 0.000 m | 0.000 m |
| 6 s | 0.000 m | 0.000 m |
| 9 s | 0.0156 m | 0.0004 m |
| 10 s | 0.0234 m | 0.0040 m |
| 15 s | 0.0499 m | 0.0121 m |
| 18 s | 0.0797 m | 0.0117 m |
| 20 s | 0.2077 m | 0.0014 m |

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
