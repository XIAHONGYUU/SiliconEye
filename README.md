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

已实现配准和证据复核工具、区域观察及AA重建skill、多种AA分割/样本对照和同坐标分歧图；交互Agent结合上下文作材料判断，人工裁决关键语义。已形成有效的局部AA工作方法，已生成局部修订和不同窗口候选；[AA skill v1](skills/silicon-eye-aa-reconstruction/SKILL.md)已在仓库封装为人机协作v1，局部与全幅接续有验证证据，尚未全局安装；当前按[接续与质量控制修订](docs/checkpoints/2026-10-19-aa-control-repair.md)复用成果、限定变更并作前后比较。

全幅材料精确恢复、自动上下文修订、完整器件/网络提取、仿真就绪网表仍未完成。具体实现、软件测试、物理结论和人审范围分别记录，不以候选或程序成功代表验收。

[最新全幅原生坐标检查点](docs/checkpoints/2026-10-19-aa-native-canvas.md)提供12块复核页与AI质量初检，全图候选尚未通过；[形状验证](docs/checkpoints/2026-10-19-aa-shape-validation.md)保留竖环/台阶/折线结果；[带状局部接续](docs/checkpoints/2026-10-19-aa-semantic-pilot.md)保留此前结果。[2026-10-18检查点](docs/checkpoints/2026-10-18-aa-workflow-reviewed.md)保存已推送版本与七份证据归档恢复入口；[已审复核图](docs/assets/aa-context-review-v1/review-sheet.png)可直接查看。原始八图在data/，不可修改；runs/与.venv/不入Git。所有输出保留来源、原生坐标、版本、有效范围和未知状态。

[全幅AA接续与定向修订](docs/checkpoints/2026-10-19-aa-full-frame-workflow.md)提供共同版图、逐对象原图对应和同页切换；R1/R2关键间隙关系已确认，仓库skill已封装为v1；全幅稠密材料真值、精确边界和新芯片泛化仍未验证。

[POLY v3联合重建](docs/checkpoints/2026-10-19-poly-full-frame-v3.md)优先满足AA/POLY相对结构：撤回普通凸形端部、保留已审U10、修订F05范围，生成下中部140条AA关系约束候选。照片坐标与设计坐标分开，未完成全幅联合布局或真实工艺DRC；方法见[联合重建架构](docs/architecture/layout-reconstruction-v1.md)。

[2026-10-19日终状态](docs/checkpoints/2026-10-19-aa-poly-day-close.md)：U05小栅/AA所示对应与整排对齐已审；宽POLY跨层点位对应存疑，下一步先核查位置。完整候选、已审范围和未知分开记录。

[POLY全幅收口候选](docs/checkpoints/2026-10-20-poly-closeout.md)已合并旧模板与局部修订，提供[统一AA/POLY图及Q1–Q4问题清单](docs/assets/poly-closeout-v1/index.html)。尚有数量、材料身份及一处AA间距冲突，质量门继续阻止正式定稿；不重新要求全幅重复验收。

[最新POLY v1工作基线](docs/checkpoints/2026-10-20-poly-v1-working-baseline.md)：Q1/Q2/Q4已批准，Q3右侧按人工确认修正为6条MOS；[统一复核页](docs/assets/poly-closeout-v3/index.html)保留前后对照。383项测试通过，可作为后续CT的工作基线；精确边界、尺度及未明确关系仍保留未知。[v2修订](docs/checkpoints/2026-10-20-poly-closeout-v2.md)作为历史保留。

## CT当前检查点

当前共同快照由[CURRENT_TASK](CURRENT_TASK.md)定位；最新为AA334／POLY696／CT10287，六处来源／接入限制保留。S3人工纠正已落实为共用POLY栅CT与源漏CT的不同身份，几何、来源及人审身份分门检查。新精确轮廓仍为AI候选，不宣称100%物理恢复、整层像素批准或M1／网表确认。

