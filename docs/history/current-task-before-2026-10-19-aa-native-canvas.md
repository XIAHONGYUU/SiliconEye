# Archived current task

Source: CURRENT_TASK.md; archived 2026-10-19 at native-canvas checkpoint. Original relative links use project root.

# 当前任务

## 当前目标与授权

2026-10-19：用户要求整理顶层文件并继续AA工作。已授权本地整理、局部修订/不同窗口验证与实验版skill准备；没有新的Git提交/推送或付费视觉服务授权。昨日已推送main提交c8ac522。

方法：[AA工作流v8](docs/architecture/aa-extraction-workflow-v8.md)。最新结果：[形状回归检查点](docs/checkpoints/2026-10-19-aa-shape-validation.md)。唯一实时状态在本文件；开发计划只定义阶段顺序。

## 唯一下一步：连续区域与共同坐标候选输出

V01/P01/B01新候选整体合理性已获[用户验收](benchmarks/aa-shape-validation-v1/human-review-v1.json)，连同S02材料关系和S05两环位置/间隙，已冻结[5个有范围局部基准](benchmarks/aa-skill-baseline-v1.json)。不重复询问这些身份/结构问题。

下一阶段将两条AA路径的局部三态输出接入共同全幅原生坐标候选层，先在一块连续区域验证覆盖、未知和隔离；不是直接全图推广或正式GDS。保持未处理/未知独立，不在冲突区域多数票并网，不继续堆案例坐标专用脚本。此项尚未实现。

- [形状回归交互页](runs/aa-shape-validation-v1e/index.html)、[汇总图](docs/assets/aa-shape-validation-v1/review-sheet.png)、[检查点](docs/checkpoints/2026-10-19-aa-shape-validation.md)。旧轮廓作AI取样/定位先验，新候选是原图分割，不是盲测或自主形状发现。
- [参数](benchmarks/aa-shape-validation-v1/spec-v1.json)、[报告](benchmarks/aa-shape-validation-v1/report-v1.json)、[核查](benchmarks/aa-shape-validation-v1/verification-v1.json)。软件门与新增人审分开；边缘邻居/碎片不自动变确定AA，逐像素边界/未建模范围/电气连接仍未审。
- 334测试、Ruff、skill校验、哈希、全部门重算、九mask不变、归档恢复及JS语法已通过。此次只登记人审和基准，不改算法或mask，不重复软件测试；浏览器交互未自动实测。

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
