# 当前入口完整归档

来源：CURRENT_TASK.md；日期：2026-10-24。
原文7773 bytes，SHA256 `f5529678e2b5a1493f9d8694b4bede24683ec7a47e8d9e133e5c176b45e81374`。

<!-- ORIGINAL CURRENT_TASK BYTES -->
# 当前任务

## 当前目标：U3端子连接已批准，接续连续候选整体复核

本轮授权：按顺序完成A/B范围收口、连续M1/V1/M2/V2/M3中样、回到N2–B1–L1主网推进一条器件支路、评估通用金属/Via skill封装条件。2026-10-24继续执行；不重启材料层，不扩为全幅金属自动重建。

[新联合候选与分层入口](docs/assets/conductive-medium-closeout-v1/index.html) · [U3端子已审页](docs/assets/n2-u3-terminal-reviewed-v2/index.html) · [当前已审支路状态](benchmarks/n2-u3-terminal-reviewed-v2/reviewed-state-v2.json) · [四项复查与封装评估](docs/reviews/2026-10-24-metal-via-closeout-readiness.md) · [技术核验](benchmarks/conductive-medium-closeout-v1/verification-v1.json) · [本轮检查点](docs/checkpoints/2026-10-24-four-point-closeout.md)。

| 项目 | 状态与限制 |
| --- | --- |
| A/B局部收口 | 分组冻结、具体路径保留未知；不再逐孔追问或重复审批成员 |
| 连续五层中样 | 已生成局部规则几何候选及来源切换；尚未采用为共同层或核准精确投影 |
| 主网到器件端子 | 用户“确认无误，批准通过”：U3→所圈CT行→对应AA环接入已确认，terminal_closed=true仅限这一条端子路径；沿途全部接口与其他分支仍未完成 |
| 金属/Via skill | 端子连接已审；连续候选整体几何复核与另一独立区域迁移证据仍待完成，暂不正式封装 |

## 必须继承的最新事实

- **A={T3,L2}，B={T1,L4}，分别经M2/M3接A、B。** [现行分组v3](benchmarks/mid-ab-structural-hypothesis-v11/grouping-state-v3.json)及[用户最新更正](benchmarks/mid-ab-structural-hypothesis-v11/grouping-human-correction-v3.json)优先；旧L3分组只保留历史，不复活为A成员，也不推导L3全局断开。具体M3-X/Y承载、返回M2及孔位仍未知。[范围收口记录](benchmarks/conductive-medium-closeout-v1/ab-closeout-v1.json)。
- MID-H1、MID-H2均为M1，在本处不与U1/U2那条M1接通；不推导为全局不同网。H1→V1→M2-A、H2→V1→M2-B已审。U1/U2本身同M1、U1/U3有V1而U2无V1，两处均接N2；精确中间走向尚未恢复，不虚构竖线跨过H1/H2。[隔离](benchmarks/mid-h1-h2-isolation-v9/reviewed-facts-v1.json)、[承载](benchmarks/mid-ab-carrier-reviewed-v10/reviewed-relations-v1.json)。
- N2上接M3-B1，下经D1接M3-L1；J01/F04、F01–F12等已审局部承载沿用原范围。13条主分支并不等于M1/CT检查全部完成；本次选N2→U3，其他12条仍未完成下层覆盖。既有P0/P5等历史裁决按前入口调取，不因本次局部未画而撤销。
- 本批M1侧孔证据为V1，M2侧孔证据为V2。共同小样M2孔组为3×4 V2；旧九对V1/V2同孔拟合和约4.52px残差已撤回，**不得作为配准依据**。不能把M2亮点当V1，更不能因拟合残差小重新采用。

## 新候选的范围与验证

[复跑输入](benchmarks/conductive-medium-closeout-v1/request-v1.json)将M1九条、M2八条、M3五条放在1800×1550局部正交设计画布；V1五处/V2六处是已审接口的候选支持区，**不是实测孔数**。稳定ID保留，A/B路径候选以虚线标示。照片原生位置、局部规则坐标、共同全幅坐标分别保存；无source_to_design_transform或common_canvas_placement。

来源读取将原35接口清单、原共同模型2接口及N2上端1接口合并为38条继承记录；不是新增3项审批。新中样仅表示其中11条。新局部模型也恰有33记录，但构成不同，不是原共同33对象注册表的替换。其他可见导体仍属未建模上下文。

