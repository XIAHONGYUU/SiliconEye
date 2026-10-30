# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-30 before finalized F1/W1 integration and two end gates.

# 当前任务

## 当前目标与状态

**N 已确认是 V1、接同一条 M2 A，并已进入工作几何；继续核查了上方 M1 横向出口，现停在新孔组 F1 的 V1 身份／M2 W1 承载裁决。** 不再询问 N/Q1/U/D。F1 未加入工作接口，不按已连接扩网。

- [当前复核入口](docs/assets/left-bu-north-reviewed-v4/index.html) · [五层切换／原图](docs/assets/left-bu-north-reviewed-v4/S2-upper-branches/index.html) · [当前规则几何](docs/assets/left-bu-north-reviewed-v4/joint-work.png) · [F1两层原图](docs/assets/left-bu-north-reviewed-v4/F1-paired.png)。
- 唯一几何恢复：[next-request](benchmarks/left-bu-north-reviewed-v4/next-request.json)；[状态](benchmarks/left-bu-north-reviewed-v4/source-review-state.json)、[报告](docs/reviews/2026-10-30-north-reviewed-v4.md)、[验证](benchmarks/left-bu-north-reviewed-v4/verification.json)。
- 当前35金属候选（M1=4/M2=9/M3=22），15已审局部接口（V1=4组/V2=11组），89显式设计候选孔。原14接口、80孔中心保持；原46孔亦在保持集内。设计视口[-1500,0,780,1440]及原点[0,0]不变。
- [N原人审](benchmarks/left-bu-north-reviewed-v4/human-review.json)原话“N：是 V1，接 A”，记录日期保持2026-10-29；本轮2026-10-30恢复并完成接续。新3×3是AI完整阵列候选，实际孔数／精密尺寸未批准；N与U V2不强迫逐孔重合。
- [Q1原话](benchmarks/left-bu-v1-reviewed-v2/human-review.json)、[U/D原话](benchmarks/left-bu-joint-work-v3/human-review.json)继续生效。AI适配器核验原问题／原话／源图及源锚点，不伪造当前几何曾获人审。旧送审请求和answer=null历史包不回写。
- README/site/gh-pages保持。main原起点66a450a；2026-10-29至10-30本地修改尚未提交/推送。skill仍LIMITED_TRIAL_V2；geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。

## 唯一待裁决与下一步

[F1原始请求](benchmarks/left-bu-north-reviewed-v4/F1-review-request.json)：**M1上方横条下突台阶的橙框F1是否为V1，并接M2蓝框W1的竖向段？** W1是已审A左侧另一条较窄M2；本次不判孔数，也不判W1与M3的连接。

- F1原生M1搜索框[1495,1882,1548,1940]；W1原生M2上下文[1478,1898,1535,2320]，向下继续。两层各用原生坐标，未做不合格的像素投影；蓝框是搜索范围，不是精密金属边界。
- F1只作来源候选，未建孔／接口，身份和承载待人审；M2自身上端亮点不能反充V1证据。不问N/Q1/U/D，不逐孔审批。
- 裁决后再建立来源绑定的整组候选孔并查包围，继而沿W1及上方横条向左接续。不能把当前视图边界当作物理终点。
- 附近细竖向M1起点与横条之间可见间隙，暂不桥接；不据局部留隙推导全局异网，内部细指和其它VIA未穷尽。

## 本轮接续、来源与验证

