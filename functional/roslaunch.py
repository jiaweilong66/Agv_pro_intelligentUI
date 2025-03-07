#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
from utils.command import Command
from utils.gpio import GpioHandler
from constant import GlobalVar

ROS_SETUP_FILEPATH = "/opt/ros/noetic/setup.bash"
ROS_WORKSPACE_FILEPATH = "/home/er/myagv_ros/devel/setup.bash"
COMMAND_SEPARATOR = " "


def roslaunch(*args, workspace: bool = True):
    command = f"roslaunch {COMMAND_SEPARATOR.join(args)}"
    if workspace is True:
        command = f"source {ROS_SETUP_FILEPATH} && source {ROS_WORKSPACE_FILEPATH} && {command}"

    Command.run_in_terminal(command=command, keep=False)


def rosrun(*args):
    command = f"source {ROS_SETUP_FILEPATH} && source {ROS_WORKSPACE_FILEPATH} && rosrun {COMMAND_SEPARATOR.join(args)}"
    Command.run_in_terminal(command=command, keep=True)


class Functional:

    @classmethod
    def init_pump(cls):
        GpioHandler.setup(GlobalVar.suction_pump_pins[0], GpioHandler.OUT)
        GpioHandler.setup(GlobalVar.suction_pump_pins[1], GpioHandler.OUT)

    @classmethod
    def turn_on_pump(cls):
        GpioHandler.output(GlobalVar.suction_pump_pins[1], GpioHandler.LOW)
        time.sleep(0.5)
        GpioHandler.output(GlobalVar.suction_pump_pins[0], GpioHandler.HIGH)

    @classmethod
    def turn_off_pump(cls):
        GpioHandler.output(GlobalVar.suction_pump_pins[1], GpioHandler.HIGH)
        GpioHandler.output(GlobalVar.suction_pump_pins[0], GpioHandler.LOW)
        time.sleep(0.05)
        GpioHandler.output(GlobalVar.suction_pump_pins[0], GpioHandler.HIGH)

    @classmethod
    def clear_pump(cls):
        GpioHandler.cleanup(*GlobalVar.suction_pump_pins)

    @classmethod
    def init_lidar(cls):
        GpioHandler.setup(GlobalVar.radar_control_pin, GpioHandler.OUT)

    @classmethod
    def open_radar(cls):
        GpioHandler.setup(GlobalVar.radar_control_pin, GpioHandler.OUT)
        GpioHandler.output(GlobalVar.radar_control_pin, GpioHandler.HIGH)
        roslaunch('myagv_odometry myagv_active.launch')

    @classmethod
    def close_radar(cls):
        GpioHandler.setup(GlobalVar.radar_control_pin, GpioHandler.OUT)
        GpioHandler.output(GlobalVar.radar_control_pin, GpioHandler.LOW)
        if Command.alive("myagv_active.launch"):
            Command.kill("myagv_active.launch")

    @classmethod
    def clear_radar(cls):
        GpioHandler.cleanup(GlobalVar.radar_control_pin)

    @classmethod
    def check_radar_running(cls):
        return Command.alive("myagv_active.launch") or GpioHandler.ishigh(GlobalVar.radar_control_pin)

    @classmethod
    def open_keyboard_control(cls):
        roslaunch("myagv_teleop", "myagv_teleop.launch", workspace=False)  # keyboard

    @classmethod
    def close_keyboard_control(cls):
        Command.kill("myagv_teleop.launch")

    @classmethod
    def open_navigation(cls):
        # 多点导航
        roslaunch("myagv_navigation", "logistics_navigation_active.launch")

    @classmethod
    def close_navigation(cls):
        Command.kill("logistics_navigation_active.launch")

    @classmethod
    def check_navigation_running(cls):
        return Command.alive("multipoint_navigation_active.launch")

