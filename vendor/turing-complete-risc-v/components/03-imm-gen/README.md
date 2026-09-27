# 03-imm-gen — 立即数生成器

## 目的

按指令格式（I/S/B/U/J）拼接分散的立即数字段，并符号扩展到 64 位。

## 引脚

| 名称 | 宽度 | 方向 | 说明 |
|---|---:|---|---|
| `instr` | 32 | 输入 | 指令字 |
| `is_store`、`is_storefp` | 1 | 输入 | 选择 S 型 |
| `is_branch` | 1 | 输入 | 选择 B 型 |
| `is_lui`、`is_auipc` | 1 | 输入 | 选择 U 型 |
| `is_jal` | 1 | 输入 | 选择 J 型 |
| `imm` | 64 | 输出 | 符号扩展的立即数；未选择其他类型时默认为 I 型 |

## 立即数组装

| 格式 | 位组成（MSB → LSB） | 宽度 |
|---|---|---:|
| I | instr[31:20] | 12 |
| S | instr[31:25] ‖ instr[11:7] | 12 |
| B | instr[31] ‖ instr[7] ‖ instr[30:25] ‖ instr[11:8] ‖ 0 | 13 |
| U | instr[31:12] ‖ 0×12 | 32 |
| J | instr[31] ‖ instr[19:12] ‖ instr[20] ‖ instr[30:21] ‖ 0 | 21 |

五种格式的符号位都是 `instr[31]`。因此可以将该位复制所需次数，再用一个 `Maker` 完成符号扩展。

## 内部设计

```text
sign   = instr[31]
sext52 = Maker(52) ← sign ×52     (64 - 12)
imm_i  = Maker(64) ← sext52 ‖ instr[31:20]
imm_s  = Maker(64) ← sext52 ‖ instr[31:25] ‖ instr[11:7]
imm_b  = Maker(64) ← sign×51 ‖ instr[31] ‖ instr[7] ‖ instr[30:25] ‖ instr[11:8] ‖ 0
imm_u  = Maker(64) ← sign×32 ‖ instr[31:12] ‖ 0×12
imm_j  = Maker(64) ← sign×43 ‖ instr[31] ‖ instr[19:12] ‖ instr[20] ‖ instr[30:21] ‖ 0
imm    = Mux 链：is_jal ? imm_j : (is_lui|is_auipc) ? imm_u : is_branch ? imm_b : (is_store|is_storefp) ? imm_s : imm_i
```

游戏的 `Maker` 支持 2/4/8 个输入，需要分层组合。从拆分成 32 个单比特的 `instr`（可与 02-decoder 共用）中取所需位。

## 在游戏中构建

1. 接收 02-decoder 的 32 个单比特输出，或在本模块内重新拆分 `instr`。
2. 按上面的五种格式搭建 `Maker` 树；符号位可以连接到多个输入。
3. 使用四个 `Mux(64)` 选择格式。
4. 保存到 Foundry 的 `RV64G/ImmGen`。

## 验证

| instr | 格式 | 预期 imm |
|---|---|---|
| 0xFFF00113（addi x2,x0,-1） | I | 0xFFFF_FFFF_FFFF_FFFF |
| 0x0021B823（sd x2,16(x3)） | S | 16 |
| 0xFE208EE3（beq, -4） | B | -4 |
| 0x123450B7（lui 0x12345） | U | 0x12345000 |
| 0x0080006F（jal +8） | J | 8 |

## 状态

目前只有设计文档。
