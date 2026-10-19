<!-- 来源：CURRENT_TASK.md；归档日期：2026-10-19；以下保留切换前原文。 -->
# 当前任务

## 当前目标与授权

2026-10-19：用户要求整理顶层文件并继续AA工作。已授权本地整理、局部修订/不同窗口验证、实验版skill准备及全幅原生候选/分块质量检查；没有新的Git提交/推送或付费视觉服务授权。昨日已推送main提交c8ac522。

方法：[AA工作流v9：AI主导、算法辅助、质量提升](docs/architecture/aa-extraction-workflow-v9.md)。全幅外推只保留实验记录，不是当前默认流程。唯一实时状态在本文件；开发计划只定义阶段顺序。

## 当前阶段完成：仓库AA人机协作skill v1已封装；后续按差异驱动接续

用户确认R1/R2之间为非AA，横向结果基本正常，左右竖向环内侧间距虽紧但不接触。关键环结构反馈已闭合；模型核对相符，无需修改图形或重新提取。后续AA任务从下列全幅版本接续，有新证据/明确缺陷才局部修订，不重启F/N块人审。

- [skill v1](skills/silicon-eye-aa-reconstruction/SKILL.md)、[封装清单](benchmarks/aa-full-frame-workflow-v1/skill-release-v1.json)、[封装条件](skills/silicon-eye-aa-reconstruction/references/full-frame-validation.md)。能力范围为当前证据下的AI主导判断、规则几何、全幅接续/定向修订与复核；未安装全局，无新的Git提交/推送。
- 当前全幅工作版本：[已审复核页](docs/assets/aa-full-frame-workflow-v1/reviewed.html)、[检查点](docs/checkpoints/2026-10-19-aa-full-frame-workflow.md)、[模型](benchmarks/aa-full-frame-workflow-v1/model-v1.json)、[参数](benchmarks/aa-full-frame-workflow-v1/spec-v3.json)。人工裁决：[记录](benchmarks/aa-full-frame-workflow-v1/human-review-v1.json)；后续采用：[状态](benchmarks/aa-full-frame-workflow-v1/acceptance-v1.json)。旧报告/页面保持历史，不覆盖追溯。
- R1/R2对应的两个对象在原生/重建几何均无面积交叠，间隙为正；[局部核对](benchmarks/aa-full-frame-workflow-v1/ring-separation-verification-v1.json)。数值只为模型分离检查，不是独立照片测距或物理工艺尺寸；人工批准只覆盖定位框内关系，不扩展到R1父对象框外结构。
- 全幅定向修订只改6个目标，330非目标与72保留AA原样保留，拆分后337有效HV对象、面积交叠0；蓝色台阶原生轮廓逐点原样纳入。12个旧中心由6/12变为12/12符合，仅作已知稀疏回归。34相关测试、Ruff、输入/输出与页面资源/JS语法检查通过，浏览器交互未自动实测。
- 全幅稠密材料完整性/精确边界尚未人工批准，最右30列源边界未由本次定位工具验证，100条历史算法疑点不是真实漏AA清单，均不自动关闭或扩大全幅批准。没有独立Agent/新芯片泛化或效率优势的验证；这些限制写入v1封装声明，不作为反复重做已审区域的理由。
- 默认复用，AI主导，算法按需辅助细节，质量优先；不因间隙窄而填平或并环，不混入CT。下一次执行按当前版本选择明确目标，先作同规格前后比较；出现新关键缺陷再暂停对应范围。

## 已完成与关键边界

- 顶层README、开发计划和旧任务入口完整归档，原文与Git上一提交字节一致：[旧README](docs/history/2026-10-19-before-top-level-README.md)、[旧计划](docs/history/2026-10-19-before-top-level-development-plan.md)、[旧当前任务](docs/history/2026-10-19-before-top-level-CURRENT_TASK.md)。README变为导航，不再把愿景列为已完成能力；AGENTS与baseline不改。
- 新[三态局部修订工具](silicon_eye/aa_semantic_revision.py)按AI指定语义、搜索带和原图边缘定位候选；保存-1未知/0候选非AA/1候选AA、处理域、原生曲线及来源。局部近横向带状适用；不支持任意形状、竖环/阶梯或全幅。不是多数票、矩形裁切或自动材料识别。
- [冻结参数](benchmarks/aa-semantic-revision-v1/spec-v1.json)、[报告](benchmarks/aa-semantic-revision-v1/report-v1.json)、[核查](benchmarks/aa-semantic-revision-v1/verification-v1.json)。S05原6中心全部正确；边界/完整mask未审。S02曾见于早期探索，其材料关系现已人审，仍非盲测；精确边界未审。
- [AA skill v1](skills/silicon-eye-aa-reconstruction/SKILL.md)已在仓库封装，结构验证与同Agent真实协议回放通过；未安装全局、未独立Agent评测；两处带状案例已审，竖环/台阶/折线新候选整体合理性已审，完整边界和全幅未审。根据当前阶段选工具，遇身份/边界未知停止相应部分，不能以skill执行成功越过人工门。
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

全幅接续前任务入口原文：[归档](docs/history/current-task-before-2026-10-19-aa-full-frame-workflow.md)。

封装前任务入口原文：[归档](docs/history/current-task-before-2026-10-19-aa-skill-v1.md)。
