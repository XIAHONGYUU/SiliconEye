# 当前任务

## 当前目标与授权

2026-10-18 用户要求“保留几何并将提取范围扩展到整个图片的AA和CT”。这条新指令接续 T02 诊断，允许本轮全幅扩展；不把旧回投数值失败当作必须先改形的条件。按 v5 共享结构/规则几何方向继续。

- D01/R01/T01/T02 的 195 个对象原样保留。保留指令不扩大为精确孔位/工艺尺寸/电气连接或全幅完整性批准。
- 仅用现有八图，实际本轮材料证据为完整 AA 与 poly 两帧；不要求补拍。原图 data/ 不改，派生 runs/。无新增付费视觉服务、Git 推送或发布授权；未提交 Git。
- 暂不进行其他层完整重建、并网或新 skill 封装。此前大量架构、区域、材料、组验证及本轮源码/图稿均未提交；本轮未核验远端状态。

## 最新结果与唯一下一步

**下一步：复核新全幅 AA＋CT 的明显漏块/误连和 CT 整组规律，处理 100 条未解决 AA 与 1 处边界冲突。材料归属未知亮点单独查看，不逐孔批准、不自动并网。**

- [本轮方法与全幅图](docs/full-scene-regular-v1.md)、[最新全幅切层页](runs/full-scene-regular-v1d/index.html)、[冻结模型](benchmarks/full-scene-regular-v1/model-v1.json)、[参数 v2](benchmarks/full-scene-regular-v1/spec-v2.json)、[统计](benchmarks/full-scene-regular-v1/report-v1.json)、[技术核查](benchmarks/full-scene-regular-v1/verification-v1.json)、[保留指令范围](benchmarks/full-scene-regular-v1/retention-instruction-v1.json)。
- 195 个保留对象逐字段完全一致；全幅有 303 条活动 AA、4284 条工作 CT 位置（1671 规律/既有正几何候选、181 推断、2432 AA 关联待核），另有 6581 条材料归属未知位置。均不是独立材料岛、器件或物理孔总数。
- 13 个 AA 行/环共享参数提案中 12 个应用为候选、1 个暂缓。两个旧边缘片段按保留阵列扩为相邻方块候选；AA-F00128 仍有边界冲突，旧完整几何另存并显示红边，不进入活动 AA 层，未强行相连。原 100 条未解决 AA 继续保留，整幅范围已处理但完整性未验收。
- 全图 11339 个来源亮点都有唯一处理去向；来源支持、模板推断、组规律/边界待核、非 AA/材料归属未知分别记录。加权亮度中心是候选观测定义，不是精确孔中心真值；不无依据补整列，不在 AA 内孔中推断 AA 接触。
- [T02 诊断](docs/t02-gate-diagnosis-v1.md)：原 5.20 px 回投失败记录未改；参考定义敏感，不能据此认定结构错。当前按用户新指令保留几何并扩范围，不声称原门已通过。
- 全项目 305 tests、相关 Ruff、原图/输入/代码/44 项输出哈希、195 对象不变、11168 对象唯一有效正交、同层 AA/CT 无交叠、来源去向唯一、SVG/页面脚本/静态引用核查通过。浏览器交互未自动实测，不绕过此前 file: 自动预览限制。
- 几何画布仍 5860×4587，原照片各 5712×4284；逐对象保留全局/局部照片映射。局部变换尚未拼成完整一致场，缺沟道/上覆材料/目标工艺/尺度，完整孔合法性及电气连接未知。

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
