# 当前任务

## 目标与授权

2026-10-20日终：用户授权保存当前状态、更新顶层文件并提交推送GitHub，明天继续。本轮剩余范围的检查/候选整理已完成，整层HOLD；等待Q1/Q2/Q3来源裁决后继续收口，不宣称全幅定稿，不启动新M1/net追踪。

本次Git保存范围：POLY415e4ff之后的CT代码、测试、基准、材料局部修订、证据复核页、工作流与检查点。原始照片、runs/和.venv/不纳入本次变更。保存前原文见[日终归档](docs/history/current-task-before-2026-10-20-ct-github-handoff.md)，[交接与验证记录](docs/checkpoints/2026-10-20-ct-github-handoff.md)记载本次保存范围；实际提交与推送以Git记录为准。当前文件是唯一实时入口。

## 当前有效输出与质量状态

- [统一复核页](docs/assets/ct-full-frame-remaining-v1/index.html)、[检查点](docs/checkpoints/2026-10-20-ct-full-frame-remaining.md)、[一次裁决清单](benchmarks/ct-full-frame-remaining-v1/review-questions-v1.json)、[整层质量门](benchmarks/ct-full-frame-remaining-v1/stage-gate-v1.json)。页面置顶3组问题，Q1/Q2有宽视野POLY与独立M1，Q3分A/B/C；其余O/T1/T2/T3/L/R仅供抽查，不要求逐孔审批。
- [CT候选模型10004条](benchmarks/ct-full-frame-remaining-v1/model-v1.json)＝原7044完整保留＋新增2960（AA1945、POLY1015）；[材料工作模型](benchmarks/ct-full-frame-remaining-v1/material-model-v1.json)695 POLY/335 AA对象逐条保持。记录数不是确认孔数或器件数；不扩大原分项批准。
- 模型与报告写有stage_status=HOLD、whole_frame_complete=false。10004条安全子集几何PASS，重叠/孔距违规0，原5px方孔/3px孔距/1px包围及避让预算不降；几何PASS不能替代整层通过。
- [来源隔离台账](benchmarks/ct-full-frame-remaining-v1/quarantined-observations-v1.json)保留403条调查候选，含7条有来源反例的整段AA路径，不能当实际漏孔数；Q1依赖的16条新源漏也不导出。不能仅删反例点再把其余路径称合格。
- [材料覆盖](benchmarks/ct-full-frame-remaining-v1/final-material-coverage-v1.json)：原286个材料已有直接CT引用，409个剩余均已检查，401个有新增CT候选，2个V3旧截段引用历史端子关系，6个端部未确定。335 AA处置为旧源漏55、新源漏检查115、旧环12、新薄条/环29、dummy108、紧凑未关联AA11、邻片边界5；有处置状态不是物理层完整。
- 局部源漏补查109列，得到142个进一步光学候选；再以栅端亮条定位三个弱小MOS的相邻源漏。当前被检查的115个新AA家族中，仅Q1两块依赖AA主动保持无CT导出。缺观察不等于物理无孔，未自动按规律补齐。
- 右下G49按13条实际源漏列及独立平行框修订来源，区分上方电阻环、本组上环和下端栅CT；源漏用共同规则相位，不将两个检出行拉满AA。[来源修订v2](benchmarks/ct-full-frame-remaining-v1/source-correspondence-repair-v2.json)。小MOS成对行的端部方向来自本组源图观察，不套用Q2全下端裁决。
- 孔距最近距离改为精确空间索引，保留硬约束。54项相关测试（5.41s）及日终全量447项测试（19.65s）、Ruff、父/源哈希、静态资源/模拟切换通过，O/R/Q1/Q3B及原图问题卡目视检查。[验证记录](benchmarks/ct-full-frame-remaining-v1/verification-v1.json)。浏览器真实渲染未自动实测；没有真实PDK DRC/LVS。

## 明天唯一下一步：收到3组来源裁决后局部修订

1. **Q1左侧四管**：保留四管/2×2结论。旧源框端部取点与既有环/G18源记录重合，不能凭旧引用认定物理归属；需要指出任意一个真实栅端CT或引出侧。红叉是“本组归属未通过”，不是“亮点非CT”。相关新栅CT与依赖新源漏暂缓，原G18工作记录不改。
2. **Q2 U10细长POLY下端**：需要实际CT位置及分别引出/共用端部的判断。旧紫框不是已验证材料边界；不凭亮条自动补CT或POLY桥。
3. **Q3环／栅端来源对应**：A/B/C三卡核对橙G与蓝A在原图和联合图的对应。对应确认后重新定位7条暂缓AA路径，保留旧记录，最后再做整层门检查。

此时不封装CT skill；不以精确孔数小误差反复索要批准，不重算已审AA/POLY或7044工作快照。当前剩余未知并未因候选文件写出或几何PASS自动解决。

## 必须继续继承的裁决与边界

- [原C/D/F批准及7044快照](benchmarks/ct-lower-middle-mos-revision-v2/acceptance-v1.json)：C/D显示三排和边列、F双孔已批；143橙框已批；C原红叉明确非孔。Q1此次红叉是不同的来源归属标记，不能混用。
- [POLY基线](benchmarks/poly-closeout-v3/stage-acceptance-v1.json)：Q1/Q2/Q4通过、Q3右侧6MOS。RIGHT6、W1/环局部、Q2栅60孔、上方同环40栅及左侧局部批准原样继承；左侧B孔数细节和旧661环孔几何意见保留。精确源点估计不升级为人工像素真值。
- V3_G1/G2只是已审主体截段，旧端子与M1/M2关系保留在[历史端子记录](benchmarks/local-terminal-review-v1.json)、[V3 case](benchmarks/block-case-v1-v3.json)及旧网络；不补POLY桥以强塞孔。R2_Q1历史归属、R1/R2非AA间隙、近邻环隔离、S03-03/04独立性、U10旧形状、18条旧电阻、SG-U04-W01电阻身份、原8图、195保留对象、网络v33都不改。
- AA-F00872按人审退休，源证据不覆盖；照片外G67不补闭合，界面遮挡、邻片不扩材料。允许新证据驱动局部材料修订，但需明确ID、父版本和前后台账，不能扩AA/缩CT迁就错误来源。
- 原生照片坐标与规则设计坐标分开；相对像素单位。工艺、尺度、极性、真实W/L、阻值、具体新M1/net与全幅完整性未知。新CT全是带来源的候选，授权生成不等于物理批准。

## 复现与交接

- 基础候选对象/几何/复核图：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-full-frame-remaining-v1/spec-v1.json --output runs/新的CT剩余目录`；输出须不存在。最终包装另附HOLD元数据和问题图；[版本说明](benchmarks/ct-full-frame-remaining-v1/README.md)。实验配方在provenance仅供审计，不原地重跑覆盖候选，更不是已封装skill。
- 测试：`.venv/bin/python -m pytest -q tests/test_ct_transfer.py tests/test_ct_joint_reconstruction.py tests/test_gate_terminal_localization.py`；相关Ruff；`git diff --check`。data/不改，runs/和.venv/不入Git。
- [本次完整历史入口归档](docs/history/current-task-before-2026-10-20-ct-full-frame-remaining.md)逐字保留前阶段批准、边界和恢复链接；阶段记录只追加、不改写人审结论。[CT工作流](docs/architecture/ct-reconstruction-workflow-v1.md)保存本轮方法与门控经验。
