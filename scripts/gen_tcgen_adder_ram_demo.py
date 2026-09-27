#!/usr/bin/env python3
"""Build a three-value RAM sum for the existing architecture save slot."""
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1] / "vendor/turing-complete-risc-v/tools"
sys.path.insert(0, str(TOOLS))

from tcgen.design import Design  # noqa: E402
from tcgen.pins import PINS  # noqa: E402
from tcsave import save16  # noqa: E402
from tcsave.save16 import Point, Wire  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
SAVE_NAME = "tcgen_adder_ram_demo"  # Reuse the architecture selected in the game.
OUT = ROOT / "build" / SAVE_NAME / "circuit.data"


def build():
    # BisFlipper's switched output has an enable input at (-1, -2). TCGen's
    # upstream pin table omits it, so extend the in-process table only.
    PINS["level_output_switched"]["in"]["enable"] = (-1, -2)
    PINS["level_output_switched"]["body"] = (0, 3, -4, 4)

    d = Design(SAVE_NAME, description="RAM[0] + RAM[1] + RAM[2] = 3 + 5 + 7 = 15")
    d.add("ram", "ram", 8, settings=[0, 0, 0], buffer_size=1024,
          init_data="assembler", x=0, y=160)
    # Three load ports form a contiguous stack above the RAM.
    for i, y in enumerate((146, 148, 150)):
        d.add(f"load{i}", "load_port", 8, x=0, y=y)
        d.add(f"address{i}", "constant", 8, settings=[i], x=-40, y=110 + 10 * i)

    d.add("load_enable", "on", 1, x=-40, y=140)
    d.add("add01", "add", 8, x=45, y=145)
    d.add("add012", "add", 8, x=65, y=150)
    d.add("carry01", "off", 1, x=45, y=140)
    d.add("carry012", "off", 1, x=65, y=145)
    d.add("sum", "level_output_switched", 8, x=95, y=150, label="SUM")
    d.add("sum_enable", "on", 1, x=85, y=148)

    for i in range(3):
        d.connect(f"address{i}_net", f"address{i}.out", f"load{i}.address")
    d.connect("load_enable_net", "load_enable.out",
              "load0.enable", "load1.enable", "load2.enable")
    d.connect("ram0", "load0.out", "add01.in0")
    d.connect("ram1", "load1.out", "add01.in1")
    d.connect("ram2", "load2.out", "add012.in1")
    d.connect("partial", "add01.out", "add012.in0")
    d.connect("carry01_net", "carry01.out", "add01.cin")
    d.connect("carry012_net", "carry012.out", "add012.cin")
    d.connect("sum_net", "add012.out", "sum.in")
    d.connect("sum_enable_net", "sum_enable.out", "sum.enable")

    # Keep addresses and RAM output wires short and inspectable in the game.
    d.wires = [
        Wire(Point(-37, 110), [(0, 15), (2, 36), (0, 7)]),
        Wire(Point(-37, 120), [(0, 17), (2, 28), (0, 5)]),
        Wire(Point(-37, 130), [(0, 19), (2, 20), (0, 3)]),
        Wire(Point(-39, 140), [(0, 23), (2, 9), (0, 1)]),
        Wire(Point(-16, 145), [(0, 1)]),
        Wire(Point(-16, 147), [(0, 1)]),
        Wire(Point(16, 145), [(6, 1), (0, 28)]),
        Wire(Point(16, 147), [(6, 1), (0, 28)]),
        Wire(Point(16, 149), [(2, 2), (0, 48)]),
        Wire(Point(47, 145), [(0, 13), (2, 4), (0, 4)]),
        Wire(Point(46, 140), [(2, 2), (4, 1), (2, 1)]),
        Wire(Point(66, 145), [(2, 2), (4, 1), (2, 1)]),
        Wire(Point(67, 150), [(0, 25)]),
        Wire(Point(86, 148), [(0, 8)]),
    ]
    d.validate()
    save = d.to_save(foundry=True)
    ram = next(c for c in save.components if c.kind == "ram")
    ram.selected_programs = {
        "campaign/sandbox": "sandbox/new_program.asm",
        "campaign/overture_1_registers": "sandbox/new_program.asm",
    }
    return save


def main():
    save = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = save16.serialize(save)
    assert save16.raw_bytes(save16.serialize(save16.parse(data))) == save16.raw_bytes(data)
    OUT.write_bytes(data)
    print("RAM bytes: 3, 5, 7; expected SUM: 15")
    print(f"components={len(save.components)} wires={len(save.wires)}")
    print(f"wrote={OUT}")


if __name__ == "__main__":
    main()
