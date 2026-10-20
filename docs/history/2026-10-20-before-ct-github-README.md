# 归档：CT日终保存前README

来源：README.md；日期：2026-10-20。以下为完整原文。

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

[RIGHT6局部CT已审基准](docs/checkpoints/2026-10-20-right6-ct-reviewed.md)：42个源漏CT、共栅POLY及11个栅CT已通过显示复核；原橙色位置以人工证据纳入。[已审页面](docs/assets/ct-right6-reviewed-v5/index.html)保留原图与设计图。其他区域、工艺尺寸及M1连接未完成确认。

[CT局部修订 v2](docs/checkpoints/2026-10-20-ct-transfer-revision.md)已生成[两项改动复核页](docs/assets/ct-transfer-revision-v2/index.html)：宽MOS与首条电阻端部已审；六管共栅端部按原图相对比例修订，环左上子段补查为32横＋15竖孔；两项已获批准，130 CT及材料模型已锁定为后续防退化基准。原始验收快照保留。

[环与18条电阻端部扩展](docs/checkpoints/2026-10-20-ct-ring-resistor-extension.md)提供[新范围复核页](docs/assets/ct-ring-resistor-extension-v1/index.html)：新增661个有照片峰支持的CT候选，已审130孔及AA/POLY不变。保留未明槽位；用户认可局部连接关系基本无问题，同环/同阵列CT几何一致性仍待优化。

[第一批中部MOS CT候选](docs/checkpoints/2026-10-20-ct-middle-mos.md)已生成[A/B/C复核页](docs/assets/ct-middle-mos-v1/index.html)：新增630源漏＋356环CT已获批准，原791记录及材料不变；AA边缘孔不因靠近POLY改判栅CT，[48处橙框已获补充确认](docs/checkpoints/2026-10-20-ct-middle-mos-confirmed.md)，[当前复核页](docs/assets/ct-middle-mos-confirmed-v2/index.html)保留原1777记录并新增48个人工确认CT；栅极主体已表达，栅端CT未专项检测，不等同图像无法识别。

[Q2栅端与引出专项检查](docs/checkpoints/2026-10-20-q2-gate-terminal-inspection.md)已提供[30栅极端部／M1候选对照页](docs/assets/q2-gate-terminal-inspection-v1/index.html)：保留1825 CT与材料，A/B下端亮条包含栅CT且本组全部下端引出已获确认；逐栅孔数/边界及共栅关系仍未知，局部配准未过精确端口门。

[Q2栅CT位置候选](docs/checkpoints/2026-10-20-q2-gate-ct-localization.md)提供[原图／联合图／M1对照页](docs/assets/q2-gate-ct-localization-v1/index.html)：用已审源漏列定位30条栅下端，新增60个POLY CT的位置及每栅两孔已获批准，保留原1825记录与AA/POLY不变；1885孔快照用于后续接续。

[上方同环小MOS三类CT整批](docs/checkpoints/2026-10-20-ct-upper-small-mos.md)提供[一次审批页](docs/assets/ct-upper-small-mos-v1/index.html)：40栅源漏280、栅端80、环413个新增候选，原1885记录和材料不变；51环槽位保留未知，待本批裁决。

## 本地运行

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev,segmentation-eval]'
.venv/bin/python -m pytest -q
```

各工具命令与冻结参数见当前任务及相应实验文档。物理尺度/工艺未知，不输出虚假工艺尺寸或把PDK经验当成照片事实。

## 历史按需阅读

[原README完整归档](docs/history/2026-10-19-before-top-level-README.md)保留早期愿景、能力对比、路线图和使用样例；其中产品愿景不代表当前实现。原开发计划和历史任务入口同样完整归档，由CURRENT_TASK链接定位，不维护多份竞争的实时状态。
