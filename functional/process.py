#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
import time
import traceback
import typing as T
import numpy as np
from components.camera import QCameraStreamCapture
from functional.roslaunch import Functional
from functional.depend.global_var import Goals, Position, Height, city_to_region_mapping, recognized_ocr_texts
from functional.depend.transformation import homo_transform_matrix
from functional.depend.navigation import MapNavigation
from functional.depend.controller_api import MechArmController
from functional.depend.wit_usb2can import CANSerialParser

import rospy
from geometry_msgs.msg import Twist
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget


class ARUCODetectionProcess(object):
    def __init__(self, camera_capture: QCameraStreamCapture):
        self.publisher = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.camera_capture = camera_capture

    def pub_vel(self, x, y, theta):
        twist = Twist()
        twist.linear.x = x
        twist.linear.y = y
        twist.linear.z = 0
        twist.angular.x = 0
        twist.angular.y = 0
        twist.angular.z = theta
        self.publisher.publish(twist)

    def stop(self):
        self.pub_vel(0, 0, 0)

    def rot_once(self, _dir=1, time_gap_input=0.5, sp=0.9, notIgnoreQR=True):
        self.pub_vel(0, 0, sp * _dir)

        time_ini = time.time()
        while True:
            _time_gap = time.time() - time_ini
            res = self.process_qr_data()
            if res != -1 and notIgnoreQR:
                self.stop()
                return 1

            if _time_gap > time_gap_input:
                self.stop()
                return 0

    def horizontal_rot_once(self, _dir=1, time_gap_input=0.5, sp=0.9, notIgnoreQR=True):
        self.pub_vel(0, sp * _dir, 0)

        time_ini = time.time()
        while True:
            _time_gap = time.time() - time_ini
            res = self.process_qr_data()
            if res != -1 and notIgnoreQR:
                # print ("res is " + str(res))
                self.stop()
                return 1

            if _time_gap > time_gap_input:
                self.stop()
                return 0

    def stage_quick_rot(self, fir_dir=1, first_rot_times=3, second_rot_times=6):
        time_wait = 1

        print("Start stage quick rot")

        def rot_dir_times(_dir, _times):
            for i in range(_times):
                # check qr first
                res = self.process_qr_data()
                if res != -1:
                    return 1

                # check rotation once then
                if self.rot_once(_dir):
                    return 1

                self.rot_once(1, time_wait, 0, False)

            print("Nothing find in this round")
            return 0

        if rot_dir_times(fir_dir, first_rot_times) == 1:
            print("counter clock found")
            return 1
        if rot_dir_times(-fir_dir, second_rot_times) == 1:
            print("clock found")
            return 1
        print("nothing found")
        return 0

    def stage_slow_rot(self, slow_rot_times=6):
        _dir = 1
        sp = 0.6
        time_gap = 0.60  # 旋转的时间

        # pre read some data
        self.rot_once(1, 1, 0)
        print("start_slow_rot")
        for i in range(slow_rot_times):
            res = self.process_qr_data()

            if res != -1:
                _perc = res[2]
                if _perc < 0.4:  # 让摄像头中心对齐画面分辨率中心
                    _dir = 1
                elif _perc > 0.6:
                    _dir = -1
                else:
                    print("slow move sucess ")
                    self.stop()
                    return 1

                self.rot_once(_dir, time_gap, sp, notIgnoreQR=False)

            else:
                if self.rot_once(1, 1, 0) != 1:
                    print("miss the target")
                    return -1

            self.rot_once(1, 1, 0, False)

        print("slow focus fail")
        return 0

    def front_once(self, time_gap=0.5, sp=0.32):  # 20 cm for 0.32sp with 0.5sec
        self.pub_vel(sp, 0, 0)

        time_ini = time.time()
        while True:
            _time_gap = time.time() - time_ini
            res = self.process_qr_data()
            if _time_gap > time_gap:
                self.stop()
                return 0

    def stages_rot(self, _dir=1, _first_dir_times=3, _second_dir_times=6):
        if self.stage_quick_rot(_dir, _first_dir_times, _second_dir_times):
            if self.stage_slow_rot(9):
                return 1
        return 0

    def Horizontal_movement(self, times=6):
        sp = 0.2
        time_gap = 0.50  # 平移的时间

        for i in range(times):
            res = self.process_qr_data()

            if res != -1:
                _perc = res[2]
                if _perc < 0.4:  # 让摄像头中心对齐画面分辨率中心
                    _dir = 1
                elif _perc > 0.6:
                    _dir = -1
                else:
                    print("horizontal move sucess ")
                    self.stop()
                    return 1

                self.horizontal_rot_once(_dir, time_gap, sp, notIgnoreQR=False)

            else:
                if self.rot_once(1, 1, 0) != 1:
                    print("miss the target")
                    return -1

            self.rot_once(1, 1, 0, False)

    def move_to_center(self):
        _dir = 1
        center_range = 25
        l_time_ratio = 1.4  # important

        # pre read some data
        self.rot_once(1, 1, 0, True)

        res = self.process_qr_data()

        if res != -1:
            l, angle = res[0], res[1]
            print("Step 2 :  found angle is " + str(angle))
            if angle > center_range:
                _dir = -1
            elif angle < -center_range:
                _dir = 1
            else:
                return 1  # 0 means done need to move

            # rotate and go forward
            self.rot_once(_dir, time_gap_input=1, sp=1, notIgnoreQR=False)
            self.front_once(time_gap=l / 100 * l_time_ratio, sp=0.5)

            # rotate back
            self.rot_once(-_dir, time_gap_input=0.8, sp=1, notIgnoreQR=False)
            if self.stages_rot(-_dir, 4, 6) == 0:
                return 0

            return 1
        else:
            print("miss target")
            return 0

    def process_qr_data(self):
        data_ = self.camera_capture.get_middleware_result()
        print(f"# Aruco data => {data_}")
        if data_ is not None:
            if not data_[0]:
                print("can't not dectet pose estimation of Aruco ")
                return -1  # 二维码的marker_length要大，而且marker_length参数要给对,不然没有位姿信息

            _z = data_[0][0][2]
            _ry = data_[0][0][4]
            _perc = data_[0][0][6][0] / 960.0  # 归一化[0,1],(892, 292)为二维码中心点坐标
            return _z, _ry, _perc  # 返回深度z,pitch,画面分辨率(960)的中心点
        else:
            return -1

    def main_process(self, first_dir=1):
        self.camera_capture.activate_middleware("ARUCO")
        # setup camera
        self.rot_once(1, 3, 0, False)

        print("Step 1")
        self.Horizontal_movement(6)  # 水平平移，让画面中心对齐ArUco码

        print("Step 2")
        # step 2: rotation and point
        if self.stages_rot(first_dir, 2, 5) == 0:  # 向右旋转2次，向左旋转5次，画面中心对齐ArUco码
            print("initial found failed")
            return 0

        # print ("Step 3")
        # step 3: move to center
        # if move_to_center() == 0:  #让小车odom跟ArUco码对齐同一直线，目前效果不好
        #    print ("Target not found")
        #    return 0

        print("Step 4")
        # step 4:
        while True:
            res = self.process_qr_data()  # 获取aruco二维码信息
            if res != -1:
                l = res[0]  # 摄像头到二维码的距离
                ag = res[1]  # 摄像头到二维码的角度
                print("l is " + str(l) + " angle is " + str(ag))

                if 30 < l:
                    if self.stage_slow_rot(6):  # 如果对齐二维码
                        res = self.process_qr_data()  # 获取aruco二维码信息
                        if res != -1:
                            self.front_once(2, 0.01)  # 前进时间长
                        continue
                    else:
                        self.stages_rot(1, 2, 4)  # 没对齐二维码旋转对齐

                elif 10 < l < 30:
                    if self.stage_slow_rot(6):  # 如果对齐二维码
                        res = self.process_qr_data()  # 获取aruco二维码信息
                        if res != -1:
                            self.front_once(1.9, 0.01)  # 前进 bug如果此时扫描不到二维码还是会前进
                        continue
                    else:
                        self.stages_rot(1, 2, 4)  # 没对齐二维码旋转对齐

                elif 5 < l < 10:
                    # one time up
                    self.front_once(0.21, sp=0.01)  # 前进0.21秒
                    print("Finsih doing")
                    continue

                elif l < 5:
                    # rot_once(1,1,0,0)
                    break

            else:  # 获取不到aruco二维码信息就退出循环
                print("Can't detect aruco.")
                self.pub_vel(0, 0, 0)
                break

        self.rot_once(1, 1, 0, False)  # 停止运动
        self.camera_capture.deactivate_middleware()


