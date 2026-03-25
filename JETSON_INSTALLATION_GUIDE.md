# Jetson Installation Guide - New UI

## Quick Start

### Method 1: Desktop Shortcut (Recommended)

1. Open terminal in the project directory
2. Run the installation script:
```bash
chmod +x install_desktop_shortcut.sh
./install_desktop_shortcut.sh
```

3. A shortcut will appear on your desktop
4. Double-click the icon to launch the application

If the icon doesn't work immediately:
- Right-click the icon → Select "Allow Launching"
- Or: Right-click → Properties → Permissions → Check "Allow executing file as program"

### Method 2: Terminal Launch

```bash
# Make the script executable (first time only)
chmod +x run_new_ui.sh

# Run the application
./run_new_ui.sh
```

### Method 3: Direct Python Launch

```bash
# From project root directory
python3 start_new_ui.py
```

## System Requirements

### Hardware
- NVIDIA Jetson (Nano, Xavier NX, AGX Xavier, etc.)
- MyAGV mobile robot base
- MechArm 270 robotic arm
- Lidar sensor
- 2 cameras (AGV camera + Arm camera)

### Software Dependencies

#### Required Packages
```bash
# System packages
sudo apt-get update
sudo apt-get install -y python3-pyqt5 python3-opencv python3-numpy

# ROS packages (should already be installed)
# - ros-melodic-base or ros-noetic-base
# - geometry_msgs

# Python packages
pip3 install pymycobot pygame
```

#### Optional Packages
```bash
# For OCR detection
pip3 install paddlepaddle paddleocr
```

## Project Structure

```
intelligent-logistics-system/
├── start_new_ui.py              # Main launcher (use this)
├── run_new_ui.sh                # Shell script launcher
├── install_desktop_shortcut.sh  # Desktop shortcut installer
├── IntelligentLogistics.desktop # Desktop entry file
├── new_ui/
│   ├── main_app.py             # Main application
│   ├── main_menu.ui            # Main menu interface
│   ├── quick_start.ui          # Quick start interface
│   ├── virtual_controller.ui   # Virtual controller interface
│   └── virtual_joystick.py     # Virtual joystick widget
├── functional/                  # Functional modules
├── components/                  # UI components
├── utils/                       # Utility functions
└── resources/                   # Resources (fonts, configs, etc.)
```

## Troubleshooting

### Issue: "No module named 'cofniger'"

**Solution**: Make sure you run from the project root directory:
```bash
cd /path/to/intelligent-logistics-system
python3 start_new_ui.py
```

### Issue: "No module named 'PyQt5'"

**Solution**: Install PyQt5:
```bash
sudo apt-get install python3-pyqt5
```

### Issue: "No module named 'pymycobot'"

**Solution**: Install pymycobot:
```bash
pip3 install pymycobot
```

### Issue: Camera not working

**Solution**: Check camera permissions and device paths:
```bash
# Check camera devices
ls -l /dev/video*

# Add user to video group
sudo usermod -a -G video $USER

# Reboot
sudo reboot
```

### Issue: ROS not found

**Solution**: Source ROS environment:
```bash
# Add to ~/.bashrc
echo "source /opt/ros/melodic/setup.bash" >> ~/.bashrc
# or for ROS Noetic
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc

# Reload
source ~/.bashrc
```

### Issue: Permission denied for GPIO

**Solution**: Add user to gpio group:
```bash
sudo usermod -a -G gpio $USER
sudo reboot
```

### Issue: Desktop shortcut doesn't work

**Solution 1**: Make files executable:
```bash
chmod +x run_new_ui.sh
chmod +x start_new_ui.py
```

**Solution 2**: Trust the desktop file:
```bash
gio set ~/Desktop/IntelligentLogistics.desktop metadata::trusted true
```

**Solution 3**: Run installation script again:
```bash
./install_desktop_shortcut.sh
```

## Running on Boot (Optional)

To automatically start the application on boot:

1. Create systemd service:
```bash
sudo nano /etc/systemd/system/intelligent-logistics.service
```

2. Add the following content:
```ini
[Unit]
Description=Intelligent Logistics System
After=graphical.target

[Service]
Type=simple
User=ubuntu
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/ubuntu/.Xauthority"
WorkingDirectory=/home/ubuntu/intelligent-logistics-system
ExecStart=/usr/bin/python3 /home/ubuntu/intelligent-logistics-system/start_new_ui.py
Restart=on-failure

[Install]
WantedBy=graphical.target
```

3. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable intelligent-logistics.service
sudo systemctl start intelligent-logistics.service
```

4. Check status:
```bash
sudo systemctl status intelligent-logistics.service
```

## Features

### Main Menu
- Quick Start: Launch the intelligent logistics workflow
- Virtual Controller: Control arm and AGV with virtual joysticks
- Product Parameters: View system information (coming soon)

### Quick Start Interface
- Lidar control
- Navigation control
- Move to shelf
- Circular sorting
- ARUCO/QR code detection
- Joystick/Keyboard control
- Real-time camera feeds
- Task progress visualization
- Log output

### Virtual Controller Interface
- Left joystick: Arm control (X/Y movement)
- Right joystick: AGV control (forward/backward/rotation)
- Gripper open/close
- Pump on/off
- Arm lock/release
- Reset to start position

## Performance Tips

1. **Close unused applications** to free up resources
2. **Use hardware acceleration** for camera processing
3. **Adjust camera resolution** if performance is slow
4. **Monitor CPU temperature** and use cooling if needed
5. **Use SSD** instead of SD card for better I/O performance

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review log output in the terminal
3. Check system logs: `journalctl -xe`
4. Verify hardware connections

## Updates

To update the application:
```bash
cd /path/to/intelligent-logistics-system
git pull origin main
# or copy new files if not using git
```

No need to reinstall the desktop shortcut after updates.
