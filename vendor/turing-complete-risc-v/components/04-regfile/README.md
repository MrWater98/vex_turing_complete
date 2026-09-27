# 04-regfile — 整数寄存器文件

## 目的

实现 x0–x31 共 32 个 64 位寄存器。每个 tick 同时读取 rs1、rs2 并向 rd 写入；x0 恒为 0。

## 引脚

| 名称 | 宽度 | 方向 | 说明 |
|---|---:|---|---|
| `rs1`、`rs2`、`rd` | 5 | 输入 | 来自 02-decoder |
| `wdata` | 64 | 输入 | 来自 99-top 的结果 mux |
| `reg_write` | 1 | 输入 | 来自 02-decoder |
| `clk_en` | 1 | 输入 | 两相时钟时仅在执行 tick 为 1 |
| `rdata1`、`rdata2` | 64 | 输出 | 两个读端口的数据 |

## 内部设计（RAM 方案）

```text
rf:     Fast RAM(64)，32 个字（若按字节寻址，地址 = idx << 3，见 B4）；选择无延迟类型（B2）
load1:  Load port(64)，address = rs1，enable = On      → raw1
load2:  Load port(64)，address = rs2，enable = On      → raw2
store:  Store port(64)，address = rd，data = wdata，enable = reg_write & clk_en & (rd != 0)
rdata1 = Mux(64)(rs1 == 0 ? 0 : raw1)
rdata2 = Mux(64)(rs2 == 0 ? 0 : raw2)
```

`rd != 0` 可用 5 位 `Or` 树，或 `Equal(5)` 加 `Not` 实现。不写 x0 且其初值为 0 也能维持零值；增加读 mux 可避免依赖 RAM 初值。

### 备选方案（若 B1 不成立）

使用 31 个 `Register(64)`、写入译码器（若干 `Decoder_3`，将 5 位译码为 32 路）以及两组读取 `Mux(64)` 树（每组 31 个）。元件数量约增加一个数量级，但行为直接。

## 在游戏中构建

1. 放置 `RAM`，将宽度设为 64、容量设为 32。
2. 添加两个 `Load port` 和一个 `Store port`。
3. 使用 `Equal(5)` 与 `Constant(5)=0` 生成 `rs1_is_zero`、`rs2_is_zero`、`rd_is_zero`。
4. 写入使能为 `And(reg_write, clk_en, Not(rd_is_zero))`。
5. 添加两个读数据 mux。
6. 保存到 Foundry 的 `RV64G/RegFile`。

## 验证

- tick 1：rd=1、wdata=5、reg_write=1；tick 2：rs1=1，应得到 rdata1=5。
- 写入 rd=0、wdata=7、reg_write=1 后，读取 rs1=0 应得到 rdata1=0。
- 同一 tick 向 rd=2 写入并读取 rs2=2。若读到旧值，则符合单周期语义（B3）。游戏时钟说明内存在前一相读取、后一相写入；若读到新值，可用 `Register` 将写入延迟一个 tick。

## 状态

目前只有设计文档。游戏资料基本支持 B1（多端口）和 B3（先读后写）；使用 Fast RAM 可规避 B2 的不确定性。战役本身也以 RAM 实现寄存器文件。仍需在游戏中复核后定案。
