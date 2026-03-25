#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
UI Demo - Only for viewing the interface
No hardware dependencies required
"""
import sys
from PyQt5.QtWidgets import QApplication, QStackedWidget
from PyQt5.QtCore import Qt
from PyQt5 import uic

# Import virtual joystick widget
from virtual_joystick import VirtualJoystick


class DemoApplication(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Intelligent Logistics System - UI Demo")
        self.resize(1024, 768)
        
        # Load UI pages
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.main_menu = uic.loadUi(os.path.join(current_dir, "main_menu.ui"))
        self.quick_start = uic.loadUi(os.path.join(current_dir, "quick_start.ui"))
        self.virtual_controller = uic.loadUi(os.path.join(current_dir, "virtual_controller.ui"))
        
        # Add pages to stack
        self.addWidget(self.main_menu)
        self.addWidget(self.quick_start)
        self.addWidget(self.virtual_controller)
        
        # Setup virtual controller joysticks
        self.setup_virtual_controller()
        
        # Connect signals
        self.setup_connections()
        
        # Show main menu first
        self.setCurrentWidget(self.main_menu)
    
    def setup_virtual_controller(self):
        """Setup virtual joystick widgets"""
        # Create arm joystick
        self.arm_joystick = VirtualJoystick(labels={
            'up': 'Arm Y+',
            'down': 'Arm Y-',
            'left': 'Arm X-',
            'right': 'Arm X+'
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
    
    def setup_connections(self):
        """Connect all button signals"""
        # Main menu buttons
        self.main_menu.quickStartButton.clicked.connect(self.show_quick_start)
        self.main_menu.controllerButton.clicked.connect(self.show_virtual_controller)
        self.main_menu.parametersButton.clicked.connect(self.show_parameters)
        
        # Back buttons
        self.quick_start.backButton.clicked.connect(self.show_main_menu)
        self.virtual_controller.backButton.clicked.connect(self.show_main_menu)
        
        # Virtual controller buttons
        self.virtual_controller.gripperOpenButton.clicked.connect(lambda: self.log_action("Gripper Open"))
        self.virtual_controller.gripperCloseButton.clicked.connect(lambda: self.log_action("Gripper Close"))
        self.virtual_controller.pumpOnButton.clicked.connect(lambda: self.log_action("Pump On"))
        self.virtual_controller.pumpOffButton.clicked.connect(lambda: self.log_action("Pump Off"))
        self.virtual_controller.lockArmButton.clicked.connect(lambda: self.log_action("Lock Arm"))
        self.virtual_controller.releaseArmButton.clicked.connect(lambda: self.log_action("Release Arm"))
        self.virtual_controller.resetButton.clicked.connect(self.on_reset)
        
        # Quick start buttons (demo only - just log actions)
        self.quick_start.quickStartTaskButton.clicked.connect(lambda: self.log_action("Quick Start Task"))
        self.quick_start.lidarButton.clicked.connect(lambda: self.log_action("Lidar Toggle"))
        self.quick_start.navigationButton.clicked.connect(lambda: self.log_action("Navigation Toggle"))
        self.quick_start.moveToShelfButton.clicked.connect(lambda: self.log_action("Move to Shelf"))
        self.quick_start.circularSortingButton.clicked.connect(lambda: self.log_action("Circular Sorting"))
        self.quick_start.arucoButton.clicked.connect(lambda: self.log_action("ARUCO Detect"))
        self.quick_start.qrButton.clicked.connect(lambda: self.log_action("QR Detect"))
        self.quick_start.joystickButton.clicked.connect(lambda: self.log_action("Joystick Control"))
        self.quick_start.keyboardButton.clicked.connect(lambda: self.log_action("Keyboard Control"))
        self.quick_start.clearLogButton.clicked.connect(self.clear_log)
    
    def show_main_menu(self):
        self.setCurrentWidget(self.main_menu)
        print("[DEMO] Returned to main menu")
    
    def show_quick_start(self):
        self.setCurrentWidget(self.quick_start)
        self.log_action("Entered Quick Start mode")
    
    def show_virtual_controller(self):
        self.setCurrentWidget(self.virtual_controller)
        print("[DEMO] Entered Virtual Controller mode")
    
    def show_parameters(self):
        print("[DEMO] Product Parameters - Coming Soon")
    
    def on_arm_joystick_moved(self, x, y):
        """Handle arm joystick movement"""
        self.virtual_controller.armStatusLabel.setText(f"Arm Control: X={x:.2f}, Y={y:.2f}")
        print(f"[DEMO] Arm: X={x:.2f}, Y={y:.2f}")
    
    def on_agv_joystick_moved(self, x, y):
        """Handle AGV joystick movement"""
        self.virtual_controller.agvStatusLabel.setText(f"AGV Control: X={x:.2f}, Y={y:.2f}")
        print(f"[DEMO] AGV: X={x:.2f}, Y={y:.2f}")
    
    def on_reset(self):
        """Reset joysticks"""
        if hasattr(self, 'arm_joystick'):
            self.arm_joystick.reset()
        if hasattr(self, 'agv_joystick'):
            self.agv_joystick.reset()
        print("[DEMO] Reset to start position")
    
    def log_action(self, action):
        """Log action to console and UI"""
        message = f"[DEMO] {action}"
        print(message)
        if hasattr(self.quick_start, 'logBrowser'):
            self.quick_start.logBrowser.append(message)
    
    def clear_log(self):
        """Clear log"""
        if hasattr(self.quick_start, 'logBrowser'):
            self.quick_start.logBrowser.clear()
        print("[DEMO] Log cleared")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = DemoApplication()
    window.show()
    
    print("=" * 60)
    print("UI Demo Started!")
    print("This is a demo version - no hardware required")
    print("You can navigate through all interfaces")
    print("=" * 60)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
