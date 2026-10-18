Source: CURRENT_TASK.md
Archived: 2026-10-18, before AA algorithm comparison handoff

# 当前任务

## 当前目标与授权

2026-10-18 已收到全幅 F01–F12 完整人审。当前方向改为 **先完整重建 AA 并独立验收，再重算 CT**；环不能由 CT/M1 连续性替代判断。见[纠偏 v6](docs/architecture/aa-first-reconstruction-v6.md)。
- D01/R01/T01/T02 的 195 个对象原样保留。保留指令不扩大为精确孔位/工艺尺寸/电气连接或全幅完整性批准。
- 仅用现有八图，实际本轮材料证据为完整 AA 与 poly 两帧；不要求补拍。原图 data/ 不改，派生 runs/。无新增付费视觉服务、Git 推送或发布授权；未提交 Git。
- 暂不进行其他层完整重建、并网或新 skill 封装。此前大量架构、区域、材料、组验证及本轮源码/图稿均未提交；本轮未核验远端状态。

## 最新结果与唯一下一步

**唯一下一步：先审定 AA 分割算法对照方案，再在冻结同一批样本上比较照片分割与正交重建前后结果。最新人审已否定部分连接/环结构，不继续手工扩补环，不重算 CT。**

- [最新复核](benchmarks/aa-completion-v1/human-review-v2.json)：F01–F04 两条误合并，F05/F06 和 F09 多补环，F09 环形状、F10 缺口及 F11 环间距需修正；F12 只认可基本表现。旧几何无交叠不表示这些拓扑关系正确。本轮只核查方法并讨论，没有新跑算法或修改模型。
- [复核页](runs/aa-completion-v1k/index.html)、[本轮修正说明](docs/aa-completion-v1.md)、[冻结模型](benchmarks/aa-completion-v1/model-v1.json)、[当前参数 spec-v9](benchmarks/aa-completion-v1/spec-v9.json)、[技术核查](benchmarks/aa-completion-v1/verification-v1.json)、[F01–F12 新旧台账](benchmarks/aa-completion-v1/coverage-review-v1.json)。
- 336 条活动 AA 几何；25 组/89 条新增结构，56 条旧候选保留记录后替代/转存疑点，上部25条 AA 共同行基线/高度修订。所有活动几何有效、正交且无面积交叠，不能外推为完整性或电气隔离已通过。
- 补外围/长条/阶梯 AA、漏掉的器件及环，修正 F06 填块、F10 环内场区误填，补右侧第四个 dummy，并补五段照片右缘邻近环。源图边界不充当物理闭合边。
- 72 条保留 AA 逐字段不变；原123条保留 CT 和其他 CT 冻结在父模型，本轮不重算。[旧 AA-F00128 冲突](benchmarks/aa-completion-v1/boundary-disposition-v1.json)由新的第四个 dummy 候选表达，原记录不覆盖。
- 原100条轮廓初始化疑点留档，尚未逐条归并；不是100个漏检器件。AA覆盖门、独立边界门待人工复核，未声明全幅无漏标。部分截图顶部小观察另存疑点，非已确认 AA。
- 来源几何在 source_geometry/旧矩阵中分别表达；长结构显式分轴重建，不将组号盲当3×3矩阵。仍无已审全幅一致畸变场，不可直接用来判定 CT 落点或并网。
- 全项目310 tests、两新文件Ruff、原图/冻结输入哈希、8 SVG尺寸、页面JS语法及静态引用通过；浏览器交互未自动实测。未提交/推送Git，既有大量未提交工作保留。
- [上一轮完整人审原文](benchmarks/full-scene-regular-v1/human-review-v1.json)与[旧 AA＋CT 结果](docs/full-scene-regular-v1.md)冻结作开发对照；新候选不继承完整性批准。

## 已审基准及历史范围

- [局部组验证](docs/group-constraints-validation-v1.md)保留 D01/R01/T01/T02 的原数值和 20 个故障样本，不作为当前范围禁令；[当前设计 v5](docs/architecture/photo-stack-workflow-v5.md)按结构组/共享参数和证据双门工作。
- [P01–P06 全部已审](docs/orthogonal-aa-polygons-v1.md)、[已审模型](benchmarks/orthogonal-aa-polygons-v1/model-v1-reviewed.json)。P05/P06 是有未建模延续的局部材料片段，不是断点或独立岛。
- [AA/CT 与三环人审](docs/geometry-reconstruction-v2.md)保留旧结构、120 CT 存在/大致位置及整体排列批准；精确尺寸/全图配准/电气连接未获批准。[旧全幅 v1h](docs/full-scene-aa-ct-v1.md)保留作开发对照。
- [区域分类 v3](docs/region-planning-reviewed-v3.md)、[区域 skill 验证](docs/region-skill-validation-v1.md)、[PDK 回查](docs/reference/pdk-recognition-guide-v1.md)、[八图来源](benchmarks/photo-stack/eight-photo-intake-v1.json)。U01 是宽 MOS 电容接法，U04 是底部 dummy；区域条目不是器件数。