class BascProcess(QThread):
    finished = pyqtSignal(object, object)
    published = pyqtSignal(object, str)

    def process(self):
        raise NotImplementedError

    def notify_finished(self, result: T.Any = None):
        self.finished.emit(self, result)

    def notify_published(self, data: object):
        self.published.emit(self, data)

    def run(self):
        result = None
        try:
            result = self.process()
        except Exception as e:
            print(e)
            print(traceback.format_exc())
        finally:
            self.quit()
            self.notify_finished(result=result)


########################################################################################################################
# # 导航至货架区
########################################################################################################################
class NavigationToShelfProcess(BascProcess):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        self.map_navigation = MapNavigation()

    def terminate(self):
        self.map_navigation.cancel_navigation()
        super().terminate()

    def process(self):
        x_goal, y_goal, orientation_z, orientation_w = Goals.goal_1
        self.map_navigation.moveToGoal(x_goal, y_goal, orientation_z, orientation_w)


########################################################################################################################
# # 循环分拣
########################################################################################################################
class CircularSortingProcess(BascProcess):

    def __init__(self, number_cycle: int = 5, parent: QWidget = None):
        super().__init__(parent=parent)
        self.number_cycle = number_cycle
        self.agv_camera_capture: QCameraStreamCapture = parent.agv_camera_capture
        self.arm_camera_capture: QCameraStreamCapture = parent.arm_camera_capture
        self.map_navigation = MapNavigation()
        self.ocr_recognition = []
        self.boxes_with_text = []
        self.controller = MechArmController("/dev/ttyACM0", 115200)  # 连接机械臂
        self.controller.send_angles(Position.move_init, 50)
        self.log = logging.getLogger("console")

    def terminate(self):
        self.map_navigation.cancel_navigation()
        super().terminate()

    def load(self):
        self.controller.send_angles([0, 0, 0, 0, 0, 0], 60)
        self.controller.send_angles(Position.place_init, 50)

        coords_s = self.controller.get_coords()  # 获取当前位姿

        coords_s[2] -= 70
        self.controller.send_coords(coords_s, 40)  # z轴下降

        Functional.turn_on_pump()
        time.sleep(2)

        coords_s = self.controller.get_coords()
        coords_s[2] += 70

        self.controller.send_coords(coords_s, 40)  # z轴抬高

        self.controller.send_angles(Position.place_point4, 50)

        self.controller.send_angles(Position.place_point2, 50)

        self.controller.send_angles(Position.place_point3, 50)

        Functional.turn_off_pump()
        time.sleep(2)

        # 结束后复位
        self.controller.send_angles(Position.move_init, 50)

    def pickup(self, angle_watch, box_height: int = 101) -> str:  # i=1,快递盒子一次只吸取一个，先识别一层
        qr_texts = None
        self.controller.send_angles(angle_watch, 50)  # 相机拍照位
        self.arm_camera_capture.activate_middleware("QR")
        while True:
            data = self.arm_camera_capture.get_middleware_result()  # 获取QR码城市信息和tvec位移矩阵
            if data is None:
                continue

            qr_texts, tvecs = data
            print("# =================================================================================================")
            print("# =================================================================================================")
            print(f"# # {qr_texts}")
            print("# =================================================================================================")
            print("# =================================================================================================")
            self.arm_camera_capture.deactivate_middleware()
            self.log.info(f"QR delivered: {qr_texts}")
            self.log.info(f"QR code location information: {tvecs}")

            if qr_texts is None:
                self.log.error("qr scanner failed")
                continue

            curr_coords = self.controller.get_coords()  # 获取当前位姿
            self.log.info(f"current coordinates: {curr_coords}")

            # 矩阵乘积，mat表达了描述机械臂从当前位姿到固定位姿的变换过程的齐次变换矩阵。(-10, -45, 10, 0, 0, 0)为手眼矩阵
            mat = homo_transform_matrix(*curr_coords) @ homo_transform_matrix(-10, -35, 10, 0, 0, 0)

            # 将列表第一个二维码的tvec位移矩阵转为齐次坐标
            p_end = np.vstack([np.reshape(tvecs[0], (3, 1)), 1])

            # 将转换矩阵与齐次坐标形式的二维码位移向量相乘，得到[x,y,z,1]并去除最后一个元素(齐次坐标)，最后转为整数类型。
            p_base = np.squeeze((mat @ p_end)[:-1]).astype(int)

            # X error compensation
            p_base[0] += 0

            # Y error compensation
            p_base[1] += 20

            # Z轴固定高度
            p_base[2] = box_height

            # 将x,y,z和当前姿态进行连接成一个新数组
            new_coords = np.concatenate([p_base, curr_coords[3:]])
            self.log.info(f"new coordinates: {new_coords}")
            self.controller.send_coords(list(new_coords), 20)

            self.log.info("turn on pump")
            Functional.turn_on_pump()
            time.sleep(2)

            curr_coords = self.controller.get_coords()  # 获取当前位姿

            curr_coords[2] += 40  # z轴抬高
            self.log.info("axis Z up")
            self.controller.send_coords(curr_coords, 40)  # z轴抬高

            self.controller.send_angles(Position.pick_point2, 50)
            time.sleep(1)

            self.controller.send_angles(Position.place_init, 50)
            time.sleep(2)

            height = 45
            coords_s = self.controller.get_coords()  # 获取当前位姿
            self.log.info(f"get current pose => {coords_s} ")

            coords_s[2] -= height
            self.log.info("axis z down")
            self.controller.send_coords(coords_s, 40)  # z轴下降

            self.log.info("turn off pump")
            Functional.turn_off_pump()

            coords_s[2] += height
            self.controller.send_coords(coords_s, 40)  # z轴抬高
            time.sleep(2)

            self.controller.send_angles(Position.place_point4, 50)  # 过渡点，防止撞掉盒子
            time.sleep(2)
            break

        # 结束后复位
        self.controller.send_angles(Position.move_init, 50)
        return qr_texts

    def process(self):  # 导航初始动作
        for text, box_goal_1, box_goal_2 in zip(recognized_ocr_texts, Goals.box_goals_1, Goals.box_goals_2):
            self.boxes_with_text.append({
                "text": text,
                "box_goals_1": box_goal_1,
                "box_goals_2": box_goal_2,
            })

        recognized_qr_texts = []
        for i in range(self.number_cycle):
            x_goal, y_goal, orientation_z, orientation_w = Goals.pack_goal
            flag_feed_goalReached = self.map_navigation.moveToGoal(x_goal, y_goal, orientation_z, orientation_w)
            if flag_feed_goalReached:
                ARUCODetectionProcess(camera_capture=self.agv_camera_capture).main_process(first_dir=-1)

                xGoal, yGoal, orientation_z, orientation_w, covariance = Goals.pack_pose
                self.map_navigation.set_pose(xGoal, yGoal, orientation_z, orientation_w, covariance)  # amcl重定位

                # 根据循环次数抓取,固定相机拍照位和吸取高度
                if i == 0:
                    box_height = Height.box_2_height
                elif i == 1:
                    box_height = Height.box_1_height
                elif i == 2:
                    box_height = Height.box_2_height
                elif i == 3:
                    box_height = Height.box_1_height
                else:
                    box_height = Height.box_1_height

                text = self.pickup(Position.pick_watch, box_height=box_height)
                self.notify_published(f"QR Text => {text}")
                recognized_qr_texts.append(text)  # 发送拍照相机关节角度和Z轴高度，抓取并返回识别文字

                # x平移1秒
                self.map_navigation.pub_vel(-0.1, 0, 0)
                time.sleep(2.5)
                self.map_navigation.pub_vel(0, 0, 0)

                # 旋转180°
                self.map_navigation.pub_vel(0, 0, -0.1)
                time.sleep(4)
                self.map_navigation.pub_vel(0, 0, 0)

                # x平移1秒
                self.map_navigation.pub_vel(0.1, 0, 0)
                time.sleep(2)

            else:
                print("failed")

            self.log.info(f"recognized_ocr_texts => {recognized_ocr_texts}")
            self.log.info(f"recognized_qr_texts => {recognized_qr_texts}")
            if not recognized_qr_texts:
                continue

            # 获取列表中的最后一个城市
            last_city = recognized_qr_texts[-1]    # 通过 OCR 获取的市级列表
            region = city_to_region_mapping.get(last_city, None)  # 上海市：华东区，返回华东区
            if region is None:
                continue

            self.agv_camera_capture.activate_middleware("OCR")
            # 查找与该区域对应的目标位置
            for box in self.boxes_with_text:
                if box["text"] != region:
                    continue
                # 获取该区域的两个个目标点
                box_goals_1 = box["box_goals_1"]
                box_goals_2 = box["box_goals_2"]

                # 遍历目标点和方向信息，依次导航到每个目标
                for target_num, goal in enumerate([box_goals_1, box_goals_2], 1):
                    # 目标坐标
                    x_goal, y_goal, orientation_z, orientation_w = goal
                    self.log.info(f"导航到{region}的目标{target_num}: x={x_goal}, y={y_goal}, 方向z={orientation_z}, 方向w={orientation_w}")
                    self.map_navigation.moveToGoal(x_goal, y_goal, orientation_z, orientation_w)

                recognized_ocr = self.agv_camera_capture.get_middleware_result()
                self.agv_camera_capture.deactivate_middleware()

                self.log.info(f"识别到{recognized_ocr},{region}快递即将搬运至{recognized_ocr}")

                ARUCODetectionProcess(camera_capture=self.agv_camera_capture).main_process(first_dir=-1)

                self.load()  # 导航完所有点进行放盒子
                self.map_navigation.pub_vel(-0.1, 0, 0)
                time.sleep(5.7)
                self.map_navigation.pub_vel(0, 0, 0)

        self.notify_published(recognized_qr_texts)


