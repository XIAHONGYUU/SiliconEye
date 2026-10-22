# 当前任务入口归档

来源：CURRENT_TASK.md；归档日期：2026-10-21；原文SHA256：172f34027eec9c1cbf63ce82daa1fe11d05e46eafed1357bc84bca0ff5bcecc6。

---

# 当前任务

## 当前目标与完成状态

用户授权按既有经验验证M1小样。已在Q2上左阶梯组生成9项规则M1伴随候选：竖条、两条U形走线、外围环段和右邻长条；几何检查通过、87个源漏CT模型包围通过，等待Q1–Q3新M1结构裁决。8个栅CT的精确M1落点仍待定，二维投影未放行；本轮未改变AA/POLY/CT或确认网络。

[当前M1复核页](docs/assets/m1-geometry-pilot-v1/index.html)、[检查点与三项核对清单](docs/checkpoints/2026-10-21-m1-geometry-pilot.md)、[输入](benchmarks/m1-geometry-pilot-v1/spec-v1.json)、[质量报告](docs/assets/m1-geometry-pilot-v1/report.json)。M1小样及本轮代码尚未提交／推送；上一已核对GitHub版本为a769561。POLY／CT两个仓库skill v1与此前证据已发布；本轮未创建金属/Via占位skill或安装全局skill。

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

## 已有POLY／CT封装验证与接续命令

- 25项相关测试通过（103.66s），相关Ruff及git diff --check通过；两个skill包装校验通过。两个样稿空delta，输入／产物哈希、源裁片、SVG和JS语法核对通过；未声称浏览器点击验收。
- 两个无本轮聊天历史的Agent分别拒绝POLY截短与CT错误归属，当前inspect均PASS；主Agent核对四包输入／产物／代码哈希、全部继承文档及六处未知。原始试用与主Agent核验在[固定验证包](benchmarks/poly-ct-skill-validation-v1/primary-agent-verification-v1.json)。未实测的人工纠正次数保持null。
- POLY首轮待评请求源窗口没覆盖对象，试用已发现并修复导航；原始请求/指令/试用保留，修正窗口重放仍拒绝同一错误几何。已补入skill提醒；不把重放计为新盲测。这是已知芯片开卷接续验证，不能证明陌生照片识别准确率或泛化。
- 统一交付：`.venv/bin/python -m silicon_eye.layer_review --request configs/poly-skill-review-v1.json --output runs/新的复核目录`；CT替换为`configs/ct-skill-review-v1.json`。inspect不生成新模型；revise用明确before／after、证据和操作ID范围，允许跨层事务，硬FAIL仅保留拒绝诊断，不导出候选快照。输出目录须新建。
- 当前联合检查：`.venv/bin/python -m silicon_eye.joint_layers --snapshot configs/joint-work-layer-v3.json --output runs/新的联合检查目录`。原生定位不等于精确投影；多观察合并AA不得套单一旧投影。AI观察格式沿用既有agent_observations，不能自行人审确认。

## 金属／层间孔评估与唯一下一步

[架构评估](docs/architecture/metal-via-skill-boundary-assessment-v1.md)建议按任务封装金属重建、层间过孔重建两个通用skill，以层ID／层对、证据帧、相对预算和特殊结构配置区分M1/M2等实例；每层独立验收，CT与网络追踪保留自身任务边界。共用skill不等于共用一组数值规则、取消逐层质量门或已经验证所有金属。官方PDK已回查，当前芯片工艺/尺度仍未知。此为架构建议，本轮只验证M1几何小样，未创建通用金属/Via skill或实现V1抽取。

发布前复跑25项相关测试通过（96.18s），相关Ruff、锁定输入与release哈希、git diff --check通过。发布使用现有XIAHONGYUU登录身份及已配置的noreply作者，不改变全局Git配置；提交和远端以本轮Git核验为准。

M1小样机器初检：16项相关测试通过，正交、连续、相互隔离及候选87孔包围通过，最小对象间距8设计像素。局部x列序用两列拟合、一列留出，误差约3原生像素，达到本样本上限；只支持宏观列序，y未独立核准，不能作为精确CT投影。原8图、全部继承文档和六处未知不变，自动网络导出关闭。样稿提供全图定位、原图/观察线与设计图切层。

唯一下一步：收录复核页Q1（P01–P05/P09竖条）、Q2（P06/P07两条U的结构与隔离）、Q3（P08连续环段及出窗端）裁决；再核清该范围y/二维对应及8个栅CT落点，不能强行扩宽金属包围孔。之后才进入M1／V1／M2联合小样。不重审旧CT、S1／S2，不重做全幅AA／POLY／CT或追全网。

M1复跑：`.venv/bin/python -m silicon_eye.metal_reconstruction --spec benchmarks/m1-geometry-pilot-v1/spec-v1.json --output runs/新的M1小样目录`。AI负责原图结构观察，脚本生成规则几何与固定检查；M1是引用当前快照的候选伴随层，不改共同清单、不复用POLY字段。

[本阶段前入口完整原文](docs/history/current-task-before-2026-10-21-poly-ct-skills.md)保留此前状态、恢复命令和历史链接；[此前身份阶段原文](docs/history/current-task-before-2026-10-21-source-identity-adjudication.md)继续可查。`runs/`仅本地，当前技能验证产物已复制到Git可追踪的benchmarks路径。

[本轮发布与金属架构评估前入口原文](docs/history/current-task-before-2026-10-21-github-metal-assessment.md)保留上阶段完整状态。

[进入M1小样前入口完整原文](docs/history/current-task-before-2026-10-21-m1-pilot.md)可回查已发布状态及上一节点。
