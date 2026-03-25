# Smart Logistics Workflow Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Intelligent Logistics UI                      │
│                      (new_ui/main_app.py)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ User clicks "Quick Start"
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              on_quick_start_task()                               │
│  • Check ROS node initialized                                    │
│  • Reset task nodes to waiting state                             │
│  • Call start_smart_logistics_workflow()                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│         SmartLogisticsProcess (QThread)                          │
│              (functional/process.py)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────┴─────────────────────┐
        │                                             │
        ▼                                             ▼
┌──────────────────┐                    ┌──────────────────────┐
│  STEP 1: Launch  │                    │   Progress Signals   │
│    Odometry      │────────────────────▶│  published.emit()    │
│  (5s wait)       │                    │                      │
└──────────────────┘                    └──────────────────────┘
        │                                             │
        ▼                                             ▼
┌──────────────────┐                    ┌──────────────────────┐
│  STEP 2: Launch  │                    │ on_smart_logistics_  │
│   Navigation     │────────────────────▶│    published()       │
│  (10s wait)      │                    │  • Update task nodes │
└──────────────────┘                    │  • Log messages      │
        │                                └──────────────────────┘
        ▼
┌──────────────────┐
│  STEP 3: Execute │
│  main.py from    │
│  Smart_Logistics │
│  Kit-22-map      │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  STEP 4: myAGV   │
│  Navigates to    │
│  Positions       │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  STEP 5: 270 Arm │
│  Vision Picking  │
│  & Sorting       │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│   Cleanup All    │
│   Processes      │
└──────────────────┘
```

## Task Node State Flow

```
Initial State:
┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
│ ... │───│ ... │───│ ... │───│ ... │───│ ... │
│  1  │   │  2  │   │  3  │   │  4  │   │  5  │
└─────┘   └─────┘   └─────┘   └─────┘   └─────┘
 Blue      Blue      Blue      Blue      Blue

After STEP 1 (Odometry Launched):
┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
│  ✓  │───│ ... │───│ ... │───│ ... │───│ ... │
│  1  │   │  2  │   │  3  │   │  4  │   │  5  │
└─────┘   └─────┘   └─────┘   └─────┘   └─────┘
 Green     Blue      Blue      Blue      Blue

After STEP 2 (Navigation Launched):
┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
│  ✓  │───│  ✓  │───│ ... │───│ ... │───│ ... │
│  1  │   │  2  │   │  3  │   │  4  │   │  5  │
└─────┘   └─────┘   └─────┘   └─────┘   └─────┘
 Green     Green     Blue      Blue      Blue

After STEP 3 (Main Program Started):
┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
│  ✓  │───│  ✓  │───│  ✓  │───│ ... │───│ ... │
│  1  │   │  2  │   │  3  │   │  4  │   │  5  │
└─────┘   └─────┘   └─────┘   └─────┘   └─────┘
 Green     Green     Green     Blue      Blue

After STEP 4 (Navigation Active):
┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
│  ✓  │───│  ✓  │───│  ✓  │───│  ✓  │───│ ... │
│  1  │   │  2  │   │  3  │   │  4  │   │  5  │
└─────┘   └─────┘   └─────┘   └─────┘   └─────┘
 Green     Green     Green     Green     Blue

After STEP 5 (Complete Success):
┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
│  ✓  │───│  ✓  │───│  ✓  │───│  ✓  │───│  ✓  │
│  1  │   │  2  │   │  3  │   │  4  │   │  5  │
└─────┘   └─────┘   └─────┘   └─────┘   └─────┘
 Green     Green     Green     Green     Green
```

## Process Communication Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    Main UI Thread                             │
│  • Handles user input                                         │
│  • Updates UI elements                                        │
│  • Displays log messages                                      │
└──────────────────────────────────────────────────────────────┘
                    ▲                    ▲
                    │                    │
         published  │                    │ finished
          signal    │                    │ signal
                    │                    │
┌──────────────────────────────────────────────────────────────┐
│              SmartLogisticsProcess Thread                     │
│  • Launches subprocesses                                      │
│  • Monitors progress                                          │
│  • Emits progress signals                                     │
│  • Handles cleanup                                            │
└──────────────────────────────────────────────────────────────┘
                    │
                    │ subprocess.Popen
                    │
        ┌───────────┴───────────┬───────────────┐
        ▼                       ▼               ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  roslaunch   │    │  roslaunch   │    │   python3    │
│  myagv_      │    │  myagv_      │    │   main.py    │
│  odometry    │    │  navigation  │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

## File Structure

```
intelligent-logistics-system/
│
├── new_ui/
│   ├── main_app.py                    ← Modified: Quick Start integration
│   ├── main_menu.ui
│   ├── quick_start.ui
│   └── virtual_controller.ui
│
├── functional/
│   ├── process.py                     ← Modified: Added SmartLogisticsProcess
│   ├── roslaunch.py
│   ├── detector.py
│   └── joystick.py
│
├── start_ui.sh                        ← Launch script
├── start_with_ros.sh                  ← Launch with auto-roscore
│
├── SMART_LOGISTICS_INTEGRATION.md    ← New: Detailed documentation
├── 智慧物流集成说明.md                  ← New: Chinese documentation
├── INTEGRATION_SUMMARY.md             ← New: Summary
└── WORKFLOW_DIAGRAM.md                ← New: This file

