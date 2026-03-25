#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Standalone script: Navigate AGV back to the initial starting position (charging station).
Runs in an independent terminal to avoid UI process resource contention.
Reads the dynamically captured origin from /tmp/agv_initial_pose.txt if available.
"""
import os
import sys
import time
import rospy
from MapNavigation import MapNavigation

# Default charging station coordinates
DEFAULT_CHARGE_GOAL = [-0.5688837170600891, -0.31650811433792114, 0.4588518939959322, 0.8885127682686084]

def get_origin_goal():
    """Read the dynamically recorded origin, or fall back to default."""
    charge_goal = DEFAULT_CHARGE_GOAL
    pose_file = "/tmp/agv_initial_pose.txt"
    try:
        if os.path.exists(pose_file):
            with open(pose_file, "r") as f:
                parts = f.read().strip().split(",")
                if len(parts) == 4:
                    charge_goal = [float(p) for p in parts]
                    print(f"[INFO] Using dynamically captured origin: x={charge_goal[0]:.4f}, y={charge_goal[1]:.4f}")
                    return charge_goal
    except Exception as e:
        print(f"[WARNING] Could not read origin file: {e}")
    
    print(f"[INFO] Using default charge_goal: x={charge_goal[0]:.4f}, y={charge_goal[1]:.4f}")
    return charge_goal

def main():
    print("=" * 50)
    print("  Return to Origin - AGV Navigation Script")
    print("=" * 50)
    
    # Initialize ROS node
    map_navigation = MapNavigation()
    
    # Get target coordinates
    charge_goal = get_origin_goal()
    x_goal, y_goal, orientation_z, orientation_w = charge_goal
    
    print(f"\n[NAV] Navigating to origin: x={x_goal:.4f}, y={y_goal:.4f}")
    print(f"[NAV] Orientation: z={orientation_z:.4f}, w={orientation_w:.4f}")
    
    # Navigate to origin with retry
    reached = False
    max_retries = 3
    for attempt in range(max_retries):
        print(f"\n[NAV] Attempt {attempt + 1}/{max_retries}...")
        reached = map_navigation.moveToGoal(x_goal, y_goal, orientation_z, orientation_w)
        if reached:
            break
        print("[NAV] Navigation failed, retrying in 2 seconds...")
        time.sleep(2)
    
    if reached:
        print("\n[NAV] ✓ Reached docking area. Performing final docking...")
        try:
            # Low speed forward pulse to dock tightly at charging station
            for _ in range(18):
                map_navigation.pub_vel(0.04, 0, 0)
                time.sleep(0.1)
            # Full stop
            map_navigation.pub_vel(0, 0, 0)
            print("[NAV] ✓ Successfully docked at the charging station!")
        except Exception as e:
            print(f"[NAV] Warning during docking: {e}")
    else:
        print("\n[NAV] ✗ Failed to reach origin after all attempts.")
        print("[NAV] Please check for obstacles or AMCL localization.")
    
    print("\n[DONE] Return to Origin script finished.")
    print("You can close this terminal window.")

if __name__ == "__main__":
    main()
