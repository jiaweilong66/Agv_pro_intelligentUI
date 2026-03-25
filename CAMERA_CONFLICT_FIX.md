# 摄像头冲突修复说明

## 问题描述
Smart Logistics在启动时出现摄像头资源冲突，导致程序卡死：
- GStreamer管道无法启动（CSI摄像头）
- USB摄像头被占用
- DBus连接错误

## 根本原因
1. **UI占用摄像头**：主UI在启动时初始化了AGV摄像头和Arm摄像头
2. **Smart Logistics需要相同摄像头**：test.py也需要使用这些摄像头资源
3. **资源冲突**：两个进程同时访问摄像头设备导致冲突

## 解决方案

### 1. 修改主UI快速启动逻辑
在`main.py`的`on_quick_start_handle()`方法中：
- 在启动Smart Logistics之前释放所有摄像头资源
- 确保AGV摄像头和Arm摄像头完全释放

### 2. 修改Smart Logistics摄像头初始化
在`Smart_Logistics_Kit-22-map/test.py`中：
- 添加5秒延迟等待UI释放摄像头资源
- 添加重试机制（3次尝试）
- 改进错误处理和日志输出

### 3. 改进摄像头类的错误处理
- **QRCodeScanner.py**：改进摄像头打开失败的错误信息
- **OCRVideoCapture.py**：添加GStreamer管道失败的详细错误信息

### 4. 使用正确的Smart Logistics程序
修改`test_full_workflow.sh`：
```bash
# 之前：运行UI程序（会启动新窗口）
setsid python3 main.py

# 现在：运行核心逻辑（无UI）
setsid python3 test.py
```

## 修复后的工作流程

1. **用户点击快速启动**
2. **UI释放摄像头资源**
   - 停止AGV摄像头捕获
   - 停止Arm摄像头捕获
   - 等待资源完全释放
3. **启动Lidar和Navigation**
   - Lidar按钮变红显示"Close"
   - Navigation按钮变红显示"Close"
4. **test_full_workflow.sh启动**
   - 等待5秒确保摄像头资源可用
   - 重试机制初始化摄像头
   - 运行Smart Logistics核心逻辑

## 预期结果

- ✅ 不再出现GStreamer错误
- ✅ 不再出现摄像头占用错误
- ✅ 不会启动额外的UI窗口
- ✅ Smart Logistics能正常访问摄像头
- ✅ 程序不会在摄像头初始化时卡死

## 故障排除

### 如果仍然出现摄像头错误：

1. **检查摄像头设备**：
   ```bash
   ls -la /dev/video*
   ```

2. **检查是否有其他进程占用摄像头**：
   ```bash
   lsof /dev/video0
   lsof /dev/video1
   ```

3. **手动释放摄像头资源**：
   ```bash
   sudo pkill -f "gst-launch"
   sudo pkill -f "nvarguscamerasrc"
   ```

4. **重启摄像头服务**（如果需要）：
   ```bash
   sudo systemctl restart nvargus-daemon
   ```

### 如果Smart Logistics仍然卡死：

1. 增加初始化延迟时间（在test.py中将5秒改为10秒）
2. 检查UI是否完全释放了摄像头资源
3. 确保没有其他程序在使用摄像头

## 代码修改总结

1. **main.py**：
   - 修改`on_quick_start_handle()`添加摄像头资源释放
   - 确保在启动Smart Logistics前完全清理资源

2. **Smart_Logistics_Kit-22-map/test.py**：
   - 添加摄像头初始化延迟和重试机制
   - 改进错误处理和日志输出

3. **Smart_Logistics_Kit-22-map/QRCodeScanner.py**：
   - 改进摄像头打开失败的错误信息

4. **Smart_Logistics_Kit-22-map/OCRVideoCapture.py**：
   - 添加GStreamer管道失败的详细错误信息

5. **test_full_workflow.sh**：
   - 改为运行test.py而不是main.py

这些修改确保了摄像头资源的正确管理，避免了冲突，让Smart Logistics能够顺利运行。