<!-- 来源：CURRENT_TASK.md；2026-10-19 日终整理前完整原文。 -->
# 当前任务

## 目标与授权

2026-10-19：继续推进并复核上方小栅结果。授权本地实施与验证；没有新的Git提交/推送授权。唯一实时入口为本文件；[开发计划](docs/development-plan.md)、[完整前入口](docs/history/current-task-before-2026-10-19-poly-small-batch.md)保留其他阶段及历史恢复信息。

## 当前结果与唯一下一步

- **复杂小栅/AA对应稿**：[页面](docs/assets/poly-small-aa-correspondence-v1/index.html)、[检查点](docs/checkpoints/2026-10-19-poly-small-aa-correspondence.md)、[对应与检查](benchmarks/poly-small-aa-correspondence-v1/report-v1.json)、[验证](benchmarks/poly-small-aa-correspondence-v1/verification-v1.json)。306条来源均有账目，305条AA对应候选/93组，1条宽POLY的AA关系未明；对应是假设，非人审或最近框分配。
- U01第一长AA的5槽/完整观察后3条为照片局部覆盖假设，前2槽未知，不生成POLY。S01/S02八条、S03两条独立身份、宽POLY身份、666父对象及全部来源坐标保持；不重复核对。
- 原AA下几何检查300通过/5冲突，发现U05后10个AA岛仍有工作坐标斜漂。另存整排对齐方案到y=784.25..814.25，保留X、ID、全部AA原生来源，其余327个AA对象不变。原AA不覆盖，AA提议未人审。以此生成305条共同AA设计候选，结构预算下305通过；这不是实际PDK DRC或识别准确率。
- **唯一下一步**：用户核对[U05整排AA对齐方案](docs/assets/poly-small-aa-correspondence-v1/index.html#U05)，并说明[宽POLY与AA的关系](docs/assets/poly-small-aa-correspondence-v1/index.html#wide)：对应阶梯缺口处AA照片未见器件AA，暂不指派邻近AA。其余可按P/A表整体核对，不逐个CT确认。新关系、AA修订、设计尺寸均未整批批准。
- 23项相关测试、Ruff、来源与父对象保持、全账目/唯一分配、SVG/XML、资源及页面脚本检查通过；浏览器交互未自动实测。无Git提交/推送、GDS导出或真实PDK DRC/LVS。此前批量来源清单[入口](benchmarks/poly-small-gate-batch-v2/source-inventory-v1.json)维持。
- 本阶段前入口完整归档：[链接](docs/history/current-task-before-2026-10-19-poly-aa-correspondence.md)。

## 生效裁决与方法边界

- [联合版图架构](docs/architecture/layout-reconstruction-v1.md)：原始照片/来源坐标与设计坐标分开；相对关系和正向结构约束优先。工作AA/POLY可据证据定向联合修订，材料身份、隔离、器件/net编号不能被几何修订悄改。
- AA采用[已审入口](docs/assets/aa-full-frame-workflow-v1/reviewed.html)和[模型](benchmarks/aa-full-frame-workflow-v1/model-v1.json)。R1/R2之间非AA、两近邻竖环隔离；AA仓库skill v1已封装未全局安装，不重开整幅审查。全幅稠密精度和跨芯片泛化未知。
- POLY下方140条联合关系及F05显示范围通过；U10形状和18条电阻主体等既有范围保持。普通MOS不自动补凸形/狗骨头；POLY不能被AA统一裁剪。V3两栅没有局部端部POLY桥，远处金属同网不改变该裁决。
- [小栅已审基线](benchmarks/poly-small-mos-local-v3/accepted-local-model-v1.json)：S01/S02来源显示范围累计8条通过；S03-03/04独立身份通过，未扩大为7条精确边界或电连接批准。当前候选模型继承此基线，保护ID随版本接续。
- CT分布可辅助判断数量、端部和独立性，不单凭亮点分配材料、孔归属或电网络。旧修正mask的0不是确认非POLY，拓扑/CT遮挡未知保持。照片外不猜连接，照片左沿不闭合残缺对象。
- AI主导、算法辅助细节，所有比较按相同成图标准。原图不可改；物理尺度/工艺、N/P、真实W/L未知，相对像素预算不冒充PDK数值。POLY skill不封装。
- 原八图、195保留对象和旧网络v33等历史裁决维持；区域分类不成为跨区域走线边界。[完整归档](docs/history/current-task-before-2026-10-19-poly-small-batch.md)含前轮资产、解释与恢复命令。

## 接续与复现

- 当前联合候选模型：[链接](benchmarks/poly-small-aa-correspondence-v1/model-v1.json)。源306观察与父666对象不变；AA工作提议及305条联合候选独立保存，未替换已审层。
- 定位实验：`.venv/bin/python -m silicon_eye.poly_gate_matching --root . --spec benchmarks/poly-small-gate-batch-v1/matching-spec-v1.json --output runs/新目录`。
- AI已裁定的来源候选：`.venv/bin/python -m silicon_eye.poly_local_revision --root . --spec benchmarks/poly-small-gate-batch-v2/spec-v1.json --output runs/新的复核目录`。本入口不重跑首尾插值模板；历史spec仅用于复现历史。
- 原始照片在data，.venv/与runs/不入Git；复核资产/基准在仓库。45项旧输入恢复方式见前入口与benchmarks/evidence/poly-reconstruction-v1d-evidence.zip。
- 当前工作树含多阶段未提交修改，不覆盖/清理；本轮新增匹配模块、两处测试及小栅批量基准/资产，修改局部复核器以保留已审颜色和跨窗口去重。匹配和复核开发输出a/b不是独立准确率实验。

当前复现：`.venv/bin/python -m silicon_eye.poly_aa_correspondence --root . --spec benchmarks/poly-small-aa-correspondence-v1/spec-v1.json --output runs/新的复核目录`。
