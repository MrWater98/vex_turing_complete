# -*- coding: utf-8 -*-
"""指令格式定义。

从同一张表（Instr）生成两种结果：
  1. 游戏汇编器使用的 .isa 定义文本（render_isa）
  2. Python 参考编码器使用的 32 位机器码（encode）

机器码行最左侧是 MSB（bit 31）。操作数始终使用位切片表示，例如 %d[4:0]。
游戏汇编器的单字符格式只读取操作数名称的首字母，因此 rd/rs1/rs2 等首字母相同的名称无法区分。
所以所有操作数名称都只有一个字符：
  %d rd   %a rs1   %b rs2   %c rs3   %i 立即数   %t 分支目标   %o 虚拟偏移
  %s 移位量   %n CSR 编号   %z CSR 立即数   %r 舍入模式

游戏要求立即数操作数带有位宽类型。游戏可执行文件中的汇编器错误信息示例：
  "Immediate operand must have size constraint, e.g. %a:U8(immediate)."
  "Expected an U for unsigned or S for signed here"
  "Operand value outside of {n}-bit signed range"
各类别的类型位于 TYPE_OF。若范围断言由类型检查，则将 expr 设为 None，不写入 .isa，只供 Python 参考编码器使用。
"""
from dataclasses import dataclass

OP = {
    'LOAD': 0b0000011, 'LOAD_FP': 0b0000111, 'MISC_MEM': 0b0001111, 'OP_IMM': 0b0010011,
    'AUIPC': 0b0010111, 'OP_IMM_32': 0b0011011, 'STORE': 0b0100011, 'STORE_FP': 0b0100111,
    'AMO': 0b0101111, 'OP': 0b0110011, 'LUI': 0b0110111, 'OP_32': 0b0111011,
    'MADD': 0b1000011, 'MSUB': 0b1000111, 'NMSUB': 0b1001011, 'NMADD': 0b1001111,
    'OP_FP': 0b1010011, 'BRANCH': 0b1100011, 'JALR': 0b1100111, 'JAL': 0b1101111,
    'SYSTEM': 0b1110011,
}


@dataclass
class Instr:
    mnemonic: str
    fmt: str                 # 下方 FORMATS 中的键
    opcode: int
    funct3: int = None
    funct7: int = None       # SH6 中为 funct6；AMO/LR 中为 funct5
    rs2: int = None          # rs2 字段固定的指令（fsqrt、fcvt、fmv、lr）
    regs: tuple = None       # 操作数寄存器类别（用于 FR2/FR3），例如 ('reg', 'freg')
    rm: bool = False         # 是否包含舍入模式操作数
    aqrl: int = 0            # AMO: aq<<1 | rl
    ext: str = 'I'
    desc: str = ''


def bits(v, n):
    return format(v & ((1 << n) - 1), '0%db' % n)


# ---------------------------------------------------------------------------
# 各格式定义：语法操作数列表、机器码 token、虚拟操作数和断言
#
# 语法操作数：(名称，类别)；类别 = reg | freg | mem | mem0 | rm | imm | imm20 | imm32 | sh6 | sh5 | zimm | csr | target
# 机器码 token：字面位串或 '%x[hi:lo]'
# ---------------------------------------------------------------------------

# expr 为 None 的断言由操作数类型（S12、U20 等）检查，因此不写入 .isa。
I12_ASSERT = (None, lambda v: -2048 <= v['i'] <= 2047, 'immediate out of 12-bit signed range')
U20_ASSERT = (None, lambda v: 0 <= v['i'] <= 1048575, 'immediate out of 20-bit unsigned range')
SH6_ASSERT = (None, lambda v: 0 <= v['s'] <= 63, 'shift amount must be 0..63')
SH5_ASSERT = (None, lambda v: 0 <= v['s'] <= 31, 'shift amount must be 0..31')
CSR_ASSERT = (None, lambda v: 0 <= v['n'] <= 4095, 'csr number must be 0..4095')
ZIMM_ASSERT = (None, lambda v: 0 <= v['z'] <= 31, 'csr immediate must be 0..31')
T32_ASSERT = (None, lambda v: 0 <= v['t'] <= 4294967295, 'target must be a 32-bit unsigned address')
B_ALIGN = ('%o % 2 == 0', lambda v: v['o'] % 2 == 0, 'branch target must be 2-byte aligned')
B_RANGE = ('%o >= -4096 && %o <= 4094', lambda v: -4096 <= v['o'] <= 4094, 'branch target out of range (+-4 KiB)')
J_ALIGN = ('%o % 2 == 0', lambda v: v['o'] % 2 == 0, 'jump target must be 2-byte aligned')
J_RANGE = ('%o >= -1048576 && %o <= 1048574', lambda v: -1048576 <= v['o'] <= 1048574, 'jump target out of range (+-1 MiB)')

