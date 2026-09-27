# -*- coding: utf-8 -*-
"""对指令表、编码器和 ISA 生成器执行自检。

    python tools/selftest.py

1. 对照手工验证过的编码向量与参考编码器结果
2. 检查伪指令的 ISA 机器码 token 路径与基本指令展开路径一致
3. 检查每条指令的 .isa 块生成 32 位或 64 位机器码行
4. 检查助记符和语法定义是否重复
5. 检查所有立即数操作数均带宽度类型（如 :S12），这是游戏汇编器的要求
6. 检查机器码行的切片均使用 [hi:lo] 形式；游戏不接受 [n]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rv64g import EXTENSIONS, BASE_INSTRUCTIONS, ext_pseudo         # noqa: E402
from rv64g.encoder import assemble, encode_base, Context, AsmError  # noqa: E402
from rv64g.formats import definitions, encode_tokens, syntax_line   # noqa: E402
from rv64g.isa_writer import full_text                              # noqa: E402

# （源指令，预期指令字）。根据 RISC-V 非特权规范的编码表手工计算。
VECTORS = [
    ('addi x1, x0, 5',        0x00500093),
    ('lui x1, 0x12345',       0x123450B7),
    ('lui x1, 0xFFFFF',       0xFFFFF0B7),
    ('auipc x2, 1',           0x00001117),
    ('jal x0, 8',             0x0080006F),   # pc = 0, +8
    ('jalr x1, 4(x2)',        0x004100E7),
    ('jalr x1, x2, 4',        0x004100E7),
    ('sd x2, 16(x3)',         0x0021B823),
    ('lw x5, -8(x6)',         0xFF832283),
    ('lbu x7, 0(x8)',         0x00044383),
    ('mul x1, x2, x3',        0x023100B3),
    ('sub x1, x2, x3',        0x403100B3),
    ('slli x1, x2, 63',       0x03F11093),
    ('srai x1, x2, 1',        0x40115093),
    ('sraiw x1, x2, 5',       0x4051509B),
    ('addiw x3, x4, -1',      0xFFF2019B),
    ('sraw x1, x2, x3',       0x403150BB),
    ('fadd.d f1, f2, f3',     0x023170D3),
    ('fadd.s f1, f2, f3, rne', 0x003100D3),
    ('fsqrt.d f4, f5',        0x5A02F253),
    ('fcvt.w.s x1, f2',       0xC00170D3),
    ('fcvt.d.s f1, f2',       0x420170D3),
    ('fmv.x.d x3, f4',        0xE20201D3),
    ('feq.d x1, f2, f3',      0xA23120D3),
    ('fmadd.s f1, f2, f3, f4', 0x203170C3),
    ('fld f1, 8(x2)',         0x00813087),
    ('fsw f3, -4(x4)',        0xFE322E27),
    ('amoadd.w x1, x2, (x3)', 0x0021A0AF),
    ('lr.d.aq x5, (x6)',      0x140332AF),
    ('sc.w.rl x1, x2, (x3)', 0x1A21A0AF),
    ('csrrs x1, mstatus, x0', 0x300020F3),
    ('csrrwi x0, 0x305, 3',   0x3051D073),
    ('ecall',                 0x00000073),
    ('ebreak',                0x00100073),
    ('fence',                 0x0FF0000F),
    ('fence.i',               0x0000100F),
]

# 用于检查伪指令的示例操作数值
SAMPLE = {'d': 5, 'a': 6, 'b': 7, 'i': -3, 'z': 9, 'n': 0x300, 't': 0x40}


def check_vectors():
    bad = 0
    for src, want in VECTORS:
        lines = assemble(src)
        got = lines[0].words[0]
        if got != want:
            print('  FAIL %-28s got %08x want %08x' % (src, got, want))
            bad += 1
    print('vectors: %d checked, %d failed' % (len(VECTORS), bad))
    return bad == 0


def check_pseudo():
    bad = 0
    for p in ext_pseudo.ALL:
        names = [n for n, _ in p.operands]
        vals = {n: SAMPLE[n] for n in names}
        pc = 0
        for name, _, fn in p.virtuals:
            vals[name] = fn(vals, pc)
        for _, fn, msg in p.asserts:
            assert fn(vals), (p.mnemonic, msg)
        word_isa, nbits = encode_tokens(p.mc, vals)
        assert nbits == 32 * p.size, (p.mnemonic, nbits)
        # 指令展开路径
        texts = {}
        for n, kind in p.operands:
            v = vals[n]
            if kind == 'reg':
                texts[n] = 'x%d' % v
            elif kind == 'freg':
                texts[n] = 'f%d' % v
            elif kind == 'target':
                texts[n] = str(v)
            elif kind == 'csr':
                texts[n] = str(v)
            else:
                texts[n] = str(v)
        ctx = Context({}, pc)
        expanded = p.expand(texts, ctx)
        words = []
        for k, e in enumerate(expanded):
            m, t = e.split(None, 1) if ' ' in e else (e, '')
            from rv64g.encoder import split_operands
            words.append(encode_base(m.lower(), split_operands(t), Context({}, pc + 4 * k)))
        word_exp = 0
        for w in words:
            word_exp = (word_exp << 32) | w
        if word_isa != word_exp:
            print('  FAIL pseudo %-10s isa %0*x expand %0*x  (%s)' % (p.mnemonic, 8 * p.size, word_isa, 8 * p.size, word_exp, ' ; '.join(expanded)))
            bad += 1
    print('pseudo: %d checked, %d failed' % (len(ext_pseudo.ALL), bad))
    return bad == 0


def check_isa_blocks():
    bad = 0
    seen = set()
    for instr in BASE_INSTRUCTIONS:
        for operands, _, _, mc in definitions(instr):
            total = 0
            for tok in mc:
                if tok[0] in '01':
                    total += len(tok)
                else:
                    rng = tok[tok.index('[') + 1:-1]
                    hi, lo = rng.split(':') if ':' in rng else (rng, rng)
                    total += int(hi) - int(lo) + 1
            if total != 32:
                print('  FAIL %s: machine code is %d bits' % (instr.mnemonic, total))
                bad += 1
            key = syntax_line(instr.mnemonic, operands)
            if key in seen:
                print('  DUP syntax: %s' % key)
                bad += 1
            seen.add(key)
    for p in ext_pseudo.ALL:
        key = syntax_line(p.mnemonic, p.operands)
        if key in seen:
            print('  DUP syntax (pseudo vs base): %s' % key)
            bad += 1
        seen.add(key)
    text = full_text(True)
    print('isa blocks: %d base instructions, %d syntax forms, %d failed; full file %d lines'
          % (len(BASE_INSTRUCTIONS), len(seen), bad, text.count('\n')))
    return bad == 0


def check_typed_immediates():
    """游戏要求立即数操作数带宽度类型；在完整 ISA 文本中查找缺少类型的立即数。"""
    text = full_text(True)
    bad = 0
    types = {}
    for line in text.split('\n'):
        if line.startswith('#') or line.startswith('assert('):
            continue
        pos = 0
        while True:
            k = line.find('(', pos)
            if k < 0:
                break
            close = line.find(')', k)
            inner = line[k + 1:close] if close > k else ''
            pos = k + 1
            if 'immediate' not in inner:
                continue
            head = line[:k]
            colon, pct = head.rfind(':'), head.rfind('%')
            t = head[colon + 1:] if colon > pct else ''
            if t[:1] in ('U', 'S') and t[1:].isdigit():
                types[t] = types.get(t, 0) + 1
            else:
                print('  FAIL untyped immediate: %s' % line)
                bad += 1
    print('typed immediates: %s; %d failed' % (' '.join('%s=%d' % kv for kv in sorted(types.items())), bad))
    return bad == 0


def check_slices():
    """游戏解析器不接受 %x[n]；检查完整 ISA 文本中的切片是否都包含冒号。"""
    text = full_text(True)
    bad = 0
    for line in text.split('\n'):
        pos = 0
        while True:
            k = line.find('[', pos)
            if k < 0:
                break
            close = line.find(']', k)
            inner = line[k + 1:close] if close > k else ''
            pos = k + 1
            if inner.isdigit():
                print('  FAIL single-index slice: %s' % line)
                bad += 1
    print('slices: %d failed' % bad)
    return bad == 0


def check_program():
    src = '''
start:
    addi x1, x0, 1
    beqz x1, start
    j end
    nop
end:
    ret
'''
    lines = assemble(src)
    words = [w for l in lines for w in l.words]
    want = [0x00100093, 0xFE008EE3, 0x0080006F, 0x00000013, 0x00008067]
    ok = words == want
    print('program: %s' % ('ok' if ok else 'FAIL %s' % ['%08x' % w for w in words]))
    return ok


def main():
    ok = True
    for fn in (check_vectors, check_pseudo, check_isa_blocks, check_typed_immediates, check_slices, check_program):
        try:
            ok = fn() and ok
        except (AsmError, AssertionError) as e:
            print('  ERROR in %s: %r' % (fn.__name__, e))
            ok = False
    print('SELFTEST', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
