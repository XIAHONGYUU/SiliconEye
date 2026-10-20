<!-- 来源：CURRENT_TASK.md；归档日期：2026-10-20；以下原文完整保留。 -->
# 当前任务

## 目标与授权

2026-10-20：用户授权先推送POLY工作基线、再依据正向Design Rule继续CT。POLY已提交并推送415e4ff（远端main已核对）；当前授权处理剩余左侧／左下大MOS CT；上方同环批已审并完成T右端局部材料修订，左侧B/D分项通过、E已执行批准方案，A/C/F局部修订待审；CT工作为未提交修改。本文件为唯一实时入口。

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

## 栅端专项检查：引出方向已确认

- [新专项复核页](docs/assets/q2-gate-terminal-inspection-v1/index.html)、[检查点](docs/checkpoints/2026-10-20-q2-gate-terminal-inspection.md)、[逐栅观察](benchmarks/q2-gate-terminal-inspection-v1/observations-v1.json)、[三组问题](benchmarks/q2-gate-terminal-inspection-v1/review-questions-v1.json)。QG01–QG30是本页索引，映射原POLY稳定ID；A8/B8/C14共60上下端、60侧向范围已检查。
- 用户明确确认A/B下端短亮条包含栅CT，且本组A/B/C全部在下端引出。[人审原话](benchmarks/q2-gate-terminal-inspection-v1/human-review-v1.json)、[逐栅方向状态](benchmarks/q2-gate-terminal-inspection-v1/terminal-status-v1.json)。30条逐栅方向已记录；孔数、精确边界、M1归属及共栅关系仍未知。C上端M1候选不自动归为栅引出。
- 三组环四角局部配准仅为候选，未拟合的源漏列横向误差中位/最大A3/8、B2.5/9、C5.5/12px，均未过最大6px门，纵向未独立验证。只供对照，禁止精确CT投影和连接确认。
- 原1825 CT、全部AA/POLY及照片哈希未改，新CT输出0。30稳定ID/120区域覆盖、资源/PNG/模拟切换、Ruff及14项相关保留测试通过。真实浏览器渲染未自动实测。

## 已审基准：Q2下端POLY CT

- [新位置复核页](docs/assets/q2-gate-ct-localization-v1/index.html)、[检查点](docs/checkpoints/2026-10-20-q2-gate-ct-localization.md)、[候选快照](benchmarks/q2-gate-ct-localization-v1/model-v1.json)、[原图逐栅测量](benchmarks/q2-gate-ct-localization-v1/measurements-v1.json)、[待判清单](benchmarks/q2-gate-ct-localization-v1/review-questions-v1.json)。
- 用户确认“孔位置及每栅两孔合理”。[批准记录](benchmarks/q2-gate-ct-localization-v1/human-review-v1.json)、[验收锁定](benchmarks/q2-gate-ct-localization-v1/acceptance-v1.json)。30条下端共60个CT（A16/B16/C28）已通过位置与数量复核，每栅两强峰来自实际照片，不按数量补孔；两处较弱峰保留未输出。原1825条完整CT、AA/POLY保持不变，当前候选总1885孔。
- 使用已审相邻源漏CT列局部锚定，再找下端亮条及横向峰，避免旧派生POLY原图端点偏差。设计中CT落自己的POLY、AA之外，方孔5px、同一行节距12px、端部相位一致，无需改POLY。
- M1只交叉核对区域与下端引出，不盲投影孔位；具体M1段/共栅/net仍未知。本轮60新孔的显示位置及每栅两孔现已获人工批准；历史算法候选字段不改写。
- 整组几何门、433全套测试、Ruff、父1825完整保留、源哈希、静态图稿和模拟切换通过；真实浏览器渲染未自动实测，不宣称真实PDK DRC。

## 最新已审批次：上方同环40栅CT及局部材料修订

- 用户批准T全部CT、L/M/R右侧30长栅源漏与下端栅CT、外围环及待查位置；要求T右端MOS的AA/POLY偏上问题局部微调。[原话与范围](benchmarks/ct-upper-small-mos-reviewed-v2/human-review-v1.json)。
- [新对照页](docs/assets/ct-upper-small-mos-reviewed-v2/index.html)、[检查点](docs/checkpoints/2026-10-20-ct-upper-small-mos-reviewed.md)、[有效CT](benchmarks/ct-upper-small-mos-reviewed-v2/model-v1.json)、[有效材料](benchmarks/ct-upper-small-mos-reviewed-v2/material-model-v1.json)、[验收锁定](benchmarks/ct-upper-small-mos-reviewed-v2/acceptance-v1.json)。历史v1不改。
- T最右AA-F01669与SG-U06-010设计几何下移7相对px，2个上端栅CT随端部移动；4个源漏CT与全部原图定位不动。其他2656个原CT完整记录、335无关AA、694无关POLY不变。T可切换修订前图。
- 51橙框按human_confirmation纳入，不伪造算法亮峰；原图坐标仍为复核格点估计。本批824 CT，完整模型2709；只解决本批51个显示槽位，不宣称全幅完整。
- 整组几何门PASS，无重叠/孔距违规，材料包围与避让通过。439全套测试、相关Ruff、源/父哈希、静态资源及模拟切换通过；T预览目视检查通过。真实浏览器渲染未测（file协议被浏览器安全策略阻止）。不是实际PDK DRC，M1/net未知；旧661细节保留意见不升级。

