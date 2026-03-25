#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import threading
import traceback
import typing as T
from functional.roslaunch import Functional

import pygame
from PyQt5.QtCore import QThread, QObject, pyqtSignal

# 尝试导入 ROS 和机械臂相关模块
try:
    import rospy
    from geometry_msgs.msg import Twist
    ROS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    print("Warning: ROS not found, joystick control will be limited")
    ROS_AVAILABLE = False
    rospy = None
    Twist = None

try:
    from pymycobot import MechArm270
    MYCOBOT_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    print("Warning: pymycobot not found, arm control will be limited")
    MYCOBOT_AVAILABLE = False
    MechArm270 = None

arm_speed = 10
init_angles = [90, 0, 0, 0, 90, 0]


class CmdVelPublisher:
    def __init__(self):
        if not ROS_AVAILABLE:
            print("[MOCK MODE] CmdVelPublisher initialized in mock mode")
            self.pub = None
            self.move_cmd = None
            self.rate = None
            self.active = False
            return
            
        self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.move_cmd = Twist()
        self.move_cmd.linear.x = 0
        self.move_cmd.linear.y = 0
        self.move_cmd.angular.z = 0
        self.rate = rospy.Rate(10)
        self.active = True
        self.publish_thread = threading.Thread(
            target=self.publish_cmd_vel, daemon=True
        )
        self.publish_thread.start()

    def pause(self):
        """Temporarily suspend publishing to allow other ROS nodes to drive the robot"""
        self.active = False
        print("[CmdVelPublisher] Paused (relinquished control of /cmd_vel)")
        
    def resume(self):
        """Resume joystick control publishing"""
        self.active = True
        print("[CmdVelPublisher] Resumed (taken control of /cmd_vel)")

    def publish_cmd_vel(self):
        if not ROS_AVAILABLE or rospy is None:
            return
        while not rospy.is_shutdown():
            if self.active and self.pub:
                self.pub.publish(self.move_cmd)
            self.rate.sleep()

    def set_speed(self, x: float = 0.0, y: float = 0.0, yaw: float = 0.0):
        if not ROS_AVAILABLE or self.move_cmd is None:
            print(f"[MOCK MODE] Set speed: x={x}, y={y}, yaw={yaw}")
            return
        self.active = True # Automatically resume on manual input
        self.move_cmd.linear.x = x
        self.move_cmd.linear.y = y
        self.move_cmd.angular.z = yaw


