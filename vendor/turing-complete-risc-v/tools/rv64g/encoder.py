# -*- coding: utf-8 -*-
"""参考汇编器（编码器）。

它使用同一份指令表独立于游戏汇编器生成机器码，用于对照验证导入游戏的 ISA 是否正确。功能范围刻意保持精简：
  - 标签（`name:`）、注释（# ; //）和空行
  - 全部基本指令及 ext_pseudo 中的伪指令（展开为基本指令）
  - 立即数：十进制、十六进制（0x）、二进制（0b）和负数
  - 内存操作数：imm(reg)、(reg)
  - 分支/跳转目标：标签或绝对地址（数字）
不支持伪操作（例如 .word）。
"""
import re
from dataclasses import dataclass

from . import BASE_BY_NAME, PSEUDO_BY_NAME
from .fields import XREG_BY_NAME, FREG_BY_NAME, CSR, RM
from .formats import definitions, encode_tokens

COMMENT_RE = re.compile(r'(#|;|//).*$')
LABEL_RE = re.compile(r'^\s*([A-Za-z_.$][\w.$]*)\s*:\s*(.*)$')
MEM_RE = re.compile(r'^\s*([^()\s]*)\s*\(\s*([^()\s]+)\s*\)\s*$')


class AsmError(Exception):
    pass


@dataclass
class Line:
    addr: int
    source: str
    expanded: list      # 展开后的基本指令字符串
    words: list         # 32 位整数


def parse_int(text):
    t = text.strip().replace('_', '')
    neg = t.startswith('-')
    if neg or t.startswith('+'):
        t = t[1:]
    if t.lower().startswith('0x'):
        v = int(t, 16)
    elif t.lower().startswith('0b'):
        v = int(t, 2)
    elif t.isdigit():
        v = int(t, 10)
    else:
        raise AsmError('bad number: %r' % text)
    return -v if neg else v


def split_operands(text):
    """按逗号拆分，同时保留括号内的逗号。"""
    out, depth, cur = [], 0, ''
    for ch in text:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur.strip())
            cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


class Context:
    def __init__(self, labels, pc):
        self.labels, self.pc = labels, pc

    def target(self, text):
        t = text.strip()
        if t in self.labels:
            return self.labels[t]
        return parse_int(t)

    def imm(self, text):
        return parse_int(text)


def _reg(text, table, what):
    t = text.strip()
    if t not in table:
        raise AsmError('unknown %s register: %r' % (what, text))
    return table[t]


def _slots(operands):
    """将定义中的操作数类别列表分组为文本操作数槽：[(kinds…)]。"""
    slots = []
    for name, kind in operands:
        if kind == 'mem':
            slots[-1] = slots[-1] + [(name, kind)]
        elif kind == 'mem0':
            slots.append([(name, kind)])
        else:
            slots.append([(name, kind)])
    return slots


def _values_for(operands, texts, ctx):
    slots = _slots(operands)
    if len(slots) != len(texts):
        return None
    values = {}
    for slot, text in zip(slots, texts):
        if len(slot) == 2:                       # imm(reg)
            (iname, _), (aname, _) = slot
            m = MEM_RE.match(text)
            if not m:
                raise AsmError('expected imm(reg): %r' % text)
            values[iname] = parse_int(m.group(1)) if m.group(1) else 0
            values[aname] = _reg(m.group(2), XREG_BY_NAME, 'integer')
            continue
        name, kind = slot[0]
        if kind == 'mem0':
            m = MEM_RE.match(text)
            if not m or m.group(1):
                raise AsmError('expected (reg): %r' % text)
            values[name] = _reg(m.group(2), XREG_BY_NAME, 'integer')
        elif kind == 'reg':
            values[name] = _reg(text, XREG_BY_NAME, 'integer')
        elif kind == 'freg':
            values[name] = _reg(text, FREG_BY_NAME, 'float')
        elif kind in ('imm', 'imm20', 'imm32', 'sh6', 'sh5', 'zimm'):
            values[name] = parse_int(text)
        elif kind == 'csr':
            values[name] = CSR[text.strip()] if text.strip() in CSR else parse_int(text)
        elif kind == 'rm':
            if text.strip() not in RM:
                raise AsmError('unknown rounding mode: %r' % text)
            values[name] = RM[text.strip()]
        elif kind == 'target':
            values[name] = ctx.target(text)
        else:
            raise AsmError('unhandled operand kind %s' % kind)
    return values


