#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import threading
import time
import typing as T
import cv2
import numpy as np
from multiprocessing import Process, Event, shared_memory, Pipe
from threading import Lock


class CameraCaptureException(Exception):
    """自定义摄像头异常"""
    pass


class _Buffer(object):
    """缓冲区管理类"""

    def __init__(self, shm: shared_memory.SharedMemory, frame: np.ndarray):
        self.shared_memory = shm
        self.frame = frame


class SharedMemoryBuffer:
    """双缓冲共享内存管理类"""

    def __init__(self, buffer_size, buffer_shape):
        self.buffers = []
        self.buffer_shape = buffer_shape
        self.mutex = Lock()
        self.active_index = 0  # 当前活跃缓冲区索引
        # 创建两个共享内存缓冲区
        for _ in range(2):
            self.buffers.append(
                self.__init_shared_memory__(buffer_size, buffer_shape)
            )

    @property
    def names(self):
        return [buf.shared_memory.name for buf in self.buffers]

    @classmethod
    def __init_shared_memory__(cls, buffer_size, buffer_shape, name: str = None) -> _Buffer:
        """初始化共享内存"""
        shm = shared_memory.SharedMemory(
            name=name,
            create=True,
            size=buffer_size
        )
        frame = np.ndarray(buffer_shape, dtype=np.uint8, buffer=shm.buf)
        return _Buffer(shm, frame)

    def switch_buffer(self):
        """切换活跃缓冲区"""
        with self.mutex:
            self.active_index = 1 - self.active_index

    def get_active_buffer(self):
        """获取当前活跃缓冲区"""
        with self.mutex:
            buffer = self.buffers[self.active_index]
        return buffer

    def release(self):
        """释放共享内存资源"""
        for buf in self.buffers:
            buf.shared_memory.close()
            buf.shared_memory.unlink()
        self.buffers.clear()


class CameraCaptureWorker(Process):
    def __init__(self, pipeline: str, pipe: Pipe, stop_event: Event, capture_args: T.Tuple[T.Any, ...] = ()):
        super().__init__(daemon=True)
        self.pipeline = pipeline  # 摄像头设备索引
        self.capture_args = capture_args
        self.context_pipe = pipe  # 进程间通信队列
        self.stop_event = stop_event  # 停止事件
        self.retry_count = 3  # 重试次数
        self.retry_interval = 2  # 重试间隔(秒)
        self.wait_parent_notify_thread: T.Optional[threading.Thread] = None
        self.__is_init = False
        print("# ##############################################################################")
        print("# 子进程启动")
        print("# ##############################################################################")

    def __wait_parent_notify__(self):
        print("# ##############################################################################")
        print("# 等待父进程通知")
        print("# ##############################################################################")
        while not self.stop_event.is_set():
            cmd, *args = self.context_pipe.recv()
            print(f"收到命令: {cmd}, 参数: {args}")

    def connect_camera_capture(self) -> T.Optional[cv2.VideoCapture]:
        print("# ##############################################################################")
        print(f"# Pipeline: {self.pipeline}")
        print(f"# Args: {self.capture_args}")
        print("# ##############################################################################")
        capture = cv2.VideoCapture(self.pipeline, *self.capture_args)
        if not capture.isOpened():
            capture.release()
            return None
        return capture

    def _init_shared_memory(self, raw_frame) -> SharedMemoryBuffer:
        """初始化共享内存"""
        try:
            memory_buffer = SharedMemoryBuffer(raw_frame.nbytes, raw_frame.shape)
            self.context_pipe.send(("init", (*memory_buffer.names, raw_frame.shape)))
            self.__is_init = True
            return memory_buffer
        except Exception as e:
            self.__is_init = False
            raise MemoryError(f"共享内存分配失败: {str(e)}")

    def camera_capture_loop(self):
        """摄像头采集内部循环"""
        capture = self.connect_camera_capture()
        if capture is None:
            raise CameraCaptureException("无法打开摄像头")
        print("# ##############################################################################")
        print("# 摄像头打开成功，摄像头采集循环开始")
        print("# ##############################################################################")
        buffer = None
        try:
            while not self.stop_event.is_set():
                print("!!!!!!")
                ret, frame = capture.read()
                print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
                if not ret:
                    continue

                if buffer is None:
                    print("# ##############################################################################")
                    print("# 初始化共享内存")
                    print("# ##############################################################################")
                    buffer = self._init_shared_memory(capture)
                    continue

                # 将新帧转换为RGB格式
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # 写入非活跃缓冲区
                buffer.switch_buffer()
                active_buffer = buffer.get_active_buffer()
                np.copyto(active_buffer.frame, frame_rgb)
                self.context_pipe.send(("update", buffer.active_index))
        finally:
            capture.release()
            if buffer is not None:
                buffer.release()
            print("# ##############################################################################")
            print("# 摄像头采集循环结束")
            print("# ##############################################################################")

    def run(self):
        self.wait_parent_notify_thread = threading.Thread(target=self.__wait_parent_notify__)
        self.wait_parent_notify_thread.daemon = True
        self.wait_parent_notify_thread.start()

        attempt = 0
        while not self.stop_event.is_set() and attempt < self.retry_count:
            try:
                self.camera_capture_loop()
                break
            except (CameraCaptureException, MemoryError) as e:
                print(f"捕获到错误: {str(e)}")
                attempt += 1
                time.sleep(self.retry_interval)
        if attempt >= self.retry_count:
            self.context_pipe.send(("error", "摄像头初始化失败"))





















