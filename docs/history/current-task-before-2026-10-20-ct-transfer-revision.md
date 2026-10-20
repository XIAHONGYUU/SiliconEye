# 当前任务

## 目标与授权

2026-10-20：用户授权先推送POLY工作基线、再依据正向Design Rule继续CT。POLY已提交并推送415e4ff（远端main已核对）；当前授权继续迁移到相邻宽MOS及环/电阻，CT工作为未提交修改。本文件为唯一实时入口。

## 最新验收与证据

- [POLY v1工作基线检查点](docs/checkpoints/2026-10-20-poly-v1-working-baseline.md)、[统一复核页](docs/assets/poly-closeout-v3/index.html)、[有效模型](benchmarks/poly-closeout-v3/model-v1.json)、[锁定记录](benchmarks/poly-closeout-v3/stage-acceptance-v1.json)。v1/v2保留作历史。
- 用户原话：Q1批准；Q2批准；Q3右侧为6条mos；Q4确认批准无误。[原话记录](benchmarks/poly-closeout-v3/human-review-v1.json)。
- Q3旧5条退休、新增6条规则栅。六条数量已确认，精确边界仍未知；其他对象几何与原生定位不改。Q1/Q2/Q4不再重复索要批准。
- 有效POLY700个材料对象、AA336个、676条明确AA目标关系；不是器件总数。多边形合法，已声明结构错误0、POLY正面积互相交叠0。仍保留5项AA关系未明确验证警告，不宣称全幅真值或真实PDK DRC通过。
- 原AI以五谷判断5条为错误，原profile证据不改写，保留[Agent评测反例](benchmarks/poly-closeout-v3/agent-evaluation-v1.json)。不得调参伪造六谷支持。
- 383项全套测试和相关Ruff通过；输入哈希与静态资源验证通过。[验证记录](benchmarks/poly-closeout-v3/verification-v1.json)。浏览器真实渲染未自动实测。

## CT当前进度

- RIGHT6局部AA/POLY/CT显示复核已通过。用户确认共栅POLY与10个新增栅CT，并确认原橙色位置。该位置已作为人工确认CT纳入，未伪造算法亮峰。当前42源漏＋11栅＝53个CT，无本局部未决槽位。
- [已审页面](docs/assets/ct-right6-reviewed-v5/index.html)、[检查点](docs/checkpoints/2026-10-20-right6-ct-reviewed.md)、[人审记录](benchmarks/ct-right6-reviewed-v5/human-review-v1.json)、[验收锁定](benchmarks/ct-right6-reviewed-v5/acceptance-v1.json)、[CT模型](benchmarks/ct-right6-reviewed-v5/model-v1.json)、[有效材料模型](benchmarks/ct-right6-reviewed-v5/material-model-v1.json)。
- 原52个CT完整对象记录不变，全部AA及共栅POLY模型不变。六栅指ID和记录保留于POLY-RIGHT6-COMMON子结构和别名；有效材料实体695不代表MOS数量减少。694个无关POLY不改。旧锁定基线不覆盖。
- 本组同层POLY共栅已由人工确认；不改变旧V3两水平栅分离。原橙色位置的原图坐标仍是复核图孔列定位估计，不能冒充精确测量。新联系人证据类型为human_confirmation、algorithm_detected=false。
- 53孔整体几何检查通过：重叠0、孔距违规0、按格点对齐、材料包围与沟道/AA避让通过。415项全套测试、相关Ruff和静态资源检查通过；最后只调整了页面对照标签。真实浏览器渲染未自动实测。
- 本组可作为人工复核基准，不重复验收。实际工艺尺寸、M1包围、上层连接和全幅CT覆盖仍未知；不将本组孔数/连接方式套用其他器件。
- 历史诊断与错位记录保留：[早期整改](docs/checkpoints/2026-10-20-ct-joint-control-repair.md)、[共栅修订](docs/checkpoints/2026-10-20-ct-common-gate.md)。

## 新区域迁移状态

