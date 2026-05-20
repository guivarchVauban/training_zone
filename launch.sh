#!/bin/bash

# Kill any leftover Gazebo processes from a previous session
pkill -f "gz sim" 2>/dev/null
pkill -f "ruby.*gz" 2>/dev/null
sleep 1

ros2 run teleop_twist_joy teleop_node --ros-args --params-file /home/sguivarch/Devs/Simulation_drone_cible/training_zone/teleop.yaml &
ros2 run joy joy_node &
ros2 launch vrx_gz competition.launch.py world:=brest_coast