PCREL = [('o', '%t - $start', lambda v, pc: v['t'] - pc)]


def _rm_tokens(instr, with_rm):
    return '%r[2:0]' if with_rm else '111'


def definitions(instr):
    """将 Instr 转换为 [(operands, virtuals, asserts, mc_tokens)]；有无舍入模式时可能生成两项。"""
    f = instr
    f3 = bits(f.funct3, 3) if f.funct3 is not None else None
    op = bits(f.opcode, 7)
    fmt = f.fmt
    if fmt == 'R':
        return [([('d', 'reg'), ('a', 'reg'), ('b', 'reg')], [], [],
                 [bits(f.funct7, 7), '%b[4:0]', '%a[4:0]', f3, '%d[4:0]', op])]
    if fmt == 'I':
        return [([('d', 'reg'), ('a', 'reg'), ('i', 'imm')], [], [I12_ASSERT],
                 ['%i[11:0]', '%a[4:0]', f3, '%d[4:0]', op])]
    if fmt == 'IL':      # rd, imm(rs1)
        return [([('d', 'reg'), ('i', 'imm'), ('a', 'mem')], [], [I12_ASSERT],
                 ['%i[11:0]', '%a[4:0]', f3, '%d[4:0]', op])]
    if fmt == 'FL':
        return [([('d', 'freg'), ('i', 'imm'), ('a', 'mem')], [], [I12_ASSERT],
                 ['%i[11:0]', '%a[4:0]', f3, '%d[4:0]', op])]
    if fmt == 'S':
        return [([('b', 'reg'), ('i', 'imm'), ('a', 'mem')], [], [I12_ASSERT],
                 ['%i[11:5]', '%b[4:0]', '%a[4:0]', f3, '%i[4:0]', op])]
    if fmt == 'FS':
        return [([('b', 'freg'), ('i', 'imm'), ('a', 'mem')], [], [I12_ASSERT],
                 ['%i[11:5]', '%b[4:0]', '%a[4:0]', f3, '%i[4:0]', op])]
    if fmt == 'B':
        return [([('a', 'reg'), ('b', 'reg'), ('t', 'target')], PCREL, [T32_ASSERT, B_ALIGN, B_RANGE],
                 ['%o[12]', '%o[10:5]', '%b[4:0]', '%a[4:0]', f3, '%o[4:1]', '%o[11]', op])]
    if fmt == 'U':
        return [([('d', 'reg'), ('i', 'imm20')], [], [U20_ASSERT],
                 ['%i[19:0]', '%d[4:0]', op])]
    if fmt == 'J':
        return [([('d', 'reg'), ('t', 'target')], PCREL, [T32_ASSERT, J_ALIGN, J_RANGE],
                 ['%o[20]', '%o[10:1]', '%o[11]', '%o[19:12]', '%d[4:0]', op])]
    if fmt == 'SH6':
        return [([('d', 'reg'), ('a', 'reg'), ('s', 'sh6')], [], [SH6_ASSERT],
                 [bits(f.funct7, 6), '%s[5:0]', '%a[4:0]', f3, '%d[4:0]', op])]
    if fmt == 'SH5':
        return [([('d', 'reg'), ('a', 'reg'), ('s', 'sh5')], [], [SH5_ASSERT],
                 [bits(f.funct7, 7), '%s[4:0]', '%a[4:0]', f3, '%d[4:0]', op])]
    if fmt == 'CSR':
        return [([('d', 'reg'), ('n', 'csr'), ('a', 'reg')], [], [CSR_ASSERT],
                 ['%n[11:0]', '%a[4:0]', f3, '%d[4:0]', op])]
    if fmt == 'CSRI':
        return [([('d', 'reg'), ('n', 'csr'), ('z', 'zimm')], [], [CSR_ASSERT, ZIMM_ASSERT],
                 ['%n[11:0]', '%z[4:0]', f3, '%d[4:0]', op])]
    if fmt == 'FIX':     # 无操作数；funct7 字段位置容纳完整 32 位指令字
        return [([], [], [], [bits(f.funct7, 32)])]
    if fmt == 'AMO':     # rd, rs2, (rs1)
        return [([('d', 'reg'), ('b', 'reg'), ('a', 'mem0')], [], [],
                 [bits(f.funct7, 5), bits(f.aqrl, 2), '%b[4:0]', '%a[4:0]', f3, '%d[4:0]', op])]
    if fmt == 'LR':      # rd, (rs1)
        return [([('d', 'reg'), ('a', 'mem0')], [], [],
                 [bits(f.funct7, 5), bits(f.aqrl, 2), '00000', '%a[4:0]', f3, '%d[4:0]', op])]
    if fmt == 'FR':      # rd, rs1, rs2 [, rm]
        base = [('d', 'freg'), ('a', 'freg'), ('b', 'freg')]
        out = []
        for with_rm in (True, False):
            ops = base + ([('r', 'rm')] if with_rm else [])
            out.append((ops, [], [], [bits(f.funct7, 7), '%b[4:0]', '%a[4:0]', _rm_tokens(f, with_rm), '%d[4:0]', op]))
        return out
    if fmt == 'FR2':     # rd、rs1 [、rm]（rs2 固定）
        rd_k, a_k = f.regs
        out = []
        for with_rm in (True, False):
            ops = [('d', rd_k), ('a', a_k)] + ([('r', 'rm')] if with_rm else [])
            out.append((ops, [], [], [bits(f.funct7, 7), bits(f.rs2, 5), '%a[4:0]', _rm_tokens(f, with_rm), '%d[4:0]', op]))
        return out
    if fmt == 'FR3':     # funct3 固定且没有 rm；regs 有两项时 rs2 固定，有三项时 rs2 是操作数
        if len(f.regs) == 3:
            rd_k, a_k, b_k = f.regs
            return [([('d', rd_k), ('a', a_k), ('b', b_k)], [], [],
                     [bits(f.funct7, 7), '%b[4:0]', '%a[4:0]', f3, '%d[4:0]', op])]
        rd_k, a_k = f.regs
        return [([('d', rd_k), ('a', a_k)], [], [],
                 [bits(f.funct7, 7), bits(f.rs2, 5), '%a[4:0]', f3, '%d[4:0]', op])]
    if fmt == 'R4':      # rd、rs1、rs2、rs3 [、rm]；funct7 字段位置只使用 fmt（2 位）
        base = [('d', 'freg'), ('a', 'freg'), ('b', 'freg'), ('c', 'freg')]
        out = []
        for with_rm in (True, False):
            ops = base + ([('r', 'rm')] if with_rm else [])
            out.append((ops, [], [], ['%c[4:0]', bits(f.funct7, 2), '%b[4:0]', '%a[4:0]', _rm_tokens(f, with_rm), '%d[4:0]', op]))
        return out
    raise ValueError('unknown format %s for %s' % (fmt, f.mnemonic))