## 数据及质量约定

- 原图不可变且可回查；后续正常计算使用重建版图，发现矛盾时修订局部，按依赖重算。
- 保留材料存在/不存在/未知三种状态，另存有效覆盖；native 坐标和公共参考变换分开。每对象有来源、状态、修订和稳定 ID。
- 10 px/μm、N/P、S/D、W/L、工艺规则均未确定。sub/implant 保留来源标签，不新增掺杂语义真值。
- 区域框、材料身份、精确几何、端口和连通分别验收。质量门按用途/区域判断，不以总 PASS 代替物理结论。
- 区域观察已封装交互 skill 与参数化出图工具；职责已收窄为整体理解/评测支线，不决定分层抽取范围。输入、分层复原、追线、器件端口、输出、三维、总控和质量复核等其他 skill 仍未实现。

## 既有已审事实与恢复入口

- [v33 最终复核稿](docs/roi2-gate-network-reviewed-v33.md)、[伴随拓扑](benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v33.json)、[覆盖记录](benchmarks/metal-extension/roi2-gate-network-coverage-v33.json)。
- Q1/Q2 相邻栅指，poly 局部不连，经 M1 共栅；中间扩散共享、体端共用，外侧扩散共接未知。原生窗口见[旧任务输入](benchmarks/agent-eval/roi2-seed-v1/input.json)，不是材料边界或统一坐标。
- 当前长 M2 入口保留；T→N04→J1/T/J2/J3/J4 五 M2/M1→CT→AA 已审；S1/S2→L01 右端短竖→左端 W/M2→W1/M1→CT→AA 已审。B→底部 M1 长横及绿色 M1/M2/M3 梳齿同电极，橙色对极隔离。
- 六处 AA 接入不是六器件；不穿 MOS 沟道/电容介质。照片外、未识别接口及 M3/M4 精确配准未知，未证明物理全网无遗漏。
- 旧 gate→A→P1 归属已撤回；保留历史物理子图。旧 E=V1、F/G 直接接 M1 已否决；旧 MOM P1/P2 裁决保留，不与新 B 电极自动合并。
- 通用 case v14 仍带历史错误入口，不能代替 v33。旧观察、编号和高亮工具保留，不冒充已实现整网追踪。
- [昨日走线协议](docs/metal-tracing-workflow-v1.md)待分层样稿可用后复用。开发过的同芯片数据只算回归，不算盲测。
- 证据恢复：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/roi2-network-reviewed-v33.zip --root .`；旧九项示例输入用同目录 roi2-reviewed-inputs-v1.zip。不是全部 runs 历史。
- 统一包：`.venv/bin/silicon-eye annotate review-package --spec benchmarks/review-package-roi2-v1.json --root . -o 新目录`。浏览器预览曾被策略拒绝，不用 CDP 绕过；用静态图交付。

## 按需历史

- [本轮全幅扩展前完整入口](docs/history/current-task-before-2026-10-18-full-scene-regular-extension.md)：字节完整保留 T02 诊断、原验证结果及当时范围，旧“不扩大到全幅”已由用户新指令接续。
- [组约束验证前入口](docs/history/current-task-before-2026-10-18-group-constraint-validation.md)、[全幅纠偏前入口](docs/history/current-task-before-2026-10-18-full-frame-correction.md)、[方向调整前入口](docs/history/current-task-before-2026-10-18-layer-reconstruction.md)、[v33 历史](docs/history/current-task-before-2026-10-17-v33-reviewed-network.md)。

- [AA 优先纠偏前完整入口](docs/history/current-task-before-2026-10-18-aa-first-review.md)：原文逐字节归档，旧联合验收下一步由本次人审反馈接续。

- [AA 补标前完整入口](docs/history/current-task-before-2026-10-18-aa-completion.md)：注明来源/日期并完整保留原文字节。
