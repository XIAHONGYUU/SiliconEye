<!-- 来源：CURRENT_TASK.md；归档日期：2026-10-19；以下为本轮反馈修订前原文。 -->
# 当前任务

## 目标与授权

2026-10-19：用户批准按五步推进POLY：冻结AA、接续旧POLY标注、局部A/B0/B1对照、验证后全幅、最后封装skill。当前授权本地实施与验证；没有新的Git提交/推送授权。

唯一实时任务入口为本文件。[开发计划](docs/development-plan.md)定义阶段顺序；[前阶段完整入口](docs/history/current-task-before-2026-10-19-poly.md)保留AA历史、裁决和恢复命令。

## 最新成果与验收门

- **第四步首轮全幅候选已生成，尚未完成全幅材料恢复**：[全幅/12块复核页](docs/assets/poly-full-frame-v1/index.html)、[检查点](docs/checkpoints/2026-10-19-poly-full-frame.md)、[完整模型](benchmarks/poly-full-frame-v1/model-v1.json)、[AI初检](benchmarks/poly-full-frame-v1/ai-review-v1.json)。统一5712×4284原生索引，分块仅显示，不切断模型。
- 49组AI重复主体观察，349个新候选，保留4个已审对象，合计353个几何对象；含MOS栅指、宽MOS及18条电阻POLY主体候选。数量均非器件统计。每组首/末完整主体及数量由AI观察声明，中间线性插值；没有运行材料分割或自主识别。
- **22处未解决范围保持未知**：上部短MOS、端部交错、独立衬底竖向MOS、左下短器件与边界裁切等。橙色是观察框，不能当材料图形；空白不当作非POLY。AA只粗上下文，无跨层投影。全幅精确边界、完整性和新材料身份均未验收。
- 4个已审对象逐字段复用：[局部采用模型](benchmarks/poly-vertical-reassessment-v3/accepted-local-model-v1.json)；P-H01位置/宽度通过，竖向v3范围与端部基本合理、无遗漏扩宽/引出，不重问。旧失败B1保留，不把v3通过归功于算法自动恢复完整尺寸。
- [技术核查](benchmarks/poly-full-frame-v1/verification-v1.json)：21项相关测试、Ruff、哈希/资源/JS检查通过；原生及HV几何交叠0；4个已审对象未改，15项冻结来源不变。浏览器交互未自动实测；技术门不等于材料/数量正确。
- **唯一下一步**：用户按全幅/分块指出新候选明显偏移/偏小及宽MOS、电阻POLY主体解释问题；AI进一步处理22处短器件/端部未知，再定向修订。不要将首版候选或规则检查通过当作全幅完成，不重跑已审AA/局部POLY。第五步skill封装仍待全幅验证。
- 前阶段入口完整保存在[归档](docs/history/current-task-before-2026-10-19-poly-full-frame.md)。

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

本轮复现：`.venv/bin/python -m silicon_eye.poly_full_frame --root . --spec benchmarks/poly-full-frame-v1/spec-v1.json --output runs/新的目录`。本轮完整复核资产在docs/assets/poly-full-frame-v1，原图在data；旧依赖仍可用前阶段证据归档恢复。
