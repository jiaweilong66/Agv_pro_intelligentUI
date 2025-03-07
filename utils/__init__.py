#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import socket
import subprocess
from .gpio import GpioHandler

CAMERA_3D_ID = "2bc5:069d"


def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=960,
    display_height=540,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )


def find_camera_device(index: int = 0):
    cameras = [
        f'/dev/{name}' for name in os.listdir('/dev') if name.startswith('video')
    ]
    cameras.reverse()
    if index >= len(cameras) or len(cameras) == 0:
        return None
    return cameras[index]


def get_localhost():
    st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        st.connect(('10.255.255.255', 1))
        IP = st.getsockname()[0]
    except Exception as e:
        print(e)
        IP = '127.0.0.1'
    finally:
        st.close()
    return IP


def get_3d_camera_status():
    usb_infos = subprocess.check_output("lsusb").decode("utf-8")
    for line in usb_infos.splitlines():
        if line.count(CAMERA_3D_ID) > 0:
            return True
    return False


__all__ = [
    "gstreamer_pipeline",
    "get_localhost",
    "get_3d_camera_status",
    "GpioHandler",
    "find_camera_device"
]
