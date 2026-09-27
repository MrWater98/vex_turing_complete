# -*- coding: utf-8 -*-
"""根据指令表生成 .isa 文本。

  isa/parts/00_settings.isa、10_fields.isa、20_rv64i.isa、…、90_pseudo.isa（各扩展片段）
  isa/rv64g.isa                                                        （导入游戏的完整文件）

游戏只接受一个 ISA 文件，因此片段用于审阅和上传 Hub，实际导入时使用完整文件。
"""
import io
import os

from . import EXTENSIONS, ext_pseudo
from .fields import fields_isa_text
from .formats import isa_token, render_isa, syntax_line

SETTINGS = '''[settings]
name = "RV64G"
variant = "single-cycle, Turing Complete sandbox"
endianness = little
line_comments = ["#", ";", "//"]
block_comments = {"/*":"*/"}
'''


def render_pseudo(p):
    lines = [syntax_line(p.mnemonic, p.operands)]
    for name, expr, _ in p.virtuals:
        lines.append('%%%s = %s' % (name, expr))
    for expr, _, msg in p.asserts:
        if expr is None:              # 立即数类型会执行范围检查
            continue
        lines.append('assert(%s, "%s: %s")' % (expr, p.mnemonic, msg))
    lines.append(' '.join(isa_token(t) for t in p.mc))
    lines.append('# [%s] %s' % (p.ext, p.desc or p.mnemonic))
    return '\n'.join(lines)


def parts():
    """按顺序返回 [(文件名，内容)]。"""
    out = [('00_settings.isa', SETTINGS), ('10_fields.isa', fields_isa_text() + '\n')]
    for prefix, ext_name, instrs in EXTENSIONS:
        blocks = [render_isa(i) for i in instrs]
        out.append((prefix + '.isa', '\n\n'.join(blocks) + '\n'))
    blocks = [render_pseudo(p) for p in ext_pseudo.PSEUDO]
    out.append(('90_pseudo.isa', '\n\n'.join(blocks) + '\n'))
    blocks = [render_pseudo(p) for p in ext_pseudo.PSEUDO_EXPERIMENTAL]
    out.append(('95_pseudo_experimental.isa', '\n\n'.join(blocks) + '\n'))
    return out


def full_text(include_experimental=True):
    ps = parts()
    body = [ps[0][1], ps[1][1], '[instructions]', '']
    for name, text in ps[2:]:
        if name.startswith('95_') and not include_experimental:
            continue
        body.append(text)
    return '\n'.join(body)


def write_all(isa_dir):
    parts_dir = os.path.join(isa_dir, 'parts')
    os.makedirs(parts_dir, exist_ok=True)
    written = []
    for name, text in parts():
        p = os.path.join(parts_dir, name)
        with io.open(p, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)
        written.append(p)
    full = os.path.join(isa_dir, 'rv64g.isa')
    with io.open(full, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(full_text(True))
    written.append(full)
    stable = os.path.join(isa_dir, 'rv64g_no_experimental.isa')
    with io.open(stable, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(full_text(False))
    written.append(stable)
    return written
