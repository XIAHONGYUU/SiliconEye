<!-- 来源：CURRENT_TASK.md；日期：2026-10-20。下方完整保留修订前原文。 -->
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

- 用户指出旧CT稿孔重叠、间距与行列不规整，要求自行检查并和已有AA/POLY匹配。旧稿已判不合格并撤回重建验收用途；473个原观察保留。自检21对重叠、89对不足旧2px间距预算，[追溯审计](benchmarks/ct-joint-reconstruction-v2/retrospective-audit-v1.json)。
- [最新联合重建页](docs/assets/ct-joint-reconstruction-v2/index.html)、[整改检查点](docs/checkpoints/2026-10-20-ct-joint-control-repair.md)、[模型](benchmarks/ct-joint-reconstruction-v2/model-v1.json)、[质量门](benchmarks/ct-joint-reconstruction-v2/report-v1.json)、[局部源图匹配](benchmarks/ct-joint-reconstruction-v2/fit-v1.json)。
- 仅右侧已确认6条MOS的扩散CT子集：7列×6行42个孔，横纵各自等间距，无重叠/孔距违规，最小边距8.76相对px；完整AA包围和POLY沟道避让通过。AA/POLY输入哈希不变。
- 新组每孔都有源图亮峰支持；局部材料对应仍为AI候选，新CT未获人工批准。统一5px方孔参考光学残差核心中位数5原生px，不能作真实工艺尺寸。试验孔距/包围预算不是真实PDK DRC。
- 硬性质量门已接入导出路径：任何重叠、孔距不足、歪列、横纵节距不一致、材料冲突、无证据或同一源峰重复使用均阻断重建导出。算法观察不再作为重建验收图。
- 404项全套测试、相关Ruff和静态资源/模拟切换检查通过；真实浏览器渲染未自动实测。

## 唯一下一步

先复核右侧六MOS组的源图对应和规则CT排列；通过后迁移到栅端、相邻宽MOS及环/电阻。当前不宣称全幅CT完成；未画区域保持未覆盖，不解释为无孔。下端接触带仍需核清POLY真实端部关系，不强塞入当前矩形或推断电连接。

## 持续生效的边界

- 下中部140条联合几何、U05、S01/S02来源范围、S03-03/04独立性、U10、18条旧电阻主体及SG-U04-W01电阻保留。Q3新宽MOS与SG-U04-W01是不同对象。
- AA-F00872仅依人工明确裁决从有效层退休；原始AA源模型、照片不覆盖。设计坐标、原图坐标、旧图册来源分开保留。新原图定位估计不等于精确边界真值。
- V3两水平主体隔离，不补POLY桥；照片外G67不补闭合，界面遮挡和邻片不扩充材料。U10原形状已审，联合定位的候选边界继续保留。
- R1/R2非AA间隙、近邻环隔离、原八图、195保留对象及旧网络v33历史裁决保持。AA仓库skill v1未全局安装；POLY skill未封装。
- 工艺/尺度、极性、真实W/L、CT逐孔归属、阻值和新增网络未确认；未做真实DRC/LVS。

## 复现与交接

- `.venv/bin/python -m silicon_eye.poly_closeout --root . --spec benchmarks/poly-closeout-v3/spec-v1.json --output runs/新的验收输出目录`
- `.venv/bin/python -m silicon_eye.ct_joint_reconstruction --spec benchmarks/ct-joint-reconstruction-v2/spec-v1.json --output runs/新的CT联合重建目录`。
- 旧ct_reconstruction只作亮点诊断，已改正整体质量状态，不作为重建验收入口。
- `.venv/bin/python -m pytest -q`；相关Ruff；`git diff --check`。
- data/不改；runs/、.venv/不入Git。POLY收口内容已随415e4ff推送；本地待提交仅为本轮CT试验代码、测试、规则文档、基准和复核页。
- [本轮前完整入口](docs/history/current-task-before-2026-10-20-poly-acceptance-v3.md)、[v2前入口](docs/history/current-task-before-2026-10-20-poly-feedback-v2.md)保留历史恢复命令。长期顺序见[开发计划](docs/development-plan.md)。

本轮CT前入口完整保留于[归档](docs/history/current-task-before-2026-10-20-CT-pilot.md)。

[联合纠偏前完整入口](docs/history/current-task-before-2026-10-20-ct-joint-repair.md)保存旧状态。
