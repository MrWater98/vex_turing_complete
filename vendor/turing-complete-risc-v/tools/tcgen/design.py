# -*- coding: utf-8 -*-
"""将网表转换为布局、布线和 Save。

布线规则（根据游戏中的观察）：
  - 导线只在端点处连接。交叉不代表连接；一条线的端点碰到另一条线的中段时会形成 T 形连接。
  - 因此只需避免经过其他网络的端点。

布局：元件沿单列（x=0）纵向排列，每个元件占用独立的行带。输入引脚在左、输出引脚在右，因此每行至多有一个输入引脚和一个输出引脚。
布线：每个网络独占一个右侧轨道 x、一个顶部主干 y 和一个左侧轨道 x。
  一条主线从输出引脚向右到右轨道、向上到顶部主干、向左到左轨道，再向下到最低的接收端所在行，最后向右连接该接收端。其他接收端从左轨道分支。
  多驱动网络（开关总线）由最低的驱动端构成主线，其他驱动端接到右侧轨道。
"""
import random
from dataclasses import dataclass, field

from .pins import PINS, pin
from tcsave.save16 import Component, Point, Save, Wire, serialize

DIR_R, DIR_D, DIR_L, DIR_U = 0, 2, 4, 6


@dataclass
class Comp:
    name: str
    kind: str
    word_size: int = 1
    settings: list = field(default_factory=list)
    label: str = ''
    ui_order: int = 0
    buffer_size: int = 0
    init_data: str = 'zeroes'
    little_endian: bool = False
    x: int = 0
    y: int = 0

    def pin_at(self, pname):
        (dx, dy), _ = pin(self.kind, pname)
        return Point(self.x + dx, self.y + dy)


@dataclass
class Net:
    name: str
    drivers: list = field(default_factory=list)   # [(comp, pin)]
    sinks: list = field(default_factory=list)     # [(comp, pin)]


