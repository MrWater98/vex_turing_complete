# 11-fpu-f — F 扩展（单精度）

## 目的

实现 IEEE-754 binary32 的 30 种运算及浮点寄存器文件 f0–f31。寄存器宽度为 64 位，单精度值使用 NaN-boxing。D 扩展（12-fpu-d）会将相同结构扩展到 53 位尾数，因此子模块应支持更换位宽后复用。

## 子模块

每项均对应一个 Foundry 元件和一个 Hub 上传单元。

| 目录/元件 | 功能 |
|---|---|
| `RV64G/FRegFile` | 与 04-regfile 类似，使用 RAM；32×64 位，三个读端口（rs1、rs2、rs3），无 x0 特例 |
| `RV64G/F_Unpack` | 将 32 位拆为符号 1 位、指数 8 位、尾数 24 位（含隐藏的 1）及 zero/inf/nan/qnan/subnormal 分类标志。NaN-box 检查：高 32 位不全为 1 时视为 canonical NaN |
| `RV64G/F_Pack` | 将符号、指数、尾数组合为 32 位并执行 NaN-boxing（高 32 位全 1） |
| `RV64G/F_Round` | 输入尾数和 guard/round/sticky 位，按 5 种 rm 模式舍入；处理溢出/下溢并输出 NV/DZ/OF/UF/NX 标志 |
| `RV64G/F_AddSub` | 对齐指数（用 Lsr 移动较小项并收集 sticky 位）、尾数加减、规格化（用 Clz 找前导零，再用 Lsl）及 F_Round |
| `RV64G/F_Mul` | 24×24 尾数乘法（一个 `Mul(64)`）、指数相加、规格化和 F_Round |
| `RV64G/F_Div` | 可将 24 位恢复除法展开为 26 级组合逻辑（24 位商加 guard/round，每级使用 Sub、Less_u、Mux）；也可用游戏 `Div(64)` 一次计算 `(尾数<<26)/尾数`，再通过 `Mod!=0` 得到 sticky 位，后者电路更小 |
| `RV64G/F_Sqrt` | 26 级逐位平方根组合电路；不能用 Div 元件和牛顿迭代替代，需构建组合级联 |
| `RV64G/F_FMA` | 精确融合乘加：48 位乘积与对齐后的加数（最多 74 位）分配到两个 64 位元件处理。首版可先实现标明为“非融合”的 Mul 后接两次 AddSub 舍入 |
| `RV64G/F_Cmp` | feq/flt/fle（quiet NaN 的 feq 不置 NV，signaling NaN 会置 NV），以及 fmin/fmax（含 NaN 规则和 -0 < +0） |
| `RV64G/F_Cvt` | fcvt.w/wu/l/lu.s（舍入；越界时输出最大/最小值并置 NV）；整数转浮点时用 Clz 规格化，再执行 F_Round |
| `RV64G/F_Misc` | fsgnj/fsgnjn/fsgnjx、fmv.x.w（符号扩展）、fmv.w.x（NaN-box）和 fclass（10 位掩码） |

## 顶层连接

```text
rs1_f, rs2_f, rs3_f  ← FRegFile
运算选择 ← 02-decoder 的 is_opfp/is_fma/is_loadfp/is_storefp、funct7[6:2]、rs2（转换类型）和 funct3
结果 mux → FRegFile 写入（freg_write）或整数 rd 写入（fcvt.w*、fmv.x.w、feq/flt/fle、fclass）
fflags_set → 09-csr 做 OR 累积；funct3 == 111 时，舍入模式 rm 使用 09-csr 的 frm
```

## 建议实现顺序

1. FRegFile、F_Unpack、F_Pack、F_Misc、flw/fsw（复用 LSU），先打通数据移动。
2. F_Cmp、F_Cvt（整数与浮点互转）。
3. F_Round、F_AddSub、F_Mul。
4. F_Div（使用 Div 元件方案）、F_Sqrt。
5. F_FMA（先做非融合版本，再实现融合版本）。

## 验证

- 1.0f=0x3F800000、2.0f=0x40000000：fadd 结果应为 0x40400000（3.0f）。
- 0.1f + 0.2f = 0x3E99999A（RNE）。
- 1.0f / 3.0f = 0x3EAAAAAB。
- sqrt(2.0f) = 0x3FB504F3。
- fcvt.w.s(-1.5f, rtz)=-1；rne=-2、rdn=-2、rup=-1。
- fclass(-0.0f)=0x008，fclass(+inf)=0x080，fclass(qNaN)=0x200。
- 可用 Python `struct` 生成参考值：`struct.unpack('<I', struct.pack('<f', v))`。

## 状态

目前为概述；开始实现各子模块时再分别补充详细文档。
