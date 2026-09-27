# -*- coding: utf-8 -*-
"""读取 circuit.data（版本 16），并输出摘要或 JSON。

    python tools/tc_dump.py <circuit.data> [--json]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tcsave import save16  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    paths = [a for a in sys.argv[1:] if not a.startswith('--')]
    for path in paths:
        data = open(path, 'rb').read()
        s = save16.parse(data)
        again = save16.serialize(s)
        ok = save16.raw_bytes(again) == save16.raw_bytes(data)
        print('# %s: custom_id=%d %d components, %d wires, roundtrip %s'
              % (path, s.custom_id, len(s.components), len(s.wires), 'OK' if ok else 'MISMATCH'))
        if '--json' in sys.argv:
            print(json.dumps(save16.to_json(s), ensure_ascii=False, indent=1))
        else:
            for c in s.components:
                print('  %-22s pos=(%d,%d) rot=%d ws=%d settings=%s label=%r size=%d le=%s init=%s%s'
                      % (c.kind, c.position.x, c.position.y, c.rotation, c.word_size, c.settings, c.user_label,
                         c.buffer_size, c.is_little_endian, c.init_data,
                         (' custom_id=%d' % c.custom_id) if c.kind == 'custom' else ''))
            for w in s.wires:
                f = w.finish
                print('  wire (%d,%d)->(%d,%d) %s color=%d' % (w.start.x, w.start.y, f.x, f.y, w.segments, w.color))


if __name__ == '__main__':
    main()
