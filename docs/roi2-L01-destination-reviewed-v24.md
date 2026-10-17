# S1 / S2 → L01 已审连接

用户裁决：“两个孔都接在 **L01 右端向上的短竖段**”。两孔连接到同一个M3导体，稳定ID `R2_corrected_gate_L01_M3_01`；不是两根独立M3。

- [人审记录](../benchmarks/metal-extension/roi2-S1-S2-L01-review-feedback-v1.json)
- [拓扑v24](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v24.json)
- [已审L01及左端W候选宽图](../runs/roi2-L01-reviewed-v24/L01-confirmed-and-W-candidate-wide.png)
- [左端原图上下层宽视图](../runs/roi2-L01-reviewed-v24/W-left-unmarked-context.png)
- [W候选和局部搜索参数](../benchmarks/metal-extension/roi2-L01-left-interface-candidate-v24.json)

L01原生M3参考路径从约(1228,3242)延续至(2320,3210)，右端上折至约(2324,3185)。身份确认不代表精确掩码、所有接口或v23配准验收。

沿线检查发现左端W候选：M2约(1200,3200)端头有成对亮点。独立使用左区六组AI候选线端做相似变换，W与S不参与拟合；拟合残差1.2～6.3px，留一1.6～13.5px。L01左端逆投影约(1201.7,3203.4)，支持W搜索区域，但锚点身份未人审、误差仍可影响相邻细线，因此未新增W已确认连接，也未发布精确跨层叠图。

下一步裁决W是否确为L01左端的M2接口；之后追踪相应M2。T的M3落线仍须单独定位。没有充分证据断言沿L01无其他V2/V3；未恢复旧gate→A→MOM关系，电容P1/P2仍分开。原图只读，本轮无生产代码改动、无推送。
