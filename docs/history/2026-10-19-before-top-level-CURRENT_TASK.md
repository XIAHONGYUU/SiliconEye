# Archived CURRENT_TASK.md

Source: CURRENT_TASK.md; archived 2026-10-19. Original body follows verbatim.

# 当前任务

## 当前目标与授权

2026-10-18阶段结束：用户认可AA提取已形成有效方法，要求保存今日工作、更新顶层文档并提交本地Git；明天争取封装AA skill。本轮不推送远端，不新建skill或继续修订mask。

方法入口：[AA工作流v8](docs/architecture/aa-extraction-workflow-v8.md)。结果/恢复：[今日检查点](docs/checkpoints/2026-10-18-aa-workflow-reviewed.md)。仍用现有八图，原始data不可改；无新增付费视觉服务。

## 最新结果与唯一下一步

**唯一下一步（下次工作）：按已审语义先完成局部修订对照、再在不同窗口验证，在此基础上封装实验版AA skill。复用现有工具和记录，明确材料门、未知边界及人工复核；不扩大到CT/其他层/追线。**

- 工作方法：代表性明暗笔画 → 多方法候选 → 同坐标分歧 → AI结合整体结构/正向设计复核 → 人工裁决 → 有证据的局部修订 → 材料门 → 正交重建。不是多数票融合、矩形裁剪或按经验补环；交互Agent判断尚未变成独立运行时视觉模型。
- [九条笔画身份](benchmarks/aa-scribble-comparison-v1/human-stroke-review-v1.json)已审：A01–A05为AA、N01–N04非AA。样稿无N05，不补造。原12检查中心保持不训练，三个种子与同窗口重复运行不算独立数据集。
- [Q1–Q4裁决](benchmarks/aa-context-review-v1/human-context-review-v1.json)：排除电阻内部误报、两条AA隔离、暗AA内部不挖空、拒绝向电阻扩宽。[Q4澄清](benchmarks/aa-context-review-v1/Q4-scope-clarification-v1.json)：指电阻外围环下侧AA横条内侧边界，必须保护外围环，不能随电阻误报删除。精确边界/整环全周尚未通过。
- 纹理RF及纹理＋结构RF三个种子均8/8 AA、0/4 BG误报；两GrabCut仍误填2/4 BG。电阻内部残余误报存在，完整mask、新窗口迁移及自动上下文修订未验收，不宣称全幅自动化或skill已完成。
- [今日复核图（已入Git）](docs/assets/aa-context-review-v1/review-sheet.png)、[本地复核页](runs/aa-context-review-v1b/index.html)、[参数与Q坐标](benchmarks/aa-context-review-v1/spec-v1.json)、[笔画对照](docs/aa-scribble-comparison-v1.md)、[综合算法评估](docs/aa-texture-structure-v1.md)。旧报告/失败mask/裁决保持原样；当前未生成语义修订mask。
- 原有全幅AA/CT/195保留对象不变，旧100初始化疑点留档。照片尺度、工艺、精确尺寸与完整连通未确定。材料、几何、端口和连接分别验收。
- 七个关键runs已明确归档，恢复索引：[AA证据归档](benchmarks/evidence/aa-workday-2026-10-18-index.json)。.venv/runs仍忽略，不把所有历史运行视为已保存。各归档用 `.venv/bin/python -m silicon_eye.evidence_archive --archive 路径 --root .` 恢复。
- 本轮软件基准324测试通过，相关Ruff/哈希/输入输出/分歧/JS通过；真实材料仍保留上述失败与未知。浏览器交互未自动实测。Git提交结果由本次结束报告给出。

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

- [今日阶段收束前完整入口](docs/history/current-task-before-2026-10-18-aa-workday-checkpoint.md)：原文字节完整归档，保留所有历史验收与恢复入口。
