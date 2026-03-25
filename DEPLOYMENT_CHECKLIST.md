# Jetson部署检查清单

## 📋 部署前检查

### 系统环境
- [ ] Jetson系统已安装并正常运行
- [ ] Python 3.7+ 已安装
- [ ] ROS环境已配置
- [ ] 网络连接正常

### 硬件连接
- [ ] 激光雷达已连接
- [ ] AGV 2D相机已连接 (GStreamer pipeline)
- [ ] MechArm 270相机已连接 (/dev/video1)
- [ ] GPIO引脚已正确连接
- [ ] 手柄控制器已连接（如需要）

### 软件依赖
- [ ] PyQt5 已安装
- [ ] OpenCV 已安装
- [ ] 其他依赖已安装 (requirements.txt)

## 📦 文件清单

### 核心文件
- [x] `new_ui/main_app.py` - 主应用程序
- [x] `new_ui/main_menu.ui` - 主菜单界面
- [x] `new_ui/quick_start.ui` - 快速启动界面

### 依赖模块（原有）
- [x] `cofniger.py` - 配置管理
- [x] `constant.py` - 全局变量
- [x] `components/` - UI组件
- [x] `functional/` - 功能模块
- [x] `utils/` - 工具函数
- [x] `resources/` - 资源文件

### 文档
- [x] `README_NEW_UI.md` - 快速开始
- [x] `NEW_UI_INTEGRATION_GUIDE.md` - 集成说明
- [x] `NEW_UI_SUMMARY.md` - 完成总结
- [x] `UI_COMPARISON.md` - UI对比
- [x] `DEPLOYMENT_CHECKLIST.md` - 本文档

## 🚀 部署步骤

### 1. 文件传输
```bash
# 将整个项目文件夹传输到Jetson
scp -r intelligent-logistics-system/ jetson@<IP>:/home/jetson/
```

### 2. 安装依赖
```bash
cd /home/jetson/intelligent-logistics-system
pip3 install -r requirements.txt
```

### 3. 配置检查
```bash
# 检查配置文件
cat cofniger.py
cat constant.py

# 检查资源文件
ls resources/
ls resources/translation/
```

### 4. 权限设置
```bash
# 给予执行权限
chmod +x new_ui/main_app.py

# 检查设备权限
ls -l /dev/video*
ls -l /dev/ttyUSB*  # 如果使用串口
```

### 5. 测试运行
```bash
# 测试导入
python3 -c "from new_ui.main_app import MainApplication; print('OK')"

# 启动应用
python3 new_ui/main_app.py
```

## ✅ 功能测试清单

### 基础功能
- [ ] 应用程序正常启动
- [ ] 主菜单显示正常
- [ ] 可以进入快速启动界面
- [ ] 可以返回主菜单
- [ ] 语言切换正常

### 硬件控制
- [ ] 激光雷达可以启动/关闭
- [ ] 导航系统可以启动/关闭
- [ ] GPIO控制正常
- [ ] 泵控制正常

### 相机功能
- [ ] AGV 2D相机画面显示正常
- [ ] MechArm 270相机画面显示正常
- [ ] 相机画面实时更新
- [ ] 相机分辨率正确

### 视觉识别
- [ ] ARUCO码识别正常
- [ ] QR码识别正常
- [ ] 识别结果正确显示
- [ ] 识别结果记录到日志

### 任务流程
- [ ] 快速启动任务可以执行
- [ ] 移动到货架任务正常
- [ ] 循环分拣任务正常
- [ ] 任务进度节点正确更新
- [ ] 任务完成后状态正确

### 控制功能
- [ ] 手柄控制正常（如有）
- [ ] 键盘控制正常
- [ ] 控制响应及时
- [ ] 控制可以正常停止

### 日志系统
- [ ] 日志正常输出到UI
- [ ] 日志内容正确
- [ ] 日志可以清除
- [ ] 日志文件正常记录

### 异常处理
- [ ] 雷达未启动时有提示
- [ ] 导航未启动时有提示
- [ ] 相机启动失败有提示
- [ ] 任务执行错误有提示

## 🐛 常见问题排查

### 问题1：应用无法启动
```bash
# 检查Python版本
python3 --version

# 检查依赖
pip3 list | grep PyQt5
pip3 list | grep opencv

# 查看错误日志
python3 new_ui/main_app.py 2>&1 | tee error.log
```

### 问题2：相机无法显示
```bash
# 检查相机设备
ls -l /dev/video*

# 测试相机
v4l2-ctl --list-devices

# 检查GStreamer
gst-inspect-1.0 | grep video
```

### 问题3：雷达无法启动
```bash
# 检查ROS环境
echo $ROS_DISTRO
roscore &

# 检查雷达节点
rosnode list
rostopic list
```

### 问题4：GPIO错误
```bash
# 检查GPIO权限
sudo usermod -a -G gpio $USER

# 检查GPIO状态
cat /sys/class/gpio/export
```

### 问题5：导航无法启动
```bash
# 检查导航包
rospack find navigation

# 检查地图文件
ls -l maps/

# 检查参数文件
ls -l config/
```

## 📊 性能检查

### CPU使用率
```bash
# 监控CPU
top -p $(pgrep -f main_app.py)
```

### 内存使用
```bash
# 监控内存
free -h
watch -n 1 free -h
```

### 相机帧率
```bash
# 检查相机帧率
# 在日志中查看相机流信息
```

### 响应时间
- [ ] 按钮点击响应 < 100ms
- [ ] 相机画面延迟 < 200ms
- [ ] 任务启动时间 < 2s

## 🔧 优化建议

### 性能优化
- [ ] 调整相机分辨率（如需要）
- [ ] 优化日志输出频率
- [ ] 调整任务执行间隔

### 稳定性优化
- [ ] 添加自动重启脚本
- [ ] 配置看门狗
- [ ] 设置日志轮转

### 用户体验优化
- [ ] 调整按钮大小（如需要）
- [ ] 优化字体大小
- [ ] 调整窗口大小

## 📝 部署记录

### 部署信息
- 部署日期：__________
- 部署人员：__________
- Jetson型号：__________
- 系统版本：__________

### 测试结果
- 基础功能：[ ] 通过 [ ] 失败
- 硬件控制：[ ] 通过 [ ] 失败
- 相机功能：[ ] 通过 [ ] 失败
- 视觉识别：[ ] 通过 [ ] 失败
- 任务流程：[ ] 通过 [ ] 失败
- 控制功能：[ ] 通过 [ ] 失败

### 问题记录
1. ___________________________
2. ___________________________
3. ___________________________

### 解决方案
1. ___________________________
2. ___________________________
3. ___________________________

## ✨ 部署完成

- [ ] 所有功能测试通过
- [ ] 性能指标达标
- [ ] 文档已更新
- [ ] 用户已培训
- [ ] 备份已完成

## 📞 技术支持

如遇问题，请：
1. 查看日志文件
2. 检查硬件连接
3. 参考文档说明
4. 记录错误信息

---

**祝部署顺利！** 🎉
