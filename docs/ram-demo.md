# RAM sum demo

[English](#english) | [中文](#中文)

<a id="english"></a>

## Circuit

This replaces the counter-driven RAM read/write experiment in the existing `tcgen_adder_ram_demo` architecture slot. The RAM starts from the three bytes assembled from `examples/tcgen_adder_ram_demo/sandbox/new_program.asm`:

| Address | Value |
| --- | ---: |
| 0 | 3 |
| 1 | 5 |
| 2 | 7 |

Three 8-bit load ports continuously read those fixed addresses. Two 8-bit adders calculate `(RAM[0] + RAM[1]) + RAM[2] = (3 + 5) + 7 = 15`. Both carry inputs are tied to `off`. One `on` enables the load ports, and another enables the switched `SUM` output. There is no counter or store port. Once the assembler initializes the RAM, `SUM` should stay at 15 on every simulation step.

The RAM is at `(0, 160)` and the load ports are at `(0, 146)`, `(0, 148)`, and `(0, 150)`. The bottom port is ten rows above the RAM, matching the contiguous port stack observed in BisFlipper. BisFlipper also showed that `level_output_switched` needs an enable wire at offset `(-1, -2)`; the generator supplies that pin in memory without changing `vendor/`.

## Generate and install in WSL

```bash
python3 scripts/gen_tcgen_adder_ram_demo.py
game_arch='/mnt/c/Users/User/AppData/Roaming/Turing Complete/schematics/architecture/tcgen_adder_ram_demo'
mkdir -p "$game_arch/sandbox"
cp build/tcgen_adder_ram_demo/circuit.data "$game_arch/circuit.data"
cp examples/tcgen_adder_ram_demo/spec.isa "$game_arch/spec.isa"
cp examples/tcgen_adder_ram_demo/sandbox/new_program.asm "$game_arch/sandbox/new_program.asm"
```

Reload the architecture in Turing Complete. The RAM uses `init_data=assembler` and selects `sandbox/new_program.asm` for `campaign/sandbox` and `campaign/overture_1_registers`. The script checks the geometric connections and that `circuit.data` can be read back. It does not run the game's assembler or RAM simulator. If `SUM` stays at zero, inspect the assembled RAM bytes first; the intended bytes at addresses 0, 1, and 2 are `03 05 07`.

<a id="中文"></a>

## 电路含义

这个电路替换了原来计数器同时读写 RAM 的实验，仍使用 `tcgen_adder_ram_demo` 架构目录。汇编文件向 RAM 的地址 `0、1、2` 分别放入 `3、5、7`。三个 8 位读口持续读取这三个地址，两个 8 位加法器计算 `(3+5)+7=15`，进位输入都接 `off`。一个 `on` 启用读口，另一个 `on` 启用 SUM 输出。电路没有计数器和写口；RAM 初始化成功后，每步的 SUM 应保持为 15。

RAM 位于 `(0, 160)`，三个读口位于 `(0, 146)`、`(0, 148)`、`(0, 150)`。最下方的读口比 RAM 高十格，与 BisFlipper 的连续端口堆叠一致。BisFlipper 还证实 `level_output_switched` 在 `(-1, -2)` 处有使能脚；生成器只在运行时补充该脚，不修改 `vendor/`。

运行上面的命令生成并复制三个文件，然后在游戏中重新加载架构。RAM 采用 `assembler` 初始化，为 `campaign/sandbox` 和 `campaign/overture_1_registers` 选择 `sandbox/new_program.asm`。生成器能检查连线与存档格式，但不能代替游戏运行汇编器或 RAM 仿真。如果 SUM 仍为零，先检查 RAM 地址 `0、1、2` 是否装入 `03 05 07`。
