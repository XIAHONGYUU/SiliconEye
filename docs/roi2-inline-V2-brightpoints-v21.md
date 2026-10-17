# 目标M2线身亮点：优先V2候选

根据用户“先判断这条M2上的V2，应该可以找到亮点”的要求，重新沿目标线身检查，不只寻找短支端头。左折弯下方M2约(2300,3158)、(2300,3177)出现两处局部亮点，位于当前目标线身，列为中间V2的优先候选区域[2285,3145,2315,3190]，单位为M2原生px。

两处在原图以及Gaussian σ=1.2、2.0px的辅助检查中均保留局部亮度峰。平滑仅用于检查拍屏纹理影响，交付图使用未经增强的原图副本；亮度持久不等于物理V2证实，不由两个亮斑直接断言有两个独立接口。反光、下层结构及同一落点的双亮瓣仍为替代解释。T/中间另有V2的人审存在事实保留；本轮只给中间位置的AI候选，不改写为已批准坐标。

[宽原图与放大对照](../runs/roi2-gate-V2-brightpoint-review-v21/M2-inline-V2-brightpoints-review.png)、[整段原图参考](../runs/roi2-gate-V2-brightpoint-review-v21/M2-full-span-brightpoint-reference.png)、[来源和坐标](../benchmarks/metal-extension/roi2-target-M2-inline-V2-brightpoints-candidate-v21.json)、[当前伴随拓扑v21](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v21.json)。

上轮只重视侧向短支，漏查了这处线身亮点；撤销“立即要求用户先定位中间V2”的推进顺序，改由AI以该候选区及T为目标继续查M3覆盖。N≈(2341,3307)仍是右侧邻线短支，不能替代线身候选。尚未接受新的M2/M3变换或指定M3导体，不恢复旧gate→A→电容归属。

验证：新记录直接来源SHA-256一致；无原图覆盖、无生产代码修改、无新增人审或M3连接。
