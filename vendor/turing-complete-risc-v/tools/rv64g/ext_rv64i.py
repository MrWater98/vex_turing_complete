# -*- coding: utf-8 -*-
"""RV64I 基本整数指令（含 ecall/ebreak/fence）。"""
from .formats import Instr, OP

E = 'I'
INSTRUCTIONS = [
    Instr('lui',   'U', OP['LUI'],   ext=E, desc='rd = sext(imm << 12)'),
    Instr('auipc', 'U', OP['AUIPC'], ext=E, desc='rd = pc + sext(imm << 12)'),
    Instr('jal',   'J', OP['JAL'],   ext=E, desc='rd = pc + 4; pc += offset'),
    Instr('jalr',  'IL', OP['JALR'], 0b000, ext=E, desc='rd = pc + 4; pc = (rs1 + imm) & ~1'),
    Instr('jalr',  'I',  OP['JALR'], 0b000, ext=E, desc='rd = pc + 4; pc = (rs1 + imm) & ~1  (register-first syntax)'),

    Instr('beq',  'B', OP['BRANCH'], 0b000, ext=E, desc='if rs1 == rs2: pc += offset'),
    Instr('bne',  'B', OP['BRANCH'], 0b001, ext=E, desc='if rs1 != rs2: pc += offset'),
    Instr('blt',  'B', OP['BRANCH'], 0b100, ext=E, desc='if rs1 < rs2 (signed): pc += offset'),
    Instr('bge',  'B', OP['BRANCH'], 0b101, ext=E, desc='if rs1 >= rs2 (signed): pc += offset'),
    Instr('bltu', 'B', OP['BRANCH'], 0b110, ext=E, desc='if rs1 < rs2 (unsigned): pc += offset'),
    Instr('bgeu', 'B', OP['BRANCH'], 0b111, ext=E, desc='if rs1 >= rs2 (unsigned): pc += offset'),

    Instr('lb',  'IL', OP['LOAD'], 0b000, ext=E, desc='rd = sext(mem8[rs1 + imm])'),
    Instr('lh',  'IL', OP['LOAD'], 0b001, ext=E, desc='rd = sext(mem16[rs1 + imm])'),
    Instr('lw',  'IL', OP['LOAD'], 0b010, ext=E, desc='rd = sext(mem32[rs1 + imm])'),
    Instr('ld',  'IL', OP['LOAD'], 0b011, ext=E, desc='rd = mem64[rs1 + imm]'),
    Instr('lbu', 'IL', OP['LOAD'], 0b100, ext=E, desc='rd = zext(mem8[rs1 + imm])'),
    Instr('lhu', 'IL', OP['LOAD'], 0b101, ext=E, desc='rd = zext(mem16[rs1 + imm])'),
    Instr('lwu', 'IL', OP['LOAD'], 0b110, ext=E, desc='rd = zext(mem32[rs1 + imm])'),

    Instr('sb', 'S', OP['STORE'], 0b000, ext=E, desc='mem8[rs1 + imm] = rs2[7:0]'),
    Instr('sh', 'S', OP['STORE'], 0b001, ext=E, desc='mem16[rs1 + imm] = rs2[15:0]'),
    Instr('sw', 'S', OP['STORE'], 0b010, ext=E, desc='mem32[rs1 + imm] = rs2[31:0]'),
    Instr('sd', 'S', OP['STORE'], 0b011, ext=E, desc='mem64[rs1 + imm] = rs2'),

    Instr('addi',  'I', OP['OP_IMM'], 0b000, ext=E, desc='rd = rs1 + imm'),
    Instr('slti',  'I', OP['OP_IMM'], 0b010, ext=E, desc='rd = (rs1 < imm) signed'),
    Instr('sltiu', 'I', OP['OP_IMM'], 0b011, ext=E, desc='rd = (rs1 < imm) unsigned'),
    Instr('xori',  'I', OP['OP_IMM'], 0b100, ext=E, desc='rd = rs1 ^ imm'),
    Instr('ori',   'I', OP['OP_IMM'], 0b110, ext=E, desc='rd = rs1 | imm'),
    Instr('andi',  'I', OP['OP_IMM'], 0b111, ext=E, desc='rd = rs1 & imm'),
    Instr('slli',  'SH6', OP['OP_IMM'], 0b001, 0b000000, ext=E, desc='rd = rs1 << shamt'),
    Instr('srli',  'SH6', OP['OP_IMM'], 0b101, 0b000000, ext=E, desc='rd = rs1 >> shamt (logical)'),
    Instr('srai',  'SH6', OP['OP_IMM'], 0b101, 0b010000, ext=E, desc='rd = rs1 >> shamt (arithmetic)'),

    Instr('add',  'R', OP['OP'], 0b000, 0b0000000, ext=E, desc='rd = rs1 + rs2'),
    Instr('sub',  'R', OP['OP'], 0b000, 0b0100000, ext=E, desc='rd = rs1 - rs2'),
    Instr('sll',  'R', OP['OP'], 0b001, 0b0000000, ext=E, desc='rd = rs1 << rs2[5:0]'),
    Instr('slt',  'R', OP['OP'], 0b010, 0b0000000, ext=E, desc='rd = (rs1 < rs2) signed'),
    Instr('sltu', 'R', OP['OP'], 0b011, 0b0000000, ext=E, desc='rd = (rs1 < rs2) unsigned'),
    Instr('xor',  'R', OP['OP'], 0b100, 0b0000000, ext=E, desc='rd = rs1 ^ rs2'),
    Instr('srl',  'R', OP['OP'], 0b101, 0b0000000, ext=E, desc='rd = rs1 >> rs2[5:0] (logical)'),
    Instr('sra',  'R', OP['OP'], 0b101, 0b0100000, ext=E, desc='rd = rs1 >> rs2[5:0] (arithmetic)'),
    Instr('or',   'R', OP['OP'], 0b110, 0b0000000, ext=E, desc='rd = rs1 | rs2'),
    Instr('and',  'R', OP['OP'], 0b111, 0b0000000, ext=E, desc='rd = rs1 & rs2'),

    Instr('addiw', 'I',   OP['OP_IMM_32'], 0b000, ext=E, desc='rd = sext32(rs1 + imm)'),
    Instr('slliw', 'SH5', OP['OP_IMM_32'], 0b001, 0b0000000, ext=E, desc='rd = sext32(rs1[31:0] << shamt)'),
    Instr('srliw', 'SH5', OP['OP_IMM_32'], 0b101, 0b0000000, ext=E, desc='rd = sext32(rs1[31:0] >> shamt) logical'),
    Instr('sraiw', 'SH5', OP['OP_IMM_32'], 0b101, 0b0100000, ext=E, desc='rd = sext32(rs1[31:0] >> shamt) arithmetic'),

    Instr('addw', 'R', OP['OP_32'], 0b000, 0b0000000, ext=E, desc='rd = sext32(rs1 + rs2)'),
    Instr('subw', 'R', OP['OP_32'], 0b000, 0b0100000, ext=E, desc='rd = sext32(rs1 - rs2)'),
    Instr('sllw', 'R', OP['OP_32'], 0b001, 0b0000000, ext=E, desc='rd = sext32(rs1[31:0] << rs2[4:0])'),
    Instr('srlw', 'R', OP['OP_32'], 0b101, 0b0000000, ext=E, desc='rd = sext32(rs1[31:0] >> rs2[4:0]) logical'),
    Instr('sraw', 'R', OP['OP_32'], 0b101, 0b0100000, ext=E, desc='rd = sext32(rs1[31:0] >> rs2[4:0]) arithmetic'),

    # fence：pred = succ = iorw（0b1111），其余字段为 0
    Instr('fence',  'FIX', OP['MISC_MEM'], funct7=0x0FF0000F, ext=E, desc='memory ordering fence (nop on this core)'),
    Instr('ecall',  'FIX', OP['SYSTEM'], funct7=0x00000073, ext=E, desc='environment call (trap to mtvec)'),
    Instr('ebreak', 'FIX', OP['SYSTEM'], funct7=0x00100073, ext=E, desc='breakpoint (halt)'),
]
