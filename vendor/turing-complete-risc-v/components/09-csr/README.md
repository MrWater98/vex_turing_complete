# 09-csr — CSR 文件、陷阱与计数器

## 目的

实现 6 种 Zicsr 指令、ecall/ebreak 陷阱、mret、作为 nop 的 wfi、与 FPU 共用的 fflags/frm，以及 cycle/instret 计数器。只实现 M 模式，不实现 U/S 模式。

## 实现的 CSR

| 名称 | 编号 | 实现 |
|---|---|---|
| fflags | 0x001 | `Register(5)`，由 FPU 执行 OR 累积 |
| frm | 0x002 | `Register(3)` |
| fcsr | 0x003 | 合并 frm ‖ fflags 读取，并拆分写入 |
| cycle / mcycle | 0xC00 / 0xB00 | `Counter(64)`，每 tick 加 1 |
| time | 0xC01 | 与 cycle 相同，也可使用游戏 Time 元件 |
| instret / minstret | 0xC02 / 0xB02 | `Counter(64)`，每个执行 tick 加 1 |
| mstatus | 0x300 | `Register(64)`，仅 MIE（3）和 MPIE（7）位有意义 |
| misa | 0x301 | 只读常量 0x8000_0000_0014_112D（RV64 I/M/A/F/D 等） |
| mie、mip | 0x304、0x344 | `Register(64)`；不支持中断，因此为 0 |
| mtvec | 0x305 | `Register(64)` |
| mscratch | 0x340 | `Register(64)` |
| mepc | 0x341 | `Register(64)` |
| mcause | 0x342 | `Register(64)`：ecall=11，ebreak=3 |
| mtval | 0x343 | `Register(64)`，值为 0 |
| mvendorid/marchid/mimpid | 0xF11–F13 | 0 |
| mhartid | 0xF14 | 0 |

## 引脚

| 名称 | 宽度 | 方向 | 说明 |
|---|---:|---|---|
| `csr_addr` | 12 | 输入 | instr[31:20] |
| `funct3` | 3 | 输入 | CSR 操作类型 |
| `rs1_val` | 64 | 输入 | rs1 的值 |
| `zimm` | 5 | 输入 | instr[19:15] |
| `is_csr`、`is_ecall`、`is_ebreak`、`is_mret` | 1 | 输入 | 指令控制信号 |
| `pc` | 64 | 输入 | 当前 PC |
| `fflags_set` | 5 | 输入 | FPU 异常标志，以 OR 累积 |
| `clk_en` | 1 | 输入 | 时钟使能 |
| `rdata` | 64 | 输出 | 要写入 rd 的旧值 |
| `trap`、`mtvec`、`mret`、`mepc` | 1/64/1/64 | 输出 | 连接到 00-pc |
| `frm` | 3 | 输出 | 连接到 FPU |

## 行为

```text
old   = 读取 mux（用 Equal(12) 译码 csr_addr，只实现表中 CSR）
src   = funct3[2] ? zext(zimm) : rs1_val
new   = funct3[1:0] == 01 ? src : funct3[1:0] == 10 ? old | src : old & ~src
write = is_csr & clk_en & ~(funct3[1:0]==10/11 且 src 来自 x0/0 时可省略写入) & (CSR 非只读)
rdata = old
```

陷阱行为：`trap = is_ecall | is_ebreak`。该 tick 将 `mepc = pc`、`mcause = is_ecall ? 11 : 3`、`mstatus.MPIE = MIE` 并清除 MIE。执行 mret 时恢复 `mstatus.MIE = MPIE`，由 00-pc 将 PC 设为 mepc。wfi 为 nop。可选地将 `is_ebreak` 接到游戏 `Halt` 元件。

## 在游戏中构建

1. 放置 9 个寄存器（`Register(64)` 或相应宽度）和两个 `Counter(64)`。
2. 用 `Equal(12)` 译码 CSR 地址，并用 `Mux(64)` 树读取。
3. 使用 `Or/And/Not(64)` 和 mux 计算写入值。
4. 保存到 Foundry 的 `RV64G/CSR`。

## 验证

- 执行 `csrrw x1, mscratch, x2`（x2=7），再执行 `csrr x3, mscratch`，x3 应为 7。
- 执行 `csrrsi x0, mstatus, 8`，MIE 应为 1；用 `csrrci` 清除。
- ecall 后 PC 应为 mtvec、mepc 为 ecall 指令地址、mcause 为 11；mret 后 PC 应为 mepc。
- 执行两条指令后，`rdinstret` 应为 2（根据计数时机调整预期）。

## 状态

目前仅有设计文档。
