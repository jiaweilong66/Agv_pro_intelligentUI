# Jetson快速启动指南

## 一键启动设置

### 步骤1：安装桌面快捷方式

在终端中运行：
```bash
cd /home/ubuntu/intelligent-logistics-system
chmod +x install_desktop_shortcut.sh
./install_desktop_shortcut.sh
```

### 步骤2：使用桌面图标

安装完成后，桌面上会出现"Intelligent Logistics System"图标。

**双击图标即可启动程序！**

如果图标无法启动：
1. 右键点击图标
2. 选择"允许启动"或"Allow Launching"

## 其他启动方式

### 方式1：Shell脚本
```bash
./run_new_ui.sh
```

### 方式2：Python直接启动
```bash
python3 start_new_ui.py
```

## 检查环境

运行环境检查脚本：
```bash
python3 check_environment.py
```

这会检查所有必需的依赖是否已安装。

## 文件说明

| 文件 | 说明 |
|------|------|
| `start_new_ui.py` | Python启动程序（推荐使用） |
| `run_new_ui.sh` | Shell启动脚本 |
| `install_desktop_shortcut.sh` | 桌面快捷方式安装脚本 |
| `check_environment.py` | 环境检查脚本 |
| `IntelligentLogistics.desktop` | 桌面快捷方式文件 |

## 界面功能

### 主菜单（3个按钮）
1. **Quick Start** - 快速启动智慧物流任务
2. **Virtual Controller** - 虚拟手柄控制
3. **Product Parameters** - 产品参数（开发中）

### 快速启动界面
- 左侧控制面板：
  - Intelligent Logistics Task（一键启动）
  - Lidar（激光雷达）
  - Navigation（导航建图）
  - Move to Shelf / Circular Sorting（任务）
  - ARUCO / QR Code Detect（视觉识别）
  - Joystick / Keyboard Control（控制方式）

- 右侧显示区域：
  - Mech 270 Camera View（机械臂相机）
  - AGV 2D Camera View（小车相机）
  - Log Output（日志输出）

- 底部任务进度：
  - 5个任务节点，显示当前进度
  - 蓝色=等待，绿色=完成，红色=错误

### 虚拟控制器界面
- **左侧遥感**：控制机械臂
  - 上/下：Y轴移动
  - 左/右：X轴移动

- **右侧遥感**：控制AGV小车
  - 上/下：前进/后退
  - 左/右：左转/右转

- **控制按钮**：
  - Gripper Open/Close（夹爪开合）
  - Pump On/Off（吸泵开关）
  - Lock Arm/Release Arm（机械臂锁定/释放）
  - Reset to Start Position（复位）

## 常见问题

### Q: 找不到模块错误
A: 确保在项目根目录运行，使用 `python3 start_new_ui.py`

### Q: 桌面图标不工作
A: 运行 `chmod +x run_new_ui.sh start_new_ui.py`

### Q: 相机无法打开
A: 检查相机连接，运行 `ls -l /dev/video*`

### Q: GPIO权限错误
A: 运行 `sudo usermod -a -G gpio,video,dialout $USER` 然后重启

## 详细文档

- `JETSON_INSTALLATION_GUIDE.md` - 完整安装指南
- `VIRTUAL_CONTROLLER_FUNCTIONS.md` - 虚拟控制器功能说明
- `QUICK_LAUNCH_GUIDE.md` - 快速启动指南

## 技术支持

如遇问题：
1. 运行 `python3 check_environment.py` 检查环境
2. 查看终端日志输出
3. 检查硬件连接
4. 参考详细文档

---

**现在就试试吧！双击桌面图标启动程序！**
