# 五处CT→AA已审，W1下接材料待裁决

用户确认J1、T、J2、J3、J4分别经对应CT列接入AA扩散端。已记录五份独立AA接入端，并加入材料连接事实；不指定S/D、器件数量，不并入整个AA矩形，不跨MOS沟道继续扩网。CT数量、精确掩码、配准精度不随导体身份批准而升级。

- [人工裁决](../benchmarks/metal-extension/roi2-upper-five-CT-AA-review-v1.json)
- [材料记录](../benchmarks/metal-extension/roi2-upper-five-M1-material-reviewed-v32.json)
- [当前拓扑v32](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v32.json)
- [五处下接端已审宽图](../runs/roi2-upper-AA-reviewed-W1-v32/upper-five-M1-CT-AA-reviewed.png)
- [金属总览](../runs/roi2-upper-AA-reviewed-W1-v32/metal-network-with-five-AA-reviewed.png)

剩余明确材料节点为W1短M1。以本处窄条结构外框三角点作M1→poly/AA仿射搜索，第四角留出约2.27/5.00px；均为AI近似框角，不是人工结构真值或CT验收。W1投影搜索范围位于poly照片约(1267,3073..3111)、AA照片约(1345,3181..3217)，只画含上下文的搜索窗口，未将其断言为CT中心。既有W1不与相邻M1横线相连的观察保留。

- [W1三层源图宽视图](../runs/roi2-upper-AA-reviewed-W1-v32/W1-M1-poly-AA-source-review.png)
- [搜索记录](../benchmarks/metal-extension/roi2-W1-material-candidate-v32.json)

需裁决：W1经框内CT接到AA扩散端还是poly栅端？若框选结构对应不正确，应先纠正位置。W1材料边尚未写入已确认关系。B电极绿色三层并网与橙色隔离保留；旧gate→A→MOM归属不恢复。其他未识别接口与图外仍未知，全网不宣告闭合。原图未改，无生产代码修改、无推送。
