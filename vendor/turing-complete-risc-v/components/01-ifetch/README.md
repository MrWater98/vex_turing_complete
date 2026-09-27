# 01-ifetch — 程序 RAM 与指令取指

## 目的

从程序 RAM 读取 `pc` 指向的 32 位指令并传给译码器。哈佛架构将程序 RAM 与数据 RAM（07-lsu）分开；`fence.i` 实现为 nop。

## 引脚

| 名称 | 宽度 | 方向 | 说明 |
|---|---:|---|---|
| `pc` | 64 | 输入 | 来自 00-pc |
| `instr` | 32 | 输出 | 当前指令字，连接到 02-decoder |

## 内部设计

```text
prog_ram: 程序 RAM（游戏汇编的程序放在这里）；选用无延迟类型（待验证 B2），并检查 endianness（B7）
load:     Load port(32)，address = pc（字节地址），enable = On
instr   = load.out
```

若游戏 RAM 使用字地址而非字节地址（B4），则将 `pc >> 2` 作为地址。若读端口延迟一个 tick（B2），改用两相时钟：在取指 tick 读取并存入 `Register(32)`，在执行 tick 使用该值。

## 在游戏中构建

1. 放置 RAM（先尝试 Fast RAM）。此引擎没有独立的 Program 元件（可执行文件中没有 `com_program`）；RAM 充当程序存储器。点击元件的“编辑程序”图标打开 IDE，其中有 `spec.isa` 和 `.asm` 标签。
2. 添加 `Load port`，宽度设为 32，地址接 `pc`，enable 接 `On`。
3. 将输出标记为 `instr`。
4. 无需封装成 Foundry 元件，可直接放入顶层电路（程序 RAM 可能是关卡/架构提供的固定元件）。

## 验证

载入 `tests/encode_check.asm`，检查 `pc = 0` 时 `instr = 0x00500093`，`pc = 4` 时 `instr = 0xFFF00113`。若字节顺序颠倒，检查 B7 的端序设置是否重复应用。

## 状态

目前只有设计文档。字节寻址（B4）和按宽度配置的 Load port 是根据游戏战役文本推测的，见验证清单第 0 节。
