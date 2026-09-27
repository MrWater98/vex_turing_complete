# -*- coding: utf-8 -*-
"""各元件类型的引脚位置（以旋转 0 为基准，坐标相对于元件位置；y 轴向下为正）。

来源：Hub 架构 “RISC-V”（id 130）中的 RV32I_ALU 元件、Overture 战役关卡答案电路，以及游戏可执行文件中的 Verilog 接口（module TC_*）。sure 字段标记置信度：
  sure=True  ：沿实际连线追踪确认
  sure=False ：根据统计或推断得出，需在游戏中验证
引脚名称沿用 Verilog 接口中的名称。

rows：元件占用的行范围（含引脚；布局时不得重叠）。cols：列范围。
body：导线不可经过的元件本体边界 (c0, c1, r0, r1)。默认范围是左侧输入引脚和右侧输出引脚之间。
"""

PINS = {}


def _reg(kind, inputs, outputs, rows, cols, sure=True, note='', body=None):
    if body is None:
        left = [x for (x, y) in dict(inputs).values() if x < 0]
        right = [x for (x, y) in dict(outputs).values() if x > 0]
        c0 = max(left) + 1 if left else cols[0]
        c1 = min(right) - 1 if right else cols[1]
        body = (c0, c1, rows[0], rows[1])
    PINS[kind] = {'in': dict(inputs), 'out': dict(outputs), 'rows': rows, 'cols': cols, 'body': body,
                  'sure': sure, 'note': note}


# 双输入门（bit/word 的引脚布局相同）：in0 (-1,-1)、in1 (-1,1)、out (2,0)
for k in ('and_bit', 'or_bit', 'xor_bit', 'nand_bit', 'nor_bit', 'xnor_bit',
          'and_word', 'or_word', 'xor_word', 'nand_word', 'nor_word', 'xnor_word',
          'equal', 'less_u', 'less_s', 'mul', 'div', 'mod'):
    _reg(k, [('in0', (-1, -1)), ('in1', (-1, 1))], [('out', (2, 0))], (-1, 1), (-1, 2))

# 三输入门
for k in ('and_3_bit', 'or_3_bit'):
    _reg(k, [('in0', (-1, -1)), ('in1', (-1, 0)), ('in2', (-1, 1))], [('out', (2, 0))], (-1, 1), (-1, 2))

# 单输入元件
for k in ('not_bit', 'not_word', 'neg', 'inc', 'clz', 'ctz'):
    _reg(k, [('in', (-1, 0))], [('out', (2, 0))], (-1, 1), (-1, 2))

# 移位元件：in (-1,-1)、amount (-1,1)、out (2,0)
for k in ('lsl', 'lsr', 'asr', 'rol', 'ror'):
    _reg(k, [('in', (-1, -1)), ('amount', (-1, 1))], [('out', (2, 0))], (-1, 1), (-1, 2))

# 加法器：cin (0,-2)、in0 (-1,-1)、in1 (-1,1)、out (2,0)。cout 尚未确认，暂估为 (0,2)
_reg('add', [('cin', (0, -2)), ('in0', (-1, -1)), ('in1', (-1, 1))], [('out', (2, 0)), ('cout', (0, 2))], (-2, 2), (-1, 2),
     note='cout 位置为估算值')

# mux：select (-1,-1)、in0 (-1,0)、in1 (-1,1)、out (2,0)。select=1 时选择 in1
_reg('mux', [('select', (-1, -1)), ('in0', (-1, 0)), ('in1', (-1, 1))], [('out', (2, 0))], (-1, 1), (-1, 2))

# 开关：in (-1,0)、enable (0,1)、out (2,0)
for k in ('switch_bit', 'switch_word'):
    _reg(k, [('in', (-1, 0)), ('enable', (0, 1))], [('out', (2, 0))], (-1, 1), (-1, 2))

# 寄存器：save (-3,-1)、save_value (-3,0)、out (3,0)
_reg('register_word', [('save', (-3, -1)), ('save_value', (-3, 0))], [('out', (3, 0))], (-2, 2), (-3, 3))
_reg('register_bit', [('save', (-3, -1)), ('in', (-3, 0))], [('out', (3, 0))], (-2, 2), (-3, 3), sure=False)
_reg('counter', [('overwrite', (-3, -1)), ('overwrite_value', (-3, 0))], [('out', (3, 0))], (-2, 2), (-3, 3))

# 常量、On/Off 元件
_reg('on', [], [('out', (1, 0))], (-1, 1), (-2, 1))
_reg('off', [], [('out', (1, 0))], (-1, 1), (-2, 1))
_reg('constant', [], [('out', (3, 0))], (-2, 2), (-4, 3), sure=False, note='输出引脚位置为估算值')

# 静态索引器：in (-2,0)、out (2,0)。settings[0] = 移位量（正数表示右移），word_size = 输出宽度
_reg('static_indexer', [('in', (-2, 0))], [('out', (2, 0))], (-1, 1), (-3, 3), sure=False, note='输入引脚可能位于 -2 或 -3')

