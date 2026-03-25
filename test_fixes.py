#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
测试修复效果的脚本
"""
import os
import time

def test_lidar_signal():
    """测试Lidar状态信号"""
    print("Testing Lidar status signal...")
    
    # 创建信号文件
    signal_file = "/tmp/ui_lidar_status_update.signal"
    with open(signal_file, 'w') as f:
        f.write("lidar_ready")
    
    print(f"Signal file created: {signal_file}")
    print("UI should detect this signal and update Lidar status to OPEN")
    
    # 等待一段时间让UI检测到信号
    time.sleep(2)
    
    # 检查信号文件是否被删除
    if not os.path.exists(signal_file):
        print("✓ Signal file was processed and removed by UI")
    else:
        print("⚠ Signal file still exists - UI may not be running")

def test_cofniger_import():
    """测试cofniger模块导入"""
    print("Testing cofniger module import...")
    
    try:
        # 添加当前目录到Python路径
        import sys
        sys.path.insert(0, '.')
        
        from cofniger import Config
        print("✓ cofniger module imported successfully")
        print(f"  - Debug mode: {Config.debug}")
        print(f"  - Resource path: {Config.resource_path}")
        
    except ImportError as e:
        print(f"✗ Failed to import cofniger: {e}")

if __name__ == "__main__":
    print("=== Testing Fixes ===")
    print()
    
    test_cofniger_import()
    print()
    
    test_lidar_signal()
    print()
    
    print("=== Test Complete ===")