95项相关测试通过；最后修订后新模块19项复跑通过，包含于95项，不合计为114项。相关Ruff、完整产物回放、来源SHA、原图裁片像素、链接、SVG和JS语法核验见verification。未实测浏览器交互，未做真实PDK DRC或新照片准确率评测；软件PASS不等于物理连接确认。

用户已对端子问题答复“确认无误，批准通过”。[人工裁决](benchmarks/n2-u3-terminal-reviewed-v2/human-review-v1.json)确认**U3宽M1经所圈CT行接入对应AA环**；[已审状态v2](benchmarks/n2-u3-terminal-reviewed-v2/reviewed-state-v2.json)只将这一条路径置terminal_closed=true，整网仍false。体端/极性、实测孔数、精确边界及现有CT/AA规范对象ID映射未知。原[事前候选](benchmarks/conductive-medium-closeout-v1/n2-terminal-candidate-v1.json)及旧模型保留当时null，不再作为当前连接状态入口。此次未批准连续中样整体几何采用或精确投影。

## 共同工作层与保留范围

唯一共同快照仍为[configs/joint-work-layer-v5.json](configs/joint-work-layer-v5.json)，AA334/POLY696/CT10287、八张5712×4284源照片及哈希不变；导体注册表仍引用[原33记录模型](docs/assets/conductive-stack-v2/model.json)。新局部几何候选未采用，原图/材料/旧批准不改；本次仅新增一条有人工依据的U3→CT→AA环接入，不改原38条继承金属接口。

S1/S2/S3材料身份、G66-P03/P04共用上端桥与蓝色栅CT、退休ROW4-AA4-SD00、四栅与33孔、R1A/R1B上端、R2连续AA单排孔及历次CT审批均按前入口原范围保留。R2_Q1、V3端子、v33网络、S03-03/04、18电阻、W01身份及195保留对象不改。

六处未知继续保留：AA-F01951、AA-F01952、材料层H1/H2（不同于MID-H1/H2）、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS。最后一处不能借蓝色栅CT证明源漏有孔或无孔。V3主体截段历史例外仍生效。未知仅限制依赖，不触发全层重做。

net_edges仍空，automatic_network_export_allowed=false，complete_network=false。物理尺度、工艺、极性、真实W/L、阻值及完整网表仍未知。

## 工具与恢复

本轮新增通用联合候选构建入口，复用原几何/来源/渲染；不是运行时自动视觉提取或自动追网器。复跑须使用新目录：

```bash
.venv/bin/python -m silicon_eye.conductive_medium --request benchmarks/conductive-medium-closeout-v1/request-v1.json --output runs/新的连续中样目录
```

共同层只读复核仍用`.venv/bin/python -m silicon_eye.layer_review --request configs/metal-stack-review-v2.json --output runs/新的共同复核目录`。新局部候选不传给旧共同注册表适配器冒充已审模型。

[POLY skill](skills/silicon-eye-poly-reconstruction/SKILL.md)、[CT skill](skills/silicon-eye-ct-reconstruction/SKILL.md)及其原封装范围保持。金属/Via按[两个通用skill＋逐层配置](docs/architecture/metal-via-skill-boundary-assessment-v1.md)设计，当前未创建SKILL.md或安装全局。原[追网约定](docs/metal-tracing-workflow-v1.md)继续有效。

## 唯一下一步、未提交状态与归档

下一步先对连续五层候选做整体来源/相对几何与隔离复核，再安排另一独立区域的迁移验证；以本条已审端子路径作为防退化对照。不重问已批准的U3、A/B或N2接口，不据本次连接批准采用全幅几何或正式封装。

Git HEAD仍389c682；本轮及此前2026-10-23的代码、benchmarks、图稿、检查点、历史档案均在工作树，未提交/推送。本轮未执行提交/推送。

[批准前入口完整原文](docs/history/current-task-before-2026-10-24-U3-terminal-reviewed.md)已核原字节与SHA；[更早四项收口入口](docs/history/current-task-before-2026-10-24-four-point-closeout.md)保留旧裁决、未知、恢复命令及未提交范围。[本次批准检查点](docs/checkpoints/2026-10-24-U3-terminal-reviewed.md)与[核验](benchmarks/n2-u3-terminal-reviewed-v2/verification-v1.json)保存批准范围与不变项。固定基线和原始证据不改。
