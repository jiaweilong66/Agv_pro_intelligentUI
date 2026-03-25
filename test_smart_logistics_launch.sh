#!/bin/bash

# Test script to launch Smart Logistics exactly like UI does
# This helps diagnose if the issue is in the launch method

echo "========================================="
echo "Testing Smart Logistics Launch Method"
echo "========================================="

# Source ROS environment
source /opt/ros/noetic/setup.bash
source /home/er/myagv_ros/devel/setup.bash

# Navigate to Smart Logistics directory
cd ~/Smart_Logistics_Kit-22-map

# Launch main.py
echo "Starting Smart Logistics main.py..."
python3 main.py

echo "========================================="
echo "Smart Logistics finished"
echo "========================================="
