# -*- coding: utf-8 -*-
"""circuit.data 格式版本 16（移植自 save_monger 的 versions/v16.nim 和 state_to_binary）。

坐标：整数网格，Point(x, y) 使用 int16。旋转：0..3（每次 90 度，见 rotate()）。
导线（Wire）路径：起点加若干（方向 0..7、长度）片段。DIRECTIONS[方向] 给出单格移动量。
"""
import io
import json
import struct
from dataclasses import dataclass, field

from . import snappy

VERSION = 16

# save_monger common.nim 中的 ComponentKind（v16 编号）。
KIND_NAMES = [
    'none', 'off', 'on', 'not_bit', 'and_bit', 'and_3_bit', 'nand_bit', 'or_bit', 'or_3_bit', 'nor_bit',
    'xor_bit', 'xnor_bit', 'switch_bit', 'delay_line_bit', 'register_bit', 'full_adder', 'maker_bit_8',
    'splitter_bit_8', 'not_word', 'or_word', 'and_word', 'nand_word', 'nor_word', 'xor_word', 'xnor_word',
    'switch_word', 'equal', 'less_u', 'less_s', 'neg', 'add', 'mul', 'div', 'lsl', 'lsr', 'rol', 'ror', 'asr',
    'counter', 'register_word', 'level_output_8_pin', 'level_delay_gate', 'mux', 'decoder_1', 'decoder_2',
    'decoder_3', 'constant', 'splitter_word_2', 'maker_word_2', 'clz', 'register_word_config',
    'probe_wire_asm', 'push_button', 'pipelined_load_port', 'load_port', 'delay_line_word', 'store_port',
    'ctz', 'cc_level_output', 'level_gate', 'level_input_1_pin', 'level_input_word', 'level_input_switched',
    'level_input_2_pin', 'level_input_3_pin', 'level_input_4_pin', 'deleted_16', 'deleted_17',
    'level_output_1_pin', 'level_output_word', 'level_output_switched', 'deleted_2', 'deleted_3',
    'level_output_2_pin', 'level_output_3_pin', 'level_output_4_pin', 'deleted_18', 'level_output_counter',
    'custom', 'cc_input', 'cc_input_buffer', 'cc_output', 'probe_memory_bit', 'probe_memory_word',
    'probe_wire_bit', 'probe_wire_word', 'deleted_20', 'halt', 'deleted_1', 'segment_display',
    'static_value', 'screen', 'time', 'keyboard', 'static_eval', 'verilog_input', 'verilog_output',
    'maker_word_4', 'maker_word_8', 'splitter_word_4', 'splitter_word_8', 'static_indexer', 'deleted_7',
    'deleted_8', 'inc', 'deleted_19', 'cc_level_input', 'deleted_9', 'mod', 'splitter_bit_2',
    'splitter_bit_4', 'maker_bit_2', 'maker_bit_4', 'deleted_10', 'concatenator_2', 'concatenator_4',
    'concatenator_8', 'static_indexer_config', 'ram', 'delay_line_word_config', 'deleted_11',
    'deleted_12', 'deleted_13', 'deleted_14', 'deleted_15',
]
KIND_IDS = {name: i for i, name in enumerate(KIND_NAMES)}

DIRECTIONS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]

INIT_DATA = ['zeroes', 'assembler', 'punch_card', 'file', 'hex_editor', 'persistent']

# 各元件类别的默认 settings 数量（读取时补齐）
DEFAULT_SETTINGS = {
    'constant': [0], 'cc_input': [2], 'cc_output': [0], 'level_gate': [0], 'level_delay_gate': [0, 0],
    'segment_display': [0], 'keyboard': [0], 'static_indexer': [0], 'ram': [0, 0, 0], 'push_button': [0],
}
MIN_ONE_WATCHED = {'probe_memory_bit', 'probe_memory_word', 'screen'}


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    def __add__(self, o):
        return Point(self.x + o.x, self.y + o.y)

    def rotate(self, r):
        r %= 4
        if r == 0:
            return self
        if r == 1:
            return Point(-self.y, self.x)
        if r == 2:
            return Point(-self.x, -self.y)
        return Point(self.y, -self.x)

    def unrotate(self, r):
        return self.rotate((4 - r) % 4)


