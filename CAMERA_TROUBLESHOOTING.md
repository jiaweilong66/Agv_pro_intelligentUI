# 相机问题排查指南

## 问题：相机有时能打开，有时打不开

这是一个常见问题，主要原因和解决方法如下：

## 诊断工具

### 1. 运行诊断脚本
```bash
chmod +x diagnose_camera.sh
./diagnose_camera.sh
```

这会检查：
- 相机设备是否存在
- 用户权限是否正确
- 是否有进程占用相机
- 相机是否能正常打开

### 2. 使用安全启动脚本
```bash
chmod +x safe_start.sh
./safe_start.sh
```

这个脚本会：
- 自动清理之前的进程
- 释放相机设备
- 设置正确的环境变量
- 启动应用程序

## 常见原因和解决方法

### 原因1: 相机设备被占用

**症状**: 
- 第一次启动正常，第二次启动失败
- 错误信息: "Device or resource busy"

**原因**: 
程序崩溃时没有正确释放相机

**解决方法**:
```bash
# 查看占用相机的进程
fuser /dev/video0 /dev/video1

# 强制释放
fuser -k /dev/video0 /dev/video1

# 或者重启系统
sudo reboot
```

### 原因2: 线程未正确清理

**症状**:
- 程序崩溃 (Aborted, core dumped)
- 相机线程仍在运行

**原因**:
QThread在程序退出时未正确停止

**解决方法**:
使用安全启动脚本，它会自动清理：
```bash
./safe_start.sh
```

### 原因3: GStreamer pipeline问题

**症状**:
- AGV相机（GStreamer）无法打开
- 错误: "no source element for URI"

**原因**:
GStreamer配置问题或相机未连接

**解决方法**:
```bash
# 测试GStreamer
gst-launch-1.0 nvarguscamerasrc ! nvoverlaysink

# 如果失败，检查相机连接
ls -l /dev/video*

# 检查GStreamer插件
gst-inspect-1.0 nvarguscamerasrc
```

### 原因4: 权限问题

**症状**:
- Permission denied
- 需要sudo才能运行

**原因**:
用户不在video组

**解决方法**:
```bash
# 添加用户到video组
sudo usermod -a -G video $USER

# 查看当前组
groups

# 如果video不在列表中，需要重新登录
# 或者重启
sudo reboot
```

### 原因5: 相机初始化时序问题

**症状**:
- 有时能打开，有时不能
- 没有明显错误信息

**原因**:
相机需要时间初始化，程序启动太快

**解决方法**:
程序已添加重试机制（3次重试，每次间隔1秒）

如果还是不稳定，可以增加延迟：
```bash
# 编辑main_app.py
# 找到 retry_delay = 1.0
# 改为 retry_delay = 2.0
```

### 原因6: OpenCV版本问题

**症状**:
- 相机打开失败
- GStreamer相关错误

**原因**:
OpenCV未正确编译GStreamer支持

**解决方法**:
```bash
# 检查OpenCV版本和GStreamer支持
python3 -c "import cv2; print(cv2.getBuildInformation())" | grep -i gstreamer

# 应该看到 GStreamer: YES

# 如果是NO，需要重新编译OpenCV或安装正确版本
```

## 最佳实践

### 1. 每次启动前清理
```bash
# 创建启动别名
echo 'alias start_ui="fuser -k /dev/video* 2>/dev/null; sleep 1; ./safe_start.sh"' >> ~/.bashrc
source ~/.bashrc

# 使用
start_ui
```

### 2. 正确关闭程序
- 不要用Ctrl+C强制终止
- 点击窗口关闭按钮
- 等待程序完全退出

### 3. 检查系统日志
```bash
# 查看内核日志
dmesg | grep video

# 查看系统日志
journalctl -xe | grep video
```

### 4. 监控相机状态
```bash
# 实时监控相机设备
watch -n 1 'ls -l /dev/video*; echo ""; fuser /dev/video* 2>&1'
```

## 调试步骤

如果相机仍然不稳定：

### 步骤1: 运行诊断
```bash
./diagnose_camera.sh > camera_diag.log 2>&1
cat camera_diag.log
```

### 步骤2: 测试相机独立运行
```bash
# 测试Python OpenCV
python3 << EOF
import cv2
cap = cv2.VideoCapture(0)
print("Camera 0:", cap.isOpened())
if cap.isOpened():
    ret, frame = cap.read()
    print("Read frame:", ret)
cap.release()
EOF
```

### 步骤3: 检查资源限制
```bash
# 检查打开文件限制
ulimit -n

# 如果太小（<1024），增加
ulimit -n 4096
```

### 步骤4: 查看详细错误
```bash
# 运行程序并保存所有输出
./safe_start.sh 2>&1 | tee app_debug.log

# 查看错误
grep -i error app_debug.log
grep -i camera app_debug.log
```

## 临时解决方案

如果相机问题持续存在，可以禁用相机功能：

### 方法1: 修改代码
编辑 `new_ui/main_app.py`，在initialize()方法中注释掉相机初始化：
```python
# self.agv_camera_capture = self.start_camera_capture(...)
# self.arm_camera_capture = self.start_camera_capture(...)
self.agv_camera_capture = None
self.arm_camera_capture = None
```

### 方法2: 使用环境变量
```bash
export DISABLE_CAMERAS=1
./safe_start.sh
```

然后在代码中检查这个变量。

## 硬件检查

### 1. 检查相机连接
```bash
# USB相机
lsusb

# CSI相机（Jetson）
ls -l /dev/video*
dmesg | grep -i camera
```

### 2. 测试相机硬件
```bash
# 使用nvgstcapture测试（Jetson）
nvgstcapture-1.0

# 使用cheese测试（Ubuntu）
cheese

# 使用ffmpeg测试
ffmpeg -f v4l2 -i /dev/video0 -frames 1 test.jpg
```

### 3. 检查相机规格
```bash
# 查看相机支持的格式
v4l2-ctl --list-formats-ext -d /dev/video0
```

## 联系支持

如果以上方法都无法解决，请提供：

1. 诊断脚本输出: `./diagnose_camera.sh`
2. 详细日志: `./safe_start.sh 2>&1 | tee debug.log`
3. 系统信息: `uname -a`
4. 相机型号和连接方式
5. 错误发生的频率和模式

## 总结

**最简单的解决方法**：
```bash
# 每次启动前运行
fuser -k /dev/video* 2>/dev/null
sleep 1
./safe_start.sh
```

或者直接使用：
```bash
./safe_start.sh
```

这个脚本会自动处理大部分相机问题。
