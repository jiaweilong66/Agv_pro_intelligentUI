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
        if keep:
            exec_command = f'gnome-terminal -- bash -c "{command}; exec bash"'
        else:
            exec_command = f'gnome-terminal -- bash -c \"{command};\"'
        return subprocess.Popen(exec_command, shell=True)

    @classmethod
    def kill(cls, command) -> bool:
        try:
            command = "ps -ef | grep -E %s | grep -v 'grep' | awk '{print $2}' | xargs kill -2" % command
            subprocess.run(command, shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Command execution failed: {e}")
            traceback.print_exc()
            return False
        return True

    @classmethod
    def alive(cls, command):
        command = "ps -ef | grep -E %s | grep -v 'grep' | wc -l" % command
        return int(cls.check_output(command)) > 0

