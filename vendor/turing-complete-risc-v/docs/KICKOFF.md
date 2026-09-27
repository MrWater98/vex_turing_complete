# 项目启动：在 Turing Complete 中实现 RV64G

## 概要

目标是在 Turing Complete 的架构沙盒中实现完整的 RISC-V `RV64G`（整数 I、乘法 M、原子操作 A、浮点 F/D、CSR 和 fence.i）。ISA 定义与设计文档在本仓库维护；电路在游戏中构建，按模块和扩展上传到 Hub。

## 可行性

- 游戏元件支持 2 至 64 位宽，可构建 64 位数据通路；加法、乘法、除法、移位、比较、RAM 和端口都是基础元件。
- 游戏汇编器支持位切片、虚拟操作数、PC 相对偏移（`$start`）、断言和小端序，可表达 RISC-V 的分散立即数编码（B/J 型）。
- 寄存器文件可由单个 64 位 RAM 加两个读端口和一个写端口构成。游戏 Symphony 战役也以 RAM 实现名为 “Register File” 的寄存器文件。

## 当前产物

| 产物 | 位置 | 状态 |
|---|---|---|
| RV64G 汇编器定义（225 条基本指令 + 52 条伪指令） | `isa/rv64g.isa`、`isa/parts/` | 已生成；尚未在游戏中验证 |
| 指令表、生成器和参考编码器 | `tools/rv64g/`、`tools/gen_isa.py`、`tools/rv_encode.py` | 自检通过（35 个手算向量，并交叉检查 52 条伪指令） |
| 汇编器验证程序及预期机器码 | `tests/encode_check.asm`、`tests/encode_check.expected.txt` | 68 个字 |
| 硬件模块设计文档及集成说明 | `components/*/README.md` | 包含引脚、内部结构、布线步骤和验证值 |
| 验证清单 | `docs/verification-checklist.md` | 11 项汇编器检查、12 项元件检查；第 0 节记录了可从游戏资料确认的内容 |

## 分工

- 生成工具维护 ISA、编码器、测试程序、模块文档和验证清单，并生成电路。`tools/tcgen` 根据公开的存档格式库实现直接生成 `circuit.data`，见 `docs/circuit-generation.md`。
- 用户在游戏中检查并运行生成的元件、记录验证结果并上传 Hub。只有生成器无法完成的电路需要手动布线。

## 建议步骤

1. 在沙盒中新建 `RV64G` 架构并载入 `isa/rv64g.isa`；如果出错，改用 `isa/rv64g_no_experimental.isa`。
2. 汇编 `tests/encode_check.asm`，与 `tests/encode_check.expected.txt` 对照，并填写验证清单 A1–A10。
3. 用 8 位小电路验证 RAM 端口（B1–B7），据此确定寄存器文件、LSU 和时钟方案。
4. 按顺序构建 `components/00-pc` 至 `05-alu`，用各模块 README 中的预期值进行单元验证。
5. 每个模块完成后保存到 Foundry 的 `RV64G/<名称>`，上传到 Hub，并在对应目录记录截图和链接。

## 阶段顺序

I → 分支/跳转 → 加载/存储 → W 型 → M → Zicsr/Zifencei → A → F → D → 集成。先从单周期开始；如果 RAM 读延迟得到验证，则改用两相时钟。F/D 拆分为 Unpack、Round、AddSub、Mul、Div、Sqrt、FMA、Cmp、Cvt 等子模块逐个实现。

## 约定

- 修改指令表后先运行 `python tools/selftest.py`，再运行 `python tools/gen_isa.py` 重新生成 ISA；不要手工编辑生成的 `.isa` 文件。
- 操作数名称只使用一个字符，因为游戏汇编器的机器码格式只识别首字母。
- 立即数必须附带宽度类型，例如 `%i:S12(immediate)`。游戏拒绝没有类型的立即数；类型集中定义在 `tools/rv64g/formats.py` 的 `TYPE_OF` 中。
- 不将电路二进制 `circuit.data` 提交到仓库，也不修改战役 Foundry 元件目录 `Overture/*` 和 `Hint */*`。
- 修改游戏存档前关闭游戏，并先备份到 `%APPDATA%\Turing Complete\backup\`。

## 参考资料

- RISC-V 规范：https://riscv.org/technical/specifications/
- 游戏汇编器文档：`<游戏目录>/asset/manual/Assembly/Language creation/`
- 后续会话交接记录：`.claude/handoffs/`
