# RAM running sum demo

[English](#english) | [中文](#中文)

<a id="english"></a>

## Circuit

The RAM contains four 8-bit values loaded from `examples/tcgen_adder_ram_demo/sandbox/new_program.asm`:

| Address | Value |
| --- | ---: |
| 0 | 3 |
| 1 | 5 |
| 2 | 7 |
| 3 | 11 |

A 2-bit counter repeatedly selects addresses `0, 1, 2, 3`. One 8-bit load port reads the selected byte. An 8-bit adder adds that byte to the previous total held in a register; the adder result is saved back to the register on each step. `SUM` displays the register's current total. Both the RAM load and register save are enabled by `on`, and the adder carry-in is `off`. Starting from zero, the logical totals after reading each byte are `3, 8, 15, 26, 29, 34, 41, 52, ...`. The 8-bit register wraps modulo 256. Depending on when the game displays state relative to a clock step, the initial screen may show zero before the first update.

## RAM port attachment

The earlier generator placed the RAM at `y=160` while the working game save had it at `y=159`. The generator now calculates the port position from component edges: the RAM top edge is `ram.y - 9`, and the load port bottom edge is at its center `y`. Placing the load port at `ram.y - 9` makes the edges meet. In this design the RAM is at `(0, 159)` and its only load port is at `(0, 150)`. This matches the attachment seen after adjusting the previous circuit in the game. The calculation is in `load_port_y()`; move the RAM by changing `ram_y` and the port and nearby logic will follow.

BisFlipper also showed that `level_output_switched` needs an enable wire at offset `(-1, -2)`. The generator adds that pin to its in-process pin table; it does not modify `vendor/`.

## Generate and install in WSL

```bash
python3 scripts/gen_tcgen_adder_ram_demo.py
game_arch='/mnt/c/Users/User/AppData/Roaming/Turing Complete/schematics/architecture/tcgen_adder_ram_demo'
mkdir -p "$game_arch/sandbox"
cp build/tcgen_adder_ram_demo/circuit.data "$game_arch/circuit.data"
cp examples/tcgen_adder_ram_demo/spec.isa "$game_arch/spec.isa"
cp examples/tcgen_adder_ram_demo/sandbox/new_program.asm "$game_arch/sandbox/new_program.asm"
```

Reload the architecture in Turing Complete. The RAM uses `init_data=assembler` and selects `sandbox/new_program.asm` for `campaign/sandbox` and `campaign/overture_1_registers`. The script validates wire placement and the `circuit.data` format. It cannot execute the game's assembler or clocked RAM/register simulation. If `SUM` stays zero, first check that RAM addresses `0..3` contain `03 05 07 0B`.

<a id="中文"></a>

## 电路含义

RAM 的地址 `0、1、2、3` 分别放入 `3、5、7、11`。2 位计数器循环选择这四个地址，一个 8 位读口读出当前数字；8 位加法器把它与寄存器保存的旧总和相加，每步再把新总和写回寄存器。`SUM` 显示寄存器中的总和。读口和寄存器保存信号都接 `on`，加法器进位输入接 `off`。从零开始，按顺序读数后的逻辑总和是 `3、8、15、26、29、34、41、52……`。总和是 8 位，超过 255 时回绕。游戏可能在第一次更新前先显示 0。

## RAM 端口贴合

旧生成器把 RAM 放在 `y=160`，但游戏里正常贴合的存档将它移到了 `y=159`。新生成器根据元件边缘计算位置：RAM 顶边是 `ram.y - 9`，读口的底边就是其中心 `y`，因此读口中心设为 `ram.y - 9`。当前 RAM 位于 `(0, 159)`，读口位于 `(0, 150)`。以后只需修改 `ram_y`，读口和周围电路会一起移动。BisFlipper 还证实 `level_output_switched` 在 `(-1, -2)` 有使能脚；生成器只在运行时补充定义，不修改 `vendor/`。

按上面的命令将电路、`spec.isa` 和汇编文件复制到游戏目录，再重新加载架构。RAM 通过 `assembler` 初始化，程序文件为 `sandbox/new_program.asm`。生成器能检查连线和存档格式，但不能运行游戏里的 RAM 与寄存器仿真。如果 SUM 始终为零，先检查 RAM 地址 `0..3` 是否为 `03 05 07 0B`。
