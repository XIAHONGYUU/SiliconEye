# 当前入口完整归档

来源：CURRENT_TASK.md；日期：2026-10-24。
原文10243 bytes，SHA256 `b1bdb138888f1e7be7bf22c87d1972f3ff439c28b70b8e99837849f0a539686c`。

<!-- ORIGINAL CURRENT_TASK BYTES -->
# 当前任务

## 当前目标：五层局部纠偏完成；独立迁移Q2已审、Q1待裁决

本轮授权：按顺序完成A/B范围收口、连续M1/V1/M2/V2/M3中样、回到N2–B1–L1主网推进一条器件支路、评估通用金属/Via skill封装条件。用户随后明确要求“复核连续五层整体几何，再进行独立区域迁移验证”。本轮按此执行；不重启材料层，不扩为全幅金属自动重建。

[来源纠偏后的连续候选](docs/assets/conductive-medium-source-review-v2/index.html) · [独立迁移当前页：Q2已审/Q1待定](docs/assets/metal-independent-transfer-v1/reviewed.html) · [本轮复核记录](docs/reviews/2026-10-24-metal-source-transfer-review.md) · [U3端子已审页](docs/assets/n2-u3-terminal-reviewed-v2/index.html) · [当前已审支路状态](benchmarks/n2-u3-terminal-reviewed-v2/reviewed-state-v2.json) · [四项复查与封装评估](docs/reviews/2026-10-24-metal-via-closeout-readiness.md) · [技术核验](benchmarks/conductive-medium-closeout-v1/verification-v1.json) · [本轮检查点](docs/checkpoints/2026-10-24-four-point-closeout.md)。

| 项目 | 状态与限制 |
| --- | --- |
| A/B局部收口 | 分组冻结、具体路径保留未知；不再逐孔追问或重复审批成员 |
| 连续五层中样 | 同层来源复核发现U1右端越过P08，已仅缩短U1；正交/间距/包围及声明来源顺序通过。仍有未建模端部，不采用为完整共同几何 |
| 主网到器件端子 | 用户“确认无误，批准通过”：U3→所圈CT行→对应AA环接入已确认，terminal_closed=true仅限这一条端子路径；沿途全部接口与其他分支仍未完成 |
| 独立区域迁移 | 同一已知芯片、与原窗口不相交；复用几何/来源/包围函数，4项反例拦截。Q2已确认B处V2接粗M3；Q1的V1到M2-A仍待裁决 |
| 金属/Via skill | 局部几何已纠偏，独立迁移只部分人审；统一CLI尚未覆盖未审接口候选，不正式封装 |

## 必须继承的最新事实

- **A={T3,L2}，B={T1,L4}，分别经M2/M3接A、B。** [现行分组v3](benchmarks/mid-ab-structural-hypothesis-v11/grouping-state-v3.json)及[用户最新更正](benchmarks/mid-ab-structural-hypothesis-v11/grouping-human-correction-v3.json)优先；旧L3分组只保留历史，不复活为A成员，也不推导L3全局断开。具体M3-X/Y承载、返回M2及孔位仍未知。[范围收口记录](benchmarks/conductive-medium-closeout-v1/ab-closeout-v1.json)。
- MID-H1、MID-H2均为M1，在本处不与U1/U2那条M1接通；不推导为全局不同网。H1→V1→M2-A、H2→V1→M2-B已审。U1/U2本身同M1、U1/U3有V1而U2无V1，两处均接N2；精确中间走向尚未恢复，不虚构竖线跨过H1/H2。[隔离](benchmarks/mid-h1-h2-isolation-v9/reviewed-facts-v1.json)、[承载](benchmarks/mid-ab-carrier-reviewed-v10/reviewed-relations-v1.json)。
- N2上接M3-B1，下经D1接M3-L1；J01/F04、F01–F12等已审局部承载沿用原范围。13条主分支并不等于M1/CT检查全部完成；本次选N2→U3，其他12条仍未完成下层覆盖。既有P0/P5等历史裁决按前入口调取，不因本次局部未画而撤销。
- 本批M1侧孔证据为V1，M2侧孔证据为V2。共同小样M2孔组为3×4 V2；旧九对V1/V2同孔拟合和约4.52px残差已撤回，**不得作为配准依据**。不能把M2亮点当V1，更不能因拟合残差小重新采用。

## 新候选的范围与验证

[当前复跑输入](benchmarks/conductive-medium-source-review-v2/request-v1.json)将M1九条、M2八条、M3五条放在1800×1550局部正交设计画布；V1五处/V2六处是已审接口的候选支持区，**不是实测孔数**。稳定ID保留，A/B路径候选以虚线标示。照片原生位置、局部规则坐标、共同全幅坐标分别保存；无source_to_design_transform或common_canvas_placement。

来源读取将原35接口清单、原共同模型2接口及N2上端1接口合并为38条继承记录；不是新增3项审批。新中样仅表示其中11条。新局部模型也恰有33记录，但构成不同，不是原共同33对象注册表的替换。其他可见导体仍属未建模上下文。

此前95项是上一轮相关测试。本轮23项conductive_medium测试通过，增加旧几何PASS但同帧顺序错误的反例、跨帧顺序禁用、U3接续及未审材料映射阻断；不与旧95简单相加。原候选模型/报告/HTML重放保持，生产渲染函数复用。来源与像素/页面/归档核验见[本轮verification](benchmarks/conductive-medium-source-review-v2/verification-v1.json)。浏览器交互未测，无真实PDK DRC/全幅准确率声明。

