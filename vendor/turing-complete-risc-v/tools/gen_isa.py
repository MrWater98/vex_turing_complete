# -*- coding: utf-8 -*-
"""生成 isa/parts/*.isa 和 isa/rv64g.isa。

    python tools/gen_isa.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rv64g import EXTENSIONS, ext_pseudo            # noqa: E402
from rv64g.isa_writer import write_all              # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    written = write_all(os.path.join(ROOT, 'isa'))
    for p in written:
        print('wrote', os.path.relpath(p, ROOT))
    total = 0
    for _, name, instrs in EXTENSIONS:
        print('  %-9s %4d instructions' % (name, len(instrs)))
        total += len(instrs)
    print('  %-9s %4d pseudo (+%d experimental)' % ('pseudo', len(ext_pseudo.PSEUDO), len(ext_pseudo.PSEUDO_EXPERIMENTAL)))
    print('  total base instructions:', total)
    return 0


if __name__ == '__main__':
    sys.exit(main())
