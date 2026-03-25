# Quick Reference Card - Smart Logistics Integration

## One-Page Quick Reference

### Start the System

```bash
cd ~/intelligent-logistics-system
./start_with_ros.sh
```

### Use Quick Start

1. Click "Quick Start" in main menu
2. Click "Quick Start" button (top left)
3. Watch nodes turn green: 1 → 2 → 3 → 4 → 5
4. Wait for "[SUCCESS]" message

### Task Nodes Meaning

| Node | Label | Meaning |
|------|-------|---------|
| 1 | Proceed to loading | Odometry launched |
| 2 | Pick goods | Navigation launched |
| 3 | Proceed to unloading | Main program started |
| 4 | Unload goods | myAGV navigating |
| 5 | Success | Workflow complete |

### Node Colors

- 🔵 Blue (...) = Waiting/In Progress
- 🟢 Green (✓) = Completed
- 🔴 Red (✗) = Error

### Common Commands

```bash
# Start roscore
roscore &

# Release cameras
sudo fuser -k /dev/video*

# Check ROS nodes
rosnode list

# Kill all ROS nodes
rosnode kill -a

# View ROS logs
tail -f ~/.ros/log/latest/rosout.log

# Restart roscore
killall -9 roscore rosmaster
roscore &
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| UI won't start | `export DISPLAY=:0` |
| ROS error | Start roscore first |
| Black cameras | `sudo fuser -k /dev/video*` |
| Node stuck | Check log output |
| Can't stop | Close UI window |

### File Locations

- UI: `~/intelligent-logistics-system/`
- Smart Logistics: `~/Smart_Logistics_Kit-22-map/`
- ROS logs: `~/.ros/log/latest/`
- Documentation: `~/intelligent-logistics-system/*.md`

### Workflow Steps

```
User clicks button
    ↓
Launch odometry (5s) → Node 1 ✓
    ↓
Launch navigation (10s) → Node 2 ✓
    ↓
Start main.py → Node 3 ✓
    ↓
Navigate → Node 4 ✓
    ↓
Pick & sort → Node 5 ✓
    ↓
Complete!
```

### Expected Duration

- Initialization: ~20 seconds
- Full workflow: 5-30 minutes
- Node 1: ~5 seconds
- Node 2: ~10 seconds
- Node 3-5: Variable

### Prerequisites

✅ ROS installed and sourced
✅ roscore running
✅ Smart_Logistics_Kit-22-map exists
✅ Cameras available (/dev/video0, /dev/video1)
✅ Mechanical arm connected (/dev/ttyACM0)

### Quick Test

```bash
# Test 1: Check directory
ls ~/Smart_Logistics_Kit-22-map/main.py

# Test 2: Check ROS
rospack find myagv_odometry
rospack find myagv_navigation

# Test 3: Check cameras
ls /dev/video*

# Test 4: Start UI
./start_ui.sh

# Test 5: Click Quick Start
# All nodes should turn green
```

### Stop Workflow

- Click "Stop Workflow" button
- Or close UI window
- All processes auto-cleanup

### Documentation

- `SMART_LOGISTICS_INTEGRATION.md` - Full details
- `智慧物流集成说明.md` - Chinese guide
- `JETSON_TEST_GUIDE.md` - Testing guide
- `WORKFLOW_DIAGRAM.md` - Visual diagrams

### Support Checklist

Before asking for help:
1. ✅ Check log output in UI
2. ✅ Check ROS logs
3. ✅ Verify roscore running
4. ✅ Verify hardware connected
5. ✅ Test components individually

### Success Indicators

✅ All 5 nodes green with ✓
✅ Log shows "[SUCCESS]"
✅ Button returns to "Quick Start"
✅ No error messages
✅ Processes cleanup cleanly

---

## 中文快速参考

### 启动系统
```bash
cd ~/intelligent-logistics-system
./start_with_ros.sh
```

### 使用快速启动
1. 点击主菜单的"快速启动"
2. 点击"快速启动"按钮
3. 观察节点变绿: 1 → 2 → 3 → 4 → 5
4. 等待"[SUCCESS]"消息

### 节点含义
1. 前往装货区 - 里程计启动
2. 拾取货物 - 导航启动
3. 前往卸货区 - 主程序启动
4. 卸载货物 - myAGV导航中
5. 成功 - 工作流程完成

### 常用命令
```bash
# 启动roscore
roscore &

# 释放摄像头
sudo fuser -k /dev/video*

# 检查ROS节点
rosnode list

# 查看日志
tail -f ~/.ros/log/latest/rosout.log
```

### 故障排除
| 问题 | 解决方案 |
|------|----------|
| UI无法启动 | `export DISPLAY=:0` |
| ROS错误 | 先启动roscore |
| 摄像头黑屏 | `sudo fuser -k /dev/video*` |
| 节点卡住 | 查看日志输出 |

---

**Print this page for quick reference during testing!**
