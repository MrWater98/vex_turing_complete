# 游戏汇编器验证程序。
# 将游戏生成的机器码与 tools/rv_encode.py 输出的 tests/encode_check.expected.txt 逐行对照。
# 每种格式至少包含一条指令，并覆盖负立即数、前向/后向分支、伪指令和实验性的 8 字节伪指令。

start:
    addi  x1, x0, 5           # I 型，正数
    addi  x2, x0, -1          # I 型，负数（验证有符号立即数）
    lui   x3, 0x12345         # U 型
    auipc x4, 1               # U 型，PC 相对地址由硬件处理
    add   x5, x1, x2          # R 型
    sub   x5, x1, x2
    slli  x6, x1, 63          # 6 位移位量
    srai  x6, x2, 1
    sraiw x7, x2, 5           # 5 位移位量，funct7
    addiw x8, x1, -3
    sraw  x9, x2, x1
    lw    x10, -8(x1)         # 加载，负偏移
    ld    x11, 0(x2)
    sd    x11, 16(x3)         # 存储
    sb    x1, -1(x2)
loop:
    beq   x1, x2, loop        # 后向分支（偏移为 0）
    bne   x1, x2, forward     # 前向分支
    bltu  x1, x2, start       # 后向分支，负偏移
    jal   x0, forward         # J 型
    jalr  x0, 0(x1)           # jalr，内存寻址语法
    jalr  x1, x2, 4           # jalr，寄存器优先语法
forward:
    mul   x12, x1, x2         # M 扩展
    mulhu x12, x1, x2
    divw  x12, x1, x2
    remu  x12, x1, x2
    amoadd.w   x13, x1, (x2)  # A 扩展
    amoswap.d.aqrl x13, x1, (x2)
    lr.w  x14, (x2)
    sc.d  x14, x1, (x2)
    csrrs x15, mstatus, x0    # Zicsr，CSR 名称
    csrrwi x0, 0x305, 3       # Zicsr，CSR 编号和立即数
    fence
    fence.i
    ecall
    ebreak
    fld   f1, 8(x2)           # F/D 扩展
    fsw   f3, -4(x4)
    fadd.d f1, f2, f3         # 省略舍入模式（dyn）
    fadd.s f1, f2, f3, rne    # 显式指定舍入模式
    fsqrt.d f4, f5
    fcvt.w.s x1, f2
    fcvt.d.s f1, f2
    fmv.x.d x3, f4
    feq.d  x1, f2, f3
    fmadd.s f1, f2, f3, f4
    # 伪指令
    nop
    mv    x1, x2
    not   x1, x2
    neg   x1, x2
    li    x1, -100
    beqz  x1, start
    bgt   x1, x2, forward
    j     start
    ret
    csrr  x1, cycle
    rdtime x2
    fmv.d f1, f2              # 同一操作数出现在两个位置（待验证项）
    fneg.s f1, f2
    # 8 字节伪指令（实验）——检查游戏如何处理超过 32 位的机器码行
    li32  x1, 0x12345678
    li32  x2, -1
    la    x3, start
    call  forward
    tail  start
