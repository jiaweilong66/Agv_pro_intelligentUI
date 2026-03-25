#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import subprocess
import traceback


class Command:

    @classmethod
    def check_output(cls, command) -> str:
        output = ''
        try:
            output = subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Command execution failed: {e}")
            traceback.print_exc()
        finally:
            if output:
                return output.decode("utf-8").strip()
            else:
                return output

    @classmethod
    def cat(cls, filepath) -> str:
        return cls.check_output(f"cat {filepath}")

    @classmethod
    def run_in_terminal(cls, command, keep: bool = False) -> subprocess.Popen:
        print(f" * Running command in terminal: \r\n\t{command}\r\n")
        import os
        import platform
        
        try:
            from utils.gpio import MOCK_MODE as _mock
        except ImportError:
            _mock = False
        
        if _mock or os.name == 'nt' or platform.system() == "Windows":
            return subprocess.Popen(command, shell=True)
            
        # 针对 Jetson 常见的 DBus Timeout 问题，使用特定的环境启动方式
        # 并尝试使用 xterm 作为后备，确保无论如何都能弹出窗口
        if keep:
            inner_cmd = f"{command}; exec bash"
        else:
            inner_cmd = f"{command}"

        # 组合命令：优先尝试 gnome-terminal (带 dbus-launch)，失败则尝试 xterm
        full_command = (
            f'gnome-terminal --title="Smart Logistics" -- bash -c "{inner_cmd}" || '
            f'xterm -hold -T "Smart Logistics (Fallback)" -e "/bin/bash -c \'{inner_cmd}\'"'
        )
        
        # 设置 DISPLAY 环境确保能打开窗口
        env = os.environ.copy()
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"
            
        return subprocess.Popen(full_command, shell=True, env=env)

    @classmethod
    def kill(cls, command) -> bool:
        """Kill process matching command pattern. First tries SIGINT, then SIGKILL."""
        try:
            import time
            # First attempt: SIGINT (graceful shutdown)
            kill_cmd = "ps -ef | grep -E %s | grep -v 'grep' | awk '{print $2}' | xargs kill -2 2>/dev/null" % command
            subprocess.run(kill_cmd, shell=True)
            
            # Wait 2s for graceful shutdown
            time.sleep(2)
            
            # Check if still alive, if so force kill with SIGKILL
            if cls.alive(command):
                force_cmd = "ps -ef | grep -E %s | grep -v 'grep' | awk '{print $2}' | xargs kill -9 2>/dev/null" % command
                subprocess.run(force_cmd, shell=True)
                print(f"[Command] Force killed: {command}")
            
        except Exception as e:
            print(f"Command kill failed: {e}")
            traceback.print_exc()
            return False
        return True

    @classmethod
    def alive(cls, command):
        command = "ps -ef | grep -E %s | grep -v 'grep' | wc -l" % command
        return int(cls.check_output(command)) > 0

