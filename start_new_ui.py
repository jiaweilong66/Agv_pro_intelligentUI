#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Intelligent Logistics System - New UI Launcher
This script ensures correct Python path and launches the new UI
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now import and run the main application
if __name__ == "__main__":
    from new_ui.main_app import main
    main()