@dataclass
class Linked:
    permanent_id: int = 0
    inner_id: int = 0
    name: str = ''
    offset: int = 0
    word_size: int = 0


@dataclass
class Component:
    kind: str
    position: Point
    rotation: int = 0
    permanent_id: int = 0
    user_label: str = ''
    custom_string: str = ''
    settings: list = field(default_factory=list)
    buffer_size: int = 0            # bytes
    ui_order: int = 0
    word_size: int = 0              # bits
    is_immutable: bool = False
    gate_variant: int = -1          # -1 = 最小门变体
    delay_variant: int = 0
    is_little_endian: bool = False
    init_data: str = 'zeroes'
    linked: list = field(default_factory=list)
    selected_programs: dict = field(default_factory=dict)
    custom_id: int = 0
    custom_word_sizes: dict = field(default_factory=dict)


@dataclass
class Wire:
    start: Point
    segments: list                  # [(direction, length)]
    color: int = 0
    comment: str = ''

    def points(self):
        p = self.start
        yield p
        for d, n in self.segments:
            dx, dy = DIRECTIONS[d]
            for _ in range(n):
                p = Point(p.x + dx, p.y + dy)
                yield p

    @property
    def finish(self):
        p = self.start
        for d, n in self.segments:
            dx, dy = DIRECTIONS[d]
            p = Point(p.x + dx * n, p.y + dy * n)
        return p


@dataclass
class Save:
    custom_id: int = 0
    gate: int = 99999
    delay: int = 99999
    menu_visible: bool = True
    clock_speed: int = 10_000_000
    dependencies: list = field(default_factory=list)
    description: str = ''
    player_data: bytes = b''
    design: list = field(default_factory=lambda: [[0] * 32 for _ in range(32)])
    components: list = field(default_factory=list)
    wires: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# 读取
# ---------------------------------------------------------------------------

class _Reader:
    def __init__(self, data):
        self.d = data
        self.i = 0

    def take(self, fmt):
        v = struct.unpack_from('<' + fmt, self.d, self.i)
        self.i += struct.calcsize('<' + fmt)
        return v if len(v) > 1 else v[0]

    def u8(self): return self.take('B')
    def u16(self): return self.take('H')
    def i16(self): return self.take('h')
    def u32(self): return self.take('I')
    def u64(self): return self.take('Q')
    def i64(self): return self.take('q')
    def boolean(self): return self.u8() != 0

    def string(self):
        n = self.u16()
        s = self.d[self.i:self.i + n]
        self.i += n
        return s.decode('latin-1')

    def point(self):
        return Point(self.i16(), self.i16())

    def seq_u8(self):
        n = self.u16()
        s = self.d[self.i:self.i + n]
        self.i += n
        return bytes(s)


def _read_component(r):
    idx = r.u16()
    kind = KIND_NAMES[idx] if idx < len(KIND_NAMES) else 'none'
    c = Component(kind=kind, position=r.point())
    c.rotation = r.u8()
    c.permanent_id = r.i64()
    c.user_label = r.string()
    c.custom_string = r.string()
    c.settings = [r.u64() for _ in range(r.u16())]
    c.buffer_size = r.i64()
    c.ui_order = r.i16()
    c.word_size = r.i64()
    c.is_immutable = r.boolean()
    c.gate_variant = r.i64()
    c.delay_variant = r.i64()
    c.is_little_endian = r.boolean()
    c.init_data = INIT_DATA[r.u8()]
    for _ in range(r.u16()):
        c.linked.append(Linked(r.i64(), r.i64(), r.string(), r.i64(), r.i64()))
    for _ in range(r.u16()):
        k = r.string()
        c.selected_programs[k] = r.string()
    if kind == 'custom':
        c.custom_id = r.i64()
        for _ in range(r.u16()):
            a = r.i64()
            c.custom_word_sizes[a] = r.i64()
    if kind in MIN_ONE_WATCHED and not c.linked:
        c.linked.append(Linked())
    defaults = DEFAULT_SETTINGS.get(kind, [])
    while len(c.settings) < len(defaults):
        c.settings.append(defaults[len(c.settings)])
    return c