## 最新分项裁决与局部修订：左侧CT v2

- [新复核页](docs/assets/ct-left-large-mos-revision-v2/index.html)、[检查点](docs/checkpoints/2026-10-20-ct-left-large-mos-revision.md)、[人审原话及G25/G26澄清](benchmarks/ct-left-large-mos-revision-v2/human-review-v1.json)、[分项批准](benchmarks/ct-left-large-mos-revision-v2/scoped-acceptance-v1.json)。B连接关系通过、逐孔误差意见保留；D显示通过；E原AA右缘+6及29孔方案已批准并执行。A/C/F新细节待本页审，不当成全批通过。
- [有效CT候选](benchmarks/ct-left-large-mos-revision-v2/model-v1.json)、[有效材料候选](benchmarks/ct-left-large-mos-revision-v2/material-model-v1.json)、[逐记录台账](benchmarks/ct-left-large-mos-revision-v2/ledger-v1.json)。新增A16＋C237＋E29＋F3＝285，合计4940孔；旧4631完整记录不变，24条授权局部修订且原图证据不动。此前2709已审记录逐条完全不变。
- A确认阶梯最右G25/G26共享扩散，不跨环接更右长栅组。旧AA5/6合为带别名的AA-LEFT-STAIR-SHARED-56；原对象存于台账。短栅主体宽40→30、中心左移15，上端补2孔。左宽MOS纠正过宽AA及过短POLY下端，原生照片定位不改，裁剪左端仍是观察边界；新精确几何待审。
- C上下外端两条为AA环、中间两条为上下排POLY栅端；只补对应栅CT，不自动确认5条宽栅共栅。F第2栅补2孔、第3栅补另一孔，原单孔设计坐标左移6形成双孔相位；3个新孔保留弱信号/邻栅相位支持身份，非独立强峰计数。
- 整组几何门、442全套测试、相关Ruff、源/父哈希、静态资源和模拟切换通过。A/C/F预览已目视核查；真实浏览器渲染未测，真实PDK DRC/M1/net/全幅完整性仍未知。旧661孔细节意见不升级。

## 唯一下一步

只提交A、C、F局部修订复核：A共享AA及左宽MOS匹配、C两排新栅端CT、F三个补孔与双孔相位。B/D不重审；E已按原批方案完成。全部仍按像素／相对设计单位，不使用假定工艺尺寸；本轮无推送授权。

## 持续生效的边界

- 下中部140条联合几何、U05、S01/S02来源范围、S03-03/04独立性、U10、18条旧电阻主体及SG-U04-W01电阻保留。Q3新宽MOS与SG-U04-W01是不同对象。
- AA-F00872仅依人工明确裁决从有效层退休；原始AA源模型、照片不覆盖。设计坐标、原图坐标、旧图册来源分开保留。新原图定位估计不等于精确边界真值。
- V3两水平主体隔离，不补POLY桥；照片外G67不补闭合，界面遮挡和邻片不扩充材料。U10原形状已审，联合定位的候选边界继续保留。
- R1/R2非AA间隙、近邻环隔离、原八图、195保留对象及旧网络v33历史裁决保持。AA仓库skill v1未全局安装；POLY skill未封装。
- 工艺/尺度、极性、真实W/L、CT逐孔归属、阻值和新增网络未确认；未做真实DRC/LVS。

## 复现与交接

- 最新候选复现：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-left-large-mos-revision-v2/spec-v1.json --output runs/新的左侧CT修订目录`。
- `.venv/bin/python -m pytest -q`；相关Ruff；`git diff --check`。data/不改；runs/、.venv/不入Git。
- POLY415e4ff已推送；所有后续CT工作仍为本地未提交修改，包含联合重建、来源纠正、局部材料修订、测试、文档、基准和复核页。
- [本次验收前完整入口及全部历史恢复链接](docs/history/current-task-before-2026-10-20-upper-ct-reviewed.md)保留原文。长期顺序见[开发计划](docs/development-plan.md)。

[左侧大MOS处理前完整入口](docs/history/current-task-before-2026-10-20-left-large-ct.md)保留此前验收和恢复状态。

[本次A–F反馈前完整入口](docs/history/current-task-before-2026-10-20-left-ct-v2-review.md)保留1946候选、原未决和E负例状态。
