# N04五处M2已审，下接M1点亮稿

用户确认J1、T、J2、J3、J4五处均接N04，并要求沿各M2点亮下层M1。

- [五处人审记录](../benchmarks/metal-extension/roi2-N04-five-M2-review-feedback-v1.json)
- [当前拓扑v28](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v28.json)
- [下接候选与原生几何](../benchmarks/metal-extension/roi2-N04-five-M2-to-M1-candidates-v28.json)
- [四条新增M1候选点亮](../runs/roi2-N04-five-M2-to-M1-v28/four-new-M1-native-highlight.png)
- [M2与M1独立原图同色复核](../runs/roi2-N04-five-M2-to-M1-v28/five-M2-to-M1-source-review.png)
- [含T既有gate/B的M1总览](../runs/roi2-N04-five-M2-to-M1-v28/five-branch-M1-overview.png)

| M2分支 | M1候选V1参考像素 | 当前结论 |
|---|---|---|
| J1 | (2053,2151) | 新增候选长竖指，身份/接口未人审 |
| J2 | (2443,2127) | 新增候选长竖指，身份/接口未人审 |
| J3 | (2551,2124) | 新增候选长竖指，身份/接口未人审 |
| J4 | (2687,2118) | 新增候选长竖指，身份/接口未人审 |
| T | gate折返双横线、B最下方长横线 | 复用既有已审接入，不强行一条M2只配一条M1 |

四处从M1原图亮点查找V1候选，源几何完整显示对应竖指；候选中心线在可见间隙前截断，不跨到邻近横线。C/D矩阵只作搜索诊断；上部区域在先前人工接受范围外，不能把逆投影落入M2当作新接口批准。主复核图是两个独立原生坐标的源视图，无跨层投影。J3方块下邻近M1框线没有相应V1证据，不自动并入。

曾考虑上方T-U点(2306,2128)，但搜索逆投影靠近相邻上方方块，未充分覆盖选定T端头，已剔除；不为了凑足五条而归入T。T长M2沿线源图重新查看，保留此前whole-span观察；(2323,2502)邻近亮点的排除保持，没有新增充分支持的M1接入，不宣称其他V1不存在。

所有五处M2→M3的人工批准已落入拓扑；四条新增M2→M1仍为候选，未加入已确认连接数组。既有共栅、B/W1裁决保留；P1/P2分开、旧gate→A→MOM归属挂起。CT/材料归属不扩展。无生产代码修改、无推送。