- [两步事务](benchmarks/left-bu-north-reviewed-v4/transaction-log.json)：S1只加N完整候选阵列及已审承载；S2只在C-M1-SPINE追加六块上方支路，不改旧骨架/源锚点/旧块/接口。中断前未完成的生成已恢复，不重做上一轮全幅。
- 右支沿器件外围返回同一宽M1；左支经短台阶接上横条并向左继续。六块是AI原生连续性观察绑定的规则候选，不是人审全网；[来源](benchmarks/left-bu-north-reviewed-v4/upper-branch-source-observations.json)与[局部块台账](benchmarks/left-bu-north-reviewed-v4/upper-branch-local-part-ledger.json)保留原生路径和范围。
- 15组完整设计阵列的逐孔包围／间距通过；物理计数、来源精密几何、工艺尺度和PDK DRC仍未知。F1不计入15组，未把普通层间交叉变为连接。
- 本轮无程序修改；28项来源适配器／接口接续相关测试通过，两个事务及当前恢复精确重放；原80孔中心、14条旧人审、原图和展示哈希保持。原生裁片、静态资源、脚本、SVG/PNG检查见验证；浏览器交互未实测。此前162项测试是上一程序变更阶段记录，未重复冒充本轮结果。
- 继承的“N待审”等限制句保留为历史，并追加本轮N已审事实；实时状态以本入口和当前15条已审模型为准。无借此删除未解决疑点。
- [本轮前入口全文](docs/history/current-task-before-2026-10-30-north-reviewed-v4.md)完整归档。以下旧裁决和未知继续有效；旧11/14接口数字各属于相应历史阶段。

## 必须接续的裁决与未知

- P1 上接 BU，P2/P3 的 L1/L2 本处不接 BR-R，P4/P5 接 R3/R4。只判局部，不推导异网。BF24/BF26 本处上接 BU；BF25 本处不接 BU/L1/L2，仍独立候选而非已确定悬空节点。BF24/26 下端、其余 23 指和细邻线仍未知。
- A/B 的 V1 身份及接 RT-M2-R01 已审；原生框 A=[3125,1930,3175,2010]、B=[3130,2775,3180,2845]，2×1 仍为设计假设。R02 其它 V1 未查清，不声明无孔。
- 原 9 个 V2：R01/R02 上端接 RT-M3-UP、下端接 RT-M3-DOWN；N1→C-M3-L01、03→T01、04→T02、05→E1、06→E2。05/06 本处 M2 不连续，不推导全局异网。08 无明确 V2、三条弱 M3 不补建是 AI 处置，非人审不存在。
- C06 原生框 [2933,2140,2977,2175] 跨旧走廊 x2940；保持原框／裁决。旧 M2/V2/M3 覆盖仅限旧声明范围，不升级五层穷尽覆盖。
- BR-R work-v3：S1 只下扩 200px，S2 只加原 M1 的 BRR-DOWN/R3/R4 局部块，S3 另加 L1/L2；原骨架／宽度／四块及旧对象、11 接口、46 孔保持。详见[前入口全文](docs/history/current-task-before-2026-10-29-R3-R4-left.md)。
- A 右支约原生 x5175 下拐；B 左支与 R3/R4 左端原先均为出界而非物理终点。旧骨架 B 近似 y2800 与横带约 y2780 的差别不能用于移动孔；BF25、细邻条与完整返回仍未知。
- 外方阵宏观搜索不等于内部 VIA 精度；ORB 保留点 P95 约129px及首版触带已拒绝。旧九对 V1/V2 同孔拟合和 4.52px 残差不可复活；V1 从 M1 侧、V2 从 M2 侧判断。
- 其它区域 A={T3,L2}/B={T1,L4}、H1/H2 局部隔离、U1/U2 同 M1、U1/U3 经 V1 接 N2、U3 CT→AA 环端子路径按历史保持，不转移到本走廊。
- [材料快照 v5](configs/joint-work-layer-v5.json)为 AA334/POLY696/CT10287；规范导体注册表仍[原33记录](docs/assets/conductive-stack-v2/model.json)。AA-F01951/1952、材料 H1/H2、边界 AA-F01744、S3-AA4-LEFT-SD-ACCESS 六处材料未知保持。物理工艺／尺度／孔数／极性／WL／阻值未知，自动网络导出禁止。

## 恢复

```bash
# 当前唯一几何入口；输出须为新目录。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/left-bu-north-reviewed-v4/next-request.json --output runs/新的上方M1接续目录
# 仍只检查旧声明范围，不能作为本轮左扩五层覆盖率
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的旧范围覆盖核对
```

其它V1从benchmarks/v1-new-short-branch-reviewed-v2/next-request.json恢复，旧中样从benchmarks/m1-local-tab-v1/work-next.json恢复，不能替代本走廊入口。历史初稿在runs/B-short-finger-initial-review-build-v2及runs/corridor-m1-v1-pre-resource-reuse-v2保留。不得自动重建README/site或发布gh-pages。
