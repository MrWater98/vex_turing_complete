[English](#english) | [中文](#中文)

<a id="english"></a>

This project bundles [turing-complete-interface](https://github.com/MegaIng/turing-complete-interface) and [TuringCompleteYosysTechlib](https://github.com/NoEdwardsNecessary/TuringCompleteYosysTechlib) to turn Verilog into a circuit that can run in Turing Complete.

### Setup

Requires Python 3.10+, Yosys, and Nim/Nimble for the TCI serializer. The project uses the local OSS CAD Suite at `../VeriFlatten/oss-cad-suite` when it is complete, then falls back to `yosys` on `PATH`.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ./vendor/turing-complete-interface nimporter
```

Yosys defaults to `../VeriFlatten/oss-cad-suite/libexec/yosys`. Set `YOSYS` to use a different executable.

### Build and run

```bash
scripts/vex-to-tc.sh path/to/vex.v [top_module]
```

Try the 4-bit ripple-carry adder example:

```bash
TC_SCHEMATICS_DIR='/mnt/c/Users/User/AppData/Roaming/Turing Complete/schematics' \
TC_LEVEL=architecture TC_SAVE_NAME=test scripts/vex-to-tc.sh examples/ripple4_add.v
```

The script writes `build/ripple4_add_tc.v` and saves the circuit under `architecture/test`. Open **Architecture → test** in Turing Complete. `TC_SCHEMATICS_DIR` points to the game's `schematics` folder; omit it on systems where the interface can find the save directory automatically. The default level is `component_factory`, and the default save name is the Verilog filename.

### RAM running sum demo

Run `python3 scripts/gen_tcgen_adder_ram_demo.py` to build an architecture that repeatedly reads RAM values `3`, `5`, `7`, and `11` and accumulates them. The total changes as `3, 8, 15, 26, ...`. The load port is positioned from the RAM edge so it attaches correctly. See [RAM demo notes](docs/ram-demo.md) for WSL installation and the circuit details. The [circuit-building guide](docs/circuit-building.md) records the pin, RAM placement, wiring, and game-checking steps learned from this example.

To convert another design, pass its file and optional top module:

```bash
scripts/vex-to-tc.sh path/to/design.v [top_module]
```

The source should be a single Verilog file with one top module. The top-level module name defaults to the input filename without `.v`.

Upstream source and licenses are kept in `vendor/`.

## 中文

本项目集成了 [turing-complete-interface](https://github.com/MegaIng/turing-complete-interface) 和 [TuringCompleteYosysTechlib](https://github.com/NoEdwardsNecessary/TuringCompleteYosysTechlib)，用于将 Verilog 转换为可在 Turing Complete 中运行的电路。

### 安装

需要 Python 3.10+、Yosys，以及用于 TCI 序列化的 Nim/Nimble。项目优先使用位于 `../VeriFlatten/oss-cad-suite` 的完整 OSS CAD Suite，否则回退到 `PATH` 中的 `yosys`。

```bash
python3 -m venv .venv
.venv/bin/pip install -e ./vendor/turing-complete-interface nimporter
```

默认使用 `../VeriFlatten/oss-cad-suite/libexec/yosys`。如需更换，可设置 `YOSYS` 环境变量。

### 构建并运行

```bash
scripts/vex-to-tc.sh path/to/vex.v [top_module]
```

先运行这个 4 位串行进位加法器例子：

```bash
TC_SCHEMATICS_DIR='/mnt/c/Users/User/AppData/Roaming/Turing Complete/schematics' \
TC_LEVEL=architecture TC_SAVE_NAME=test scripts/vex-to-tc.sh examples/ripple4_add.v
```

脚本会生成 `build/ripple4_add_tc.v`，并将电路保存到 `architecture/test`。在游戏中打开 **Architecture → test**。`TC_SCHEMATICS_DIR` 指向游戏的 `schematics` 目录；如果接口能自动找到存档目录，可以省略它。默认关卡是 `component_factory`，默认存档名是 Verilog 文件名。

### RAM 累加演示

运行 `python3 scripts/gen_tcgen_adder_ram_demo.py`，生成循环读取 RAM 中 `3、5、7、11` 并逐步累加的电路，总和依次为 `3、8、15、26……`。读口位置根据 RAM 边缘计算，确保两者贴合。WSL 安装命令与电路说明见 [RAM 演示记录](docs/ram-demo.md)；引脚、RAM 贴合、布线和游戏内检查步骤见 [电路搭建指南](docs/circuit-building.md)。

转换其他设计时传入 Verilog 路径和可选的顶层模块名：

```bash
scripts/vex-to-tc.sh path/to/design.v [top_module]
```

输入应为包含一个顶层模块的 Verilog 文件。未指定 `top_module` 时，默认使用文件名（不含 `.v`）作为模块名。

上游代码及许可证保存在 `vendor/` 中。
