# B侧M1可见几何收尾与目标M2向M3延伸

B→最低M1长横线的导体身份已由用户确认。本轮沿长横线、右转竖向母线至右侧阵列，补入五条接在该侧母线上的横指候选；相邻左侧母线、反向横指不并入。完成的是当前照片内这一段M1可见几何的候选追踪，不是全部接触/器件端口验收。未通过CT向扩散或MOS沟道扩网；没有足够证据新增V1，也没有宣告所有额外V1绝不存在。

[原图与点亮总览](../runs/roi2-gate-M1-M3-followup-v20/B-M1-visible-branches-review.png)、[宽局部](../runs/roi2-gate-M1-M3-followup-v20/B-M1-array-branches-wide.png)、[几何与范围](../benchmarks/metal-extension/roi2-B-M1-visible-branches-candidate-v20.json)。自适应逐行寻峰曾使第二横指漂到邻行，该临时检查图不作为证据；交付采用按原图确定行身份的固定中心线，精确边界保持未知。

下一阶段已检查目标M2全段及M3附近原图。T→M3及中间另有V2是已有人工事实；尚不能确定对应的M3具体导体。M2约(2341,3307)短支接在右侧邻线(x≈2321)，目标线该处约x2301；不将这处醒目短支自动视为用户所述中间V2。约(2350,2604)端头也在邻线。中间V2的存在不因当前未定位而撤销。

[目标M2整段原图/标线](../runs/roi2-gate-M1-M3-followup-v20/M2-target-full-span-review.png)、[T附近M2/M3宽原图](../runs/roi2-gate-M1-M3-followup-v20/T-M2-M3-native-context.png)、[接口定位记录](../benchmarks/metal-extension/roi2-target-M2-M3-interface-localization-v20.json)。两层图为独立原图窗口，没有已接受的新变换，不能按相同像素坐标直接选线。SIFT候选仅29匹配/5内点且线性尺度退化近零，已拒绝；上下边框的局部畸变也不适合据此直接选择密集M3线。没有提交错误投影或新增M3连接。

当前最小人审点：在整段M2原图中指出中间V2位置；若指N附近，需指出它接在哪根平行M2上。定位后以该接口和T为目标做有结构锚点的M2/M3局部核对，再逐根点亮M3。

[当前伴随拓扑v20](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v20.json)。直接来源哈希、B目的导体身份、P1/P2不并网及旧gate→A→电容归属挂起检查通过。原图只读，无生产代码修改，无GitHub推送。
