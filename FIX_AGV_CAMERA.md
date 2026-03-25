# 修复AGV 2D相机问题

## 快速修复

### 步骤1: 测试相机
```bash
chmod +x test_agv_camera.py fix_agv_camera.py
python3 test_agv_camera.py
```

### 步骤2: 自动修复配置
```bash
python3 fix_agv_camera.py
```

这个脚本会：
1. 扫描所有可用的相机
2. 测试每个相机是否工作
3. 推荐最佳配置
4. 可选：自动更新constant.py

### 步骤3: 重启应用
```bash
./safe_start.sh
```

## 手动修复

### 方法1: 使用USB相机代替CSI相机

如果CSI相机不工作，可以使用USB相机：

编辑 `constant.py`:
```python
# 原来的配置（CSI相机）
# camera2D_pipline = gstreamer_pipeline(sensor_id=0, flip_method=2)

# 改为USB相机
camera2D_pipline = 0  # /dev/video0
# 或
camera2D_pipline = 1  # /dev/video1
```

### 方法2: 修改CSI相机参数

如果CSI相机存在但配置不对：

编辑 `constant.py`:
```python
# 尝试不同的sensor_id
camera2D_pipline = gstreamer_pipeline(sensor_id=1, flip_method=2)

# 或尝试不同的flip_method
camera2D_pipline = gstreamer_pipeline(sensor_id=0, flip_method=0)
```

### 方法3: 使用简化的GStreamer pipeline

编辑 `utils/__init__.py` 中的 `gstreamer_pipeline` 函数，使用更简单的配置：

```python
def gstreamer_pipeline(
    sensor_id=0,
    capture_width=640,  # 降低分辨率
    capture_height=480,
    display_width=640,
    display_height=480,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )
```

## 诊断命令

### 检查相机硬件
```bash
# 查看相机设备
ls -l /dev/video*

# 查看USB设备
lsusb

# 查看内核日志
dmesg | grep -i camera
dmesg | grep -i csi
dmesg | grep -i video
```

### 测试CSI相机
```bash
# 使用nvgstcapture测试
nvgstcapture-1.0

# 使用gst-launch测试
gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! nvoverlaysink

# 检查GStreamer插件
gst-inspect-1.0 nvarguscamerasrc
```

### 测试USB相机
```bash
# 使用v4l2测试
v4l2-ctl --list-devices
v4l2-ctl --list-formats-ext -d /dev/video0

# 使用ffmpeg测试
ffmpeg -f v4l2 -i /dev/video0 -frames 1 test.jpg

# 使用OpenCV测试
python3 -c "import cv2; cap=cv2.VideoCapture(0); print('Opened:', cap.isOpened()); cap.release()"
```

## 常见问题

### Q1: "nvbuf_utils: Could not get EGL display connection"
**原因**: GStreamer配置问题或CSI相机未连接

**解决**:
1. 检查CSI相机连接
2. 尝试使用USB相机
3. 检查是否有权限问题

### Q2: "Error opening bin: no source element for URI"
**原因**: GStreamer pipeline格式错误

**解决**:
运行 `python3 fix_agv_camera.py` 自动检测正确配置

### Q3: 相机打开但是黑屏
**原因**: 相机初始化成功但无法读取帧

**解决**:
1. 检查相机镜头盖是否打开
2. 检查相机是否有足够光线
3. 尝试不同的flip_method参数

### Q4: "Cannot query video position"
**原因**: GStreamer pipeline问题

**解决**:
降低分辨率或帧率，参考方法3

## 推荐配置

### 配置1: Jetson CSI Camera (推荐)
```python
camera2D_pipline = gstreamer_pipeline(sensor_id=0, flip_method=2)
```

### 配置2: USB Camera
```python
camera2D_pipline = 0  # 或 1, 2, 3...
```

### 配置3: 低分辨率CSI Camera (更稳定)
```python
# 修改utils/__init__.py中的默认参数
capture_width=640
capture_height=480
```

## 验证修复

修改配置后，运行：
```bash
python3 test_agv_camera.py
```

应该看到：
```
✓ Camera opened successfully with default config!
✓ Frame captured! Size: (540, 960, 3)
```

然后启动应用：
```bash
./safe_start.sh
```

相机画面应该正常显示。

## 如果还是不行

1. 提供以下信息：
```bash
# 系统信息
uname -a

# 相机设备
ls -l /dev/video*

# 测试结果
python3 test_agv_camera.py > camera_test.log 2>&1
cat camera_test.log

# 内核日志
dmesg | grep -i camera > camera_dmesg.log
cat camera_dmesg.log
```

2. 尝试禁用AGV相机，只使用Arm相机：

编辑 `new_ui/main_app.py`，在initialize()方法中：
```python
# 注释掉AGV相机
# self.agv_camera_capture = self.start_camera_capture(...)
self.agv_camera_capture = None
```

3. 查看详细文档：
```bash
cat CAMERA_TROUBLESHOOTING.md
```
