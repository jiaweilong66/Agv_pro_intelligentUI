#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import traceback
from multiprocessing import Pipe, Event, shared_memory

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QSize, Qt
from PyQt5.QtGui import QImage, QPixmap

from utils.camera_api import CameraCaptureWorker


class CameraCaptureTransponder(QThread):
    transmit = pyqtSignal(object)

    def __init__(self, pipeline: str, size: QSize, *args, parent: QObject = None):
        super().__init__(parent=parent)
        self.parent_pipe, self.child_pipe = Pipe()
        self.__running = False
        self.__size = size
        self.stop_event = Event()
        self.capture_worker = CameraCaptureWorker(pipeline, self.child_pipe, self.stop_event, capture_args=args)
        self.capture_worker.start()
        self.shm_buffers = None

    def stopped(self):
        self.__running = False

    def resize(self, size: QSize):
        self.__size = size

    def OCR(self):
        self.parent_pipe.send(("ocr", None))

    def _handle_init(self, payload):
        """处理初始化消息"""
        shm_name1, shm_name2, frame_shape = payload
        self.shm_buffers = [
            shared_memory.SharedMemory(name=shm_name1),
            shared_memory.SharedMemory(name=shm_name2)
        ]
        self.frame_shape = frame_shape
        self.current_index = 0

    def _handle_update(self, buffer_index):
        """处理更新消息"""
        if self.shm_buffers is None:
            return

        self.current_index = buffer_index
        self._update_display()

    def _handle_error(self, message):
        pass

    def _update_display(self):
        try:
            buffer = self.shm_buffers[self.current_index]
            frame = np.ndarray(self.frame_shape, dtype=np.uint8, buffer=buffer.buf)
            height, width, _ = self.frame_shape
            bytes_per_line = 3 * width
            image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image)
            pixmap = pixmap.scaled(self.__size, Qt.KeepAspectRatio)
            self.transmit.emit(pixmap)
        except Exception as e:
            print(f"显示错误: {str(e)}")

    def run(self):
        """处理进程间消息"""
        try:
            self.__running = True
            while self.__running is True:
                msg_type, payload = self.parent_pipe.recv()
                if msg_type == "init":
                    self._handle_init(payload)
                elif msg_type == "update":
                    self._handle_update(payload)
                elif msg_type == "error":
                    self._handle_error(payload)
            self.close()
        except Exception as e:
            print(f"运行错误: {str(e)}")
            print(traceback.format_exc())

    def close(self):
        """关闭事件处理"""
        self.stop_event.set()

        if self.capture_worker.is_alive():
            self.capture_worker.join(2)
            if self.capture_worker.is_alive():
                self.capture_worker.terminate()

        if self.shm_buffers:
            for shm in self.shm_buffers:
                shm.close()
