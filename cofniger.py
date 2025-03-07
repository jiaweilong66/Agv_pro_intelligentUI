#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import logging


class Config:
    debug = True
    resource_path = "resources"

    class Logger:
        basic_format = "%(asctime)s - %(name)s - [%(levelname)-s] - %(message)s"
        basic_datefmt = '%Y-%m-%d %H:%M:%S'
        basic_filepath = "manager.log"
        console_name = "console"
        console_format = "【%(levelname)s】 %(message)s"
        console_datefmt = '%H:%M:%S'
        console_level = logging.DEBUG
