#!/bin/bash
# Safe startup script with cleanup

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Intelligent Logistics System"
echo "Safe Startup Mode"
echo "=========================================="
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up..."
    
    # Kill any hanging Python processes
    pkill -f "start_new_ui.py" 2>/dev/null
    pkill -f "main_app.py" 2>/dev/null
    
    # Release camera devices
    fuser -k /dev/video0 2>/dev/null
    fuser -k /dev/video1 2>/dev/null
    
    # Small delay
    sleep 1
    
    echo "Cleanup complete"
}

# Register cleanup on exit
trap cleanup EXIT INT TERM

# Check if roscore is running
echo "Checking ROS master..."
if pgrep -x "roscore" > /dev/null || pgrep -x "rosmaster" > /dev/null; then
    echo "✓ ROS master is running"
else
    echo "⚠ ROS master is not running"
    echo "Starting roscore..."
    
    # Source ROS
    if [ -f "/opt/ros/noetic/setup.bash" ]; then
        source /opt/ros/noetic/setup.bash
    elif [ -f "/opt/ros/melodic/setup.bash" ]; then
        source /opt/ros/melodic/setup.bash
    fi
    
    # Start roscore in background
    roscore &
    ROSCORE_PID=$!
    sleep 3
fi

# Check camera availability
echo ""
echo "Checking cameras..."
if [ -e "/dev/video0" ]; then
    echo "✓ /dev/video0 exists"
else
    echo "⚠ /dev/video0 not found"
fi

if [ -e "/dev/video1" ]; then
    echo "✓ /dev/video1 exists"
else
    echo "⚠ /dev/video1 not found"
fi

# Don't kill camera processes - let the app handle it
echo ""
echo "Note: Not releasing cameras - app will handle them"

# Start the application
echo ""
echo "=========================================="
echo "Starting application..."
echo "=========================================="
echo ""

# Set environment variables for better stability
export QT_QPA_PLATFORM=xcb
# Don't set OPENCV_VIDEOIO_PRIORITY_GSTREAMER - let OpenCV decide

# Run with Python unbuffered output
python3 -u start_new_ui.py

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Application exited with code: $EXIT_CODE"
echo "=========================================="

# Cleanup will run automatically via trap
