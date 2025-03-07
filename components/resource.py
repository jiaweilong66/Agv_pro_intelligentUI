#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import os
import sys
import typing as T


class FileResource:
    """
    FileResource is a class to read and write file.
    """

    def __init__(self, relative_path: str):
        if getattr(sys, 'frozen', False):
            base_path = getattr(sys, "_MEIPASS")
        else:
            base_path = os.getcwd()
        self.path = os.path.join(base_path, relative_path)

    def get(self, *args):
        return os.path.join(self.path, *args)

    def read(self, *filepath):
        with open(self.get(*filepath), "r", encoding="utf-8") as f:
            return f.read()

    def write(self, data: str, *filepath):
        with open(self.get(*filepath), "w", encoding="utf-8") as f:
            f.write(data)

    def load_json(self, *filepath):
        with open(self.get(*filepath), "r", encoding="utf-8") as f:
            return json.load(f)

    def dump_json(self, data: T.Union[dict, list], *filepath):
        with open(self.get(*filepath, ), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @classmethod
    def generation(cls, desc: str, target: str):
        with open(desc, "r", encoding="utf-8") as f:
            content = f.read()
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return target




