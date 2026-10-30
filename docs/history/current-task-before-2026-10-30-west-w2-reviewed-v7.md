# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-30 before W2 V2 integration and new M1 V1 questions.

# 当前任务

## 当前目标与状态

**W1-U1、W1-D1 已裁决正确：均为 V2，分别接 B-U / RT-M3-UP、B-D / RT-M3-DOWN；已接入联合工作几何。下一处新裁决为西侧另一条长 M2（W2）的上下端。** 不重问 W1/F1/N/Q1 或 A 的旧 U/D。

- [当前复核入口](docs/assets/west-w1-ends-reviewed-v6/index.html) · [五层切换/原图](docs/assets/west-w1-ends-reviewed-v6/S1-W1-ends/index.html) · [规则几何](docs/assets/west-w1-ends-reviewed-v6/joint-work.png)。
- 唯一几何恢复：[next-request](benchmarks/west-w1-ends-reviewed-v6/next-request.json)；[状态](benchmarks/west-w1-ends-reviewed-v6/source-review-state.json)、[报告](docs/reviews/2026-10-30-west-w1-ends-reviewed-v6.md)、[验证](benchmarks/west-w1-ends-reviewed-v6/verification.json)。
- 当前36金属候选（M1=4/M2=10/M3=22），18已审局部接口（V1=5组/V2=13组），109显式设计候选孔。旧36金属、16人审、93孔边界与中心保持。视口[-1500,0,780,1440]、原点[0,0]不变；W2尚未入工作层。
- [本轮人审原话](benchmarks/west-w1-ends-reviewed-v6/human-review.json)：“W1-U1、W1-D1 均正确”。上端3×2、下端5×2为AI完整阵列候选；身份/承载批准不覆盖孔数、尺寸、精密落点或真实PDK DRC。
- [F1原人审](benchmarks/west-w1-reviewed-v5/human-review.json)、[N原话](benchmarks/left-bu-north-reviewed-v4/human-review.json)、[Q1原话](benchmarks/left-bu-v1-reviewed-v2/human-review.json)、[A的U/D原话](benchmarks/left-bu-joint-work-v3/human-review.json)继续生效。旧送审answer=null包保留；不回写原请求或把新几何冒充原已审图。
- README/site/gh-pages保持；10月29–30日本地修改未提交/推送。skill仍LIMITED_TRIAL_V2；geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。

## 唯一当前裁决批次与下一步

沿B-U/B-D向左发现另一长M2，暂称W2；只建立来源候选，不扩工作几何或自动连网。[来源观察](benchmarks/west-w1-ends-reviewed-v6/W2-source-observations.json)、[两端裁决请求](benchmarks/west-w1-ends-reviewed-v6/W2-review-request.json)。

- **W2-U**：上端M2橙框[1070,1900,1120,1970]是否为V2并接B-U / RT-M3-UP？[M2/M3大邻域](docs/assets/west-w1-ends-reviewed-v6/W2-U-paired.png)。
- **W2-D**：下端M2橙框[1095,2700,1150,2815]是否为V2并接B-D / RT-M3-DOWN？[M2/M3大邻域](docs/assets/west-w1-ends-reviewed-v6/W2-D-paired.png)。
- 只判两处新身份与承载，不要求物理孔数。W2不是W1或A；各层原生坐标独立、未投影。搜索框不是精密金属边界，M3自身孔组不反充V2证据。
- 裁决后再按既有事务补来源绑定的W2金属/完整候选阵列与联合包围，保留全部旧孔中心；如超出视口，先单独做明确的视口扩展，不能缩放或平移旧几何。
- W1中部M3交叉和右侧中部起始的另一个M2不自动连接；尚未宣称母线所有分支、五层或全网完整。

## 本轮接续与验证

- 一个新增接口事务，仅加W1两端完整候选阵列及原生来源/人审绑定；无程序修改，无金属重算/移动，无照片改写。[事务](benchmarks/west-w1-ends-reviewed-v6/transaction-log.json)。
- 18组完整设计候选阵列的包围/间距通过；旧36金属、16条人审、93孔边界与中心逐项相等。当前恢复精确回放。物理数量、来源精密几何、工艺尺度仍未知。
- 28项接口扩展/来源适配器测试通过；来源哈希、原图裁片逐像素、静态资源、脚本语法、SVG和PNG核验见verification。浏览器交互未实测；不重复算此前阶段测试。
- README/site的25文件与gh-pages引用核对保持。[前入口全文](docs/history/current-task-before-2026-10-30-west-w1-ends-reviewed-v6.md)完整归档；历史pending措辞是旧阶段记录，当前以18条工作人审和W2唯一新裁决批次为准。

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
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/west-w1-ends-reviewed-v6/next-request.json --output runs/新的W1两端接续目录
# 仅旧声明范围，不作为左扩五层全覆盖率。
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的旧范围覆盖核对
```

其它V1从benchmarks/v1-new-short-branch-reviewed-v2/next-request.json恢复，旧中样从benchmarks/m1-local-tab-v1/work-next.json恢复，均不替代本走廊入口。历史失败初稿保留于runs/；不得自动重建README/site或发布gh-pages。
