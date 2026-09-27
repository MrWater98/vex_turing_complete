# -*- coding: utf-8 -*-
"""生成 RV64G/ALU64 Foundry 元件；结构与 Hub 的 RV32I_ALU 相同，但数据宽度为 64 位。

    python tools/gen_alu64.py [输出目录]      默认 build/ALU64/

引脚：a(64) b(64) funct3(3) alt(1: funct7[5] = SUB/SRA) -> y(64)
funct3: 0 add/sub  1 sll  2 slt  3 sltu  4 xor  5 srl/sra  6 or  7 and
移位量直接使用 b（确认 static_indexer 引脚后再屏蔽 b[5:0]）。
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tcgen.design import Design       # noqa: E402
from tcgen.sim import Sim, mask, sext  # noqa: E402
from tcsave import save16              # noqa: E402

W = 64


def build():
    d = Design('ALU64', description='RV64I ALU: add sub sll slt sltu xor srl sra or and')
    d.add('a', 'cc_input', W, [2], 'a', ui_order=-2)
    d.add('b', 'cc_input', W, [2], 'b', ui_order=-4)
    d.add('f3', 'cc_input', 3, [2], 'funct3', ui_order=-6)
    d.add('alt', 'cc_input', 1, [2], 'alt', ui_order=-8)
    d.add('y', 'cc_output', W, [0], 'y', ui_order=-2)

    d.add('notb', 'not_word', W)
    d.add('bsel', 'mux', W)
    d.add('adder', 'add', W)
    d.add('sll', 'lsl', W)
    d.add('slt', 'less_s', W)
    d.add('sltu', 'less_u', W)
    d.add('xor', 'xor_word', W)
    d.add('srl', 'lsr', W)
    d.add('sra', 'asr', W)
    d.add('srsel', 'mux', W)
    d.add('or', 'or_word', W)
    d.add('and', 'and_word', W)
    d.add('dec', 'decoder_3', 1)
    d.add('dis', 'off', 1)
    for k in range(8):
        d.add('sw%d' % k, 'switch_word' if k not in (2, 3) else 'switch_bit', W if k not in (2, 3) else 1)

    # 分配输入
    d.connect('a', 'a.out', 'adder.in0', 'sll.in', 'slt.in0', 'sltu.in0', 'xor.in0', 'srl.in', 'sra.in', 'or.in0', 'and.in0')
    d.connect('b', 'b.out', 'notb.in', 'bsel.in0', 'sll.amount', 'slt.in1', 'sltu.in1', 'xor.in1', 'srl.amount', 'sra.amount', 'or.in1', 'and.in1')
    d.connect('alt', 'alt.out', 'bsel.select', 'adder.cin', 'srsel.select')
    d.connect('notb', 'notb.out', 'bsel.in1')
    d.connect('bmux', 'bsel.out', 'adder.in1')
    d.connect('srl_o', 'srl.out', 'srsel.in0')
    d.connect('sra_o', 'sra.out', 'srsel.in1')
    # 将运算结果接到开关
    for k, src in enumerate(['adder.out', 'sll.out', 'slt.out', 'sltu.out', 'xor.out', 'srsel.out', 'or.out', 'and.out']):
        d.connect('r%d' % k, src, 'sw%d.in' % k)
    # 译码器
    d.connect('f3', 'f3.out', 'dec.sel')
    d.connect('dis', 'dis.out', 'dec.dis')
    for k in range(8):
        d.connect('en%d' % k, 'dec.out%d' % k, 'sw%d.enable' % k)
    # 总线
    d.connect('y', *['sw%d.out' % k for k in range(8)], 'y.in')
    return d


def reference(a, b, f3, alt):
    sh = b & 63
    if f3 == 0:
        return mask(a - b if alt else a + b, W)
    if f3 == 1:
        return mask(a << sh, W)
    if f3 == 2:
        return int(sext(a, W) < sext(b, W))
    if f3 == 3:
        return int(a < b)
    if f3 == 4:
        return a ^ b
    if f3 == 5:
        return mask(sext(a, W) >> sh, W) if alt else a >> sh
    if f3 == 6:
        return a | b
    return a & b


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    out_dir = sys.argv[1] if len(sys.argv) > 1 else 'build/ALU64'
    d = build()
    save = d.build(foundry=True)
    print('components %d, wires %d, bounds %s' % (len(save.components), len(save.wires), d.bounds))
    # 模拟验证（移位量仅测试 0..63）
    sim = Sim(d)
    rng = random.Random(1)
    bad = 0
    for t in range(400):
        a = rng.getrandbits(W)
        b = rng.getrandbits(W) if t % 2 else rng.getrandbits(6)
        f3 = rng.randrange(8)
        alt = rng.randrange(2) if f3 in (0, 5) else 0
        if f3 in (1, 5):
            b &= 63
        got = sim.run({'a': a, 'b': b, 'f3': f3, 'alt': alt})[0]['y']
        want = reference(a, b, f3, alt)
        if got != want:
            bad += 1
            if bad <= 5:
                print('  MISMATCH f3=%d alt=%d a=%x b=%x got=%x want=%x' % (f3, alt, a, b, got, want))
    print('simulation: %d vectors, %d mismatches' % (400, bad))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'circuit.data')
    data = save16.serialize(save)
    with open(path, 'wb') as fh:
        fh.write(data)
    again = save16.parse(data)
    assert save16.raw_bytes(save16.serialize(again)) == save16.raw_bytes(data)
    print('wrote %s (%d bytes, custom_id %d)' % (path, len(data), save.custom_id))
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
