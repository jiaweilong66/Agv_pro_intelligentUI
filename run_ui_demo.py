#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
UI Demo Mode Launcher
Run UI interface without Jetson hardware and ROS environment
"""
import sys
import os

print("=" * 60)
print("Intelligent Logistics System - UI Demo Mode")
print("=" * 60)
print("Note: Running in demo mode")
print("- No hardware dependencies required")
print("- Only for viewing UI and testing interactions")
print("=" * 60)
print()

# Check necessary dependencies
missing_packages = []
try:
    import PyQt5
except ImportError:
    missing_packages.append("PyQt5")

if missing_packages:
    print("Error: Missing required packages!")
    print("Missing packages:", ", ".join(missing_packages))
    print("\nPlease run the following command to install:")
    print(f"  pip install {' '.join(missing_packages)}")
    print("\nOr run:")
    print("  pip install -r requirements_windows.txt")
    input("\nPress Enter to exit...")
    sys.exit(1)

# Import and run demo application
try:
    print("Starting UI interface...")
    print()
    # Add new_ui directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'new_ui'))
    from new_ui.demo_app import main
    main()
except Exception as e:
    print(f"\nError: {e}")
    print("\nDetailed error information:")
    import traceback
    traceback.print_exc()
    print("\nPossible solutions:")
    print("1. Ensure all dependencies are installed: pip install PyQt5")
    print("2. Check Python version is 3.7 or higher")
    print("3. Check the error message above to identify missing modules")
    input("\nPress Enter to exit...")
    sys.exit(1)
