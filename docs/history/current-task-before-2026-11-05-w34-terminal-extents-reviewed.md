# 当前任务入口完整归档

来源：CURRENT_TASK.md；日期：2026-11-05（Asia/Shanghai）。以下为四条M2延伸几何验收前入口全文；实际G1/G2/Q1已另行归档通过。

---

# 当前任务

## 当前目标与状态

**M3固定窗口的R01/R02/B01及整体无明显漏段已通过实际确认单归档。已接续本区8处V2、4处V1的批准，并将四条细M2沿原出口补到可见线端，现只待新增连续范围几何验收。**

- [M3实际归档](docs/assets/w34-m3-remainder-v1/review/review-record.md) · [M3窗口已审工作基线](benchmarks/w34-m3-reviewed-v2/working-baseline.json) · [10片段已审覆盖表](benchmarks/w34-m3-reviewed-v2/scoped-coverage.json)。G1/G2和整体Q1通过，范围M3=[180,2120,1280,2490]。批准只为所示几何及无明显漏段，不是全部接口或整芯片穷尽覆盖。
- [最新53金属工作候选](docs/assets/w34-terminal-extension-v1/work/index.html) · [唯一接续请求](benchmarks/w34-terminal-extension-v1/next-request.json) · [本轮验证](benchmarks/w34-terminal-extension-v1/verification.json)。M1=11/M2=17/M3=25，34条已审局部连接、188候选设计孔精确保留，物理孔数/尺寸仍未知。
- 本次仅为既有W34-M2-S01/S02/S03追加上方局部范围，S04追加下方范围；原生锚点、原骨架/短头、M1/M3/VIA全部保持。原窗口出口不当作物理终点，新可见线端也不当作已知电气端点。

## 唯一下一步：四条细M2延伸范围验收

- [固定复核单](docs/assets/w34-terminal-extension-v1/review/index.html)，预览 http://127.0.0.1:8772/w34-terminal-extension-v1/review/index.html 。包W34-TERMINAL-EXTENSION-20261105-V1，build=3784b60f6a8b4a8badd22b1c7330919f。
- G1只看S01/S02/S03上方新增长度、端部高低和相邻间隙；G2只看S04下方新增连续范围及邻线间隙；整体Q1汇总。不重审旧短头、M3窗口或已审VIA，不要求逐孔数。
- M2新增原生观察：S01约[309,1750]→[313,1870]；S02约[393,1750]→[399,1870]；S03约[479,1700]→[483,1870]；S04约[795,2840]→[806,3120]→[814,3400]。端点坐标为AI可见线端观察，非精确量测或电气终止结论。
- 新设计局部块只延伸连续段，旧足迹均保留；S01/S02顶到设计y50，S03顶到y12，S04底到y1370，画布/原点不变。完整来源上下文和新旧同坐标图可切换；未对照片直接投影。
- 实际导出check归档后，先从M1侧核四个新端部附近是否有V1/承载。现未判断新孔，不得由几何延伸直接新增连接。

## 接口清点与质量门

