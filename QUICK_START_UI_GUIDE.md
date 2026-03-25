# 智慧物流系统 - 快速启动界面使用指南

## 启动方式
```bash
python new_ui/main_app.py
```

## 界面说明

### 顶部标题栏
- **Intelligent Logistics System** 按钮：点击返回主菜单（三选一界面）
- **Language Selection**：语言选择下拉框（English / 中文）

### 左侧控制面板

#### 1. Intelligent Logistics Task
- **Quick Start** 按钮：启动完整的智慧物流任务流程
- 点击后会自动执行5个任务节点，每2秒完成一个节点

#### 2. Lidar（激光雷达）
- **Open/Close** 按钮：开启/关闭激光雷达里程计
- 开启后按钮变红色

#### 3. Navigation（导航）
- **Open/Close** 按钮：开启/关闭导航系统
- 开启后按钮变红色

#### 4. Intelligent Logistics Tasks（智慧物流任务）
- **Move to Shelf**：机器人移动到货架
- **Circular Sorting**：循环分拣任务
- 两个按钮都是绿色

#### 5. Visual Functional（视觉功能）
- **ARUCO Code Detect**：ARUCO码识别
- **QR Code Detect**：QR码识别
- 点击后按钮变红色并显示"Stop"

#### 6. Motion Control（运动控制）
- **Open Joystick Control**：打开手柄控制
- **Open Keyboard Control**：打开键盘控制
- 两个按钮都是绿色

### 右侧显示面板

#### 相机显示区域
- **Mech 270 Camera View**：270机械臂相机画面
- **AGV 2D Camera View**：AGV小车相机画面

#### 日志区域
- 黑色背景的日志输出窗口
- 显示所有操作的详细信息
- **Log Clear** 按钮：清除日志（绿色按钮）

### 底部进度条

显示5个任务节点的执行状态：

1. **Proceed to the loading**（前往装载区）
2. **Pick goods**（拾取货物）
3. **Proceed to the unloading**（前往卸载区）
4. **Unload goods**（卸载货物）
5. **Success**（任务成功）

**状态指示**：
- 🟢 绿色圆圈 + ✓：任务已完成
- 🔵 蓝色圆圈 + ...：等待执行
- 🔴 红色圆圈 + ✗：执行失败

**连接线颜色**：
- 绿色：已完成的节点之间
- 灰色：未完成的节点之间

## 操作流程示例

### 快速启动完整任务
1. 点击左上角 **Quick Start** 按钮
2. 观察底部进度条，节点会依次变绿
3. 查看日志输出了解任务详情
4. 所有节点完成后任务自动结束

### 单独测试功能
1. 点击 **Lidar** 的 Open/Close 启动雷达
2. 点击 **Navigation** 的 Open/Close 启动导航
3. 点击 **ARUCO Code Detect** 启动视觉识别
4. 点击 **Move to Shelf** 执行移动任务
5. 查看日志了解每个功能的执行情况

### 返回主菜单
- 点击顶部的 **Intelligent Logistics System** 按钮
- 返回到三选一的主界面

## 按钮颜色说明
- 🔵 **蓝色**：标准功能按钮（Lidar, Navigation, Vision）
- 🟢 **绿色**：执行/确认按钮（Move to Shelf, Circular Sorting, Motion Control, Log Clear）
- 🔴 **红色**：运行中状态（功能激活后）
- ⚪ **白色**：返回按钮（Intelligent Logistics System）

## 注意事项
1. Quick Start 任务会自动执行，每个节点间隔2秒
2. 日志会持续累积，建议定期点击 Log Clear 清除
3. 某些功能需要硬件支持才能真正运行
4. 点击顶部标题可随时返回主菜单

## 技术特点
- 基于 PyQt5 开发
- 自动任务进度管理
- 实时日志输出
- 动态状态指示
- 简洁直观的界面设计
