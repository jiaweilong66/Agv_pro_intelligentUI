#!/bin/bash
# Setup all script permissions

echo "Setting up permissions for all scripts..."

chmod +x install_desktop_shortcut.sh
chmod +x start_with_ros.sh
chmod +x run_new_ui.sh
chmod +x start_new_ui.py
chmod +x safe_start.sh
chmod +x diagnose_camera.sh
chmod +x check_environment.py

echo "✓ All scripts are now executable"
echo ""
echo "Available commands:"
echo "  ./safe_start.sh           - Safe startup with cleanup"
echo "  ./start_with_ros.sh       - Auto-start with roscore"
echo "  ./diagnose_camera.sh      - Diagnose camera issues"
echo "  ./check_environment.py    - Check dependencies"
echo "  ./install_desktop_shortcut.sh - Install desktop icon"
