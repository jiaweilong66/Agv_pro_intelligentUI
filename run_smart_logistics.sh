#!/bin/bash
# Smart Logistics Workflow Runner
# This script runs the Smart Logistics main program

echo "=========================================="
echo "Smart Logistics Workflow Runner"
echo "=========================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TARGET_DIR="$SCRIPT_DIR/Smart_Logistics_Kit-22-map"

# Check if Smart Logistics directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "ERROR: Smart Logistics directory not found!"
    echo "Expected location: $TARGET_DIR/"
    echo ""
    echo "Please ensure the Smart_Logistics_Kit-22-map directory"
    echo "is in your repository directory."
    exit 1
fi

# Check if main.py exists
if [ ! -f "$TARGET_DIR/main.py" ]; then
    echo "ERROR: main.py not found!"
    echo "Expected location: $TARGET_DIR/main.py"
    exit 1
fi

echo "✓ Smart Logistics directory found"
echo "✓ main.py found"
echo ""

# Check if roscore is running
if ! pgrep -x "roscore" > /dev/null && ! pgrep -x "rosmaster" > /dev/null; then
    echo "WARNING: roscore does not appear to be running!"
    echo "Will attempt to continue, but ROS nodes might fail if master truly isn't available."
    echo ""
fi

echo "Starting Smart Logistics workflow..."
echo "=========================================="
echo ""

# Navigate to Smart Logistics directory and run main.py
cd "$TARGET_DIR"
python3 main.py

echo ""
echo "=========================================="
echo "Smart Logistics workflow finished"
echo "=========================================="
