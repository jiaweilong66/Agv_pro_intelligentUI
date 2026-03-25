#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Generate quick_start.ui file"""

ui_template = '''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>QuickStart</class>
 <widget class="QWidget" name="QuickStart">
  <property name="geometry">
   <rect><x>0</x><y>0</y><width>1280</width><height>800</height></rect>
  </property>
  <property name="windowTitle">
   <string>Quick Start</string>
  </property>
  <property name="styleSheet">
   <string notr="true">QWidget {{ background-color: #f0f0f0; }}
QPushButton {{ background-color: #4A90E2; color: white; border: none; border-radius: 5px; padding: 8px; font-size: 12px; font-weight: bold; }}
QPushButton:hover {{ background-color: #357ABD; }}
QGroupBox {{ background-color: white; border: 2px solid #ddd; border-radius: 8px; margin-top: 10px; font-weight: bold; padding-top: 15px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}</string>
  </property>
  <layout class="QVBoxLayout" name="verticalLayout">
   <property name="spacing"><number>10</number></property>
   <property name="leftMargin"><number>15</number></property>
   <property name="topMargin"><number>15</number></property>
   <property name="rightMargin"><number>15</number></property>
   <property name="bottomMargin"><number>15</number></property>
   
   <!-- Header -->
   <item>
    <layout class="QHBoxLayout" name="headerLayout">
     <item>
      <widget class="QPushButton" name="backButton">
       <property name="minimumSize"><size><width>300</width><height>50</height></size></property>
       <property name="maximumSize"><size><width>300</width><height>50</height></size></property>
       <property name="font"><font><pointsize>14</pointsize><weight>75</weight><bold>true</bold></font></property>
       <property name="styleSheet"><string notr="true">QPushButton {{ background-color: white; border: 2px solid #333; border-radius: 5px; color: black; }}
QPushButton:hover {{ background-color: #e0e0e0; }}</string></property>
       <property name="text"><string>Intelligent Logistics System</string></property>
      </widget>
     </item>
     <item><spacer name="horizontalSpacer"><property name="orientation"><enum>Qt::Horizontal</enum></property><property name="sizeHint" stdset="0"><size><width>40</width><height>20</height></size></property></spacer></item>
     <item>
      <widget class="QLabel" name="languageLabel">
       <property name="minimumSize"><size><width>200</width><height>50</height></size></property>
       <property name="font"><font><pointsize>14</pointsize><weight>75</weight><bold>true</bold></font></property>
       <property name="styleSheet"><string notr="true">QLabel {{ background-color: white; border: 2px solid #333; border-radius: 5px; padding: 10px; }}</string></property>
       <property name="text"><string>Language Selection</string></property>
       <property name="alignment"><set>Qt::AlignCenter</set></property>
      </widget>
     </item>
     <item>
      <widget class="QComboBox" name="languageComboBox">
       <property name="minimumSize"><size><width>120</width><height>50</height></size></property>
       <property name="font"><font><pointsize>12</pointsize></font></property>
       <property name="styleSheet"><string notr="true">QComboBox {{ background-color: white; border: 2px solid #333; border-radius: 5px; padding: 5px; }}</string></property>
       <item><property name="text"><string>English</string></property></item>
       <item><property name="text"><string>中文</string></property></item>
      </widget>
     </item>
    </layout>
   </item>
'''

with open('new_ui/quick_start.ui', 'w', encoding='utf-8') as f:
    f.write(ui_template)

print("UI file part 1 created successfully!")
