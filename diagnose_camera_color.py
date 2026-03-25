#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Diagnose camera color issues
"""
import cv2
import numpy as np

def analyze_frame(frame, frame_num):
    """Analyze frame color distribution"""
    if frame is None:
        return
    
    # Calculate color statistics
    b_mean = np.mean(frame[:,:,0])
    g_mean = np.mean(frame[:,:,1])
    r_mean = np.mean(frame[:,:,2])
    
    b_std = np.std(frame[:,:,0])
    g_std = np.std(frame[:,:,1])
    r_std = np.std(frame[:,:,2])
    
    print(f"\nFrame {frame_num} Analysis:")
    print(f"  Blue  - Mean: {b_mean:.1f}, Std: {b_std:.1f}")
    print(f"  Green - Mean: {g_mean:.1f}, Std: {g_std:.1f}")
    print(f"  Red   - Mean: {r_mean:.1f}, Std: {r_std:.1f}")
    
    # Check if it's all green
    if g_mean > 200 and r_mean < 50 and b_mean < 50:
        print("  ⚠ WARNING: Image is mostly green!")
        print("     Possible causes:")
        print("     1. Camera lens cap is on")
        print("     2. Camera is covered")
        print("     3. Color format issue")
    
    # Check if it's all black
    if b_mean < 10 and g_mean < 10 and r_mean < 10:
        print("  ⚠ WARNING: Image is all black!")
        print("     Possible causes:")
        print("     1. No light")
        print("     2. Camera not working")
    
    # Check if there's variation (actual image)
    if b_std > 20 or g_std > 20 or r_std > 20:
        print("  ✓ Image has variation - likely showing real content")

def test_camera_formats(camera_id):
    """Test different camera formats"""
    print(f"\n{'='*60}")
    print(f"Testing Camera {camera_id} with different formats")
    print(f"{'='*60}\n")
    
    formats = [
        ("Default", None),
        ("MJPEG", cv2.VideoWriter_fourcc(*'MJPG')),
        ("YUYV", cv2.VideoWriter_fourcc(*'YUYV')),
    ]
    
    for format_name, fourcc in formats:
        print(f"\nTrying format: {format_name}")
        cap = cv2.VideoCapture(camera_id)
        
        if fourcc is not None:
            cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        
        if not cap.isOpened():
            print(f"  ✗ Failed to open camera")
            continue
        
        # Try to read a frame
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print(f"  ✗ Failed to read frame")
            cap.release()
            continue
        
        print(f"  ✓ Frame captured: {frame.shape}")
        analyze_frame(frame, 1)
        
        # Save test image
        filename = f"test_camera{camera_id}_{format_name}.jpg"
        cv2.imwrite(filename, frame)
        print(f"  ✓ Saved test image: {filename}")
        
        cap.release()
        
        # Ask if this looks correct
        response = input(f"\n  Does {filename} look correct? (y/n): ").strip().lower()
        if response == 'y':
            print(f"  ✓ Format '{format_name}' works!")
            return format_name, fourcc
    
    return None, None

def main():
    print("="*60)
    print("Camera Color Diagnostic Tool")
    print("="*60)
    
    # Test camera 0
    print("\n\nTesting Camera 0 (AGV 2D Camera)...")
    print("-"*60)
    
    cap0 = cv2.VideoCapture(0)
    if cap0.isOpened():
        ret, frame = cap0.read()
        if ret:
            print(f"✓ Camera 0 opened: {frame.shape}")
            analyze_frame(frame, 1)
            
            # Save image
            cv2.imwrite("camera0_test.jpg", frame)
            print("\n✓ Saved: camera0_test.jpg")
            print("  Please check this image file")
            
            # Read a few more frames
            for i in range(2, 6):
                ret, frame = cap0.read()
                if ret:
                    analyze_frame(frame, i)
        else:
            print("✗ Failed to read frame from camera 0")
        cap0.release()
    else:
        print("✗ Failed to open camera 0")
    
    # Test camera 1
    print("\n\nTesting Camera 1 (Arm Camera)...")
    print("-"*60)
    
    cap1 = cv2.VideoCapture(1)
    if cap1.isOpened():
        ret, frame = cap1.read()
        if ret:
            print(f"✓ Camera 1 opened: {frame.shape}")
            analyze_frame(frame, 1)
            
            # Save image
            cv2.imwrite("camera1_test.jpg", frame)
            print("\n✓ Saved: camera1_test.jpg")
            print("  Please check this image file")
        else:
            print("✗ Failed to read frame from camera 1")
        cap1.release()
    else:
        print("✗ Failed to open camera 1")
    
    # Offer to test different formats
    print("\n\n" + "="*60)
    print("Would you like to test different color formats?")
    print("="*60)
    response = input("Test formats for camera 0? (y/n): ").strip().lower()
    
    if response == 'y':
        format_name, fourcc = test_camera_formats(0)
        if format_name:
            print(f"\n✓ Recommended format for camera 0: {format_name}")
    
    print("\n" + "="*60)
    print("Diagnostic complete")
    print("="*60)
    print("\nCheck the saved images:")
    print("  - camera0_test.jpg")
    print("  - camera1_test.jpg")
    print("\nIf camera 0 is all green:")
    print("  1. Check if lens cap is on")
    print("  2. Make sure camera is not covered")
    print("  3. Try using camera 1 as AGV camera instead")

if __name__ == "__main__":
    main()
