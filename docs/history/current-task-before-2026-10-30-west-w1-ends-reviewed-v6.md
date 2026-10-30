# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-30 before W1 end review integration and W2 source-only gate.

# 当前任务

## 当前目标与状态

**F1 已确认是 V1、接 M2 W1，并已进入工作几何；W1 已核查到可见下端，两端 U1／D1 的 V2 身份及 M3 承载待集中裁决。** 不再问 F1/N/Q1/U/D。新 U1/D1 尚未加入工作接口，不按已接通扩网。

- [当前复核入口](docs/assets/west-w1-reviewed-v5/index.html) · [五层切换/原图](docs/assets/west-w1-reviewed-v5/S4-F1-interface/index.html) · [规则几何](docs/assets/west-w1-reviewed-v5/joint-work.png) · [W1-U1原图](docs/assets/west-w1-reviewed-v5/W1-U-paired.png) · [W1-D1原图](docs/assets/west-w1-reviewed-v5/W1-D-paired.png)。
- 唯一几何恢复：[next-request](benchmarks/west-w1-reviewed-v5/next-request.json)；[状态](benchmarks/west-w1-reviewed-v5/source-review-state.json)、[报告](docs/reviews/2026-10-30-west-w1-reviewed-v5.md)、[验证](benchmarks/west-w1-reviewed-v5/verification.json)。
- 当前36金属候选（M1=4/M2=10/M3=22），16已审局部接口（V1=5组/V2=11组），93显式设计候选孔。原15接口、89孔中心及原骨架/源锚点/旧局部块保持；设计视口[-1500,0,780,1440]、原点[0,0]不变。
- [F1原人审](benchmarks/west-w1-reviewed-v5/human-review.json)原话“F1：是 V1，接 W1”。新2×2是AI完整阵列候选，实际孔数/尺寸未批准；M1台阶相对尺寸也仍是候选。W1源锚点仍[1502,1920]→[1515,2320]，下方可见部分通过独立局部块续接，不改原锚点。
- [N原话](benchmarks/left-bu-north-reviewed-v4/human-review.json)、[Q1原话](benchmarks/left-bu-v1-reviewed-v2/human-review.json)、[U/D原话](benchmarks/left-bu-joint-work-v3/human-review.json)继续生效。AI适配器只迁移绑定的源身份/承载；原送审请求与answer=null历史包不回写，几何与数量不随之获审。
- README/site/gh-pages保持。main原起点66a450a；10月29–30日本地修改未提交/推送。skill仍LIMITED_TRIAL_V2；geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。

## 唯一当前裁决批次与下一步

[W1两端请求](benchmarks/west-w1-reviewed-v5/W1-V2-review-request.json)：

- **W1-U1／W1-V2-U**：M2上端孔组[1480,1900,1528,1965]是否为V2，并接紫色B-U／RT-M3-UP宽母线？
- **W1-D1／W1-V2-D**：M2下端孔组[1500,2705,1545,2805]是否为V2，并接粉色B-D／RT-M3-DOWN宽母线？
- 只判这两处新身份与承载，物理孔数未知；不是已审A的U/D，不重问F1/N/Q1和旧接口。M3自身的孔不能反充V2证据。
- 两层各用原生坐标；框是搜索范围，不是精密金属边界，未声称投影或精密包围通过。U1/D1尚未作为接口/孔加入工作层。
- 裁决后再补来源绑定的完整候选孔组及联合包围，沿B-U/B-D的接入分支继续。W1中部普通M3交叉不自动连接；右侧从约y2400开始的另一条M2不直接并入W1。

## 本轮接续、来源与验证

- [四步事务](benchmarks/west-w1-reviewed-v5/transaction-log.json)：S1只补F1的M1下突台阶；S2加W1及来源清单；S3只给W1续下端来源局部块；S4只加F1完整候选孔和已审承载。不另起模型、不重跑已审全幅。
- W1在原生M2上连续到下端孔组；其右邻中部起始的M2与它有可见间隙，局部留隙不推导全局异网。[来源清单](benchmarks/west-w1-reviewed-v5/W1-source-continuation.json)保留完整可见路径、邻线、中部交叉未知与M3候选承载；[台账](benchmarks/west-w1-reviewed-v5/W1-full-source-ledger.json)逐块绑定来源。
- 16组完整设计阵列的逐孔包围/间距通过；W1的U1/D1不计入其中。实际数量、来源精密几何、工艺尺度与PDK DRC未知；source_to_design_transform=null。
- 本轮无程序修改，39项金属/接口扩展与来源适配器测试通过；四事务和当前恢复精确回放，原89中心、15旧人审保持。原图裁片/静态资源/脚本/SVG与PNG检查见验证，浏览器交互未实测。此前162项属于上一程序修改阶段，不重复算作本轮测试。
- 继承的“F1待审”等限制句保留为历史，追加本轮已审事实；实时状态以本入口和16条已审工作接口为准，未通过清理文本消除未知。
- [前入口全文](docs/history/current-task-before-2026-10-30-west-w1-reviewed-v5.md)完整归档；以下旧裁决与未知仍有效，旧11/14/15接口数各属相应历史阶段。

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
# 当前唯一几何恢复入口，输出用新目录。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/west-w1-reviewed-v5/next-request.json --output runs/新的W1接续目录
# 仍仅旧声明范围，不作为左扩五层全覆盖率
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的旧范围覆盖核对
```

其它V1从benchmarks/v1-new-short-branch-reviewed-v2/next-request.json恢复，旧中样从benchmarks/m1-local-tab-v1/work-next.json恢复，均不替代本走廊入口。历史初稿在runs/B-short-finger-initial-review-build-v2及runs/corridor-m1-v1-pre-resource-reuse-v2保留。不得自动重建README/site或发布gh-pages。
