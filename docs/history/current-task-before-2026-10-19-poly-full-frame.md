<!-- 来源：CURRENT_TASK.md；归档日期：2026-10-19；以下为本轮前原文。 -->
# 当前任务

## 目标与授权

2026-10-19：用户批准按五步推进POLY：冻结AA、接续旧POLY标注、局部A/B0/B1对照、验证后全幅、最后封装skill。当前授权本地实施与验证；没有新的Git提交/推送授权。

唯一实时任务入口为本文件。[开发计划](docs/development-plan.md)定义阶段顺序；[前阶段完整入口](docs/history/current-task-before-2026-10-19-poly.md)保留AA历史、裁决和恢复命令。

## 最新成果与验收门

- **前三步局部门已完成**：AA冻结、POLY历史接续、横向/竖向局部比较。P-H01蓝色位置/宽度合理；P-V01 v3主体/端部基本合理、范围接近实际，无明显方向偏差、无遗漏扩宽或引出。局部批准不扩展为全幅批准。
- [已审竖向页](docs/assets/poly-vertical-reassessment-v3/reviewed.html)、[人工原话](benchmarks/poly-vertical-reassessment-v3/human-review-v1.json)、[采用状态](benchmarks/poly-vertical-reassessment-v3/acceptance-v1.json)、[检查点](docs/checkpoints/2026-10-19-poly-vertical-reassessment.md)。本轮没有重绘，也不再追问这两条栅的已审范围。
- [采用局部模型](benchmarks/poly-vertical-reassessment-v3/accepted-local-model-v1.json)：两条横向和两条竖向对象，来源使用全幅POLY原生坐标，规则几何仍是逐对象局部对应，不是共同全幅配准。保留横向端部未知和旧CT/拓扑未知；竖向显示范围的遗漏疑点已关闭，精确像素边界/物理尺寸未测量。
- v1竖向偏小失败对照保留；v3通过来自AI宽上下文重新观察，不证明原算法可恢复完整尺寸。算法只改法向且固定core长度的局限已明确；完整范围门仍生效。35项前阶段相关测试、Ruff及输入/输出/页面静态核查通过，不代替物理真值。
- **唯一下一步：进入第四步全幅POLY候选重建**。复用这四个对象，AI先理解全幅器件与AA/POLY结构，识别完整主体/端部范围，再按需算法辅助；原生画布连续保留，分块仅用于检查，不反复重审既有对象。只将新增材料/形状歧义交用户。第五步POLY skill封装等待全幅验证。
- 本轮前入口完整保存在[归档](docs/history/current-task-before-2026-10-19-poly-accepted.md)。原v1、v2、v3候选报告与页面保持历史，不覆盖已存哈希。

## 生效裁决与边界

- AA：采用[已审入口](docs/assets/aa-full-frame-workflow-v1/reviewed.html)与[模型](benchmarks/aa-full-frame-workflow-v1/model-v1.json)；[仓库skill v1](skills/silicon-eye-aa-reconstruction/SKILL.md)已封装，未全局安装。R1/R2间非AA，两条竖环虽近但隔离；不重开F/N整图复核。全幅稠密完整性、精确边界和跨芯片泛化未验证。
- POLY：蓝色原标注与ROI2身份已确认，但不是精确像素边界；V3两栅没有通过局部端部POLY相连，远处经金属同网不推翻这一事实。旧修正mask中的0不视为确定非POLY，必须保留拓扑未知与CT下方未知。
- 本轮未投影AA到POLY，不以AA裁剪POLY；POLY可伸出AA。CT亮点只作遮挡候选，不据此分配材料、孔归属或网络。
- AI主导，算法按需改进细节，A/B0/B1按相同成图标准比较；没有改善就保留基线。原图不可改，原生来源与正交规则几何分别保留；未知不计正确背景，不猜照片外连接。
- 原八图、195保留对象、旧网络v33及撤回入口等历史裁决保持。区域分类用于理解和评测，不成为跨区域分层/走线边界。物理尺度/工艺、N/P和真实W/L未知。

## 使用与恢复

- 方法：[POLY局部到全幅工作流](docs/architecture/poly-reconstruction-workflow-v1.md)；[冻结参数](benchmarks/poly-reconstruction-v1/spec-v1.json)。
- 复跑到新目录：`.venv/bin/python -m silicon_eye.poly_reconstruction_review --root . --spec benchmarks/poly-reconstruction-v1/spec-v1.json --output runs/新的目录`。
- 恢复本轮及必要旧输入：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/poly-reconstruction-v1d-evidence.zip --root .`。45项证据空目录恢复与哈希已核查；范围见[清单](benchmarks/poly-reconstruction-v1/evidence-inventory-v1.json)，不声称保存全部历史runs。
- `.venv/`与`runs/`不入Git；复核资产、基准和限定证据归档保存在仓库。开发中v1a/b/c不是独立实验，不纳入多轮效果统计。
