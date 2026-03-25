# Smart Logistics Workflow Integration Guide

## Overview

The complete Smart Logistics workflow from `~/Smart_Logistics_Kit-22-map/` has been integrated into the Quick Start interface. When you click the "Quick Start" button, it will automatically execute the full workflow including navigation, vision-based picking, and sorting.

## Workflow Architecture

### Process Flow

The Quick Start button now triggers the `SmartLogisticsProcess` which executes three main steps:

1. **Launch myAGV Odometry System**
   ```bash
   roslaunch myagv_odometry myagv_active.launch
   ```

2. **Launch Navigation System**
   ```bash
   roslaunch myagv_navigation simplify_logistics_navigation_active.launch
   ```

3. **Execute Smart Logistics Main Program**
   ```bash
   cd ~/Smart_Logistics_Kit-22-map/
   python3 main.py
   ```

### Task Progress Visualization

The 5 task progress nodes at the bottom of the Quick Start interface now map to the actual workflow stages:

- **Node 1: "Proceed to the loading"** - Odometry system launched, myAGV ready
- **Node 2: "Pick goods"** - Navigation system active, ready for picking
- **Node 3: "Proceed to the unloading"** - Smart logistics program started, navigating
- **Node 4: "Unload goods"** - 270 arm performing vision-based picking and sorting
- **Node 5: "Success"** - Complete workflow finished successfully

Each node changes color based on status:
- **Blue (...)**: Waiting/In Progress
- **Green (✓)**: Completed Successfully
- **Red (✗)**: Error Occurred

## Implementation Details

### New Process Class: `SmartLogisticsProcess`

Location: `functional/process.py`

This new process class handles:
- Sequential launching of ROS launch files
- Execution of the Smart_Logistics_Kit-22-map/main.py script
- Progress reporting through signals
- Proper cleanup of all subprocesses on termination

Key features:
- Uses `subprocess.Popen` to launch ROS nodes
- Monitors process status and reports progress
- Handles graceful shutdown with proper cleanup
- Reports errors and warnings to the UI

### Modified Quick Start Handler

Location: `new_ui/main_app.py` - `on_quick_start_task()`

Changes:
- Now starts `SmartLogisticsProcess` instead of just navigation
- Checks for ROS node initialization before starting
- Provides clear error messages if roscore is not running
- Button toggles between "Quick Start" and "Stop Workflow"

### Progress Tracking

Location: `new_ui/main_app.py` - `on_smart_logistics_published()`

The workflow reports progress through published messages:
- `[STEP 1/5]` - Odometry launch → Updates Node 1
- `[STEP 2/5]` - Navigation launch → Updates Node 2
- `[STEP 3/5]` - Main program start → Updates Node 3
- `[STEP 4/5]` - Navigation active → Updates Node 4
- `[STEP 5/5]` - Vision picking → Updates Node 5
- `[SUCCESS]` - Complete workflow → Final success state

## Usage Instructions

### Prerequisites

1. **ROS Environment**: Ensure ROS is properly installed and sourced
   ```bash
   source /opt/ros/melodic/setup.bash  # or your ROS version
   ```

2. **Smart Logistics Directory**: The directory must exist at:
   ```
   ~/Smart_Logistics_Kit-22-map/
   ```

3. **ROS Master**: Start roscore before launching the UI:
   ```bash
   roscore
   ```
   
   Or use the provided startup script that auto-starts roscore:
   ```bash
   ./start_with_ros.sh
   ```

### Running the Workflow

1. **Launch the UI**:
   ```bash
   ./start_ui.sh
   ```

2. **Click "Quick Start" button** in the Quick Start interface

3. **Monitor Progress**:
   - Watch the 5 task nodes change color as workflow progresses
   - Read detailed log messages in the log output area
   - Each step is clearly labeled with [STEP X/5] markers

4. **Stop if Needed**:
   - Click the "Stop Workflow" button to terminate
   - All processes will be cleanly shut down

### Expected Behavior

When the workflow runs successfully:

1. **Initialization** (5 seconds)
   - Odometry system launches
   - Node 1 turns green

2. **Navigation Setup** (10 seconds)
   - Navigation system launches
   - Node 2 turns green

3. **Smart Logistics Execution** (variable time)
   - Main program starts
   - myAGV navigates to designated positions
   - 270 mechanical arm performs vision-based object detection
   - Objects are picked and sorted
   - Nodes 3, 4, 5 turn green as tasks complete

