# 当前入口完整归档

来源：CURRENT_TASK.md；日期：2026-10-24。
原文8992 bytes，SHA256 `c9eaa8c646739e204e7fbf57c6e5b4eb56c61fe8498eff2822d8601c70fff5da`。

<!-- ORIGINAL CURRENT_TASK BYTES -->
# 当前任务

## 当前目标与授权

完成用户批准的四项工程工作：当前接口范围收尾、统一操作入口、固定任务验证、金属与层间孔两个试用skill。本轮恢复退出前的未提交工作并完成交付；不重启AA/POLY/CT，不扩为整芯片自动提取或完整网表，不包含本轮推送授权。

最新用户裁决：Q1原窄M2-A承载错误，六孔组经V1接宽M2-B。已完成局部修订、质量门补强与Q2审批接续：[更正复核页](docs/assets/metal-independent-q1-reviewed-v3/index.html) · [复查报告](docs/reviews/2026-10-24-independent-Q1-carrier-correction.md) · [人工记录](benchmarks/metal-independent-q1-correction-v2/q1-human-carrier-correction-scoped-v3.json) · [核验](benchmarks/metal-independent-q1-correction-v2/verification-v3.json)。

此前已完成工程试用交付：[统一复核总入口](docs/assets/conductive-workflow-trial-v1/index.html) · [交付报告](docs/reviews/2026-10-24-conductive-workflow-trial.md) · [输入与接续契约](docs/architecture/conductive-workflow-contract-v1.md) · [固定任务](benchmarks/conductive-workflow-trial-v1/fixed-tasks-v1.json) · [评价](benchmarks/conductive-workflow-trial-v1/evaluation-v1.json) · [技术核验](benchmarks/conductive-workflow-trial-v1/verification-v1.json) · [检查点](docs/checkpoints/2026-10-24-conductive-workflow-trial.md)。

| 四项工作 | 当前结果与限制 |
| --- | --- |
| 当前接口收尾 | Q1六孔组接宽M2-B已裁决，原窄A候选撤回；Q2与U3实际批准保留 |
| 统一入口 | AI观察→规则候选→来源/几何门→复核包→实际人工裁决→父包增量接续；失败只交诊断 |
| 固定任务验证 | 旧中样、独立区域、无重复审批接续、旧来源错位拒绝四任务通过；同芯片工程回归，不是盲测识别准确率 |
| 两个试用skill | 仓库内金属重建、层间孔重建已创建并校验；未安装全局，未验证独立Agent在新照片上的首次判断质量 |

## 必须继承的事实

- **A={T3,L2}，B={T1,L4}，分别经M2/M3接A、B。** [最新分组](benchmarks/mid-ab-structural-hypothesis-v11/grouping-state-v3.json)及[用户更正](benchmarks/mid-ab-structural-hypothesis-v11/grouping-human-correction-v3.json)优先。旧L3只保留历史，不复活为A成员、不推导全局断开。具体返回M2、M3-X/Y及逐孔路径仍未知。
- MID-H1/H2为M1，本处与U1/U2那条M1隔离，不推导全局异网；H1→V1→M2-A、H2→V1→M2-B已审。U1/U2本身同一M1，U1/U3有V1、U2无V1；两处均接N2。精确中间走向未恢复，不虚构跨H1/H2的连线。
- N2上接M3-B1，下经D1接M3-L1；J01/F04、F01–F12等已审局部承载不变。13条主分支不等于下层覆盖完成；本次只保留已审U3器件支路，其余分支未完成下层检查。P0/P5等历史裁决按归档原范围保留，不因局部未画撤销。
- 用户批准**U3宽M1→所圈CT行→对应AA环**，只限这条端子路径terminal_closed=true。体端/极性、实测孔数、精确边界及规范CT/AA对象ID映射未知。[实际批准与状态](benchmarks/n2-u3-terminal-reviewed-v2/reviewed-state-v2.json)；整网仍false。
- 本批已审孔来源策略为M1照片侧V1、M2照片侧V2；共同小样M2孔组3×4 V2。旧九对V1/V2同孔拟合和约4.52px残差已撤回，不复用作配准依据，不借M3亮点证明V2。
- 连续设计候选U1右端已从1700缩至1310，纠正原生U1右端1945<P08左竖2006的次序；其他32条局部对象保持。显式同帧次序是来源检查，不是跨层配准。[来源复核](benchmarks/conductive-medium-source-review-v2/whole-geometry-review-v1.json)。

## 当前候选、已审与未知

[连续中样统一包](docs/assets/conductive-workflow-trial-v1/final-main/index.html)为1800×1550局部设计画布，M1九条、M2八条、M3五条及V1五处/V2六处支持区。它不是原共同33对象注册表的替换；孔组框不代表实测切孔阵列；U1/U3右侧转角、其他可见导体、A/B逐孔路径未完整建模。

