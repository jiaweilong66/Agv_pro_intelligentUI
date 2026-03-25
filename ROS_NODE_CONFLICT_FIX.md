# ROS Node Conflict Fix

## Problem Description

When running the Smart Logistics workflow, you may encounter this error:

```
rospy.exceptions.ROSException: rospy.init_node() has already been called with different arguments
```

This happens because:
1. The UI initializes a ROS node named `intelligent_logistics_ui` when it starts
2. The `MapNavigation` class tries to initialize another node named `map_navigation`
3. ROS doesn't allow multiple `init_node()` calls in the same process

## Solution Applied

### 1. Fixed MapNavigation Class

Modified `functional/depend/navigation.py` to check if ROS node is already initialized:

```python
class MapNavigation(object, metaclass=Singleton):
    def __init__(self):
        # Check if ROS node is already initialized
        try:
            rospy.get_node_uri()
            # Node already initialized, skip init_node
        except rospy.exceptions.ROSException:
            # Node not initialized, initialize it
            rospy.init_node('map_navigation', anonymous=False)
```

### 2. Added Workflow Protection

Modified `on_move_to_shelf()` and `on_circular_sorting()` to prevent conflicts:
- These functions now check if Smart Logistics workflow is running
- If running, they show a warning and prevent execution
- This avoids ROS node conflicts

## Usage Guidelines

### When Running Smart Logistics Workflow

**DO:**
- ✅ Click "Quick Start" button
- ✅ Wait for all 5 nodes to complete
- ✅ Monitor progress in log output
- ✅ Click "Stop Workflow" if you need to stop

**DON'T:**
- ❌ Don't click "Move to Shelf" while workflow is running
- ❌ Don't click "Circular Sorting" while workflow is running
- ❌ Don't manually start Lidar/Navigation (workflow does this automatically)

### When Using Individual Functions

If you want to use individual functions like "Move to Shelf" or "Circular Sorting":

1. **Don't use Quick Start** - Use individual buttons instead
2. **Start Lidar first** - Click "Open/Close" under Lidar
3. **Start Navigation** - Click "Open/Close" under Navigation
4. **Then use individual functions** - Click "Move to Shelf" or "Circular Sorting"

## Why This Happens

### ROS Node Initialization Rules

In ROS, each Python process can only call `rospy.init_node()` once. If you try to call it again with different parameters, ROS throws an exception.

### Our Architecture

```
UI Process (intelligent_logistics_ui node)
    ├── Quick Start Workflow
    │   └── Launches subprocess (separate process, no conflict)
    │       └── Smart_Logistics_Kit-22-map/main.py
    │           └── Can initialize its own ROS node
    │
    └── Individual Functions (same process)
        ├── Move to Shelf
        │   └── Uses MapNavigation (needs ROS node)
        └── Circular Sorting
            └── Uses MapNavigation (needs ROS node)
```

### The Fix

1. **MapNavigation** now checks if node exists before initializing
2. **Individual functions** are blocked when workflow is running
3. **Subprocess isolation** - Smart Logistics runs in separate process

## Testing

### Test 1: Smart Logistics Workflow Only

```bash
./start_ui.sh
# Click "Quick Start" in main menu
# Click "Quick Start" button
# Wait for completion
# ✅ Should work without errors
```

### Test 2: Individual Functions Only

```bash
./start_ui.sh
# Click "Quick Start" in main menu
# Click "Open/Close" under Lidar
# Click "Open/Close" under Navigation
# Click "Move to Shelf"
# ✅ Should work without errors
```

### Test 3: Conflict Prevention

```bash
./start_ui.sh
# Click "Quick Start" in main menu
# Click "Quick Start" button (workflow starts)
# Try to click "Move to Shelf"
# ✅ Should show warning: "Smart Logistics workflow is running"
```

## Error Messages

### If you see this error:

```
rospy.exceptions.ROSException: rospy.init_node() has already been called
```

**Solution:**
1. Stop the current workflow
2. Close and restart the UI
3. Use either workflow OR individual functions, not both simultaneously

### If you see this warning:

```
[WARNING] Smart Logistics workflow is running. Please wait for completion or stop it first.
```

**Solution:**
1. Wait for workflow to complete (all nodes green)
2. Or click "Stop Workflow" button
3. Then you can use individual functions

## Technical Details

### ROS Node Lifecycle

```
UI Starts
    ↓
init_ros_node() called
    ↓
ROS node "intelligent_logistics_ui" created
    ↓
[Option 1: Quick Start]
    ↓
SmartLogisticsProcess starts
    ↓
Subprocess launched (separate process)
    ↓
Smart_Logistics_Kit-22-map/main.py runs
    ↓
Can initialize its own ROS node (no conflict)

[Option 2: Individual Functions]
    ↓
MapNavigation created
    ↓
Checks if node exists (yes, it does)
    ↓
Skips init_node(), uses existing node
    ↓
Works correctly
```

### Why Subprocess Works

The Smart Logistics workflow runs in a subprocess:
- Separate memory space
- Separate ROS node
- No conflict with parent process

Individual functions run in the same process:
- Share memory with UI
- Share ROS node with UI
- Must check before initializing

## Best Practices

### For Users

1. **Choose your workflow:**
   - Use Quick Start for complete automation
   - Use individual buttons for manual control
   - Don't mix them

2. **If you get errors:**
   - Restart the UI
   - Choose one approach and stick with it

3. **Monitor the logs:**
   - Watch for warning messages
   - Check node status in log output

### For Developers

1. **Always check before init_node:**
   ```python
   try:
       rospy.get_node_uri()
       # Already initialized
   except rospy.exceptions.ROSException:
       rospy.init_node('node_name')
   ```

2. **Use subprocesses for isolation:**
   - External programs should run in subprocess
   - This prevents ROS node conflicts

3. **Add workflow state checks:**
   - Check if other processes are running
   - Prevent conflicting operations

## Summary

The ROS node conflict has been fixed by:
1. Making MapNavigation check for existing node
2. Preventing individual functions during workflow
3. Using subprocess isolation for Smart Logistics

Users should either use Quick Start OR individual functions, not both at the same time.

---

## 中文说明

### 问题描述

运行智慧物流工作流程时可能遇到此错误：

```
rospy.exceptions.ROSException: rospy.init_node() has already been called with different arguments
```

### 原因

1. UI启动时初始化了名为 `intelligent_logistics_ui` 的ROS节点
2. `MapNavigation` 类尝试初始化另一个名为 `map_navigation` 的节点
3. ROS不允许在同一进程中多次调用 `init_node()`

### 解决方案

1. **修复了MapNavigation类** - 现在会检查节点是否已存在
2. **添加了工作流程保护** - 工作流程运行时阻止个别功能
3. **使用子进程隔离** - Smart Logistics在独立进程中运行

### 使用指南

**运行智慧物流工作流程时：**
- ✅ 点击"快速启动"按钮
- ✅ 等待所有5个节点完成
- ❌ 不要点击"移动到货架"
- ❌ 不要点击"循环分拣"

**使用单独功能时：**
1. 不要使用快速启动
2. 先启动雷达
3. 再启动导航
4. 然后使用单独功能

### 如果遇到错误

1. 停止当前工作流程
2. 关闭并重启UI
3. 选择使用工作流程或单独功能，不要同时使用
