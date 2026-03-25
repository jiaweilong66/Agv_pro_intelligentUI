#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
import math
import re
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pyzbar import pyzbar
from components.camera import QCameraMiddleware

# 尝试导入 PaddlePaddle，如果失败则使用模拟模式
try:
    import paddle.utils
    from paddleocr import PaddleOCR
    paddle.utils.run_check()
    paddle.disable_signal_handler()
    PADDLE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    print("Warning: PaddlePaddle not found, OCR functionality will be limited")
    PADDLE_AVAILABLE = False
    PaddleOCR = None


class CodeType:
    ARUCO = "ARUCO"
    QR = "QR"
    OCR = "OCR"


class ARUCOCodeDetector(QCameraMiddleware):
    def __init__(self):
        super().__init__()
        self.pose_data_dict = {}
        self.marker_length = 0.04  # -- Here, the measurement unit is metre.0.055 is for orgianl big
        # Camera internals 摄像头的内部参数矩阵
        self.camera_matrix = np.array(
            [
                [785.855437, 0.000000, 451.670922],
                [0.000000, 584.820336, 259.056856],
                [0.000000, 0.000000, 1.000000]
            ]
        )
        # 畸变系数矩阵
        self.dist_coefficient = np.array(([[0.095135, -0.109279, -0.002513, -0.002418, 0.000000]]))
        self.R_flip = np.zeros((3, 3), dtype=np.float32)
        self.R_flip[0, 0] = 1.0
        self.R_flip[1, 1] = -1.0
        self.R_flip[2, 2] = -1.0
        self.pose_data = [None, None, None, None, None, None]

    @staticmethod
    def _is_rotation_matrix(R):
        """
        Checks if a matrix is a valid rotation matrix.

        :param R:    rotation matrix
        :return:     [bool] True or False
        """
        Rt = np.transpose(R)
        shouldBeIdentity = np.dot(Rt, R)
        I = np.identity(3, dtype=R.dtype)
        n = np.linalg.norm(I - shouldBeIdentity)
        return n < 1e-6

    @staticmethod
    def _rotation_matrix_to_euler_angles(R):
        """
        Calculates rotation matrix to euler angles

        :param R:     rotation matrix
        :return:      [np.array] roll, pitch, yaw
        """
        assert ARUCOCodeDetector._is_rotation_matrix(R)

        sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
        singular = sy < 1e-6

        if not singular:
            x = math.atan2(R[2, 1], R[2, 2])
            y = math.atan2(-R[2, 0], sy)
            z = math.atan2(R[1, 0], R[0, 0])
        else:
            x = math.atan2(-R[1, 2], R[1, 1])
            y = math.atan2(-R[2, 0], sy)
            z = 0

        return np.array([x, y, z])

    def _detect(self, corners, ids, imgWithAruco):
        """
        Show the Axis of aruco and return the x,y,z(unit is cm), roll, pitch, yaw

        :param corners:        get from cv2.aruco.detectMarkers()
        :param ids:            get from cv2.aruco.detectMarkers()
        :param imgWithAruco:   assign imRemapped_color to imgWithAruco directly
        :return:               x,y,z (units is cm), roll, pitch, yaw (units is degree)
        """
        if len(corners) <= 0:
            return None

        x1 = (int(corners[0][0][0][0]), int(corners[0][0][0][1]))
        x2 = (int(corners[0][0][1][0]), int(corners[0][0][1][1]))
        x3 = (int(corners[0][0][2][0]), int(corners[0][0][2][1]))
        x4 = (int(corners[0][0][3][0]), int(corners[0][0][3][1]))
        # Drawing detected frame white color
        # OpenCV stores color images in Blue, Green, Red
        cv2.line(imgWithAruco, x1, x2, (255, 0, 0), 1)
        cv2.line(imgWithAruco, x2, x3, (255, 0, 0), 1)
        cv2.line(imgWithAruco, x3, x4, (255, 0, 0), 1)
        cv2.line(imgWithAruco, x4, x1, (255, 0, 0), 1)
        # font type hershey_simpex
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(imgWithAruco, 'C1', x1, font, 1, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(imgWithAruco, 'C2', x2, font, 1, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(imgWithAruco, 'C3', x3, font, 1, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(imgWithAruco, 'C4', x4, font, 1, (255, 255, 255), 1, cv2.LINE_AA)
        if ids is not None:  # if aruco marker detected
            rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(
                corners,
                self.marker_length,
                self.camera_matrix,
                self.dist_coefficient
            )

            for i in range(rvec.shape[0]):
                imgWithAruco = cv2.drawFrameAxes(
                    imgWithAruco,
                    self.camera_matrix,
                    self.dist_coefficient,
                    rvec,
                    tvec,
                    self.marker_length
                )

                frame_makers = cv2.aruco.drawDetectedMarkers(imgWithAruco.copy(), corners)
                self.set_frame(frame_makers)
            # --- The midpoint displays the ID number
            cornerMid = (int((x1[0] + x2[0] + x3[0] + x4[0]) / 4), int((x1[1] + x2[1] + x3[1] + x4[1]) / 4))

            # cv2.putText(frame, "id=" + str(ids), cornerMid, font, 1, (255, 255, 255), 1, cv2.LINE_AA)

            rvec = rvec[0][0]
            tvec = tvec[0][0]
            # --- Print the tag position in camera frame
            str_position = "MARKER Position x=%.4f (cm)  y=%.4f (cm)  z=%.4f (cm)" % (
                tvec[0] * 100,
                tvec[1] * 100,
                tvec[2] * 100
            )
            # -- Obtain the rotation matrix tag->camera
            R_ct = np.matrix(cv2.Rodrigues(rvec)[0])
            R_tc = R_ct.T
            # -- Get the attitude in terms of euler 321 (Needs to be flipped first)
            roll_marker, pitch_marker, yaw_marker = self._rotation_matrix_to_euler_angles(self.R_flip * R_tc)
            # -- Print the marker's attitude respect to camera frame
            str_attitude = "MARKER Attitude degrees r=%.4f  p=%.4f  y=%.4f" % (
                math.degrees(roll_marker),
                math.degrees(pitch_marker),
                math.degrees(yaw_marker)
            )
            print(str_position)
            self.pose_data[0] = tvec[0] * 100
            self.pose_data[1] = tvec[1] * 100
            self.pose_data[2] = tvec[2] * 100
            self.pose_data[3] = math.degrees(roll_marker)
            self.pose_data[4] = math.degrees(pitch_marker)
            self.pose_data[5] = math.degrees(yaw_marker)

            self.pose_data_dict[ids] = self.pose_data

            roll_deg = math.degrees(roll_marker)
            pitch_deg = math.degrees(pitch_marker)
            yaw_deg = math.degrees(yaw_marker)

            if abs(yaw_deg) % 90.0 < 30:
                return [tvec[0] * 100, tvec[1] * 100, tvec[2] * 100, roll_deg, pitch_deg, yaw_deg, cornerMid]
            else:
                return None

    def __call__(self, raw_frame: np.array):
        frame = raw_frame
        # frame = cv2.flip(raw_frame, -1)  # 垂直镜像翻转
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 灰度化
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)  # 设置预定义的字典

        parameters = cv2.aruco.DetectorParameters()  # 使用默认值初始化检测器参数

        # 使用aruco.detectMarkers()函数可以检测到marker，返回ID和标志板的4个角点坐标
        corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        if ids is not None:
            frame_makers = cv2.aruco.drawDetectedMarkers(frame.copy(), corners, ids)
            ids_len = len(ids)

            res = []
            if ids_len > 0:
                for i in range(ids_len):
                    # 输入四个角点坐标，计算并返回x,y,z (units is cm), roll, pitch, yaw (units is degree),Aruco id
                    aruco_res = self._detect(corners[i:i + 1], ids[i][0], frame)
                    if aruco_res is not None:
                        res.append(aruco_res)
                    i += 1
            self.set_frame(frame_makers)
            return res, ids

        else:
            self.set_frame(frame.copy())
            return None


class OCRCodeDetector(QCameraMiddleware):
    def __init__(self, font_path="./SIMFANG.TTF", font_size=40):
        super().__init__()
        logging.basicConfig(level=logging.ERROR)
        
        if PADDLE_AVAILABLE and PaddleOCR is not None:
            self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        else:
            self.paddle_ocr = None
            print("Warning: PaddleOCR not available, OCR detection disabled")
            
        try:
            self.font = ImageFont.truetype(font_path, font_size)
        except:
            self.font = ImageFont.load_default()
            
        self.text_color = (0, 255, 0)
        self.time_out = 30
        self.start_time = time.time()

    def __call__(self, raw_frame: np.array):
        if self.paddle_ocr is None:
            # 模拟模式：在图像上显示提示信息
            cv2.putText(raw_frame, "OCR Not Available (Mock Mode)", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            self.set_frame(raw_frame)
            return None
            
        self.set_frame(raw_frame)
        ocr_result_list = self.paddle_ocr.ocr(raw_frame, cls=True)
        for ocr_result in ocr_result_list:
            if ocr_result is None:
                continue
            for word_info in ocr_result:
                text = word_info[1][0]
                box = word_info[0]
                cv2.polylines(
                    raw_frame, [np.array(box).astype(np.int32)], isClosed=True, color=(0, 255, 0), thickness=2
                )
                pil_image = Image.fromarray(raw_frame)
                draw = ImageDraw.Draw(pil_image)

                bbox = draw.textbbox((0, 0), text, font=self.font)
                box_x0, box_y0, box_x1, box_y1 = bbox
                text_width = box_x1 - box_x0
                text_height = box_y1 - box_y0

                center_x = (box[0][0] + box[2][0]) / 2
                center_y = (box[0][1] + box[2][1]) / 2
                text_x = center_x - text_width / 2
                text_y = center_y - text_height / 2

                draw.text((text_x, text_y), text, font=self.font, fill=self.text_color)

                char_frame = np.array(pil_image)
                self.set_frame(char_frame)
                return text


class QRCodeDetector(QCameraMiddleware):
    def __init__(self, font_path, font_size=25):
        super().__init__()
        self.font_path = font_path
        self.font_size = font_size
        self.font = ImageFont.truetype(self.font_path, self.font_size)
        self.time_out = 60
        self.text_color = (0, 255, 0)
        self.camera_matrix = np.array([
            [827.29511682, 0., 368.87666292],
            [0., 824.88958537, 262.03016541],
            [0., 0., 1.]])

        self.marker_size = 0.027
        self.dist_coefficient = np.array(([[0.21780081, -0.56324781, 0.01165061, 0.01845253, -1.0631406]]))

        self.marker_points = np.array(
            [
                [-self.marker_size / 2, self.marker_size / 2, 0],
                [self.marker_size / 2, self.marker_size / 2, 0],
                [self.marker_size / 2, -self.marker_size / 2, 0],
                [-self.marker_size / 2, -self.marker_size / 2, 0]
            ],
            dtype=np.float32)

    def __call__(self, raw_frame: np.array):
        city = "未知城市"
        decode_objects = pyzbar.decode(raw_frame)
        if not decode_objects:
            self.set_frame(raw_frame)
            return None

        for decode_object in decode_objects:
            qr_data = decode_object.data.decode("utf-8")
            print(f"QR Code Data: {qr_data}")
            match = re.search(r'地址：(.+?市)', qr_data)
            if match is not None:
                city = match.group(1)
                if "省" in city:
                    parts = city.split("省")
                    city = parts[-1]
                print(f"City: {city}")
            else:
                print("未找到城市信息")

            points = decode_object.polygon
            if len(points) != 4:
                continue
            pts = np.array(points, dtype=np.int32)
            cv2.polylines(raw_frame, [pts], isClosed=True, color=(255, 0, 0), thickness=2)
            _, rvec, tvec, = cv2.solvePnP(self.marker_points, np.float32(pts), self.camera_matrix,
                                          self.dist_coefficient)
            tvec = tvec.T.reshape(1, 1, 3)

            x, y, w, h = cv2.boundingRect(pts)
            pil_image = Image.fromarray(raw_frame)
            draw = ImageDraw.Draw(pil_image)
            bbox = draw.textbbox((x, y), qr_data, font=self.font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            text_x = x + (w - text_width) // 2
            text_y = y + (h - text_height) // 2

            draw.text((text_x, text_y), qr_data, font=self.font, fill=self.text_color)
            qr_frame = np.array(pil_image)

            self.set_frame(qr_frame)
            return city, tvec
