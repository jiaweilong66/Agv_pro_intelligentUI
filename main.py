#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging
import sys
import time
import typing as T

import cv2

from cofniger import Config
from constant import GlobalVar

from components import OperationUI

from functional.roslaunch import Functional
from functional.detector import ARUCOCodeDetector, QRCodeDetector, OCRCodeDetector
from functional.process import BascProcess, NavigationToShelfProcess, CircularSortingProcess, ParkingChargingProcess
from functional.joystick import JoystickController
from components.stylesheet import Stylesheet
from components.resource import FileResource
from components.console import QConsoleHandler
from components.camera import QCameraStreamCapture, QCameraStream, QCameraMiddleware
from components.prompt import QPrompt

from utils import GpioHandler

from PyQt5.QtCore import QSize, QCoreApplication, QTranslator, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget

GpioHandler.setmode(GpioHandler.BCM)
Functional.init_lidar()
Functional.init_pump()
Functional.turn_off_pump()
_translate = QCoreApplication.translate


def wait_for_timeout(timeout: int = 0):
    a = 0.1
    while timeout > 0:
        timeout -= a
        time.sleep(a)
        QCoreApplication.processEvents()


def setup_console_handler(parent: QWidget = None) -> QConsoleHandler:
    return QConsoleHandler(
        formatter=logging.Formatter(
            fmt=Config.Logger.console_format,
            datefmt=Config.Logger.console_datefmt
        ),
        level=Config.Logger.console_level,
        parent=parent
    )


def setup_logger_config(debug: bool):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format=Config.Logger.basic_format,
        datefmt=Config.Logger.basic_datefmt,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Config.Logger.basic_filepath)
        ]
    )


class Flag:
    radar_running: T.Optional[bool] = None          # 雷达流程运行标识
    navigation_running: T.Optional[bool] = None     # 导航流程运行标识
    keyboard_running: bool = False                  # 键盘控制运行标识
    detector_running: bool = False                  # 检测器运行标识
    joystick_running: bool = False                  # 手柄控制运行标识
    quick_start_process: bool = False               # 快速启动流程标识

    circular_sorting_process: bool = False            # 排序流程运行标识
    parking_charging_process: bool = False            # 充电流程运行标识
    navigation_shelf_process: bool = False            # 导航流程运行标识


