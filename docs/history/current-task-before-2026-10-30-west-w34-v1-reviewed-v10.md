# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-30 before W3/W4 V1 integration and continuous M1 coverage gap phase.

# 当前任务

## 当前目标与状态

**W3-U/D、W4-U/D四处均为V2，分别接B-U / RT-M3-UP、B-D / RT-M3-DOWN，已接入联合工作几何。下一批只裁决W3/W4对应的四处M1/V1，不重问旧V2。**

- [当前复核入口](docs/assets/west-w34-reviewed-v9/index.html) · [五层切换/原图](docs/assets/west-w34-reviewed-v9/S4-W34-V2/index.html) · [规则几何](docs/assets/west-w34-reviewed-v9/joint-work.png)。
- 唯一几何恢复：[next-request](benchmarks/west-w34-reviewed-v9/next-request.json)；[状态](benchmarks/west-w34-reviewed-v9/source-review-state.json)、[报告](docs/reviews/2026-10-30-west-w34-reviewed-v9.md)、[验证](benchmarks/west-w34-reviewed-v9/verification.json)。
- 当前39金属候选（M1=4/M2=13/M3=22），26已审局部接口（V1=7组/V2=19组），165显式设计候选孔。旧22人审、133孔边界与中心保持；两条M3各追加一个西侧来源块，旧骨架/宽度/源锚点/原块不变。
- 视口仅左扩750为[-2700,0,780,1440]，原点/尺度不变。新增W3/W4各以上3×2、下5×2完整阵列作AI候选，物理孔数/尺寸/精密源落点未批准。[本轮人审原话](benchmarks/west-w34-reviewed-v9/human-review.json)：“W3-U、W3-D 均正确”“W4-U、W4-D 均正确”。
- 旧[W2 V1](benchmarks/west-w2-v1-reviewed-v8/human-review.json)、[W2 V2](benchmarks/west-w2-reviewed-v7/human-review.json)、[W1两端](benchmarks/west-w1-ends-reviewed-v6/human-review.json)、[F1](benchmarks/west-w1-reviewed-v5/human-review.json)、[N](benchmarks/left-bu-north-reviewed-v4/human-review.json)、[Q1](benchmarks/left-bu-v1-reviewed-v2/human-review.json)、[A的U/D](benchmarks/left-bu-joint-work-v3/human-review.json)继续生效；旧送审answer=null保持，不回写历史。
- README/site/gh-pages保持，10月29–30日本地修改未提交/推送。skill仍LIMITED_TRIAL_V2；geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。

## 唯一当前裁决批次与下一步

[M1来源观察](benchmarks/west-w34-reviewed-v9/W34-M1-source-observations.json) · [四接口裁决请求](benchmarks/west-w34-reviewed-v9/W34-V1-review-request.json)。下列仅为来源候选，尚未加新M1几何或V1工作接口。

- **W3-N**：M1上横条台阶[728,1905,775,1955]是否含V1并接W3？[两层大图](docs/assets/west-w34-reviewed-v9/W3-N-paired.png)。
- **W3-S**：M1下宽横条[755,2708,810,2756]是否含V1并接W3？[两层大图](docs/assets/west-w34-reviewed-v9/W3-S-paired.png)。
- **W4-N**：M1上横条下方[360,1908,410,1975]是否含V1并接W4？[两层大图](docs/assets/west-w34-reviewed-v9/W4-N-paired.png)。特别区分孔组和细竖向M1起点/拍屏纹理，不照搬W3台阶解释。
- **W4-S**：M1下宽横条[385,2710,445,2764]是否含V1并接W4？[两层大图](docs/assets/west-w34-reviewed-v9/W4-S-paired.png)。
- 只判新身份/承载，不要求孔数；V1从M1源图判断，已审M2上V2不反充V1证据。各层原生坐标独立、未投影，搜索框不是精密金属边界。
- 上下M1横条同帧续接已建C-M1-SPINE西侧横条，但本处V1连接仍待裁决。不得因细线邻近/普通交叉自动补连接、判物理无孔或全局异网。裁决后再追加来源块/台阶/整组孔并查包围。

## 本轮接续与验证

- [四事务](benchmarks/west-w34-reviewed-v9/transaction-log.json)：S1只左扩视口；S2只追加两条M3母线来源延续；S3新增W3/W4与清单；S4只加四处已审V2及完整候选阵列。无程序修改，不重跑已审全幅。
- 26组完整设计阵列的包围/间距通过；旧22裁决、133孔边界/中心保持，旧金属骨架/宽度/源锚点/原局部块保持。四事务和当前恢复精确回放，旧M3几何被追加后几何包含。
- 58项视口、来源块、金属/接口扩展与原生裁决适配器测试通过；来源哈希、原图裁片逐像素、静态资源/脚本/SVG/PNG核验见verification。浏览器交互未实测；物理孔数/精密源几何/工艺尺度/真实PDK DRC/所有可见接口覆盖仍未知。
- README/site的25文件及gh-pages引用保持。[前入口全文](docs/history/current-task-before-2026-10-30-west-w34-reviewed-v9.md)完整归档；历史pending句不改写，当前以26已审工作接口和本批W3/W4新V1为准。

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
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/west-w34-reviewed-v9/next-request.json --output runs/新的W3W4接续目录
# 仅旧声明范围，不作为左扩五层全覆盖率。
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的旧范围覆盖核对
```

其它V1从benchmarks/v1-new-short-branch-reviewed-v2/next-request.json恢复，旧中样从benchmarks/m1-local-tab-v1/work-next.json恢复，均不替代本走廊入口。历史失败初稿保留于runs/；不得自动重建README/site或发布gh-pages。
