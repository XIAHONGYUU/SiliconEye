# 当前任务入口完整归档

来源：CURRENT_TASK.md；日期：2026-11-05（Asia/Shanghai）。以下为四处V1搜索目标裁决前入口全文。实际导出已明确四处均为“非孔”；旧待裁决文字仅为历史。

---

# 当前任务

## 当前目标与状态

**四条M2延伸几何已由实际确认单G1/G2/Q1通过归档。本次从M1侧检查四个新端部邻域，AI尚不能可靠辨认V1；仅生成身份搜索复核单，模型未新增孔、金属或连接。**

- [延伸几何实际归档](docs/assets/w34-terminal-extension-v1/review/review-record.md) · [已审范围工作基线](benchmarks/w34-terminal-reviewed-v2/working-baseline.json)。S01/S02/S03上方和S04下方连续范围通过；原生锚点/原骨架和已审短头保留。批准不是新端部孔身份或电气终点。
- [当前53金属工作模型](docs/assets/w34-terminal-extension-v1/work/index.html) · [几何接续请求](benchmarks/w34-terminal-extension-v1/next-request.json)。M1=11/M2=17/M3=25，34条已审局部连接、188候选设计孔保持。当前模型与本次检查前逐字节一致。
- [原M3固定窗口基线](benchmarks/w34-m3-reviewed-v2/working-baseline.json)及10片段来源/几何批准继续有效，不扩为全部接口或全芯片覆盖。四个短头的V2、旧4处V1等均不重审。

## 唯一下一步：四处M1搜索框的V1身份裁决

- [固定VIA确认单](docs/assets/w34-terminal-v1-inspection-v1/review/index.html)，预览 http://127.0.0.1:8772/w34-terminal-v1-inspection-v1/review/index.html 。包W34-TERMINAL-V1-IDENTITY-20261105-V1，build=baa23ce29a0445b2a9ae7a5d88e82e37。
- N1/N2/N3对应上方三个搜索邻域；S1为下方邻域。**只问M1橙框里能否辨认V1**：通过表示可确认有V1；不是孔/选框偏了选择需修改并说明；看不清可选不确定。本次没有重复整体汇总题。
- M1原生搜索框：N1=[307,1728,347,1790]；N2=[398,1728,438,1790]；N3=[486,1685,520,1745]；S1=[803,3345,853,3445]。这些是AI搜索邻域，不是已经检出的孔组或合格精确投影。
- 页面保留M1大邻域、邻线放大、未标注图及独立M2已审线端上下文；M2只作参照，不能作为V1来源。相邻细线/金属亮边/拍屏纹理为替代解释。AI目前不能可靠消除这些歧义，因此不得写成已确认孔。
- [观察记录](benchmarks/w34-terminal-v1-inspection-v1/observations.json)中identity_confirmed/connection_confirmed/lower_metal_id/upper_metal_id均为null；context_m2_id仅供定位，不是承载批准。**即使身份通过，本次也不批准接哪条M2。**
- 实际导出check归档后：通过者再核M1承载与M2对应，必要时补建M1；不确定者保留null；选框错误则按反馈修搜索范围。未有承载批准前不新增模型接口。

## 来源与质量门

- [来源图台账](benchmarks/w34-terminal-v1-inspection-v1/view-provenance.json)记录每张照片哈希/原生裁图范围，M1/M2分开显示，不直接叠图。[本轮检查](benchmarks/w34-terminal-v1-inspection-v1/verification.json)有12项来源/状态不变量检查通过，不代表AI孔识别成功。
- 四个M1框均完整落在对应宽图与放大图内；所有新身份/承载字段为null；旧34连接、188候选孔及禁止自动网表/共同采用状态保持；README/site当前冻结哈希保持。本次未变生产代码或模型几何，未重复扩大软件测试。
- 固定包manifest与证据文件校验通过；浏览器检查M1宽图/放大图、下方M2上下文加载正常，未替人点击审批。M1来源窗口中未明确辨认不等于无孔。
- 前轮四端几何18项检查/统一入口重放通过，先前114项软件测试及定向Ruff通过。历史总回归README哈希漂移FAIL保持，未宣称整套PASS。
- 金属/VIA skill仍LIMITED_TRIAL_V2；source_to_design_transform=null、geometry_adopted=false、net_edges=[]、complete_network=false。工程检查不替代真实PDK DRC或物理身份判断。
- [本轮记录](docs/reviews/2026-11-05-w34-terminal-v1-inspection.md)。远端仍[6a217d5](https://github.com/XIAHONGYUU/SiliconEye/commit/6a217d54cf2962abe80a7b34b1bb14d03e630cc7)，后续工作留本地，未改README/site/gh-pages、AA/POLY/CT或规范注册表。

## 基线与历史

- [原接口和出口清点](benchmarks/w34-terminal-extension-v1/interface-sweep.json)接续本区8处V2和4处V1；原M2窗口未见额外明确V2为AI观察，非物理无孔。四条新延伸端部不在其已审接口覆盖之内。
- [旧联合基线](benchmarks/w34-joint-reviewed-v2/working-baseline.json)、[旧M2基线](benchmarks/w34-m2-reviewed-v2/working-baseline.json)、[四端身份](benchmarks/w34-short-terminal-reviewed-v2/identity-baseline.json)、[四条来源连接](benchmarks/w34-joint-geometry-v1/source-connection-baseline.json)继续有效；旧pending字段是提交历史。
- [本次前入口全文](docs/history/current-task-before-2026-11-05-w34-terminal-extents-reviewed.md) · [更早入口](docs/history/current-task-before-2026-11-05-w34-M3-window-reviewed.md) · [固定确认协议](docs/review-sheet-protocol.md)。

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
# 模型从已审几何基线继续，不重复补建或延伸事务。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/w34-terminal-extension-v1/next-request.json --output runs/新的四端接续目录
# 换成实际收到的新身份确认单，不自行填写人审答案。
.venv/bin/python -m silicon_eye.review_sheet check --package docs/assets/w34-terminal-v1-inspection-v1/review --decision /实际路径/review-decision.json --archive
```

不得自动重建README/site或发布gh-pages；本次仅核V1身份，承载/连接批准需后续独立证据。
