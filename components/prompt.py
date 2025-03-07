#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
import typing as T
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox, QWidget


class QPrompt(QObject):
    def __init__(self, logger: T.Union[logging.Logger, str] = None, parent: QWidget = None):
        super(QPrompt, self).__init__(parent)
        self.__parent = parent
        self._logger = logging.getLogger() if logger is None else self.setLogger(logger)

    def setParent(self, parent: QWidget):
        super().setParent(parent)
        self.__parent = parent

    def setLogger(self, logger: T.Union[logging.Logger, str]):
        if isinstance(logger, str):
            self._logger = logging.getLogger(logger)
        elif isinstance(logger, logging.Logger):
            self._logger = logger
        else:
            raise TypeError("logger must be a logging.Logger or a str")

    def warning(self, title: str = "Warning", message: str = ""):
        self._logger.warning(message)
        return QMessageBox.warning(self.__parent, title, message, QMessageBox.Ok)

    def question(self, title: str = "Warning", message: str = "") -> bool:
        default = QMessageBox.Yes
        buttons = default | QMessageBox.No
        reply = QMessageBox.question(self.__parent, title, message, buttons, default)
        return reply == default
