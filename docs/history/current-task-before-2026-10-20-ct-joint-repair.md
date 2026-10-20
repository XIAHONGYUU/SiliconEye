<!-- 归档来源：CURRENT_TASK.md；日期：2026-10-20。以下为CT联合纠偏前完整原文。 -->
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

- [CT局部复核页](docs/assets/ct-reconstruction-v1/index.html)、[工作流/规则](docs/architecture/ct-reconstruction-workflow-v1.md)、[试验参数](benchmarks/ct-reconstruction-v1/spec-v1.json)、[结果](benchmarks/ct-reconstruction-v1/report-v1.json)。
- 四处局部共473个观察候选（399个原紧凑形状观察＋74个补充亮峰），不是CT真值计数；归属全部待局部配准复核，M1包围及网络未知。已审AA/POLY输入哈希不变。
- 393项全套测试及最后参数化修订10项定向测试通过；Ruff与静态资源检查通过。原/补充观察同页对照，补充观察保留未知；未获局部同组对应时禁止周期吸附，不按孔列规律自动补孔。
- 质量门HOLD：继承全局投影未通过精确落点验证，方孔尺寸与孔距预算尚未由目标工艺/人工确认，保留间距冲突。未扩大为全幅提取或skill完成。

## 唯一下一步

先针对CT01/CT02验证原生照片与共同设计坐标的局部结构对应，区分投影、孔尺寸和误检导致的冲突，再修订AA/POLY归属；CT03/CT04检验电阻端部与环的迁移效果。不要把未经验证的投影用于归属，也不要求用户逐孔裁决。局部通过后再扩大范围。

## 持续生效的边界

- 下中部140条联合几何、U05、S01/S02来源范围、S03-03/04独立性、U10、18条旧电阻主体及SG-U04-W01电阻保留。Q3新宽MOS与SG-U04-W01是不同对象。
- AA-F00872仅依人工明确裁决从有效层退休；原始AA源模型、照片不覆盖。设计坐标、原图坐标、旧图册来源分开保留。新原图定位估计不等于精确边界真值。
- V3两水平主体隔离，不补POLY桥；照片外G67不补闭合，界面遮挡和邻片不扩充材料。U10原形状已审，联合定位的候选边界继续保留。
- R1/R2非AA间隙、近邻环隔离、原八图、195保留对象及旧网络v33历史裁决保持。AA仓库skill v1未全局安装；POLY skill未封装。
- 工艺/尺度、极性、真实W/L、CT逐孔归属、阻值和新增网络未确认；未做真实DRC/LVS。

## 复现与交接

- `.venv/bin/python -m silicon_eye.poly_closeout --root . --spec benchmarks/poly-closeout-v3/spec-v1.json --output runs/新的验收输出目录`
- `.venv/bin/python -m silicon_eye.ct_reconstruction --spec benchmarks/ct-reconstruction-v1/spec-v1.json --output runs/新的CT试验目录`。
- `.venv/bin/python -m pytest -q`；相关Ruff；`git diff --check`。
- data/不改；runs/、.venv/不入Git。POLY收口内容已随415e4ff推送；本地待提交仅为本轮CT试验代码、测试、规则文档、基准和复核页。
- [本轮前完整入口](docs/history/current-task-before-2026-10-20-poly-acceptance-v3.md)、[v2前入口](docs/history/current-task-before-2026-10-20-poly-feedback-v2.md)保留历史恢复命令。长期顺序见[开发计划](docs/development-plan.md)。

本轮CT前入口完整保留于[归档](docs/history/current-task-before-2026-10-20-CT-pilot.md)。
