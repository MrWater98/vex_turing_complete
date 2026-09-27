# -*- coding: utf-8 -*-
"""M 扩展：13 种乘法和除法指令。"""
from .formats import Instr, OP

E = 'M'
F7 = 0b0000001
INSTRUCTIONS = [
    Instr('mul',    'R', OP['OP'], 0b000, F7, ext=E, desc='rd = (rs1 * rs2)[63:0]'),
    Instr('mulh',   'R', OP['OP'], 0b001, F7, ext=E, desc='rd = (rs1 * rs2)[127:64] signed x signed'),
    Instr('mulhsu', 'R', OP['OP'], 0b010, F7, ext=E, desc='rd = (rs1 * rs2)[127:64] signed x unsigned'),
    Instr('mulhu',  'R', OP['OP'], 0b011, F7, ext=E, desc='rd = (rs1 * rs2)[127:64] unsigned x unsigned'),
    Instr('div',    'R', OP['OP'], 0b100, F7, ext=E, desc='rd = rs1 / rs2 signed (div by 0 -> -1, overflow -> rs1)'),
    Instr('divu',   'R', OP['OP'], 0b101, F7, ext=E, desc='rd = rs1 / rs2 unsigned (div by 0 -> all ones)'),
    Instr('rem',    'R', OP['OP'], 0b110, F7, ext=E, desc='rd = rs1 % rs2 signed (div by 0 -> rs1, overflow -> 0)'),
    Instr('remu',   'R', OP['OP'], 0b111, F7, ext=E, desc='rd = rs1 % rs2 unsigned (div by 0 -> rs1)'),

    Instr('mulw',  'R', OP['OP_32'], 0b000, F7, ext=E, desc='rd = sext32(rs1[31:0] * rs2[31:0])'),
    Instr('divw',  'R', OP['OP_32'], 0b100, F7, ext=E, desc='rd = sext32(rs1[31:0] / rs2[31:0]) signed'),
    Instr('divuw', 'R', OP['OP_32'], 0b101, F7, ext=E, desc='rd = sext32(rs1[31:0] / rs2[31:0]) unsigned'),
    Instr('remw',  'R', OP['OP_32'], 0b110, F7, ext=E, desc='rd = sext32(rs1[31:0] % rs2[31:0]) signed'),
    Instr('remuw', 'R', OP['OP_32'], 0b111, F7, ext=E, desc='rd = sext32(rs1[31:0] % rs2[31:0]) unsigned'),
]
