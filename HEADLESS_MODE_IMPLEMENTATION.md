# Headless模式实现说明

## 问题解决

你希望使用Smart_Logistics_Kit-22-map/main.py但不启动新的UI界面。

## 解决方案

### 1. 修改Smart_Logistics_Kit-22-map/main.py

添加了headless模式支持：

```python
def main(debug: bool = Config.debug, headless: bool = False):
    if headless:
        # Headless模式 - 运行Smart Logistics工作流但不显示UI
        print("[HEADLESS] Starting Smart Logistics in headless mode...")
        
        # 初始化ROS节点
        if ROS_AVAILABLE:
            if not init_ros_node():
                print("[ERROR] Failed to initialize ROS node. Is roscore running?")
                sys.exit(1)
        
        # 直接运行Smart Logistics进程
        from functional.process import SmartLogisticsProcess
        
        # 创建最小的QCoreApplication用于Qt功能
        app = QCoreApplication(sys.argv)
        
        # 创建并启动Smart Logistics进程
        process = SmartLogisticsProcess()
        process.finished.connect(lambda: app.quit())
        process.published.connect(lambda msg: print(f"[HEADLESS] {msg}"))
        process.start()
        
        # 运行事件循环
        sys.exit(app.exec_())
    else:
        # 正常UI模式
        # ... 原有的UI代码
```

### 2. 添加命令行参数支持

```python
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Logistics System')
    parser.add_argument('--headless', action='store_true', 
                       help='Run in headless mode without UI')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    main(debug=args.debug, headless=args.headless)
```

### 3. 修改test_full_workflow.sh

```bash
# 使用headless模式运行
setsid python3 main.py --headless
```

## 优势

### ✅ 使用完整的Smart Logistics功能
- 使用main.py中的完整SmartLogisticsProcess
- 包含所有UI中的智慧物流逻辑
- 支持所有摄像头和传感器功能

### ✅ 不启动UI界面
- 使用QCoreApplication而不是QApplication
- 不创建MainApplication窗口
- 不显示任何UI界面

### ✅ 保持所有功能
- ROS节点初始化
- 摄像头资源管理
- 进程间通信
- 错误处理和日志

### ✅ 命令行控制
- 支持--headless参数
- 支持--debug参数
- 可以扩展更多参数

## 使用方法

### 1. 正常UI模式（原有功能）
```bash
cd Smart_Logistics_Kit-22-map
python3 main.py
```

### 2. Headless模式（新功能）
```bash
cd Smart_Logistics_Kit-22-map
python3 main.py --headless
```

### 3. 通过test_full_workflow.sh（推荐）
```bash
./test_full_workflow.sh
```
脚本会自动使用headless模式运行Smart Logistics。

## 工作流程

1. **用户点击快速启动**
2. **主UI释放摄像头资源**
3. **启动Lidar和Navigation**（按钮变红）
4. **test_full_workflow.sh启动**
5. **运行main.py --headless**
   - 不显示UI界面
   - 直接运行SmartLogisticsProcess
   - 输出日志到控制台
6. **完成后自动退出**

## 日志输出

Headless模式会在控制台输出详细日志：
```
[HEADLESS] Starting Smart Logistics in headless mode...
[HEADLESS] Starting Smart Logistics workflow...
[HEADLESS] [STEP 1/5] Opening Lidar odometry system...
[HEADLESS] [STEP 2/5] Opening navigation system...
[HEADLESS] [STEP 3/5] Starting Smart Logistics main program...
[HEADLESS] Smart Logistics workflow completed
```

## 故障排除

### 如果出现"No module named 'functional.process'"错误：
确保在Smart_Logistics_Kit-22-map目录中运行：
```bash
cd Smart_Logistics_Kit-22-map
python3 main.py --headless
```

### 如果出现ROS相关错误：
确保roscore正在运行：
```bash
roscore
```

### 如果需要调试：
使用debug模式：
```bash
python3 main.py --headless --debug
```

## 总结

现在你可以：
- ✅ 使用完整的Smart Logistics功能（main.py）
- ✅ 不启动额外的UI界面（headless模式）
- ✅ 保持所有原有功能和逻辑
- ✅ 通过命令行参数控制行为
- ✅ 获得详细的控制台日志输出

这个解决方案完美结合了你的需求：使用main.py的完整功能，但不显示UI界面。