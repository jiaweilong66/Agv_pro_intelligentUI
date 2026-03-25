#!/bin/bash

# Independent script to launch Smart Logistics
# This runs completely separately from UI process

# Source ROS environment
source /opt/ros/noetic/setup.bash
source /home/er/myagv_ros/devel/setup.bash

# Navigate and run
cd ~/Smart_Logistics_Kit-22-map
exec python3 main.py
