# Lidar状态修复说明

## 问题描述
雷达在快速启动后仍然显示为未打开状态，即使里程计数据正常。

## 修复方案

### 1. 信号机制
- 当`test_full_workflow.sh`检测到里程计数据正常时，创建信号文件`/tmp/ui_lidar_status_update.signal`
- UI每秒检查一次该信号文件
- 检测到信号后强制设置Lidar状态为OPEN

### 2. 状态管理
- 添加了`Flag.radar_forced_status`标志来防止外部强制状态被实际硬件状态覆盖
- 修改了`setup_radar_control_button()`方法，在强制状态下不重新检查硬件状态

### 3. 调试信息
- 添加了详细的日志输出来帮助诊断问题
- 定时器启动时会输出确认信息
- 信号处理过程中会输出详细步骤

## 测试方法

### 方法1：运行完整工作流
```bash
./test_full_workflow.sh
```
当看到以下日志时，Lidar按钮应该变为红色"Close"状态：
```
[WORKFLOW] Checking odometry data...
[WORKFLOW] ✓ Odometry data normal
```

### 方法2：手动测试信号
```bash
python3 create_lidar_signal.py
```
这会创建信号文件，UI应该在1秒内检测到并更新状态。

### 方法3：直接创建信号文件
```bash
echo "lidar_ready" > /tmp/ui_lidar_status_update.signal
```

## 预期行为

1. **UI启动时**：
   - 看到日志："Status check timer started - checking for external signals every 1 second"

2. **信号检测时**：
   - 看到日志："Found signal file: /tmp/ui_lidar_status_update.signal"
   - 看到日志："Signal content: 'lidar_ready'"
   - 看到日志："Processing lidar_ready signal..."
   - 看到日志："Lidar status forced to OPEN by external signal"
   - 看到日志："Flag.radar_running is now: True"
   - 看到日志："Signal file processed and removed"

3. **UI状态变化**：
   - Lidar按钮变为红色
   - 按钮文本变为"Close"

## 故障排除

### 如果Lidar状态仍未更新：

1. **检查UI是否启动了定时器**：
   - 查看日志中是否有："Status check timer started"

2. **检查信号文件是否被创建**：
   ```bash
   ls -la /tmp/ui_lidar_status_update.signal
   ```

3. **手动测试信号处理**：
   ```bash
   python3 create_lidar_signal.py
   ```

4. **检查UI日志**：
   - 应该看到信号处理的详细日志
   - 如果没有日志，说明定时器可能没有启动

5. **检查权限**：
   - 确保UI有权限读写`/tmp/`目录

### 如果按钮状态被重置：

- 这可能是因为其他地方调用了`setup_radar_control_button()`
- 检查`Flag.radar_forced_status`是否被意外重置

## 代码修改总结

1. **main.py**：
   - 添加了`Flag.radar_forced_status`标志
   - 修改了`setup_radar_control_button()`方法
   - 添加了`check_external_status_signals()`方法
   - 在`initialize()`中启动了状态检查定时器
   - 在`start_radar_control_handle()`中重置强制状态标志

2. **test_full_workflow.sh**：
   - 在检测到里程计数据正常时创建信号文件
   - 添加了PYTHONPATH设置来解决模块导入问题

这个修复方案通过文件系统信号实现了脚本与UI之间的可靠通信，确保Lidar状态能够正确显示。