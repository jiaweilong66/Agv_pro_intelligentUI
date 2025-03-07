import logging
import subprocess
import traceback
from typing import IO

from PyQt5.QtCore import QObject, pyqtSignal, QThread
from logging import Handler


class QConsoleHandler(QObject, Handler):
    level_color_mapping = {
        logging.INFO: "white",
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.DEBUG: "green",
        logging.CRITICAL: "cyan",
    }
    outputted = pyqtSignal(str)

    """A custom logging handler that outputs to a QTextBrowser widget."""

    def __init__(self, formatter: logging.Formatter, level: int = logging.INFO, parent=None):
        super().__init__(parent=parent)
        self.level = level
        self.setFormatter(formatter)

    def format(self, record):
        format_message = super().format(record)
        color = self.level_color_mapping.get(record.levelno, "white")
        return f"<div style='color:{color};padding:0px;margin:0px;'>{format_message}</div>"

    def emit(self, record):
        message = self.format(record)
        self.outputted.emit(message)


class QProcessStdout(QThread):
    outputted = pyqtSignal(str)

    def __init__(self, process: IO, parent=None):
        super().__init__(parent=parent)
        self.process = process

    def run(self):
        for line in iter(self.process.readline, ''):
            if len(line) == 0:
                break
            self.outputted.emit(line)