# 3 位译码器：dis (0,-4)、sel (-1,-2)、out0..7 = (1,-3)..(1,4)
_reg('decoder_3', [('dis', (0, -4)), ('sel', (-1, -2))], [('out%d' % k, (1, k - 3)) for k in range(8)], (-5, 5), (-2, 2))
_reg('decoder_2', [('sel', (-1, -1))], [('out%d' % k, (1, k - 1)) for k in range(4)], (-3, 3), (-2, 2), sure=False)
_reg('decoder_1', [('select', (-1, 0))], [('out0', (1, 0)), ('out1', (1, 1))], (-2, 2), (-2, 2), sure=False)

# 8 位拆分/组合元件：in (-1,0)、out0..7 = (1,-3)..(1,4)；或 in0..7 = (-1,-3)..(-1,4)、out (1,0)
_reg('splitter_bit_8', [('in', (-1, 0))], [('out%d' % k, (1, k - 3)) for k in range(8)], (-5, 5), (-1, 1))
_reg('maker_bit_8', [('in%d' % k, (-1, k - 3)) for k in range(8)], [('out', (1, 0))], (-5, 5), (-1, 1), sure=False)
_reg('splitter_bit_4', [('in', (-1, 0))], [('out%d' % k, (1, k - 1)) for k in range(4)], (-3, 3), (-1, 1), sure=False)
_reg('maker_bit_4', [('in%d' % k, (-1, k - 1)) for k in range(4)], [('out', (1, 0))], (-3, 3), (-1, 1), sure=False)
_reg('splitter_bit_2', [('in', (-1, 0))], [('out0', (1, -1)), ('out1', (1, 0))], (-2, 2), (-1, 1), sure=False)
_reg('maker_bit_2', [('in0', (-1, -1)), ('in1', (-1, 0))], [('out', (1, 0))], (-2, 2), (-1, 1), sure=False)

# word 拆分/组合元件
_reg('splitter_word_2', [('in', (-1, 0))], [('out0', (1, -1)), ('out1', (1, 0))], (-2, 2), (-1, 1))
_reg('maker_word_2', [('in0', (-1, -1)), ('in1', (-1, 0))], [('out', (1, 0))], (-2, 2), (-1, 1))
_reg('splitter_word_4', [('in', (-1, 0))], [('out%d' % k, (1, k - 1)) for k in range(4)], (-3, 3), (-1, 1), sure=False)
_reg('maker_word_4', [('in%d' % k, (-1, k - 1)) for k in range(4)], [('out', (1, 0))], (-3, 3), (-1, 1), sure=False)
_reg('splitter_word_8', [('in', (-1, 0))], [('out%d' % k, (1, k - 3)) for k in range(8)], (-5, 5), (-1, 1), sure=False)
_reg('maker_word_8', [('in%d' % k, (-1, k - 3)) for k in range(8)], [('out', (1, 0))], (-5, 5), (-1, 1), sure=False)
_reg('concatenator_2', [('in0', (-1, -1)), ('in1', (-1, 0))], [('out', (1, 0))], (-2, 2), (-1, 1), sure=False)

# 自定义元件内部的输入/输出引脚
_reg('cc_input', [], [('out', (3, 0))], (-4, 4), (-4, 4))
_reg('cc_output', [('in', (-3, 0))], [], (-4, 4), (-4, 4))

# 架构关卡的输入/输出（Level input/output 的 switched 变体）：目前只确认了数值引脚
_reg('level_input_switched', [], [('out', (3, 0))], (-3, 3), (-4, 4), sure=False, note='enable 引脚尚未确认')
_reg('level_output_switched', [('in', (-3, 0))], [], (-3, 3), (-4, 4), sure=False, note='enable 引脚尚未确认')

# RAM 及其端口。端口与 RAM 的 x 坐标相同，纵向堆叠在 RAM 上方。
# load_port: enable (-15,-1) address (-15,0) out (16,-1)   store_port: enable (-15,-1) address (-15,0) data (-15,1)
_reg('ram', [], [], (-9, 9), (-15, 15), note='无引脚；尺寸 31×19（sprite）')
_reg('load_port', [('enable', (-15, -1)), ('address', (-15, 0))], [('out', (16, -1))], (-1, 0), (-17, 17))
_reg('store_port', [('enable', (-15, -1)), ('address', (-15, 0)), ('data', (-15, 1))], [], (-1, 1), (-17, 17))

_reg('halt', [('in', (-1, 0))], [], (-1, 1), (-2, 1), sure=False)


def pin(kind, name):
    p = PINS[kind]
    if name in p['in']:
        return p['in'][name], 'in'
    if name in p['out']:
        return p['out'][name], 'out'
    raise KeyError('%s has no pin %r (in=%s out=%s)' % (kind, name, list(p['in']), list(p['out'])))
