#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Test and display camera feeds individually
Press 'q' to quit, 's' to save snapshot
"""
import cv2
import sys

def test_camera(camera_id, name):
    """Test a single camera and display the feed"""
    print(f"\n{'='*60}")
    print(f"Testing {name} (video{camera_id})")
    print(f"{'='*60}")
    print("Press 'q' to quit")
    print("Press 's' to save snapshot")
    print()
    
    # Open camera
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print(f"✗ Failed to open {name}")
        return False
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print(f"✓ Camera opened successfully")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps}")
    print()
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("✗ Failed to read frame")
            break
        
        frame_count += 1
        
        # Add text overlay
        cv2.putText(frame, f"{name} - Frame: {frame_count}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   1, (0, 255, 0), 2)
        cv2.putText(frame, f"Resolution: {width}x{height}", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit, 's' to save", 
                   (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.7, (255, 255, 255), 2)
        
        # Display
        cv2.imshow(name, frame)
        
        # Handle key press
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Quit by user")
            break
        elif key == ord('s'):
            filename = f"{name.replace(' ', '_')}_snapshot.jpg"
            cv2.imwrite(filename, frame)
            print(f"✓ Snapshot saved: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"✓ {name} test completed. Total frames: {frame_count}")
    return True

def main():
    print("="*60)
    print("Camera Test Tool")
    print("="*60)
    
    if len(sys.argv) > 1:
        # Test specific camera
        camera_id = int(sys.argv[1])
        name = f"Camera {camera_id}"
        test_camera(camera_id, name)
    else:
        # Interactive menu
        print("\nAvailable cameras:")
        print("0 - AGV 2D Camera (video0) - 3264x2464")
        print("1 - Arm Camera (video1) - 640x480")
        print()
        
        choice = input("Select camera to test (0 or 1, or 'both'): ").strip().lower()
        
        if choice == 'both':
            print("\nTesting both cameras sequentially...")
            print("First: AGV 2D Camera")
            input("Press Enter to start AGV camera test...")
            test_camera(0, "AGV 2D Camera")
            
            print("\nSecond: Arm Camera")
            input("Press Enter to start Arm camera test...")
            test_camera(1, "Arm Camera")
        elif choice == '0':
            test_camera(0, "AGV 2D Camera")
        elif choice == '1':
            test_camera(1, "Arm Camera")
        else:
            print("Invalid choice")
            return
    
    print("\n" + "="*60)
    print("Test completed")
    print("="*60)

if __name__ == "__main__":
    main()