def _read_wire(r):
    color = r.u8()
    comment = r.string()
    start = r.point()
    segments = []
    while True:
        seg = r.u16()
        direction = seg >> 13
        length = seg & 0x1FFF
        if length == 0:
            break
        segments.append((direction, length))
    return Wire(start, segments, color, comment)


def parse(data):
    """将 circuit.data 字节解析为 Save；只接受版本 16。"""
    if not data:
        return Save()
    if data[0] != VERSION:
        raise ValueError('unsupported save version %d (only %d)' % (data[0], VERSION))
    raw = snappy.decompress(data[1:])
    r = _Reader(raw)
    s = Save()
    s.custom_id = r.i64()
    r.u32()
    s.gate = r.i64()
    s.delay = r.i64()
    s.menu_visible = r.boolean()
    s.clock_speed = r.u64()
    s.dependencies = [r.i64() for _ in range(r.u16())]
    s.description = r.string()
    r.u8()
    r.u16()
    s.player_data = r.seq_u8()
    r.string()
    if s.custom_id != 0:
        for x in range(32):
            for y in range(16):
                v = r.u8()
                s.design[x][2 * y] = v & 0xF0
                s.design[x][2 * y + 1] = (v << 4) & 0xFF
    s.components = [_read_component(r) for _ in range(r.i64())]
    s.wires = [_read_wire(r) for _ in range(r.i64())]
    if r.i != len(raw):
        raise ValueError('trailing bytes: %d of %d consumed' % (r.i, len(raw)))
    return s


# ---------------------------------------------------------------------------
# 写入
# ---------------------------------------------------------------------------

class _Writer:
    def __init__(self):
        self.b = bytearray()

    def put(self, fmt, *v):
        self.b += struct.pack('<' + fmt, *v)

    def u8(self, v): self.put('B', v)
    def u16(self, v): self.put('H', v)
    def i16(self, v): self.put('h', v)
    def u32(self, v): self.put('I', v)
    def u64(self, v): self.put('Q', v & 0xFFFFFFFFFFFFFFFF)
    def i64(self, v): self.put('q', v)
    def boolean(self, v): self.u8(1 if v else 0)

    def string(self, s):
        raw = s.encode('latin-1')
        self.u16(len(raw))
        self.b += raw

    def point(self, p):
        self.i16(p.x)
        self.i16(p.y)


def _write_component(w, c):
    w.u16(KIND_IDS[c.kind])
    w.point(c.position)
    w.u8(c.rotation)
    w.i64(c.permanent_id)
    w.string(c.user_label)
    w.string(c.custom_string)
    w.u16(len(c.settings))
    for s in c.settings:
        w.u64(s)
    w.i64(c.buffer_size)
    w.i16(c.ui_order)
    w.i64(c.word_size)
    w.boolean(c.is_immutable)
    w.i64(c.gate_variant)
    w.i64(c.delay_variant)
    w.boolean(c.is_little_endian)
    w.u8(INIT_DATA.index(c.init_data))
    w.u16(len(c.linked))
    for l in c.linked:
        w.i64(l.permanent_id)
        w.i64(l.inner_id)
        w.string(l.name)
        w.i64(l.offset)
        w.i64(l.word_size)
    w.u16(len(c.selected_programs))
    for k, v in c.selected_programs.items():
        w.string(k)
        w.string(v)
    if c.kind == 'custom':
        w.i64(c.custom_id)
        w.u16(len(c.custom_word_sizes))
        for a, b in c.custom_word_sizes.items():
            w.i64(a)
            w.i64(b)


