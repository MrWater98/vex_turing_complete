# -*- coding: utf-8 -*-
"""F 扩展（单精度）。D 扩展复用相同指令表，只修改 fmt（见 ext_d.py）。"""
from .formats import Instr, OP


def fp_instructions(ext, sfx, fmt, nbits):
    """sfx 为 '.s' 或 '.d'；fmt 为 0b00（S）或 0b01（D）。"""
    E = ext
    f7 = lambda f5: (f5 << 2) | fmt
    load_f3, store_f3 = (0b010, 0b010) if fmt == 0 else (0b011, 0b011)
    out = [
        Instr('flw' if fmt == 0 else 'fld', 'FL', OP['LOAD_FP'], load_f3, ext=E,
              desc='rd = mem%s[rs1 + imm] (NaN-boxed if 32-bit)' % nbits),
        Instr('fsw' if fmt == 0 else 'fsd', 'FS', OP['STORE_FP'], store_f3, ext=E,
              desc='mem%s[rs1 + imm] = rs2' % nbits),

        Instr('fmadd' + sfx,  'R4', OP['MADD'],  funct7=fmt, ext=E, desc='rd = rs1 * rs2 + rs3'),
        Instr('fmsub' + sfx,  'R4', OP['MSUB'],  funct7=fmt, ext=E, desc='rd = rs1 * rs2 - rs3'),
        Instr('fnmsub' + sfx, 'R4', OP['NMSUB'], funct7=fmt, ext=E, desc='rd = -(rs1 * rs2) + rs3'),
        Instr('fnmadd' + sfx, 'R4', OP['NMADD'], funct7=fmt, ext=E, desc='rd = -(rs1 * rs2) - rs3'),

        Instr('fadd' + sfx, 'FR', OP['OP_FP'], funct7=f7(0b00000), ext=E, desc='rd = rs1 + rs2'),
        Instr('fsub' + sfx, 'FR', OP['OP_FP'], funct7=f7(0b00001), ext=E, desc='rd = rs1 - rs2'),
        Instr('fmul' + sfx, 'FR', OP['OP_FP'], funct7=f7(0b00010), ext=E, desc='rd = rs1 * rs2'),
        Instr('fdiv' + sfx, 'FR', OP['OP_FP'], funct7=f7(0b00011), ext=E, desc='rd = rs1 / rs2'),
        Instr('fsqrt' + sfx, 'FR2', OP['OP_FP'], funct7=f7(0b01011), rs2=0, regs=('freg', 'freg'), ext=E, desc='rd = sqrt(rs1)'),

        Instr('fsgnj' + sfx,  'FR3', OP['OP_FP'], 0b000, f7(0b00100), regs=('freg', 'freg', 'freg'), ext=E, desc='rd = |rs1| with sign of rs2'),
        Instr('fsgnjn' + sfx, 'FR3', OP['OP_FP'], 0b001, f7(0b00100), regs=('freg', 'freg', 'freg'), ext=E, desc='rd = |rs1| with inverted sign of rs2'),
        Instr('fsgnjx' + sfx, 'FR3', OP['OP_FP'], 0b010, f7(0b00100), regs=('freg', 'freg', 'freg'), ext=E, desc='rd = rs1 with sign = sign(rs1) xor sign(rs2)'),
        Instr('fmin' + sfx, 'FR3', OP['OP_FP'], 0b000, f7(0b00101), regs=('freg', 'freg', 'freg'), ext=E, desc='rd = min(rs1, rs2)'),
        Instr('fmax' + sfx, 'FR3', OP['OP_FP'], 0b001, f7(0b00101), regs=('freg', 'freg', 'freg'), ext=E, desc='rd = max(rs1, rs2)'),

        Instr('fcvt.w' + sfx,  'FR2', OP['OP_FP'], funct7=f7(0b11000), rs2=0b00000, regs=('reg', 'freg'), ext=E, desc='rd = int32(rs1) sign-extended'),
        Instr('fcvt.wu' + sfx, 'FR2', OP['OP_FP'], funct7=f7(0b11000), rs2=0b00001, regs=('reg', 'freg'), ext=E, desc='rd = uint32(rs1) sign-extended'),
        Instr('fcvt.l' + sfx,  'FR2', OP['OP_FP'], funct7=f7(0b11000), rs2=0b00010, regs=('reg', 'freg'), ext=E, desc='rd = int64(rs1)'),
        Instr('fcvt.lu' + sfx, 'FR2', OP['OP_FP'], funct7=f7(0b11000), rs2=0b00011, regs=('reg', 'freg'), ext=E, desc='rd = uint64(rs1)'),
        Instr('fcvt' + sfx + '.w',  'FR2', OP['OP_FP'], funct7=f7(0b11010), rs2=0b00000, regs=('freg', 'reg'), ext=E, desc='rd = float(int32(rs1))'),
        Instr('fcvt' + sfx + '.wu', 'FR2', OP['OP_FP'], funct7=f7(0b11010), rs2=0b00001, regs=('freg', 'reg'), ext=E, desc='rd = float(uint32(rs1))'),
        Instr('fcvt' + sfx + '.l',  'FR2', OP['OP_FP'], funct7=f7(0b11010), rs2=0b00010, regs=('freg', 'reg'), ext=E, desc='rd = float(int64(rs1))'),
        Instr('fcvt' + sfx + '.lu', 'FR2', OP['OP_FP'], funct7=f7(0b11010), rs2=0b00011, regs=('freg', 'reg'), ext=E, desc='rd = float(uint64(rs1))'),

        Instr('feq' + sfx, 'FR3', OP['OP_FP'], 0b010, f7(0b10100), regs=('reg', 'freg', 'freg'), ext=E, desc='rd = (rs1 == rs2)'),
        Instr('flt' + sfx, 'FR3', OP['OP_FP'], 0b001, f7(0b10100), regs=('reg', 'freg', 'freg'), ext=E, desc='rd = (rs1 < rs2)'),
        Instr('fle' + sfx, 'FR3', OP['OP_FP'], 0b000, f7(0b10100), regs=('reg', 'freg', 'freg'), ext=E, desc='rd = (rs1 <= rs2)'),
        Instr('fclass' + sfx, 'FR3', OP['OP_FP'], 0b001, f7(0b11100), rs2=0, regs=('reg', 'freg'), ext=E, desc='rd = classification mask of rs1'),
    ]
    if fmt == 0:
        out += [
            Instr('fmv.x.w', 'FR3', OP['OP_FP'], 0b000, f7(0b11100), rs2=0, regs=('reg', 'freg'), ext=E, desc='rd = sext(rs1[31:0]) raw bits'),
            Instr('fmv.w.x', 'FR3', OP['OP_FP'], 0b000, f7(0b11110), rs2=0, regs=('freg', 'reg'), ext=E, desc='rd = NaN-box(rs1[31:0]) raw bits'),
        ]
    else:
        out += [
            Instr('fmv.x.d', 'FR3', OP['OP_FP'], 0b000, f7(0b11100), rs2=0, regs=('reg', 'freg'), ext=E, desc='rd = rs1 raw bits'),
            Instr('fmv.d.x', 'FR3', OP['OP_FP'], 0b000, f7(0b11110), rs2=0, regs=('freg', 'reg'), ext=E, desc='rd = rs1 raw bits'),
            Instr('fcvt.s.d', 'FR2', OP['OP_FP'], funct7=(0b01000 << 2) | 0b00, rs2=0b00001, regs=('freg', 'freg'), ext=E, desc='rd = single(rs1)'),
            Instr('fcvt.d.s', 'FR2', OP['OP_FP'], funct7=(0b01000 << 2) | 0b01, rs2=0b00000, regs=('freg', 'freg'), ext=E, desc='rd = double(rs1)'),
        ]
    return out


INSTRUCTIONS = fp_instructions('F', '.s', 0b00, '32')
