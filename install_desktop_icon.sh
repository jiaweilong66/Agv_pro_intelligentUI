#!/bin/bash

# 安装桌面快捷方式脚本 - 最简单版本

echo "========================================="
echo "安装智慧物流UI桌面快捷方式"
echo "========================================="

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 桌面路径
DESKTOP_DIR="$HOME/Desktop"
if [ ! -d "$DESKTOP_DIR" ]; then
    DESKTOP_DIR="$HOME/桌面"
fi

if [ ! -d "$DESKTOP_DIR" ]; then
    echo "错误: 找不到桌面目录"
    exit 1
fi

# 创建.desktop文件
DESKTOP_FILE="$DESKTOP_DIR/IntelligentLogisticsUI.desktop"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Intelligent Logistics UI
Comment=智慧物流系统用户界面
Exec=$SCRIPT_DIR/start_with_ros.sh
Icon=utilities-terminal
Terminal=true
Categories=Application;Development;
Path=$SCRIPT_DIR
EOF

# 设置可执行权限
chmod +x "$DESKTOP_FILE"
chmod +x "$SCRIPT_DIR/start_with_ros.sh"

# 标记为可信任
if command -v gio &> /dev/null; then
    gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null
fi

echo ""
echo "✓ 桌面快捷方式已创建"
echo "✓ 路径: $SCRIPT_DIR/start_with_ros.sh"
echo ""
echo "现在可以双击桌面图标启动UI"
echo "如果提示不可信任，右键点击 -> 允许启动"
echo ""
echo "========================================="
