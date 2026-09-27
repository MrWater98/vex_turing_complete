# -*- coding: utf-8 -*-
"""使用参考编码器将汇编文件转换为机器码，并输出对照表。

    python tools/rv_encode.py tests/encode_check.asm            # 输出到标准输出
    python tools/rv_encode.py tests/encode_check.asm -o out.txt # 输出到文件
    python tools/rv_encode.py tests/encode_check.asm --origin 0x1000

输出格式：地址、小端序的 4 个字节、32 位指令字、源代码。
可将字节序列与游戏的机器码视图（或程序 RAM 内容）对照。
"""
import argparse
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rv64g.encoder import assemble, listing, AsmError      # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('asm')
    ap.add_argument('-o', '--output')
    ap.add_argument('--origin', default='0')
    args = ap.parse_args()
    src = io.open(args.asm, encoding='utf-8').read()
    try:
        lines = assemble(src, origin=int(args.origin, 0))
    except AsmError as e:
        print('error:', e)
        return 1
    text = listing(lines)
    if args.output:
        with io.open(args.output, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text + '\n')
        print('wrote', args.output, '(%d words)' % sum(len(l.words) for l in lines))
    else:
        print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
