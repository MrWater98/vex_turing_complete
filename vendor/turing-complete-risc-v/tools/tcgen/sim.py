# -*- coding: utf-8 -*-
"""网表模拟器（组合逻辑，通过迭代求固定点），尽量匹配游戏元件语义。

值用整数表示，位宽由 word_size 指定。开关总线对已启用开关的值执行 OR；若没有启用项，结果为 0。
"""
from .pins import PINS


def mask(v, w):
    return v & ((1 << w) - 1)


def sext(v, w):
    v = mask(v, w)
    return v - (1 << w) if v >> (w - 1) else v


class Sim:
    def __init__(self, design):
        self.d = design
        self.pin_net = {}
        for n in design.nets:
            for c, p in n.drivers + n.sinks:
                self.pin_net[(c.name, p)] = n.name

    def inputs_of(self, c, values):
        """返回元件输入引脚值字典；未连接的引脚值为 0。"""
        out = {}
        for p in PINS[c.kind]['in']:
            nn = self.pin_net.get((c.name, p))
            out[p] = values.get(nn, 0) if nn else 0
        return out

    def eval_comp(self, c, i, ext_inputs):
        k, w = c.kind, c.word_size
        if k == 'cc_input':
            return {'out': mask(ext_inputs.get(c.name, 0), w)}
        if k in ('on',):
            return {'out': 1}
        if k in ('off',):
            return {'out': 0}
        if k == 'constant':
            return {'out': mask(c.settings[0] if c.settings else 0, w)}
        if k in ('and_bit', 'and_word'):
            return {'out': i['in0'] & i['in1']}
        if k in ('or_bit', 'or_word'):
            return {'out': i['in0'] | i['in1']}
        if k in ('xor_bit', 'xor_word'):
            return {'out': i['in0'] ^ i['in1']}
        if k in ('nand_bit', 'nand_word'):
            return {'out': mask(~(i['in0'] & i['in1']), w)}
        if k in ('nor_bit', 'nor_word'):
            return {'out': mask(~(i['in0'] | i['in1']), w)}
        if k in ('xnor_bit', 'xnor_word'):
            return {'out': mask(~(i['in0'] ^ i['in1']), w)}
        if k in ('and_3_bit',):
            return {'out': i['in0'] & i['in1'] & i['in2']}
        if k in ('or_3_bit',):
            return {'out': i['in0'] | i['in1'] | i['in2']}
        if k in ('not_bit', 'not_word'):
            return {'out': mask(~i['in'], w)}
        if k == 'neg':
            return {'out': mask(-i['in'], w)}
        if k == 'inc':
            return {'out': mask(i['in'] + 1, w)}
        if k == 'add':
            s = i['in0'] + i['in1'] + (i['cin'] & 1)
            return {'out': mask(s, w), 'cout': (s >> w) & 1}
        if k == 'mul':
            return {'out': mask(i['in0'] * i['in1'], w)}
        if k == 'equal':
            return {'out': int(i['in0'] == i['in1'])}
        if k == 'less_u':
            return {'out': int(i['in0'] < i['in1'])}
        if k == 'less_s':
            return {'out': int(sext(i['in0'], w) < sext(i['in1'], w))}
        if k == 'lsl':
            return {'out': mask(i['in'] << i['amount'], w) if i['amount'] < w else 0}
        if k == 'lsr':
            return {'out': (i['in'] >> i['amount']) if i['amount'] < w else 0}
        if k == 'asr':
            a = min(i['amount'], w - 1)
            return {'out': mask(sext(i['in'], w) >> a, w)}
        if k == 'mux':
            return {'out': i['in1'] if i['select'] & 1 else i['in0']}
        if k in ('switch_bit', 'switch_word'):
            return {'out': i['in'] if i['enable'] & 1 else None}      # None 表示未启用（高阻 Z）
        if k == 'decoder_3':
            sel = i['sel'] & 7
            return {'out%d' % j: int(j == sel and not (i['dis'] & 1)) for j in range(8)}
        if k == 'decoder_2':
            sel = i['sel'] & 3
            return {'out%d' % j: int(j == sel) for j in range(4)}
        if k == 'splitter_bit_8':
            return {'out%d' % j: (i['in'] >> j) & 1 for j in range(8)}
        if k == 'maker_bit_8':
            return {'out': sum((i['in%d' % j] & 1) << j for j in range(8))}
        if k == 'static_indexer':
            sh = c.settings[0] if c.settings else 0
            if sh >= 1 << 63:
                sh -= 1 << 64
            v = i['in'] >> sh if sh >= 0 else i['in'] << (-sh)
            return {'out': mask(v, w)}
        if k == 'cc_output':
            return {}
        raise NotImplementedError('sim: %s' % k)

    def run(self, ext_inputs, max_iter=100):
        values = {n.name: 0 for n in self.d.nets}
        for _ in range(max_iter):
            new = {n.name: None for n in self.d.nets}
            for c in self.d.comps:
                outs = self.eval_comp(c, self.inputs_of(c, values), ext_inputs)
                for p, v in outs.items():
                    nn = self.pin_net.get((c.name, p))
                    if nn is None or v is None:
                        continue
                    new[nn] = v if new[nn] is None else (new[nn] | v)
            new = {k: (0 if v is None else v) for k, v in new.items()}
            if new == values:
                break
            values = new
        else:
            raise RuntimeError('simulation did not settle')
        outs = {}
        for c in self.d.comps:
            if c.kind == 'cc_output':
                nn = self.pin_net.get((c.name, 'in'))
                outs[c.name] = mask(values.get(nn, 0), c.word_size)
        return outs, values
