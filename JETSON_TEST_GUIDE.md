# Jetson Testing Guide - Smart Logistics Integration

## Quick Start Testing

This guide helps you test the Smart Logistics workflow integration on your Jetson system.

## Pre-Test Checklist

### 1. Verify Directory Structure

```bash
# Check Smart Logistics directory exists
ls ~/Smart_Logistics_Kit-22-map/

# Should see main.py and other files
ls ~/Smart_Logistics_Kit-22-map/main.py
```

### 2. Verify ROS Installation

```bash
# Check ROS is installed
which roslaunch
which roscore

# Source ROS environment
source /opt/ros/melodic/setup.bash  # or your ROS version

# Verify ROS packages exist
rospack find myagv_odometry
rospack find myagv_navigation
```

### 3. Verify Hardware Connections

```bash
# Check cameras
ls /dev/video*
# Should see: /dev/video0, /dev/video1

# Check mechanical arm
ls /dev/ttyACM*
# Should see: /dev/ttyACM0

# Check USB serial (if using CAN)
ls /dev/ttyUSB*
```

### 4. Verify Python Dependencies

```bash
cd ~/intelligent-logistics-system

# Test imports
python3 -c "import rospy; print('ROS OK')"
python3 -c "import cv2; print('OpenCV OK')"
python3 -c "from PyQt5 import QtWidgets; print('PyQt5 OK')"
python3 -c "from pymycobot import MechArm270; print('pymycobot OK')"
```

## Test Procedure

### Test 1: Basic UI Launch

```bash
cd ~/intelligent-logistics-system

# Start roscore first
roscore &

# Wait 5 seconds
sleep 5

# Launch UI
./start_ui.sh
```

**Expected Result:**
- UI window opens
- Main menu appears with 3 buttons
- No error messages in terminal

**If Failed:**
- Check error messages
- Verify all dependencies installed
- Check camera devices not in use

### Test 2: Quick Start Interface

**Steps:**
1. Click "Quick Start" button in main menu
2. Quick Start interface should appear
3. Verify all UI elements visible:
   - Left panel with 9 function buttons
   - Right panel with 2 camera views
   - Bottom with 5 task progress nodes
   - Log output area

**Expected Result:**
- All buttons clickable
- Camera views show black (not started yet)
- Task nodes show blue "..."
- Log shows initialization messages

### Test 3: Individual Components

Before testing full workflow, test individual components:

#### Test Lidar
1. Click "Open/Close" button under Lidar
2. Wait 5-10 seconds
3. Button should turn red and say "Close"
4. Log should show "Lidar odometry started successfully"

#### Test Navigation
1. Ensure Lidar is running
2. Click "Open/Close" button under Navigation
3. Wait 10-15 seconds
4. Button should turn red and say "Close"
5. Log should show "Navigation system started"

#### Test Cameras
1. Cameras should start automatically
2. AGV 2D Camera View should show camera feed
3. Mech 270 Camera View should show camera feed
4. If black, check camera devices

### Test 4: Smart Logistics Workflow (Full Test)

**Prerequisites:**
- roscore running
- All hardware connected
- Smart_Logistics_Kit-22-map directory exists
- No other processes using cameras

**Steps:**

1. **Start Fresh**
   ```bash
   # Kill any existing processes
   rosnode kill -a
   killall -9 python3
   
   # Release cameras
   sudo fuser -k /dev/video*
   
   # Restart roscore
   killall -9 roscore rosmaster
   roscore &
   sleep 5
   
   # Launch UI
   ./start_ui.sh
   ```

2. **Navigate to Quick Start**
   - Click "Quick Start" in main menu

3. **Start Workflow**
   - Click "Quick Start" button (top left)
   - Button should change to "Stop Workflow" (red)

4. **Monitor Progress**
   
   Watch the 5 task nodes at bottom:
   
   **Node 1: "Proceed to the loading"**
   - Should turn green within 5-10 seconds
   - Log shows: "[STEP 1/5] ✓ MyAGV odometry launched successfully"
   
   **Node 2: "Pick goods"**
   - Should turn green within 10-15 seconds after Node 1
   - Log shows: "[STEP 2/5] ✓ Navigation system launched successfully"
   
   **Node 3: "Proceed to the unloading"**
   - Should turn green within 5 seconds after Node 2
   - Log shows: "[STEP 3/5] ✓ Smart logistics program started"
   
   **Node 4: "Unload goods"**
   - Should turn green when myAGV starts navigating
   - Log shows: "[STEP 4/5] MyAGV navigating to positions..."
   
   **Node 5: "Success"**
   - Should turn green when arm starts picking
   - Log shows: "[STEP 5/5] 270 arm performing vision-based picking and sorting..."
   - Finally: "[SUCCESS] ✓ Smart logistics workflow completed successfully!"

5. **Verify Completion**
   - All 5 nodes should be green with checkmarks
   - Button should return to "Quick Start"
   - Log should show "[CLEANUP] ✓ All processes stopped"

**Expected Duration:**
- Total workflow: 5-30 minutes (depends on Smart Logistics tasks)
- Initialization: ~20 seconds
- Main workflow: Variable (depends on navigation and picking tasks)

### Test 5: Stop Workflow

