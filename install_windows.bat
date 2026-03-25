@echo off
chcp 65001 >nul
echo ============================================================
echo 智能物流系统 - Windows 依赖安装
echo ============================================================
echo.
echo 正在安装必要的 Python 包...
echo.

pip install -r requirements_windows.txt

if errorlevel 1 (
    echo.
    echo 安装失败！请检查：
    echo 1. 是否已安装 Python 3.7+
    echo 2. 是否已将 Python 添加到系统 PATH
    echo 3. 网络连接是否正常
    echo.
) else (
    echo.
    echo ============================================================
    echo 安装完成！
    echo ============================================================
    echo.
    echo 现在可以运行: run_ui_demo.bat
    echo 或者直接运行: python run_ui_demo.py
    echo.
)

pause
