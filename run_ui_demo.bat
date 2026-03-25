@echo off
chcp 65001 >nul
echo ============================================================
echo Intelligent Logistics System - UI Demo Mode
echo ============================================================
echo.
echo Starting UI interface...
echo.
python run_ui_demo.py
if errorlevel 1 (
    echo.
    echo Startup failed! Please check:
    echo 1. Python 3.7+ is installed
    echo 2. Dependencies are installed: pip install PyQt5
    echo.
    pause
)
