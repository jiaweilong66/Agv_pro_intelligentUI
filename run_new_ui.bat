@echo off
chcp 65001 >nul
echo ============================================================
echo 智能物流系统 - 新版UI (集成完整功能)
echo ============================================================
echo.
echo 正在启动新版UI界面...
echo.
python new_ui/main_app.py
if errorlevel 1 (
    echo.
    echo 启动失败！请检查：
    echo 1. 是否已安装 Python 3.7+
    echo 2. 是否已安装依赖包: pip install -r requirements_windows.txt
    echo 3. 是否已正确配置硬件连接
    echo.
    pause
)