- [本区接口和出口清点](benchmarks/w34-terminal-extension-v1/interface-sweep.json)：6条本区M2相关的8处V2及4处V1均接续原已审记录；四个短头V2已审，不重问。AI在原M2窗口[280,1870,850,2840]未识别额外明确V2组，不能升级为物理无孔。其它M1来源接触未穷尽。
- 当前只是四条已知线的连续延伸，包络[280,1650,850,3450]不是新矩形全部导体/孔的完整覆盖声明。大邻域内其它导体按上下文显示，不自动补连或并入清单。
- [显式局部修订请求](benchmarks/w34-terminal-extension-v1/request.json)仅列四个允许变化ID，[局部来源台账](benchmarks/w34-terminal-extension-v1/local-parts-ledger.json)完整继承旧记录并追加四行。统一入口技术门及next-request精确重放通过。
- 18项直接不变量检查通过：53稳定ID保持；只四个限定M2追加块；四个旧feature字段/足迹保留；M1/M3/V1/V2对象、34接口及裁决、188孔、画布/原点保持；README/site当前冻结哈希保持。固定页面及原图/规则图浏览器加载通过，未替人审批。
- 前轮114项相关软件测试及定向Ruff已通过；本轮为数据与稿件更新，未重复扩大测试。旧历史总回归的README哈希漂移FAIL原样保持，不报全套PASS。
- 金属/VIA skill仍LIMITED_TRIAL_V2；source_to_design_transform=null、geometry_adopted=false、net_edges=[]、complete_network=false。工程门不是物理真值/PDK DRC，不自动写共同GDS或完整网表。
- [本轮记录](docs/reviews/2026-11-05-w34-terminal-extension.md)。远端仍[6a217d5](https://github.com/XIAHONGYUU/SiliconEye/commit/6a217d54cf2962abe80a7b34b1bb14d03e630cc7)，后续工作留本地，未改README/site/gh-pages、AA/POLY/CT或规范注册表。

## 基线与历史

- [上一批联合几何基线](benchmarks/w34-joint-reviewed-v2/working-baseline.json)、[旧M2基线](benchmarks/w34-m2-reviewed-v2/working-baseline.json)、[四端身份](benchmarks/w34-short-terminal-reviewed-v2/identity-baseline.json)、[四条来源连接](benchmarks/w34-joint-geometry-v1/source-connection-baseline.json)继续有效，历史pending字段不重解释为当前待审批。
- [本次前入口完整归档](docs/history/current-task-before-2026-11-05-w34-M3-window-reviewed.md) · [更早入口](docs/history/current-task-before-2026-11-05-w34-joint-geometry-reviewed.md) · [固定确认协议](docs/review-sheet-protocol.md)。

## 必须接续的裁决与未知

- P1 上接 BU，P2/P3 的 L1/L2 本处不接 BR-R，P4/P5 接 R3/R4。只判局部，不推导异网。BF24/BF26 本处上接 BU；BF25 本处不接 BU/L1/L2，仍独立候选而非已确定悬空节点。BF24/26 下端、其余 23 指和细邻线仍未知。
- A/B 的 V1 身份及接 RT-M2-R01 已审；原生框 A=[3125,1930,3175,2010]、B=[3130,2775,3180,2845]，2×1 仍为设计假设。R02 其它 V1 未查清，不声明无孔。
- 原 9 个 V2：R01/R02 上端接 RT-M3-UP、下端接 RT-M3-DOWN；N1→C-M3-L01、03→T01、04→T02、05→E1、06→E2。05/06 本处 M2 不连续，不推导全局异网。08 无明确 V2、三条弱 M3 不补建是 AI 处置，非人审不存在。
- C06 原生框 [2933,2140,2977,2175] 跨旧走廊 x2940；保持原框／裁决。旧 M2/V2/M3 覆盖仅限旧声明范围，不升级五层穷尽覆盖。
- BR-R work-v3：S1 只下扩 200px，S2 只加原 M1 的 BRR-DOWN/R3/R4 局部块，S3 另加 L1/L2；原骨架／宽度／四块及旧对象、11 接口、46 孔保持。详见[前入口全文](docs/history/current-task-before-2026-10-29-R3-R4-left.md)。
- A 右支约原生 x5175 下拐；B 左支与 R3/R4 左端原先均为出界而非物理终点。旧骨架 B 近似 y2800 与横带约 y2780 的差别不能用于移动孔；BF25、细邻条与完整返回仍未知。
- 外方阵宏观搜索不等于内部 VIA 精度；ORB 保留点 P95 约129px及首版触带已拒绝。旧九对 V1/V2 同孔拟合和 4.52px 残差不可复活；V1 从 M1 侧、V2 从 M2 侧判断。
- 其它区域 A={T3,L2}/B={T1,L4}、H1/H2 局部隔离、U1/U2 同 M1、U1/U3 经 V1 接 N2、U3 CT→AA 环端子路径按历史保持，不转移到本走廊。
- [材料快照 v5](configs/joint-work-layer-v5.json)为 AA334/POLY696/CT10287；规范导体注册表仍[原33记录](docs/assets/conductive-stack-v2/model.json)。AA-F01951/1952、材料 H1/H2、边界 AA-F01744、S3-AA4-LEFT-SD-ACCESS 六处材料未知保持。物理工艺／尺度／孔数／极性／WL／阻值未知，自动网络导出禁止。



## 恢复

```bash
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/w34-terminal-extension-v1/next-request.json --output runs/新的四端接续目录
# 换成实际收到的下一份确认单，不自行填写人审答案。
.venv/bin/python -m silicon_eye.review_sheet check --package docs/assets/w34-terminal-extension-v1/review --decision /实际路径/review-decision.json --archive
```

不得自动重建README/site或发布gh-pages；几何批准与孔身份/承载批准分别保留。
