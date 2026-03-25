# 智慧物流系统 - 新版UI

## 快速开始

### Windows用户
双击运行：
```
run_new_ui.bat
```

### Linux/Mac用户
```bash
python new_ui/main_app.py
```

## 主要功能

### 🚀 快速启动
一键执行完整的智慧物流任务流程，包括：
1. 启动雷达和导航
2. 导航到货架
3. 停车充电
4. 任务完成

### 🎮 硬件控制
- **Lidar**：激光雷达开关
- **Navigation**：导航系统开关
- **Joystick/Keyboard**：手柄/键盘控制

### 📦 物流任务
- **Move to Shelf**：移动到货架
- **Circular Sorting**：循环分拣

### 👁️ 视觉识别
- **ARUCO Code Detect**：ARUCO码识别
- **QR Code Detect**：QR码识别

### 📹 相机显示
- **Mech 270 Camera**：270机械臂相机
- **AGV 2D Camera**：AGV小车相机

### 📊 任务进度
底部5个节点实时显示任务执行状态：
- 🔵 蓝色：等待执行
- 🟢 绿色：已完成
- 🔴 红色：执行失败

## 界面说明

```
┌─────────────────────────────────────────────────────────────┐
│ [Intelligent Logistics System]  [Language Selection] [中文] │
├──────────────────┬──────────────────────────────────────────┤
│ 左侧控制面板      │          右侧显示区域                     │
│                  │                                          │
│ • Quick Start    │  ┌──────────┬──────────┐                │
│ • Lidar          │  │ Mech 270 │ AGV 2D   │                │
│ • Navigation     │  │ Camera   │ Camera   │                │
│ • Tasks          │  └──────────┴──────────┘                │
│ • Vision         │                                          │
│ • Motion Control │  ┌────────────────────┐                 │
│                  │  │ Log Output         │                 │
│                  │  │                    │                 │
│                  │  └────────────────────┘                 │
│                  │  [Log Clear]                            │
├──────────────────┴──────────────────────────────────────────┤
│ [○] → [○] → [○] → [○] → [○]  任务进度                       │
└─────────────────────────────────────────────────────────────┘
```

## 操作流程

### 方式一：快速启动（推荐）
1. 点击 **Quick Start** 按钮
2. 系统自动执行所有步骤
3. 观察底部进度条和日志输出
4. 等待任务完成

### 方式二：手动操作
1. 点击 **Lidar - Open/Close** 启动雷达
2. 点击 **Navigation - Open/Close** 启动导航
3. 点击 **Move to Shelf** 执行移动任务
4. 或点击 **Circular Sorting** 执行分拣任务

### 方式三：视觉识别测试
1. 确保雷达已启动
2. 点击 **ARUCO Code Detect** 或 **QR Code Detect**
3. 将码放在相机前
4. 查看识别结果

## 按钮颜色说明

- 🔵 **蓝色**：标准功能按钮（默认状态）
- 🟢 **绿色**：执行类按钮（Move to Shelf, Circular Sorting等）
- 🔴 **红色**：功能正在运行中
- ⚪ **白色**：返回主菜单按钮

## 常见问题

### Q: 启动失败怎么办？
A: 检查以下几点：
1. Python版本是否为3.7+
2. 是否安装了依赖：`pip install -r requirements_windows.txt`
3. 硬件是否正确连接

### Q: 相机无法显示？
A: 检查：
1. 相机是否正确连接
2. 设备权限是否正确
3. 查看日志输出的错误信息

### Q: 雷达启动失败？
A: 确保：
1. ROS环境已正确安装
2. 雷达硬件已连接
3. 有足够的系统权限

### Q: 如何返回主菜单？
A: 点击顶部的 **Intelligent Logistics System** 按钮

## 技术特点

- ✅ 完全集成原main.py的所有功能
- ✅ 现代化的UI设计
- ✅ 实时任务进度显示
- ✅ 双相机同时显示
- ✅ 中英文切换
- ✅ 完善的错误提示

## 文档

- [完整集成说明](NEW_UI_INTEGRATION_GUIDE.md)
- [快速启动指南](QUICK_START_UI_GUIDE.md)
- [原系统文档](README.md)

## 系统要求

- Python 3.7+
- PyQt5
- OpenCV
- ROS (用于导航和雷达)
- 其他依赖见 requirements_windows.txt

## 开发者

基于原 `main.py` 完全重构，保留所有功能接口。

---

**提示**：首次使用建议先阅读 [NEW_UI_INTEGRATION_GUIDE.md](NEW_UI_INTEGRATION_GUIDE.md) 了解详细功能说明。
