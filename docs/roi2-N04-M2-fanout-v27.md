# N04局部投影及M2接口候选

用户指认“应该是NO4这条线”，统一对应此前图稿N04。按工作对应使用T→N04，保留原话及暂定语气。N04参考路径原生M3约(2054,2219)至(2684,2208)。

- [用户选择](../benchmarks/metal-extension/roi2-T-N04-user-selection-v1.json)
- [局部变换记录](../benchmarks/metal-extension/roi2-N04-local-registration-candidate-v27.json)
- [候选接入清单](../benchmarks/metal-extension/roi2-N04-M2-fanout-candidates-v27.json)
- [修正局部叠图](../runs/roi2-N04-M2-fanout-v27/N04-corrected-local-overlay.png)
- [M2与M3原图宽视图](../runs/roi2-N04-M2-fanout-v27/N04-M2-attachment-candidates-wide.png)
- [当前拓扑v27](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v27.json)

采用局部相似变换，三个相邻错开线端的AI候选对应约束尺度和转角，T以“点落在线上”的约束参与拟合，没有虚构T在M3上的精确横坐标。拟合残差[0.5184559069606635, 1.6785292717159868, 1.88908422926453]px；留一线端误差[1.2440648448981453, 2.634298742367826, 3.4659699170870795]px。拟合点并非人审校准像素；T也不是独立验证点。端部J1/J4超出三个锚点横向支撑，外推不确定性较高。另记录200组±5px锚点扰动的投影敏感性，不能当实际精度。此变换只用于T周围，不替代S/W或全图配准。

可见范围筛得5个M2位置：J1左端、T、中间方形块J2/J3、J4右端。只有T为用户指定工作连接，其余4处未确认V2及N04归属，不写入已审连接。尤其J2/J3仅凭投影经过方块底边不能证明打孔，须核对下层M2的V2证据；不能报成5条已确认M2，也不能将其视为5个不同电气网络。没有排除更小接口或V3。

保持W1支线已审状态、材料未知，电容P1/P2分开，旧gate→A→MOM归属挂起。原图只读，无生产代码修改、无推送。
