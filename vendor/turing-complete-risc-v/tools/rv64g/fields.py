# -*- coding: utf-8 -*-
"""寄存器、CSR 和舍入模式字段定义。

ISA 文件的 [fields] 部分和 Python 编码器共用此表。
"""

# 整数寄存器：（数字名称、ABI 名称……）
XREG = [
    ('x0', 'zero'), ('x1', 'ra'), ('x2', 'sp'), ('x3', 'gp'), ('x4', 'tp'),
    ('x5', 't0'), ('x6', 't1'), ('x7', 't2'), ('x8', 's0', 'fp'), ('x9', 's1'),
    ('x10', 'a0'), ('x11', 'a1'), ('x12', 'a2'), ('x13', 'a3'), ('x14', 'a4'),
    ('x15', 'a5'), ('x16', 'a6'), ('x17', 'a7'), ('x18', 's2'), ('x19', 's3'),
    ('x20', 's4'), ('x21', 's5'), ('x22', 's6'), ('x23', 's7'), ('x24', 's8'),
    ('x25', 's9'), ('x26', 's10'), ('x27', 's11'), ('x28', 't3'), ('x29', 't4'),
    ('x30', 't5'), ('x31', 't6'),
]

# 浮点寄存器
FREG = [
    ('f0', 'ft0'), ('f1', 'ft1'), ('f2', 'ft2'), ('f3', 'ft3'), ('f4', 'ft4'),
    ('f5', 'ft5'), ('f6', 'ft6'), ('f7', 'ft7'), ('f8', 'fs0'), ('f9', 'fs1'),
    ('f10', 'fa0'), ('f11', 'fa1'), ('f12', 'fa2'), ('f13', 'fa3'), ('f14', 'fa4'),
    ('f15', 'fa5'), ('f16', 'fa6'), ('f17', 'fa7'), ('f18', 'fs2'), ('f19', 'fs3'),
    ('f20', 'fs4'), ('f21', 'fs5'), ('f22', 'fs6'), ('f23', 'fs7'), ('f24', 'fs8'),
    ('f25', 'fs9'), ('f26', 'fs10'), ('f27', 'fs11'), ('f28', 'ft8'), ('f29', 'ft9'),
    ('f30', 'ft10'), ('f31', 'ft11'),
]

# 有名称的 CSR（12 位编号）；也可以直接使用编号。
CSR = {
    'fflags': 0x001, 'frm': 0x002, 'fcsr': 0x003,
    'cycle': 0xC00, 'time': 0xC01, 'instret': 0xC02,
    'mvendorid': 0xF11, 'marchid': 0xF12, 'mimpid': 0xF13, 'mhartid': 0xF14,
    'mstatus': 0x300, 'misa': 0x301, 'mie': 0x304, 'mtvec': 0x305,
    'mscratch': 0x340, 'mepc': 0x341, 'mcause': 0x342, 'mtval': 0x343, 'mip': 0x344,
    'mcycle': 0xB00, 'minstret': 0xB02,
}

# 浮点舍入模式（funct3）
RM = {'rne': 0, 'rtz': 1, 'rdn': 2, 'rup': 3, 'rmm': 4, 'dyn': 7}


def _lookup(table):
    m = {}
    for i, names in enumerate(table):
        for n in names:
            m[n] = i
    return m


XREG_BY_NAME = _lookup(XREG)
FREG_BY_NAME = _lookup(FREG)


def fields_isa_text():
    """生成 [fields] 部分的正文。"""
    out = ['[fields]', '']
    out.append('reg')
    for i, names in enumerate(XREG):
        for n in names:
            out.append('%s %s' % (n, format(i, '05b')))
    out.append('')
    out.append('freg')
    for i, names in enumerate(FREG):
        for n in names:
            out.append('%s %s' % (n, format(i, '05b')))
    out.append('')
    out.append('csr')
    for n, v in CSR.items():
        out.append('%s %s' % (n, format(v, '012b')))
    out.append('')
    out.append('rm')
    for n, v in RM.items():
        out.append('%s %s' % (n, format(v, '03b')))
    out.append('')
    return '\n'.join(out)
