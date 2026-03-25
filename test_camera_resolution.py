#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Test camera with different resolutions
"""
import cv2

def test_resolution(camera_id, width, height):
    """Test camera with specific resolution"""
    print(f"\nTesting {width}x{height}...")
    
    cap = cv2.VideoCapture(camera_id)
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    if not cap.isOpened():
        print(f"  ✗ Failed to open camera")
        return False
    
    # Get actual resolution
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"  Requested: {width}x{height}")
    print(f"  Actual: {actual_width}x{actual_height}")
    
    # Try to read frame
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print(f"  ✗ Failed to read frame")
        cap.release()
        return False
    
    print(f"  ✓ Frame captured: {frame.shape}")
    
    # Check if it's all green
    import numpy as np
    b_mean = np.mean(frame[:,:,0])
    g_mean = np.mean(frame[:,:,1])
    r_mean = np.mean(frame[:,:,2])
    
    print(f"  Color: R={r_mean:.1f}, G={g_mean:.1f}, B={b_mean:.1f}")
    
    if g_mean > 200 and r_mean < 50 and b_mean < 50:
        print(f"  ⚠ Still all green!")
    else:
        print(f"  ✓ Colors look normal!")
    
    # Save test image
    filename = f"camera{camera_id}_{width}x{height}.jpg"
    cv2.imwrite(filename, frame)
    print(f"  ✓ Saved: {filename}")
    
    # Display
    cv2.imshow(f"Camera {camera_id} - {width}x{height}", frame)
    print(f"  Press any key to continue...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    cap.release()
    return True

def main():
    print("="*60)
    print("Camera Resolution Test")
    print("="*60)
    
    camera_id = 0
    
    # Test different resolutions
    resolutions = [
        (640, 480),    # VGA - lowest
        (800, 600),    # SVGA
        (1280, 720),   # HD
        (1920, 1080),  # Full HD
        (3264, 2464),  # Original high resolution
    ]
    
    print(f"\nTesting Camera {camera_id} with different resolutions...")
    print("We'll start from lowest to highest")
    print()
    
    for width, height in resolutions:
        success = test_resolution(camera_id, width, height)
        if not success:
            print(f"  Skipping higher resolutions...")
            break
        
        response = input("\n  Continue to next resolution? (y/n): ").strip().lower()
        if response != 'y':
            break
    
    print("\n" + "="*60)
    print("Test complete")
    print("="*60)
    print("\nCheck the saved images to see which resolution works best")
    print("If lower resolutions show correct colors, use that resolution")

if __name__ == "__main__":
    main()
