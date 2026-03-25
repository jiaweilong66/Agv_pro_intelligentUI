#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import typing as T

# 尝试导入 Jetson.GPIO，如果失败则使用模拟模块
try:
    import Jetson.GPIO as GPIO
    MOCK_MODE = False
except (ImportError, ModuleNotFoundError):
    print("Warning: Jetson.GPIO not found, using mock GPIO for UI testing")
    # 创建模拟的 GPIO 模块
    class MockGPIO:
        IN = 0
        OUT = 1
        HIGH = 1
        LOW = 0
        PWM = 2
        BCM = 11
        PUD_UP = 22
        PUD_DOWN = 21
        BOTH = 33
        
        _pin_states = {}
        
        @classmethod
        def setup(cls, channel, mode):
            cls._pin_states[channel] = cls.LOW
            
        @classmethod
        def setmode(cls, mode):
            pass
            
        @classmethod
        def input(cls, channel):
            return cls._pin_states.get(channel, cls.LOW)
            
        @classmethod
        def output(cls, channel, value):
            cls._pin_states[channel] = value
            
        @classmethod
        def add_event_detect(cls, channel, edge, callback=None, bouncetime=None):
            pass
            
        @classmethod
        def remove_event_detect(cls, channel):
            pass
            
        @classmethod
        def gpio_function(cls, channel):
            return cls.OUT
            
        @classmethod
        def cleanup(cls, channels=None):
            if channels:
                if isinstance(channels, (list, tuple)):
                    for ch in channels:
                        cls._pin_states.pop(ch, None)
                else:
                    cls._pin_states.pop(channels, None)
            else:
                cls._pin_states.clear()
    
    GPIO = MockGPIO()
    MOCK_MODE = True


class GpioHandler:
    IN = GPIO.IN
    OUT = GPIO.OUT
    HIGH = GPIO.HIGH
    LOW = GPIO.LOW
    PWM = GPIO.PWM

    BCM = GPIO.BCM
    PUD_UP = GPIO.PUD_UP
    PUD_DOWN = GPIO.PUD_DOWN

    @classmethod
    def islow(cls, pin_number: int) -> bool:
        return cls.input(pin_number) == GPIO.LOW

    @classmethod
    def ishigh(cls, pin_number: int) -> bool:
        return cls.input(pin_number) == GPIO.HIGH

    @classmethod
    def setup(cls, channel: int, mode: int):
        GPIO.setup(channel, mode)

    @classmethod
    def setmode(cls, mode: int):
        GPIO.setmode(mode)

    @classmethod
    def input(cls, channel: int):
        return GPIO.input(channel)

    @classmethod
    def output(cls, channel: int, value: int):
        return GPIO.output(channel, value)

    @classmethod
    def event_detect(cls, channel: int, callback: T.Callable, bouncetime: int):
        GPIO.add_event_detect(channel, GPIO.BOTH, callback=callback, bouncetime=bouncetime)

    @classmethod
    def remove_event_detect(cls, channel: int):
        GPIO.remove_event_detect(channel)
        GPIO.cleanup(channel)

    @classmethod
    def gpio_function(cls, channel: int):
        return GPIO.gpio_function(channel)

    @classmethod
    def listening(cls, channel: int, callback: T.Callable, timeout: int, valid_signal: int = 0):
        def on_detect_callback(ori_channel):
            if cls.input(ori_channel) == valid_signal:
                callback()

        GPIO.add_event_detect(channel, GPIO.BOTH, callback=on_detect_callback, bouncetime=timeout)

    @classmethod
    def cleanup(cls, *channels: T.Tuple[int, ...]):
        channels = channels or None
        GPIO.cleanup(channels)
