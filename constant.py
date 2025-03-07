#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from utils import gstreamer_pipeline


class GlobalVar:
    comport = "/dev/ttyS0"
    baudrate = 115200
    suction_pump_pins = (19, 26)  # 电磁阀引脚/电机引脚
    radar_control_pin = 20
    debug = False
    camera2D_pipline = gstreamer_pipeline(sensor_id=0, flip_method=2)
    camera3D_pipline = 0
