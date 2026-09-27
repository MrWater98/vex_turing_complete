# -*- coding: utf-8 -*-
"""A 扩展：lr/sc 和 9 种 AMO，分别支持 W（32 位）/D（64 位）及 aq/rl 四种后缀组合。"""
from .formats import Instr, OP

E = 'A'
AMOS = [  # （名称，funct5）
    ('amoswap', 0b00001), ('amoadd', 0b00000), ('amoxor', 0b00100), ('amoand', 0b01100),
    ('amoor', 0b01000), ('amomin', 0b10000), ('amomax', 0b10100), ('amominu', 0b11000),
    ('amomaxu', 0b11100),
]
SUFFIX = [('', 0b00), ('.aq', 0b10), ('.rl', 0b01), ('.aqrl', 0b11)]
WIDTH = [('.w', 0b010, '32'), ('.d', 0b011, '64')]

INSTRUCTIONS = []
for w, f3, nbits in WIDTH:
    for sfx, aqrl in SUFFIX:
        INSTRUCTIONS.append(Instr('lr' + w + sfx, 'LR', OP['AMO'], f3, 0b00010, aqrl=aqrl, ext=E,
                                  desc='rd = mem%s[rs1]; reserve (always succeeds on this core)' % nbits))
        INSTRUCTIONS.append(Instr('sc' + w + sfx, 'AMO', OP['AMO'], f3, 0b00011, aqrl=aqrl, ext=E,
                                  desc='mem%s[rs1] = rs2; rd = 0 (success)' % nbits))
        for name, f5 in AMOS:
            INSTRUCTIONS.append(Instr(name + w + sfx, 'AMO', OP['AMO'], f3, f5, aqrl=aqrl, ext=E,
                                      desc='rd = mem%s[rs1]; mem%s[rs1] = op(rd, rs2)' % (nbits, nbits)))