class Design:
    def __init__(self, name, custom_id=None, description=''):
        self.name = name
        self.custom_id = custom_id if custom_id is not None else random.getrandbits(62) | 1
        self.description = description
        self.comps = []
        self.by_name = {}
        self.nets = []
        self.net_by_name = {}

    # ----- 网表 -----
    def add(self, name, kind, ws=1, settings=None, label='', **kw):
        if kind not in PINS:
            raise KeyError('unknown kind %s' % kind)
        c = Comp(name, kind, ws, list(settings or []), label or '', **kw)
        if name in self.by_name:
            raise KeyError('duplicate component %s' % name)
        self.comps.append(c)
        self.by_name[name] = c
        return c

    def net(self, name):
        if name not in self.net_by_name:
            n = Net(name)
            self.nets.append(n)
            self.net_by_name[name] = n
        return self.net_by_name[name]

    def connect(self, net_name, *endpoints):
        """endpoints 是 'comp.pin' 字符串。输出引脚为驱动端，输入引脚为接收端。"""
        n = self.net(net_name)
        for ep in endpoints:
            cname, pname = ep.split('.')
            c = self.by_name[cname]
            _, direction = pin(c.kind, pname)
            (n.drivers if direction == 'out' else n.sinks).append((c, pname))
        return n

    # ----- 布局 -----
    def place(self, gap=1, order=None):
        """将元件纵向放在一列中；可用 order 指定顺序。"""
        comps = [self.by_name[n] for n in order] if order else self.comps
        y = 0
        for c in comps:
            r0, r1 = PINS[c.kind]['rows']
            c.x = 0
            c.y = y - r0
            y = c.y + r1 + 1 + gap
        self.height = y

    # ----- 布线 -----
    def route(self):
        wires = []
        n_nets = len(self.nets)
        max_right = max(c.x + PINS[c.kind]['cols'][1] for c in self.comps)
        min_left = min(c.x + PINS[c.kind]['cols'][0] for c in self.comps)
        min_row = min(c.y + PINS[c.kind]['rows'][0] for c in self.comps)
        right_lane0 = max_right + 3
        left_lane0 = min_left - 3
        highway0 = min_row - 3
        self.bounds = None
        for i, n in enumerate(self.nets):
            if not n.drivers:
                raise ValueError('net %s has no driver' % n.name)
            if not n.sinks:
                continue
            rlane = right_lane0 + i
            llane = left_lane0 - i
            hwy = highway0 - i
            drivers = sorted(n.drivers, key=lambda cp: cp[0].pin_at(cp[1]).y)
            sinks = sorted(n.sinks, key=lambda cp: cp[0].pin_at(cp[1]).y)
            src = drivers[-1][0].pin_at(drivers[-1][1])          # 最低处的驱动端
            last = sinks[-1][0].pin_at(sinks[-1][1])              # 最低处的接收端
            # 主线：src → 右轨道 → 顶部主干 → 左轨道 → 最后一个接收端
            segs = []
            segs.append((DIR_R, rlane - src.x))
            segs.append((DIR_U, src.y - hwy))
            segs.append((DIR_L, rlane - llane))
            segs.append((DIR_D, last.y - hwy))
            segs.append((DIR_R, last.x - llane))
            wires.append(Wire(src, [s for s in segs if s[1] > 0], color=0, comment=''))
            # 其他驱动端：用短线连接到右轨道
            for c, p in drivers[:-1]:
                q = c.pin_at(p)
                wires.append(Wire(q, [(DIR_R, rlane - q.x)]))
            # 其他接收端：从左轨道分支
            for c, p in sinks[:-1]:
                q = c.pin_at(p)
                wires.append(Wire(Point(llane, q.y), [(DIR_R, q.x - llane)]))
        self.wires = wires
        xs = [p.x for w in wires for p in (w.start, w.finish)] + [c.x for c in self.comps]
        ys = [p.y for w in wires for p in (w.start, w.finish)] + [c.y for c in self.comps]
        self.bounds = (min(xs), min(ys), max(xs), max(ys))
        return wires

    # ----- 校验 -----
    def validate(self):
        """检查所有导线端点都落在所属网络的引脚或导线上，并且没有经过其他网络的端点。"""
        pin_owner = {}
        for n in self.nets:
            for c, p in n.drivers + n.sinks:
                q = c.pin_at(p)
                if q in pin_owner and pin_owner[q] is not n:
                    raise ValueError('pin %s used by two nets' % (q,))
                pin_owner[q] = n
        # 每个网络的点集合
        net_points = {}
        net_ends = {}
        wire_net = {}
        for n in self.nets:
            net_points[n.name] = set()
            net_ends[n.name] = set()
        # 导线到网络的映射：若端点是引脚，则使用该引脚所属的网络
        for w in self.wires:
            owner = None
            for e in (w.start, w.finish):
                if e in pin_owner:
                    owner = pin_owner[e]
            wire_net[id(w)] = owner
        # 对没有接触引脚的分支，迭代查找它所接触的主线所属网络
        changed = True
        while changed:
            changed = False
            for w in self.wires:
                if wire_net[id(w)] is not None:
                    continue
                for w2 in self.wires:
                    n2 = wire_net[id(w2)]
                    if n2 is None or w2 is w:
                        continue
                    pts = set(w2.points())
                    if w.start in pts or w.finish in pts:
                        wire_net[id(w)] = n2
                        changed = True
                        break
        for w in self.wires:
            n = wire_net[id(w)]
            if n is None:
                raise ValueError('wire %s->%s belongs to no net' % (w.start, w.finish))
            net_points[n.name].update(w.points())
            net_ends[n.name].update((w.start, w.finish))
        # 若其他网络的端点落在当前网络的路径上，则报错
        for a in self.nets:
            for b in self.nets:
                if a is b:
                    continue
                bad = net_ends[a.name] & net_points[b.name]
                if bad:
                    raise ValueError('net %s endpoint %s lies on net %s' % (a.name, sorted(bad)[0], b.name))
        # 不允许经过其他网络的引脚
        for n in self.nets:
            for q, owner in pin_owner.items():
                if owner is not n and q in net_points[n.name]:
                    raise ValueError('net %s passes over pin %s of net %s' % (n.name, q, owner.name))
        # 不允许经过元件本体（引脚除外）
        bodies = {}
        for c in self.comps:
            c0, c1, r0, r1 = PINS[c.kind]['body']
            for yy in range(c.y + r0, c.y + r1 + 1):
                for xx in range(c.x + c0, c.x + c1 + 1):
                    bodies[Point(xx, yy)] = c
        for n in self.nets:
            for q in net_points[n.name]:
                if q in bodies and q not in pin_owner:
                    raise ValueError('net %s passes over body of %s at %s' % (n.name, bodies[q].name, q))
        return True

    # ----- 输出 -----
    def to_save(self, foundry=True):
        s = Save()
        s.custom_id = self.custom_id if foundry else 0
        s.description = self.description
        s.gate = 99999
        s.delay = 99999
        s.menu_visible = True
        s.clock_speed = 10_000_000
        if foundry:
            for x in range(15, 19):           # Hub 元件的基础图案（4×6 格）
                for y in range(13, 19):
                    s.design[x][y] = 0x90
        ids = set()
        for c in self.comps:
            pid = random.getrandbits(62) | 1
            while pid in ids:
                pid = random.getrandbits(62) | 1
            ids.add(pid)
            comp = Component(kind=c.kind, position=Point(c.x, c.y), rotation=0, permanent_id=pid,
                             user_label=c.label, settings=list(c.settings), word_size=c.word_size,
                             ui_order=c.ui_order, buffer_size=c.buffer_size, init_data=c.init_data,
                             is_little_endian=c.little_endian, gate_variant=-1, delay_variant=0)
            s.components.append(comp)
        s.wires = list(self.wires)
        return s

    def build(self, foundry=True, order=None):
        self.place(order=order)
        self.route()
        self.validate()
        return self.to_save(foundry)

    def write(self, path, foundry=True, order=None):
        data = serialize(self.build(foundry, order))
        with open(path, 'wb') as fh:
            fh.write(data)
        return data
