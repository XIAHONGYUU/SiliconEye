# 当前任务

## 目标与授权

2026-10-20：用户授权先推送POLY工作基线、再依据正向Design Rule继续CT。POLY已提交并推送415e4ff（远端main已核对）；当前授权按五类位置顺序扩展CT，先处理电阻左侧中部MOS；CT工作为未提交修改。本文件为唯一实时入口。

## 最新验收与证据

- [POLY v1工作基线检查点](docs/checkpoints/2026-10-20-poly-v1-working-baseline.md)、[统一复核页](docs/assets/poly-closeout-v3/index.html)、[有效模型](benchmarks/poly-closeout-v3/model-v1.json)、[锁定记录](benchmarks/poly-closeout-v3/stage-acceptance-v1.json)。v1/v2保留作历史。
- 用户原话：Q1批准；Q2批准；Q3右侧为6条mos；Q4确认批准无误。[原话记录](benchmarks/poly-closeout-v3/human-review-v1.json)。
- Q3旧5条退休、新增6条规则栅。六条数量已确认，精确边界仍未知；其他对象几何与原生定位不改。Q1/Q2/Q4不再重复索要批准。
- 有效POLY700个材料对象、AA336个、676条明确AA目标关系；不是器件总数。多边形合法，已声明结构错误0、POLY正面积互相交叠0。仍保留5项AA关系未明确验证警告，不宣称全幅真值或真实PDK DRC通过。
- 原AI以五谷判断5条为错误，原profile证据不改写，保留[Agent评测反例](benchmarks/poly-closeout-v3/agent-evaluation-v1.json)。不得调参伪造六谷支持。
- 383项全套测试和相关Ruff通过；输入哈希与静态资源验证通过。[验证记录](benchmarks/poly-closeout-v3/verification-v1.json)。浏览器真实渲染未自动实测。

## RIGHT6前阶段记录（最新几何见下节）

- RIGHT6局部AA/POLY/CT显示复核已通过。用户确认共栅POLY与10个新增栅CT，并确认原橙色位置。该位置已作为人工确认CT纳入，未伪造算法亮峰。当前42源漏＋11栅＝53个CT，无本局部未决槽位。
- [已审页面](docs/assets/ct-right6-reviewed-v5/index.html)、[检查点](docs/checkpoints/2026-10-20-right6-ct-reviewed.md)、[人审记录](benchmarks/ct-right6-reviewed-v5/human-review-v1.json)、[验收锁定](benchmarks/ct-right6-reviewed-v5/acceptance-v1.json)、[CT模型](benchmarks/ct-right6-reviewed-v5/model-v1.json)、[有效材料模型](benchmarks/ct-right6-reviewed-v5/material-model-v1.json)。
- 原52个CT完整对象记录不变，全部AA及共栅POLY模型不变。六栅指ID和记录保留于POLY-RIGHT6-COMMON子结构和别名；有效材料实体695不代表MOS数量减少。694个无关POLY不改。旧锁定基线不覆盖。
- 本组同层POLY共栅已由人工确认；不改变旧V3两水平栅分离。原橙色位置的原图坐标仍是复核图孔列定位估计，不能冒充精确测量。新联系人证据类型为human_confirmation、algorithm_detected=false。
- 53孔整体几何检查通过：重叠0、孔距违规0、按格点对齐、材料包围与沟道/AA避让通过。415项全套测试、相关Ruff和静态资源检查通过；最后只调整了页面对照标签。真实浏览器渲染未自动实测。
- 本组可作为人工复核基准，不重复验收。实际工艺尺寸、M1包围、上层连接和全幅CT覆盖仍未知；不将本组孔数/连接方式套用其他器件。
- 历史诊断与错位记录保留：[早期整改](docs/checkpoints/2026-10-20-ct-joint-control-repair.md)、[共栅修订](docs/checkpoints/2026-10-20-ct-common-gate.md)。

## 最新局部修订与验收状态

- 用户已认可W1宽MOS（12源漏＋11栅）与E1首条电阻上端7孔；本轮两项修订也已获用户逐项批准。[原话与范围](benchmarks/ct-transfer-revision-v2/human-review-v1.json)。
- [只看改动的复核页](docs/assets/ct-transfer-revision-v2/index.html)、[检查点](docs/checkpoints/2026-10-20-ct-transfer-revision.md)、[参数](benchmarks/ct-transfer-revision-v2/spec-v1.json)、[有效CT基准](benchmarks/ct-transfer-revision-v2/model-v1.json)、[有效材料基准](benchmarks/ct-transfer-revision-v2/material-model-v1.json)、[本次批准记录](benchmarks/ct-transfer-revision-v2/human-review-v2.json)、[验收锁定](benchmarks/ct-transfer-revision-v2/acceptance-v1.json)。
- 六管原图栅孔中位y1319与宽MOS y1320接近，原重建却额外下伸。候选以已审宽MOS端部高度1507为参照，将共栅横带从1501..1516收至1500..1507，11栅孔y1508.5→1503.5；x、孔尺寸、原图证据、六栅指与共栅拓扑不变。此为相对几何修订，精确原图边界与工艺尺寸未知。
- 直接在原始照片环带测亮度剖面峰，顶部32、左侧15，共47个候选（原30＋4）。全部由实测局部峰支持，空格不补孔。该数量仅为左上可见子段，不代表全环覆盖。
- 新候选共130 CT；72个完整记录不变（RIGHT6源漏42＋WIDE23＋电阻7），11个共栅孔仅改设计坐标，34个旧环候选在[台账](benchmarks/ct-transfer-revision-v2/ledger-v1.json)完整保留。原v5验收锁定、迁移v1、全部AA与694个无关POLY对象保持不变；材料候选仅改共栅外轮廓。
- 整组无重叠/孔距违规、材料包围与避让通过。423项测试、相关Ruff、输入哈希和静态图稿/切换检查通过；浏览器真实渲染未自动实测。本次显示范围已获人审通过，130 CT与材料基准已锁定；不等于真实PDK DRC或M1网络确认。

