# A/B的M3及ABAB结构推断（2026-10-23）

[用户原文](../../benchmarks/mid-ab-structural-hypothesis-v11/human-structural-inference-v1.json)提出B经M3／邻M2接T1、A直接接T3，并以排除dummy后的ABAB布局及M3走线支持；明确孔未看清。因此保存为human_structural_inference_vias_not_resolved，不新增已审接口。既有35接口、H1/A、H2/B、U1/U2隔离及主网边界不改。

## 执行纠偏

原事前观察保留了M3替代解释，但复核问题过于聚焦“下端V1直接落M1”，需要把上层母线及其回接分支纳入同一次判断。这是执行未充分落实现有正向布局／跨层接口流程，不是要求用户逐孔批准，也不以孔模糊阻止提出与检查结构假设。

[当前宽图页](../assets/mid-ab-structural-hypothesis-v11/index.html)扩大M1到T1左侧，四条主竖线L4/L2/T1/T3间距123/121/121源像素；M2端部呈两排，M3有错开的X/Y短段及延伸Z。可见结构支持交错解释，但不能独立确认V1/V2或精确承载。[结构观察](../../benchmarks/mid-ab-structural-hypothesis-v11/structural-observation-v1.json)分开支持、候选与未知；不把M2亮端当V1，不把近似y当配准。

T1“左边相隔的四根线”可能指第4根，也可能指4根全部，已异步询问。物理条带索引L4为T1左侧第4根，L2为T3左侧第4根。仅在前一种解释下条件分组为B={L4,T1}、A={L2,T3}，未采用。A端“直接”与前文M3路线的详细关系保留未知，不擅自强填。

## 验证

[核验](../../benchmarks/mid-ab-structural-hypothesis-v11/verification-v1.json)：52处SHA引用及父包清单，35接口人审来源，推断／条件分组未转确认，A详细路径未强填；6份裁片与源像素一致，16链接和1段JS语法通过。已看三层放大标图，未测浏览器交互。代码未改，未重跑软件测试。

共同几何／照片及旧记录不改，自动网络边为空，整网未完成。无新孔形或跨层投影。此次未提交／推送。

[前入口归档](../history/current-task-before-2026-10-23-MID-AB-structural-hypothesis.md)payload 16414 bytes，SHA256 `82a8e95228e7dd3107bb763bad0dbb967761d1b796a1696f4e64e020fe82ccab`，核对原字节一致。