# ---------------------------------------------------------------------------
# .isa 文本
# ---------------------------------------------------------------------------

def isa_token(tok):
    """将机器码 token 转换为游戏语法。游戏解析器要求切片中始终有冒号，因此将 %o[20] 写成 %o[20:20]。
    （游戏错误信息 "Expected slice syntax after field/pattern reference in bit pattern"；2026-09-15 的 A1 检查确认。）"""
    if tok.startswith('%') and '[' in tok and ':' not in tok:
        n = tok[tok.index('[') + 1:-1]
        return '%s[%s:%s]' % (tok[:tok.index('[')], n, n)
    return tok


FIELD_OF = {'reg': 'reg', 'freg': 'freg', 'rm': 'rm',
            'imm': 'immediate', 'imm20': 'immediate', 'imm32': 'immediate',
            'sh6': 'immediate', 'sh5': 'immediate', 'zimm': 'immediate',
            'target': 'immediate | label', 'csr': 'csr | immediate'}

# 不同立即数类别的位宽类型（S 表示有符号，U 表示无符号）；游戏汇编器要求每个立即数都声明类型。
#   imm    I/S 型 12 位      imm20  lui/auipc 的高 20 位（0..0xFFFFF）
#   sh6    64 位移位量        sh5    W 型移位量      zimm  CSR 立即数      csr  CSR 编号
#   target 绝对地址（标签）   imm32  li32（使用 S33 接收 -2^31..2^32-1）
TYPE_OF = {'imm': 'S12', 'imm20': 'U20', 'imm32': 'S33', 'sh6': 'U6', 'sh5': 'U5',
           'zimm': 'U5', 'csr': 'U12', 'target': 'U32'}


