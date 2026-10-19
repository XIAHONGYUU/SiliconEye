<!-- Source: CURRENT_TASK.md; archived 2026-10-19 before small-MOS human feedback revision. Original content below. -->
# 当前任务

## 目标与授权

2026-10-19：用户批准按五步推进POLY：冻结AA、接续旧POLY标注、局部A/B0/B1对照、验证后全幅、最后封装skill。当前授权本地实施与验证；没有新的Git提交/推送授权。

唯一实时任务入口为本文件。[开发计划](docs/development-plan.md)定义阶段顺序；[前阶段完整入口](docs/history/current-task-before-2026-10-19-poly.md)保留AA历史、裁决和恢复命令。

## 最新成果与验收门

- **方向已改为联合版图重建**：[架构](docs/architecture/layout-reconstruction-v1.md)。原图/摄影来源对应与设计坐标分开；相对关系与正向结构约束优先，不追求像素投影完全重合。AA/POLY工作几何可在证据下定向联合修订，不改变原图、材料身份/隔离裁决和器件/net编号。
- **POLY v3候选已出**：[复核页](docs/assets/poly-full-frame-v3/index.html)、[检查点](docs/checkpoints/2026-10-19-poly-full-frame-v3.md)、[模型](benchmarks/poly-full-frame-v3/model-v1.json)、[反馈](benchmarks/poly-full-frame-v3/human-review-v1.json)。批量凸形模板撤回，普通未审主体保持矩形及完整端部长度；U10显示范围通过并原样保留，不再询问。
- F05-GATE单独展示扩大矩形范围及接触侧候选；暂将用户F05大MOS定位U01 G27/G28，用户已确认基本满足需求，不声称CT连接已经恢复。U19/U22排除、电阻18条规则主体、4个既有局部及U10两条原图几何保持。
- 下中部140条候选明确关联器件AA，共享列、两端伸出、避环和目标交叠检查通过；模型working_reconstruction_layers指向AA共同坐标的joint设计候选，原摄影复核图另存。本轮仅修POLY即可满足关系，AA模型不动。所列预算为相对像素，不是真实PDK规则。
- [前后比较](benchmarks/poly-full-frame-v3/before-after-v1.json)：用新明确目标核查原投影候选，目标AA无交叠2→0、侵环92→0、下端伸出不足140→0。它们是约束自洽指标，不是独立识别准确率；不能以“挪进AA”证明原候选真实存在。页面下方展示的联合相对关系已获用户认可；不扩大到未展示范围或全幅数量确认。
- [验证](benchmarks/poly-full-frame-v3/verification-v1.json)：30项相关测试、Ruff、来源/既有几何保持、普通矩形、U19/U22排除和页面静态检查通过。照片对应失败时不画来源叠加，但已有明确关系的设计候选仍可生成。浏览器交互未自动实测。
- 全图仍为666对象（含电阻等，非器件数量），20处详细形状范围与U21右沿等未关闭；未完成全幅联合布局/真实PDK DRC/LVS/物理尺寸或网络恢复，POLY skill不封装。
- **最新人工复核**：[记录](benchmarks/poly-full-frame-v3/human-review-v2.json)。页面下方新旧联合图通过，F05-GATE基本满足需求；F01–F04原橙框小MOS栅识别未通过。规则生成/正交检查不替代识别门；该次仅记裁决；本轮后续局部修订见下。
- **上方小MOS局部稿**：[入口](docs/assets/poly-small-mos-local-v1/index.html)、[检查点](docs/checkpoints/2026-10-19-poly-small-mos-local.md)。S01/S02共8条单独修订，658个其他对象保持；D02另存7条未合并来源候选，取代旧5槽的提议尚待裁决。D03/D04未修，F01–F04未整体核清。14项相关测试和规则检查通过，识别门未通过；AA并列上下文未精确配准，新几何未安排到共同AA设计坐标。
- **唯一下一步**：用户核对S01/S02端部及D02的03/04两条紧邻主体是否为独立栅。通过后明确局部数量与AA对应，再安排共同设计坐标及扩展同类修订。保留下方已审联合图/F05/U10；不重问整图、不直接重跑旧模板。持久修订输入为benchmarks/poly-small-mos-local-v1/spec-v1.json。
- 本次验收前入口完整归档：[记录](docs/history/current-task-before-2026-10-19-poly-small-local.md)。此前历史沿归档链接回查。

## 生效裁决与边界

- AA：采用[已审入口](docs/assets/aa-full-frame-workflow-v1/reviewed.html)与[模型](benchmarks/aa-full-frame-workflow-v1/model-v1.json)；[仓库skill v1](skills/silicon-eye-aa-reconstruction/SKILL.md)已封装，未全局安装。R1/R2间非AA，两条竖环虽近但隔离；不重开F/N整图复核。全幅稠密完整性、精确边界和跨芯片泛化未验证。
- POLY：蓝色原标注与ROI2身份已确认，但不是精确像素边界；V3两栅没有通过局部端部POLY相连，远处经金属同网不推翻这一事实。旧修正mask中的0不视为确定非POLY，必须保留拓扑未知与CT下方未知。
- 摄影来源模型不以AA裁剪POLY；v3新增下中部AA关系约束的独立设计候选，POLY可伸出AA。CT亮点只作遮挡候选，不据此分配材料、孔归属或网络。
- AI主导，算法按需改进细节，A/B0/B1按相同成图标准比较；没有改善就保留基线。原图不可改，原生来源与正交规则几何分别保留；未知不计正确背景，不猜照片外连接。
- 原八图、195保留对象、旧网络v33及撤回入口等历史裁决保持。区域分类用于理解和评测，不成为跨区域分层/走线边界。物理尺度/工艺、N/P和真实W/L未知。

## 使用与恢复

- 方法：[POLY局部到全幅工作流](docs/architecture/poly-reconstruction-workflow-v1.md)；[冻结参数](benchmarks/poly-reconstruction-v1/spec-v1.json)。
- 复跑到新目录：`.venv/bin/python -m silicon_eye.poly_reconstruction_review --root . --spec benchmarks/poly-reconstruction-v1/spec-v1.json --output runs/新的目录`。
- 恢复本轮及必要旧输入：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/poly-reconstruction-v1d-evidence.zip --root .`。45项证据空目录恢复与哈希已核查；范围见[清单](benchmarks/poly-reconstruction-v1/evidence-inventory-v1.json)，不声称保存全部历史runs。
- `.venv/`与`runs/`不入Git；复核资产、基准和限定证据归档保存在仓库。开发中v1a/b/c不是独立实验，不纳入多轮效果统计。

本轮复现：`.venv/bin/python -m silicon_eye.poly_full_frame --root . --spec benchmarks/poly-full-frame-v3/spec-v1.json --output runs/新的目录`。本轮完整复核资产在docs/assets/poly-full-frame-v3，原图在data；旧依赖仍可用前阶段证据归档恢复。

局部复现：`.venv/bin/python -m silicon_eye.poly_local_revision --root . --spec benchmarks/poly-small-mos-local-v1/spec-v1.json --output runs/新的目录`。不把旧全幅模板重跑作为本轮补丁的接续。
