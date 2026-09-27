# 10-amo — A 扩展

## 目的

实现 lr.w/d、sc.w/d，以及 .w/.d 形式的 amoswap/add/xor/and/or/min/max/minu/maxu。单核设计忽略 aq/rl 顺序约束。

## 引脚

| 名称 | 宽度 | 方向 | 说明 |
|---|---:|---|---|
| `addr` | 64 | 输入 | rs1 的值，不加立即数 |
| `rs2_val` | 64 | 输入 | rs2 的值 |
| `funct5` | 5 | 输入 | instr[31:27] |
| `funct3` | 3 | 输入 | 010=W，011=D |
| `is_amo`、`clk_en` | 1 | 输入 | AMO 指令及时钟使能 |
| `old` | 64 | 输出 | 写入 rd 的值；sc 返回 0/1 |
| `mem_read`、`mem_write`、`mem_wdata`、`mem_funct3` | — | 输出 | 发往 07-lsu 的请求 |

## 行为（单 tick 内完成读、计算、写）

```text
old  = LSU 读取结果（宽度由 funct3 决定；W 型符号扩展）
new  = 根据 funct5 选择：
       00001 swap：rs2
       00000 add： old + rs2
       00100 xor： old ^ rs2
       01100 and： old & rs2
       01000 or：  old | rs2
       10000 min： Less_s(old, rs2) ? old : rs2
       10100 max： Less_s(old, rs2) ? rs2 : old
       11000 minu / 11100 maxu：用 Less_u 实现对应选择
       00010 lr：不写内存，reservation = 1，reserved_addr = addr
       00011 sc：若 reservation & (reserved_addr == addr)，写入 rs2 且 old = 0；否则 old = 1。随后 reservation = 0
mem_write = is_amo & clk_en & (非 lr) & (若为 sc 则仅在成功时为 1)
```

W 型只写低 32 位（复用 LSU 的 sw 路径），`old` 符号扩展到 64 位。

前提是游戏 RAM 支持同 tick 读和写（B3）。若不支持，则拆成两个 tick（读 tick、写 tick），期间保持 `clk_en`。

## 在游戏中构建

1. 放置 `Add/Xor/And/Or(64)`、`Less_s/Less_u(64)` 和 mux 树（按 funct5 高位译码）。
2. 放置 `Register(1)` 保存 reservation、`Register(64)` 保存 reserved_addr，以及 `Equal(64)`。
3. 保存到 Foundry 的 `RV64G/AMO`。

## 验证

- 地址 0 初值为 5。执行 `amoadd.d x1, x2, (x0)`（x2=3），应有 x1=5、内存值 8。
- 执行 `lr.d x1, (x0)` 得到 8；执行 `sc.d x3, x4, (x0)`（x4=9）应得 x3=0、内存值 9；再次执行 sc.d 应得 x3=1。
- 用 `amomax.w` 比较 -1 和 1，结果为 1；用 `amomaxu.w` 则结果为 0xFFFF_FFFF。

## 状态

目前仅有设计文档。
