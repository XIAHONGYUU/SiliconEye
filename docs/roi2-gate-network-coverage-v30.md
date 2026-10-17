# 共栅网可见金属总览与B端新分支

本轮用户确认T下方M1长竖指无误，继续追踪全网。五根上部M1、共栅M1、B长横线/右侧母线、W1，以及六份M2、N04/L01两根M3的现有记录已统一点亮。导体身份已审，参考像素路径不等于精确掩码。

- [三层总览](../runs/roi2-gate-network-coverage-v30/corrected-gate-three-metal-overview.png)
- [B梳齿三层原图与候选](../runs/roi2-gate-network-coverage-v30/B-comb-native-review.png)
- [B局部配准候选](../runs/roi2-gate-network-coverage-v30/B-comb-local-alignment.png)
- [覆盖与候选记录](../benchmarks/metal-extension/roi2-gate-network-coverage-v30.json)
- [拓扑v30](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v30.json)

新的关键分支在B长横线右转后的梳齿结构：M1右母线及交替横齿为入口，M2/M3均见对应金属梳齿。不能因包络对应直接并网。已另作本处M2→M1、M3→M1局部仿射候选，三包络角点拟合、一角点留出；训练角点、留出角点均为AI近似坐标，残差只检查包络，不验证过孔。此处未沿用上部C/D变换。绿色表示同侧电极候选，橙色对极保持隔离。未新增B梳齿V1/V2确认边；不把它自动等同于旧ROI2电容。

需用户裁决：B接入的是不是图中绿色右母线及五根横齿，并且经V1/V2与绿色M2/M3为同一电极？若有错，指出哪一层或哪一排。此裁决影响是否扩展跨层导体；无需逐一确认每个亮点。

其他检查：上部五M1下方可见CT列/AA结构，尚未把精确材料落点加入确认网；W1下层材料仍未知。N04/L01全可见跨度复查未发现足够支持的新接口候选，不据此断言所有V2/V3不存在。M4宏观检查没有可加入的接口，未接受M3/M4配准。全网仍未闭合，原图不改，无生产代码改动、无推送。
