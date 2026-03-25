#!/bin/bash
# Camera Diagnostic Script

echo "=========================================="
echo "Camera Diagnostic Tool"
echo "=========================================="
echo ""

echo "1. Checking camera devices..."
ls -l /dev/video* 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Camera devices found"
else
    echo "✗ No camera devices found"
fi
echo ""

echo "2. Checking camera permissions..."
groups | grep -q video
if [ $? -eq 0 ]; then
    echo "✓ User is in video group"
else
    echo "✗ User is NOT in video group"
    echo "  Run: sudo usermod -a -G video $USER"
    echo "  Then logout and login again"
fi
echo ""

echo "3. Checking for processes using cameras..."
CAMERA_PROCS=$(fuser /dev/video* 2>/dev/null)
if [ -z "$CAMERA_PROCS" ]; then
    echo "✓ No processes using cameras"
else
    echo "⚠ Processes using cameras: $CAMERA_PROCS"
    echo "  Run: sudo kill -9 $CAMERA_PROCS"
fi
echo ""

echo "4. Testing camera with v4l2..."
if command -v v4l2-ctl &> /dev/null; then
    echo "Camera devices:"
    v4l2-ctl --list-devices
else
    echo "⚠ v4l2-utils not installed"
    echo "  Install: sudo apt-get install v4l2-utils"
fi
echo ""

echo "5. Testing camera with Python..."
python3 << 'EOF'
import cv2
import sys

print("Testing /dev/video0...")
cap0 = cv2.VideoCapture(0)
if cap0.isOpened():
    print("✓ /dev/video0 can be opened")
    cap0.release()
else:
    print("✗ /dev/video0 cannot be opened")

print("\nTesting /dev/video1...")
cap1 = cv2.VideoCapture(1)
if cap1.isOpened():
    print("✓ /dev/video1 can be opened")
    cap1.release()
else:
    print("✗ /dev/video1 cannot be opened")

print("\nTesting GStreamer pipeline...")
try:
    pipeline = "nvarguscamerasrc ! video/x-raw(memory:NVMM), width=640, height=480, format=NV12, framerate=30/1 ! nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink"
    cap_gst = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    if cap_gst.isOpened():
        print("✓ GStreamer pipeline works")
        cap_gst.release()
    else:
        print("✗ GStreamer pipeline failed")
except Exception as e:
    print(f"✗ GStreamer test error: {e}")
EOF

echo ""
echo "=========================================="
echo "Diagnostic complete"
echo "=========================================="