def syntax_line(mnemonic, operands):
    """生成语法行。内存操作数遵循 RISC-V 习惯写成 imm(rs1)，立即数需带位宽类型。"""
    parts = []
    i = 0
    while i < len(operands):
        name, kind = operands[i]
        if kind == 'mem':                 # 前一个操作数是立即数，后面接 (rs1)
            parts[-1] = parts[-1] + ' (%%%s(reg))' % name
        elif kind == 'mem0':
            parts.append('(%%%s(reg))' % name)
        else:
            t = TYPE_OF.get(kind)
            parts.append('%%%s%s(%s)' % (name, ':' + t if t else '', FIELD_OF[kind]))
        i += 1
    return mnemonic if not parts else mnemonic + ' ' + ', '.join(parts)


def render_isa(instr):
    """将一个 Instr 转换为一个或多个 .isa 定义块。"""
    blocks = []
    for operands, virtuals, asserts, mc in definitions(instr):
        lines = [syntax_line(instr.mnemonic, operands)]
        for name, expr, _ in virtuals:
            lines.append('%%%s = %s' % (name, expr))
        for expr, _, msg in asserts:
            if expr is None:          # 由操作数类型执行检查
                continue
            lines.append('assert(%s, "%s: %s")' % (expr, instr.mnemonic, msg))
        lines.append(' '.join(isa_token(t) for t in mc))
        lines.append('# [%s] %s' % (instr.ext, instr.desc or instr.mnemonic))
        blocks.append('\n'.join(lines))
    return '\n\n'.join(blocks)


# ---------------------------------------------------------------------------
# 编码
# ---------------------------------------------------------------------------

def encode_tokens(mc, values):
    """根据机器码 token 列表和操作数值生成整数（最左侧为 MSB）。"""
    word = 0
    nbits = 0
    for tok in mc:
        if tok[0] in '01':
            word = (word << len(tok)) | int(tok, 2)
            nbits += len(tok)
            continue
        name = tok[1]
        hi, lo = tok[tok.index('[') + 1:-1].split(':') if ':' in tok else (tok[tok.index('[') + 1:-1],) * 2
        hi, lo = int(hi), int(lo)
        v = values[name]
        width = hi - lo + 1
        word = (word << width) | ((v >> lo) & ((1 << width) - 1))
        nbits += width
    assert nbits % 32 == 0, 'machine code is %d bits' % nbits
    return word, nbits


def encode(instr, operands_present, values, pc):
    """values：操作数名称到整数的映射；operands_present：实际提供的操作数名称集合。"""
    for operands, virtuals, asserts, mc in definitions(instr):
        names = {n for n, _ in operands}
        if names != operands_present:
            continue
        vals = dict(values)
        for name, _, fn in virtuals:
            vals[name] = fn(vals, pc)
        for _, fn, msg in asserts:
            if not fn(vals):
                raise ValueError('%s: %s' % (instr.mnemonic, msg))
        return encode_tokens(mc, vals)
    raise ValueError('%s: operand set %s does not match any form' % (instr.mnemonic, sorted(operands_present)))
