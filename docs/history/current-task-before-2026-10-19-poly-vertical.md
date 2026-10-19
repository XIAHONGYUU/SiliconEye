<!-- 来源：CURRENT_TASK.md；归档日期：2026-10-19；以下保留本轮前原文。 -->
# 当前任务

## 目标与授权

2026-10-19：用户批准按五步推进POLY：冻结AA、接续旧POLY标注、局部A/B0/B1对照、验证后全幅、最后封装skill。当前授权本地实施与验证；没有新的Git提交/推送授权。

唯一实时任务入口为本文件。[开发计划](docs/development-plan.md)定义阶段顺序；[前阶段完整入口](docs/history/current-task-before-2026-10-19-poly.md)保留AA历史、裁决和恢复命令。

## 最新成果与验收门

- **第一、二步完成**：AA工作版本与验收范围已冻结，旧蓝色POLY标注、V3修正、两类未知mask、ROI2材料身份已接回。[冻结基线](benchmarks/poly-reconstruction-v1/baseline-v1.json)。
- **第三步局部反馈已收到，竖向完整范围未通过**：[POLY切换复核页](docs/assets/poly-reconstruction-v1/index.html)、[检查点](docs/checkpoints/2026-10-19-poly-reconstruction.md)、[报告](benchmarks/poly-reconstruction-v1/report-v1.json)。P-H01横向双栅、P-V01竖向双栅、P-E01横向案例端部细节；三个视图仅两个独立物理案例。
- A为AI直接观察主体，B0为局部GrabCut可见支持，B1为算法辅助的规则几何候选；已审旧mask保持不动。新边界不是已审像素真值，矩形封口不代表真实栅端。
- 35项相关测试、Ruff、冻结来源与输出哈希、正交边和分离、未知状态、坐标矩阵、页面资源/JS语法检查通过。[核查](benchmarks/poly-reconstruction-v1/verification-v1.json)。浏览器交互未自动实测，质量提升尚待材料复核。
- **新裁决**：[反馈](benchmarks/poly-reconstruction-v1/human-review-v2.json)：P-H01蓝色位置/宽度合理；P-V01蓝色比黄色贴合，但实际尺寸明显偏小，不能采用为完整外形。横向批准保留，不重问。
- **原因**：旧core误作主体范围，算法只调法向、切线长度不变；几何规则/不交叠门不能发现完整尺寸不足。仅属内部片段时必须阻止升级完整layer。当前工具尚未恢复完整端部。
- **唯一下一步**：AI结合AA沟道、POLY连续形状与上下层上下文，先识别P-V01完整候选范围，核查局部对应，再辅助修边；不能只扩大算法半径或把旧core复制到全图。第四、五步仍未完成。
- [最新反馈/宽上下文页](docs/assets/poly-reconstruction-context-v2/index.html)并列AA/POLY原生窗口，无跨层投影；未产生新几何，不声称尺寸修复已完成。[本轮前入口](docs/history/current-task-before-2026-10-19-poly-context.md)保留原文。

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
