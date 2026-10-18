# CURRENT_TASK archive

Source: CURRENT_TASK.md
Archived: 2026-10-18 before user-authorized full-scene regular extension.

# 当前任务

## 当前目标与授权

2026-10-18：按顶层 v5 跑一轮结构组重建及质量门验证。先复原规则材料版图，再进行器件/网络分析；区域观察不裁割图层或网络。当前只用现有八图，不要求补拍。

- 内层 silicon-eye 仓库、.venv；data/ 原图不可改，runs/ 为派生试验。没有新增付费视觉服务、远端推送或发布授权；本轮未提交 Git。
- 暂缓金属独立重走、其他层完整扩展、并网和新 skill 封装。既有区域 skill 保留。
- 大量此前架构/区域/材料几何工作仍未提交；本轮新增 group_constraints.py、测试、参数/模型/报告及图稿。未覆盖父模型、原图或既有人审。未在本轮重新核验远端状态。

## 最新结果与唯一下一步

**下一步：先确定 CT 观测参考与质量门分级的修订方案，再重验 T02；局部真实禁区/上覆材料支持仍待建立。不扩大到全幅或网络追踪。**

- [T02 门失败诊断](docs/t02-gate-diagnosis-v1.md)：用户认为无明显提取错误。本轮未改几何/变换/门限或代码；唯一数值失败集中在中排，旧峰值参考平均向上偏约 4.55 px。仅改变中心估计定义，原变换不动，中位差即可由 5.20 变为 3.94 px；敏感性实验不是新真值或正式通过。保留原结果，不能把观测一致性失败直接叫作结构提取错误。本次只诊断，未新增批准。
- [本轮完整验证与旧新图](docs/group-constraints-validation-v1.md)、[同页切层入口](runs/group-constraints-v1f/index.html)、[冻结输入 v2](benchmarks/group-constraints-v1/spec-v2.json)、[新模型](benchmarks/group-constraints-v1/model-v1.json)、[规则及反例结果](benchmarks/group-constraints-v1/report-v1.json)、[核查记录](benchmarks/group-constraints-v1/verification-v1.json)。依据[当前设计 v5](docs/architecture/photo-stack-workflow-v5.md)实现共享模板、局部照片拟合及重建规则检查，尚未形成全幅联合变形场或工艺 DRC。
- D01：底部 U04 dummy，2×34 等尺寸/等节距 AA；下排 34 个来源受截断，完整形状为推断。排除截断中心，使用完整角点及可见上沿检查，54 个留出点中位/P95=2.96/8.22 px，当前工作门通过，新几何待审。
- R01：旧 AA-G003 等宽连续环，内孔保留；4 个内侧留出角点中位/P95=1.80/3.99 px，当前工作门通过，新宽度及变换未继承人审。
- T01：U01 宽 MOS 电容接法内的四列 CT，不是四个 MOS。96 槽中 82 个有单一来源、13 个推断、1 槽双来源。17 个留出观察中位/P95=3.31/5.43 px；几何/观测通过，完整孔合法性待定。
- T02：已审 M03 MOS 区域三个相邻 AA 单元，3×3 CT 模板/单元；单元数不是 MOS 数。9 个留出观察中位=5.20 px，超过冻结门限 4 px，照片门失败；模板外亮点 CT-F03736 仍未解释。不得放宽阈值或强行变形过门。
- 9 类 20 例受控变异全部拦截；全项目 296 tests、相关 Ruff、来源/代码/输出哈希、正交/有效/分离、SVG 和页面脚本/静态引用通过。浏览器交互未自动实测，不绕过此前 file: 自动预览限制。机器通过不等于物理通过。
- 本轮还纠正了两处验证范围：T01 属于 U01，不能验证跨 MOS 一致性；截断中心会偏移，D01 协议已修正并记录。初始输入和中间结果保留。本轮是同照片开发验证，留出集已参与开发，不是盲测，也不是提示词识别准确率/改进量评测；未调用独立视觉模型。
- 沟道禁区、上覆金属及工艺数值规则缺依赖时为待定；合成禁区反例成功不代表真实禁区已识别。新模型共 195 几何记录（72 AA、123 CT），不是独立岛、孔或器件真值。照片单位仍相对/px，工艺尺度未定。

## 已审基准及保留状态

- [全幅 v1h 候选](docs/full-scene-aa-ct-v1.md)继续作为开发候选及反例，F01–F12 人审暂停；100 条 AA 未解决，不作为生产材料或整网输入。
- [P01–P06 全部已审](docs/orthogonal-aa-polygons-v1.md)、[已审模型](benchmarks/orthogonal-aa-polygons-v1/model-v1-reviewed.json)。P05/P06 是有未建模延续的局部材料片段，不是断点或独立岛。
- [AA/CT 及三环人审](docs/geometry-reconstruction-v2.md)：旧 35 个 AA 结构/dummy 排列、120 CT 存在/大致位置和三环整体排列批准保留；原 79 个算法疑点及批准范围保留，精确尺寸/全图配准/电气连接未获批准。
- [区域分类 v3](docs/region-planning-reviewed-v3.md)、[区域 skill 及验证](docs/region-skill-validation-v1.md)、[PDK 回查](docs/reference/pdk-recognition-guide-v1.md)、[八图来源](benchmarks/photo-stack/eight-photo-intake-v1.json)。22 个区域是观察条目，不是器件计数。U01 为宽 MOS 电容接法，U04 为底部 dummy AA；材料身份不能替代几何/端口批准。

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

- [本轮验证前完整入口](docs/history/current-task-before-2026-10-18-group-constraint-validation.md)：字节完整归档此前架构、材料、批准及恢复入口，不作为竞争下一步。
- [全幅纠偏前入口](docs/history/current-task-before-2026-10-18-full-frame-correction.md)、[方向调整前入口](docs/history/current-task-before-2026-10-18-layer-reconstruction.md)、[v33 整合前入口](docs/history/current-task-before-2026-10-17-v33-reviewed-network.md)。
