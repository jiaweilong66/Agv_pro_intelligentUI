#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Test AGV 2D Camera (CSI Camera with GStreamer)
"""
import cv2
import sys

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=960,
    display_height=540,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

print("=" * 60)
print("AGV 2D Camera Test")
print("=" * 60)
print()

# Test 1: Simple pipeline
print("Test 1: Testing with sensor_id=0, flip_method=2 (default config)...")
pipeline1 = gstreamer_pipeline(sensor_id=0, flip_method=2)
print(f"Pipeline: {pipeline1}")
print()

cap1 = cv2.VideoCapture(pipeline1, cv2.CAP_GSTREAMER)
if cap1.isOpened():
    print("✓ Camera opened successfully with default config!")
    ret, frame = cap1.read()
    if ret:
        print(f"✓ Frame captured! Size: {frame.shape}")
    else:
        print("✗ Failed to read frame")
    cap1.release()
else:
    print("✗ Failed to open camera with default config")
    print()
    
    # Test 2: Try different sensor IDs
    print("Test 2: Trying different sensor IDs...")
    for sensor_id in [0, 1]:
        print(f"  Testing sensor_id={sensor_id}...")
        pipeline = gstreamer_pipeline(sensor_id=sensor_id, flip_method=0)
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        if cap.isOpened():
            print(f"  ✓ sensor_id={sensor_id} works!")
            cap.release()
            break
        else:
            print(f"  ✗ sensor_id={sensor_id} failed")
        cap.release()
    
    print()
    
    # Test 3: Try simpler pipeline
    print("Test 3: Testing with simpler pipeline...")
    simple_pipeline = "nvarguscamerasrc ! nvoverlaysink"
    print(f"Pipeline: {simple_pipeline}")
    print("Note: This will show video in a window if it works")
    print("Press Ctrl+C to stop")
    print()
    
    # Test 4: Try lower resolution
    print("Test 4: Testing with lower resolution...")
    pipeline_low = gstreamer_pipeline(
        sensor_id=0,
        capture_width=640,
        capture_height=480,
        display_width=640,
        display_height=480,
        framerate=30,
        flip_method=2
    )
    print(f"Pipeline: {pipeline_low}")
    cap_low = cv2.VideoCapture(pipeline_low, cv2.CAP_GSTREAMER)
    if cap_low.isOpened():
        print("✓ Camera opened with lower resolution!")
        ret, frame = cap_low.read()
        if ret:
            print(f"✓ Frame captured! Size: {frame.shape}")
        else:
            print("✗ Failed to read frame")
        cap_low.release()
    else:
        print("✗ Failed to open camera with lower resolution")
    
    print()
    
    # Test 5: Check GStreamer plugins
    print("Test 5: Checking GStreamer plugins...")
    import subprocess
    try:
        result = subprocess.run(['gst-inspect-1.0', 'nvarguscamerasrc'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ nvarguscamerasrc plugin is available")
        else:
            print("✗ nvarguscamerasrc plugin not found")
            print("  This is a CSI camera plugin for Jetson")
    except Exception as e:
        print(f"✗ Error checking GStreamer: {e}")

print()
print("=" * 60)
print("Recommendations:")
print("=" * 60)
print()

print("1. Check if CSI camera is connected:")
print("   - Look for camera ribbon cable connection")
print("   - Make sure it's properly seated")
print()

print("2. Check camera with nvgstcapture:")
print("   nvgstcapture-1.0")
print()

print("3. Check dmesg for camera errors:")
print("   dmesg | grep -i camera")
print("   dmesg | grep -i csi")
print()

print("4. If using USB camera instead of CSI:")
print("   - Edit constant.py")
print("   - Change: camera2D_pipline = 0  # or 1 for /dev/video1")
print()

print("5. Try running with sudo (for testing only):")
print("   sudo python3 test_agv_camera.py")
print()
