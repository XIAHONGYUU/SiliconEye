# Gate真实入口的接口检查 v17

用户确认T经V2向上接M3、B经V1向下接M1，T/B之间另有一处M2→M3接口。中间接口的存在已审，精确位置、各接口目标导体ID尚未指定。

## 后续执行顺序

1. 在整条选中M2上检查V2，定位T及中间接口；区分相邻平行M2的侧向短段，不能按邻近归并。
2. 在M1上逐段检查对应长M2下方的V1，包含原gate入口、B端以及中段；已认可的六线局部变换不能外推到上下两端。
3. 先验证相应局部结构对应与覆盖，再标出目标M1/M3；不能仅按各层相同像素、单锚点平移、鼠标位置或亮斑投影。
4. 从真实接口扩展同层导体，保持未知、候选、已审状态。T→M3不表示T处没有V1，B→M1不表示B处没有V2。

当前中心线仅是显示参考，不能证明接口穷尽。此前“仅T/B两端”的检查口径不完整，不再以M2上的端头列表代表整条线的跨层接口列表。旧A链及MOM子图保留其已审物理事实，但不恢复共栅归属。

## 证据

- 人审：[接口方向与中间接口](../benchmarks/metal-extension/roi2-gate-T-B-interior-interface-review-v1.json)
- 当前拓扑：[v17](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v17.json)
- 原图宽视图：[T](../runs/roi2-gate-endpoint-layer-review-v16/T-lower-upper-originals.png)、[B](../runs/roi2-gate-endpoint-layer-review-v16/B-lower-upper-originals.png)

本次只落实追踪检查口径，不启动用户要求留待追踪结束后的统一复盘。无生产代码修改、无推送。