- [W1/R1/E1联合复核页](docs/assets/ct-transfer-v1/index.html)、[迁移检查点](docs/checkpoints/2026-10-20-ct-transfer.md)、[参数](benchmarks/ct-transfer-v1/spec-v1.json)、[候选模型](benchmarks/ct-transfer-v1/model-v1.json)、[质量门](benchmarks/ct-transfer-v1/report-v1.json)。
- 新增64个候选：W1相邻宽MOS为12源漏＋11栅；R1/AA-W07环顶部30、左侧4；E1/G48-P01首条长电阻上端7。均未获人工批准。环左侧其余部分、电阻下端/其他电阻未覆盖。
- 原53个已审CT完整记录不变，695个材料对象不变，验收锁定和输入哈希均验证。整组117孔检查无重叠/孔距违规，最小边距7.25相对px；新归属与局部源图对应仍是AI候选，不等于真实PDK DRC通过。
- 420项全套测试和相关Ruff通过，含真实已审记录/材料防退化阻断、缺观察不补孔、同槽多峰与横纵孔列测试。资源/SVG/PNG与模拟切换检查通过；真实浏览器渲染未自动实测。
- 复用已存亮点观察验证迁移，不声称检测召回或完整覆盖提高。未选择峰保留于拟合台账，不自动删为误报；缺观察不补齐。M1/网络不推断。

## 唯一下一步

只复核新卡W1、R1、E1的材料归属、原图边界与规则孔列，不重验RIGHT6。通过后再扩展覆盖；失败则保留新区域候选并有针对性修订，不降低已审组标准或按预期补孔。

## 持续生效的边界

- 下中部140条联合几何、U05、S01/S02来源范围、S03-03/04独立性、U10、18条旧电阻主体及SG-U04-W01电阻保留。Q3新宽MOS与SG-U04-W01是不同对象。
- AA-F00872仅依人工明确裁决从有效层退休；原始AA源模型、照片不覆盖。设计坐标、原图坐标、旧图册来源分开保留。新原图定位估计不等于精确边界真值。
- V3两水平主体隔离，不补POLY桥；照片外G67不补闭合，界面遮挡和邻片不扩充材料。U10原形状已审，联合定位的候选边界继续保留。
- R1/R2非AA间隙、近邻环隔离、原八图、195保留对象及旧网络v33历史裁决保持。AA仓库skill v1未全局安装；POLY skill未封装。
- 工艺/尺度、极性、真实W/L、CT逐孔归属、阻值和新增网络未确认；未做真实DRC/LVS。

## 复现与交接

- `.venv/bin/python -m silicon_eye.poly_closeout --root . --spec benchmarks/poly-closeout-v3/spec-v1.json --output runs/新的验收输出目录`
- `.venv/bin/python -m silicon_eye.ct_joint_reconstruction --spec benchmarks/ct-right6-reviewed-v5/spec-v1.json --output runs/新的CT联合重建目录`。
- 旧ct_reconstruction只作亮点诊断，已改正整体质量状态，不作为重建验收入口。
- `.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-transfer-v1/spec-v1.json --output runs/新的CT迁移目录`。
- `.venv/bin/python -m pytest -q`；相关Ruff；`git diff --check`。
- data/不改；runs/、.venv/不入Git。POLY收口内容已随415e4ff推送；本地待提交包含CT诊断、联合重建、源图纠正和本轮共栅局部POLY修订、测试、文档、基准与复核页。
- [本轮前完整入口](docs/history/current-task-before-2026-10-20-poly-acceptance-v3.md)、[v2前入口](docs/history/current-task-before-2026-10-20-poly-feedback-v2.md)保留历史恢复命令。长期顺序见[开发计划](docs/development-plan.md)。

本轮CT前入口完整保留于[归档](docs/history/current-task-before-2026-10-20-CT-pilot.md)。

[联合纠偏前完整入口](docs/history/current-task-before-2026-10-20-ct-joint-repair.md)保存旧状态。

[共栅修订前完整入口](docs/history/current-task-before-2026-10-20-common-gate.md)保留源漏确认前的状态。

[本次验收前完整入口](docs/history/current-task-before-2026-10-20-right6-reviewed.md)保留上阶段待核状态。

[迁移前完整入口](docs/history/current-task-before-2026-10-20-ct-transfer.md)保留已审基准与恢复状态。