class JoystickController(QThread):
    """Joystick controller class"""
    noticed = pyqtSignal(str)
    
    def __init__(self, parent: QObject = None):
        super(JoystickController, self).__init__(parent=parent)
        self.previous_state = [0, 0, 0, 0, 0, 0]
        
        if MYCOBOT_AVAILABLE and MechArm270 is not None:
            try:
                self.mech_arm = MechArm270("/dev/ttyACM0")
            except:
                print("[MOCK MODE] MechArm270 not available")
                self.mech_arm = None
        else:
            self.mech_arm = None
            
        self.cmd_vel_publisher = CmdVelPublisher()
        self.gripper_value = 100
        self.hat_pressed = False
        self.__running = False

    @property
    def is_running(self):
        return self.__running

    def stop_running(self):
        self.__running = False

    def notice(self, msg: str):
        self.noticed.emit(msg)
        
    def joyaxis_motion_event_handle(self, event, joystick):
        axis = event.axis
        value = round(event.value, 2)
        if abs(value) == 1.0:
            self.previous_state[axis] = value
            if self.mech_arm:
                if axis == 0 and value == -1.00:
                    self.mech_arm.jog_coord(2, 1, arm_speed)
                elif axis == 0 and value == 1.00:
                    self.mech_arm.jog_coord(2, 0, arm_speed)
                if axis == 1 and value == 1.00:
                    self.mech_arm.jog_coord(1, 0, arm_speed)
                elif axis == 1 and value == -1.00:
                    self.mech_arm.jog_coord(1, 1, arm_speed)
                if axis == 2 and value == 1.00:
                    self.mech_arm.power_on()
            if axis == 4 and value == 1.00:
                self.cmd_vel_publisher.set_speed(x=-0.2)
            elif axis == 4 and value == -1.00:
                self.cmd_vel_publisher.set_speed(x=0.2)
            if axis == 3 and value == 1.00:
                self.cmd_vel_publisher.set_speed(y=-0.2)
            elif axis == 3 and value == -1.00:
                self.cmd_vel_publisher.set_speed(y=0.2)
            if axis == 5 and value == 1.00:
                self.cmd_vel_publisher.set_speed(yaw=-0.2)
            elif axis == 5 and value != 1.00:
                self.cmd_vel_publisher.set_speed()
        else:
            if self.previous_state[axis] != 0:
                self.cmd_vel_publisher.set_speed()
                if self.mech_arm:
                    self.mech_arm.stop()
                self.previous_state[axis] = 0

    def joybutton_down_event_handle(self, event, joystick):
        if not self.mech_arm:
            return
            
        if joystick.get_button(0) == 1:
            self.mech_arm.set_gripper_value(0, 70)
            # mc.send_angles([-90, 0, 0, 0, 90, 0],50)
            self.mech_arm.send_angles([-93.6, 1.93, 6.24, -0.17, 68.81, -6.24], 50)
             
        if joystick.get_button(1) == 1:
            Functional.turn_on_pump()
             
        if joystick.get_button(2) == 1:
            Functional.turn_off_pump()
             
        if joystick.get_button(3) == 1:
            self.mech_arm.set_gripper_value(100, 70)
             
        if joystick.get_button(4) == 1:
            self.mech_arm.release_all_servos()
        if joystick.get_button(5) == 1:
            self.cmd_vel_publisher.set_speed(yaw=0.2)
        if joystick.get_button(7) == 1:
            self.mech_arm.send_angles(init_angles, 100)
    
    def joyhat_motion_event_handle(self, event, joystick):
        if not self.mech_arm:
            return
            
        hat_value = joystick.get_hat(0)
        if hat_value == (0, -1):
            self.mech_arm.jog_coord(3, 0, arm_speed)
        elif hat_value == (0, 1):
            self.mech_arm.jog_coord(3, 1, arm_speed)
        elif hat_value == (-1, 0):
            self.mech_arm.jog_angle(6, 0, arm_speed)
        elif hat_value == (1, 0):
            self.mech_arm.jog_angle(6, 1, arm_speed)
        if hat_value != (0, 0):
            self.hat_pressed = True
        else:
            if self.hat_pressed:
                self.cmd_vel_publisher.set_speed()
                self.mech_arm.stop()
                self.hat_pressed = False
                
    def handle_event(self, event, joystick):
        if event.type == pygame.JOYAXISMOTION:
            self.joyaxis_motion_event_handle(event, joystick)

        if event.type == pygame.JOYBUTTONDOWN:
            self.joybutton_down_event_handle(event, joystick)
            
        if event.type == pygame.JOYBUTTONUP:
            if event.button == 5:
                self.cmd_vel_publisher.set_speed()
                
        if event.type == pygame.JOYHATMOTION:
            self.joyhat_motion_event_handle(event, joystick)
            
    def run(self):
        try:
            pygame.init()
            pygame.joystick.init()
            joystick_counter = pygame.joystick.get_count()
            if joystick_counter == 0:
                self.notice("No joystick detected")
                return

            self.__running = True
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            
            # Setup hardware (Pumps and MechArm) cleanly and safely here in background thread
            try:
                Functional.init_pump()
                Functional.turn_off_pump()
            except Exception as e:
                self.notice(f"Pump init failed: {e}")
                
            if MYCOBOT_AVAILABLE and self.mech_arm is not None:
                try:
                    self.mech_arm.send_angles(init_angles, 50)
                    self.mech_arm.set_gripper_state(0, 100)
                    import time
                    time.sleep(1)
                    self.mech_arm.set_fresh_mode(0)
                    print("init_ok")
                except Exception as e:
                    self.notice(f"Arm init failed: {e}")
            
            
            # 检查 ROS 是否可用
            if not ROS_AVAILABLE or rospy is None:
                self.notice("ROS not available, running in mock mode")
                # 在模拟模式下简单循环
                while self.__running:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.__running = False
                    pygame.time.wait(100)
            else:
                while not rospy.is_shutdown() and self.__running:
                    for event in pygame.event.get():
                        self.handle_event(event, joystick)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self.notice("Exception")
            print("Exception ...")
        finally:
            self.__running = False
            self.notice("Finishing")
            if self.mech_arm is not None:
                self.mech_arm.stop()
                self.mech_arm.close()
            pygame.joystick.quit()
            pygame.quit()
            Functional.turn_off_pump()
            Functional.clear_pump()
            print("Finished")
