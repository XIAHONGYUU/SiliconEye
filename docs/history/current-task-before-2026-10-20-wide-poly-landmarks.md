<!-- 来源：CURRENT_TASK.md；2026-10-20 接续前完整原文。 -->
# 当前任务

## 当前目标与授权

2026-10-19 日终：用户要求记录本轮裁决，将今日修改提交 Git 并推送 GitHub；今晚停止几何扩展，明天再讨论宽 POLY 对应问题。本文件是唯一实时任务入口。

## 最新验收与证据

- [日终检查点](docs/checkpoints/2026-10-19-aa-poly-day-close.md)汇总今日工作与限制。
- [最新已审页面](docs/assets/poly-small-aa-correspondence-v1/reviewed.html)、[人工记录](benchmarks/poly-small-aa-correspondence-v1/human-review-v1.json)：**U05 所示对应及整排AA对齐合理，通过该显示范围**。十个AA工作对象 AA-F01697..AA-F01706 的整排对齐得到认可；原生来源不变。不是全幅305条关系或精确尺寸、CT、网络的整批批准。
- **宽POLY SG-U04-W01：身份已确认，当前跨层点位对应受到质疑。** 旧选区可能对应错误；撤回以该选区推断“没有器件AA/场区POLY”的结论。原候选快照保留，仅作历史。
- 当前来源账目306条，305条AA对应候选、93组、1条宽POLY关系未明；2个未完整观察槽位不补画。原AA工作几何检查300通过/5冲突，新工作候选305通过；这是相对像素结构检查，不能证明物理真值或真实PDK DRC。
- AA采用[已审全幅入口](docs/assets/aa-full-frame-workflow-v1/reviewed.html)及[模型](benchmarks/aa-full-frame-workflow-v1/model-v1.json)。仓库[AA skill v1](skills/silicon-eye-aa-reconstruction/SKILL.md)已封装，未全局安装；POLY skill尚未封装。

## 唯一下一步（明天）

重新核清 SG-U04-W01 在 AA/POLY 原图中的实际对应位置，先使用独立结构标记验证，再讨论目标AA及局部几何。不得沿用有争议点位推出器件缺失，不重问已确认的宽POLY身份，不重跑整幅已审AA。

## 持续生效的边界

- [联合重建架构](docs/architecture/layout-reconstruction-v1.md)：来源坐标与规则设计坐标分离，几何可定向修订，材料身份、隔离及编号不可悄改。当前305条联合候选独立保存，原始照片及原AA基线不覆盖。
- S01/S02累计8条来源显示范围、S03-03/04两独立栅身份保持；下中部140条已审联合关系、F05范围、U10及18条电阻主体保持。不能扩大批准范围。
- R1/R2之间非AA、近邻竖环隔离；V3无局部端部POLY桥，远处金属同网不改变材料隔离。原八图、195保留对象和旧网络v33裁决维持。
- AI主导判断，算法辅助细节；统一成图标准、局部接续、同条件前后比较、质量门防退化。不再从头要求整幅重复验收。CT可辅助数量/端部/独立性，不单凭亮点确定材料或电连接。
- 工艺及物理尺度未知，所有预算为相对像素；未做真实PDK DRC/LVS或完整网表验收。浏览器交互未自动实测。

## 复现与历史

- 当前[联合候选](benchmarks/poly-small-aa-correspondence-v1/model-v1.json)、[分离AA工作候选](benchmarks/poly-small-aa-correspondence-v1/AA-working-model-v1.json)、[来源清单](benchmarks/poly-small-gate-batch-v2/source-inventory-v1.json)与人工记录一起使用，旧模型自身的未审标签不覆盖新裁决。
- 复现候选：`.venv/bin/python -m silicon_eye.poly_aa_correspondence --root . --spec benchmarks/poly-small-aa-correspondence-v1/spec-v1.json --output runs/新的复核目录`。该命令生成候选，不自动转移人审批准。
- 验证：`.venv/bin/python -m pytest -q`；相关Python文件 Ruff；`git diff --check`。
- 原图 data/ 不改写；runs/、.venv/ 不入Git。今日代码、基准、复核资产和证据归档按用户授权提交推送。
- [整理前完整入口](docs/history/current-task-before-2026-10-19-day-close.md)保留所有此前接续命令及历史链接；[开发计划](docs/development-plan.md)保留长期阶段顺序。
