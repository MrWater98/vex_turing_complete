# 在 Turing Complete 中搭建可运行的电路

这份记录来自 `tcgen_adder_ram_demo` 的几次实际生成、游戏内调整，以及对 `schematic_hub/BisFlipper/circuit.data` 的反向解析。示例源码是 [`scripts/gen_tcgen_adder_ram_demo.py`](../scripts/gen_tcgen_adder_ram_demo.py)；电路当前使用一个 RAM 读口、一个计数器、一个 8 位加法器和一个保存总和的寄存器。

## 1. 先写清楚每一步的状态

先确定输入、输出和哪些值需要跨步骤保存。当前电路的目标是从 RAM 顺序读出 `3、5、7、11`，并不断累加：

```text
地址计数器 ──→ RAM 读地址
RAM 读数 ─────┐
              加法器 ──→ 寄存器的保存值
寄存器旧总和 ──┘             │
       ↑                     │
       └─────────────────────┘
寄存器当前总和 ──→ SUM 输出
```

计数器是 2 位，地址循环为 `0、1、2、3`。RAM、加法器、寄存器都是 8 位。寄存器是反馈路径中的状态元件，避免把加法器输出直接接回输入而形成组合环。以寄存器和计数器初始为零、地址 0 首先被读取为前提，保存后的逻辑总和为 `3、8、15、26、29、34……`，超过 255 时按 8 位回绕。游戏画面显示的是更新前还是更新后的状态，需要在游戏内对照确认。

## 2. 用已知存档确认元件和引脚

`vendor/turing-complete-risc-v/tools/tcsave/save16.py` 可以解析 `circuit.data`；`vendor/turing-complete-risc-v/tools/tcgen/pins.py` 记录了常用引脚偏移。先找一个游戏中确实能工作的同类电路，再比对坐标。BisFlipper 的 RAM 在 `(41,59)`，三个读口在 `(41,43)`、`(41,45)`、`(41,47)`，写口在 `(41,49)`。它的 `level_output_switched` 在 `(82,70)`：数值线接 `(79,70)`，另一条线接 `(81,68)`，后者是输出使能脚。现有 vendor 引脚表没有定义这个使能脚；示例生成器只在进程内补充 `(-1,-2)`，没有修改 vendor 文件。

常用的旋转 0 引脚偏移如下；坐标均相对于元件中心：

| 元件 | 输入 | 输出 |
| --- | --- | --- |
| 计数器 | 覆盖 `(-3,-1)`、覆盖值 `(-3,0)` | `(+3,0)` |
| RAM 读口 | 使能 `(-15,-1)`、地址 `(-15,0)` | `(+16,-1)` |
| 8 位加法器 | 进位 `(0,-2)`、两个加数 `(-1,-1)` 和 `(-1,+1)` | 和 `(+2,0)` |
| 字寄存器 | 保存 `(-3,-1)`、保存值 `(-3,0)` | 当前值 `(+3,0)` |
| switched 输出 | 数值 `(-3,0)`、使能 `(-1,-2)` | 游戏输出 |

## 3. 按边缘计算 RAM 端口位置

仅仅给 RAM 和端口相同的 `x` 坐标还不够；它们必须在游戏的格网上贴合。当前解析到的 RAM 上边缘是 `ram.y - 9`，读口下边缘是 `load_port.y`。因此**单个读口**按下式放置：

```python
load_x = ram_x
load_y = ram_y - 9
```

例如游戏中已贴合的存档是 RAM `(0,159)`、读口 `(0,150)`。旧脚本让 RAM 位于 `(0,160)`，读口仍在 `(0,150)`，两者就差一格。现在脚本使用 `load_port_y()` 从元件行范围计算，并用断言检查两个边缘相等。若在游戏中拖动 RAM 得到新的有效位置，应反向解析保存后的 `circuit.data`，把修正写回生成器。

多个端口不能直接套用单端口公式。参考 BisFlipper，读口中心间隔两格；最下方若是写口，其中心在 `ram.y - 10`。写口比读口多一个数据输入行，因此堆叠时需要按端口种类计算边界和引脚位置。读口、写口的上下顺序还决定同一步中操作的先后；需要读旧值时，读口放在写口上方。

## 4. 把数据源和使能也接完整

当前 RAM 设为 `init_data="assembler"`。`examples/tcgen_adder_ram_demo/spec.isa` 定义了 8 位 `byte` 指令，`sandbox/new_program.asm` 写入四个字节：

```asm
byte 3
byte 5
byte 7
byte 11
```

在生成的 RAM 元件上，`selected_programs` 将 `campaign/sandbox` 和 `campaign/overture_1_registers` 指向 `sandbox/new_program.asm`。游戏目录里必须同时有 `circuit.data`、`spec.isa` 和该 `.asm` 文件。只复制电路文件，RAM 可能不会装入这些数据。

RAM 读口的使能脚接 `on`；寄存器的保存脚也接 `on`；加法器的进位输入接 `off`；switched 输出的使能脚另接一个 `on`。遗漏任一使能脚，都可能出现地址或内部信号变化、但 `SUM` 仍为零的情况。

## 5. 布线、生成和游戏内检查

先用 `Design.connect()` 表示驱动端和接收端，再按真实引脚坐标添加 `Wire`。同一网络可以从一个输出分到多个输入；不同网络的导线可以交叉，但不要让一条导线的端点落在另一网络的导线上。`Design.validate()` 能发现部分几何冲突，却不能证明端口已被游戏识别为同一 RAM，也不能模拟 RAM 或寄存器时序。因此 RAM 贴合需单独用边缘公式检查，最终仍要在游戏里观察。

从仓库根目录生成并复制：

```bash
python3 scripts/gen_tcgen_adder_ram_demo.py
game_arch='/mnt/c/Users/User/AppData/Roaming/Turing Complete/schematics/architecture/tcgen_adder_ram_demo'
mkdir -p "$game_arch/sandbox"
cp build/tcgen_adder_ram_demo/circuit.data "$game_arch/circuit.data"
cp examples/tcgen_adder_ram_demo/spec.isa "$game_arch/spec.isa"
cp examples/tcgen_adder_ram_demo/sandbox/new_program.asm "$game_arch/sandbox/new_program.asm"
```

在 Turing Complete 中重新加载架构，先看 RAM 的地址 `0..3` 是否为 `03 05 07 0B`，再看计数器是否循环 `0..3`、读口值是否随地址变化，最后看寄存器和 `SUM`。如果 SUM 始终为零，按“RAM 内容 → 端口贴合和使能 → 读口输出 → 加法器输出 → 寄存器保存 → 输出使能”的顺序排查。若旧版 `SUM=15` 电路仍出现，说明游戏还没有重新加载新的 `circuit.data`。

不要把脚本中的存档解析成功当成游戏仿真成功。稳定的 `3+5+7=15` 版本已在游戏中观察到正确结果；当前逐步累加版本的具体时序仍需以游戏中显示为准。
