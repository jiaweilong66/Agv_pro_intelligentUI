#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from PyQt5.QtCore import QObject, pyqtSignal

# Minimal stub for QConsoleHandler
class QConsoleHandler(QObject):
    outputted = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()