## 环与电阻其余可见部分：新增候选

- 用户授权扩展该区域其余可见部分。[新复核页](docs/assets/ct-ring-resistor-extension-v1/index.html)、[检查点](docs/checkpoints/2026-10-20-ct-ring-resistor-extension.md)、[候选模型](benchmarks/ct-ring-resistor-extension-v1/model-v1.json)、[覆盖/待查槽位](benchmarks/ct-ring-resistor-extension-v1/coverage-v1.json)。
- 新增661：环上边续段114、左边续段87、右边96、下边135；18条电阻中02–18上端115、01–18下端114。合计791 CT。用户认可显示范围内连接关系基本无问题，但指出同阵列/同环孔列局部突兀；逐孔几何未定稿。[反馈记录](benchmarks/ct-ring-resistor-extension-v1/human-review-v1.json)。
- 原130 CT完整记录和全部材料不变。沿照片局部路径测峰，源图局部间距追踪抵抗缓慢畸变，独立规则几何满足原质量预算。缺观察、源图残差和首尾空位均保留，不按规则生成孔，不宣称全环逐孔召回完整。
- 整组791孔检查通过，无重叠/孔距违规，最小边距4.4相对px；426全套测试、相关Ruff、输入/锁定哈希、SVG/PNG/资源及模拟切换通过。真实浏览器渲染未自动实测，真实PDK/M1网络未确认。

## 最新批次：中部MOS A/B/C补充确认

- [更新复核页](docs/assets/ct-middle-mos-confirmed-v2/index.html)、[检查点](docs/checkpoints/2026-10-20-ct-middle-mos-confirmed.md)、[有效CT快照](benchmarks/ct-middle-mos-confirmed-v2/model-v1.json)、[补充裁决](benchmarks/ct-middle-mos-confirmed-v2/human-review-v1.json)、[锁定范围](benchmarks/ct-middle-mos-confirmed-v2/acceptance-v1.json)。
- 用户原先批准986个源漏/环CT，又明确48橙色虚框可认为CT。本轮将48个（24源漏＋24环）以人工确认纳入；当前1825孔、Q2本地1034。原1777条完整记录与全部AA/POLY不改。旧661仍是关系基本通过/几何细节待优化，不静默升级。
- 48处仅证据类型human_confirmation，algorithm_detected=false；原图格点定位为估计，不编造算法亮度或人工精确点标。原48显示槽位已解决，但栅端CT、M1仍未知。AA边缘孔不因距POLY较近改判栅孔。
- [栅端诊断](benchmarks/ct-middle-mos-confirmed-v2/gate-assessment.md)：30条栅极主体已表达；上一轮51条路径全AA，栅CT没有专项检测。端部形状/原图定位仍是候选，亮边与孔需区分，上下端/侧向引出及M1对应未完成。不能将流程没覆盖等同于照片无法识别。
- 全组几何门、429项全套测试、Ruff、源与父快照哈希、静态资源/模拟切换通过。真实浏览器渲染未自动实测；不宣称完整逐孔召回或真实工艺DRC。

## 唯一下一步

先依据本次评估，针对Q2完整POLY上下端及侧向引出做专项定位，再关联栅CT；必要时使用可靠局部对应的M1，不盲投影。已审AA/源漏/环不重做。该问题收口后继续已批准顺序：上方小MOS、左侧大MOS、其他环、下方宽MOS；本次未声称这些批次已完成。

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

[本次修订前完整入口](docs/history/current-task-before-2026-10-20-ct-transfer-revision.md)保留迁移v1及原验收状态。

复现本次：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-transfer-revision-v2/spec-v1.json --output runs/新的CT修订目录`。

[本次批准前完整入口](docs/history/current-task-before-2026-10-20-ct-transfer-v2-accepted.md)保留待验收状态。

[本次扩展前完整入口](docs/history/current-task-before-2026-10-20-ct-ring-extension.md)保留130孔已审状态。

复现扩展：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-ring-resistor-extension-v1/spec-v1.json --output runs/新的环电阻CT扩展目录`。

[本次反馈前完整入口](docs/history/current-task-before-2026-10-20-ct-regularity-feedback.md)保留原待审状态。

[本次中部MOS前完整入口](docs/history/current-task-before-2026-10-20-ct-middle-mos.md)保留此前细节优化反馈。

复现本批：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-middle-mos-v1/spec-v1.json --output runs/新的中部MOS_CT目录`。

[本次批准前完整入口](docs/history/current-task-before-2026-10-20-ct-middle-mos-accepted.md)保留A/B/C原待审状态。

[48孔确认前完整入口](docs/history/current-task-before-2026-10-20-ct-middle-confirm48.md)保留原未知及此前验收。

复现本次：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-middle-mos-confirmed-v2/spec-v1.json --output runs/新的中部MOS人工确认输出`。