[POLY重建skill](skills/silicon-eye-poly-reconstruction/SKILL.md)与[CT重建skill](skills/silicon-eye-ct-reconstruction/SKILL.md)已在仓库封装v1；共用[输入输出与局部接续契约](docs/architecture/layer-reconstruction-skill-contract-v1.md)、[交付／验证报告](docs/reviews/2026-10-21-poly-ct-skills.md)。[POLY样稿](docs/assets/poly-skill-package-v1/index.html)和[CT样稿](docs/assets/ct-skill-package-v1/index.html)提供旧新模型与可切换层；skill可以按仓库路径读取，未作全局安装。

[CT工作层早期工程收口](docs/assets/ct-work-layer-final-v5/index.html)及[收口检查点](docs/checkpoints/2026-10-21-ct-working-layer-v1-closeout.md)保留当时的695 POLY／五处限制等历史数值；已由后续共同快照接续，不可作为当前模型入口。

[CT重建工作流](docs/architecture/ct-reconstruction-workflow-v1.md)记录源图定位、AA/POLY联合约束、规则孔阵列、来源反例隔离和整层质量门。几何PASS、程序测试通过与物理批准分别记录，不能互相替代；工艺及尺度未知，尚未执行真实PDK DRC/LVS。

已审范围按原批准保留：[RIGHT6](docs/checkpoints/2026-10-20-right6-ct-reviewed.md)、[局部迁移修订](docs/checkpoints/2026-10-20-ct-transfer-revision.md)、[Q2栅CT](docs/checkpoints/2026-10-20-q2-gate-ct-localization.md)、[上方小MOS](docs/checkpoints/2026-10-20-ct-upper-small-mos-reviewed.md)、[左侧大MOS修订](docs/checkpoints/2026-10-20-ct-left-large-mos-revision.md)、[中下部C/D/F修订](docs/checkpoints/2026-10-20-ct-lower-middle-mos-revision.md)。[此前README完整原文](docs/history/2026-10-20-before-ct-github-README.md)保留各阶段过程，不能将历史待审文字当作当前状态。

[2026-10-21实施前审计](docs/reviews/2026-10-21-aa-poly-ct/report.md)保留当时的接口／质量门缺陷与来源疑点；其中接续、联合检查及三处来源疑点已按下述实施记录分别处理。收口版本已推送6e5bb17，后续本机修改状态查CURRENT_TASK。

[三层接续与联合质量门实施记录](docs/reviews/2026-10-21-joint-continuation/report.md)保留引用、共享结构及跨层退化检查的实现验证；当时保留的来源疑点已在本轮继续修订。

[三处来源修订v1](docs/reviews/2026-10-21-source-ownership.md)保留原争用诊断。用户随后批准S1／S2，并纠正S3蓝色为共用POLY栅端CT；已退休错误源漏身份、补上共用上端POLY，并加人审身份硬门。[当前共同清单v3](configs/joint-work-layer-v3.json)、[新版复核页](docs/assets/ct-source-ownership-reviewed-v2/index.html)及[裁决实施报告](docs/reviews/2026-10-21-source-ownership-adjudication.md)记录最新状态。

## 金属／层间孔的后续架构

[skill边界评估](docs/architecture/metal-via-skill-boundary-assessment-v1.md)建议“金属重建＋层间过孔重建”两个通用skill，用各层／层对配置与独立质量门表达差异。CT与网络点亮保留独立任务边界。先以M1及M1／V1／M2小样验证，再验证另一层对；当前只是架构建议，尚未实现这些新skill或全幅金属重建。

## 本地运行

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev,segmentation-eval]'
.venv/bin/python -m pytest -q
```

各工具命令与冻结参数见当前任务及相应实验文档。物理尺度/工艺未知，不输出虚假工艺尺寸或把PDK经验当成照片事实。

## 历史按需阅读

[原README完整归档](docs/history/2026-10-19-before-top-level-README.md)保留早期愿景、能力对比、路线图和使用样例；其中产品愿景不代表当前实现。原开发计划和历史任务入口同样完整归档，由CURRENT_TASK链接定位，不维护多份竞争的实时状态。
