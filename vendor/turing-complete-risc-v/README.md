# Turing Complete 中的 RV64G

这是一个在游戏 [Turing Complete](https://store.steampowered.com/app/1444480/) 的架构沙盒中实现 RISC-V `RV64G` 的项目（RV64I + M + A + F + D + Zicsr + Zifencei）。

项目产物分为两类：

| 类别 | 位置 | 维护方式 |
|---|---|---|
| ISA 定义、参考编码器、测试程序和设计文档 | `isa/`、`tools/`、`tests/`、`components/*/README.md` | 以文本形式维护 |
| 电路 | `tools/gen_*.py` 生成 `circuit.data`，再导入 Foundry（见 `docs/circuit-generation.md`） | 生成器负责构建和模拟；在游戏内检查并上传 Hub |

组件（硬件模块）和扩展（ISA 指令集合）分别放在独立目录中，便于单独上传到 Hub。

## 目录结构

```text
isa/
  rv64g.isa                  导入游戏的完整 ISA 定义（生成文件）
  rv64g_no_experimental.isa  去掉 8 字节伪指令的稳定版
  parts/                     各扩展的 ISA 片段
tools/
  rv64g/                     指令表、.isa 生成器和参考编码器
  tcsave/                    circuit.data v16 读写工具
  tcgen/                     网表到布局、布线及 circuit.data 的生成器与模拟器
  gen_alu64.py               生成第一个 Foundry 元件 RV64G/ALU64
  tc_dump.py                 输出存档摘要或 JSON
  gen_isa.py                 从指令表重建 isa/
  rv_encode.py               将 .asm 编码并与预期机器码对照
  selftest.py                检查指令表、编码器和生成器
tests/
  encode_check.asm           用于验证游戏汇编器的程序
  encode_check.expected.txt  参考编码器给出的预期机器码
components/                  硬件模块的设计文档
docs/                         项目启动、生成电路及验证说明
```

## 快速开始

```bash
python tools/selftest.py          # 检查指令表和编码器
python tools/gen_isa.py           # 修改指令表后重建 isa/
```

在游戏中：

1. 在沙盒中新建架构 `RV64G`。
2. 将 `isa/rv64g.isa` 粘贴到 ISA 编辑器中。如果游戏报错，试用 `isa/rv64g_no_experimental.isa`。
3. 将 `tests/encode_check.asm` 作为程序汇编，并逐行与 `tests/encode_check.expected.txt` 对照机器码。
4. 将结果记录在 `docs/verification-checklist.md`。

## ISA 定义使用的游戏语法

这里只使用从游戏汇编器文档（`asset/manual/Assembly/Language creation/`）和游戏程序的错误信息中确认过的功能。证据见 `docs/verification-checklist.md` 第 0 节。

- 使用位切片 `%o[10:5]` 表示 RISC-V 分散编码的立即数（B/J 型）。
- 使用虚拟操作数 `%o = %t - $start` 计算 PC 相对偏移。
- 使用断言检查立即数的范围和对齐。
- 立即数必须声明宽度类型：`%i:S12(immediate)`、`%s:U6(immediate)`、`%t:U32(immediate | label)`。类型会执行范围检查，因此不再重复添加范围断言。类型定义见 `tools/rv64g/formats.py` 中的 `TYPE_OF`。
- 所有操作数名称都使用单字符（`%d %a %b %c %i %t %s %n %z %r`），因为游戏的单字符机器码格式只读取操作数名称的首字母。

## 实现顺序

| 阶段 | 内容 | 相关目录 |
|---|---|---|
| 1 | 验证 ISA 定义及 RISC-V 编码 | `isa/`、`tests/`、`docs/verification-checklist.md` |
| 2 | PC、取指、译码、立即数生成器、寄存器文件、ALU（R/I 型） | `components/00-pc` 至 `05-alu` |
| 3 | 分支、跳转、lui/auipc | `components/06-branch` |
| 4 | 11 种加载和存储指令 | `components/07-lsu` |
| 5 | W 型指令 | `components/05-alu` |
| 6 | M 扩展 | `components/08-muldiv` |
| 7 | Zicsr 和 Zifencei | `components/09-csr` |
| 8 | A 扩展 | `components/10-amo` |
| 9 | F 扩展 | `components/11-fpu-f` |
| 10 | D 扩展 | `components/12-fpu-d` |
| 集成 | 顶层电路板 | `components/99-top` |

初始设计采用单周期、非流水线的哈佛架构（程序 RAM 和数据 RAM 分离）。如果游戏 RAM 存在读延迟，则改用两阶段（取指/执行）状态机，详见验证清单。

## 指令数量

| 扩展 | 基本指令数 | 备注 |
|---|---:|---|
| RV64I | 53 | 包括两种 jalr 语法，以及 fence/ecall/ebreak |
| A | 88 | 11 种 × W/D × aq/rl 四种组合 |
| D | 32 | 包括 fcvt.s.d / fcvt.d.s |
| 伪指令 | 48（另有 4 个实验项） | li 仅支持 12 位；li32/la/call/tail 占两条指令 |

## 参考资料

- RISC-V 非特权与特权规范：https://riscv.org/technical/specifications/
- 游戏汇编器文档：`<游戏目录>/asset/manual/Assembly/Language creation/**/doc.txt`
- 游戏 ISA 示例：`<游戏目录>/campaign/symphony/default.isa`
