# 08-muldiv — M 扩展

## 目的

实现 mul、mulh、mulhsu、mulhu、div、divu、rem、remu 及 5 种 W 型指令。`is_m = (is_op|is_op32) & funct7==0000001`。

## 引脚

| 名称 | 宽度 | 方向 |
|---|---:|---|
| `a`、`b` | 64 | 输入 |
| `funct3` | 3 | 输入 |
| `is_word` | 1 | 输入 |
| `y` | 64 | 输出 |

## 运算

| funct3 | 64 位 | W 型 |
|---|---|---|
| 000 | mul（低 64 位） | mulw |
| 001 | mulh（高 64 位，s×s） | |
| 010 | mulhsu（s×u） | |
| 011 | mulhu（u×u） | |
| 100 | div | divw |
| 101 | divu | divuw |
| 110 | rem | remw |
| 111 | remu | remuw |

## 乘法

若 `Mul(64)` 只输出乘积低 64 位（B8），需用 32 位部分积计算高 64 位：

```text
al = a[31:0], ah = a[63:32], bl = b[31:0], bh = b[63:32]（全部零扩展到 64 位）
p0 = al*bl, p1 = ah*bl, p2 = al*bh, p3 = ah*bh        （各结果可容纳于 64 位）
mid = p1 + p2 + (p0 >> 32)                             （最多 66 位；两个进位需单独处理，见 B10）
mulhu = p3 + (mid >> 32) + (mid 的进位 << 32)
mulh   = mulhu(a,b) - (a<0 ? b : 0) - (b<0 ? a : 0)     （用 Less_s 判断符号，再用 Mux、Sub）
mulhsu = mulhu(a,b) - (a<0 ? b : 0)
```

若 `Add(64)` 没有进位输出，可用 `Less_u(sum, p1)` 检测进位（若和小于其中一个加数，表示溢出）。

## 除法

若游戏 `Div`/`Mod` 执行无符号运算（B9），则在外围处理符号：

```text
neg_a = a[63], neg_b = b[63]
ua = neg_a ? Neg(a) : a, ub = neg_b ? Neg(b) : b
q  = Div(64)(ua, ub), r = Mod(64)(ua, ub)
div  = (neg_a ^ neg_b) ? Neg(q) : q
rem  = neg_a ? Neg(r) : r
divu = Div(64)(a, b), remu = Mod(64)(a, b)
```

用 mux 处理规范规定的特殊情况：

| 条件 | div | divu | rem | remu |
|---|---|---|---|---|
| b == 0 | -1（全 1） | 全 1 | a | a |
| a == INT_MIN 且 b == -1（仅 div/rem） | a | | 0 | |

用 `Equal(64)` 检查 `b == 0`；溢出条件为 `Equal(a, 0x8000…) & Equal(b, 0xFFFF…)`。

W 型先符号扩展或零扩展低 32 位，再使用相同电路，最后对结果执行 sext32。divuw/remuw 的输入零扩展。

## 在游戏中构建

1. 放置四个 `Mul(64)`（或根据 B8 调整数量）、若干 `Add(64)` 和用于进位检测的 `Less_u`。
2. 放置各两个 `Div(64)`、`Mod(64)`（有符号/无符号路径）、四个 `Neg(64)`、三个特殊条件 `Equal` 和 mux 树。
3. 保存到 Foundry 的 `RV64G/MulDiv`。

## 验证

| 运算 | a | b | y |
|---|---|---|---|
| mulhu | 0xFFFF_FFFF_FFFF_FFFF | 0xFFFF_FFFF_FFFF_FFFF | 0xFFFF_FFFF_FFFF_FFFE |
| mulh | -1 | -1 | 0 |
| mulhsu | -1 | 0xFFFF_FFFF_FFFF_FFFF | -1（0xFFFF…） |
| div | -7 | 2 | -3 |
| rem | -7 | 2 | -1 |
| div | 7 | 0 | -1 |
| rem | 7 | 0 | 7 |
| div | INT_MIN | -1 | INT_MIN |
| rem | INT_MIN | -1 | 0 |
| divw | 0x8000_0000（即 -2^31） | -1 | 0xFFFF_FFFF_8000_0000 |

## 状态

目前仅有设计文档。