[当前独立迁移更正包](docs/assets/metal-independent-q1-reviewed-v3/index.html)：Q1所圈六孔组经V1接IT1-M2-B；Q2仍为IT1-M2-B经V2接IT1-M3-BUS。Q1原假设接窄A错误，历史稳定ID IT1-V1-A保留，不能从后缀推承载。只改V1承载/候选阵列和B设计上端，其余金属、原生锚点及Q2保持。

六孔数量来自用户；2列×3行、尺寸/间距/位置及B设计边界仍为AI候选，不是新几何批准或精确投影。A/B是否同层连续仍未知；独立样本A/B不是上文MID分组。当前Q1/Q2均已裁决，无需重问；不是独立全区域或全网完成。

[旧迁移页](docs/assets/conductive-workflow-trial-v1/final-independent/index.html)、[旧父包接续](docs/assets/conductive-workflow-trial-v1/final-resumed/index.html)保留当时Q1=null，作为事前证据，不再表示当前Q1状态。新的人工承载更正通过before/after与实际旧送审包绑定，已知多孔必须保留整组占用，逐孔核包围；不以单框PASS证明多孔能被窄金属承载。

## 共同层与材料不变项

唯一共同快照仍为[configs/joint-work-layer-v5.json](configs/joint-work-layer-v5.json)：AA334/POLY696/CT10287、八张5712×4284照片及哈希不变；导体注册表仍引用[原33记录模型](docs/assets/conductive-stack-v2/model.json)。新局部候选未采用；原图、材料、旧批准未改。

S1/S2/S3身份、G66-P03/P04共用上端桥与蓝色栅CT、退休ROW4-AA4-SD00、四栅与33孔、R1A/R1B上端、R2连续AA单排孔、R2_Q1、V3端子/v33网络、S03-03/04、18电阻、W01及195保留对象均按原范围继承。

六处未知：AA-F01951、AA-F01952、材料层H1/H2（不同于MID-H1/H2）、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS。最后一处不借蓝色栅CT证明源漏有/无孔；V3主体截段历史例外继续有效。未知只限制依赖，不触发整层重做。

net_edges空、automatic_network_export_allowed=false、complete_network=false、共同几何采用关闭。真实尺度、工艺、极性、W/L、阻值及完整网表未知；规则门不是实际PDK DRC。

## 运行、验证与使用

[金属重建skill](skills/silicon-eye-metal-reconstruction/SKILL.md)与[层间孔重建skill](skills/silicon-eye-via-reconstruction/SKILL.md)共用入口；旧[POLY](skills/silicon-eye-poly-reconstruction/SKILL.md)/[CT](skills/silicon-eye-ct-reconstruction/SKILL.md)范围和[追网约定](docs/metal-tracing-workflow-v1.md)不变。

```bash
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/metal-independent-q1-correction-v2/request-scoped-v3.json --output runs/新的试用目录
```

换main-request-v1.json复跑中样，换resume-request-v1.json接续父包；输出目录须新建。输入是AI先完成的观察，非运行时自动视觉识别。支持设计几何局部变化，需父包、实际变化ID和AI提案依据；原生锚点、接口身份、预算、来源门及旧审批不得静默改变。现已支持实际人工裁决绑定的未审接口承载更正；新增/退休/合并ID、改来源或更换已审接口仍需另作事务。

此前相关整合回归123项通过；最终新模块29项通过，恢复后复核同样29项通过（16.12s），存在重叠不相加。Ruff、两skill格式、CLI三包重放、反例拒绝、文件哈希/像素来源、SVG/JS检查通过；浏览器交互未测。本次新增最终workflow模块39项通过（18.09s）；此前workflow+Via联合75项通过（70.12s），重叠不相加。新包CLI重放一致，旧三包模型/报告保持；增加六孔占用、承载更正、范围和再次接续反例。已记录Q1一次实际人工纠正，未测陌生芯片或效率提升。

## 唯一下一步与未提交状态

下一步：使用两个试用skill扩大一处连续区域的金属/接口覆盖，先识别未建模导体和端部、保留已审锚点，再按统一格式形成新候选与复核包；只有出现影响身份/连接的新歧义才请用户裁决。Q1/Q2/U3不重复审批；不借几何门通过宣布全层或整网完成。

Git基线HEAD=6b57db383303a31a892b2226382804a4604cc277（上一轮已推送）；本轮统一模块、模板、测试、试用skills及配套文档/证据为未提交工作，未推送。没有更改原始照片、固定材料结果或已审记录。

[本轮整理前入口完整原文](docs/history/current-task-before-2026-10-24-conductive-workflow-trial.md)已核原字节与SHA，保留旧裁决、恢复命令、历史归档及上一轮提交状态。历史过程按需调取，CURRENT_TASK仍为唯一实时操作入口。

[本次Q1裁决前入口完整归档](docs/history/current-task-before-2026-10-24-Q1-carrier-correction.md)保留当时未知和试用状态，已核原字节与SHA。最新更正仅增加一条有实际人工依据的局部V1承载关系，不改变完整网表/共同几何状态。
