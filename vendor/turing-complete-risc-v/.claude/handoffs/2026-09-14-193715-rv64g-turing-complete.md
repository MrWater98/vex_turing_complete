# RV64G 项目交接摘要

本项目计划在 Turing Complete 的架构沙盒中实现 RISC-V RV64G。ISA 生成器、参考编码器、测试程序、硬件模块文档和电路存档生成工具均位于本目录。

## 当前状态

- `tools/selftest.py` 可检查指令表、参考编码和 ISA 生成结果。
- `tools/gen_alu64.py` 可生成 Foundry 元件 `RV64G/ALU64` 的 `circuit.data`。
- 电路生成流程绕过 TCI 的自动布局：`tools/tcgen/design.py` 负责摆放和布线，`tools/tcgen/sim.py` 在写入存档前模拟逻辑。
- 生成器和 ISA 仍需在游戏中打开并验证；未验证的假设记录在 `docs/verification-checklist.md` 与 `docs/circuit-generation.md`。

## 开发约定

1. 修改指令表后运行 `python tools/selftest.py` 和 `python tools/gen_isa.py`。
2. 游戏存档格式及电路生成细节见 `docs/circuit-generation.md`。
3. 电路设计按 `components/` 中的模块文档推进，完成的模块在游戏中检查后再上传 Hub。
4. 修改游戏存档前先关闭游戏并备份。
