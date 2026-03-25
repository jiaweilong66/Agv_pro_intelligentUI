#!/bin/bash

# Complete Smart Logistics Workflow Test Script
# Simulates three independent terminal startup methods to ensure navigation accuracy

echo "========================================="
echo "Smart Logistics Complete Workflow Test"
echo "========================================="

# Source ROS environment
source /opt/ros/noetic/setup.bash
source /home/er/myagv_ros/devel/setup.bash

echo ""
echo "[Step 1/3] Starting Lidar Odometry System..."
echo "Executing: roslaunch myagv_odometry myagv_active.launch"

# Use setsid to create new process group, simulating independent terminal
setsid roslaunch myagv_odometry myagv_active.launch > /tmp/lidar_output.log 2>&1 &
LIDAR_PID=$!
echo "Lidar PID: $LIDAR_PID (independent process group)"

# Wait 10 seconds for Lidar to fully start and stabilize (reduced from 20)
echo "Waiting 10 seconds for Lidar to fully start and stabilize..."
sleep 5

# Check if laser data is being published normally
echo "Checking laser data publishing status..."
for i in {1..3}; do
    if timeout 3 rostopic hz /scan --window=3 2>/dev/null | grep -q "Hz"; then
        echo "✓ Laser data publishing normally"
        echo "[LIDAR_READY] Laser data publishing normally"
        break
    else
        echo "Waiting for laser data... ($i/5)"
        sleep 2
    fi
done

# Check odometry data
echo "Checking odometry data..."
if timeout 3 rostopic echo /odom -n 1 >/dev/null 2>&1; then
    echo "✓ Odometry data normal"
else
    echo "⚠ Odometry data abnormal"
fi

echo ""
echo "[Step 2/3] Starting Navigation System..."
echo "Executing: roslaunch myagv_navigation simplify_logistics_navigation_active.launch"

# Use setsid to create new process group, simulating independent terminal
setsid roslaunch myagv_navigation simplify_logistics_navigation_active.launch > /tmp/nav_output.log 2>&1 &
NAV_PID=$!
echo "Navigation PID: $NAV_PID (independent process group)"

# Wait 15 seconds for navigation system to fully start and stabilize (reduced from 30)
echo "Waiting 15 seconds for navigation system to fully start and stabilize..."
sleep 10

# Check key navigation topics
echo "Checking navigation system status..."
nav_topics=("/map" "/move_base/goal" "/move_base/status" "/amcl_pose")
for topic in "${nav_topics[@]}"; do
    if rostopic list | grep -q "^${topic}$"; then
        echo "✓ Topic $topic exists"
    else
        echo "✗ Topic $topic missing"
    fi
done

# Check if TF transforms are available
echo "Checking TF transform status..."
if timeout 5 rosrun tf tf_echo map base_footprint 2>/dev/null | head -n 5 | grep -q "Translation"; then
    echo "✓ TF transform map->base_footprint normal"
else
    echo "⚠ TF transform may be abnormal"
fi

# Check if AMCL localization is stable
echo "Checking AMCL localization status..."
if timeout 3 rostopic echo /amcl_pose -n 1 >/dev/null 2>&1; then
    echo "✓ AMCL localization data normal"
    echo "[NAVIGATION_READY] AMCL localization data normal"
else
    echo "⚠ AMCL localization data abnormal"
fi

# Additional wait for system to fully stabilize (reduced from 10)
echo "Additional 5 seconds wait for all systems to fully stabilize..."
sleep 5

echo ""
echo "[Step 3/3] Starting Smart Logistics Main Program..."
echo "Executing: cd Smart_Logistics_Kit-22-map && python3 test.py"

# Switch to Smart Logistics directory and run in new process group
cd Smart_Logistics_Kit-22-map

# Use setsid to create new process group, simulating independent terminal
echo "All systems stabilized, starting Smart Logistics task..."
setsid python3 test.py

# Cleanup after main program ends
echo ""
echo "========================================="
echo "Smart Logistics Main Program Ended"
echo "========================================="

# Ask whether to close Lidar and Navigation
read -p "Close Lidar and Navigation? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Closing Navigation (PID: $NAV_PID)..."
    # Kill entire process group
    pkill -P $NAV_PID 2>/dev/null
    kill $NAV_PID 2>/dev/null
    
    echo "Closing Lidar (PID: $LIDAR_PID)..."
    # Kill entire process group
    pkill -P $LIDAR_PID 2>/dev/null
    kill $LIDAR_PID 2>/dev/null
    
    echo "Cleanup completed"
fi

echo "Test script ended"
