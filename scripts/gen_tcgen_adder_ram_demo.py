#!/usr/bin/env python3
"""Build a RAM-fed running sum in the existing architecture save slot."""
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1] / "vendor/turing-complete-risc-v/tools"
sys.path.insert(0, str(TOOLS))

from tcgen.design import Design  # noqa: E402
from tcgen.pins import PINS  # noqa: E402
from tcsave import save16  # noqa: E402
from tcsave.save16 import Point, Wire  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SAVE_NAME = "tcgen_adder_ram_demo"  # Keep the architecture already selected in the game.
OUT = ROOT / "build" / SAVE_NAME / "circuit.data"
RAM_VALUES = (3, 5, 7, 11)


def load_port_y(ram_y):
    """Put the bottom edge of a load port on the RAM's top edge."""
    ram_top = ram_y + PINS["ram"]["rows"][0]
    return ram_top - PINS["load_port"]["rows"][1]


def build():
    # BisFlipper confirms an enable pin at (-1, -2) on switched outputs.
    # Extend only this process's pin table; leave vendor files untouched.
    PINS["level_output_switched"]["in"]["enable"] = (-1, -2)
    PINS["level_output_switched"]["body"] = (0, 3, -4, 4)

    ram_y = 159
    y = load_port_y(ram_y)  # 150: matches the game-adjusted working save.
    assert y + PINS["load_port"]["rows"][1] == ram_y + PINS["ram"]["rows"][0]

    d = Design(SAVE_NAME, description="Running sum of RAM bytes 3, 5, 7, 11")
    d.add("ram", "ram", 8, settings=[0, 0, 0], buffer_size=1024,
          init_data="assembler", x=0, y=ram_y)
    d.add("load", "load_port", 8, x=0, y=y)
    d.add("address", "counter", 2, x=-30, y=y)
    d.add("load_enable", "on", 1, x=-25, y=y - 5)
    d.add("total", "register_word", 8, x=30, y=y - 10)
    d.add("save_total", "on", 1, x=18, y=y - 11)
    d.add("adder", "add", 8, x=50, y=y - 1)
    d.add("carry_zero", "off", 1, x=50, y=y - 7)
    d.add("sum", "level_output_switched", 8, x=85, y=y - 20, label="SUM")
    d.add("sum_enable", "on", 1, x=75, y=y - 22)

    d.connect("address_net", "address.out", "load.address")
    d.connect("load_enable_net", "load_enable.out", "load.enable")
    d.connect("ram_value", "load.out", "adder.in1")
    d.connect("current_total", "total.out", "adder.in0", "sum.in")
    d.connect("next_total", "adder.out", "total.save_value")
    d.connect("save_total_net", "save_total.out", "total.save")
    d.connect("carry_zero_net", "carry_zero.out", "adder.cin")
    d.connect("sum_enable_net", "sum_enable.out", "sum.enable")

    # Each wire is tied to its actual pin. The feedback passes through a
    # register, which breaks the combinational cycle.
    d.wires = [
        Wire(Point(-27, y), [(0, 12)]),
        Wire(Point(-24, y - 5), [(0, 6), (2, 4), (0, 3)]),
        Wire(Point(16, y - 1), [(2, 1), (0, 33)]),
        Wire(Point(33, y - 10), [(0, 9), (2, 8), (0, 7)]),
        Wire(Point(33, y - 10), [(0, 37), (6, 10), (0, 12)]),
        Wire(Point(52, y - 1), [(0, 8), (6, 14), (4, 35), (2, 5), (0, 2)]),
        Wire(Point(19, y - 11), [(0, 8)]),
        Wire(Point(51, y - 7), [(2, 3), (4, 1), (2, 1)]),
        Wire(Point(76, y - 22), [(0, 8)]),
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
    print(f"RAM bytes: {RAM_VALUES}; expected running totals: 3, 8, 15, 26, 29, ...")
    print(f"RAM y={next(c.position.y for c in save.components if c.kind == 'ram')}; "
          f"load y={next(c.position.y for c in save.components if c.kind == 'load_port')}")
    print(f"components={len(save.components)} wires={len(save.wires)}")
    print(f"wrote={OUT}")


if __name__ == "__main__":
    main()
