# 当前共栅网已识别分支点亮复核稿 v33

W1已由用户确认经CT接AA扩散端。至此，本轮已识别分支的金属点亮和端点类别复核完成：Q1/Q2共栅经当前长M2分三路，T→N04→五个M2/M1接入→CT→AA；S1/S2→L01→W/M2→W1/M1→CT→AA；B→M1长横线/右侧母线→绿色梳齿M1/M2/M3同电极。橙色梳齿对极隔离。

- [统一静态复核入口](../runs/roi2-gate-network-reviewed-v33/index.html)
- [金属总览](../runs/roi2-gate-network-reviewed-v33/gate-network-metal-overview.png)
- [连接摘要](../runs/roi2-gate-network-reviewed-v33/gate-network-connection-summary.png)
- [AA接入位置](../runs/roi2-gate-network-reviewed-v33/six-AA-access-locations.png)
- [W1下接端已审](../runs/roi2-gate-network-reviewed-v33/W1-CT-AA-reviewed.png)
- [W1裁决](../benchmarks/metal-extension/roi2-W1-CT-AA-review-v1.json)
- [当前拓扑](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v33.json)
- [覆盖记录](../benchmarks/metal-extension/roi2-gate-network-coverage-v33.json)

六份AA接入记录表示六个观察位置，不等于六个器件、六个相互隔离的扩散区，不分配S/D。AA图的粗位置标记沿用局部搜索参考，不是精确边界；没有把整个AA条或矩形合并成导体。连接摘要不是完整MOS原理图。B绿色电极与旧R2_CAP_01之间没有自动身份合并；旧错误gate→A→MOM关系继续挂起。

已识别分支复核完成与完整物理网无遗漏不同：其他未识别过孔/接口、缺少已验收配准的M4关系、照片外延伸仍未知。没有新证据要求逐个确认所有CT，也不继续为了消除抽象未知而制造新确认节点。后续按既有约定汇总本轮入口选线、局部配准范围、整段分支检查和电极隔离的错误与改进；当前稿可作为人工基准种子，不能称独立盲测。

原图未改。生产代码未改，无新GitHub推送。通用case v14仍带历史旧入口关系，不能用它代替v33伴随拓扑宣称整网结果；完整通用case导出待后续适配。

## 复盘固化与 GitHub 归档

2026-10-17 已固化[金属点亮流程 v1](metal-tracing-workflow-v1.md)，最终静态入口及四张图已保存至[版本化证据归档](../benchmarks/evidence/README.md)。上文“无新推送”等描述是 v33 形成时状态；现用户已授权提交推送本轮开发与复核产物。下一轮先重走流程再评估 skill；未宣称自动整网追踪已实现。
