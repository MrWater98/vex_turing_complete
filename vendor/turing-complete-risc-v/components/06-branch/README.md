# 06-branch — 分支比较器与跳转目标

## 目的

判断 6 种 B 型分支条件，计算 jal/jalr 目标，并将 `branch_taken` 和 `target` 传给 00-pc。

## 引脚

| 名称 | 宽度 | 方向 | 说明 |
|---|---:|---|---|
| `a`、`b` | 64 | 输入 | rs1、rs2 的值 |
| `funct3` | 3 | 输入 | 分支类型 |
| `is_branch`、`is_jal`、`is_jalr` | 1 | 输入 | 指令类型信号 |
| `pc` | 64 | 输入 | 当前 PC |
| `imm` | 64 | 输入 | 来自 03-imm-gen 的 B/J/I 型立即数 |
| `branch_taken` | 1 | 输出 | 分支或跳转是否成立 |
| `target` | 64 | 输出 | 分支/跳转目标 |

## 条件判断

| funct3 | 分支 | 条件 |
|---|---|---|
| 000 | beq | eq |
| 001 | bne | ~eq |
| 100 | blt | lt_s |
| 101 | bge | ~lt_s |
| 110 | bltu | lt_u |
| 111 | bgeu | ~lt_u |

```text
eq   = Equal(64)(a, b)
lt_s = Less_s(64)(a, b)
lt_u = Less_u(64)(a, b)
base = funct3[2] ? (funct3[1] ? lt_u : lt_s) : eq       （两级 1 位 Mux）
cond = base ^ funct3[0]
branch_taken = (is_branch & cond) | is_jal | is_jalr
```

## 目标地址计算

```text
t_rel = Add(64)(pc, imm)                    （branch、jal）
t_reg = Add(64)(a, imm) & ~1                （jalr 将最低位置 0）
target = is_jalr ? t_reg : t_rel
```

`& ~1` 可由 `And(64)` 和 `Constant(64)=0xFFFF_FFFF_FFFF_FFFE` 实现。

## 在游戏中构建

1. 放置 `Equal(64)`、`Less_s(64)`、`Less_u(64)`、两个 1 位 `Mux` 和一个 `Xor`。
2. 放置两个 `Add(64)`、一个 `And(64)` 和一个 `Mux(64)`。
3. 保存到 Foundry 的 `RV64G/Branch`。

## 验证

- a=5、b=5：funct3=000 时 cond=1；funct3=001 时 cond=0。
- a=-1、b=1：blt 为 1，bltu 为 0。
- pc=8、imm=-4、is_branch=1、cond=1 时 target=4。
- is_jalr=1、a=0x1001、imm=0 时 target=0x1000。

## 状态

目前仅有设计文档。
