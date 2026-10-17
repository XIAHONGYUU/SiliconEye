# B端绿色电极已审，继续检查下接材料

用户确认“绿色 M2、M3 梳齿通过过孔与绿色 M1 同属一个电极，而橙色母线属于另一极、保持隔离”。已加入B电极M1→V1→M2、M2→V2→M3两条导体级连接；每条表示一组接口，不指定过孔数量、精确位置或像素掩码。橙色对极保持隔离，不与旧ROI2电容自动合并。

- [人审记录](../benchmarks/metal-extension/roi2-B-comb-electrode-review-v1.json)
- [当前拓扑v31](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v31.json)
- [金属覆盖记录](../benchmarks/metal-extension/roi2-gate-network-coverage-v31.json)
- [更新三层点亮总览](../runs/roi2-B-comb-reviewed-v31/corrected-gate-three-metal-reviewed.png)
- [B电极已审宽图](../runs/roi2-B-comb-reviewed-v31/B-comb-electrode-reviewed.png)

B绿色电极在M1/M2/M3可见梳齿范围复查：M2母线未见充分支持的额外引出；M3母线和横齿与旁边长横线保留可见间隙，未见足够支持的V3候选。因此没有加入M4连接；该观察不是全局无过孔、无出口的人工裁决。

下一人工节点在上部五M1下接材料。已用本处外框三角点分别建立M1→poly、M1→AA局部仿射搜索候选，第四框角留出；poly五列CT在源图单独标记，M1端头搜索到CT列顶部的偏差约1.8～6.8px，只作寻找同一列的诊断，不是独立配准真值。AA彩线为搜索条带，故意不填满AA矩形、不穿越沟道合并扩散区。J4超出左侧拟合外框支撑，保留外推边界。

- [M1／poly／AA宽图](../runs/roi2-B-comb-reviewed-v31/upper-five-M1-CT-AA-review.png)
- [候选记录](../benchmarks/metal-extension/roi2-upper-five-M1-material-candidates-v31.json)

需裁决：J1、T、J2、J3、J4是否经图中对应CT列接到AA扩散端？只核对接触列与端子类别，不逐个确认CT，不指定S/D。五条材料连接尚未加入已确认拓扑；W1下层材料也未闭合。全网不宣告完成。原图不改，无生产代码修改、无推送。
