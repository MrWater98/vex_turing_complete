# -*- coding: utf-8 -*-
"""D 扩展（双精度）。复用 F 扩展的指令表，并将 fmt 设为 01。"""
from .ext_f import fp_instructions

INSTRUCTIONS = fp_instructions('D', '.d', 0b01, '64')
