# 当前任务

## 当前目标与完成状态

2026-10-21用户批准分别封装“POLY重建”和“CT重建”，并完成统一输入输出、接续规则、独立Agent试用三项收尾。现已完成仓库内人机协作v1；未重新提取全幅，未采纳新的材料几何，未新增人工裁决。本轮用户已授权提交并推送GitHub；执行前远端核对仍为6e5bb17，正在发布已有成果并评估金属／层间孔的skill边界。全局安装不在范围内。

本文件为唯一实时入口。[POLY skill](skills/silicon-eye-poly-reconstruction/SKILL.md)、[CT skill](skills/silicon-eye-ct-reconstruction/SKILL.md)、[共用契约](docs/architecture/layer-reconstruction-skill-contract-v1.md)、[封装验证报告](docs/reviews/2026-10-21-poly-ct-skills.md)、[POLY样稿](docs/assets/poly-skill-package-v1/index.html)、[CT样稿](docs/assets/ct-skill-package-v1/index.html)。skill可按明确仓库路径读取，未安装全局。

## 当前唯一共同工作层

[当前快照v3](configs/joint-work-layer-v3.json)仍为AA334／POLY696／CT10287。696包含G66-P03/P04上端桥，不代表新增MOS。设计画布5860×4587；8张原图5712×4284及哈希、相对预算、历史裁决完整保留。源图与冻结父包不改；历史AA337／POLY700及单层旧清单不能覆盖当前层。

- S1三列身份／相对位置与S2显示修订已批准。72条来源修订保留，旧16对争用及新争用均0；批准不扩大为全层逐孔／像素边界。
- S3人工纠正生效：紫色为ROW4-AA3源漏CT；蓝色为G66-P03／P04共用POLY向上栅CT。蓝色当前ID为CT-G66-P03-P04-SHARED-TOP-01，目标G66-P03-P04-TOP-BUS；旧ROW4-AA4-SD00错误CT退休。新桥／孔精确几何仍AI候选，编号映射仍局部AI索引，不伪装人审像素真值。
- 已审身份硬门拒绝蓝色改AA、紫色目标改变、旧身份复活、共用成员丢失；几何与来源无争用不能代替身份核验。[实施与裁决](docs/reviews/2026-10-21-source-ownership-adjudication.md)、[人工复核页](docs/assets/ct-source-ownership-reviewed-v2/index.html)。
- 退休别名、G68合法桥、G26阶梯AA局部截面、AA最新层适配、变化域保护继续有效。仅重算有明确证据的影响范围，跨层修订一次联合检查，候选不自动晋级。

## 保留未知、批准与使用边界

六处来源／接入限制：AA-F01951、AA-F01952、H1、H2、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS。最后一处不独立证明另有源漏孔，也不证明无孔；不能借用蓝色栅CT或补孔。V3两主体截段历史端子例外另列。均无当前新增人工问题，未知仅阻塞相应依赖。

工程收口、几何PASS与已审显示范围不升级为100%物理恢复、整层像素批准、M1连接或网表。`automatic_network_export_allowed=false`；物理尺度、工艺、极性、真实W/L及阻值未知，无真实PDK DRC/LVS。

四栅G06R-P01～P04及33孔、R1A／R1B上端与均匀源漏、R2本处连续AA单排孔、旧Q1／Q2／Q3继续有效；邻环隔离不变。C/D/F、143橙框、RIGHT6、宽MOS／环／电阻、Q2栅60孔、上方40栅、左侧局部、661环孔及B孔数精度意见保留原范围。R2_Q1、V3端子、网络v33、S03-03/04、18电阻、W01身份及195保留对象不改。原父包与本轮前入口完整保留，不把旧S3源漏解释带回当前任务。

## 本轮验证与接续命令

- 25项相关测试通过（103.66s），相关Ruff及git diff --check通过；两个skill包装校验通过。两个样稿空delta，输入／产物哈希、源裁片、SVG和JS语法核对通过；未声称浏览器点击验收。
- 两个无本轮聊天历史的Agent分别拒绝POLY截短与CT错误归属，当前inspect均PASS；主Agent核对四包输入／产物／代码哈希、全部继承文档及六处未知。原始试用与主Agent核验在[固定验证包](benchmarks/poly-ct-skill-validation-v1/primary-agent-verification-v1.json)。未实测的人工纠正次数保持null。
- POLY首轮待评请求源窗口没覆盖对象，试用已发现并修复导航；原始请求/指令/试用保留，修正窗口重放仍拒绝同一错误几何。已补入skill提醒；不把重放计为新盲测。这是已知芯片开卷接续验证，不能证明陌生照片识别准确率或泛化。
- 统一交付：`.venv/bin/python -m silicon_eye.layer_review --request configs/poly-skill-review-v1.json --output runs/新的复核目录`；CT替换为`configs/ct-skill-review-v1.json`。inspect不生成新模型；revise用明确before／after、证据和操作ID范围，允许跨层事务，硬FAIL仅保留拒绝诊断，不导出候选快照。输出目录须新建。
- 当前联合检查：`.venv/bin/python -m silicon_eye.joint_layers --snapshot configs/joint-work-layer-v3.json --output runs/新的联合检查目录`。原生定位不等于精确投影；多观察合并AA不得套单一旧投影。AI观察格式沿用既有agent_observations，不能自行人审确认。

## 唯一下一步

当前先完成GitHub同步，再基于现有架构评估金属重建与层间孔重建的skill粒度；不在本轮实现新skill、提取M1或追全网。不重审S1／S2，不重做全幅AA／POLY／CT。

[本阶段前入口完整原文](docs/history/current-task-before-2026-10-21-poly-ct-skills.md)保留此前状态、恢复命令和历史链接；[此前身份阶段原文](docs/history/current-task-before-2026-10-21-source-identity-adjudication.md)继续可查。`runs/`仅本地，当前技能验证产物已复制到Git可追踪的benchmarks路径。

[本轮发布与金属架构评估前入口原文](docs/history/current-task-before-2026-10-21-github-metal-assessment.md)保留上阶段完整状态。
