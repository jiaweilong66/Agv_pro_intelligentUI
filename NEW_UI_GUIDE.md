# 智慧物流系统 UI 使用指南

## 概述
这是一个全新设计的智慧物流系统用户界面，提供了直观的操作体验和完整的功能控制。

## 启动方式
```bash
python new_ui/main_app.py
```

或使用批处理文件：
```bash
run_ui_demo.bat
```

## 界面布局

### 顶部标题栏
- **系统标题**: Intelligent Logistics System
- **语言选择**: 支持中英文切换（English / 中文）

### 左侧控制面板

#### 1. Intelligent Logistics Task（智慧物流任务）
- **Quick Start 按钮**: 一键启动完整的智慧物流流程
- **任务进度条**: 显示5个任务节点的执行状态
  - 节点1: Proceed to loading（前往装载区）
  - 节点2: Pick goods（拾取货物）
  - 节点3: Proceed to unloading（前往卸载区）
  - 节点4: Unload goods（卸载货物）
  - 节点5: Success（任务完成）
  
  **状态指示**:
  - 🔵 蓝色（...）: 等待执行
  - 🟢 绿色（✓）: 已完成
  - 🔴 红色（✗）: 执行失败

#### 2. Lidar（激光雷达）
- **Open/Close 按钮**: 启动/关闭激光雷达里程计
- 启动后按钮变为红色"Close"状态

#### 3. Navigation（导航）
- **Open/Close 按钮**: 启动/关闭导航系统
- 启动后加载地图并初始化定位

#### 4. Intelligent Logistics Tasks（智慧物流任务）
- **Move to Shelf**: 机器人移动到货架前
- **Circular Sorting**: 持续循环执行分拣任务

#### 5. Visual Functional（视觉识别功能）
- **ARUCO Code Detect**: 启动ARUCO码识别算法
- **QR Code Detect**: 启动QR码识别算法

#### 6. Motion Control（运动控制）
- **Open Joystick Control**: 打开手柄控制
- **Open Keyboard Control**: 打开键盘控制

### 右侧显示面板

#### 相机画面显示
- **Mech 270 Camera View**: 270-M5机械臂相机画面
- **AGV 2D Camera View**: AGV小车相机画面
- 当程序调用摄像头时，画面会自动显示在对应区域

#### 日志输出
- 显示所有程序运行信息
- 包括任务进度、系统状态、错误信息等
- **Log Clear 按钮**: 清除日志内容

## 功能说明

### 快速启动任务流程
1. 点击"Quick Start"按钮
2. 系统自动执行完整的物流任务流程
3. 任务进度条实时显示当前执行状态
4. 日志区域输出详细的执行信息
5. 所有节点完成后任务自动结束

### 激光雷达操作
1. 点击"Open/Close"启动激光雷达
2. 按钮变红表示雷达正在运行
3. 再次点击关闭雷达

### 视觉识别
1. 点击对应的检测按钮启动算法
2. 按钮变红并显示"Stop"状态
3. 摄像头画面会显示在右侧区域
4. 再次点击停止检测

### 运动控制
- 选择手柄或键盘控制方式
- 使用对应的输入设备控制机器人移动

## 按钮颜色说明
- 🔵 **蓝色**: 标准功能按钮
- 🟢 **绿色**: 执行/确认类按钮（Move to Shelf, Circular Sorting, Motion Control, Log Clear）
- 🔴 **红色**: 运行中/停止按钮（Lidar, Navigation, Vision Detection）

## 日志信息类型
- `[INFO]`: 一般信息
- `[SYSTEM]`: 系统消息
- `[TASK]`: 任务执行信息
- `[LIDAR]`: 激光雷达相关
- `[NAVIGATION]`: 导航相关
- `[VISION]`: 视觉识别相关
- `[CONTROL]`: 运动控制相关
- `[SORTING]`: 分拣任务相关

## 技术特点
- 基于 PyQt5 开发
- 模块化设计，易于扩展
- 实时状态反馈
- 友好的用户界面
- 支持多语言切换

## 注意事项
1. 确保已安装所有依赖：`pip install -r requirements_windows.txt`
2. 某些功能需要硬件支持（摄像头、激光雷达等）
3. 日志信息会持续累积，建议定期清除
4. 任务执行过程中请勿关闭程序

## 未来扩展
- [ ] 实际硬件集成
- [ ] 完整的语言国际化
- [ ] 相机画面实时显示
- [ ] 任务自动化脚本
- [ ] 数据统计和分析
