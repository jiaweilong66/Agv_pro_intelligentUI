# ROS环境下启动UI指南

## 方法1：自动启动（推荐）

使用自动启动脚本，会自动启动roscore和UI：

```bash
# 添加执行权限（首次）
chmod +x start_with_ros.sh

# 启动
./start_with_ros.sh
```

这个脚本会：
1. 检查roscore是否已运行
2. 如果没有运行，自动启动roscore
3. 等待ROS初始化完成
4. 启动UI应用程序
5. 关闭UI时自动清理roscore

## 方法2：手动启动

### 步骤1：启动roscore

在第一个终端窗口：
```bash
# Source ROS环境
source /opt/ros/noetic/setup.bash
# 或者 melodic
# source /opt/ros/melodic/setup.bash

# 启动roscore
roscore
```

保持这个终端运行！

### 步骤2：启动UI

在第二个终端窗口：
```bash
cd /path/to/intelligent-logistics-system
python3 start_new_ui.py
```

## 方法3：使用tmux（高级）

使用tmux可以在一个终端管理多个窗口：

```bash
# 安装tmux（如果没有）
sudo apt-get install tmux

# 启动tmux会话
tmux new -s logistics

# 在第一个窗口启动roscore
source /opt/ros/noetic/setup.bash
roscore

# 创建新窗口 (Ctrl+B 然后按 C)
# 在新窗口启动UI
cd /path/to/intelligent-logistics-system
python3 start_new_ui.py

# 切换窗口: Ctrl+B 然后按 N (下一个) 或 P (上一个)
# 退出tmux: Ctrl+B 然后按 D (detach)
# 重新连接: tmux attach -t logistics
```

## 使用流程

### 1. 启动系统
```bash
./start_with_ros.sh
```

### 2. 等待UI加载
- 看到主菜单界面
- 点击"Quick Start"进入主界面

### 3. 启动功能
按顺序操作：

1. **点击Lidar按钮** - 启动激光雷达
   - 第一次点击会初始化ROS节点
   - 如果roscore未运行，会提示错误
   
2. **点击Navigation按钮** - 启动导航系统
   - 需要先启动Lidar

3. **使用其他功能**
   - Move to Shelf - 移动到货架
   - Circular Sorting - 循环排序
   - ARUCO/QR Detect - 视觉识别
   - Joystick/Keyboard Control - 控制方式

### 4. 虚拟控制器
- 点击主菜单的"Virtual Controller"
- 使用虚拟遥感控制机械臂和小车
- 需要先启动Lidar才能使用AGV控制

## 故障排查

### 问题1: "Unable to register with master node"

**原因**: roscore未运行

**解决**:
```bash
# 检查roscore是否运行
ps aux | grep roscore

# 如果没有运行，启动它
roscore
```

### 问题2: "Failed to initialize ROS node"

**原因**: ROS环境未正确配置

**解决**:
```bash
# Source ROS环境
source /opt/ros/noetic/setup.bash

# 添加到.bashrc自动加载
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
```

### 问题3: UI启动卡住

**原因**: 程序在等待roscore

**解决**:
1. 按Ctrl+C停止程序
2. 先启动roscore
3. 再启动UI

或者使用自动启动脚本：
```bash
./start_with_ros.sh
```

### 问题4: 点击Lidar按钮没反应

**原因**: ROS节点初始化失败

**解决**:
1. 确保roscore正在运行
2. 查看日志输出的错误信息
3. 重启UI程序

## 开机自动启动

### 方法1: systemd服务

创建服务文件：
```bash
sudo nano /etc/systemd/system/intelligent-logistics.service
```

内容：
```ini
[Unit]
Description=Intelligent Logistics System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/intelligent-logistics-system
ExecStart=/home/ubuntu/intelligent-logistics-system/start_with_ros.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable intelligent-logistics.service
sudo systemctl start intelligent-logistics.service
```

### 方法2: 桌面自动启动

创建自动启动文件：
```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/intelligent-logistics.desktop
```

内容：
```ini
[Desktop Entry]
Type=Application
Name=Intelligent Logistics System
Exec=/home/ubuntu/intelligent-logistics-system/start_with_ros.sh
Terminal=true
```

## 环境变量

如果需要自定义ROS环境，编辑启动脚本：

```bash
nano start_with_ros.sh
```

添加环境变量：
```bash
# 自定义ROS工作空间
source /home/ubuntu/myagv_ros/devel/setup.bash

# 设置ROS_MASTER_URI（如果需要）
export ROS_MASTER_URI=http://localhost:11311

# 设置ROS_IP（如果需要）
export ROS_IP=192.168.1.100
```

## 性能优化

### 1. 减少启动时间
```bash
# 预先启动roscore
roscore &

# 等待几秒后启动UI
sleep 3
python3 start_new_ui.py
```

### 2. 使用roslaunch
创建launch文件：
```xml
<!-- logistics.launch -->
<launch>
  <node name="intelligent_logistics_ui" pkg="intelligent_logistics" type="start_new_ui.py" output="screen"/>
</launch>
```

启动：
```bash
roslaunch intelligent_logistics logistics.launch
```

## 日志查看

### 查看ROS日志
```bash
# ROS节点列表
rosnode list

# 节点信息
rosnode info /intelligent_logistics_ui

# 话题列表
rostopic list

# 查看话题数据
rostopic echo /cmd_vel
```

### 查看应用日志
```bash
# 实时查看
tail -f ~/.ros/log/latest/intelligent_logistics_ui*.log

# 查看所有日志
ls ~/.ros/log/
```

## 总结

**最简单的启动方式**：
```bash
./start_with_ros.sh
```

这个脚本会处理所有的ROS初始化，你只需要等待UI出现即可！
