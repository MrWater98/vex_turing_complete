# 02-decoder — 指令字段拆分与控制信号

## 目的

将 32 位指令拆成字段，并识别 opcode，生成各模块使用的单比特控制信号。funct3/funct7 的具体解释由对应运算模块（ALU、分支、LSU 等）负责。

## 引脚

输入：`instr`（32 位）

输出字段：

| 名称 | 宽度 | 位范围 |
|---|---:|---|
| `opcode` | 7 | [6:0] |
| `rd` | 5 | [11:7] |
| `funct3` | 3 | [14:12] |
| `rs1` | 5 | [19:15] |
| `rs2` | 5 | [24:20] |
| `funct7` | 7 | [31:25] |
| `rs3` | 5 | [31:27]（R4 型） |
| `fmt` | 2 | [26:25]（浮点） |
| `shamt6` | 6 | [25:20]（RV64 移位） |
| `csr` | 12 | [31:20] |

opcode 单热控制输出：

| 名称 | opcode | 含义 |
|---|---|---|
| `is_lui` | 0110111 | LUI |
| `is_auipc` | 0010111 | AUIPC |
| `is_jal` | 1101111 | JAL |
| `is_jalr` | 1100111 | JALR |
| `is_branch` | 1100011 | 条件分支 |
| `is_load` | 0000011 | 整数加载 |
| `is_store` | 0100011 | 整数存储 |
| `is_opimm` | 0010011 | I 型整数运算 |
| `is_op` | 0110011 | R 型整数运算（含 M 扩展） |
| `is_opimm32` | 0011011 | W 型立即数运算 |
| `is_op32` | 0111011 | W 型 R 格式运算（含 M 扩展） |
| `is_miscmem` | 0001111 | fence、fence.i |
| `is_system` | 1110011 | csr*、ecall、ebreak、mret、wfi |
| `is_amo` | 0101111 | A 扩展 |
| `is_loadfp` | 0000111 | flw/fld |
| `is_storefp` | 0100111 | fsw/fsd |
| `is_opfp` | 1010011 | F/D 浮点运算 |
| `is_fma` | 10x0x11 | fmadd/fmsub/fnmsub/fnmadd（opcode[6:4]=100，[1:0]=11） |

派生信号：

| 名称 | 逻辑表达式 |
|---|---|
| `reg_write` | is_lui \\| is_auipc \\| is_jal \\| is_jalr \\| is_load \\| is_opimm \\| is_op \\| is_opimm32 \\| is_op32 \\| is_system·(funct3≠0) \\| is_amo \\| is_opfp·(rd 为整数目标时：fcvt.w/l、fmv.x、feq/flt/fle、fclass) |
| `freg_write` | is_loadfp \\| is_fma \\| is_opfp·(rd 为浮点目标时) |
| `is_word_op` | is_opimm32 \\| is_op32 |
| `is_m` | (is_op \\| is_op32) · (funct7 == 0000001) |
| `alu_src_imm` | is_opimm \\| is_opimm32 \\| is_load \\| is_store \\| is_jalr \\| is_loadfp \\| is_storefp |
| `is_ecall` | is_system · funct3==0 · csr==0x000 |
| `is_ebreak` | is_system · funct3==0 · csr==0x001 |
| `is_mret` | is_system · funct3==0 · csr==0x302 |
| `is_csr` | is_system · funct3≠0 |

## 内部设计

- 使用 `Splitter` 拆分指令位。游戏 splitter 支持 2/4/8 路；可先将 32 位拆成 4 个 8 位块，再通过 `Maker`/`Splitter` 组合出 7、5、3、5、5、7 位字段。最简单的方案是把 32 位完全拆成单比特（`Splitter_8` ×4，再用单比特 splitter），然后分别用 `Maker` 组合字段。
- opcode 识别使用 18 组 `Equal(7)` 与 `Constant(7)`。
- 派生信号使用 `Or`/`And` 门。

## 在游戏中构建

1. 将 `instr` 拆成 32 个单比特。
2. 按字段表用 `Maker` 组合并添加标签。
3. 对 18 个 opcode 常量分别使用 `Equal(7)` 生成 `is_*` 信号。
4. 放置派生信号所需的逻辑门。
5. 保存到 Foundry 的 `RV64G/Decoder`。

## 验证

对于 `instr = 0x00500093`（addi x1, x0, 5），应有 `is_opimm = 1`、`rd = 1`、`rs1 = 0`、`funct3 = 0`、立即数字段 [31:20] = 5。对于 `instr = 0xFE208EE3`（beq x1, x0, -4），应有 `is_branch = 1`、`rs1 = 1`、`rs2 = 0`。

## 状态

目前仅有设计文档。
