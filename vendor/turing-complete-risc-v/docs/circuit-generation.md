# 电路生成：直接生成 circuit.data

自 2026-09-15 起，电路可由仓库中的生成器直接构建。无需在游戏 GUI 中手工绘制：工具生成 `circuit.data` 并放入 Foundry，用户再在游戏中打开检查。

## 依据

- **存档格式：** 游戏开发者公开的 [save_monger](https://github.com/Stuffe/save_monger)（CC0，支持格式版本 16）。`tools/tcsave/` 是对其 `common.nim`、`versions/v16.nim` 和 `state_to_binary` 的 Python 移植。文件由版本字节 16 和 Snappy 原始块组成。记录称，在本机 115 个 v16 存档中有 113 个可逐字节往返一致；其余两个只在读取时填充的默认设置上不同。
- **引脚位置：** 通过追踪 Hub 架构 “RISC-V”（id 130）的 `RV32I_ALU` 和 Overture 战役关卡答案电路确认。引脚名称参照游戏可执行文件中的 Verilog 接口（例如 `module TC_Add (cin, in0, in1, out, cout)`）。表位于 `tools/tcgen/pins.py`。
- **布线规则：** 检查 Hub 的 112 个电路后，发现 7276 处线段相交但没有共同端点，因此线段交叉不代表连接；仅端点处连接引脚或其他线段主体。

## 工具

| 文件 | 用途 |
|---|---|
| `tools/tcsave/snappy.py` | 纯 Python Snappy；压缩目前只输出字面块 |
| `tools/tcsave/save16.py` | v16 存档读写和 JSON 转换 |
| `tools/tc_dump.py` | 输出存档摘要或 JSON |
| `tools/tcgen/pins.py` | 各元件的引脚相对坐标、元件边界和置信度 |
| `tools/tcgen/design.py` | 将网表转换为单列布局、分轨布线、验证结果并写入存档 |
| `tools/tcgen/sim.py` | 网表模拟器，在导入游戏前检查逻辑 |
| `tools/gen_alu64.py` | 第一个元件 `RV64G/ALU64` 的生成器，含 400 组向量模拟对照 |

```bash
python tools/gen_alu64.py build/ALU64          # 输出 build/ALU64/circuit.data
python tools/tc_dump.py build/ALU64/circuit.data
```

安装路径：`%APPDATA%\Turing Complete\schematics\foundry\RV64G\<名称>\circuit.data`。复制文件前请先退出游戏。

## 布线方式（design.py）

元件竖直排列在一列中，每个元件独占一段行空间。每条网络独占一个右侧轨道、一条顶部主干和一个左侧轨道；连线按输出引脚 → 右轨道 → 顶部主干 → 左轨道 → 输入引脚的顺序绘制。多驱动网络（例如开关总线）的其他驱动端接到右侧轨道。验证器检查网络是否经过其他网络的端点、其他网络的引脚或元件本体。

布局尺寸随网络数量增长。例如 ALU64 有 27 个元件、52 条线，布局为 42×143 格。顶层电路的紧凑布线尚未实现。

## 尚待在游戏中验证

| 项目 | 当前假设 | 检查方法 |
|---|---|---|
| 生成的 Foundry 元件能否加载（design 4×6 格、cc 引脚设置） | 使用与 Hub 元件相同的数值 | 在 Foundry 打开 ALU64 |
| `add` 的 cout 引脚位置 | (0,+2) | ALU64 未使用 |
| `constant` 输出引脚位置 | (3,0) | 在下一个元件中检查 |
| `static_indexer` 输入引脚位置 | (-2,0) 或 (-3,0) | 在下一个元件中检查 |
| 自定义元件实例的引脚布局规则 | cc 引脚设置 `[0]` 表示边（0 右、2 左）；顺序由位置/ui_order 决定 | 构建顶层电路时确认 |
| 移位量大于等于位宽时游戏移位器的行为 | 输出 0 | ALU64 测试中令 b ≥ 64 |