[整体来源复核](benchmarks/conductive-medium-source-review-v2/whole-geometry-review-v1.json)发现：原生U1右端x=1945<P08左竖x=2006，旧设计却1700>1380。仅将U1右端1700缩至1310；其余32条模型记录、11接口、A/B分组保持。新增source_order_checks为同帧声明关系硬门，不是跨层配准。M1列、M2列、M3母线的代表顺序另有记录；U1/U3右侧转角、其他导体、A/B逐孔分配仍未建模或未知，不能宣布完整五层GDS恢复。

独立区域窗口[2250,100,3350,1150]与旧窗口[800,1700,2350,3300]不相交。[首次AI候选](benchmarks/metal-independent-transfer-v1/initial-ai-observation-v1.json)先于人工裁决保存；同芯片非盲测。新局部六条金属/两处支持区只复用现有工具函数，未修改CLI绕过未审接口限制。四项控制（A/B误并、V1借M2、缺包围、错层对）被拦。

用户已答复**Q2正确**：[原文](benchmarks/metal-independent-transfer-v1/q2-human-review-v1.json)、[当前迁移状态](benchmarks/metal-independent-transfer-v1/reviewed-state-v2.json)、[评价](benchmarks/metal-independent-transfer-v1/evaluation-reviewed-v2.json)。只确认IT1-M2-B经V2接IT1-M3-BUS；Q1（M1圈示V1→窄M2-A）、A/B同层是否连续、实测孔数及几何采用未批准。待Q1，不重复问Q2；不以一次正确宣布迁移全部成功。

用户已对端子问题答复“确认无误，批准通过”。[人工裁决](benchmarks/n2-u3-terminal-reviewed-v2/human-review-v1.json)确认**U3宽M1经所圈CT行接入对应AA环**；[已审状态v2](benchmarks/n2-u3-terminal-reviewed-v2/reviewed-state-v2.json)只将这一条路径置terminal_closed=true，整网仍false。体端/极性、实测孔数、精确边界及现有CT/AA规范对象ID映射未知。原[事前候选](benchmarks/conductive-medium-closeout-v1/n2-terminal-candidate-v1.json)及旧模型保留当时null，不再作为当前连接状态入口。此次未批准连续中样整体几何采用或精确投影。

## 共同工作层与保留范围

唯一共同快照仍为[configs/joint-work-layer-v5.json](configs/joint-work-layer-v5.json)，AA334/POLY696/CT10287、八张5712×4284源照片及哈希不变；导体注册表仍引用[原33记录模型](docs/assets/conductive-stack-v2/model.json)。新局部几何候选未采用，原图/材料/旧批准不改；本次仅新增一条有人工依据的U3→CT→AA环接入，不改原38条继承金属接口。

S1/S2/S3材料身份、G66-P03/P04共用上端桥与蓝色栅CT、退休ROW4-AA4-SD00、四栅与33孔、R1A/R1B上端、R2连续AA单排孔及历次CT审批均按前入口原范围保留。R2_Q1、V3端子、v33网络、S03-03/04、18电阻、W01身份及195保留对象不改。

六处未知继续保留：AA-F01951、AA-F01952、材料层H1/H2（不同于MID-H1/H2）、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS。最后一处不能借蓝色栅CT证明源漏有孔或无孔。V3主体截段历史例外仍生效。未知仅限制依赖，不触发全层重做。

net_edges仍空，automatic_network_export_allowed=false，complete_network=false。物理尺度、工艺、极性、真实W/L、阻值及完整网表仍未知。

## 工具与恢复

联合候选构建入口本轮增量加入同帧来源顺序门及已审U3端子接续；没有增加案例专用生产脚本。独立样本复用底层函数做迁移试验，尚未实现未审接口的统一CLI。不是运行时自动视觉提取或自动追网器。复跑须使用新目录：

```bash
.venv/bin/python -m silicon_eye.conductive_medium --request benchmarks/conductive-medium-source-review-v2/request-v1.json --output runs/新的连续中样目录
```

共同层只读复核仍用`.venv/bin/python -m silicon_eye.layer_review --request configs/metal-stack-review-v2.json --output runs/新的共同复核目录`。新局部候选不传给旧共同注册表适配器冒充已审模型。

[POLY skill](skills/silicon-eye-poly-reconstruction/SKILL.md)、[CT skill](skills/silicon-eye-ct-reconstruction/SKILL.md)及其原封装范围保持。金属/Via按[两个通用skill＋逐层配置](docs/architecture/metal-via-skill-boundary-assessment-v1.md)设计，当前未创建SKILL.md或安装全局。原[追网约定](docs/metal-tracing-workflow-v1.md)继续有效。

## 唯一下一步、未提交状态与归档

唯一下一步：等待独立迁移Q1裁决（所圈M1 V1是否接窄M2-A），Q2与U3不重复问；按该结果增量记录或局部纠偏。统一候选接口入口及进一步封装依证据再推进，不据当前门通过采用全幅几何。

Git HEAD仍389c682；本轮及此前2026-10-23的代码、benchmarks、图稿、检查点、历史档案均在工作树，未提交/推送。本轮未执行提交/推送。

[批准前入口完整原文](docs/history/current-task-before-2026-10-24-U3-terminal-reviewed.md)已核原字节与SHA；[更早四项收口入口](docs/history/current-task-before-2026-10-24-four-point-closeout.md)保留旧裁决、未知、恢复命令及未提交范围。[本次批准检查点](docs/checkpoints/2026-10-24-U3-terminal-reviewed.md)与[核验](benchmarks/n2-u3-terminal-reviewed-v2/verification-v1.json)保存批准范围与不变项。固定基线和原始证据不改。

[本轮整理前入口完整归档](docs/history/current-task-before-2026-10-24-metal-source-transfer-review.md)已核原字节及SHA，保留U3完整批准和四项接续范围。[本轮检查点](docs/checkpoints/2026-10-24-metal-source-transfer-review.md)记录局部变更与迁移范围。
