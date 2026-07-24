#!/bin/bash
# Activate Nav2 lifecycle nodes

sleep 6

echo "Configuring planner_server..."
ros2 lifecycle set /planner_server configure
sleep 1

echo "Activating planner_server..."
ros2 lifecycle set /planner_server activate
sleep 1

echo "Configuring controller_server..."
ros2 lifecycle set /controller_server configure
sleep 1

echo "Activating controller_server..."
ros2 lifecycle set /controller_server activate
sleep 1

echo "Configuring bt_navigator..."
ros2 lifecycle set /bt_navigator configure
sleep 1

echo "Activating bt_navigator..."
ros2 lifecycle set /bt_navigator activate
sleep 1

echo "All Nav2 nodes activated!"
