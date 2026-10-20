<!-- 来源：CURRENT_TASK.md；日期：2026-10-20。以下完整保留局部验收前原文。 -->
# 当前任务

## 目标与授权

2026-10-20：用户授权先推送POLY工作基线、再依据正向Design Rule继续CT。POLY已提交并推送415e4ff（远端main已核对）；当前CT局部试验为未提交修改。本文件为唯一实时入口。

## 最新验收与证据

- [POLY v1工作基线检查点](docs/checkpoints/2026-10-20-poly-v1-working-baseline.md)、[统一复核页](docs/assets/poly-closeout-v3/index.html)、[有效模型](benchmarks/poly-closeout-v3/model-v1.json)、[锁定记录](benchmarks/poly-closeout-v3/stage-acceptance-v1.json)。v1/v2保留作历史。
- 用户原话：Q1批准；Q2批准；Q3右侧为6条mos；Q4确认批准无误。[原话记录](benchmarks/poly-closeout-v3/human-review-v1.json)。
- Q3旧5条退休、新增6条规则栅。六条数量已确认，精确边界仍未知；其他对象几何与原生定位不改。Q1/Q2/Q4不再重复索要批准。
- 有效POLY700个材料对象、AA336个、676条明确AA目标关系；不是器件总数。多边形合法，已声明结构错误0、POLY正面积互相交叠0。仍保留5项AA关系未明确验证警告，不宣称全幅真值或真实PDK DRC通过。
- 原AI以五谷判断5条为错误，原profile证据不改写，保留[Agent评测反例](benchmarks/poly-closeout-v3/agent-evaluation-v1.json)。不得调参伪造六谷支持。
- 383项全套测试和相关Ruff通过；输入哈希与静态资源验证通过。[验证记录](benchmarks/poly-closeout-v3/verification-v1.json)。浏览器真实渲染未自动实测。

## CT当前进度

- 用户已确认当前42个源漏CT合理，并明确RIGHT6六MOS的gate在POLY上相连、有CT引出；授权局部微调POLY。[裁决](benchmarks/ct-gate-bus-v4/human-review-v1.json)。不扩大为新增栅CT边界/数量批准，也不改变旧V3两水平栅分离。
- [最新联合复核页](docs/assets/ct-gate-bus-v4/index.html)、[共栅检查点](docs/checkpoints/2026-10-20-ct-common-gate.md)、[CT模型](benchmarks/ct-gate-bus-v4/model-v1.json)、[新有效材料候选](benchmarks/ct-gate-bus-v4/material-model-v1.json)、[质量门](benchmarks/ct-gate-bus-v4/report-v1.json)。
- 42个已审源漏CT完整对象记录不变，全部AA及694个无关POLY对象不变。六栅指加下端横带合为POLY-RIGHT6-COMMON；六栅指原ID/记录通过子结构和别名保留。材料实体700→695不代表MOS数量减少。原锁定基线不覆盖，新材料模型仍是局部修订候选。
- 新增10个源图亮峰支持的栅CT，全部由共栅POLY包围、避开AA。一个可能漏检的格点槽位仅以橙框问号显示，未导出为CT；不得按MOS个数补孔。紫色为新增栅CT，蓝色为已审源漏CT。
- 52个CT整体几何检查通过：重叠0、孔距违规0；同组按格点对齐。支持缺观察的空格点，不将双倍孔距当作补孔许可。共栅横带与新CT精确边界待复核，M1包围和网络仍未知。
- 413项全套测试、相关Ruff及静态资源/模拟切换检查通过。输入哈希、42源漏完整记录、无关材料保留均验证通过；真实浏览器渲染未自动实测。
- 旧亮点稿21对重叠/89对不足间距的失败记录及源图左移一列的纠正仍保留，不能以几何通过替代源图对应检查。见[早期整改](docs/checkpoints/2026-10-20-ct-joint-control-repair.md)。

## 唯一下一步

复核共栅横带范围、新增紫色栅CT及橙色待核点；不重新要求已确认源漏CT验收。局部通过后迁移到相邻宽MOS和环/电阻。其他区域仍未覆盖，不解释为没有孔；不推断M1连接或宣称全幅CT完成。

## 持续生效的边界

- 下中部140条联合几何、U05、S01/S02来源范围、S03-03/04独立性、U10、18条旧电阻主体及SG-U04-W01电阻保留。Q3新宽MOS与SG-U04-W01是不同对象。
- AA-F00872仅依人工明确裁决从有效层退休；原始AA源模型、照片不覆盖。设计坐标、原图坐标、旧图册来源分开保留。新原图定位估计不等于精确边界真值。
- V3两水平主体隔离，不补POLY桥；照片外G67不补闭合，界面遮挡和邻片不扩充材料。U10原形状已审，联合定位的候选边界继续保留。
- R1/R2非AA间隙、近邻环隔离、原八图、195保留对象及旧网络v33历史裁决保持。AA仓库skill v1未全局安装；POLY skill未封装。
- 工艺/尺度、极性、真实W/L、CT逐孔归属、阻值和新增网络未确认；未做真实DRC/LVS。

## 复现与交接

- `.venv/bin/python -m silicon_eye.poly_closeout --root . --spec benchmarks/poly-closeout-v3/spec-v1.json --output runs/新的验收输出目录`
- `.venv/bin/python -m silicon_eye.ct_joint_reconstruction --spec benchmarks/ct-gate-bus-v4/spec-v1.json --output runs/新的CT联合重建目录`。
- 旧ct_reconstruction只作亮点诊断，已改正整体质量状态，不作为重建验收入口。
- `.venv/bin/python -m pytest -q`；相关Ruff；`git diff --check`。
- data/不改；runs/、.venv/不入Git。POLY收口内容已随415e4ff推送；本地待提交包含CT诊断、联合重建、源图纠正和本轮共栅局部POLY修订、测试、文档、基准与复核页。
- [本轮前完整入口](docs/history/current-task-before-2026-10-20-poly-acceptance-v3.md)、[v2前入口](docs/history/current-task-before-2026-10-20-poly-feedback-v2.md)保留历史恢复命令。长期顺序见[开发计划](docs/development-plan.md)。

本轮CT前入口完整保留于[归档](docs/history/current-task-before-2026-10-20-CT-pilot.md)。

[联合纠偏前完整入口](docs/history/current-task-before-2026-10-20-ct-joint-repair.md)保存旧状态。

[共栅修订前完整入口](docs/history/current-task-before-2026-10-20-common-gate.md)保留源漏确认前的状态。
