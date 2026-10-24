# A/B本处成员澄清（2026-10-23）

用户最新原文：“T1,L4,经过M2与M3与B连接在一起。T3,L3,经过M2与M3与A连接在一起。”[最新记录](../../benchmarks/mid-ab-structural-hypothesis-v11/grouping-human-review-v2.json)绑定上轮原图页与结构候选，明确B={T1,L4}、A={T3,L3}及M2/M3路径层次。[当前状态](../../benchmarks/mid-ab-structural-hypothesis-v11/grouping-state-v2.json)以两个本处人工接受的结构分组保存。

T1左侧计数歧义关闭，不接左侧4根全部；A的旧AI候选L2由最新L3取代，不凭ABAB将其改回。沿用此前未看清孔的限制：两组成员明确不等于每个V1/V2接口、精确孔形、M3-X/Y承载或整体网络已验证。35原子接口不变，新原子接口0；成员分组决策2，不混用计数。

[新分组页](../assets/mid-ab-structural-hypothesis-v11/grouping-reviewed.html)仅重画两张M1标记副本，显式标L3（旧单图索引x≈1062）、T3为A，L4、T1为B，L2为灰参照。M2/M3原图复用。颜色是跨层分组成员，不是在M1上画同层短路。

前后比较发现：旧E1的123/121/121等距只适用L4/L2/T1/T3，不适用更换L3后的四个索引。当前原生间距62/182/121；不将旧几何支持“继承”为当前ABAB证明，也不擅自移动几何、判dummy或改用户编号。把器件结构背景与M1条带索引差异留给下一次联合自查。

[核验](../../benchmarks/mid-ab-structural-hypothesis-v11/grouping-verification-v2.json)：46处SHA引用、父包原字节、35接口来源、两组成员及层次、L2不复活／旧等距不迁移、16本地链接、12个原图／标记目标、1段JS语法通过。已看新M1宽局部。生产代码未改、测试未重跑，浏览器交互未实测。

共同v5、AA/POLY/CT、33几何和原图／旧包不改，无自动网络边，未宣布整网完成。本轮未提交／推送。

[前入口完整归档](../history/current-task-before-2026-10-23-MID-AB-groups-clarified.md)payload 16758 bytes，SHA256 `4a62f3c530cdc2b70beb34b9eb800ef8c00be01a1621709875dcc76fcb81d6ce`，核对原字节一致。当前入口保留已解决成员和下一步定位任务，不再重复计数问题。
