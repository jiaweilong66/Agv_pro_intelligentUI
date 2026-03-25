# Virtual Controller Functions

## Overview
The Virtual Controller interface provides real-time control of the MechArm270 robotic arm and AGV mobile base through intuitive virtual joysticks.

## Components Initialized

### MechArm270 (Robotic Arm)
- Port: `/dev/ttyACM0`
- Initial angles: `[90, 0, 0, 0, 90, 0]`
- Arm speed: `10`
- Gripper range: `0-100`

### CmdVelPublisher (AGV Control)
- Topic: `/cmd_vel`
- Linear speed range: `-0.3 to 0.3 m/s`
- Angular speed range: `-0.5 to 0.5 rad/s`

## Virtual Joystick Controls

### Left Joystick - Arm Control
Controls the MechArm270 robotic arm position:

- **Up (Arm Y+)**: Move arm forward (coord 1, direction 1)
- **Down (Arm Y-)**: Move arm backward (coord 1, direction 0)
- **Left (Arm X-)**: Move arm left (coord 2, direction 1)
- **Right (Arm X+)**: Move arm right (coord 2, direction 0)

The joystick uses `jog_coord()` for continuous movement and automatically stops when released.

### Right Joystick - AGV Control
Controls the AGV mobile base:

- **Up (Forward)**: Move robot forward (linear.x = positive)
- **Down (Backward)**: Move robot backward (linear.x = negative)
- **Left**: Rotate robot left (angular.z = positive)
- **Right**: Rotate robot right (angular.z = negative)

The joystick publishes velocity commands to `/cmd_vel` topic and stops when released.

## Button Functions

### Top Row - Gripper Control (Green Buttons)

#### Gripper Open
- Increases gripper value by 10 (max 100)
- Opens the gripper jaws
- Command: `mech_arm.set_gripper_value(gripper_value, 100)`

#### Gripper Close
- Decreases gripper value by 10 (min 0)
- Closes the gripper jaws
- Moves arm to pick position: `[-93.6, 1.93, 6.24, -0.17, 68.81, -6.24]`
- Command: `mech_arm.set_gripper_value(gripper_value, 100)`

#### Pump On
- Activates the suction pump
- Command: `Functional.turn_on_pump()`
- Used for picking up objects with suction

#### Pump Off
- Deactivates the suction pump
- Command: `Functional.turn_off_pump()`
- Used for releasing objects

### Middle Row - Arm Lock Control (Red Buttons)

#### Lock Arm
- Powers on all arm servos
- Locks the arm in current position
- Command: `mech_arm.power_on()`
- Prevents manual movement

#### Release Arm
- Releases all arm servos
- Allows manual positioning
- Command: `mech_arm.release_all_servos()`
- Useful for teaching positions

### Bottom Row - Reset (Orange Button)

#### Reset to Start Position
- Resets both joysticks to center
- Moves arm to initial position: `[90, 0, 0, 0, 90, 0]`
- Command: `mech_arm.send_angles(init_angles, 100)`
- Speed: 100

## Real-time Feedback

### Status Labels
- **Arm Status**: Displays current arm joystick position (X, Y)
- **AGV Status**: Displays current AGV joystick position (X, Y)
- Values range from -1.0 to 1.0

### Visual Feedback
- Joystick ball follows mouse cursor in real-time
- Ball color changes when pressed (darker blue)
- Auto-centers when released
- Direction labels show control mapping

## Integration with Original Code

All functions are integrated from the original `main.py` and `functional/joystick.py`:

1. **MechArm270 Control**: Same as physical joystick controller
2. **CmdVelPublisher**: Identical ROS velocity publishing
3. **Pump Control**: Uses same `Functional` class methods
4. **Gripper Control**: Same gripper value range and commands

## Fallback Behavior

If hardware is not available:
- MechArm270: Logs simulated commands to console
- CmdVelPublisher: Logs simulated movement to console
- All buttons remain functional for testing
- No errors thrown, graceful degradation

## Usage Tips

1. **Start Radar First**: Some functions require radar to be running
2. **Smooth Control**: Joysticks provide proportional control based on distance from center
3. **Emergency Stop**: Release joysticks to immediately stop movement
4. **Reset Often**: Use reset button to return to known safe position
5. **Lock for Precision**: Lock arm when not actively controlling for stability

## Safety Notes

- Always ensure clear workspace before moving arm
- Use release arm function for manual teaching
- Reset position returns to safe home position
- Pump should be turned off when not in use
- AGV movement stops automatically when joystick is released
