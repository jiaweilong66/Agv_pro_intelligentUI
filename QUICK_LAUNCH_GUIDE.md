# Quick Launch Guide

## 在Jetson上启动新UI界面

### 方法1：桌面快捷方式（推荐）

**首次安装：**
```bash
chmod +x install_desktop_shortcut.sh
./install_desktop_shortcut.sh
```

**使用：**
- 双击桌面上的"Intelligent Logistics System"图标

### 方法2：命令行启动

```bash
# 首次运行需要添加执行权限
chmod +x run_new_ui.sh

# 启动程序
./run_new_ui.sh
```

### 方法3：Python直接启动

```bash
python3 start_new_ui.py
```

## 常见问题

### 找不到模块 (ModuleNotFoundError)

确保在项目根目录运行：
```bash
cd /home/ubuntu/intelligent-logistics-system
python3 start_new_ui.py
```

### 桌面图标不工作

右键点击图标 → 选择"允许启动"

或运行：
```bash
chmod +x run_new_ui.sh
chmod +x start_new_ui.py
```

### 权限问题

```bash
# 添加用户到必要的组
sudo usermod -a -G video,gpio,dialout $USER
sudo reboot
```

## 界面说明

### 主菜单
- **Quick Start**: 快速启动智慧物流任务
- **Virtual Controller**: 虚拟手柄控制界面
- **Product Parameters**: 产品参数（开发中）

### 快速启动界面
- 激光雷达控制
- 导航系统控制
- 移动到货架
- 循环排序任务
- 视觉识别（ARUCO/QR码）
- 手柄/键盘控制
- 实时相机画面
- 任务进度显示
- 日志输出

### 虚拟控制器界面
- 左侧遥感：机械臂控制
- 右侧遥感：小车控制
- 夹爪开合
- 吸泵开关
- 机械臂锁定/释放
- 复位到初始位置

## 文件说明

- `start_new_ui.py` - 主启动程序
- `run_new_ui.sh` - Shell启动脚本
- `install_desktop_shortcut.sh` - 桌面快捷方式安装脚本
- `new_ui/main_app.py` - 主应用程序
- `new_ui/*.ui` - UI界面文件
- `JETSON_INSTALLATION_GUIDE.md` - 详细安装指南
