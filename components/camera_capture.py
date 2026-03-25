#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import traceback
from multiprocessing import Pipe, Event, shared_memory

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QSize, Qt
from PyQt5.QtGui import QImage, QPixmap

from utils.camera_api import CameraCaptureWorker
import dataclasses
import threading
import time
import typing as T

import cv2

MiddlewareFunc = T.Callable[[T.List[T.List[int]]], T.Any]  # Intelligent Logistics System


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
            
            # 【修复跨线程崩溃】只生成 QImage 并缩放，不在这里创建 QPixmap
            image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            image = image.scaled(self.__size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 发射 QImage 出去给主线程
            self.transmit.emit(image)
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


class QCameraMiddleware:
    def __init__(self):
        self.__frame: T.Optional[np.ndarray] = None
        self.__result: T.Optional[T.Any] = None

    @property
    def name(self):
        return self.__class__.__name__

    def set_frame(self, frame: np.ndarray):
        self.__frame = frame

    def get_frame(self) -> T.Optional[np.ndarray]:
        return self.__frame

    def set_result(self, result: T.Any):
        self.__result = result

    def get_result(self) -> T.Optional[T.Any]:
        return self.__result

    def __call__(self, frame: T.List[T.List[int]]) -> T.Any:
        raise NotImplementedError()


Middleware = T.TypeVar("Middleware", bound=QCameraMiddleware)


@dataclasses.dataclass
class QCameraStream(object):
    pipeline: str
    middleware: Middleware
    frame: np.ndarray = dataclasses.field(default=None)
    # 【修复跨线程崩溃】将原来的 pixmap 改为 image，并使用 QImage 类型
    image: QImage = dataclasses.field(default=None)
    result: T.Any = dataclasses.field(default=None)

    def set_result(self, result: T.Any):
        self.result = result

    def set_frame(self, frame: np.ndarray):
        self.frame = frame


class QPixmapConversionMiddleware(QCameraMiddleware):

    def __init__(self, size: QSize):
        super().__init__()
        # 【修复语法错误】修正了原来的 "自.__size=大小"
        self.__size = size

    def resize(self, size: QSize):
        self.__size = size

    def __call__(self, frame: np.ndarray):
        try:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            # 【修复跨线程崩溃】不转 QPixmap，直接对 QImage 缩放并返回
            return img.scaled(self.__size.width(), self.__size.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        except Exception as error:
            print(self.__size, type(self.__size))
            print("{error}: {error_msg}".format(error=error, error_msg=error.__str__()))


class QCameraStreamCapture(QThread):
    streamed = pyqtSignal(QCameraStream)

    def __init__(self, pipeline: T.Union[str, int], size: QSize, params: tuple = None, parent=None):
        super(QCameraStreamCapture, self).__init__(parent)
        params = params or ()
        self.__size = size
        self.__running = False
        self.__is_opened = False
        self.__pipeline = pipeline
        self.__middleware_name: T.Optional[str] = None
        self.__middleware_table: T.Dict[str, Middleware] = {}
        self.__middleware_result: T.List = []
        self.__mutex = threading.Lock()
        self.__capture = cv2.VideoCapture(pipeline, *params)
        self.__conversion_middleware = QPixmapConversionMiddleware(size=size)

    def register_middleware(self, name: str, middleware: Middleware):
        if name not in self.__middleware_table.keys():
            self.__middleware_table[name] = middleware
            return True
        return False

    def unregister_middleware(self, name: str):
        if name in self.__middleware_table.keys():
            del self.__middleware_table[name]
            return True
        return False

    def activate_middleware(self, name: str) -> bool:
        with self.__mutex:
            self.__middleware_name = name
            self.__middleware_result.clear()
        return self.__middleware_table.get(name) is not None

    def deactivate_middleware(self):
        with self.__mutex:
            self.__middleware_name = None
            self.__middleware_result.clear()

    @property
    def size(self) -> QSize:
        return self.__size

    def resize(self, size: QSize):
        self.__conversion_middleware.resize(size)
        self.__size = size

    @property
    def pipeline(self) -> T.Union[str, int]:
        return self.__pipeline

    @property
    def is_opened(self) -> bool:
        return self.__is_opened

    @property
    def capture(self) -> cv2.VideoCapture:
        return self.__capture

    @property
    def is_running(self) -> bool:
        return self.__running

    def stopped(self):
        self.__running = False

    def clear_middleware(self):
        self.__middleware_table.clear()

    def get_middleware_result(self) -> T.Any:
        if not self.__middleware_result:
            return None
            return self.__middleware_result[-1]

    def __middleware_handle(self, frame: np.ndarray) -> QCameraStream:
        with self.__mutex:
            middleware = self.__middleware_table.get(self.__middleware_name, None)
            stream = QCameraStream(pipeline=self.pipeline, middleware=middleware)
            if middleware is not None:
                result = middleware(frame)
                frame = middleware.get_frame()
                self.__middleware_result.append(result)
                if len(self.__middleware_result) > 5:
                    self.__middleware_result.pop(0)
                middleware.set_result(result)
                stream.set_result(result)

            # 【修复跨线程崩溃】赋值给新的 image 属性，接收的是 QImage
            stream.image = self.__conversion_middleware(frame)
            return stream

    def __emit_stream(self, camera_stream: QCameraStream):
        self.__camera_stream = camera_stream
        self.streamed.emit(camera_stream)

    def run(self):
        self.__running = True
        self.__is_opened = self.__capture.isOpened()
        while self.__is_opened:
            ret, frame = self.__capture.read()
            if not ret:
                continue

            if self.__running is False:
                break
            camera_stream = self.__middleware_handle(frame)
            self.__emit_stream(camera_stream)
        self.__capture.release()
        self.__is_opened = False
        self.__capture = None
        print(f"{self.pipeline} camera thread quit.")