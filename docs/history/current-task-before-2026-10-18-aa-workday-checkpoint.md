# Archived current task

Source: CURRENT_TASK.md; archived 2026-10-18 at AA workday checkpoint. Original body follows verbatim.

# 当前任务

## 当前目标与授权

2026-10-18 用户批准“照片分割 → 材料/间隙验收 → 正交重建 → 前后检查”的顺序，并要求比较三类AA算法。已完成探索性固定样本对照；[合同v7](docs/architecture/aa-segmentation-contract-v7.md)固定阶段，不继续凭几何先验补环。
- D01/R01/T01/T02 的 195 个对象原样保留。保留指令不扩大为精确孔位/工艺尺寸/电气连接或全幅完整性批准。
- 仅用现有八图，实际本轮材料证据为完整 AA 与 poly 两帧；不要求补拍。原图 data/ 不改，派生 runs/。无新增付费视觉服务、Git 推送或发布授权；未提交 Git。
- 暂不进行其他层完整重建、并网或新 skill 封装。此前大量架构、区域、材料、组验证及本轮源码/图稿均未提交；本轮未核验远端状态。

## 最新结果与唯一下一步

**唯一下一步：以已审Q1–Q4约束准备有原图证据的局部修订对照：排除电阻内部误报、保留间隙、保持暗AA内部连续、不向电阻扩宽；精确边界仍未知。不按复核框直接裁切，不改正式几何/CT；本轮仅登记裁决，尚未生成修订mask。**

- [最新上下文复核页](runs/aa-context-review-v1b/index.html)、[整张复核图](runs/aa-context-review-v1b/review-sheet.png)、[说明](docs/aa-context-review-v1.md)、[参数与问题坐标](benchmarks/aa-context-review-v1/spec-v1.json)。保留宽上下文、主候选与同坐标分歧；Q1电阻误报、Q2隔离、Q3暗AA均获确认；Q4向电阻扩宽已否决，精确上边界未标注。见[人工裁决](benchmarks/aa-context-review-v1/human-context-review-v1.json)。
- 4方案×3种子严格一致/分歧仅作提示，不多数投票，不称独立置信度。AI上下文意见中上述四项已获本处人审，不是精确边界或本工艺DRC结论。324测试、相关Ruff、哈希、原图逐像素、分歧重算、静态图QA与JS语法通过；浏览器交互未自动实测。
- [笔画与五算法对照页](runs/aa-scribble-comparison-v1b/index.html)、[说明及核查清单](docs/aa-scribble-comparison-v1.md)、[参数](benchmarks/aa-scribble-comparison-v1/spec-v1.json)、[报告](benchmarks/aa-scribble-comparison-v1/report-v1.json)、[评估](benchmarks/aa-scribble-comparison-v1/assessment-v1.json)。
- A01–A05五条AA、N01–N04四条非AA笔画已由用户确认沿线材料身份，见[裁决](benchmarks/aa-scribble-comparison-v1/human-stroke-review-v1.json)；用户提及N05，但当前样稿无此ID，未关联位置。历史实验仍保留当时AI候选状态；沿原生照片，不做几何正交。覆盖MOS/环的明暗与电阻条纹、窄间隙。原7训练中心保留，原12检查中心及半径10避让区不参加训练；邻近图像上下文非盲测。
- 五方案×三种子×两窗口共30次结果：纹理RF及纹理＋结构RF均8/8 AA、0/4 BG误报，(3950,3510)漏检恢复；仅颜色RF仍7/8 AA、2/4 BG误报。两GrabCut均8/8 AA但误报2/4 BG，窄间隙失败。
- 电阻内部非训练诊断框残余预测AA：纹理RF约13%，纹理＋结构约15%，固定GMM约2.5%，迭代0%；该AI框无稠密标签，非IoU/准确率，不能以更干净掩盖误连。新笔画和训练预算改变，不报纯算法提升或全图通过。
- U已由用户[确认电阻内部非AA](benchmarks/aa-prompted-comparison-v1/human-U-review-v1.json)，U用于训练，非独立检查。原18中心加U共19人审中心；现有九条笔画身份已审，但完整边界/mask未审。
- [上一轮纹理/方向结构消融](docs/aa-texture-structure-v1.md)及全部旧实验保留。原始照片、正式AA几何/CT/195保留对象不变；旧100初始化疑点仍留档，不手剪mask或按先验补环。
- 322测试、相关Ruff、输入/依赖代码/输出哈希、全中心分数重算、避让与冲突检查、30mask重跑一致、页面JS语法通过。浏览器交互未自动实测，无提交/推送Git，既有未提交工作保留。

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

- [算法对照前完整入口](docs/history/current-task-before-2026-10-18-aa-algorithm-comparison.md)：注明来源/日期，完整保留原文字节。

- [少量提示实验前完整入口](docs/history/current-task-before-2026-10-18-aa-prompted-comparison.md)：注明来源/日期并完整保留原文字节。

- [纹理结构验证前入口](docs/history/current-task-before-2026-10-18-aa-texture-structure.md)：原文完整归档，包含U确认及追加提示失败结果。

- [笔画对照前入口](docs/history/current-task-before-2026-10-18-aa-scribble-comparison.md)：原文完整归档，保留前轮纹理/结构结论。
