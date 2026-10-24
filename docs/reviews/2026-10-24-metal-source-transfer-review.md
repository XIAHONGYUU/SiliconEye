# 五层整体来源复核与独立区域迁移

用户要求先复核连续五层整体几何，再进行独立区域迁移。本轮完成指定导体范围的来源/相对几何复核，修正一处错位；独立样本工具门已验证，Q2已获人审，Q1仍待裁决。

## 整体复核发现并修正的问题

旧模型虽然满足正交、同层间距和孔组双侧包围，却有一处同帧位置关系错误：M1照片中U1右端x=1945，在P08左竖段x=2006的左侧；旧规则图却画成1700>1380。两者在不同y位置，未发生碰撞，所以原几何门不会报错。

本轮只将U1右端1700缩到1310，恢复1310<1380；其余32条模型记录、11条已审接口、A/B现行成员均保持。[新候选](../assets/conductive-medium-source-review-v2/index.html)、[修订范围](../../benchmarks/conductive-medium-source-review-v2/revision-v1.json)、[整体复核记录](../../benchmarks/conductive-medium-source-review-v2/whole-geometry-review-v1.json)保存前后证据。原图和旧模型不覆盖。

新增同层、同照片的显式来源顺序门；旧模型在新门下失败，局部修订后通过。这个门只检查所声明的次序，不推算跨层变换或像素精度。另核对M1列、M2列和M3母线的代表顺序。U3经CT接AA环的批准已接续到新候选，不再重新要求审批。

结论是**指定片段的规则几何可继续使用，完整五层GDS尚未恢复**：U1/U3的右侧转角、其他导体和A/B的具体接口仍未建模或未知；V1/V2方框只是已审孔组支持区，不是实测孔阵列。新几何未采用为共同工作层。

## 独立区域迁移

新窗口为原生[2250,100,3350,1150]，与旧中样[800,1700,2350,3300]交集为0。它仍来自同一颗已知芯片，不是陌生芯片或隔离历史上下文的盲测。[首次AI观察](../../benchmarks/metal-independent-transfer-v1/initial-ai-observation-v1.json)在本轮人工回复前保存。

新局部包含6条金属、2处接口支持区。复用已有`geometry_audit`、`interface_audit`、`source_identity_audit`、`source_order_audit`、`source_panels`和分层SVG函数，不新增案例专用生产脚本。几何、来源、包围及A/B顺序检查通过；同层误并、V1借用M2来源、缺上下包围、错层对四种反例均被拒绝。

| 接口 | 首次判断 | 当前人审结果 |
| --- | --- | --- |
| Q1 / IT1-V1-A | M1圈示孔组为V1，接窄M2-A | 待裁决，正确性仍为null |
| Q2 / IT1-V2-B | M2-B处V2接紫色粗M3母线 | 用户“Q2正确”，通过；送审后修订0次 |

[当前迁移页](../assets/metal-independent-transfer-v1/reviewed.html)、[Q2原文](../../benchmarks/metal-independent-transfer-v1/q2-human-review-v1.json)、[当前状态](../../benchmarks/metal-independent-transfer-v1/reviewed-state-v2.json)、[评价记录](../../benchmarks/metal-independent-transfer-v1/evaluation-reviewed-v2.json)。A/B是否同层连续另保持未知，不能由Q2承载批准推导；孔数、精确几何和完整网表均未批准。

本次证明的是这些底层工具可在另一空间区域表达候选并执行质量门。现有`conductive_medium`统一CLI仍要求已审接口，没有为新接口建立完整候选接续入口；此次没有用假批准绕过它，因此不声称已经完成同一CLI仅换配置的端到端迁移。需先完成Q1裁决，再据结果决定接口适配和正式封装，不能以软件门或Q2一项正确宣布整个skill已验证。

## 技术核验

本轮23项相关测试通过，新增来源顺序反例、跨帧禁用、局部修改不波及其他对象、已审U3接续和未审规范材料对象映射拦截。Ruff与差异检查通过。原候选模型、报告及两页HTML重放保持原内容。

[本轮核验](../../benchmarks/conductive-medium-source-review-v2/verification-v1.json)记录来源/产物哈希、原图裁片像素、页面链接与SVG/JS语法、Q2批准范围和入口归档。未测试浏览器交互，没有真实PDK DRC、全幅覆盖或陌生芯片准确率声明。本轮未提交/推送GitHub。
