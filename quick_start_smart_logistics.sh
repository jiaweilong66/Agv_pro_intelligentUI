#!/bin/bash

# Quick Start Script for Smart Logistics
# This script runs completely independently from UI

echo "========================================="
echo "Quick Start: Smart Logistics Workflow"
echo "========================================="

# Source ROS environment
source /opt/ros/noetic/setup.bash
source /home/er/myagv_ros/devel/setup.bash

# Navigate to Smart Logistics directory
cd ~/Smart_Logistics_Kit-22-map

# Run main.py
echo "Starting Smart Logistics main.py..."
python3 main.py

echo "========================================="
echo "Smart Logistics workflow completed"
echo "========================================="
