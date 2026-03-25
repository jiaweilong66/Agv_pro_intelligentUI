#!/bin/bash
# Simple startup script with camera cleanup

echo "=========================================="
echo "Intelligent Logistics System"
echo "=========================================="
echo ""

# Always release cameras before starting
echo "Releasing camera devices..."
fuser -k /dev/video* 2>/dev/null  # 释放所有video设备
sleep 1
echo "✓ Cameras released"
echo ""

# Check if roscore is running
if pgrep -x "roscore" > /dev/null || pgrep -x "rosmaster" > /dev/null; then
    echo "✓ ROS master is running"
else
    echo "⚠ ROS master is not running"
    echo "  Starting roscore in background..."
    
    # Source ROS
    if [ -f "/opt/ros/noetic/setup.bash" ]; then
        source /opt/ros/noetic/setup.bash
    elif [ -f "/opt/ros/melodic/setup.bash" ]; then
        source /opt/ros/melodic/setup.bash
    fi
    
    roscore &
    sleep 3
    echo "✓ ROS master started"
fi

echo ""
echo "Starting UI..."
echo ""

# Start the application
python3 start_new_ui.py

echo ""
echo "Application closed"
