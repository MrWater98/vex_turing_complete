# 05-alu — 64 位 ALU（含 W 型）

## 目的

实现 10 种 R/I 型整数运算和 9 种 W 型运算（先进行 32 位运算，再符号扩展）。M 扩展由 08-muldiv 负责，这里只合并结果 mux。

## 引脚

| 名称 | 宽度 | 方向 | 说明 |
|---|---:|---|---|
| `a` | 64 | 输入 | rs1 的值（lui 为 0，auipc 为 pc） |
| `b` | 64 | 输入 | rs2 的值或立即数（`alu_src_imm`） |
| `funct3` | 3 | 输入 | 运算选择字段 |
| `funct7_5` | 1 | 输入 | funct7[5]，用于选择 sub/sra |
| `is_opimm_any` | 1 | 输入 | is_opimm \\| is_opimm32；立即数形式没有 sub |
| `is_word` | 1 | 输入 | is_opimm32 \\| is_op32 |
| `force_add` | 1 | 输入 | load/store/jalr/auipc/lui 地址或加法运算；忽略 funct3 强制 add |
| `y` | 64 | 输出 | 运算结果 |

## 运算选择

| funct3 | funct7[5]=0 | funct7[5]=1（仅 R 型） |
|---|---|---|
| 000 | add | sub |
| 001 | sll | |
| 010 | slt | |
| 011 | sltu | |
| 100 | xor | |
| 101 | srl | sra |
| 110 | or | |
| 111 | and | |

`sub_sel = funct3==000 & funct7_5 & ~is_opimm_any`；`sra_sel = funct3==101 & funct7_5`（立即数 srai 的 funct7[5] 也是 1，因此不应用 `is_opimm_any` 屏蔽）。

## 内部设计

```text
b_eff   = sub_sel ? Neg(64)(b) : b            （或用 Not 加进位 1）
sum     = Add(64)(a, b_eff)
sh      = is_word ? b[4:0] : b[5:0]           （用 5/6 位 Maker）
shl     = Lsl(64)(a, sh)
shr     = Lsr(64)(a, sh)
sar     = Asr(64)(a, sh)
lt      = Less_s(64)(a, b) → 零扩展为 64 位（63 个 0 加 1 位）
ltu     = Less_u(64)(a, b)
res64   = 按 funct3 用 Mux8 选择 sum、shl、lt、ltu、Xor、(sra_sel ? sar : shr)、Or、And
y64     = force_add ? sum : res64
```

W 型指令先计算，再取低 32 位并符号扩展；移位有单独路径：

```text
srlw    = 将 a 的低 32 位零扩展后送入 Lsr(64)，再取结果低 32 位
sraw    = 将 a 的低 32 位符号扩展为 sext32，再送入 Asr(64)
sllw    = 取 Lsl(64)(a, sh5) 的低 32 位
y       = is_word ? sext32(y64 或对应 W 型结果的 [31:0]) : y64
sext32(v) = Maker(64) ← v[31] ×32 ‖ v[31:0]
```

在元件设置中确认 `Less_s/Less_u` 的输入宽度是否为 64 位，以及结果是否为 1 位。

## 在游戏中构建

1. 放置 `Neg(64)`、`Add(64)`、`Lsl(64)`、`Lsr(64)`、`Asr(64)`、`Xor(64)`、`Or(64)`、`And(64)`、`Less_s(64)`、`Less_u(64)`。
2. 用 `Mux(64)` 构建 8 选 1 树，以 funct3 三个位控制三级选择。
3. W 型路径使用 `Splitter` 取低 32 位，再用 `Maker` 符号扩展。
4. 保存到 Foundry 的 `RV64G/ALU`。

## 验证向量（a、b → y）

| 运算 | a | b | y |
|---|---|---|---|
| add | 0xFFFF_FFFF_FFFF_FFFF | 1 | 0 |
| sub | 0 | 1 | 0xFFFF_FFFF_FFFF_FFFF |
| sra | 0x8000_0000_0000_0000 | 63 | 0xFFFF_FFFF_FFFF_FFFF |
| srl | 0x8000_0000_0000_0000 | 63 | 1 |
| sltu | 1 | 0xFFFF_FFFF_FFFF_FFFF | 1 |
| slt | 1 | 0xFFFF_FFFF_FFFF_FFFF | 0 |
| addw | 0x7FFF_FFFF | 1 | 0xFFFF_FFFF_8000_0000 |
| srlw | 0xFFFF_FFFF_FFFF_FFFF | 1 | 0x7FFF_FFFF |
| sraw | 0x8000_0000 | 4 | 0xFFFF_FFFF_F800_0000 |

## 状态

2026-09-15：`tools/gen_alu64.py` 可生成 Foundry 元件 `RV64G/ALU64`（27 个元件、52 条线；400 组模拟向量一致）。引脚为 a(64)、b(64)、funct3(3)、alt(1) → y(64)，结构与 Hub 的 RV32I_ALU 相同（译码器 → 开关总线）。确认 `static_indexer` 引脚后再处理 b[5:0] 移位量屏蔽；W 型由外围元件封装。游戏验证见 D1–D5。

目前仅有设计文档。
