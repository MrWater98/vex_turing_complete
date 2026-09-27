#!/usr/bin/env python3
"""Build a RAM-fed adder test circuit for Turing Complete.

A counter writes its value to a RAM word and reads the same word each tick.
This makes the RAM path observable even when no assembler program is loaded.
"""
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1] / "vendor/turing-complete-risc-v/tools"
sys.path.insert(0, str(TOOLS))

from tcgen.design import Design  # noqa: E402
from tcgen.pins import PINS  # noqa: E402
from tcgen.sim import Sim  # noqa: E402
from tcsave import save16  # noqa: E402
from tcsave.save16 import Point, Wire  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/tcgen_adder_ram_demo/circuit.data"


def build():
    # BisFlipper has a wire from not_bit(73, 68).out to the switched output
    # at (81, 68), two rows above its value input. TCGen's pin table omits
    # this enable pin. Extend the in-process table without editing vendor/.
    PINS["level_output_switched"]["in"]["enable"] = (-1, -2)
    # The estimated body in that table covers the real enable lead. The
    # game's BisFlipper save routes horizontally into this pin from the left.
    PINS["level_output_switched"]["body"] = (0, 3, -4, 4)
    d = Design(
        "tcgen_adder_ram_demo",
        description="RAM read/write 8-bit adder test bench; counter supplies address and data",
    )

    # Counter supplies the current word address and the word written there.
    # Its 2-bit output wraps after four entries.
    d.add("vector_index", "counter", 2, x=-30, y=146)
    d.add("ram_enable", "on", 1, x=-25, y=136)

    # The port is placed 16 rows above its RAM, matching the game's port layout.
    # Keep the RAM well below the adder so the router's horizontal buses do not
    # pass through the RAM body.
    d.add(
        "vectors",
        "ram",
        8,
        settings=[0, 0, 0],
        buffer_size=1024,
        init_data="zeroes",
        x=0,
        y=160,
    )
    d.add("vector_port", "load_port", 16, x=0, y=144)
    d.add("vector_write", "store_port", 16, x=0, y=146)
    d.add("split", "splitter_word_2", 8, x=50, y=48)
    d.add("adder", "add", 8, x=72, y=61)
    d.add("cin_zero", "off", 1, x=70, y=57)
    d.add("sum", "level_output_switched", 8, x=104, y=70, label="SUM")
    d.add("sum_enable", "on", 1, x=94, y=68)

    d.connect(
        "ram_enable",
        "ram_enable.out",
        "vector_port.enable",
        "vector_write.enable",
    )
    d.connect(
        "counter_word",
        "vector_index.out",
        "vector_port.address",
        "vector_write.address",
        "vector_write.data",
    )
    d.connect("packed_vector", "vector_port.out", "split.in")
    d.connect("a", "split.out0", "adder.in0")
    d.connect("b", "split.out1", "adder.in1")
    d.connect("cin_zero", "cin_zero.out", "adder.cin")
    d.connect("sum", "adder.out", "sum.in")
    d.connect("sum_enable", "sum_enable.out", "sum.enable")

    # Design.build() intentionally stacks every component in a column. RAM
    # ports are instead physically mounted above their RAM, so place this
    # test bench explicitly using the offset seen in BisFlipper.
    positions = {
        "vector_index": (-30, 146),
        "ram_enable": (-25, 136),
        "vectors": (0, 160),
        "vector_port": (0, 144),
        "vector_write": (0, 146),
        "split": (50, 48),
        "adder": (72, 61),
        "cin_zero": (70, 57),
        "sum": (104, 70),
        "sum_enable": (94, 68),
    }
    for name, (x, y) in positions.items():
        d.by_name[name].x = x
        d.by_name[name].y = y
    # Keep the counter-to-RAM connections explicit and short. Each wire starts
    # at the counter output and ends at one port pin; no T junction is needed.
    # Likewise use the BisFlipper enable-pin lead for the SUM output.
    local_names = ("counter_word", "ram_enable", "cin_zero", "sum_enable")
    local_nets = [d.net_by_name[name] for name in local_names]
    for net in local_nets:
        d.nets.remove(net)
    d.route()
    d.nets.extend(local_nets)
    counter_out = d.by_name["vector_index"].pin_at("out")
    d.wires.extend([
        Wire(counter_out, [(6, 2), (0, 12)]),  # load address (-15, 144)
        Wire(counter_out, [(0, 12)]),          # store address (-15, 146)
        Wire(counter_out, [(2, 1), (0, 12)]),  # store data (-15, 147)
        Wire(Point(-24, 136), [(0, 7), (2, 7), (0, 2)]),  # load enable
        Wire(Point(-24, 136), [(0, 6), (2, 9), (0, 3)]),  # store enable
    ])
    d.wires.append(Wire(Point(71, 57), [(2, 2), (0, 1)]))
    d.wires.append(Wire(Point(95, 68), [(0, 8)]))
    d.validate()
    save = d.to_save(foundry=True)
    return d, save


def verify_vectors():
    # Exercise the generated combinational chain with packed words supplied in
    # place of the RAM output. RAM timing is game-specific and cannot
    # be emulated by TCGen's combinational simulator.
    vectors = [(address, 0) for address in range(4)]
    probe = Design("tcgen_adder_ram_data_path")
    probe.add("packed", "cc_input", 16)
    probe.add("low_byte", "static_indexer", 8, settings=[0])
    probe.add("high_byte", "static_indexer", 8, settings=[8])
    probe.add("adder", "add", 8)
    probe.add("cin_zero", "off", 1)
    probe.add("sum", "cc_output", 8)
    probe.connect("packed", "packed.out", "low_byte.in", "high_byte.in")
    probe.connect("a", "low_byte.out", "adder.in0")
    probe.connect("b", "high_byte.out", "adder.in1")
    probe.connect("cin_zero", "cin_zero.out", "adder.cin")
    probe.connect("sum", "adder.out", "sum.in")
    sim = Sim(probe)

    expected = [0, 1, 2, 3]
    for i, ((a, b), result) in enumerate(zip(vectors, expected)):
        # After one full counter cycle, the store port has written addresses
        # 0..3 as 16-bit words. The upper byte is zero.
        packed_word = (b << 8) | a
        outputs, _ = sim.run({"packed": packed_word})
        assert outputs["sum"] == result, (a, b, outputs["sum"], result)
        print(f"address {i}: RAM={a:3d} SUM={result:3d} (0x{result:02x})")
    print(f"data-path simulation: {len(vectors)} rows, 0 mismatches")


def main():
    d, save = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = save16.serialize(save)
    parsed = save16.parse(data)
    assert save16.raw_bytes(save16.serialize(parsed)) == save16.raw_bytes(data)
    OUT.write_bytes(data)
    verify_vectors()
    print(f"components={len(save.components)} wires={len(save.wires)} bounds={d.bounds}")
    print(f"wrote={OUT} bytes={len(data)} custom_id={save.custom_id}")


if __name__ == "__main__":
    main()
