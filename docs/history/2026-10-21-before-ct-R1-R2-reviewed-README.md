# 原文归档

来源：README.md；归档日期：2026-10-21；原文SHA256：41c5657380d4a1ccd378bdfbf76798df272f9044a4a75e6c06183a25d31ae13b。以下保留修订前完整原文，历史状态不作为当前任务。

---

# Silicon Eye

从同一位置的多层芯片照片，逐步恢复材料层、器件与连接，输出可复核的版图、电路和编号视图。

## 从这里开始

| 入口 | 用途 |
| --- | --- |
| [CURRENT_TASK.md](CURRENT_TASK.md) | 唯一实时状态：当前授权、最新验收、未知、下一步 |
| [开发计划](docs/development-plan.md) | 阶段顺序与完成条件 |
| [照片栈总架构](docs/architecture/photo-stack-workflow-v3.md) | 全幅共同坐标与区域观察的边界 |
| [AA工作流v9](docs/architecture/aa-extraction-workflow-v9.md) | AI直接提取与算法辅助修订，共同以质量提升为目标 |
| [固定基线](docs/baseline.md) | 项目基准与限制 |
| [项目规则](AGENTS.md) | 长期执行约定 |

## 当前能力

已实现配准和证据复核工具、区域观察skill、多种AA分割/样本对照和同坐标分歧图；交互Agent结合上下文作材料判断，人工裁决关键语义。已形成有效的局部AA工作方法，已生成局部修订和不同窗口候选；[AA skill v1](skills/silicon-eye-aa-reconstruction/SKILL.md)已在仓库封装为人机协作v1，局部与全幅接续有验证证据，尚未全局安装；当前按[接续与质量控制修订](docs/checkpoints/2026-10-19-aa-control-repair.md)复用成果、限定变更并作前后比较。

全幅材料精确恢复、自动上下文修订、完整器件/网络提取、仿真就绪网表仍未完成。具体实现、软件测试、物理结论和人审范围分别记录，不以候选或程序成功代表验收。

[最新全幅原生坐标检查点](docs/checkpoints/2026-10-19-aa-native-canvas.md)提供12块复核页与AI质量初检，全图候选尚未通过；[形状验证](docs/checkpoints/2026-10-19-aa-shape-validation.md)保留竖环/台阶/折线结果；[带状局部接续](docs/checkpoints/2026-10-19-aa-semantic-pilot.md)保留此前结果。[2026-10-18检查点](docs/checkpoints/2026-10-18-aa-workflow-reviewed.md)保存已推送版本与七份证据归档恢复入口；[已审复核图](docs/assets/aa-context-review-v1/review-sheet.png)可直接查看。原始八图在data/，不可修改；runs/与.venv/不入Git。所有输出保留来源、原生坐标、版本、有效范围和未知状态。

[全幅AA接续与定向修订](docs/checkpoints/2026-10-19-aa-full-frame-workflow.md)提供共同版图、逐对象原图对应和同页切换；R1/R2关键间隙关系已确认，仓库skill已封装为v1；全幅稠密材料真值、精确边界和新芯片泛化仍未验证。

[POLY v3联合重建](docs/checkpoints/2026-10-19-poly-full-frame-v3.md)优先满足AA/POLY相对结构：撤回普通凸形端部、保留已审U10、修订F05范围，生成下中部140条AA关系约束候选。照片坐标与设计坐标分开，未完成全幅联合布局或真实工艺DRC；方法见[联合重建架构](docs/architecture/layout-reconstruction-v1.md)。

[2026-10-19日终状态](docs/checkpoints/2026-10-19-aa-poly-day-close.md)：U05小栅/AA所示对应与整排对齐已审；宽POLY跨层点位对应存疑，下一步先核查位置。完整候选、已审范围和未知分开记录。

[POLY全幅收口候选](docs/checkpoints/2026-10-20-poly-closeout.md)已合并旧模板与局部修订，提供[统一AA/POLY图及Q1–Q4问题清单](docs/assets/poly-closeout-v1/index.html)。尚有数量、材料身份及一处AA间距冲突，质量门继续阻止正式定稿；不重新要求全幅重复验收。

[最新POLY v1工作基线](docs/checkpoints/2026-10-20-poly-v1-working-baseline.md)：Q1/Q2/Q4已批准，Q3右侧按人工确认修正为6条MOS；[统一复核页](docs/assets/poly-closeout-v3/index.html)保留前后对照。383项测试通过，可作为后续CT的工作基线；精确边界、尺度及未明确关系仍保留未知。[v2修订](docs/checkpoints/2026-10-20-poly-closeout-v2.md)作为历史保留。

## CT当前检查点

[CT全幅工作层收口页](docs/assets/ct-work-layer-closeout-v3/index.html)提供AA/POLY/CT/未知开关、全幅联合图、端口证据与来源裁决页。8条旧轨迹及20条零散观察完成调查处置，保留物理未知；撤回33条未审记录、新增234条候选、5条仅修正来源，当前10226条。全部335 AA／696 POLY以及原7044在v2中的记录保留。**最终来源门仍HOLD：新增R1A/R1B上方长MOS栅端及R2近邻环归属待裁决，尚未整层定稿。** 457项全量测试和几何PASS不代替物理验收。[当前任务](CURRENT_TASK.md)是唯一实时入口，[本轮检查点](docs/checkpoints/2026-10-21-ct-work-layer-closeout.md)保存范围、未知和冻结候选说明；[旧Q1/Q2/Q3已裁决页](docs/assets/ct-full-frame-adjudication-v2/index.html)继续保留，不重审。

[CT重建工作流](docs/architecture/ct-reconstruction-workflow-v1.md)记录源图定位、AA/POLY联合约束、规则孔阵列、来源反例隔离和整层质量门。几何PASS、程序测试通过与物理批准分别记录，不能互相替代；工艺及尺度未知，尚未执行真实PDK DRC/LVS。

已审范围按原批准保留：[RIGHT6](docs/checkpoints/2026-10-20-right6-ct-reviewed.md)、[局部迁移修订](docs/checkpoints/2026-10-20-ct-transfer-revision.md)、[Q2栅CT](docs/checkpoints/2026-10-20-q2-gate-ct-localization.md)、[上方小MOS](docs/checkpoints/2026-10-20-ct-upper-small-mos-reviewed.md)、[左侧大MOS修订](docs/checkpoints/2026-10-20-ct-left-large-mos-revision.md)、[中下部C/D/F修订](docs/checkpoints/2026-10-20-ct-lower-middle-mos-revision.md)。[此前README完整原文](docs/history/2026-10-20-before-ct-github-README.md)保留各阶段过程，不能将历史待审文字当作当前状态。

## 本地运行

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev,segmentation-eval]'
.venv/bin/python -m pytest -q
```

各工具命令与冻结参数见当前任务及相应实验文档。物理尺度/工艺未知，不输出虚假工艺尺寸或把PDK经验当成照片事实。

## 历史按需阅读

[原README完整归档](docs/history/2026-10-19-before-top-level-README.md)保留早期愿景、能力对比、路线图和使用样例；其中产品愿景不代表当前实现。原开发计划和历史任务入口同样完整归档，由CURRENT_TASK链接定位，不维护多份竞争的实时状态。
