<!-- 来源：CURRENT_TASK.md；归档日期：2026-10-20；以下原文完整保留。 -->
# 当前任务

## 目标与授权

2026-10-20：继续CT联合重建，当前只处理中下部MOS反馈的局部修订。用户已批准143个橙色候选，要求C/D恢复大多数三排源漏孔、补边列，C红叉明确不是孔，F单栅孔为双孔。本轮不推送GitHub，不自动确认M1/net。

POLY基线415e4ff已推送；全部后续CT实现、材料局部修订、测试、文档、基准和页面仍是本地未提交修改。Git状态包含多轮既有工作，不清理或覆盖。

## 最新结果与验收状态

- [局部修订复核页](docs/assets/ct-lower-middle-mos-revision-v2/index.html)、[检查点](docs/checkpoints/2026-10-20-ct-lower-middle-mos-revision.md)、[人审原话](benchmarks/ct-lower-middle-mos-revision-v2/human-review-v1.json)、[批准范围](benchmarks/ct-lower-middle-mos-revision-v2/scoped-acceptance-v1.json)。143橙框已批，不再要求逐孔重审；新增/移动精确位置仍是候选。
- [当前CT7044孔](benchmarks/ct-lower-middle-mos-revision-v2/model-v1.json)、[当前材料](benchmarks/ct-lower-middle-mos-revision-v2/material-model-v1.json)、[逐记录台账](benchmarks/ct-lower-middle-mos-revision-v2/ledger-v1.json)、[覆盖与未知](benchmarks/ct-lower-middle-mos-revision-v2/coverage-v1.json)。继承6874、增加170＝143已批橙框＋27数量/边列/栅孔局部补充；34条父记录局部修订，其中23条中心改变；6840条父记录完整不变。
- C：G40/G42上下排完整AA源漏列各11列均三排；下排右侧阶梯边列补2处局部候选。G40上排最右阶梯列2孔，原红叉按非孔排除，不扩AA承载它。[负例](benchmarks/ct-lower-middle-mos-revision-v2/excluded-sites-v1.json)。
- D：G41/G43上下排完整AA源漏列各11列均三排；最左阶梯边列各补1个，精确源图行与AA位置对应仍候选，不按三排强行填满阶梯边界。
- F：G47-P01改为2栅孔，原单孔设计坐标左移6px、新孔右移6px，节距12px。原来源亮峰不动；第二孔原图中心为邻孔相位估计，不能称独立测峰。其他单峰栅G40-P08、G41r2-P03、G43r2-P03、G43r2-P10保持原状，用户未单独裁决其精确孔数。
- 原因：剖面只见两峰时，原程序将检测到的行当作完整行数并拉满AA高度，漏第三行且放大孔距。普通几何门不能发现这种合法但不完整的结果。[新结构/数量检查](benchmarks/ct-lower-middle-mos-revision-v2/stage-quality-v1.json)检查44个完整三排列、共相位等距、4个阶梯例外、F双孔及红叉负例；原版44个本轮要求不满足，修订版均满足。这是人审样本驱动检查，不是独立算法召回率证明。
- 全6874来源证据逐条保持；原4940完整记录保持；695POLY和335AA对象保持。原始照片与已有验收文件不改；新材料文件只有父版本元信息更新，材料对象无修订。
- 7044孔整体几何PASS，重叠0、最小孔距违规0、最小边距4.4px，5px方孔/3px孔距/1px包围与沟道避让预算不降。49项相关测试通过；输入/父哈希、静态资源、SVG/PNG及模拟切换通过，C/D/F规则预览已目视检查。[验证](benchmarks/ct-lower-middle-mos-revision-v2/verification-v1.json)。真实浏览器渲染未实测；不是实际PDK DRC。

## 唯一下一步

只核对新页C/D三排孔与阶梯边列相对位置，以及F双孔。A/B/E提供上下文；已批143橙框、原4940工作快照及既有材料不重审。通过后再评估全幅剩余CT覆盖，不提前宣称全幅完成。

## 接续基线及仍生效裁决

- [POLY基线](benchmarks/poly-closeout-v3/stage-acceptance-v1.json)：Q1/Q2/Q4通过，Q3右侧6MOS。后续CT已授权局部修订AA/POLY，但需明确ID、父版本、前后台账，不能任意扩张材料迁就孔位。
- [RIGHT6已审](benchmarks/ct-right6-reviewed-v5/acceptance-v1.json)、[W1/环修订已审](benchmarks/ct-transfer-revision-v2/acceptance-v1.json)、[Q2栅60孔已审](benchmarks/q2-gate-ct-localization-v1/acceptance-v1.json)、[上方小MOS已审](benchmarks/ct-upper-small-mos-reviewed-v2/acceptance-v1.json)、[左侧局部已审](benchmarks/ct-left-large-mos-revision-v2/acceptance-v1.json)。左侧A/C/F通过，B连接关系通过但孔数细节意见保留，D显示通过，E批准AA右缘+6方案已执行。旧661环孔仅连接基本通过，几何细节意见保留，不升级为逐孔真值。
- R2_Q1历史栅CT归属与局部M1裁决保持；[本批两个源图点位在历史簇内](benchmarks/ct-lower-middle-mos-v1/prior-R2-crosscheck-v1.json)，不借旧簇批准扩充新网络。完整模型/哈希锁定不等于整快照逐孔人工批准。
- 下中部140栅联合几何、U05、S01/S02来源、S03-03/04独立性、U10、18条旧电阻主体、SG-U04-W01电阻保持；Q3新宽MOS与该电阻不是同一对象。AA-F00872依人工裁决退休，原证据不改。
- R1/R2非AA间隙、近邻环隔离、V3两水平POLY不补桥、照片外G67不补闭合、界面遮挡/邻片不扩材料、原八图、195保留对象及网络v33历史裁决继续有效。
- 原生照片坐标与规则设计坐标分开；人工确认存在/数量不等于精确点标。human_confirmation / algorithm_detected=false，不伪造亮峰。相对像素单位；真实尺度、极性、W/L、阻值、工艺DRC/LVS、新CT具体M1/net归属与全幅完整性未知。
- AA仓库skill v1未全局安装，POLY/CT skill未封装。CT工作流固化见[架构记录](docs/architecture/ct-reconstruction-workflow-v1.md)；长期顺序见[开发计划](docs/development-plan.md)。

## 复现与交接

- 当前修订复现：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-lower-middle-mos-revision-v2/spec-v1.json --output runs/新的中下部CT修订目录`。输出目录须不存在；不重新跑父阶段覆盖模型。
- 相关测试：`.venv/bin/python -m pytest -q tests/test_ct_transfer.py tests/test_ct_joint_reconstruction.py tests/test_gate_terminal_localization.py`；相关Ruff；`git diff --check`。data/不可改；runs/、.venv/不入Git。
- [本次反馈前完整入口](docs/history/current-task-before-2026-10-20-lower-middle-ct-revision.md)逐字保留全部历史验收、原140栅候选状态与此前恢复链接；旧快照均保留，不替换批准记录。