########################################################################################################################
# # 泊车充电
########################################################################################################################
class ParkingChargingProcess(BascProcess):

    def __init__(self, parent: T.Optional[QWidget] = None):
        super().__init__(parent=parent)
        self.map_navigation = MapNavigation()
        self.can_serial_parser = CANSerialParser('/dev/ttyUSB0', 9600, 1)

    def terminate(self):
        self.map_navigation.cancel_navigation()
        super().terminate()

    def process(self):
        x_goal, y_goal, orientation_z, orientation_w = Goals.goal_1_back  # 先导航到该点，避免撞到快递放置盒
        flag_feed_goalReached = self.map_navigation.moveToGoal(x_goal, y_goal, orientation_z, orientation_w)
        if flag_feed_goalReached:

            # x平移1秒
            self.map_navigation.pub_vel(0.1, 0, 0)
            time.sleep(6)
            self.map_navigation.pub_vel(0, 0, 0)

            # 旋转
            self.map_navigation.pub_vel(0, 0, 0.1)
            time.sleep(4.8)
            self.map_navigation.pub_vel(0, 0, 0)

            self.can_serial_parser.open()  # 打开usb串口
            # 发送AT 命令从透传模式进入AT指令模式
            self.can_serial_parser.send_at_commands(["AT+CG", "AT+AT"])

            while not rospy.is_shutdown():
                # 开始读取数据
                x_speed, z_speed, which_mode, infrared_bits = self.can_serial_parser.read_serial_data()

                if infrared_bits[7] == 0:
                    if which_mode == 0x01:
                        self.map_navigation.pub_vel(x_speed, 0, z_speed)
                    elif which_mode == 0xBB:  # 测压区
                        self.map_navigation.pub_vel(0, 0, 0)
                        time.sleep(1)
                        self.map_navigation.pub_vel(0, 0, 0.5)
                        time.sleep(1.15)
                        self.map_navigation.pub_vel(0, 0, 0)
                        time.sleep(0.5)
                        self.map_navigation.pub_vel(-0.1, 0, 0)
                        time.sleep(1)
                        self.map_navigation.pub_vel(0, 0, 0)
                    elif which_mode == 0xAA:  # 充电区
                        self.map_navigation.pub_vel(0, 0, 0)
                        time.sleep(1)
                        self.map_navigation.pub_vel(0, 0, -0.5)
                        time.sleep(1.15)
                        self.map_navigation.pub_vel(0, 0, 0)
                        time.sleep(0.5)
                        self.map_navigation.pub_vel(-0.1, 0, 0)
                        time.sleep(1)
                        self.map_navigation.pub_vel(0, 0, 0)
                        break
                    elif which_mode == 0xCF:
                        self.map_navigation.pub_vel(0, 0, 0)
                        break
                else:
                    self.map_navigation.pub_vel(0, 0, 0)
                    break

