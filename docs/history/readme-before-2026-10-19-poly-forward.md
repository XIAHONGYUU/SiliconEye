<!-- 来源：README.md；归档日期：2026-10-19；以下保留本轮前原文。 -->
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

[POLY首轮局部对照](docs/checkpoints/2026-10-19-poly-reconstruction.md)已冻结AA、接回旧标注并生成横向/竖向A/B0/B1切换页；横向位置/宽度和重新观察后的竖向范围已获局部批准，见[已审竖向页](docs/assets/poly-vertical-reassessment-v3/reviewed.html)；全幅POLY与skill封装尚未完成。方法见[POLY工作流v1](docs/architecture/poly-reconstruction-workflow-v1.md)。

[全幅POLY首轮候选](docs/checkpoints/2026-10-19-poly-full-frame.md)已生成：保留4个已审对象、新增349个主体候选、22处未知，支持12块/图层切换；全幅材料完整性仍未通过。

[全幅POLY v2定向修订](docs/checkpoints/2026-10-19-poly-full-frame-v2.md)补短器件/端部候选、约束匹配排共列，并新增待审局部AA/POLY联合图；逐项反馈和前后比较可追溯，仍未全幅验收。

## 本地运行

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev,segmentation-eval]'
.venv/bin/python -m pytest -q
```

各工具命令与冻结参数见当前任务及相应实验文档。物理尺度/工艺未知，不输出虚假工艺尺寸或把PDK经验当成照片事实。

## 历史按需阅读

[原README完整归档](docs/history/2026-10-19-before-top-level-README.md)保留早期愿景、能力对比、路线图和使用样例；其中产品愿景不代表当前实现。原开发计划和历史任务入口同样完整归档，由CURRENT_TASK链接定位，不维护多份竞争的实时状态。
