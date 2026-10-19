# 归档：CURRENT_TASK.md

日期：2026-10-19；来源：仓库根CURRENT_TASK.md；以下原文完整保留。

# 当前任务

## 当前目标与授权

2026-10-19：用户要求整理顶层文件并继续AA工作。已授权本地整理、局部修订/不同窗口验证、实验版skill准备及全幅原生候选/分块质量检查；没有新的Git提交/推送或付费视觉服务授权。昨日已推送main提交c8ac522。

方法：[AA工作流v9：AI主导、算法辅助、质量提升](docs/architecture/aa-extraction-workflow-v9.md)。全幅外推只保留实验记录，不是当前默认流程。唯一实时状态在本文件；开发计划只定义阶段顺序。

## 唯一下一步：选择另一处竖向或折线AA，冻结同规格细节比较范围

用户授权执行三个任务，现已按v9/skill实际完成：接续与拒绝退化通过；用户进一步确认蓝色B1更贴合AA，细节改善在当前对象范围通过，不宣称全skill通过。没有全图训练/推断、未改原图/原AA模型/CT或人工记录。

- [三任务检查点](docs/checkpoints/2026-10-19-aa-skill-three-tasks.md)、[已审复核页](docs/assets/aa-skill-three-task-v1/reviewed.html)、[冻结任务](benchmarks/aa-skill-three-task-v1/plan-v1.json)、[结果](benchmarks/aa-skill-three-task-v1/report-v1.json)、[核查](benchmarks/aa-skill-three-task-v1/verification-v1.json)。同一Agent已知案例回归，不是独立盲测；被测skill快照锁定。
- T1：S05状态/处理域按字节复用，变化0，不重训、不重复询问双环身份和间隙。
- T2：旧全幅台阶AA对象A、缓存GrabCut候选B0、AI修订并调用既有拟合的正交几何B1同坐标对照；六边/一组件/无孔保持，技术检查通过。用户确认蓝色B1更贴合材料，采用为该对象后续局部工作版本；[人工裁决](benchmarks/aa-skill-three-task-v1/human-review-v1.json)、[采用记录](benchmarks/aa-skill-three-task-v1/acceptance-v1.json)。距离历史AI角点更近仍只作诊断；旧全幅单体模型不追溯覆盖，精确光刻边界和尺度不升级。
- 当前人工核查已完成，不重复询问当前台阶身份/边界或N01–N12。下一步仅选择另一处竖向或折线AA并锁定源图、旧成果和目标细节，再按同一成图标准比较；本轮不启动新提取。
- T3：既有GrabCut在已审跨度内将双环核心连片，按已有隔离裁决拒绝替换并保留S05，无重复人审。只检查局部材料，不推电气连接。
- 相关Ruff、所有锁定输入哈希、输出manifest、页面链接检查通过；原图叠图已作AI视觉检查，浏览器交互未自动实测。没有生产代码修改；独立评测、泛化、精确边界准确率及效率收益仍未验证。无Git提交/推送。
- [前轮接续/比较修订](docs/checkpoints/2026-10-19-aa-control-repair.md)仍生效：已有五例范围直接保留；全幅RF实验不作默认基线；质量优先、局部变化、AI上下文复核和规则几何标准不降低。

## 已完成与关键边界