**Steps:**
1. Start the workflow as in Test 4
2. Wait until Node 2 or 3 is green
3. Click "Stop Workflow" button

**Expected Result:**
- Log shows "[SYSTEM] Stopping Smart Logistics workflow..."
- Log shows "[CLEANUP] Stopping all processes..."
- Button returns to "Quick Start"
- All processes terminated cleanly

### Test 6: Error Handling

#### Test 6a: No roscore
```bash
# Kill roscore
killall -9 roscore rosmaster

# Launch UI
./start_ui.sh

# Try to start workflow
# Click "Quick Start" button
```

**Expected Result:**
- Error dialog appears: "Failed to initialize ROS node"
- Message: "Please start roscore first"
- Button remains "Quick Start"

#### Test 6b: Missing Smart Logistics Directory
```bash
# Temporarily rename directory
mv ~/Smart_Logistics_Kit-22-map ~/Smart_Logistics_Kit-22-map.backup

# Start workflow
```

**Expected Result:**
- Log shows: "[ERROR] Smart Logistics directory not found"
- Current node turns red
- Workflow stops

```bash
# Restore directory
mv ~/Smart_Logistics_Kit-22-map.backup ~/Smart_Logistics_Kit-22-map
```

## Troubleshooting

### Issue: UI doesn't start

**Check:**
```bash
# Python version
python3 --version  # Should be 3.6+

# PyQt5 installed
python3 -c "from PyQt5 import QtWidgets"

# Display available
echo $DISPLAY  # Should show :0 or similar
```

**Fix:**
```bash
# Install PyQt5 if missing
pip3 install PyQt5

# Set display
export DISPLAY=:0
```

### Issue: Cameras show black

**Check:**
```bash
# Camera devices exist
ls -l /dev/video*

# No other process using cameras
sudo lsof /dev/video*
```

**Fix:**
```bash
# Release cameras
sudo fuser -k /dev/video*

# Restart UI
./start_ui.sh
```

### Issue: Node stays blue (doesn't turn green)

**Check:**
```bash
# Check ROS nodes running
rosnode list

# Check ROS topics
rostopic list

# Check for errors
rostopic echo /rosout
```

**Fix:**
- Check log output for specific error messages
- Verify ROS packages installed correctly
- Check hardware connections

### Issue: Workflow stops at specific node

**Node 1 fails:**
- Check: `rospack find myagv_odometry`
- Check: Lidar hardware connected
- Check: ROS master running

**Node 2 fails:**
- Check: `rospack find myagv_navigation`
- Check: Map files exist
- Check: Node 1 completed successfully

**Node 3 fails:**
- Check: `~/Smart_Logistics_Kit-22-map/main.py` exists
- Check: Python dependencies in Smart Logistics
- Check: File permissions (should be executable)

**Node 4/5 fail:**
- Check: Camera devices working
- Check: Mechanical arm connected
- Check: Navigation goals configured correctly

## Performance Monitoring

### Monitor ROS Nodes
```bash
# In separate terminal
watch -n 1 'rosnode list'
```

### Monitor System Resources
```bash
# CPU and memory
htop

# GPU (Jetson)
tegrastats
```

### Monitor Logs
```bash
# ROS logs
tail -f ~/.ros/log/latest/rosout.log

# UI logs (if configured)
tail -f ~/intelligent-logistics-system/logs/app.log
```

## Success Criteria

The integration is working correctly if:

- ✅ UI launches without errors
- ✅ Quick Start interface displays correctly
- ✅ Individual components (Lidar, Navigation) work
- ✅ Cameras display video feeds
- ✅ Quick Start button starts workflow
- ✅ All 5 nodes turn green in sequence
- ✅ Log shows detailed progress messages
- ✅ Workflow completes successfully
- ✅ Stop button terminates workflow cleanly
- ✅ UI closes without errors
- ✅ No zombie processes left running

## Test Report Template

```
Date: _______________
Tester: _______________
Jetson Model: _______________
ROS Version: _______________

Test Results:
[ ] Test 1: Basic UI Launch - PASS / FAIL
[ ] Test 2: Quick Start Interface - PASS / FAIL
[ ] Test 3: Individual Components - PASS / FAIL
[ ] Test 4: Full Workflow - PASS / FAIL
[ ] Test 5: Stop Workflow - PASS / FAIL
[ ] Test 6: Error Handling - PASS / FAIL

Notes:
_________________________________________________
_________________________________________________
_________________________________________________

Issues Found:
_________________________________________________
_________________________________________________
_________________________________________________
```

## Next Steps After Testing

If all tests pass:
1. Document any specific configuration needed for your setup
2. Create desktop shortcut for easy access
3. Train users on the workflow
4. Set up monitoring for production use

If tests fail:
1. Document specific error messages
2. Check hardware connections
3. Verify software dependencies
4. Review log files for details
5. Consult troubleshooting section

## Support

For issues or questions:
1. Check log output in UI
2. Review documentation files
3. Check ROS logs: `~/.ros/log/latest/`
4. Verify hardware connections
5. Test components individually

## Conclusion

This testing guide ensures the Smart Logistics workflow integration is working correctly on your Jetson system. Follow the tests in order, and document any issues for troubleshooting.