def _write_wire(w, wire):
    w.u8(wire.color)
    w.string(wire.comment)
    w.point(wire.start)
    for d, n in wire.segments:
        assert 0 < n < 0x2000 and 0 <= d < 8
        w.u16((d << 13) | n)
    w.u16(0)


def serialize(s):
    """将 Save 序列化为 circuit.data 字节（版本 16）。"""
    w = _Writer()
    w.i64(s.custom_id)
    w.u32(0)
    w.i64(s.gate)
    w.i64(s.delay)
    w.boolean(s.menu_visible)
    w.u64(s.clock_speed)
    w.u16(len(s.dependencies))
    for d in s.dependencies:
        w.i64(d)
    w.string(s.description)
    w.u8(0)
    w.u16(0)
    w.u16(len(s.player_data))
    w.b += s.player_data
    w.string('')
    if s.custom_id != 0:
        for x in range(32):
            for y in range(16):
                w.u8((s.design[x][2 * y] & 0xF0) | (s.design[x][2 * y + 1] >> 4))
    comps = [c for c in s.components if not c.kind.startswith('deleted') and c.kind != 'none']
    w.i64(len(comps))
    for c in comps:
        _write_component(w, c)
    wires = [x for x in s.wires if x.segments]
    w.i64(len(wires))
    for x in wires:
        _write_wire(w, x)
    return bytes([VERSION]) + snappy.compress(bytes(w.b))


def raw_bytes(data):
    """解压 circuit.data，返回其正文（用于往返检查）。"""
    return snappy.decompress(data[1:])


def load(path):
    with open(path, 'rb') as fh:
        return parse(fh.read())


def dump(path, save):
    with open(path, 'wb') as fh:
        fh.write(serialize(save))


# ---------------------------------------------------------------------------
# JSON 转储
# ---------------------------------------------------------------------------

def to_json(s):
    def comp(c):
        d = {'kind': c.kind, 'pos': [c.position.x, c.position.y], 'rot': c.rotation, 'id': c.permanent_id,
             'label': c.user_label, 'custom_string': c.custom_string, 'settings': c.settings,
             'buffer_size': c.buffer_size, 'ui_order': c.ui_order, 'word_size': c.word_size,
             'immutable': c.is_immutable, 'gate_variant': c.gate_variant, 'delay_variant': c.delay_variant,
             'little_endian': c.is_little_endian, 'init_data': c.init_data,
             'linked': [vars(l) for l in c.linked], 'selected_programs': c.selected_programs}
        if c.kind == 'custom':
            d['custom_id'] = c.custom_id
            d['custom_word_sizes'] = c.custom_word_sizes
        return d

    def wire(x):
        f = x.finish
        return {'start': [x.start.x, x.start.y], 'finish': [f.x, f.y], 'segments': x.segments,
                'color': x.color, 'comment': x.comment}

    return {'custom_id': s.custom_id, 'gate': s.gate, 'delay': s.delay, 'menu_visible': s.menu_visible,
            'clock_speed': s.clock_speed, 'dependencies': s.dependencies, 'description': s.description,
            'player_data_len': len(s.player_data), 'components': [comp(c) for c in s.components],
            'wires': [wire(x) for x in s.wires]}


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    for path in sys.argv[1:]:
        data = open(path, 'rb').read()
        s = parse(data)
        again = serialize(s)
        ok = raw_bytes(again) == raw_bytes(data)
        print('%s: %d components, %d wires, roundtrip %s' % (path, len(s.components), len(s.wires), 'OK' if ok else 'MISMATCH'))
        if '--json' in sys.argv:
            print(json.dumps(to_json(s), ensure_ascii=False, indent=1))
