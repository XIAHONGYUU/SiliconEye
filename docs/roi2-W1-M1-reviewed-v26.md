# W1短竖向M1已审

用户确认W处M2下端经V1接到紫框W1短竖向M1。

- [人审记录](../benchmarks/metal-extension/roi2-W1-V1-M1-review-feedback-v1.json)
- [当前拓扑v26](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v26.json)
- [W1源图及邻近横线](../runs/roi2-W1-M1-followup-v26/W1-short-M1-review.png)
- [M1原生观察](../benchmarks/metal-extension/roi2-W1-M1-native-observation-v26.json)
- [T上下层独立原图及搜索编号](../runs/roi2-W1-M1-followup-v26/T-M2-M3-native-search-review.png)

W1稳定ID `R2_corrected_gate_W1_M1_01`；参考短段约x1244,y3213..3249。原图邻近横线与短段间有间隙；不把它直接扩大成横向母线。CT/AA/poly归属尚未确定，本轮无材料端子新增。图内金属追踪到短段不等于物理网络封闭。

另一已审接口T在M2约(2285,2183)，其M3落线仍未知。提供M3原生搜索行N01..N13，编号为图像参考点而非已确认十三根导体，弱行可能是条纹/邻线残留。不用此前下方拟合外推到T，不以同像素坐标直接投影。需要明确T实际接入哪条M3；若原图不足以识别，应继续精化局部结构配准，不强行选线。

保留S1/S2→L01→W→V1→W1；旧gate→A→MOM关系仍挂起，P1/P2分开。源哈希与记录关系检查，不替代物理验收。无生产代码改动、无GitHub推送。