def encode_base(mnemonic, texts, ctx):
    """将一条基本指令编码为 32 位整数。"""
    if mnemonic not in BASE_BY_NAME:
        raise AsmError('unknown instruction: %s' % mnemonic)
    last_err = None
    for instr in BASE_BY_NAME[mnemonic]:
        for operands, virtuals, asserts, mc in definitions(instr):
            try:
                values = _values_for(operands, texts, ctx)
            except AsmError as e:
                last_err = e
                continue
            if values is None:
                continue
            for name, _, fn in virtuals:
                values[name] = fn(values, ctx.pc)
            for _, fn, msg in asserts:
                if not fn(values):
                    raise AsmError('%s: %s' % (mnemonic, msg))
            word, nbits = encode_tokens(mc, values)
            assert nbits == 32
            return word
    raise AsmError('%s: no matching operand form for %r%s' % (mnemonic, texts, ' (%s)' % last_err if last_err else ''))


def _pseudo_size(mnemonic, texts):
    for p in PSEUDO_BY_NAME.get(mnemonic, []):
        if len(_slots(p.operands)) == len(texts):
            return p
    return None


def _is_base(mnemonic, texts):
    """若某个基本指令定义的文本操作数数量匹配，则返回 True。"""
    for instr in BASE_BY_NAME.get(mnemonic, []):
        for operands, _, _, _ in definitions(instr):
            if len(_slots(operands)) == len(texts):
                return True
    return False


def _split_line(text):
    text = COMMENT_RE.sub('', text).strip()
    if not text:
        return None, None
    parts = text.split(None, 1)
    mnemonic = parts[0].lower()
    texts = split_operands(parts[1]) if len(parts) > 1 else []
    return mnemonic, texts


def assemble(source, origin=0):
    """将完整源代码转换为 [Line]。扫描两遍：先解析标签地址，再编码。"""
    items = []          # (标签或 None，助记符，操作数文本，源代码行)
    for raw in source.splitlines():
        line = COMMENT_RE.sub('', raw).rstrip()
        if not line.strip():
            continue
        m = LABEL_RE.match(line)
        label = None
        if m and not m.group(1).lower() in BASE_BY_NAME and m.group(1).lower() not in PSEUDO_BY_NAME:
            label, line = m.group(1), m.group(2)
        mnemonic, texts = _split_line(line) if line.strip() else (None, None)
        items.append((label, mnemonic, texts, raw.strip()))

    labels, pc = {}, origin
    for label, mnemonic, texts, _ in items:
        if label:
            labels[label] = pc
        if mnemonic is None:
            continue
        if _is_base(mnemonic, texts):
            pc += 4
        else:
            p = _pseudo_size(mnemonic, texts)
            if p is None:
                raise AsmError('unknown instruction: %s' % mnemonic)
            pc += 4 * p.size

    out, pc = [], origin
    for label, mnemonic, texts, src in items:
        if mnemonic is None:
            continue
        ctx = Context(labels, pc)
        if _is_base(mnemonic, texts):
            expanded = [src]
            words = [encode_base(mnemonic, texts, ctx)]
        else:
            p = _pseudo_size(mnemonic, texts)
            names = [n for slot in _slots(p.operands) for n, _ in slot[:1]]
            ops = dict(zip(names, texts))
            expanded = p.expand(ops, ctx)
            words = []
            for k, e in enumerate(expanded):
                em, et = _split_line(e)
                words.append(encode_base(em, et, Context(labels, pc + 4 * k)))
        out.append(Line(pc, src, expanded, words))
        pc += 4 * len(words)
    return out


def listing(lines):
    """生成对照列表：地址、小端字节、指令字和源代码。"""
    rows = []
    for ln in lines:
        for k, w in enumerate(ln.words):
            b = w.to_bytes(4, 'little')
            src = ln.source if k == 0 else '  -> ' + ln.expanded[k]
            rows.append('%08x  %s  %08x  %s' % (ln.addr + 4 * k, ' '.join('%02x' % x for x in b), w, src))
    return '\n'.join(rows)
