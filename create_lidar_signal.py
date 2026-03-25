#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
手动创建Lidar状态信号文件的测试脚本
"""
import os
import time

def create_lidar_signal():
    """创建Lidar准备就绪信号"""
    signal_file = "/tmp/ui_lidar_status_update.signal"
    
    print(f"Creating signal file: {signal_file}")
    
    try:
        with open(signal_file, 'w') as f:
            f.write("lidar_ready")
        
        print("✓ Signal file created successfully")
        print("Content: 'lidar_ready'")
        print()
        print("If the UI is running, it should:")
        print("1. Detect this signal file within 1 second")
        print("2. Set Lidar status to OPEN (red 'Close' button)")
        print("3. Remove the signal file")
        print("4. Log: 'Lidar status forced to OPEN by external signal'")
        print()
        
        # 等待几秒钟让UI处理
        print("Waiting 5 seconds for UI to process...")
        time.sleep(5)
        
        # 检查文件是否被删除
        if os.path.exists(signal_file):
            print("⚠ Signal file still exists - UI may not be running or not processing signals")
            print("You can manually delete it with: rm /tmp/ui_lidar_status_update.signal")
        else:
            print("✓ Signal file was processed and removed by UI")
            
    except Exception as e:
        print(f"✗ Error creating signal file: {e}")

if __name__ == "__main__":
    print("=== Lidar Signal Test ===")
    print()
    create_lidar_signal()
    print()
    print("=== Test Complete ===")