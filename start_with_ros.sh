#!/bin/bash
# Complete startup script for Intelligent Logistics System with ROS
# This script starts roscore and then launches the UI

# Set non-interactive flag to skip ROS version selection prompt in .bashrc
export ROS_DISTRO_SELECTED=1
export CHOOSE_ROS_DISTRO=noetic

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Intelligent Logistics System"
echo "Complete Startup with ROS"
echo "=========================================="
echo ""

# Fix DISPLAY for VNC sessions
if [ -z "$DISPLAY" ]; then
    echo -e "${YELLOW}DISPLAY not set, detecting...${NC}"
    # Try common VNC displays
    for disp in :0 :1 :2; do
        if xdpyinfo -display $disp >/dev/null 2>&1; then
            export DISPLAY=$disp
            echo -e "${GREEN}✓ Using DISPLAY=$DISPLAY${NC}"
            break
        fi
    done
    
    if [ -z "$DISPLAY" ]; then
        export DISPLAY=:0
        echo -e "${YELLOW}⚠ Defaulting to DISPLAY=:0${NC}"
    fi
else
    echo -e "${GREEN}✓ DISPLAY=$DISPLAY${NC}"
fi

# Set environment variables to avoid GTK conflicts
export QT_QPA_PLATFORM_PLUGIN_PATH=""
export QT_XKB_CONFIG_ROOT="/usr/share/X11/xkb"
export OPENCV_VIDEOIO_PRIORITY_MSMF="0"
export OPENCV_VIDEOIO_DEBUG="0"

# Suppress GTK warnings
export G_MESSAGES_DEBUG=""
export PYTHONWARNINGS="ignore"

# Check if roscore is already running
if pgrep -x "roscore" > /dev/null || pgrep -x "rosmaster" > /dev/null; then
    echo -e "${GREEN}✓ ROS master is already running${NC}"
else
    echo -e "${YELLOW}Starting ROS master (roscore)...${NC}"
    
    # Source ROS environment - directly source ROS Noetic without interactive prompt
    # This bypasses the "ros noetic(1) or ros2 galactic(2)?" prompt in .bashrc
    if [ -f "/opt/ros/noetic/setup.bash" ]; then
        source /opt/ros/noetic/setup.bash
        echo -e "${GREEN}✓ ROS Noetic environment loaded${NC}"
    elif [ -f "/opt/ros/melodic/setup.bash" ]; then
        source /opt/ros/melodic/setup.bash
        echo -e "${GREEN}✓ ROS Melodic environment loaded${NC}"
    else
        echo -e "${RED}✗ ROS not found!${NC}"
        echo "Please install ROS first."
        exit 1
    fi
    
    # Also source workspace setup if it exists
    if [ -f "$HOME/catkin_ws/devel/setup.bash" ]; then
        source "$HOME/catkin_ws/devel/setup.bash"
        echo -e "${GREEN}✓ Catkin workspace loaded${NC}"
    fi
    
    # Start roscore in background
    roscore > /tmp/roscore.log 2>&1 &
    ROSCORE_PID=$!
    
    # Wait for roscore to start
    echo "Waiting for ROS master to initialize..."
    sleep 3
    
    # Check if roscore started successfully
    if pgrep -x "roscore" > /dev/null || pgrep -x "rosmaster" > /dev/null; then
        echo -e "${GREEN}✓ ROS master started successfully (PID: $ROSCORE_PID)${NC}"
    else
        echo -e "${RED}✗ Failed to start ROS master${NC}"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Starting UI Application..."
echo "=========================================="
echo ""

# Run the UI application
python3 start_new_ui.py

# Cleanup function
cleanup() {
    echo ""
    echo "=========================================="
    echo "Shutting down..."
    echo "=========================================="
    
    # Kill roscore if we started it
    if [ ! -z "$ROSCORE_PID" ]; then
        echo "Stopping ROS master..."
        kill $ROSCORE_PID 2>/dev/null
        sleep 1
        # Force kill if still running
        kill -9 $ROSCORE_PID 2>/dev/null
    fi
    
    echo "Cleanup complete"
}

# Register cleanup function to run on exit
trap cleanup EXIT

# If we get here, the UI has closed
echo ""
echo "UI application closed"
