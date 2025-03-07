#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import dataclasses
import threading
import time
import typing as T

import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt
from PyQt5.QtGui import QPixmap, QImage

MiddlewareFunc = T.Callable[[T.List[T.List[int]]], T.Any]  # Intelligent Logistics System


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
    pixmap: QPixmap = dataclasses.field(default=None)
    result: T.Any = dataclasses.field(default=None)

    def set_result(self, result: T.Any):
        self.result = result

    def set_frame(self, frame: np.ndarray):
        self.frame = frame


class QPixmapConversionMiddleware(QCameraMiddleware):

    def __init__(self, size: QSize):
        super().__init__()
        self.__size = size

    def resize(self, size: QSize):
        self.__size = size

    def __call__(self, frame: np.ndarray):
        try:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
            pix = QPixmap.fromImage(img)
            return pix.scaled(self.__size.width(), self.__size.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
                # stime = time.perf_counter()
                result = middleware(frame)
                # cost_time = time.perf_counter() - stime
                # print(f"@@@@Call middleware [{self.__middleware.name}] result ==> {result} cost time ==> {cost_time}")
                frame = middleware.get_frame()
                self.__middleware_result.append(result)
                if len(self.__middleware_result) > 5:
                    self.__middleware_result.pop(0)
                middleware.set_result(result)
                stream.set_result(result)

            stream.pixmap = self.__conversion_middleware(frame)
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
