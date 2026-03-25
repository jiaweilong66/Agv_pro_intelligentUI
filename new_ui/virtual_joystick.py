#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Virtual Joystick Widget
Provides a visual joystick control with mouse interaction
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPoint, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
import math


class VirtualJoystick(QWidget):
    """Virtual joystick widget with visual feedback"""
    
    # Signal emitted when joystick position changes
    # Parameters: (x, y) where x and y are in range [-1.0, 1.0]
    positionChanged = pyqtSignal(float, float)
    
    def __init__(self, parent=None, labels=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        
        # Joystick state
        self.stick_position = QPointF(0, 0)  # Normalized position (-1 to 1)
        self.is_pressed = False
        
        # Labels for directions (optional)
        self.labels = labels or {
            'up': 'Up',
            'down': 'Down',
            'left': 'Left',
            'right': 'Right'
        }
        
        # Visual settings
        self.outer_circle_color = QColor(200, 200, 200)
        self.inner_circle_color = QColor(100, 100, 100)
        self.stick_color = QColor(74, 144, 226)  # Blue
        self.stick_pressed_color = QColor(53, 122, 189)  # Darker blue
        self.cross_color = QColor(150, 150, 150)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
    
    def paintEvent(self, event):
        """Draw the joystick"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        size = min(width, height)
        center_x = width // 2
        center_y = height // 2
        
        # Outer circle radius
        outer_radius = size // 2 - 20
        # Inner circle radius
        inner_radius = outer_radius // 3
        # Stick radius
        stick_radius = outer_radius // 5
        
        # Draw outer circle (background)
        painter.setPen(QPen(self.outer_circle_color, 2))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawEllipse(QPoint(center_x, center_y), outer_radius, outer_radius)
        
        # Draw cross lines
        painter.setPen(QPen(self.cross_color, 2))
        # Horizontal line
        painter.drawLine(center_x - outer_radius, center_y, 
                        center_x + outer_radius, center_y)
        # Vertical line
        painter.drawLine(center_x, center_y - outer_radius,
                        center_x, center_y + outer_radius)
        
        # Draw inner circle
        painter.setPen(QPen(self.inner_circle_color, 2))
        painter.setBrush(QBrush(QColor(220, 220, 220)))
        painter.drawEllipse(QPoint(center_x, center_y), inner_radius, inner_radius)
        
        # Calculate stick position
        stick_x = center_x + int(self.stick_position.x() * (outer_radius - stick_radius))
        stick_y = center_y + int(self.stick_position.y() * (outer_radius - stick_radius))
        
        # Draw stick
        stick_color = self.stick_pressed_color if self.is_pressed else self.stick_color
        painter.setPen(QPen(stick_color, 3))
        painter.setBrush(QBrush(stick_color))
        painter.drawEllipse(QPoint(stick_x, stick_y), stick_radius, stick_radius)
        
        # Draw direction labels
        painter.setPen(QPen(QColor(100, 100, 100)))
        painter.setFont(QFont('Arial', 10, QFont.Bold))
        
        # Up label
        painter.drawText(center_x - 20, center_y - outer_radius - 10, 
                        40, 20, Qt.AlignCenter, self.labels['up'])
        # Down label
        painter.drawText(center_x - 20, center_y + outer_radius + 10,
                        40, 20, Qt.AlignCenter, self.labels['down'])
        # Left label
        painter.drawText(center_x - outer_radius - 50, center_y - 10,
                        40, 20, Qt.AlignCenter, self.labels['left'])
        # Right label
        painter.drawText(center_x + outer_radius + 10, center_y - 10,
                        40, 20, Qt.AlignCenter, self.labels['right'])
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.LeftButton:
            self.is_pressed = True
            self.updateStickPosition(event.pos())
    
    def mouseMoveEvent(self, event):
        """Handle mouse move"""
        if self.is_pressed:
            self.updateStickPosition(event.pos())
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton:
            self.is_pressed = False
            # Reset to center
            self.stick_position = QPointF(0, 0)
            self.update()
            self.positionChanged.emit(0.0, 0.0)
    
    def updateStickPosition(self, mouse_pos):
        """Update stick position based on mouse position"""
        # Calculate center
        center_x = self.width() // 2
        center_y = self.height() // 2
        size = min(self.width(), self.height())
        outer_radius = size // 2 - 20
        
        # Calculate offset from center
        dx = mouse_pos.x() - center_x
        dy = mouse_pos.y() - center_y
        
        # Calculate distance from center
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Normalize to range [-1, 1]
        if distance > 0:
            # Limit to outer circle
            if distance > outer_radius:
                dx = dx * outer_radius / distance
                dy = dy * outer_radius / distance
                distance = outer_radius
            
            # Normalize
            normalized_x = dx / outer_radius
            normalized_y = dy / outer_radius
        else:
            normalized_x = 0
            normalized_y = 0
        
        # Update position
        self.stick_position = QPointF(normalized_x, normalized_y)
        self.update()
        
        # Emit signal
        self.positionChanged.emit(normalized_x, normalized_y)
    
    def setPosition(self, x, y):
        """Set joystick position programmatically"""
        # Clamp values to [-1, 1]
        x = max(-1.0, min(1.0, x))
        y = max(-1.0, min(1.0, y))
        
        self.stick_position = QPointF(x, y)
        self.update()
    
    def reset(self):
        """Reset joystick to center"""
        self.stick_position = QPointF(0, 0)
        self.is_pressed = False
        self.update()
        self.positionChanged.emit(0.0, 0.0)
