# -*- coding: utf-8 -*-
"""Zifencei：fence.i（本处理器采用哈佛架构，因此实现为 nop）。"""
from .formats import Instr, OP

INSTRUCTIONS = [
    Instr('fence.i', 'FIX', OP['MISC_MEM'], funct7=0x0000100F, ext='Zifencei',
          desc='instruction-fetch fence (nop: program memory is separate)'),
]