- 顶层README、开发计划和旧任务入口完整归档，原文与Git上一提交字节一致：[旧README](docs/history/2026-10-19-before-top-level-README.md)、[旧计划](docs/history/2026-10-19-before-top-level-development-plan.md)、[旧当前任务](docs/history/2026-10-19-before-top-level-CURRENT_TASK.md)。README变为导航，不再把愿景列为已完成能力；AGENTS与baseline不改。
- 新[三态局部修订工具](silicon_eye/aa_semantic_revision.py)按AI指定语义、搜索带和原图边缘定位候选；保存-1未知/0候选非AA/1候选AA、处理域、原生曲线及来源。局部近横向带状适用；不支持任意形状、竖环/阶梯或全幅。不是多数票、矩形裁切或自动材料识别。
- [冻结参数](benchmarks/aa-semantic-revision-v1/spec-v1.json)、[报告](benchmarks/aa-semantic-revision-v1/report-v1.json)、[核查](benchmarks/aa-semantic-revision-v1/verification-v1.json)。S05原6中心全部正确；边界/完整mask未审。S02曾见于早期探索，其材料关系现已人审，仍非盲测；精确边界未审。
- [实验版AA skill](skills/silicon-eye-aa-reconstruction/SKILL.md)已创建于仓库，结构验证与同Agent真实协议回放通过；未安装全局、未独立Agent评测；两处带状案例已审，竖环/台阶/折线新候选整体合理性已审，完整边界和全幅未审。根据当前阶段选工具，遇身份/边界未知停止相应部分，不能以skill执行成功越过人工门。
- [笔画裁决](benchmarks/aa-scribble-comparison-v1/human-stroke-review-v1.json)：A01–A05为AA、N01–N04非AA；无N05，不造位置。原12检查中心及既有采样约束保留。[Q1–Q4](benchmarks/aa-context-review-v1/human-context-review-v1.json)：电阻内部误报排除、AA间隙隔离、暗内部不挖空。[Q4澄清](benchmarks/aa-context-review-v1/Q4-scope-clarification-v1.json)：保护电阻外围环下侧AA横条，不错误扩宽；整环/精确内外边界未审。
- 原始八图data/不可改，只用现有照片。尺度、工艺、N/P、S/D、精确W/L和完整连接未知。原生坐标与公共参考变换分开；正交重建在材料门之后，不把倾斜照片边缘直接当最终GDS。
- 正式AA/CT/195保留对象与旧100初始化疑点不变。区域观察skill仅帮助理解/评测，不把区域划分当分层恢复或跨区域走线边界。
- 328测试、相关Ruff、哈希、原文归档完整性、三态/处理域、回放一致及页面JS语法通过；浏览器交互未自动实测。未知不计正确背景，软件PASS不证明材料真值或全幅完成。

## 恢复与按需历史

上一版输出恢复：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/aa-semantic-revision-v1d-evidence.zip --root .`。
重跑：`.venv/bin/python -m silicon_eye.aa_semantic_revision --root . --spec benchmarks/aa-semantic-revision-v1/spec-v1.json --output runs/新的目录`。

昨日7归档、失败对照与复核图：[2026-10-18检查点](docs/checkpoints/2026-10-18-aa-workflow-reviewed.md)。.venv与runs仍忽略；没有将所有历史runs视为已保存。
已审几何、区域分类、PDK回查和原八图来源链接保存在[旧当前任务](docs/history/2026-10-19-before-top-level-CURRENT_TASK.md)。

既有[v33网络](docs/roi2-gate-network-reviewed-v33.md)及旧gate入口撤回等裁决保持；六个AA接入不是六个器件，不穿MOS沟道或电容介质，不猜照片外连接或合并不同历史电极。详细已审路径及恢复命令均在上述旧入口，当前不推进追线。

新版恢复：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/aa-semantic-revision-v2a-evidence.zip --root .`；重跑用spec-v2.json，旧版本保留。

本轮恢复：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/aa-shape-validation-v1e-evidence.zip --root .`；前阶段入口完整保留于[归档](docs/history/current-task-before-2026-10-19-aa-shape-validation.md)。

本轮恢复：按[分卷索引](benchmarks/evidence/aa-native-canvas-v1a-index.json)用evidence_archive逐份恢复，全部分卷须齐备；[全幅前入口完整归档](docs/history/current-task-before-2026-10-19-aa-native-canvas.md)。

纠偏前任务入口原文：[归档](docs/history/current-task-before-2026-10-19-aa-control-repair.md)。

质量目标纠偏前入口原文：[归档](docs/history/current-task-before-2026-10-19-aa-quality-first.md)。

本轮前任务入口原文：[归档](docs/history/current-task-before-2026-10-19-aa-three-tasks.md)。

当前台阶验收前入口原文：[归档](docs/history/current-task-before-2026-10-19-aa-detail-accepted.md)。
