#!/bin/bash
# Install Desktop Shortcut for Intelligent Logistics System
# This script creates a desktop shortcut for easy access

echo "=========================================="
echo "Intelligent Logistics System"
echo "Desktop Shortcut Installation"
echo "=========================================="
echo ""

# Get the current directory (project root)
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Desktop directory
DESKTOP_DIR="$HOME/Desktop"

# Desktop entry file
DESKTOP_FILE="IntelligentLogistics.desktop"

# Check if Desktop directory exists
if [ ! -d "$DESKTOP_DIR" ]; then
    echo "Creating Desktop directory..."
    mkdir -p "$DESKTOP_DIR"
fi

# Update the desktop file with correct path
echo "Creating desktop shortcut..."
cat > "$DESKTOP_DIR/$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Intelligent Logistics System
Comment=MyAGV Intelligent Logistics Management System
Exec=bash -c "cd $PROJECT_DIR && ./start_with_ros.sh"
Icon=applications-system
Terminal=true
Categories=Application;Development;
StartupNotify=true
EOF

# Make the desktop file executable
chmod +x "$DESKTOP_DIR/$DESKTOP_FILE"

# Make the run scripts executable
chmod +x "$PROJECT_DIR/run_new_ui.sh"
chmod +x "$PROJECT_DIR/start_with_ros.sh"
chmod +x "$PROJECT_DIR/start_new_ui.py"

# Trust the desktop file (for Ubuntu 20.04+)
if command -v gio &> /dev/null; then
    gio set "$DESKTOP_DIR/$DESKTOP_FILE" metadata::trusted true
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "A shortcut has been created on your desktop:"
echo "  $DESKTOP_DIR/$DESKTOP_FILE"
echo ""
echo "You can now double-click the icon on your desktop to launch the application."
echo ""
echo "If the icon doesn't work, try:"
echo "1. Right-click the icon"
echo "2. Select 'Allow Launching'"
echo "   or 'Properties' -> 'Permissions' -> 'Allow executing file as program'"
echo ""
