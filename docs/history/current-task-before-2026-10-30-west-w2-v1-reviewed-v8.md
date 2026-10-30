# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-30 before W2 V1 integration and west branch batch.

# 当前任务

## 当前目标与状态

**W2-U、W2-D均为V2，分别接B-U / RT-M3-UP、B-D / RT-M3-DOWN，已进入联合工作几何。下一批只核W2对应的M1上横条N、下宽横条S是否经V1接W2。** 不重问已审W2 V2、W1/F1/N/Q1或A旧U/D。

- [当前复核入口](docs/assets/west-w2-reviewed-v7/index.html) · [五层切换/原图](docs/assets/west-w2-reviewed-v7/S4-W2-interfaces/index.html) · [规则几何](docs/assets/west-w2-reviewed-v7/joint-work.png)。
- 唯一几何恢复：[next-request](benchmarks/west-w2-reviewed-v7/next-request.json)；[状态](benchmarks/west-w2-reviewed-v7/source-review-state.json)、[报告](docs/reviews/2026-10-30-west-w2-reviewed-v7.md)、[验证](benchmarks/west-w2-reviewed-v7/verification.json)。
- 当前37金属候选（M1=4/M2=11/M3=22），20已审局部接口（V1=5组/V2=15组），125显式设计候选孔。旧18人审、109孔边界与中心保持。仅两条旧M3追加左方来源局部块；旧骨架/源锚点/旧块不改。视口向左扩450为[-1950,0,780,1440]，原点/尺度不变。
- [人审原话](benchmarks/west-w2-reviewed-v7/human-review.json)：W2-U“是 V2，接 B-U”；W2-D“是 V2，接 B-D”。新上端3×2、下端5×2为AI完整阵列候选，物理数量/尺寸/精密源落点未批准。
- 旧[W1两端](benchmarks/west-w1-ends-reviewed-v6/human-review.json)、[F1](benchmarks/west-w1-reviewed-v5/human-review.json)、[N](benchmarks/left-bu-north-reviewed-v4/human-review.json)、[Q1](benchmarks/left-bu-v1-reviewed-v2/human-review.json)、[A的U/D](benchmarks/left-bu-joint-work-v3/human-review.json)继续生效。旧送审answer=null保留，不回写历史，不将候选几何冒充原人审图。
- README/site/gh-pages保持，10月29–30日本地修改未提交/推送。skill仍LIMITED_TRIAL_V2；geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。

## 唯一当前裁决批次与下一步

[M1来源观察](benchmarks/west-w2-reviewed-v7/W2-M1-source-observations.json) · [新V1裁决请求](benchmarks/west-w2-reviewed-v7/W2-V1-review-request.json)。

- **W2-N**：M1上方横条下突台阶[1085,1898,1138,1948]是否含V1，并接M2 W2？[M1/M2大邻域](docs/assets/west-w2-reviewed-v7/W2-N-paired.png)。这是新位置，不是A上旧N。
- **W2-S**：M1下方宽横条[1118,2688,1175,2735]是否含V1，并接M2 W2？[M1/M2大邻域](docs/assets/west-w2-reviewed-v7/W2-S-paired.png)。
- 只判新身份与承载，不要求物理孔数。两层分别保留原生坐标，未互相投影；M2自身V2孔不反充V1证据。搜索框不是精密金属边界。
- 上下横条在同帧可见地续接既有C-M1-SPINE的西侧横条；此轮只记来源路径，未加新V1或假定其连接W2。邻近细竖M1不按距离桥接，不宣称物理无孔或全局异网。
- 裁决后再追加来源绑定的M1延续/台阶与完整候选孔组，保持旧孔位置并检验上下金属整组包围；其余交叉/邻线及全网覆盖仍未知。

## 本轮接续与验证

- [四事务](benchmarks/west-w2-reviewed-v7/transaction-log.json)：S1仅左扩视口；S2仅补两条M3西侧来源块；S3新增W2及来源清单；S4新增两处已审V2与完整候选阵列。无程序修改，不重跑已审全幅。
- 当前20组完整设计候选阵列的包围/孔间距通过，旧18裁决、109孔边界与中心逐项相等，旧金属骨架/宽度/源锚点/旧局部块保持。四事务与当前恢复精确回放。
- 58项左扩视口、来源块、金属/接口扩展与原生裁决适配器测试通过；来源哈希、原图裁片逐像素、静态资源、脚本语法、SVG/PNG检查见verification。浏览器交互未实测；物理孔数、精密源几何、工艺尺度与真实PDK DRC未知。
- README/site的25文件及gh-pages引用保持。[前入口全文](docs/history/current-task-before-2026-10-30-west-w2-reviewed-v7.md)完整归档；旧pending句为相应历史阶段记录，实时状态以20已审接口和本批W2新V1为准。

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
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/west-w2-reviewed-v7/next-request.json --output runs/新的W2接续目录
# 仅旧声明范围，不作为左扩五层全覆盖率。
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的旧范围覆盖核对
```

其它V1从benchmarks/v1-new-short-branch-reviewed-v2/next-request.json恢复，旧中样从benchmarks/m1-local-tab-v1/work-next.json恢复，均不替代本走廊入口。历史失败初稿保留于runs/；不得自动重建README/site或发布gh-pages。
