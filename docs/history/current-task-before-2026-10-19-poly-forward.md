<!-- 来源：CURRENT_TASK.md；归档日期：2026-10-19；以下为本轮方向修订前原文。 -->
# 当前任务

## 目标与授权

2026-10-19：用户批准按五步推进POLY：冻结AA、接续旧POLY标注、局部A/B0/B1对照、验证后全幅、最后封装skill。当前授权本地实施与验证；没有新的Git提交/推送授权。

唯一实时任务入口为本文件。[开发计划](docs/development-plan.md)定义阶段顺序；[前阶段完整入口](docs/history/current-task-before-2026-10-19-poly.md)保留AA历史、裁决和恢复命令。

## 最新成果与验收门

- **全幅POLY v2定向修订已出，尚未验收**：[复核页](docs/assets/poly-full-frame-v2/index.html)、[检查点](docs/checkpoints/2026-10-19-poly-full-frame-v2.md)、[模型](benchmarks/poly-full-frame-v2/model-v1.json)、[逐项反馈](benchmarks/poly-full-frame-v2/human-review-v1.json)、[前后比较](benchmarks/poly-full-frame-v2/before-after-v1.json)。原v1保留，不能再将橙框当作没有POLY或已处理完成。
- 落实反馈：U18补截断POLY；U19/U22排除且无候选交叠；上部及左下短器件/端部已补候选；U10新增单独窗口提出两条栅体候选（不是两个新器件）；G41/G43短排由12暂改11，旧候选ID退休，不更改器件/net ID。
- 5组跨排共同列约束已执行，规则图列差为0，原生照片偏移保留。4个既有局部已审对象逐字段不动，18条电阻规则主体保持；电阻来源投影单独修订为新候选。
- 当前666个几何对象/69组，不是器件数量或准确率；20处详细形状待核范围保留。U20不生成POLY，U21右沿仍无材料候选。新增端部模板仍是AI候选；没有判断CT归属/电连接。
- 下中部AA/POLY局部联合图：4外框角拟合+2内部检查点，残差6.35/7.98原生px，12px为本轮工作预算。**新配准未人工确认，不是全幅配准或物理精度**。AA模型不改，140个对象的联合坐标为派生候选；G43r2-P11（右侧较下短排最右端）AA关系超预算，用橙色虚线显示，保留坐标/AA/POLY多种解释。
- [技术核查](benchmarks/poly-full-frame-v2/verification-v1.json)：25项相关测试、Ruff、HV与原生/规则不交叠、共同列、排除范围、冻结来源和页面静态检查通过。浏览器交互未自动实测，材料/边界/完整性仍未验收。完整证据资产在docs/assets，原始照片不动。
- **唯一下一步**：用户先核查AA/POLY联合图对应及橙色虚线问题、U10和少量新端部样式；AI按裁决定向修订。不要重开既有4个局部或逐个CT人审，不将新增图形数量当质量提升。全幅未完成，POLY skill暂不封装。
- 前入口完整归档：[记录](docs/history/current-task-before-2026-10-19-poly-full-frame-v2.md)。

## 生效裁决与边界

- AA：采用[已审入口](docs/assets/aa-full-frame-workflow-v1/reviewed.html)与[模型](benchmarks/aa-full-frame-workflow-v1/model-v1.json)；[仓库skill v1](skills/silicon-eye-aa-reconstruction/SKILL.md)已封装，未全局安装。R1/R2间非AA，两条竖环虽近但隔离；不重开F/N整图复核。全幅稠密完整性、精确边界和跨芯片泛化未验证。
- POLY：蓝色原标注与ROI2身份已确认，但不是精确像素边界；V3两栅没有通过局部端部POLY相连，远处经金属同网不推翻这一事实。旧修正mask中的0不视为确定非POLY，必须保留拓扑未知与CT下方未知。
- 全幅模型不以AA裁剪POLY；v2仅新增下中部待审局部AA/POLY叠加，POLY可伸出AA。CT亮点只作遮挡候选，不据此分配材料、孔归属或网络。
- AI主导，算法按需改进细节，A/B0/B1按相同成图标准比较；没有改善就保留基线。原图不可改，原生来源与正交规则几何分别保留；未知不计正确背景，不猜照片外连接。
- 原八图、195保留对象、旧网络v33及撤回入口等历史裁决保持。区域分类用于理解和评测，不成为跨区域分层/走线边界。物理尺度/工艺、N/P和真实W/L未知。

## 使用与恢复

- 方法：[POLY局部到全幅工作流](docs/architecture/poly-reconstruction-workflow-v1.md)；[冻结参数](benchmarks/poly-reconstruction-v1/spec-v1.json)。
- 复跑到新目录：`.venv/bin/python -m silicon_eye.poly_reconstruction_review --root . --spec benchmarks/poly-reconstruction-v1/spec-v1.json --output runs/新的目录`。
- 恢复本轮及必要旧输入：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/poly-reconstruction-v1d-evidence.zip --root .`。45项证据空目录恢复与哈希已核查；范围见[清单](benchmarks/poly-reconstruction-v1/evidence-inventory-v1.json)，不声称保存全部历史runs。
- `.venv/`与`runs/`不入Git；复核资产、基准和限定证据归档保存在仓库。开发中v1a/b/c不是独立实验，不纳入多轮效果统计。

本轮复现：`.venv/bin/python -m silicon_eye.poly_full_frame --root . --spec benchmarks/poly-full-frame-v2/spec-v1.json --output runs/新的目录`。本轮完整复核资产在docs/assets/poly-full-frame-v2，原图在data；旧依赖仍可用前阶段证据归档恢复。