4. **Completion**
   - All nodes green with checkmarks
   - Success message displayed
   - All processes cleanly terminated

## Troubleshooting

### Issue: "ROS node initialization error"

**Solution**: Start roscore before launching the UI
```bash
# Terminal 1
roscore

# Terminal 2
./start_ui.sh
```

### Issue: "Smart Logistics directory not found"

**Solution**: Verify the directory exists
```bash
ls ~/Smart_Logistics_Kit-22-map/
```

If missing, clone or copy the Smart_Logistics_Kit-22-map directory to your home folder.

### Issue: "main.py not found"

**Solution**: Check that main.py exists in the Smart Logistics directory
```bash
ls ~/Smart_Logistics_Kit-22-map/main.py
```

### Issue: Workflow stops at a specific node

**Check**:
1. ROS launch files are properly installed
2. Navigation maps are available
3. Camera devices are accessible
4. Mechanical arm is connected

**View detailed errors** in the log output area of the UI.

### Issue: Processes don't terminate cleanly

**Solution**: The workflow includes automatic cleanup, but if needed:
```bash
# Kill all ROS nodes
rosnode kill -a

# Or restart roscore
killall -9 roscore rosmaster
roscore
```

## Code Structure

### Files Modified

1. **functional/process.py**
   - Added `SmartLogisticsProcess` class
   - Handles subprocess management
   - Reports progress through signals

2. **new_ui/main_app.py**
   - Modified `on_quick_start_task()` to use new workflow
   - Added `start_smart_logistics_workflow()` method
   - Added `on_smart_logistics_published()` for progress tracking
   - Added `on_smart_logistics_finished()` for completion handling
   - Updated `closeEvent()` to cleanup smart logistics process

### Integration Points

The workflow integrates with existing UI components:
- **Log Browser**: All progress messages appear in real-time
- **Task Nodes**: Visual progress indication
- **Console Handler**: Detailed logging for debugging
- **Process Management**: Proper thread lifecycle management

## Advanced Configuration

### Customizing Workflow Steps

To modify the workflow, edit `functional/process.py` in the `SmartLogisticsProcess.process()` method:

```python
def process(self):
    # Modify launch commands here
    odometry_cmd = ["roslaunch", "myagv_odometry", "myagv_active.launch"]
    navigation_cmd = ["roslaunch", "myagv_navigation", "simplify_logistics_navigation_active.launch"]
    
    # Modify Smart Logistics path here
    smart_logistics_path = os.path.expanduser("~/Smart_Logistics_Kit-22-map")
```

### Adjusting Timing

Modify sleep delays in `SmartLogisticsProcess.process()`:

```python
time.sleep(5)   # Wait after odometry launch
time.sleep(10)  # Wait after navigation launch
```

### Adding Custom Steps

Add additional steps between existing ones:

```python
# After navigation launch
self.notify_published("[CUSTOM] Running custom initialization...")
# Your custom code here
self.notify_published("[CUSTOM] ✓ Custom step completed")
```

## Testing on Jetson

### Full System Test

1. Connect all hardware (cameras, arm, AGV)
2. Start roscore
3. Launch UI with `./start_ui.sh`
4. Click Quick Start
5. Verify all 5 nodes complete successfully

### Individual Component Test

Test each component separately:

```bash
# Test odometry
roslaunch myagv_odometry myagv_active.launch

# Test navigation
roslaunch myagv_navigation simplify_logistics_navigation_active.launch

# Test Smart Logistics
cd ~/Smart_Logistics_Kit-22-map/
python3 main.py
```

## Benefits of Integration

1. **One-Click Operation**: Complete workflow starts with single button click
2. **Visual Progress**: Real-time status updates through task nodes
3. **Error Handling**: Clear error messages and graceful failure handling
4. **Clean Shutdown**: All processes properly terminated on stop
5. **Logging**: Comprehensive logging for debugging and monitoring
6. **Reusable**: Can be triggered multiple times without restart

## Future Enhancements

Potential improvements:
- Add pause/resume functionality
- Implement workflow checkpoints
- Add configuration file for custom workflows
- Support multiple workflow profiles
- Add workflow recording and playback
- Integrate with remote monitoring

## Summary

The Smart Logistics workflow is now fully integrated into the Quick Start interface. Users can launch the complete workflow with a single button click, monitor progress through visual indicators, and view detailed logs in real-time. The implementation handles all subprocess management, error handling, and cleanup automatically.
