# -*- coding: utf-8 -*-
"""将 RV64G 指令表转换为 Turing Complete 汇编器定义（.isa）和 Python 参考编码器。

扩展对应的模块：
  ext_rv64i, ext_zifencei, ext_zicsr, ext_m, ext_a, ext_f, ext_d, ext_pseudo
"""
from . import ext_rv64i, ext_zifencei, ext_zicsr, ext_m, ext_a, ext_f, ext_d, ext_pseudo

# （文件前缀、扩展名称、指令列表）；顺序也是写入 .isa 的顺序。
EXTENSIONS = [
    ('20_rv64i', 'RV64I', ext_rv64i.INSTRUCTIONS),
    ('30_zifencei', 'Zifencei', ext_zifencei.INSTRUCTIONS),
    ('31_zicsr', 'Zicsr', ext_zicsr.INSTRUCTIONS),
    ('40_m', 'M', ext_m.INSTRUCTIONS),
    ('50_a', 'A', ext_a.INSTRUCTIONS),
    ('60_f', 'F', ext_f.INSTRUCTIONS),
    ('70_d', 'D', ext_d.INSTRUCTIONS),
]

BASE_INSTRUCTIONS = [i for _, _, lst in EXTENSIONS for i in lst]

BASE_BY_NAME = {}
for _i in BASE_INSTRUCTIONS:
    BASE_BY_NAME.setdefault(_i.mnemonic, []).append(_i)

PSEUDO_BY_NAME = ext_pseudo.BY_NAME
