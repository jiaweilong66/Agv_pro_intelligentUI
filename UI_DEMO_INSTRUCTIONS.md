# UI Demo Instructions

## Quick Start

### Windows
Simply double-click `run_ui_demo.bat` or run:
```bash
python run_ui_demo.py
```

### Linux/Mac
```bash
python3 run_ui_demo.py
```

## Requirements

Only PyQt5 is required for the demo:
```bash
pip install PyQt5
```

## What You Can Do

The demo allows you to:

1. **Navigate between interfaces**
   - Main Menu with 3 buttons
   - Quick Start interface
   - Virtual Controller interface

2. **Test Virtual Joysticks**
   - Drag the joystick balls with your mouse
   - Watch them follow your cursor in real-time
   - Release to auto-center
   - See position values update

3. **Click All Buttons**
   - All buttons are functional and log actions
   - No hardware required
   - Safe to test everything

## Interface Overview

### Main Menu
- Quick Start: Opens the logistics task interface
- Virtual Controller: Opens the dual joystick controller
- Product Parameters: Coming soon

### Quick Start Interface
- Left panel: Control buttons for logistics tasks
- Right panel: Camera views (placeholders in demo)
- Bottom: Task progress nodes (5 stages)
- Log output area

### Virtual Controller
- Left joystick: Arm control (X+/X-/Y+/Y-)
- Right joystick: AGV control (Forward/Backward/Left/Right)
- Top buttons: Gripper and Pump controls
- Middle buttons: Arm lock/release
- Bottom button: Reset position

## Notes

- This is a UI-only demo
- No hardware dependencies
- Camera views will show placeholders
- All actions are logged to console
- Designed for Jetson platform but demo runs on any OS

## Troubleshooting

If you get an error:
1. Make sure Python 3.7+ is installed
2. Install PyQt5: `pip install PyQt5`
3. Run from the project root directory
4. Check that all .ui files exist in new_ui/ folder