class IntelligentLogisticsManager(QWidget, OperationUI):
    def __init__(self):
        super().__init__()
        self.console = logging.getLogger(Config.Logger.console_name)
        self.file_resource = FileResource(Config.resource_path)
        self.console_handler = setup_console_handler(self)

        self.image_recognition_middlewares: T.Dict[str, QCameraMiddleware] = {}
        
        self.sorting_process: T.Optional[CircularSortingProcess] = None
        self.navigation_process: T.Optional[NavigationToShelfProcess] = None
        self.charging_process: T.Optional[ParkingChargingProcess] = None

        self.joystick_controller: T.Optional[JoystickController] = None

        self.agv_camera_capture: T.Optional[QCameraStreamCapture] = None
        self.arm_camera_capture: T.Optional[QCameraStreamCapture] = None

        self.prompt = QPrompt()
        self.application = QApplication.instance()
        self.translator = QTranslator(self)

    def setup_ui(self):
        self.setupUi(self)
        self.logger_browser.setReadOnly(True)
        size = self.geometry()
        screen = QDesktopWidget().screenGeometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
        self.setup_language_initial()

    def initialize(self):
        self.console_handler.setParent(self)
        self.console.addHandler(self.console_handler)
        self.console.info(_translate("MainWindow", "MyAGV Intelligent Logistics Management System Start"))

        self.prompt.setParent(self)
        self.prompt.setLogger(Config.Logger.console_name)

        self.setup_radar_control_button()
        self.setup_navigation_control_button()

        font_path = self.file_resource.get("font", "SIMFANG.TTF")
        self.image_recognition_middlewares = {
            "OCR": OCRCodeDetector(font_path=font_path),
            "QR": QRCodeDetector(font_path=font_path),
            "ARUCO": ARUCOCodeDetector()
        }

        self.console.info(_translate("MainWindow", "load image recognition middleware ..."))

        self.agv_camera_capture = self.start_camera_capture(GlobalVar.camera2D_pipline, cv2.CAP_GSTREAMER)
        if self.agv_camera_capture is not None:
            self.console.info(_translate("MainWindow", "MyAGV 2D Camera Start ..."))
        else:
            self.console.error(_translate("MainWindow", "MyAGV 2D Camera Start Failed ..."))

        self.arm_camera_capture = self.start_camera_capture(pipeline="/dev/video1")
        # self.arm_camera_capture = self.start_camera_capture(pipeline=find_camera_device(-1))
        if self.arm_camera_capture is not None:
            self.console.info(_translate("MainWindow", "MechArm 270 Camera Start ..."))
        else:
            self.console.error(_translate("MainWindow", "MechArm 270 Camera Start Failed ..."))

    def connect_signals(self):
        self.console_handler.outputted.connect(self.on_console_output)
        self.language_selection.currentTextChanged.connect(self.on_language_selection_changed)
        self.log_clear_button.clicked.connect(self.on_clear_log_handle)

        self.radar_control_button.clicked.connect(lambda: self.start_radar_control_handle())
        self.navigation_control_button.clicked.connect(lambda: self.start_navigation_control_handle())

        self.quick_start_button.clicked.connect(lambda: self.on_quick_start_handle())

        self.sorting_button.clicked.connect(lambda: self.on_sorting_process_handle())
        self.navigation_button.clicked.connect(lambda: self.on_navigation_process_handle())
        self.charging_button.clicked.connect(lambda: self.on_charging_process_handle())

        self.OCR_identification_button.clicked.connect(lambda: self.on_image_identification_handle("OCR"))
        self.QR_identification_button.clicked.connect(lambda: self.on_image_identification_handle("QR"))
        self.ARUCO_identification_button.clicked.connect(lambda: self.on_image_identification_handle("ARUCO"))

        self.joystick_control_button.clicked.connect(lambda: self.on_joystick_control_handle())
        self.keyboard_control_button.clicked.connect(lambda: self.on_keyboard_control_handle())

    def setup_radar_control_button(self):
        if Flag.radar_running is None:
            Flag.radar_running = Functional.check_radar_running()

        if not Flag.radar_running:
            self.radar_control_button.setStyleSheet(Stylesheet.Button.BlueButtonStyle)
            self.radar_control_button.setText(_translate("MainWindow", "Open"))
        else:
            self.radar_control_button.setStyleSheet(Stylesheet.Button.RedButtonStyle)
            self.radar_control_button.setText(_translate("MainWindow", "Close"))

    def setup_navigation_control_button(self):
        if Flag.navigation_running is None:
            Flag.navigation_running = Functional.check_navigation_running()
        if not Flag.navigation_running:
            self.navigation_control_button.setStyleSheet(Stylesheet.Button.BlueButtonStyle)
            self.navigation_control_button.setText(_translate("MainWindow", "Open"))
            Flag.navigation_running = False
        else:
            self.navigation_control_button.setStyleSheet(Stylesheet.Button.RedButtonStyle)
            self.navigation_control_button.setText(_translate("MainWindow", "Close"))
            Flag.navigation_running = True

    def start_radar_control_handle(self):
        if not Flag.radar_running:
            Functional.open_radar()
            Flag.radar_running = True
            self.console.info(_translate("MainWindow", "lidar open ..."))
        else:
            Functional.close_radar()
            Flag.radar_running = False
            self.console.info(_translate("MainWindow", "lidar close ..."))
        self.radar_control_button.setEnabled(True)
        self.setup_radar_control_button()

    def check_radar_running(self, prompt: bool = False) -> bool:
        # prompt参数指定radar不在运行时是否提示, 在运行返回True 则返回False
        if not Flag.radar_running and prompt is True:
            self.prompt.warning(
                _translate("MainWindow", "Warning"),
                _translate("MainWindow", "Please turn on the radar first")
            )
        return Flag.radar_running
    
    def check_navigation_running(self, prompt: bool = False) -> bool:
        if not Flag.navigation_running and prompt is True:
            self.prompt.warning(
                _translate("MainWindow", "Warning"),
                _translate("MainWindow", "Please turn on the navigation first")
            )
        return Flag.navigation_running

    def start_navigation_control_handle(self):
        if not Flag.navigation_running:
            if self.check_radar_running(prompt=True) is False:
                return

            Functional.open_navigation()
            self.console.info(_translate("MainWindow", "navigation open ..."))
            self.navigation_control_button.setStyleSheet(Stylesheet.Button.RedButtonStyle)
            self.navigation_control_button.setText(_translate("MainWindow", "Close"))
            Flag.navigation_running = True
        else:
            Functional.close_navigation()
            self.console.info(_translate("MainWindow", "navigation close ..."))
            self.navigation_control_button.setStyleSheet(Stylesheet.Button.BlueButtonStyle)
            self.navigation_control_button.setText(_translate("MainWindow", "Start"))
            Flag.navigation_running = False

    def on_quick_start_handle(self):
        # ##############################################################################################################
        # # Intelligent Logistics Task Quick Startup
        # ##############################################################################################################
        if Flag.quick_start_process is False:
            self.console.info(_translate("MainWindow", "process start ..."))
            self.quick_start_button.setText(_translate("MainWindow", "Close"))
            self.quick_start_button.setStyleSheet(Stylesheet.Button.RedButtonStyle)

            if Flag.quick_start_process is False:
                if Flag.radar_running is False:
                    self.start_radar_control_handle()

                wait_for_timeout(10)

                if Flag.navigation_running is False:
                    self.start_navigation_control_handle()

                wait_for_timeout(10)

                self.start_navigation_process_handle()
                Flag.quick_start_process = True

        else:
            self.quick_start_button.setText(_translate("MainWindow", "Quick Start"))
            self.quick_start_button.setStyleSheet(Stylesheet.Button.BlueButtonStyle)
            Flag.quick_start_process = False

    def start_sorting_process_handle(self):
        Flag.circular_sorting_process = True
        self.console.info(_translate("MainWindow", "sorting process start ..."))
        self.sorting_button.setStyleSheet(Stylesheet.Button.RedButtonStyle)
        self.navigation_button.setEnabled(False)
        self.charging_button.setEnabled(False)

        self.sorting_process = CircularSortingProcess(parent=self)
        self.sorting_process.published.connect(self.on_process_published_handle)
        self.sorting_process.finished.connect(self.on_process_finished_handle)
        self.sorting_process.start()

    def start_navigation_process_handle(self):
        Flag.navigation_shelf_process = True
        self.console.info(_translate("MainWindow", "navigation process start ..."))
        self.navigation_button.setStyleSheet(Stylesheet.Button.RedButtonStyle)
        self.sorting_button.setEnabled(False)
        self.charging_button.setEnabled(False)

        self.navigation_process = NavigationToShelfProcess(parent=self)
        self.navigation_process.finished.connect(self.on_process_finished_handle)
        self.navigation_process.published.connect(self.on_process_published_handle)
        self.navigation_process.start()

    def start_charging_process_handle(self):
        Flag.parking_charging_process = True
        self.console.info(_translate("MainWindow", "charging process start ..."))
        self.charging_button.setStyleSheet(Stylesheet.Button.RedButtonStyle)
        self.sorting_button.setEnabled(False)
        self.navigation_button.setEnabled(False)

        self.charging_process = ParkingChargingProcess(parent=self)
        self.charging_process.finished.connect(self.on_process_finished_handle)
        self.charging_process.published.connect(self.on_process_published_handle)
        self.charging_process.start()

    def on_navigation_process_handle(self):
        try:
            if self.check_radar_running(prompt=True) is False:
                return

            if self.check_navigation_running(prompt=True) is False:
                return
            
            if Flag.navigation_shelf_process is False:
                self.start_navigation_process_handle()
            else:
                self.console.info(_translate("MainWindow", "navigation to shelf process is running ..."))
                answer = self.prompt.question(
                    _translate("MainWindow", "Waring"),
                    _translate("MianWindow", "The current process is running, is it down?")
                )
                if answer is True:
                    self.console.info(_translate("MainWindow", "close navigation process"))
                    self.navigation_process.terminate()
        except Exception as e:
            self.console.debug(f"navigation process error: {e}")
            self.console.exception(e)

    def on_sorting_process_handle(self):
        try:
            if self.check_radar_running(prompt=True) is False:
                return

            if self.check_navigation_running(prompt=True) is False:
                return
            
            if Flag.circular_sorting_process is False:
                self.start_sorting_process_handle()
            else:
                self.console.info(_translate("MainWindow", "circular sorting process is running ..."))
                answer = self.prompt.question(
                    _translate("MainWindow", "Waring"),
                    _translate("MianWindow", "The current process is running, is it down?")
                )
                if answer is True:
                    self.console.info(_translate("MainWindow", "close circular sorting process"))
                    self.sorting_process.terminate()
        except Exception as e:
            self.console.debug(f"sorting process error: {e}")
            self.console.exception(e)

    def on_charging_process_handle(self):
        try:
            if self.check_radar_running(prompt=True) is False:
                return

            if self.check_navigation_running(prompt=True) is False:
                return

            if Flag.parking_charging_process is False:
                self.start_charging_process_handle()
            else:
                self.console.info(_translate("MainWindow", "parking charging process is running ..."))
                answer = self.prompt.question(
                    _translate("MainWindow", "Waring"),
                    _translate("MianWindow", "The current process is running, is it down?")
                )
                if answer is True:
                    self.console.info(_translate("MainWindow", "close parking charging process ..."))
                    self.charging_process.terminate()
        except Exception as e:
            self.console.debug(f"charging process error: {e}")
            self.console.exception(e)

    def on_process_finished_handle(self, process: BascProcess):
        if isinstance(process, ParkingChargingProcess):
            self.navigation_button.setEnabled(True)
            self.sorting_button.setEnabled(True)
            self.console.info(_translate("MainWindow", "charging process done."))
            self.charging_process = None
            Flag.parking_charging_process = False

            if Flag.quick_start_process:
                self.console.info(_translate("MainWindow", "intelligent logistics task done."))
                Flag.quick_start_process = False

        elif isinstance(process, NavigationToShelfProcess):
            self.sorting_button.setEnabled(True)
            self.charging_button.setEnabled(True)
            self.console.info(_translate("MainWindow", "navigation process done."))
            self.navigation_process = None
            Flag.navigation_shelf_process = False
            if Flag.quick_start_process:
                self.start_charging_process_handle()

        elif isinstance(process, CircularSortingProcess):
            self.navigation_button.setEnabled(True)
            self.charging_button.setEnabled(True)
            self.console.info(_translate("MainWindow", "sorting process done."))
            self.sorting_process = None
            Flag.circular_sorting_process = False
            if Flag.quick_start_process:
                self.start_navigation_process_handle()

    def on_process_published_handle(self, process: BascProcess, message: object):
        self.console.info(message)

    def start_camera_capture(self, pipeline: str, *args) -> QCameraStreamCapture:
        camera_stream_capture = QCameraStreamCapture(pipeline=pipeline, parent=self, size=QSize(320, 240), params=args)
        camera_stream_capture.streamed.connect(self.on_camera_stream_handle)
        for name, recognition_middleware in self.image_recognition_middlewares.items():
            camera_stream_capture.register_middleware(name, recognition_middleware)
        camera_stream_capture.start()
        return camera_stream_capture

    def on_image_identification_handle(self, code_type: str):
        button_sender = self.sender()
        identification_buttons = (
            self.OCR_identification_button,
            self.ARUCO_identification_button,
            self.QR_identification_button
        )
        if not Flag.detector_running:
            start_translate_table = {
                "OCR": _translate("MainWindow", "start OCR detector"),
                "ARUCO": _translate("MainWindow", "start ARUCO detector"),
                "QR": _translate("MainWindow", "start QR detector")
            }
            self.console.info(start_translate_table[code_type])
            if code_type in ("OCR", "ARUCO"):
                self.agv_camera_capture.activate_middleware(code_type)
            else:
                self.arm_camera_capture.activate_middleware(code_type)
            button_sender.setStyleSheet(Stylesheet.Button.RedButtonStyle)
            for button in identification_buttons:
                if button != button_sender:
                    button.setEnabled(False)
            Flag.detector_running = True
        else:
            stop_translate_table = {
                "OCR": _translate("MainWindow", "stop OCR detector"),
                "ARUCO": _translate("MainWindow", "stop ARUCO detector"),
                "QR": _translate("MainWindow", "stop QR detector")
            }
            self.console.info(stop_translate_table[code_type])
            if code_type in ("OCR", "ARUCO"):
                self.agv_camera_capture.deactivate_middleware()
            else:
                self.arm_camera_capture.deactivate_middleware()

            button_sender.setStyleSheet(Stylesheet.Button.BlueButtonStyle)
            for button in identification_buttons:
                button.setEnabled(True)
            Flag.detector_running = False

    def on_camera_stream_handle(self, camera_stream: QCameraStream):
        if camera_stream.pixmap is None:
            return

        if camera_stream.result is not None:
            stylesheet = "border:1px solid cyan;background-color: rgb(218, 218, 218);"
            self.console.info(camera_stream.result)
        else:
            stylesheet = "background-color: rgb(218, 218, 218);"

        if camera_stream.pipeline.startswith("/dev/video"):
            self.arm_camera_view.setStyleSheet(stylesheet)
            self.arm_camera_view.setPixmap(camera_stream.pixmap)
            self.arm_camera_view.update()
        else:
            self.agv_camera_view.setStyleSheet(stylesheet)
            self.agv_camera_view.setPixmap(camera_stream.pixmap)
            self.arm_camera_view.update()

    def on_joystick_control_handle(self):
        if Flag.joystick_running is False:
            if self.check_radar_running(prompt=True) is False:
                return

            self.console.info(_translate("MainWindow", "open joystick control ..."))
            self.joystick_control_button.setStyleSheet(Stylesheet.Button.RedButtonStyle)
            self.joystick_control_button.setText(_translate("MainWindow", "Close Joystick Control"))
            self.joystick_controller = JoystickController(parent=self)
            self.joystick_controller.noticed.connect(self.on_joystick_control_notice_handle)
            self.joystick_controller.start()
            Flag.joystick_running = True
        else:
            self.console.info(_translate("MainWindow", "close joystick control ..."))
            self.joystick_control_button.setStyleSheet(Stylesheet.Button.BlueButtonStyle)
            self.joystick_control_button.setText(_translate("MainWindow", "Open Joystick Control"))
            self.joystick_controller.stop_running()

    def on_joystick_control_notice_handle(self, message):
        if message == "Finishing":
            Flag.joystick_running = False
            self.joystick_controller = None
            self.joystick_control_button.setStyleSheet(Stylesheet.Button.BlueButtonStyle)
        else:
            self.console.info(message)

    def on_keyboard_control_handle(self):
        if not Flag.keyboard_running:
            if self.check_radar_running(prompt=True) is False:
                return

            Functional.open_keyboard_control()
            self.console.info(_translate("MainWindow", "open keyboard control ..."))
            self.keyboard_control_button.setStyleSheet(Stylesheet.Button.RedButtonStyle)
            self.keyboard_control_button.setText(_translate("MainWindow", "Close Keyboard Control"))
            Flag.keyboard_running = True
        else:
            Functional.close_keyboard_control()
            self.console.info(_translate("MainWindow", "close keyboard control ..."))
            self.keyboard_control_button.setStyleSheet(Stylesheet.Button.BlueButtonStyle)
            self.keyboard_control_button.setText(_translate("MainWindow", "Open Keyboard Control"))

    def on_language_selection_changed(self, language):
        if language == "英文":
            self.console.info(_translate("MainWindow", "language changed to english"))
        else:
            self.console.info(_translate("MainWindow", "language changed to chinese"))
        self.file_resource.dump_json({"language": language}, 'localConfig.json')
        self.setup_language_initial(language)

    def setup_language_initial(self, language: str = None):
        if language is None:
            language = self.file_resource.load_json('localConfig.json').get('language')
        else:
            self.language_selection.currentTextChanged.disconnect(self.on_language_selection_changed)

        if language in ("English", "英文"):
            self.application.removeTranslator(self.translator)

        elif language in ("Chinese", "中文"):
            language_filepath = self.file_resource.get('translation', 'zh_CN.qm')
            self.translator.load(language_filepath)
            self.application.installTranslator(self.translator)

        self.retranslateUi(self)
        self.language_selection.setCurrentText(language)
        self.language_selection.currentTextChanged.connect(self.on_language_selection_changed)

    def on_console_output(self, message):
        self.logger_browser.append(message)
        if not self.logger_browser.underMouse():
            end_cursor = self.logger_browser.textCursor().End
            self.logger_browser.moveCursor(end_cursor)
        self.logger_browser.ensureCursorVisible()
        self.logger_browser.update()

    def on_clear_log_handle(self):
        self.logger_browser.setEnabled(False)
        self.logger_browser.clear()
        self.logger_browser.setEnabled(True)

    def resizeEvent(self, event):
        self.agv_camera_view.clear()
        self.arm_camera_view.clear()

        if event.size().height() > 850:
            self.functionalWidget.setMinimumWidth(550)
            arm_camera_view_size = QSize(600, 400)
            agv_camera_view_size = QSize(600, 400)
        else:
            self.functionalWidget.setMinimumWidth(450)
            arm_camera_view_size = QSize(320, 240)
            agv_camera_view_size = QSize(320, 240)

        if self.agv_camera_capture is not None:
            self.agv_camera_capture.resize(agv_camera_view_size)

        if self.arm_camera_capture is not None:
            self.arm_camera_capture.resize(arm_camera_view_size)
        super().resizeEvent(event)

    def closeEvent(self, event):
        if self.arm_camera_capture is not None:
            self.console.info(f"close mecharm270 camera ...")
            self.arm_camera_capture.deactivate_middleware()
            self.arm_camera_capture.stopped()
            self.arm_camera_capture.terminate()

        if self.agv_camera_capture is not None:
            self.console.info(f"close agv camera ...")
            self.agv_camera_capture.deactivate_middleware()
            self.agv_camera_capture.stopped()
            self.agv_camera_capture.terminate()

        if Flag.radar_running is True:
            self.console.info("close radar ...")
            Functional.close_radar()

        if Flag.navigation_running is True:
            self.console.info("close navigation ...")
            Functional.close_navigation()

        Functional.clear_pump()
        self.console.info("clear pump pins ..")
        Functional.clear_radar()
        GpioHandler.cleanup()
        self.console.info("clear radar pins ..")
        self.console.info("close application ...")
        event.accept()


def main(debug: bool = Config.debug):
    setup_logger_config(debug=debug)
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    application = QApplication(sys.argv)
    Intelligent_logistics_manager = IntelligentLogisticsManager()
    Intelligent_logistics_manager.setup_ui()
    Intelligent_logistics_manager.connect_signals()
    Intelligent_logistics_manager.initialize()
    Intelligent_logistics_manager.show()
    sys.exit(application.exec_())


if __name__ == '__main__':
    main()
