#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
from pymycobot import MechArm270


class MechArmController(object):

    def __init__(self, comport: str, baudrate: int, debug: bool = False):
        self.__mech_arm = MechArm270(comport, baudrate, debug=debug)
        self.__timeout = 5
        self.log = self.__mech_arm.log

    @property
    def mech_arm(self):
        return self.__mech_arm

    def get_coords(self):
        while True:
            coords = self.__mech_arm.get_coords()
            if coords != -1 or coords is not None:
                return coords
            time.sleep(1)

    def get_angles(self):
        while True:
            angles = self.__mech_arm.get_angles()
            if angles != -1 or angles is not None:
                return angles
            time.sleep(1)

    def wait_to_position(self, position: list, speed: int = 50, move_id=0) -> None:
        start_time = time.time()
        if move_id == 0:
            self.__mech_arm.send_angles(position, speed)
        else:
            self.__mech_arm.send_coords(position, speed, mode=1)

        while time.time() - start_time < self.__timeout:
            try:
                is_moving = self.__mech_arm.is_moving()
                if is_moving == 0:
                    break
                time.sleep(0.1)
                # self.log.info(f" * mechArm moving status: {is_moving}")
                # in_position_code = self.__mech_arm.is_in_position(data=position, id=move_id)
                # if in_position_code is None:
                #     continue

                # if in_position_code == 1:
                #     break
            finally:
                time.sleep(0.1)

    def send_angles(self, angles: list, speed: int = 50) -> None:
        # return self.wait_to_position(angles, speed, move_id=0)
        self.__mech_arm.send_angles(angles, speed)
        self.wait()

    def send_coords(self, coords: list, speed: int = 50) -> None:
        # return self.wait_to_position(coords, speed, move_id=1)
        self.__mech_arm.send_coords(coords, speed, 1)
        self.wait()

    def wait(self):
        time.sleep(0.3)
        state = self.mech_arm.is_moving()
        while state != 0:
            state = self.mech_arm.is_moving()
            time.sleep(0.1)
