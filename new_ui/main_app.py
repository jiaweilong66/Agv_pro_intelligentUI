#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
New Intelligent Logistics System UI
Main Application Entry Point - Integrated with original main.py interfaces
"""
import logging
import sys
import time
import typing as T

import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QSize, QCoreApplication, QTranslator, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage  # 【新增】必须导入 QPixmap 和 QImage
from PyQt5 import uic

from cofniger import Config
from constant import GlobalVar

from functional.roslaunch import Functional
from utils.command import Command
from functional.detector import ARUCOCodeDetector, QRCodeDetector, OCRCodeDetector
from functional.process import BascProcess, NavigationToShelfProcess, CircularSortingProcess, ParkingChargingProcess, SmartLogisticsProcess
from functional.joystick import JoystickController, CmdVelPublisher
from components.stylesheet import Stylesheet
from components.resource import FileResource
from components.console import QConsoleHandler
from components.camera import QCameraStreamCapture, QCameraStream, QCameraMiddleware
from components.prompt import QPrompt

from utils import GpioHandler

# Import virtual joystick widget
try:
    from new_ui.virtual_joystick import VirtualJoystick
except ImportError:
    from virtual_joystick import VirtualJoystick

# Try to import MechArm270
try:
    from pymycobot import MechArm270
    MYCOBOT_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    print("Warning: pymycobot not found, arm control will be limited")
    MYCOBOT_AVAILABLE = False
    MechArm270 = None

# Try to import and initialize ROS
try:
    import rospy
    ROS_AVAILABLE = True
    # Don't initialize ROS node here - it will block if roscore is not running
    # ROS node will be initialized when needed
    print("ROS libraries available")
except (ImportError, ModuleNotFoundError):
    print("Warning: ROS not found, some features will be limited")
    ROS_AVAILABLE = False
    rospy = None

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
    radar_running: T.Optional[bool] = None
    navigation_running: T.Optional[bool] = None
    keyboard_running: bool = False
    detector_running: bool = False
    joystick_running: bool = False
    quick_start_process: bool = False
    circular_sorting_process: bool = False
    parking_charging_process: bool = False
    navigation_shelf_process: bool = False
    ros_node_initialized: bool = False


def init_ros_node():
    """Initialize ROS node if not already initialized"""
    if not ROS_AVAILABLE or rospy is None:
        return False
    
    if Flag.ros_node_initialized:
        return True
    
    try:
        rospy.init_node('intelligent_logistics_ui', anonymous=True, disable_signals=True)
        Flag.ros_node_initialized = True
        print("ROS node initialized successfully")
        return True
    except rospy.exceptions.ROSException as e:
        print(f"ROS node initialization error: {e}")
        return False


class MainApplication(QStackedWidget):
    # Signals for thread-safe UI updates
    start_progress_timer_sig = pyqtSignal()
    stop_progress_timer_sig = pyqtSignal()
    thread_safe_log_sig = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Intelligent Logistics System")
        self.resize(1024, 768)
        
        # Logger and console setup
        self.console = logging.getLogger(Config.Logger.console_name)
        self.file_resource = FileResource(Config.resource_path)
        self.console_handler = setup_console_handler(self)
        
        # Image recognition middlewares
        self.image_recognition_middlewares: T.Dict[str, QCameraMiddleware] = {}
        
        # Process instances
        self.sorting_process: T.Optional[CircularSortingProcess] = None
        self.navigation_process: T.Optional[NavigationToShelfProcess] = None
        self.charging_process: T.Optional[ParkingChargingProcess] = None
        self.smart_logistics_process: T.Optional[SmartLogisticsProcess] = None
        
        # Controller
        self.joystick_controller: T.Optional[JoystickController] = None
        
        # Virtual controller components
        self.mech_arm = None
        self.cmd_vel_publisher = None
        self.gripper_value = 100
        self.arm_speed = 10
        self.init_angles = [90, 0, 0, 0, 90, 0]
        
        # Camera captures
        self.agv_camera_capture: T.Optional[QCameraStreamCapture] = None
        self.arm_camera_capture: T.Optional[QCameraStreamCapture] = None
        
        # Prompt and translator
        self.prompt = QPrompt()
        self.application = QApplication.instance()
        self.translator = QTranslator(self)
        
        # Load UI pages
        self.main_menu = uic.loadUi("new_ui/main_menu.ui")
        self.quick_start = uic.loadUi("new_ui/quick_start.ui")
        self.virtual_controller = uic.loadUi("new_ui/virtual_controller.ui")
        
        # Add pages to stack
        self.addWidget(self.main_menu)
        self.addWidget(self.quick_start)
        self.addWidget(self.virtual_controller)
        
        # Task progress tracking
        self.current_task_node = 0
        self.task_timer = QTimer()
        self.task_timer.timeout.connect(self.advance_task_progress)
        
        # Virtual joystick widgets
        self.arm_joystick = None
        self.agv_joystick = None
        
        # Virtual controller state
        self.arm_position = [0.0, 0.0]
        self.agv_position = [0.0, 0.0]
        
        # Initialize
        self.initialize()
        
        # Internal control flags and timers
        self._last_progress = ""
        self._progress_timer = QTimer(self)
        self._progress_timer.timeout.connect(self._poll_task_progress)
        
        # Connect signals
        self.start_progress_timer_sig.connect(self._on_start_progress_timer)
        self.stop_progress_timer_sig.connect(self._on_stop_progress_timer)
        self.thread_safe_log_sig.connect(self._sync_log_message)
        
        # Setup virtual controller joysticks
        self.setup_virtual_controller()
        
        # Connect signals
        self.setup_connections()
        
        # Show main menu first
        self.setCurrentWidget(self.main_menu)
        
    def initialize(self):
        """Initialize all components"""
        self.console_handler.setParent(self)
        self.console.addHandler(self.console_handler)
        self.console.info(_translate("MainWindow", "MyAGV Intelligent Logistics Management System Start"))
        
        self.prompt.setParent(self)
        self.prompt.setLogger(Config.Logger.console_name)
        
        self.setup_radar_control_button()
        self.setup_navigation_control_button()
        
        # Setup image recognition middlewares
        font_path = self.file_resource.get("font", "SIMFANG.TTF")
        self.image_recognition_middlewares = {
            "OCR": OCRCodeDetector(font_path=font_path),
            "QR": QRCodeDetector(font_path=font_path),
            "ARUCO": ARUCOCodeDetector()
        }
        
        self.console.info(_translate("MainWindow", "load image recognition middleware ..."))
        
        # Start cameras automatically on UI launch
        self.log_message("[SYSTEM] Starting UI cameras...")
        
        # Start AGV camera (CSI Camera)
        try:
            self.agv_camera_capture = self.start_camera_capture(GlobalVar.camera2D_pipline, cv2.CAP_GSTREAMER)
            if self.agv_camera_capture is not None:
                self.log_message("[CAMERA] ✓ AGV camera started")
            else:
                self.log_message("[CAMERA] ✗ AGV camera failed to start")
        except Exception as e:
            self.log_message(f"[CAMERA] Error starting AGV camera: {e}")
            self.agv_camera_capture = None
        
        # Start Arm camera (USB Camera)
        try:
            # Try /dev/video1 first, then fallback to /dev/video0
            for video_device in ["/dev/video1", "/dev/video0", 1, 0]:
                try:
                    self.arm_camera_capture = self.start_camera_capture(pipeline=video_device)
                    if self.arm_camera_capture is not None:
                        self.log_message(f"[CAMERA] ✓ Arm camera started on {video_device}")
                        break
                except Exception as e:
                    continue
            
            if self.arm_camera_capture is None:
                self.log_message("[CAMERA] ✗ Arm camera failed to start")
        except Exception as e:
            self.log_message(f"[CAMERA] Error starting Arm camera: {e}")
            self.arm_camera_capture = None
        
        # Setup language
        self.setup_language_initial()
        
        self.log_message("[SYSTEM] ✓ UI initialization completed")
        self.log_message("[SYSTEM] Use Quick Start to run Smart Logistics workflow")
        
        # Initialize virtual controller components
        self.initialize_virtual_controller()
    
    def setup_virtual_controller(self):
        """Setup virtual joystick widgets"""
        # Create arm joystick
        self.arm_joystick = VirtualJoystick(labels={
            'up': 'Joint 2 Up',
            'down': 'Joint 2 Down',
            'left': 'Joint 1 Left',
            'right': 'Joint 1 Right'
        })
        self.arm_joystick.positionChanged.connect(self.on_arm_joystick_moved)
        
        # Create AGV joystick
        self.agv_joystick = VirtualJoystick(labels={
            'up': 'Forward',
            'down': 'Backward',
            'left': 'Left',
            'right': 'Right'
        })
        self.agv_joystick.positionChanged.connect(self.on_agv_joystick_moved)
        
        # Replace the placeholder labels with joystick widgets
        # Arm joystick
        arm_layout = self.virtual_controller.armJoystickLabel.parent().layout()
        arm_layout.replaceWidget(self.virtual_controller.armJoystickLabel, self.arm_joystick)
        self.virtual_controller.armJoystickLabel.deleteLater()
        
        # AGV joystick
        agv_layout = self.virtual_controller.agvJoystickLabel.parent().layout()
        agv_layout.replaceWidget(self.virtual_controller.agvJoystickLabel, self.agv_joystick)
        self.virtual_controller.agvJoystickLabel.deleteLater()
    
    def initialize_virtual_controller(self):
        """Initialize MechArm270 and CmdVelPublisher for virtual controller"""
        try:
            # Initialize MechArm270
            if MYCOBOT_AVAILABLE and MechArm270 is not None:
                try:
                    self.mech_arm = MechArm270("/dev/ttyACM0")
                    self.console.info("[ARM] MechArm270 initialized successfully")
                except Exception as e:
                    self.console.warning(f"[ARM] MechArm270 not available: {e}")
                    self.mech_arm = None
            else:
                self.console.warning("[ARM] pymycobot not installed, arm control disabled")
                self.mech_arm = None
            
            # Initialize CmdVelPublisher for AGV control (requires ROS)
            # Don't initialize here - will be initialized when radar is started
            self.cmd_vel_publisher = None
            self.console.info("[AGV] CmdVelPublisher will be initialized when needed")
            
        except Exception as e:
            self.console.error(f"[CONTROLLER] Virtual controller initialization error: {e}")


    def setup_connections(self):
        """Connect all button signals"""
        # Console output
        self.console_handler.outputted.connect(self.on_console_output)
        
        # Main menu buttons
        self.main_menu.quickStartButton.clicked.connect(self.show_quick_start)
        self.main_menu.controllerButton.clicked.connect(self.show_virtual_controller)
        self.main_menu.parametersButton.clicked.connect(self.show_parameters)
        
        # Quick start back button (Intelligent Logistics System button)
        self.quick_start.backButton.clicked.connect(self.show_main_menu)
        
        # Virtual controller back button
        self.virtual_controller.backButton.clicked.connect(self.show_main_menu)
        
        # Virtual controller buttons
        self.virtual_controller.gripperOpenButton.clicked.connect(self.on_gripper_open)
        self.virtual_controller.gripperCloseButton.clicked.connect(self.on_gripper_close)
        self.virtual_controller.pumpOnButton.clicked.connect(self.on_pump_on)
        self.virtual_controller.pumpOffButton.clicked.connect(self.on_pump_off)
        self.virtual_controller.lockArmButton.clicked.connect(self.on_lock_arm)
        self.virtual_controller.releaseArmButton.clicked.connect(self.on_release_arm)
        self.virtual_controller.resetButton.clicked.connect(self.on_reset_position)
        
        # Quick start function buttons
        self.quick_start.quickStartTaskButton.clicked.connect(self.on_quick_start_task)
        self.quick_start.lidarButton.clicked.connect(self.on_lidar_toggle)
        self.quick_start.navigationButton.clicked.connect(self.on_navigation_toggle)
        self.quick_start.moveToShelfButton.clicked.connect(self.on_move_to_shelf)
        self.quick_start.circularSortingButton.clicked.connect(self.on_circular_sorting)
        self.quick_start.arucoButton.clicked.connect(self.on_aruco_detect)
        self.quick_start.qrButton.clicked.connect(self.on_qr_detect)
        self.quick_start.joystickButton.clicked.connect(self.on_joystick_control)
        self.quick_start.keyboardButton.clicked.connect(self.on_keyboard_control)
        self.quick_start.clearLogButton.clicked.connect(self.on_clear_log)
        
        # Language selection
        self.quick_start.languageComboBox.currentTextChanged.connect(self.on_language_changed)
        
    # Navigation methods
    def show_main_menu(self):
        self.setCurrentWidget(self.main_menu)
        self.log_message("[SYSTEM] Returned to main menu")
        
    def show_quick_start(self):
        self.setCurrentWidget(self.quick_start)
        self.log_message("[INFO] Entered Quick Start mode")
    
    def show_virtual_controller(self):
        self.setCurrentWidget(self.virtual_controller)
        self.console.info("[INFO] Entered Virtual Controller mode")
        
    def show_parameters(self):
        self.log_message("[INFO] Product Parameters - Coming Soon")
    
    # Radar and Navigation Control
    def setup_radar_control_button(self):
        if Flag.radar_running is None:
            Flag.radar_running = Functional.check_radar_running()
        
        if not Flag.radar_running:
            self.quick_start.lidarButton.setStyleSheet("")
            self.quick_start.lidarButton.setText("Open/Close")
        else:
            self.quick_start.lidarButton.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; } QPushButton:hover { background-color: #c0392b; }")
            self.quick_start.lidarButton.setText("Close")
    
    def setup_navigation_control_button(self):
        if Flag.navigation_running is None:
            Flag.navigation_running = Functional.check_navigation_running()
        
        if not Flag.navigation_running:
            self.quick_start.navigationButton.setStyleSheet("")
            self.quick_start.navigationButton.setText("Open/Close")
            Flag.navigation_running = False
        else:
            self.quick_start.navigationButton.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; } QPushButton:hover { background-color: #c0392b; }")
            self.quick_start.navigationButton.setText("Close")
            Flag.navigation_running = True
    
    def check_radar_running(self, prompt: bool = False) -> bool:
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

    # Quick Start function handlers
    def on_quick_start_task(self):
        """Handle quick start task button - Run complete Smart Logistics workflow"""
        if not Flag.quick_start_process:
            self.log_message("[INFO] ========== Starting Intelligent Logistics Task ==========")
            self.log_message("[SYSTEM] Preparing system for Smart Logistics workflow...")
            
            # Reset all nodes to waiting state
            self.reset_task_nodes() # Reset all icons to blue first
            self.update_task_node(1, "waiting") # Explicitly set first node to waiting
            
            self.quick_start.quickStartTaskButton.setText(_translate("MainWindow", "Stop"))
            self.quick_start.quickStartTaskButton.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; } QPushButton:hover { background-color: #c0392b; }")
            
            # Start workflow directly (QTimer.singleShot used inside makes it non-blocking safely)
            self._start_quick_start_workflow_async()
            
            Flag.quick_start_process = True
            
        else:
            # Stop the workflow - only kill main.py, keep lidar and navigation running
            self.log_message("[SYSTEM] Stopping Smart Logistics task...")
            
            # Kill main.py and its child processes
            try:
                Command.kill("Smart_Logistics_Kit-22-map/main.py")
                Command.kill("agv_aruco")
                self.log_message("[SYSTEM] ✓ Smart Logistics main program stopped")
            except Exception as e:
                self.log_message(f"[SYSTEM] Warning: {e}")
            
            # Cancel any pending move_base goals so the robot stops moving
            try:
                import subprocess as _sp
                _sp.run("rostopic pub -1 /move_base/cancel actionlib_msgs/GoalID -- '{}' 2>/dev/null", 
                        shell=True, timeout=3)
                _sp.run("rostopic pub -1 /cmd_vel geometry_msgs/Twist '{linear: {x: 0}, angular: {z: 0}}' 2>/dev/null",
                        shell=True, timeout=3)
                self.log_message("[SYSTEM] ✓ Robot stopped moving")
            except Exception:
                pass
            
            # Clean up progress file
            try:
                import os
                progress_file = "/tmp/smart_logistics_progress.txt"
                if os.path.exists(progress_file):
                    os.remove(progress_file)
            except Exception:
                pass
            
            # Stop progress monitoring timer safely via signal
            self.stop_progress_timer_sig.emit()
            
            # Only reset the Quick Start button, leave lidar and navigation as-is
            self.quick_start.quickStartTaskButton.setText(_translate("MainWindow", "Quick Start"))
            self.quick_start.quickStartTaskButton.setStyleSheet("")
            self.reset_task_nodes()
            Flag.quick_start_process = False
            self.log_message("[INFO] Task stopped. Lidar and Navigation remain running.")
            
            # CRITICAL: Reconnect mechanical arm for UI virtual controller
            self.log_message("[SYSTEM] Reconnecting mechanical arm for UI...")
            try:
                from pymycobot.mecharm270 import MechArm270
                if MYCOBOT_AVAILABLE:
                    # Give a small delay for main.py to release the port
                    time.sleep(1)
                    self.mech_arm = MechArm270("/dev/ttyACM0")
                    self.log_message("[ARM] ✓ Mechanical arm reconnected for UI")
                else:
                    self.log_message("[ARM] MechArm270 not available")
            except Exception as e:
                self.log_message(f"[ARM] Warning: Could not reconnect mechanical arm: {e}")
                self.mech_arm = None
    
    def _start_quick_start_workflow_async(self):
        """Fully automated quick start: call UI native radar, navigation, then run main.py"""
        self.log_message("[INFO] Starting automated smart logistics tasks...")
        
        # Step 1: Start lidar
        self.log_message("[STEP 1/3] Starting Lidar System (a new terminal and RViz will pop up)...")
        if not Flag.radar_running:
            self.on_lidar_toggle()  # call native switch, yellow Starting... state, after 8s red and update Node
        else:
            self.log_message("[INFO] Lidar is already running.")
            self.update_task_node(1, "completed")
        
        # Delay 12 seconds to start navigation, avoid system freeze, let ROS Master and lidar stabilize
        self.log_message("[INFO] Waiting 12 seconds to ensure Lidar starts completely...")
        QTimer.singleShot(12000, self._start_navigation_step)

    def _start_navigation_step(self):
        """Step 2: Start Navigation"""
        self.log_message("[STEP 2/3] Starting Navigation System (a new terminal and RViz will pop up)...")
        if not Flag.navigation_running:
            # Skip lidar check prompt in Quick Start (radar is ensured in step 1)
            self.on_navigation_toggle(skip_radar_check=True)
        else:
            self.log_message("[INFO] Navigation is already running.")
            self.update_task_node(2, "completed")
        
        # on_navigation_toggle has a 12s internal Timer. Node 2 will be updated in _finalize_navigation_start
        # Wait for the navigation's 8s finalize then another 8s before starting main.py
        self.log_message("[INFO] Waiting 20 seconds to ensure navigation stability and node registration...")
        QTimer.singleShot(20000, self._start_main_py_step)

    def _start_main_py_step(self):
        """Step 3: Auto-start main.py"""
        self.update_task_node(3, "waiting") # Set node 3 to waiting before starting main.py
        self.log_message("[STEP 3/3] Base system is ready, automatically booting Smart Logistics Program...")
        
        # Call main application loop automatically
        self.start_smart_logistics_workflow()
    
    def advance_task_progress(self):
        """Advance to next task node (for demo purposes)"""
        self.current_task_node += 1
        
        if self.current_task_node == 1:
            self.update_task_node(1, "completed")
            self.log_message("[TASK] ✓ Node 1: Proceeding to loading area - COMPLETED")
        elif self.current_task_node == 2:
            self.update_task_node(2, "completed")
            self.log_message("[TASK] ✓ Node 2: Picking goods - COMPLETED")
        elif self.current_task_node == 3:
            self.update_task_node(3, "completed")
            self.log_message("[TASK] ✓ Node 3: Proceeding to unloading area - COMPLETED")
        elif self.current_task_node == 4:
            self.update_task_node(4, "completed")
            self.log_message("[TASK] ✓ Node 4: Unloading goods - COMPLETED")
        elif self.current_task_node == 5:
            self.update_task_node(5, "completed")
            self.log_message("[TASK] ✓ Node 5: Task SUCCESS!")
            self.log_message("[INFO] ========== All Tasks Completed Successfully ==========")
            self.task_timer.stop()
    
    def reset_task_nodes(self):
        """Reset all task nodes to initial state"""
        for i in range(1, 6):
            self.update_task_node(i, "waiting")
        for i in range(1, 5):
            connector_name = f"connector{i}"
            if hasattr(self.quick_start, connector_name):
                connector = getattr(self.quick_start, connector_name)
                connector.setStyleSheet("QLabel { background-color: #cccccc; }")
    
    def on_lidar_toggle(self):
        """Toggle lidar on/off"""
        if not Flag.radar_running:
            Flag.radar_running = True
            Functional.open_radar()
            
            # Show transitional UI state
            self.quick_start.lidarButton.setEnabled(False)
            self.quick_start.lidarButton.setText("Starting...")
            self.quick_start.lidarButton.setStyleSheet("QPushButton { background-color: #f39c12; color: white; }")
            self.log_message("[LIDAR] Starting Lidar odometry, please wait...")
            
            # Wait for 8s to confirm startup before showing as "Open"
            QTimer.singleShot(8000, self._finalize_lidar_start)
        else:
            Functional.close_radar()
            Flag.radar_running = False
            self.quick_start.lidarButton.setEnabled(True)
            self.quick_start.lidarButton.setText("Open/Close")
            self.quick_start.lidarButton.setStyleSheet("")
            self.log_message("[LIDAR] Lidar odometry stopped")
            
    def _finalize_lidar_start(self):
        if Flag.radar_running:
            self.quick_start.lidarButton.setEnabled(True)
            self.quick_start.lidarButton.setText("Close")
            self.quick_start.lidarButton.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; } QPushButton:hover { background-color: #c0392b; }")
            self.log_message("[LIDAR] Lidar odometry started successfully")
    
    def on_navigation_toggle(self, skip_radar_check=False):
        """Toggle navigation on/off"""
        if not Flag.navigation_running:
            # Only show prompt explicitly when manually clicking, skip during Quick Start
            if not skip_radar_check and self.check_radar_running(prompt=True) is False:
                return
            
            Flag.navigation_running = True
            Functional.open_navigation()
            
            # Show transitional UI state
            self.quick_start.navigationButton.setEnabled(False)
            self.quick_start.navigationButton.setText("Starting...")
            self.quick_start.navigationButton.setStyleSheet("QPushButton { background-color: #f39c12; color: white; }")
            self.log_message("[NAVIGATION] Starting Navigation system, please wait for AMCL localization...")
            
            # Wait for 12s to confirm AMCL alignment before showing as "Open"
            QTimer.singleShot(12000, self._finalize_navigation_start)
        else:
            Functional.close_navigation()
            Flag.navigation_running = False
            self.quick_start.navigationButton.setEnabled(True)
            self.quick_start.navigationButton.setText("Open/Close")
            self.quick_start.navigationButton.setStyleSheet("")
            self.log_message("[NAVIGATION] Navigation system stopped")
            
    def _finalize_navigation_start(self):
        if Flag.navigation_running:
            self.quick_start.navigationButton.setEnabled(True)
            self.quick_start.navigationButton.setText("Close")
            self.quick_start.navigationButton.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; } QPushButton:hover { background-color: #c0392b; }")
            self.log_message("[NAVIGATION] Navigation system started successfully")
    
    def on_move_to_shelf(self):
        """Move robot to shelf (Single Delivery Mode)"""
        try:
            if Flag.quick_start_process:
                self.log_message("[WARNING] Smart Logistics workflow is already running. Please stop it first.")
                return
            
            if not Flag.radar_running or not Flag.navigation_running:
                self.prompt.warning(
                    _translate("MainWindow", "Warning"),
                    _translate("MainWindow", "Please open Lidar and Navigation first!")
                )
                return
                
            self.log_message("[TASK] Starting Move To Shelf (Single Pick) process...")
            Flag.quick_start_process = True
            self.quick_start.quickStartTaskButton.setText("Stop Task")
            self.quick_start.moveToShelfButton.setEnabled(False)
            self.quick_start.circularSortingButton.setEnabled(False)
            
            # Start logistics process in a background thread to safely release UI resources
            threading.Thread(target=self.start_smart_logistics_workflow, args=("single",), daemon=True).start()
            
        except Exception as e:
            self.console.exception(e)
    
    def on_circular_sorting(self):
        """Start circular sorting task (Continuous Mode)"""
        try:
            if Flag.quick_start_process:
                self.log_message("[WARNING] Smart Logistics workflow is already running. Please stop it first.")
                return
            
            if not Flag.radar_running or not Flag.navigation_running:
                self.prompt.warning(
                    _translate("MainWindow", "Warning"),
                    _translate("MainWindow", "Please open Lidar and Navigation first!")
                )
                return
                
            self.log_message("[TASK] Starting Circular Sorting (Continuous Loop) process...")
            Flag.quick_start_process = True
            self.quick_start.quickStartTaskButton.setText("Stop Task")
            self.quick_start.moveToShelfButton.setEnabled(False)
            self.quick_start.circularSortingButton.setEnabled(False)
            
            # Start logistics process in a background thread to safely release UI resources
            threading.Thread(target=self.start_smart_logistics_workflow, args=("circular",), daemon=True).start()
            
        except Exception as e:
            self.console.exception(e)

    def on_aruco_detect(self):
        """Start ARUCO code detection"""
        button = self.quick_start.arucoButton
        
        if not Flag.detector_running:
            if self.agv_camera_capture is None:
                self.log_message("[ERROR] AGV camera not available")
                return
            
            self.log_message("[VISION] ARUCO code detection algorithm started")
            self.agv_camera_capture.activate_middleware("ARUCO")
            button.setText("Stop ARUCO")
            button.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; } QPushButton:hover { background-color: #c0392b; }")
            self.quick_start.qrButton.setEnabled(False)
            Flag.detector_running = True
        else:
            self.log_message("[VISION] ARUCO code detection stopped")
            self.agv_camera_capture.deactivate_middleware()
            button.setText("ARUCO Code Detect")
            button.setStyleSheet("")
            self.quick_start.qrButton.setEnabled(True)
            Flag.detector_running = False
    
    def on_qr_detect(self):
        """Start QR code detection"""
        button = self.quick_start.qrButton
        
        if not Flag.detector_running:
            if self.arm_camera_capture is None:
                self.log_message("[ERROR] Arm camera not available")
                return
            
            self.log_message("[VISION] QR code detection algorithm started")
            self.arm_camera_capture.activate_middleware("QR")
            button.setText("Stop QR")
            button.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; } QPushButton:hover { background-color: #c0392b; }")
            self.quick_start.arucoButton.setEnabled(False)
            Flag.detector_running = True
        else:
            self.log_message("[VISION] QR code detection stopped")
            self.arm_camera_capture.deactivate_middleware()
            button.setText("QR Code Detect")
            button.setStyleSheet("")
            self.quick_start.arucoButton.setEnabled(True)
            Flag.detector_running = False
    
    def on_joystick_control(self):
        """Open joystick control"""
        if Flag.joystick_running is False:
            if self.check_radar_running(prompt=True) is False:
                return
            
            try:
                if ROS_AVAILABLE and not Flag.ros_node_initialized:
                    init_ros_node()
                self.log_message("[CONTROL] Opening joystick control interface...")
                self.quick_start.joystickButton.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; } QPushButton:hover { background-color: #c0392b; }")
                self.quick_start.joystickButton.setText(_translate("MainWindow", "Close Joystick Control"))
                self.joystick_controller = JoystickController(parent=self)
                self.joystick_controller.noticed.connect(self.on_joystick_control_notice_handle)
                self.joystick_controller.start()
                Flag.joystick_running = True
            except Exception as e:
                self.console.error(f"[CONTROL] Failed to start joystick controller: {e}")
                self.log_message(f"[ERROR] Joystick control failed: {e}")
                self.quick_start.joystickButton.setStyleSheet("")
                self.quick_start.joystickButton.setText(_translate("MainWindow", "Open Joystick Control"))
                Flag.joystick_running = False
        else:
            try:
                self.log_message("[CONTROL] Closing joystick control...")
                self.quick_start.joystickButton.setStyleSheet("")
                self.quick_start.joystickButton.setText(_translate("MainWindow", "Open Joystick Control"))
                if self.joystick_controller is not None:
                    self.joystick_controller.stop_running()
            except Exception as e:
                self.console.error(f"[CONTROL] Error closing joystick: {e}")
    
    def on_joystick_control_notice_handle(self, message):
        if message == "Finishing":
            Flag.joystick_running = False
            self.joystick_controller = None
            self.quick_start.joystickButton.setStyleSheet("")
        else:
            self.log_message(message)
    
    def on_keyboard_control(self):
        """Open keyboard control"""
        if not Flag.keyboard_running:
            if self.check_radar_running(prompt=True) is False:
                return
            
            Functional.open_keyboard_control()
            self.log_message("[CONTROL] Keyboard control activated - Use arrow keys to control robot")
            self.quick_start.keyboardButton.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; } QPushButton:hover { background-color: #c0392b; }")
            self.quick_start.keyboardButton.setText(_translate("MainWindow", "Close Keyboard Control"))
            Flag.keyboard_running = True
        else:
            Functional.close_keyboard_control()
            self.log_message("[CONTROL] Keyboard control deactivated")
            self.quick_start.keyboardButton.setStyleSheet("")
            self.quick_start.keyboardButton.setText(_translate("MainWindow", "Open Keyboard Control"))
            Flag.keyboard_running = False
    
    def on_clear_log(self):
        """Clear log output"""
        self.quick_start.logBrowser.clear()
        self.log_message("[SYSTEM] Log cleared")
    
    def on_language_changed(self, language):
        """Handle language selection change"""
        if language == "English":
            self.log_message("[SYSTEM] Language changed to English")
        else:
            self.log_message("[SYSTEM] Language changed to Chinese")
        self.file_resource.dump_json({"language": language}, 'localConfig.json')
        self.setup_language_initial(language)
    
    def setup_language_initial(self, language: str = None):
        """Setup initial language"""
        if language is None:
            language = self.file_resource.load_json('localConfig.json').get('language')
        
        if language in ("English", "英文"):
            self.application.removeTranslator(self.translator)
        elif language in ("Chinese", "中文"):
            language_filepath = self.file_resource.get('translation', 'zh_CN.qm')
            self.translator.load(language_filepath)
            self.application.installTranslator(self.translator)
        
        if hasattr(self.quick_start, 'languageComboBox'):
            self.quick_start.languageComboBox.setCurrentText(language)

    # Process handlers
    def check_camera_devices(self):
        """Check camera device availability and log status"""
        import cv2
        import os
        from constant import GlobalVar
        
        self.log_message("[CAMERA] ========== Camera Device Status Check ==========")
        
        # Check AGV 2D Camera (CSI Camera - /dev/video0)
        self.log_message("[CAMERA] AGV 2D Camera:")
        self.log_message(f"[CAMERA]   Device: sensor_id=0 (CSI Camera via GStreamer)")
        self.log_message(f"[CAMERA]   Physical Device: /dev/video0")
        self.log_message(f"[CAMERA]   Pipeline: {GlobalVar.camera2D_pipline}")
        
        # Test AGV camera availability
        agv_available = False
        try:
            if os.path.exists("/dev/video0"):
                # Try to open with GStreamer pipeline
                cap = cv2.VideoCapture(GlobalVar.camera2D_pipline, cv2.CAP_GSTREAMER)
                if cap.isOpened():
                    agv_available = True
                    self.log_message("[CAMERA]   Status: ✓ Available (not occupied)")
                    cap.release()
                else:
                    self.log_message("[CAMERA]   Status: ✗ Cannot open (may be occupied)")
            else:
                self.log_message("[CAMERA]   Status: ✗ Device /dev/video0 not found")
        except Exception as e:
            self.log_message(f"[CAMERA]   Status: ✗ Error testing: {e}")
        
        # Check Arm Camera (/dev/video1)
        self.log_message("[CAMERA] Arm Camera:")
        self.log_message("[CAMERA]   Device: /dev/video1 (Primary), fallback to /dev/video0")
        
        arm_available = False
        arm_device = None
        
        # Test /dev/video1 first
        for device in ["/dev/video1", "/dev/video0", 1, 0]:
            try:
                if isinstance(device, str) and not os.path.exists(device):
                    continue
                    
                cap = cv2.VideoCapture(device)
                if cap.isOpened():
                    arm_available = True
                    arm_device = device
                    self.log_message(f"[CAMERA]   Status: ✓ Available on {device}")
                    cap.release()
                    break
                else:
                    self.log_message(f"[CAMERA]   Testing {device}: Cannot open")
            except Exception as e:
                self.log_message(f"[CAMERA]   Testing {device}: Error - {e}")
        
        if not arm_available:
            self.log_message("[CAMERA]   Status: ✗ No available arm camera found")
        
        # Summary
        self.log_message("[CAMERA] ================================================")
        if agv_available and arm_available:
            self.log_message("[CAMERA] ✓ All cameras available for Smart Logistics")
        elif agv_available:
            self.log_message("[CAMERA] ⚠ AGV camera available, but arm camera unavailable")
        elif arm_available:
            self.log_message("[CAMERA] ⚠ Arm camera available, but AGV camera unavailable")
        else:
            self.log_message("[CAMERA] ✗ No cameras available - Smart Logistics may fail")
        
        return agv_available, arm_available

    def start_smart_logistics_workflow(self, mode="single"):
        """Start the Smart Logistics workflow in background thread"""
        self.update_task_node(3, "waiting")
        
        # Check camera device status before starting
        self.log_message("[SYSTEM] Checking camera device availability...")
        agv_available, arm_available = self.check_camera_devices()
        
        # Stop UI cameras to free resources for Smart Logistics
        self.log_message("[SYSTEM] Stopping UI cameras for Smart Logistics...")
        
        # Force stop and cleanup AGV camera
        if self.agv_camera_capture is not None:
            try:
                self.log_message("[CAMERA] Stopping AGV camera...")
                self.agv_camera_capture.deactivate_middleware()
                self.agv_camera_capture.stopped()
                if not self.agv_camera_capture.wait(2000):
                    self.log_message("[CAMERA] AGV camera thread stuck, forcefully terminating...")
                    self.agv_camera_capture.terminate()
                    self.agv_camera_capture.wait(1000)
                self.agv_camera_capture.deleteLater()
                self.agv_camera_capture = None
                self.log_message("[CAMERA] ✓ AGV camera stopped and cleaned up")
            except Exception as e:
                self.log_message(f"[CAMERA] Error stopping AGV camera: {e}")
                
        # Force stop and cleanup Arm camera
        if self.arm_camera_capture is not None:
            try:
                self.log_message("[CAMERA] Stopping Arm camera...")
                self.arm_camera_capture.deactivate_middleware()
                self.arm_camera_capture.stopped()
                if not self.arm_camera_capture.wait(2000):
                    self.log_message("[CAMERA] Arm camera thread stuck, forcefully terminating...")
                    self.arm_camera_capture.terminate()
                    self.arm_camera_capture.wait(1000)
                self.arm_camera_capture.deleteLater()
                self.arm_camera_capture = None
                self.log_message("[CAMERA] ✓ Arm camera stopped and cleaned up")
                
                # Additional cleanup - force release GStreamer resources
                import gc
                gc.collect()  # Force garbage collection
                time.sleep(1)  # Give time for cleanup
                
            except Exception as e:
                self.log_message(f"[CAMERA] Warning: Error stopping arm camera: {e}")
                self.arm_camera_capture = None
        
        # Additional cleanup - force release GStreamer/V4L2 resources
        import gc
        gc.collect()
        time.sleep(1)
        
        # Extra wait to ensure all camera resources are released
        self.log_message("[CAMERA] Waiting for camera resources to be fully released...")
        time.sleep(2)
        
        # CRITICAL: Shutdown UI's ROS node/publisher to avoid conflicts with Smart Logistics
        self.log_message("[ROS] Relinquishing UI's ROS control to avoid conflicts...")
        try:
            if ROS_AVAILABLE and rospy is not None and Flag.ros_node_initialized:
                # IMPORTANT: Pause the background publisher thread from the joystick!
                # Setting it to None is not enough, as the thread will keep running 
                # and fighting move_base for /cmd_vel control.
                if hasattr(self, 'cmd_vel_publisher') and self.cmd_vel_publisher is not None:
                    try:
                        if hasattr(self.cmd_vel_publisher, 'pause'):
                            self.cmd_vel_publisher.pause()
                        else:
                            self.cmd_vel_publisher = None
                        self.log_message("[ROS] ✓ Paused cmd_vel publisher")
                    except Exception as e:
                        self.log_message(f"[ROS] Warning: {e}")
                
                self.log_message("[ROS] ✓ UI ROS operations paused")
        except Exception as e:
            self.log_message(f"[ROS] Warning: Could not pause ROS operations: {e}")
        
        # Release mechanical arm connection to avoid serial port conflict
        self.log_message("[SYSTEM] Releasing mechanical arm connection for Smart Logistics...")
        if hasattr(self, 'mech_arm') and self.mech_arm is not None:
            try:
                self.log_message(f"[ARM] Found active mechanical arm connection: {self.mech_arm}")
                self.mech_arm.close()
                self.log_message("[ARM] ✓ Mechanical arm connection released")
            except Exception as e:
                self.log_message(f"[ARM] Warning: Error releasing arm connection: {e}")
            finally:
                self.mech_arm = None
        else:
            self.log_message("[ARM] No active mechanical arm connection found")
        
        
        # Wait for camera resources to be fully released
        self.log_message("[CAMERA] Waiting for camera resources to be fully released...")
        time.sleep(3)
        
        # ===== CORE FIX: Run main.py in an independent terminal =====
        # The previous QThread + subprocess.PIPE approach shared resources with the UI.
        # Capturing stdout caused I/O polling that competed with the camera and ROS,
        # making the AGV movements stutter.
        # Now we launch it purely via gnome-terminal, just like Lidar and Navigation.
        self.log_message("[SYSTEM] Starting Smart Logistics in independent terminal...")
        self.log_message("[INFO] main.py will run in its own terminal for best performance")
        
        import os
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dir = os.path.join(script_dir, "Smart_Logistics_Kit-22-map")
        
        # Build the command to run in independent terminal
        run_command = (
            f"source /opt/ros/noetic/setup.bash && "
            f"source /home/er/myagv_ros/devel/setup.bash && "
            f"cd {target_dir} && "
            f"python3 main.py --mode {'circular' if 'circular' in mode else 'single'}"
        )
        
        Command.run_in_terminal(command=run_command, keep=True)
        
        self.log_message("[TASK] ✓ Smart Logistics program launched in independent terminal")
        self.log_message("[INFO] Task progress will update automatically")
        
        # Tell the main thread to start the progress polling timer
        self.start_progress_timer_sig.emit()
    
    def _on_start_progress_timer(self):
        """Main thread handler to start the progress timer safely"""
        # Clean up any old progress file
        progress_file = "/tmp/smart_logistics_progress.txt"
        try:
            import os
            if os.path.exists(progress_file):
                os.remove(progress_file)
        except Exception:
            pass
            
        self._last_progress = ""
        if self._progress_timer:
            self._progress_timer.start(3000)  # Poll every 3 seconds
            
    def _on_stop_progress_timer(self):
        """Main thread handler to stop the progress timer safely"""
        if self._progress_timer:
            self._progress_timer.stop()
    
    def play_node_audio(self, node_num):
        """Asynchronously play the node completion audio via system ALSA string (card 3, device 0)"""
        import os
        import subprocess
        sound_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sound")
        file_path = os.path.join(sound_dir, f"{node_num}.mp3")
        
        if not os.path.exists(file_path):
            self.log_message(f"[AUDIO] Warning: Cannot play audio, file not found: {file_path}")
            return
            
        try:
            # We use ffmpeg -> aplay with plughw:UACDemoV10,0 to guarantee format/sample-rate compatibility 
            # and automatically find the USB sound card by its ALSA device name, preventing ID shift issues.
            play_cmd = f"ffmpeg -i '{file_path}' -f wav - 2>/dev/null | aplay -D plughw:UACDemoV10,0 -q -"
            subprocess.Popen(play_cmd, shell=True, stderr=subprocess.DEVNULL)
            self.log_message(f"[AUDIO] Playing node {node_num} sound (USB Speaker)")
        except Exception as e:
            self.log_message(f"[AUDIO] Failed to play sound for node {node_num}: {e}")

    def _poll_task_progress(self):
        """Poll /tmp/smart_logistics_progress.txt to update UI task nodes"""
        import os
        progress_file = "/tmp/smart_logistics_progress.txt"
        try:
            if not os.path.exists(progress_file):
                return
            with open(progress_file, 'r') as f:
                stage = f.read().strip()
            
            if stage == self._last_progress:
                return  # No change
            self._last_progress = stage
            
            # Map progress stages to UI task nodes:
            # Node 1: Proceed to loading area
            # Node 2: Pick goods
            # Node 3: Proceed to unloading area
            # Node 4: Unload goods
            # Node 5: Success
            if stage == "LOADING":
                self.update_task_node(1, "completed")
                self.log_message("[TASK] ✓ Node 1: AGV navigating to loading area")
                self.play_node_audio(1)
            elif stage == "PICKING":
                self.update_task_node(1, "completed")
                self.update_task_node(2, "completed")
                self.log_message("[TASK] ✓ Node 2: Picking goods from shelf")
                self.play_node_audio(2)
            elif stage == "UNLOADING":
                self.update_task_node(1, "completed")
                self.update_task_node(2, "completed")
                self.update_task_node(3, "completed")
                self.log_message("[TASK] ✓ Node 3: AGV navigating to unloading area")
                self.play_node_audio(3)
            elif stage == "PLACING":
                self.update_task_node(1, "completed")
                self.update_task_node(2, "completed")
                self.update_task_node(3, "completed")
                self.update_task_node(4, "completed")
                self.log_message("[TASK] ✓ Node 4: Placing goods at destination")
                self.play_node_audio(4)
            elif stage == "SUCCESS":
                for i in range(1, 6):
                    self.update_task_node(i, "completed")
                self.log_message("[TASK] ✓ Node 5: ========== All Tasks Completed! ==========")
                self.play_node_audio(5)
                # Auto stop progress polling safely via signal
                self.stop_progress_timer_sig.emit()
        except Exception:
            pass  # File might be being written to, ignore errors

    def on_smart_logistics_published(self, process, message):
        """Handle Smart Logistics workflow progress messages"""
        msg = str(message)
        self.log_message(msg)
        # Note: Task nodes are now updated via _poll_task_progress (file-based)
        # to ensure accuracy with main.py's internal state.

    
    def on_smart_logistics_finished(self, process, result):
        """Handle Smart Logistics workflow completion"""
        self._smart_logistics_running = False
        self.smart_logistics_process = None
        self.log_message("[WORKFLOW] Smart Logistics workflow finished")
        
        # Restore UI window
        self.log_message("[UI] Restoring UI window...")
        self.showNormal()  # Restore window from minimized state
        
        # Restore UI process priority
        self.log_message("[SYSTEM] Restoring UI priority...")
        try:
            import os
            import psutil
            p = psutil.Process(os.getpid())
            p.nice(0)  # Restore normal priority
            self.log_message("[UI] ✓ UI process priority restored")
        except Exception as e:
            self.log_message(f"[UI] Warning: Could not restore UI priority: {e}")
        
        # Reconnect mechanical arm for UI virtual controller
        self.log_message("[SYSTEM] Reconnecting mechanical arm for UI...")
        try:
            if MYCOBOT_AVAILABLE and MechArm270 is not None:
                self.mech_arm = MechArm270("/dev/ttyACM0")
                self.log_message("[ARM] ✓ Mechanical arm reconnected for UI")
            else:
                self.log_message("[ARM] MechArm270 not available")
        except Exception as e:
            self.log_message(f"[ARM] Warning: Could not reconnect mechanical arm: {e}")
            self.mech_arm = None
        
        # Restart UI cameras after Smart Logistics finishes (with delay to avoid resource conflict)
        self.log_message("[SYSTEM] Cameras will remain disabled")
        self.log_message("[SYSTEM] Use ARUCO/QR buttons to manually start cameras if needed")
    
    def restart_ui_cameras(self):
        """Restart UI cameras with delay to avoid resource conflicts"""
        try:
            # Restart AGV camera
            if self.agv_camera_capture is None or not self.agv_camera_capture.isRunning():
                self.agv_camera_capture = self.start_camera_capture(GlobalVar.camera2D_pipline, cv2.CAP_GSTREAMER)
                if self.agv_camera_capture is not None:
                    self.log_message("[SYSTEM] ✓ AGV camera restarted")
        except Exception as e:
            self.console.error(f"Error restarting AGV camera: {e}")
        
        try:
            # Restart Arm camera
            for video_device in ["/dev/video1", "/dev/video0", 1, 0]:
                try:
                    self.arm_camera_capture = self.start_camera_capture(pipeline=video_device)
                    if self.arm_camera_capture is not None:
                        self.log_message(f"[SYSTEM] ✓ Arm camera restarted on {video_device}")
                        break
                except Exception as e:
                    continue
        except Exception as e:
            self.console.error(f"Error restarting arm camera: {e}")
        
        self.log_message("[SYSTEM] ✓ UI cameras restart completed")
    
    def start_sorting_process_handle(self):
        """Start circular sorting process"""
        Flag.circular_sorting_process = True
        self.log_message("[TASK] ========== Circular Sorting Process Started ==========")
        self.quick_start.circularSortingButton.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; } QPushButton:hover { background-color: #c0392b; }")
        self.quick_start.moveToShelfButton.setEnabled(False)
        
        self.sorting_process = CircularSortingProcess(parent=self)
        self.sorting_process.published.connect(self.on_process_published_handle)
        self.sorting_process.finished.connect(self.on_process_finished_handle)
        self.sorting_process.start()
    
    def start_navigation_process_handle(self):
        """Start navigation to shelf process"""
        Flag.navigation_shelf_process = True
        self.log_message("[TASK] ========== Navigation to Shelf Process Started ==========")
        self.quick_start.moveToShelfButton.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; } QPushButton:hover { background-color: #c0392b; }")
        self.quick_start.circularSortingButton.setEnabled(False)
        
        self.navigation_process = NavigationToShelfProcess(parent=self)
        self.navigation_process.finished.connect(self.on_process_finished_handle)
        self.navigation_process.published.connect(self.on_process_published_handle)
        self.navigation_process.start()
    
    def start_charging_process_handle(self):
        """Start parking charging process"""
        Flag.parking_charging_process = True
        self.log_message("[TASK] ========== Parking Charging Process Started ==========")
        self.quick_start.moveToShelfButton.setEnabled(False)
        self.quick_start.circularSortingButton.setEnabled(False)
        
        self.charging_process = ParkingChargingProcess(parent=self)
        self.charging_process.finished.connect(self.on_process_finished_handle)
        self.charging_process.published.connect(self.on_process_published_handle)
        self.charging_process.start()
    
    def on_process_finished_handle(self, process: BascProcess):
        """Handle process completion"""
        if isinstance(process, ParkingChargingProcess):
            self.quick_start.moveToShelfButton.setEnabled(True)
            self.quick_start.circularSortingButton.setEnabled(True)
            self.log_message("[TASK] Charging process completed")
            self.update_task_node(5, "completed")
            self.charging_process = None
            Flag.parking_charging_process = False
            
            if Flag.quick_start_process:
                self.log_message("[INFO] ========== Intelligent Logistics Task Completed ==========")
                Flag.quick_start_process = False
                self.quick_start.quickStartTaskButton.setText(_translate("MainWindow", "Quick Start"))
                self.quick_start.quickStartTaskButton.setStyleSheet("")
        
        elif isinstance(process, NavigationToShelfProcess):
            self.quick_start.circularSortingButton.setEnabled(True)
            self.quick_start.moveToShelfButton.setStyleSheet("")
            self.log_message("[TASK] Navigation to shelf process completed")
            self.update_task_node(1, "completed")
            self.update_task_node(2, "completed")
            self.navigation_process = None
            Flag.navigation_shelf_process = False
            
            if Flag.quick_start_process:
                self.update_task_node(3, "completed")
                self.update_task_node(4, "completed")
                self.start_charging_process_handle()
        
        elif isinstance(process, CircularSortingProcess):
            self.quick_start.moveToShelfButton.setEnabled(True)
            self.quick_start.circularSortingButton.setStyleSheet("")
            self.log_message("[TASK] Circular sorting process completed")
            self.sorting_process = None
            Flag.circular_sorting_process = False
    
    def on_process_published_handle(self, process: BascProcess, message: object):
        """Handle process messages"""
        self.log_message(str(message))
    
    # Camera handlers
    def start_camera_capture(self, pipeline: str, *args) -> QCameraStreamCapture:
        """Start camera capture with retry mechanism"""
        max_retries = 3
        retry_delay = 1.0  # seconds
        
        for attempt in range(max_retries):
            try:
                self.console.info(f"Attempting to start camera: {pipeline} (attempt {attempt + 1}/{max_retries})")
                
                # Add small delay before retry
                if attempt > 0:
                    time.sleep(retry_delay)
                
                # For USB cameras (integer pipeline), set lower resolution
                if isinstance(pipeline, int):
                    import cv2
                    cap_test = cv2.VideoCapture(pipeline)
                    if cap_test.isOpened():
                        # Set to a reasonable resolution (not too high)
                        cap_test.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                        cap_test.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                        cap_test.release()
                        self.console.info(f"Set camera {pipeline} to 1280x720")
                
                camera_stream_capture = QCameraStreamCapture(
                    pipeline=pipeline,
                    parent=self,
                    size=QSize(320, 240),
                    params=args
                )
                camera_stream_capture.streamed.connect(self.on_camera_stream_handle)
                for name, recognition_middleware in self.image_recognition_middlewares.items():
                    camera_stream_capture.register_middleware(name, recognition_middleware)
                camera_stream_capture.start()
                
                # Wait a bit to see if camera actually starts
                time.sleep(0.5)
                
                self.console.info(f"Camera started successfully: {pipeline}")
                return camera_stream_capture
                
            except Exception as e:
                self.console.error(f"Camera start attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    self.console.info(f"Retrying in {retry_delay} seconds...")
                else:
                    self.console.error(f"Failed to start camera after {max_retries} attempts: {pipeline}")
        
        return None

    # [Cross-thread crash fix] Core fix: Safely create and use QPixmap here
    def on_camera_stream_handle(self, camera_stream: QCameraStream):
        """Handle camera stream updates - same logic as original main.py"""
        try:
            # 1. [Compatibility] Safely get the image property whether it's named image or pixmap
            img_data = getattr(camera_stream, 'image', None)
            if img_data is None:
                img_data = getattr(camera_stream, 'pixmap', None)
                
            if img_data is None:
                return
            
            if camera_stream.result is not None:
                stylesheet = "border:1px solid cyan;background-color: rgb(218, 218, 218);"
                self.log_message(f"[VISION] Detected: {camera_stream.result}")
            else:
                stylesheet = "background-color: rgb(218, 218, 218);"
            
            # 2. [Safe Conversion] Use it if it's already a QPixmap, otherwise convert from QImage
            if isinstance(img_data, QImage):
                display_pixmap = QPixmap.fromImage(img_data)
            else:
                display_pixmap = img_data
            
            # 3. Render to UI
            if isinstance(camera_stream.pipeline, str) and camera_stream.pipeline.startswith("/dev/video"):
                # Arm camera (video1)
                if hasattr(self.quick_start, 'camera270Label'):
                    self.quick_start.camera270Label.setStyleSheet(stylesheet)
                    self.quick_start.camera270Label.setPixmap(display_pixmap)
                    self.quick_start.camera270Label.update()
            else:
                # AGV camera (GStreamer)
                if hasattr(self.quick_start, 'agvCameraLabel'):
                    self.quick_start.agvCameraLabel.setStyleSheet(stylesheet)
                    self.quick_start.agvCameraLabel.setPixmap(display_pixmap)
                    self.quick_start.agvCameraLabel.update()
        except Exception as e:
            self.console.error(f"Camera stream error: {e}")

    # Utility methods
    def log_message(self, message):
        """Add message to log browser using a thread-safe signal"""
        self.thread_safe_log_sig.emit(str(message))
        
    def _sync_log_message(self, message):
        """Internal slot that strictly executes in the main GUI thread"""
        if not hasattr(self, 'quick_start') or not hasattr(self.quick_start, 'logBrowser'):
            return
            
        self.quick_start.logBrowser.append(message)
        self._trim_log_browser()
    
    def _trim_log_browser(self):
        """Keep logBrowser under 300 lines to prevent layout bloat and speed up UI"""
        doc = self.quick_start.logBrowser.document()
        max_lines = 300
        if doc.blockCount() > max_lines:
            cursor = self.quick_start.logBrowser.textCursor()
            cursor.movePosition(cursor.Start)
            # Remove oldest 50 lines at a time
            for _ in range(50):
                cursor.movePosition(cursor.Down, cursor.KeepAnchor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # Remove leftover newline
    
    def on_console_output(self, message):
        """Handle console output from console handler signal"""
        self.log_message(message)
    
    def update_task_node(self, node_number, status="waiting"):
        """
        Update task progress node color and icon
        status: "waiting" (blue), "completed" (green), "error" (red)
        """
        node_name = f"node{node_number}"
        connector_name = f"connector{node_number}"
        
        if hasattr(self.quick_start, node_name):
            node = getattr(self.quick_start, node_name)
            
            if status == "completed":
                node.setText("✓")
                node.setStyleSheet("""
                    QLabel {
                        background-color: #7ED321;
                        border-radius: 25px;
                        color: white;
                        font-weight: bold;
                        font-size: 18px;
                    }
                """)
                if hasattr(self.quick_start, connector_name):
                    connector = getattr(self.quick_start, connector_name)
                    connector.setStyleSheet("QLabel { background-color: #7ED321; }")
            
            elif status == "error":
                node.setText("✗")
                node.setStyleSheet("""
                    QLabel {
                        background-color: #E74C3C;
                        border-radius: 25px;
                        color: white;
                        font-weight: bold;
                        font-size: 18px;
                    }
                """)
                if hasattr(self.quick_start, connector_name):
                    connector = getattr(self.quick_start, connector_name)
                    connector.setStyleSheet("QLabel { background-color: #E74C3C; }")
            
            else:  # waiting
                node.setText("...")
                node.setStyleSheet("""
                    QLabel {
                        background-color: #4A90E2;
                        border-radius: 25px;
                        color: white;
                        font-weight: bold;
                        font-size: 18px;
                    }
                """)
                if hasattr(self.quick_start, connector_name):
                    connector = getattr(self.quick_start, connector_name)
                    connector.setStyleSheet("QLabel { background-color: #cccccc; }")
    
    # Virtual Controller handlers
    def on_arm_joystick_moved(self, x, y):
        """Handle arm joystick movement - controls MechArm270"""
        self.arm_position = [x, y]
        # Update status label
        self.virtual_controller.armStatusLabel.setText(f"Arm Control: X={x:.2f}, Y={y:.2f}")
        
        # Determine dominant axis and intended direction to avoid conflicting commands
        new_state = None
        speed = 20  # Safe fixed speed for jogging
        
        if abs(x) > 0.1 or abs(y) > 0.1:
            if abs(x) > abs(y):
                # X axis dominant (Left/Right -> Joint 1)
                new_state = ('joint1', 0 if x > 0 else 1)
            else:
                # Y axis dominant (Up/Down -> Joint 2)
                new_state = ('joint2', 0 if y < 0 else 1)
                
        current_state = getattr(self, '_current_jog_state', None)
        
        if self.mech_arm is not None:
            if new_state is not None:
                # Only send the serial command if the state (joint or direction) has changed.
                # This prevents serial buffer flooding which causes huge stop() delays!
                if new_state != current_state:
                    self._current_jog_state = new_state
                    joint = 1 if new_state[0] == 'joint1' else 2
                    direction = new_state[1]
                    self.mech_arm.jog_angle(joint, direction, speed)
            else:
                # Joy centered, only send stop() ONCE if we were previously moving
                if current_state is not None:
                    self.mech_arm.stop()
                    self._current_jog_state = None
        else:
            if new_state is not None and new_state != current_state:
                self._current_jog_state = new_state
                self.console.info(f"[ARM] Moving {new_state[0]}, direction {new_state[1]} (simulated)")
            elif new_state is None and current_state is not None:
                self.console.info("[ARM] Stopped (simulated)")
                self._current_jog_state = None
    
    def on_agv_joystick_moved(self, x, y):
        """Handle AGV joystick movement - controls robot base"""
        self.agv_position = [x, y]
        # Update status label
        self.virtual_controller.agvStatusLabel.setText(f"AGV Control: X={x:.2f}, Y={y:.2f}")
        
        if self.cmd_vel_publisher is None and ROS_AVAILABLE:
            if not Flag.ros_node_initialized:
                init_ros_node()
            if Flag.ros_node_initialized:
                try:
                    # CmdVelPublisher might not be imported at the top due to loops or missing modules in mock mode
                    self.cmd_vel_publisher = CmdVelPublisher()
                except Exception as e:
                    self.console.warning(f"[AGV] CmdVelPublisher initialization failed: {e}")
        
        # Control the AGV based on joystick position
        # X axis controls rotation
        # Y axis controls forward/backward movement
        if self.cmd_vel_publisher is not None:
            if abs(x) > 0.1 or abs(y) > 0.1:
                # Y axis: forward/backward (inverted)
                linear_x = -y * 0.3
                # X axis: rotation (inverted)
                angular_z = -x * 0.5
                self.cmd_vel_publisher.set_speed(x=linear_x, yaw=angular_z)
            else:
                # Stop when joystick is centered
                self.cmd_vel_publisher.set_speed(x=0.0, yaw=0.0)
        else:
            if abs(x) > 0.1 or abs(y) > 0.1:
                self.console.info(f"[AGV] Moving: X={x:.2f}, Y={y:.2f} (simulated)")
    
    def on_gripper_open(self):
        """Open gripper"""
        self.console.info("[GRIPPER] Opening gripper...")
        if self.mech_arm is not None:
            self.mech_arm.set_gripper_value(100, 70)
        else:
            self.console.info("[GRIPPER] Gripper open (simulated)")
    
    def on_gripper_close(self):
        """Close gripper"""
        self.console.info("[GRIPPER] Closing gripper...")
        if self.mech_arm is not None:
            self.mech_arm.set_gripper_value(0, 70)
        else:
            self.console.info("[GRIPPER] Gripper close (simulated)")
    
    def on_pump_on(self):
        """Turn on pump"""
        self.console.info("[PUMP] Turning on pump...")
        try:
            Functional.turn_on_pump()
        except Exception as e:
            self.console.error(f"[PUMP] Failed to turn on pump: {e}")
    
    def on_pump_off(self):
        """Turn off pump"""
        self.console.info("[PUMP] Turning off pump...")
        try:
            Functional.turn_off_pump()
        except Exception as e:
            self.console.error(f"[PUMP] Failed to turn off pump: {e}")
    
    def on_lock_arm(self):
        """Lock arm servos - power on"""
        self.console.info("[ARM] Locking arm servos (power on)...")
        if self.mech_arm is not None:
            self.mech_arm.power_on()
        else:
            self.console.info("[ARM] Arm lock (simulated)")
    
    def on_release_arm(self):
        """Release arm servos - release all"""
        self.console.info("[ARM] Releasing arm servos...")
        if self.mech_arm is not None:
            self.mech_arm.release_all_servos()
        else:
            self.console.info("[ARM] Arm release (simulated)")
    
    def on_reset_position(self):
        """Navigate AGV back to charging station and reset arm"""
        from PyQt5.QtWidgets import QMessageBox
        
        # Check if navigation is available
        if not Flag.radar_running or not Flag.navigation_running:
            QMessageBox.warning(self, "Navigation Not Ready",
                "Lidar and Navigation must be running first.\n"
                "Please start them from the Quick Start page.")
            return
        
        # Prevent multiple clicks causing stuttering
        if Command.alive("return_to_origin.py"):
            QMessageBox.information(self, "Already Running", 
                "The robot is already navigating back to the origin.\n"
                "Please wait for it to arrive.")
            return

        # Show immediate visible feedback to the user
        reply = QMessageBox.question(self, "Return to Origin",
            "The AGV will navigate back to the starting position.\n"
            "Cameras and Virtual Joystick will be disabled to ensure smooth movement.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        
        if reply != QMessageBox.Yes:
            return
        
        self.console.info("[NAV] Returning AGV to charging station...")
        
        # Reset joysticks
        if self.arm_joystick:
            self.arm_joystick.reset()
        if self.agv_joystick:
            self.agv_joystick.reset()
            
        # CRITICAL FIX: Pause the UI's cmd_vel publisher so it stops spamming 0,0,0
        # and doesn't fight against ROS navigation!
        if self.cmd_vel_publisher is not None:
            if hasattr(self.cmd_vel_publisher, 'pause'):
                self.cmd_vel_publisher.pause()
            self.log_message("[NAV] ✓ Virtual joystick paused (relinquished /cmd_vel control)")
        
        # Reset arm to initial position
        if self.mech_arm is not None:
            try:
                self.mech_arm.send_angles(self.init_angles, 100)
                self.console.info("[ARM] Arm reset to initial position")
            except Exception as e:
                self.console.error(f"[ARM] Reset failed: {e}")
        
        # ===== Free resources to prevent stuttering =====
        # Stop UI cameras
        if self.agv_camera_capture is not None:
            try:
                self.agv_camera_capture.stop()
                if not self.agv_camera_capture.wait(2000):
                    self.agv_camera_capture.terminate()
                self.agv_camera_capture.deleteLater()
                self.agv_camera_capture = None
            except Exception:
                self.agv_camera_capture = None
        
        if self.arm_camera_capture is not None:
            try:
                self.arm_camera_capture.stop()
                if not self.arm_camera_capture.wait(2000):
                    self.arm_camera_capture.terminate()
                self.arm_camera_capture.deleteLater()
                self.arm_camera_capture = None
            except Exception:
                self.arm_camera_capture = None
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Lower UI process priority
        try:
            import psutil
            p = psutil.Process(os.getpid())
            p.nice(19)
        except Exception:
            pass
        
        # Disable the button temporarily
        self.virtual_controller.resetButton.setEnabled(False)
        self.virtual_controller.resetButton.setText("Navigating to Origin...")
        
        # Launch return_to_origin.py in independent terminal
        import os
        import subprocess
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dir = os.path.join(script_dir, "Smart_Logistics_Kit-22-map")
        
        ros_cmd = (
            f"source /opt/ros/noetic/setup.bash && "
            f"source /home/er/myagv_ros/devel/setup.bash && "
            f"cd {target_dir} && "
            f"python3 return_to_origin.py"
        )
        
        # Try Command.run_in_terminal first (gnome-terminal with xterm fallback)
        try:
            Command.run_in_terminal(command=ros_cmd, keep=True)
            self.log_message("[NAV] ✓ Return-to-Origin launched in terminal")
        except Exception as e:
            # Ultimate fallback: run directly as detached subprocess with log file
            self.log_message(f"[NAV] Terminal launch failed ({e}), using direct subprocess...")
            try:
                log_file = "/tmp/return_to_origin.log"
                with open(log_file, "w") as lf:
                    subprocess.Popen(
                        ["bash", "-c", ros_cmd],
                        stdout=lf,
                        stderr=lf,
                        start_new_session=True,
                        stdin=subprocess.DEVNULL
                    )
                self.log_message(f"[NAV] ✓ Return-to-Origin running IN BACKGROUND (log: {log_file})")
                QMessageBox.information(self, "Navigation Started",
                    "The robot is returning to the origin IN THE BACKGROUND.\n"
                    "Since terminal launch failed, you won't see a new window.\n"
                    "Please watch the robot's physical movement.")
            except Exception as e2:
                QMessageBox.critical(self, "Launch Failed",
                    f"Could not start navigation script:\n{e2}")
                self.virtual_controller.resetButton.setEnabled(True)
                self.virtual_controller.resetButton.setText("Reset to Start Position")
                return
        
        self.log_message("[NAV] Robot is navigating back to origin...")
        
        # Restore button after 30 seconds (assume movement finished or failed by then)
        from PyQt5.QtCore import QTimer
        def restore_btn():
            self.virtual_controller.resetButton.setEnabled(True)
            self.virtual_controller.resetButton.setText("Reset to Start Position")
            if hasattr(self, 'cmd_vel_publisher') and self.cmd_vel_publisher is not None:
                if hasattr(self.cmd_vel_publisher, 'resume'):
                    self.cmd_vel_publisher.resume() # Restore joystick functionality
        
        QTimer.singleShot(30000, restore_btn)

    
    def closeEvent(self, event):
        """Handle application close"""
        self.console.info("Closing application...")
        
        # Stop joystick controller first
        if self.joystick_controller is not None:
            try:
                self.console.info("Stopping joystick controller...")
                self.joystick_controller.stop_running()
                self.joystick_controller.wait(2000)  # Wait up to 2 seconds
                if self.joystick_controller.isRunning():
                    self.joystick_controller.terminate()
                self.joystick_controller = None
            except Exception as e:
                self.console.error(f"Error stopping joystick controller: {e}")
        
        # Stop virtual controller components
        if self.mech_arm is not None:
            try:
                self.console.info("Stopping MechArm270...")
                self.mech_arm.stop()
                self.mech_arm.close()
            except Exception as e:
                self.console.error(f"Error closing MechArm270: {e}")
        
        if self.cmd_vel_publisher is not None:
            try:
                self.console.info("Stopping AGV movement...")
                self.cmd_vel_publisher.set_speed(x=0.0, yaw=0.0)
            except Exception as e:
                self.console.error(f"Error stopping AGV: {e}")
        
        # Stop process threads
        if self.smart_logistics_process is not None and self.smart_logistics_process.isRunning():
            try:
                self.console.info("Stopping smart logistics process...")
                self.smart_logistics_process.terminate()
                self.smart_logistics_process.wait(2000)
            except Exception as e:
                self.console.error(f"Error stopping smart logistics process: {e}")
        
        if self.sorting_process is not None and self.sorting_process.isRunning():
            try:
                self.console.info("Stopping sorting process...")
                self.sorting_process.terminate()
                self.sorting_process.wait(2000)
            except Exception as e:
                self.console.error(f"Error stopping sorting process: {e}")
        
        if self.navigation_process is not None and self.navigation_process.isRunning():
            try:
                self.console.info("Stopping navigation process...")
                self.navigation_process.terminate()
                self.navigation_process.wait(2000)
            except Exception as e:
                self.console.error(f"Error stopping navigation process: {e}")
        
        if self.charging_process is not None and self.charging_process.isRunning():
            try:
                self.console.info("Stopping charging process...")
                self.charging_process.terminate()
                self.charging_process.wait(2000)
            except Exception as e:
                self.console.error(f"Error stopping charging process: {e}")
        
        # Stop cameras
        if self.arm_camera_capture is not None:
            try:
                self.console.info("Closing mecharm270 camera...")
                self.arm_camera_capture.deactivate_middleware()
                self.arm_camera_capture.stopped()
                self.arm_camera_capture.wait(2000)
                if self.arm_camera_capture.isRunning():
                    self.arm_camera_capture.terminate()
            except Exception as e:
                self.console.error(f"Error closing arm camera: {e}")
        
        if self.agv_camera_capture is not None:
            try:
                self.console.info("Closing agv camera...")
                self.agv_camera_capture.deactivate_middleware()
                self.agv_camera_capture.stopped()
                self.agv_camera_capture.wait(2000)
                if self.agv_camera_capture.isRunning():
                    self.agv_camera_capture.terminate()
            except Exception as e:
                self.console.error(f"Error closing agv camera: {e}")
        
        # Stop radar and navigation
        if Flag.radar_running is True:
            try:
                self.console.info("Closing radar...")
                Functional.close_radar()
            except Exception as e:
                self.console.error(f"Error closing radar: {e}")
        
        if Flag.navigation_running is True:
            try:
                self.console.info("Closing navigation...")
                Functional.close_navigation()
            except Exception as e:
                self.console.error(f"Error closing navigation: {e}")
        
        # Cleanup GPIO
        try:
            Functional.clear_pump()
            self.console.info("Clearing pump pins...")
            Functional.clear_radar()
            GpioHandler.cleanup()
            self.console.info("Clearing radar pins...")
        except Exception as e:
            self.console.error(f"Error cleaning up GPIO: {e}")
        
        self.console.info("Application closed successfully")
        
        # Small delay to ensure all threads finish
        QCoreApplication.processEvents()
        time.sleep(0.5)
        
        event.accept()


def main(debug: bool = Config.debug, headless: bool = False):
    setup_logger_config(debug=debug)
    
    if headless:
        # Headless mode - run Smart Logistics workflow without UI
        print("[HEADLESS] Starting Smart Logistics in headless mode...")
        
        # Initialize ROS node
        if ROS_AVAILABLE:
            if not init_ros_node():
                print("[ERROR] Failed to initialize ROS node. Is roscore running?")
                sys.exit(1)
        
        # Import and run the Smart Logistics process directly
        from functional.process import SmartLogisticsProcess
        import time
        
        print("[HEADLESS] Starting Smart Logistics workflow...")
        
        # Create a minimal QCoreApplication for Qt functionality
        app = QCoreApplication(sys.argv)
        
        # Create and start the Smart Logistics process
        process = SmartLogisticsProcess()
        
        def on_finished():
            print("[HEADLESS] Smart Logistics workflow completed")
            app.quit()
        
        def on_published(message):
            print(f"[HEADLESS] {message}")
        
        process.finished.connect(on_finished)
        process.published.connect(on_published)
        process.start()
        
        # Run the event loop
        sys.exit(app.exec_())
    else:
        # Normal UI mode
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        application = QApplication(sys.argv)
        
        # Create and show main window
        window = MainApplication()
        window.show()
        
        sys.exit(application.exec_())


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Logistics System')
    parser.add_argument('--headless', action='store_true', 
                       help='Run in headless mode without UI')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    main(debug=args.debug, headless=args.headless)