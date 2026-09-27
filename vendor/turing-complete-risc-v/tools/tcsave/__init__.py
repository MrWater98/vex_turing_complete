# -*- coding: utf-8 -*-
"""读写 Turing Complete 存档（circuit.data，格式版本 16）。

这是对游戏开发者公开的 save_monger（https://github.com/Stuffe/save_monger，CC0）中
common.nim、versions/v16.nim 和 state_to_binary 的 Python 移植。

文件由版本字节（16）和 Snappy 原始块组成；解压后是按小端序排列的定长字段。
"""
from .save16 import (Component, Wire, Point, Save, parse, serialize, load, dump,
                     KIND_NAMES, KIND_IDS, DIRECTIONS)

__all__ = ['Component', 'Wire', 'Point', 'Save', 'parse', 'serialize', 'load', 'dump',
           'KIND_NAMES', 'KIND_IDS', 'DIRECTIONS']