External dependency:
~/Smart_Logistics_Kit-22-map/
└── main.py                            ← Executed by workflow
```

## Signal Flow Diagram

```
User Action                 Process                    UI Update
───────────                ─────────                  ──────────

Click "Quick Start"
      │
      ├──────────────▶ Initialize ROS node
      │                      │
      │                      ├──────────────▶ Show "Initializing..."
      │                      │
      ├──────────────▶ Start SmartLogisticsProcess
      │                      │
      │                      ├──────────────▶ Button: "Stop Workflow"
      │                      │                Node 1: Blue (...)
      │                      │
      │               Launch odometry
      │                      │
      │                      ├──────────────▶ Log: "[STEP 1/5]..."
      │                      │                Node 1: Green (✓)
      │                      │
      │               Launch navigation
      │                      │
      │                      ├──────────────▶ Log: "[STEP 2/5]..."
      │                      │                Node 2: Green (✓)
      │                      │
      │               Execute main.py
      │                      │
      │                      ├──────────────▶ Log: "[STEP 3/5]..."
      │                      │                Node 3: Green (✓)
      │                      │
      │               myAGV navigates
      │                      │
      │                      ├──────────────▶ Log: "[STEP 4/5]..."
      │                      │                Node 4: Green (✓)
      │                      │
      │               Arm picks & sorts
      │                      │
      │                      ├──────────────▶ Log: "[STEP 5/5]..."
      │                      │                Node 5: Green (✓)
      │                      │
      │               Cleanup processes
      │                      │
      │                      ├──────────────▶ Log: "[SUCCESS]..."
      │                      │                Button: "Quick Start"
      │                      │
      │               Process finished
      │                      │
      │                      └──────────────▶ All nodes green
```

## Error Handling Flow

```
Error Condition                Action                      UI Response
───────────────               ──────                      ───────────

ROS not initialized
      │
      ├──────────────▶ Show error dialog
      │                      │
      │                      └──────────────▶ "Please start roscore"
      │                                       Button remains "Quick Start"

Smart Logistics dir missing
      │
      ├──────────────▶ Log error message
      │                      │
      │                      └──────────────▶ "[ERROR] Directory not found"
      │                                       Current node: Red (✗)

Process launch fails
      │
      ├──────────────▶ Cleanup launched processes
      │                      │
      │                      └──────────────▶ "[ERROR] Launch failed"
      │                                       Current node: Red (✗)
      │                                       Button: "Quick Start"

User clicks "Stop"
      │
      ├──────────────▶ Terminate all processes
      │                      │
      │                      └──────────────▶ "[CLEANUP] Stopping..."
      │                                       Button: "Quick Start"
      │                                       Nodes reset to blue
```

## Subprocess Management

```
SmartLogisticsProcess
        │
        ├─── subprocess.Popen (odometry)
        │         │
        │         ├─── roslaunch process
        │         │         │
        │         │         └─── ROS nodes (lidar, odometry, etc.)
        │         │
        │         └─── Cleanup: SIGTERM → wait → SIGKILL
        │
        ├─── subprocess.Popen (navigation)
        │         │
        │         ├─── roslaunch process
        │         │         │
        │         │         └─── ROS nodes (map, amcl, move_base, etc.)
        │         │
        │         └─── Cleanup: SIGTERM → wait → SIGKILL
        │
        └─── subprocess.Popen (main.py)
                  │
                  ├─── Python process
                  │         │
                  │         └─── Smart logistics logic
                  │
                  └─── Cleanup: SIGTERM → wait → SIGKILL
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    Original main.py                          │
│  • Camera handling                                           │
│  • Process management                                        │
│  • ROS integration                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Reused components
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  new_ui/main_app.py                          │
│  • Inherits camera handling                                  │
│  • Extends process management                                │
│  • Adds Smart Logistics workflow                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ New integration
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            SmartLogisticsProcess                             │
│  • Launches external workflow                                │
│  • Reports progress                                          │
│  • Manages subprocesses                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Executes
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         ~/Smart_Logistics_Kit-22-map/main.py                 │
│  • Complete logistics workflow                               │
│  • Navigation + Vision + Sorting                             │
└─────────────────────────────────────────────────────────────┘
```

## Summary

This diagram shows how the Smart Logistics workflow is integrated into the Quick Start interface through:

1. **UI Layer**: User interaction and visual feedback
2. **Process Layer**: Thread management and subprocess control
3. **ROS Layer**: Launch files and node management
4. **Application Layer**: Smart Logistics main program execution

The integration maintains clean separation of concerns while providing seamless user experience.
