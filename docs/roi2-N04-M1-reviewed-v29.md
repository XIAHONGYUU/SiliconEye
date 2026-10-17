# N04下接M1复核与T漏项修正

用户原话：“批准无误，但是别忘了T那根线对应的下面的M1长竖段”。J1/J2/J3/J4下接M1身份及连接获批准。T对应上方区域中的M1长竖段按用户纠正补回；既有T沿途gate折返双横线、B最下方长横线继续保留。

上一版以局部C/D搜索不充分排除了T-U。这不构成物理断开的证据；本次由用户指出T下方长竖段后，恢复其导体级连接。AI将描述定位到原T-U附近长竖指（约x2300..2306、y1960..2190），此源图定位与精确V1中心仍为参考，不能把用户纠正扩大为像素掩码或全局配准批准。T近(2306,2128)仅为亮点参考，不在图上圈为已审过孔。中部旧(2323,2502)排除不变。

- [人审与T纠正](../benchmarks/metal-extension/roi2-N04-M1-review-feedback-v2.json)
- [源几何记录](../benchmarks/metal-extension/roi2-N04-five-M2-to-M1-reviewed-v29.json)
- [拓扑v29](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v29.json)
- [五根M1宽图](../runs/roi2-N04-five-M2-to-M1-v29/five-M1-native-highlight.png)
- [M2/M1同色原图](../runs/roi2-N04-five-M2-to-M1-v29/five-M2-to-M1-reviewed-source.png)
- [M1总览](../runs/roi2-N04-five-M2-to-M1-v29/M1-network-overview.png)

下一步：在五根M1可见范围检查CT及下层材料落点，先核对局部结构对应再投影；未知保留未知。不穿过MOS沟道或电容介质，不恢复旧gate→A→MOM归属，不宣告全网闭合。原图与v28历史不改，无生产代码修改、无推送。
