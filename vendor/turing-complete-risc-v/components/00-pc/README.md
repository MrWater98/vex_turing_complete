# 00-pc — PC 寄存器与下一 PC 选择

## 目的

保存当前指令地址，并在每个周期更新为 `pc + 4`、分支/跳转目标或陷阱向量之一。

## 引脚

| 名称 | 宽度 | 方向 | 说明 |
|---|---:|---|---|
| `clk_en` | 1 | 输入 | 是否在当前 tick 更新 PC（单周期时恒为 1；两相时钟时仅在执行 tick 为 1） |
| `branch_taken` | 1 | 输入 | 06-branch 判断分支成立或正在执行 jal/jalr 时为 1 |
| `target` | 64 | 输入 | 06-branch 计算出的分支/跳转目标 |
| `trap` | 1 | 输入 | 09-csr 检测到 ecall/ebreak 时为 1 |
| `mtvec` | 64 | 输入 | 陷阱向量（09-csr） |
| `mret` | 1 | 输入 | 正在执行 mret 时为 1 |
| `mepc` | 64 | 输入 | 返回地址（09-csr） |
| `pc` | 64 | 输出 | 当前 PC，连接到 01-ifetch、03-imm-gen 的 auipc、06-branch 和 09-csr |
| `pc_plus4` | 64 | 输出 | jal/jalr 写入 rd 的返回值 |

## 内部设计

```text
pc_reg: Register(64)，初始值 0
pc_plus4 = Add(64)(pc, Constant(64)=4)
next_pc  = Mux(64)，优先级：trap ? mtvec : mret ? mepc : branch_taken ? target : pc_plus4
pc_reg.in = next_pc，pc_reg.save = clk_en
```

用三个串联的 `Mux(64)` 实现优先级选择，后级条件优先级更高。

## 在游戏中构建

1. 放置一个 `Register(64)`，将输出标记为 `pc`。
2. 使用值为 4 的 `Constant(64)` 和 `Add(64)` 生成 `pc_plus4`。
3. 放置三个 `Mux(64)`，选择端依次连接 `branch_taken`、`mret`、`trap`。
4. 将最后一个 mux 的输出连接到寄存器输入，将 `clk_en` 连接到保存端。
5. 保存到 Foundry 的 `RV64G/PC`。

## 验证

- 不连接其他信号并连续 tick 时，`pc` 应依次为 0、4、8……。
- 设置 `branch_taken = 1`、`target = 0x40`，下一 tick 的 `pc` 应为 `0x40`。
- 使用游戏的电路重置进行复位（寄存器初始值为 0）。

## 状态

目前只有设计文档，尚未构建电路。
