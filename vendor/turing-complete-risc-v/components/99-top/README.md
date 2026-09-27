# 99-top — 顶层电路集成

## 目的

连接各模块并决定不同指令的 mux 选择信号。单周期设计在一个 tick 内完成取指、译码、执行和写回。

## 数据流

```text
00-pc ──pc──▶ 01-ifetch ──instr──▶ 02-decoder ──字段/控制信号──▶ 所有模块
                                   03-imm-gen ──imm──▶ ALU b 输入 / 06-branch
04-regfile ──rdata1, rdata2──▶ 05-alu、06-branch、07-lsu(wdata)、08-muldiv、09-csr、10-amo
05-alu ──y──▶ 07-lsu(addr) / 结果 mux
结果 mux ──wdata──▶ 04-regfile
06-branch ──branch_taken, target──▶ 00-pc
09-csr ──trap/mtvec/mret/mepc──▶ 00-pc
11/12-fpu ──▶ FRegFile、结果 mux（整数结果）、09-csr(fflags)
```

## ALU 输入选择

| 指令 | a | b |
|---|---|---|
| R 型、W 型 R | rs1 | rs2 |
| I 型、W 型 I | rs1 | imm |
| load/store/loadfp/storefp/jalr | rs1 | imm（地址） |
| lui | 0 | imm（force_add） |
| auipc | pc | imm（force_add） |
| branch | rs1 | rs2（由 06-branch 比较，ALU 结果不使用） |

`a_sel`: is_auipc ? pc : is_lui ? 0 : rdata1。`b_sel`: alu_src_imm ? imm : rdata2。

## 写入 rd 的值（结果 mux）

| 指令 | wdata |
|---|---|
| op/opimm/op32/opimm32（不含 M） | ALU y |
| M | 08-muldiv y |
| lui/auipc | ALU y（force_add） |
| jal/jalr | pc_plus4 |
| load | 07-lsu rdata |
| csr* | 09-csr rdata（旧值） |
| amo/lr/sc | 10-amo old |
| fcvt.w/wu/l/lu.*、fmv.x.*、feq/flt/fle、fclass | FPU 整数结果 |

`reg_write` 是 02-decoder 的派生信号。浮点目的寄存器通过 `freg_write` 写入 FRegFile。

## 存储器请求选择

07-lsu 接收整数加载/存储、浮点加载/存储和 AMO 三类请求。`is_amo` 优先；其余情况 `mem_read = is_load | is_loadfp`、`mem_write = is_store | is_storefp`，`wdata = is_storefp ? rs2_f : rdata2`。

## 时钟

- 单周期：`clk_en = 1`。RAM 全部使用 Fast RAM（游戏资料显示它只增加门成本、不增加延迟；忽略分数）。
- 游戏时钟元件将一个周期分为两相：存储器在前一相读取、后一相写入。因此同 tick 内的寄存器文件读写符合单周期语义（B3）。
- 若 Fast RAM 仍存在读延迟（B2），用 `Register(1)` 翻转 `phase`。取指 tick（phase 0）不写入；执行 tick（phase 1）才令 `clk_en = 1`。取指 tick 末尾将 `instr` 存入 `Register(32)`。

## 在游戏中构建

1. 在沙盒中创建 `RV64G` 架构并应用 `isa/rv64g.isa`。
2. 依次放置 Foundry 的 `RV64G/*` 元件：PC → Decoder → ImmGen → RegFile → ALU → Branch → LSU →（MulDiv）→（CSR）→（AMO）→（FPU）。
3. 按上方表格连接 mux。
4. 用运行程序 `tests/run_*.asm`（待编写）检查寄存器值，不要用 `tests/encode_check.asm` 做此项检查。

## 集成验证程序（待编写）

| 文件 | 内容 | 检查方式 |
|---|---|---|
| `tests/run_01_alu.asm` | addi/add/sub/移位/比较 | 检查 x1–x10 |
| `tests/run_02_branch.asm` | 循环 10 次，测试 6 种条件分支 | 检查计数器寄存器 |
| `tests/run_03_mem.asm` | sd/ld/sb/lb 组合 | 检查内存转储 |
| `tests/run_04_m.asm` | mul/div 特殊规则 | |
| `tests/run_05_csr.asm` | ecall 处理程序 → mret | |
| `tests/run_06_fp.asm` | 0.1+0.2、1/3 | 检查浮点寄存器位模式 |

## 状态

目前仅有设计文档。
