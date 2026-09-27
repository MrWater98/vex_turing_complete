# RAM adder demo

[English](#english) | [中文](#中文)

<a id="english"></a>

## What we learned from BisFlipper

We parsed `schematic_hub/BisFlipper/circuit.data` with `vendor/turing-complete-risc-v/tools/tcsave/save16.py` and traced the wires to its RAM ports. BisFlipper places its 8-bit RAM at `(41, 59)`. The first load port is at `(41, 43)`, 16 grid rows above the RAM; further ports are spaced two rows apart. Its load-port enable pins are driven by `on`. The store-port enable is driven by circuit logic.

We also found **two** wires at BisFlipper's `level_output_switched` at `(82, 70)`: data enters at `(79, 70)` and a wire from `not_bit` ends at `(81, 68)`. The latter is the output enable pin, offset `(-1, -2)`. The vendored TCGen pin table omits this pin. The generator adds it to its in-memory pin table and connects `on`, without changing files under `vendor/`. Our earlier conclusion that no enable wire was needed was wrong.

BisFlipper initializes RAM from the assembler and stores program selections under keys such as `campaign/sandbox`. Those selections depend on the game context. In our local save, `levels.txt` selected `tcgen_adder_ram_demo` for `sandbox`, while `settings.txt` named `overture_1_registers` as the current level. This mismatch is a plausible reason why a counter could advance while an assembler-initialized RAM still reads zero in the architecture view. It does not prove what data the game actually loaded.

## Current circuit

Run the generator from the repository root:

```bash
python3 scripts/gen_tcgen_adder_ram_demo.py
```

It writes `build/tcgen_adder_ram_demo/circuit.data`. To install it in the WSL game save directory:

```bash
game_schematics='/mnt/c/Users/User/AppData/Roaming/Turing Complete/schematics'
mkdir -p "$game_schematics/architecture/tcgen_adder_ram_demo"
cp build/tcgen_adder_ram_demo/circuit.data \
  "$game_schematics/architecture/tcgen_adder_ram_demo/circuit.data"
```

The current demo starts its RAM at zero and does not need a selected assembly program. A 2-bit counter at `(-30, 146)` has three short, separate wires from its output to the load address `(-15, 144)`, store address `(-15, 146)`, and store data `(-15, 147)`. This avoids relying on a long perimeter route or a T junction. `on` enables both RAM ports. The 16-bit load-port output is split into two 8-bit operands, added with carry-in tied to `off`, and sent to `level_output_switched`; a second `on` drives that output's enable pin. The working game save has the RAM at `(0, 156)`, the load port at `(0, 144)`, and the store port at `(0, 146)`. Their 12/10-row spacing matches the bottom two ports in BisFlipper's stack. An earlier generated RAM position `(0, 160)` left a gap and did not attach the ports correctly. Reload the architecture after copying the save.

The memory has 8-bit cells, while both ports access 16 bits at a time. Addresses `0, 1, 2, 3` therefore refer to overlapping pairs of bytes, so `SUM` is not simply the current counter value. The load port is above the store port; the game processes ports from top to bottom, so each load sees memory before that tick's store. The precise numeric sequence also depends on byte order and on when the counter advances relative to the displayed tick. The generator's `0, 1, 2, 3` data-path check injects those values directly and does not predict game RAM output.

The generator checks wire placement and save serialization. Its local simulator checks the combination of byte extraction and addition using supplied data; it cannot simulate the RAM, assembler selection, or game ticks. The in-game sequence still needs to be observed. If SUM remains zero, inspect the load-port output after a full counter cycle. A zero there points to RAM write enable, address, data, or port attachment. A changing load-port value with a zero SUM points to the splitter, adder, or output data/enable connection.

`examples/tcgen_adder_ram_demo/spec.isa` and `sandbox/new_program.asm` are retained as an assembler-vector experiment. They are not used by the current self-writing RAM circuit.

<a id="中文"></a>

## 从 BisFlipper 学到的内容

我们反向解析了 `schematic_hub/BisFlipper/circuit.data` 并逐点追踪导线。它的 8 位 RAM 位于 `(41, 59)`，第一个读口位于 `(41, 43)`，比 RAM 高 16 格；其余端口每隔两格排列。读口使能接 `on`，写口使能由电路逻辑控制。

BisFlipper 的 `level_output_switched` 位于 `(82, 70)`，**有两条输入线**：数值线接到 `(79, 70)`，另一条来自 `not_bit` 的线接到 `(81, 68)`。后者是偏移 `(-1, -2)` 的输出使能脚。vendor 的 TCGen 引脚表漏掉了它；生成器只在运行时补充引脚定义并接上 `on`，没有修改 vendor 文件。此前认为输出不需要使能线，是错误判断。

BisFlipper 通过 assembler 初始化 RAM，并以 `campaign/sandbox` 等关卡键选择程序。本机 `levels.txt` 将 `tcgen_adder_ram_demo` 选作 `sandbox` 架构，而 `settings.txt` 的当前关卡是 `overture_1_registers`。这可能解释 counter 变化但 RAM 仍读零的现象；存档本身无法证明游戏实际装载了哪些数据。

当前演示用 `python3 scripts/gen_tcgen_adder_ram_demo.py` 生成 `build/tcgen_adder_ram_demo/circuit.data`，按上面的命令复制到游戏目录。RAM 从零初始化，不依赖汇编程序。2 位 counter 位于 `(-30, 146)`，三根短线从它的输出分别连接读地址 `(-15, 144)`、写地址 `(-15, 146)` 和写数据 `(-15, 147)`，不再依赖绕外圈的长线或 T 形分支。`on` 启用两个 RAM 端口；16 位读数拆成两个 8 位数，经进位输入接 `off` 的加法器送到 SUM，另一个 `on` 接 SUM 的使能脚。游戏中正常工作的存档将 RAM 放在 `(0, 156)`，读口和写口分别位于 `(0, 144)`、`(0, 146)`；相差 12/10 格，与 BisFlipper 端口堆叠的底部两个端口一致。之前生成脚本中的 RAM `(0, 160)` 留出了间隔，端口没有正确附着。复制后需要重新加载架构。

RAM 以 8 位为存储单元，读写端口却都是 16 位。地址 `0、1、2、3` 因此读取和写入相互重叠的两个字节，SUM 不一定等于当前 counter。读口位于写口上方；游戏按从上到下的顺序处理端口，所以读操作看到的是本周期写入前的内容。具体数值还与字节序、计数器更新和画面显示的先后有关。生成器中 `0、1、2、3` 的检查是向加法器直接注入测试数据，并非游戏 RAM 的预期输出序列。

生成器检查布线和存档读写；本地组合逻辑模拟不能验证游戏 RAM 的写入时序。如果 SUM 仍为零，先看读口输出：读口也为零时检查写入使能、地址、数据和端口位置；读口已变化时检查拆分器、加法器和输出的数值及使能连接。

`examples/tcgen_adder_ram_demo/` 中的 `.isa` 与 `.asm` 是保留的汇编向量实验，不参与当前的自写 RAM 电路。
