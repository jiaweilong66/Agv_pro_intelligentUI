#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Environment Check Script
Verifies that all dependencies are installed and configured correctly
"""
import sys
import os

def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 6:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.6+")
        return False

def check_module(module_name, package_name=None):
    """Check if a Python module is installed"""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"  ✓ {package_name} - Installed")
        return True
    except ImportError:
        print(f"  ✗ {package_name} - Not installed")
        return False

def check_project_structure():
    """Check if project structure is correct"""
    print("\nChecking project structure...")
    required_files = [
        'start_new_ui.py',
        'new_ui/main_app.py',
        'new_ui/main_menu.ui',
        'new_ui/quick_start.ui',
        'new_ui/virtual_controller.ui',
        'new_ui/virtual_joystick.py',
        'cofniger.py',
        'constant.py',
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - Missing")
            all_exist = False
    
    return all_exist

def main():
    print("=" * 60)
    print("Intelligent Logistics System - Environment Check")
    print("=" * 60)
    print()
    
    results = []
    
    # Check Python version
    results.append(check_python_version())
    
    # Check required modules
    print("\nChecking required Python packages...")
    results.append(check_module('PyQt5', 'PyQt5'))
    results.append(check_module('cv2', 'opencv-python'))
    results.append(check_module('numpy', 'numpy'))
    
    # Check optional modules
    print("\nChecking optional Python packages...")
    check_module('pygame', 'pygame')
    check_module('pymycobot', 'pymycobot')
    
    # Check ROS (optional)
    print("\nChecking ROS packages (optional)...")
    ros_available = check_module('rospy', 'ROS')
    if ros_available:
        check_module('geometry_msgs', 'geometry_msgs')
    
    # Check project structure
    results.append(check_project_structure())
    
    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("✓ All required dependencies are installed!")
        print("You can now run: python3 start_new_ui.py")
    else:
        print("✗ Some dependencies are missing.")
        print("\nTo install missing packages:")
        print("  sudo apt-get install python3-pyqt5 python3-opencv python3-numpy")
        print("  pip3 install pygame pymycobot")
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()
