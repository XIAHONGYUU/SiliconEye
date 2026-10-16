# 不依赖Virtuoso的局部电路检查

本入口生成浏览器可打开的SVG、直接查看的PNG和结构化局部网表JSON；不依赖Virtuoso、PDK、仿真器或外部模型服务。

```bash
.venv/bin/silicon-eye annotate networks \
  --spec benchmarks/device-m1-m2-network-v2.json \
  -o runs/device-m1-m2-current-next
```

要求已有参数绑定的本机材料、配准和人工复核证据；输出必须是新目录。旧v1参数继续重放旧候选，v2参数显式绑定三份人工复核记录，适合生成当前解释。

## 图如何表示电路

- 每个MOS独立画出G、A、B、Bulk四个端子。N/P和源漏方向尚未确定，因此使用不带极性箭头的通用MOS符号，A/B不强行命名S/D。
- 相同网络标号表示连接：V3两个栅使用N3_G，共用扩散使用N3_M。
- 绿色表示人工确认的关系，蓝色虚线为候选，黄色提示未知。体端保持Bulk ?，不接地或默认短接扩散区。
- N3_G与N3_M分列是关系未知，不表示确认断开。图下方明确提示这一点。
- 图中的span/run只是图像支持代理，不是已测真实W/L；不换算μm。

主要文件：

| 文件 | 用途 |
| --- | --- |
| local-schematic.svg | 可缩放矢量电路图 |
| local-schematic.png | 图像预览 |
| local-netlist.json | 同一数据生成的器件/网络/事实/未知关系，非可仿真SPICE |
| manifest.json | 参数、人工裁决应用结果、源码哈希、证据及历史候选 |
| report.md | 连接表、电路图、照片对照和关键路径核查 |

当前检查包：[runs/device-m1-m2-current-v1r2/report.md](../runs/device-m1-m2-current-v1r2/report.md)，批量运行文件留本机。

## 人工裁决进入重跑

`network_reviews.py`读取参数中明确绑定的人工反馈，保留物理栅身份，并应用：

1. M为V3两MOS的共享扩散区。
2. G1/G2的局部poly端部不连；两个物理栅不合并。
3. 两栅至少经M2接到同一电气网络N3_G。
4. V1/V2细支路与U形M1在当前局部断开；此约束不扩大为全局不可能经M2相连。
5. 栅网络与M关系未知；旧N3_MG整体并网从当前网络中撤回，作为历史未批准假设保留。

缺失共享区批准、遗漏未知关系、相互冲突的裁决、AI伪装人工确认或不支持的确认类型均拒绝运行。候选M1并网若违反已确认局部断开也会失败；合法的其他层连接不能被局部M1断开直接否决。

## 关键路径核查进度

第1项“人工裁决进入实际输出”已实现。第2项已保留关键原生M1/M2上下文并记录分析，但未完成精确M2路径验证：

- M1左竖线与中间横线有接近/相连迹象，保留AI候选。
- 局部SIFT候选变换缩放近零，把多个源位置塌缩到同一目标点，已拒绝；不能把其残差0当对齐正确。
- 可见过孔阵列候选的跨层身份尚不够明确，未强行拟合M2变换。
- 两栅经M2同网继续采用人工确认；栅到M保持未知。需要的是关键落点之间的路径证据，不是逐CT数量验收。

检查参数及失败原因见[关键路径记录](../benchmarks/m2-key-path-review-v1.json)。原始照片和已批准mask不变；未生成带假模型的SPICE或仿真结果。

## 当前版本：公共栅与共享扩散区同网

2026-10-15用户“批准连接关系，继续推进”：追加
`benchmarks/device-gate-diffusion-feedback-v1.json`，以绑定的前轮图和报告为范围，
明确替代此前的G到M未知状态。旧反馈和历史输出保持原样。

```bash
.venv/bin/silicon-eye annotate networks \
  --spec benchmarks/device-m1-m2-network-v3.json \
  -o runs/device-m1-m2-connected-next
```

v3消费四份复核记录，统一为N3_GM。V3_Q1的G/B、V3_Q2的G/A同网，
仍保留两器件和两物理栅；旧N3_MG是历史AI候选，当前N3_GM来自人工批准。
这不确认其他蓝色映射、体端、源漏方向、精确M2路径或实际W/L。

当前检查包为`runs/device-m1-m2-connected-v1r1/report.md`。
下一步从V3三个局部信号网络的外部去向入手，优先检查N3_A/N3_B通向哪些邻接器件或金属分支，
同时保留体端及类型未知，不再重复追问已批准的G到M连接。

## V3外侧网络边界检查

```bash
.venv/bin/silicon-eye annotate networks \
  --spec benchmarks/device-network-boundary-v1.json \
  -o runs/device-network-boundary-next
```

复用当前已批准的四器件拓扑，仅增加原图观察；绑定前轮manifest并拒绝改变其端子网络。
输出无标注原生PNG、独立标号副本、左/右端局部和`network-boundary.json`。
M1用A-L/A-R、B-L/B-R标记上下横条端部；M2用P1-P4标记未配准结构，全部保持未分配。
坐标均为各自源照片的原生px，两个图没有共同像素坐标系，不能按同名位置叠加接线。

`critical_views[].observations`只允许AI候选窗口，明确窗口坐标、建议网络（未配准时必须空）、
观察及未知说明。窗口不改变材料或网表，精确间隙和CT计数不是本阶段验收目标。
当前证据入口为`runs/device-network-boundary-v1r1/report.md`；需先核对M2结构与V3的身份对应。

## 上层走线及器件组层次

```bash
.venv/bin/python -m silicon_eye.upper_routing_review \
  --spec benchmarks/upper-routing-review-v1.json \
  -o runs/upper-routing-review-next
```

本入口复用networks导出，额外消费绑定的P2身份反馈，输出层次总览SVG/PNG、
M3/M4原生窗口与观察副本、M2→M3局部平移诊断、拟合/留出结构原生图和upper-routing.json。
身份反馈仅决定对象对应，不改变端子网络；当前拓扑与前轮逐项核验一致。

宏观平移由一个AI阵列对应拟合、一个短段对应留出检查；亮支持分位敏感性不能当精度置信区间。
P2上端靠近M3横向束下缘是路线候选，不是确认的单根走线或过孔。
另一条P3/S3/V4链只有形状/空间线索；M3/M4未配准，与P2连接未知。

层次图在同一页展示V3两MOS、已确认N3_GM、外侧候选网络及上层走线对象，
不将多轨束压成单一网络，也不从金属宽度推断电源或电路功能。
当前检查包为`runs/upper-routing-review-v1r2/report.md`。
