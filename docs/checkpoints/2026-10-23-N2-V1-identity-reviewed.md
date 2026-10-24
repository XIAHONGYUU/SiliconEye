# N2附近V1身份与M1连续性裁决（2026-10-23）

用户原文“u1,u3上在m1处有v1,u2没有。可以看到U1和U2本身就是一条线，所以有孔是非常正常的。”保存在[人审记录](../../benchmarks/n2-v1-identity-reviewed-v7/human-review-v1.json)。落实U1/U3有V1、U2无V1，U1/U2属于同一M1；不把同线推成U2也有孔，不把U3顺带并入。精确孔数／边界和M2承载本轮未批准。

[身份与同层事实](../../benchmarks/n2-v1-identity-reviewed-v7/reviewed-site-identities-v1.json)独立于旧31条跨层接口保存。两处正V1组使用V1-N2-U1／V1-N2-U3；U2没有via_group_id。U1/U2来源M1 ID为M1-N2-U1-U2，只是已审观察点归属，不是全幅精确多边形或全部分支完成。

## 接续结果

[当前大字页](../assets/n2-v1-identity-reviewed-v7/index.html)保留完整上下段、三处4倍宽局部、原图/标记及层切换；M1上蓝线标U1/U2同线，灰线标U2以下候选延伸。薄竖段在U3宽横带上方似有暗间隙，故不把两者合成一个物理M1，也不由此断言全局不同网。用户确认只覆盖U1/U2同线。

M2蓝色N2和灰色J01供相邻导体参照；本轮AI初判U1/U3的V1都由N2承载。两个粗对应仍候选，真值null，无M2像素落点，尚无新已审跨层边。[AI观察](../../benchmarks/n2-v1-identity-reviewed-v7/continuation-observation-v1.json)、[请求](../../benchmarks/n2-v1-identity-reviewed-v7/request-v1.json)。下一个问题只核这两处导体级对应，不重复V1身份／U1-U2连续性。

控制边界：人工从原图明确确认的粗物理连接可以作为有范围的连接事实；这不证明精确矩阵或孔包围。受支持局部配准仍是自动投影／坐标推导／几何采用的前提。此前“先核V1身份”门已完成，不把缺数值配准误用为拒绝人工粗身份事实；也不以本图未配准自动重叠推导新边。没有新矩阵、旧局部矩阵不外推、没有V1/V2同孔配对。

[追踪流程](../metal-tracing-workflow-v1.md)第2/3项补入此边界及“同线不等于处处有孔、无孔不等于断线”。[评价](../../benchmarks/n2-v1-identity-reviewed-v7/evaluation-result-v1.json)只记录人工三处presence与U1/U2连续性；事前没有确定二元预测，不填造3/3自动准确率。

## 核验与继承

[核验](../../benchmarks/n2-v1-identity-reviewed-v7/verification-v1.json)：45处引用SHA；U2不造孔／M1不断线、U3不误并、两候选未采用；12份原图裁片像素一致、22链接、24动态图路径、1段JS语法通过，已看两层宽标图；未测浏览器交互。本轮无源码修改、pytest未重跑，先前38测试保留为当时证据。

B1/L113路径、旧31跨层接口、P组、共同v5/33导体、材料与照片不变；本轮仅身份／同层事实，无自动net_edges或整网验收。此次未提交／推送。

[入口完整归档](../history/current-task-before-2026-10-23-N2-V1-identity-reviewed.md)来源CURRENT_TASK.md、2026-10-23，头后payload 17191 bytes，SHA256 `0dbd2c38a6fb02486b9356d30dd41f0f2da171d5f96d312114413e0b3ee3cd33`；已逐字节核对，历史链保持。
