#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
AGV Camera Configuration Fix
Helps configure the correct camera for AGV 2D
"""
import cv2
import sys
import os

def test_camera(source, description):
    """Test if a camera source works"""
    print(f"Testing {description}...")
    try:
        if isinstance(source, str):
            cap = cv2.VideoCapture(source, cv2.CAP_GSTREAMER)
        else:
            cap = cv2.VideoCapture(source)
        
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                print(f"  ✓ {description} works! Frame size: {frame.shape}")
                return True
            else:
                print(f"  ✗ {description} opened but can't read frames")
                return False
        else:
            print(f"  ✗ {description} failed to open")
            return False
    except Exception as e:
        print(f"  ✗ {description} error: {e}")
        return False

def gstreamer_pipeline(sensor_id=0, flip_method=2):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width=1920, height=1080, framerate=30/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width=960, height=540, format=BGRx ! "
        f"videoconvert ! "
        f"video/x-raw, format=BGR ! appsink"
    )

print("=" * 70)
print("AGV 2D Camera Configuration Helper")
print("=" * 70)
print()

# Test different camera sources
cameras = []

print("Scanning for available cameras...")
print()

# Test CSI cameras (GStreamer)
for sensor_id in [0, 1]:
    for flip in [0, 2]:
        pipeline = gstreamer_pipeline(sensor_id=sensor_id, flip_method=flip)
        desc = f"CSI Camera (sensor_id={sensor_id}, flip={flip})"
        if test_camera(pipeline, desc):
            cameras.append({
                'type': 'gstreamer',
                'config': f'gstreamer_pipeline(sensor_id={sensor_id}, flip_method={flip})',
                'description': desc
            })
            break  # Found working flip, no need to test others

# Test USB cameras
for video_id in range(4):
    desc = f"USB Camera /dev/video{video_id}"
    if test_camera(video_id, desc):
        cameras.append({
            'type': 'usb',
            'config': str(video_id),
            'description': desc
        })

print()
print("=" * 70)
print("Results:")
print("=" * 70)
print()

if not cameras:
    print("✗ No working cameras found!")
    print()
    print("Troubleshooting steps:")
    print("1. Check camera connections")
    print("2. Run: ls -l /dev/video*")
    print("3. Run: dmesg | grep -i camera")
    print("4. For CSI camera, run: nvgstcapture-1.0")
    sys.exit(1)

print(f"Found {len(cameras)} working camera(s):")
print()

for i, cam in enumerate(cameras, 1):
    print(f"{i}. {cam['description']}")
    print(f"   Config: {cam['config']}")
    print()

# Generate configuration
print("=" * 70)
print("Recommended Configuration:")
print("=" * 70)
print()

recommended = cameras[0]
print(f"Use: {recommended['description']}")
print()

if recommended['type'] == 'gstreamer':
    print("Edit constant.py and set:")
    print(f"  camera2D_pipline = {recommended['config']}")
else:
    print("Edit constant.py and set:")
    print(f"  camera2D_pipline = {recommended['config']}")

print()
print("=" * 70)
print("Quick Fix:")
print("=" * 70)
print()

# Create a backup and modify constant.py
constant_file = 'constant.py'
if os.path.exists(constant_file):
    print(f"Would you like to automatically update {constant_file}? (y/n)")
    response = input().strip().lower()
    
    if response == 'y':
        # Backup
        backup_file = 'constant.py.backup'
        with open(constant_file, 'r') as f:
            content = f.read()
        with open(backup_file, 'w') as f:
            f.write(content)
        print(f"✓ Backup created: {backup_file}")
        
        # Update
        if recommended['type'] == 'gstreamer':
            new_line = f"    camera2D_pipline = {recommended['config']}"
        else:
            new_line = f"    camera2D_pipline = {recommended['config']}"
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'camera2D_pipline' in line:
                lines[i] = new_line
                break
        
        with open(constant_file, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"✓ Updated {constant_file}")
        print()
        print("Configuration updated! Restart the application to apply changes.")
    else:
        print("Manual update required. See configuration above.")
else:
    print(f"✗ {constant_file} not found in current directory")
    print("Please run this script from the project root directory")

print()
