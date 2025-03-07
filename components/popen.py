#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import typing as T
import subprocess

from PyQt5.QtCore import QThread, QObject, pyqtSignal


class QSubprocessPopen(QThread):
    finished = pyqtSignal()

    def __init__(self, command: T.Union[str, T.List[str]], output: bool = False, parent: QObject = None):
        super(QSubprocessPopen, self).__init__(parent)
        self.command = command
        self.process = None
        self.stdout = None
        self.stderr = None
        self.returncode = None
        self.finished = False
        self.__output = output

    def run(self):
        try:
            self.process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if self.__output:
                self.stdout, self.stderr = self.process.communicate()
            self.process.wait()
        except Exception as e:
            print(e)
        finally:
            self.finished = True
            self.finished.emit()
            self.process = None
            self.stdout = None
            self.stderr = None
