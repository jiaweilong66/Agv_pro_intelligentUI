#!/bin/bash
# Intelligent Logistics System - New UI Launcher for Jetson
# This script launches the new UI interface on Jetson platform

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Set environment variables
export DISPLAY=:0
export QT_QPA_PLATFORM=xcb

# Print startup message
echo "=========================================="
echo "Intelligent Logistics System"
echo "Starting New UI Interface..."
echo "=========================================="
echo ""

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed!"
    echo "Please install Python3 first."
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: PyQt5 is not installed!"
    echo "Please run: sudo apt-get install python3-pyqt5"
    exit 1
fi

# Run the new UI application
echo "Launching application..."
echo ""
python3 start_new_ui.py

# Check exit status
if [ $? -ne 0 ]; then
    echo ""
    echo "=========================================="
    echo "Application exited with error"
    echo "Press Enter to close..."
    read
fi
