# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-30 before W3/W4 V2 integration and M1/V1 batch.

# 当前任务

## 当前目标与状态

**W2-N、W2-S均为V1且接W2，已接续M1横条/台阶及完整候选孔组；W2已有上下V1、上下V2四处已审接口。下一批集中裁决更西侧W3/W4的四处V2，不重问旧接口。**

- [当前复核入口](docs/assets/west-w2-v1-reviewed-v8/index.html) · [五层切换/原图](docs/assets/west-w2-v1-reviewed-v8/S2-W2-V1/index.html) · [规则几何](docs/assets/west-w2-v1-reviewed-v8/joint-work.png)。
- 唯一几何恢复：[next-request](benchmarks/west-w2-v1-reviewed-v8/next-request.json)；[状态](benchmarks/west-w2-v1-reviewed-v8/source-review-state.json)、[报告](docs/reviews/2026-10-30-west-w2-v1-reviewed-v8.md)、[验证](benchmarks/west-w2-v1-reviewed-v8/verification.json)。
- 当前37金属候选（M1=4/M2=11/M3=22），22已审局部接口（V1=7组/V2=15组），133显式设计候选孔。旧20人审、125孔边界与中心保持；仅C-M1-SPINE追加3个来源块，旧骨架/宽度/源锚点/原块不改。视口[-1950,0,780,1440]、原点/尺度不变。
- [本轮人审原话](benchmarks/west-w2-v1-reviewed-v8/human-review.json)：“W2-N：是 V1，接 W2”“W2-S：是 V1，接 W2”。两组2×2为AI完整设计候选，物理孔数/尺寸/精密源落点未批准；W2的上下V1/V2未被强制逐孔重合。
- 旧[W2 V2](benchmarks/west-w2-reviewed-v7/human-review.json)、[W1两端](benchmarks/west-w1-ends-reviewed-v6/human-review.json)、[F1](benchmarks/west-w1-reviewed-v5/human-review.json)、[N](benchmarks/left-bu-north-reviewed-v4/human-review.json)、[Q1](benchmarks/left-bu-v1-reviewed-v2/human-review.json)、[A的U/D](benchmarks/left-bu-joint-work-v3/human-review.json)继续生效。旧送审answer=null保留，原生人审与AI几何资格分开。
- README/site/gh-pages保持；10月29–30日本地修改未提交/推送。skill仍LIMITED_TRIAL_V2；geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。

## 唯一当前裁决批次与下一步

[西侧来源观察](benchmarks/west-w2-v1-reviewed-v8/west-branch-source-observations.json) · [四接口裁决请求](benchmarks/west-w2-v1-reviewed-v8/west-branch-review-request.json)。从右至左为已审W2、新W3、新W4；W3/W4尚未入工作几何。

- **W3-U**：M2孔组[702,1900,750,1970]是否V2并接B-U / RT-M3-UP？[两层图](docs/assets/west-w2-v1-reviewed-v8/W3-U-paired.png)。
- **W3-D**：M2孔组[730,2705,782,2820]是否V2并接B-D / RT-M3-DOWN？[两层图](docs/assets/west-w2-v1-reviewed-v8/W3-D-paired.png)。
- **W4-U**：M2孔组[337,1900,391,1975]是否V2并接B-U / RT-M3-UP？[两层图](docs/assets/west-w2-v1-reviewed-v8/W4-U-paired.png)。
- **W4-D**：M2孔组[372,2700,428,2825]是否V2并接B-D / RT-M3-DOWN？[两层图](docs/assets/west-w2-v1-reviewed-v8/W4-D-paired.png)。
- 四处仅判身份和承载，不要求孔数；相似阵列不能代替新物理连接证据。各层原生坐标独立、未投影，M3自身孔不反充V2证据。不重问W2/W1/F1等旧裁决。
- 裁决后再分事务补来源绑定的金属延续、必要视口和完整候选孔组，保留旧坐标/裁决并查联合包围；W3/W4的M1/V1尚未核清。

## 本轮接续与验证

- [两事务](benchmarks/west-w2-v1-reviewed-v8/transaction-log.json)：S1仅给原C-M1-SPINE追加北横条/下突台阶/南横条；S2只加两处已审V1与完整候选阵列。无程序修改、不重跑已审全幅。
- 22组完整设计阵列的包围/间距通过，旧20裁决与125孔边界/中心保持；两事务和当前恢复精确回放。M1原几何被追加后几何包含，其他36金属不变。
- [W2限定来源核查](benchmarks/west-w2-v1-reviewed-v8/W2-scoped-interface-audit.json)列出4处已审接口；中段细横线未辨出另一独立V1，邻近细竖M1未桥接。AI检查范围不是物理无孔、原生照片穷尽、全可见导体或全网覆盖证明。
- 38项来源局部块、接口扩展、原生裁决适配器测试通过；原图裁片逐像素、来源哈希、静态资源/脚本/SVG/PNG检查见verification。浏览器交互未实测；物理孔数/源精密几何/工艺尺度/真实PDK DRC未知。
- README/site的25文件及gh-pages引用保持。[前入口全文](docs/history/current-task-before-2026-10-30-west-w2-v1-reviewed-v8.md)完整归档；旧pending句属相应历史阶段，当前以22已审接口和本批W3/W4新V2为准。

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
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/west-w2-v1-reviewed-v8/next-request.json --output runs/新的W2V1接续目录
# 仅旧声明范围，不作为左扩五层全覆盖率。
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的旧范围覆盖核对
```

其它V1从benchmarks/v1-new-short-branch-reviewed-v2/next-request.json恢复，旧中样从benchmarks/m1-local-tab-v1/work-next.json恢复，均不替代本走廊入口。历史失败初稿保留于runs/；不得自动重建README/site或发布gh-pages。
