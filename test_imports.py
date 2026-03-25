#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
测试所有模块导入是否正常
"""
import sys

print("测试模块导入...")
print("=" * 60)

modules_to_test = [
    ("PyQt5", "PyQt5"),
    ("OpenCV", "cv2"),
    ("NumPy", "numpy"),
    ("Pillow", "PIL"),
    ("Pygame", "pygame"),
]

failed = []
passed = []

for name, module in modules_to_test:
    try:
        __import__(module)
        print(f"✓ {name:20s} - OK")
        passed.append(name)
    except ImportError as e:
        print(f"✗ {name:20s} - 缺失")
        failed.append((name, module))

print("=" * 60)

# 测试项目模块
print("\n测试项目模块...")
print("=" * 60)

project_modules = [
    ("GPIO 工具", "utils.gpio"),
    ("命令工具", "utils.command"),
    ("ROS 启动", "functional.roslaunch"),
    ("检测器", "functional.detector"),
    ("手柄控制", "functional.joystick"),
    ("进程管理", "functional.process"),
]

for name, module in project_modules:
    try:
        __import__(module)
        print(f"✓ {name:20s} - OK")
        passed.append(name)
    except Exception as e:
        print(f"✗ {name:20s} - 错误: {str(e)[:40]}")
        failed.append((name, module))

print("=" * 60)

# 总结
print(f"\n总结:")
print(f"  通过: {len(passed)} 个模块")
print(f"  失败: {len(failed)} 个模块")

if failed:
    print("\n需要安装的包:")
    for name, module in failed:
        if module in ["PyQt5", "cv2", "numpy", "PIL", "pygame"]:
            pkg = "opencv-python" if module == "cv2" else module
            pkg = "Pillow" if module == "PIL" else pkg
            print(f"  pip install {pkg}")
    print("\n或运行: pip install -r requirements_windows.txt")
else:
    print("\n所有模块导入正常！可以运行 UI 了。")
    print("运行命令: python run_ui_demo.py")

print()
input("按回车键退出...")
