# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-30 before fixed-scope M1 coverage repair and final source review.

# 当前任务

## 当前目标与状态

**W3-N/S、W4-N/S四处均为V1并接对应W3/W4，已接入联合工作几何。本批8处V1/V2已审接口全部接续；当前无未落实的本批人工裁决。下一步按固定M1连续范围清单补几何，不再扩展零散接口。**

- [当前复核入口](docs/assets/west-w34-v1-reviewed-v10/index.html) · [五层切换/原图](docs/assets/west-w34-v1-reviewed-v10/S2-W34-V1/index.html) · [规则几何](docs/assets/west-w34-v1-reviewed-v10/joint-work.png) · 同页支持同坐标前后设计切换。
- 唯一几何恢复：[next-request](benchmarks/west-w34-v1-reviewed-v10/next-request.json)；[状态](benchmarks/west-w34-v1-reviewed-v10/source-review-state.json)、[报告](docs/reviews/2026-10-30-west-w34-v1-reviewed-v10.md)、[验证](benchmarks/west-w34-v1-reviewed-v10/verification.json)。
- 当前39金属候选（M1=4/M2=13/M3=22），30已审局部接口（V1=11组/V2=19组），179显式设计候选孔。旧26裁决、165孔边界/中心保持；只C-M1-SPINE追加4个来源块，旧骨架/宽度/源锚点/原块保持，其余38金属不变。视口[-2700,0,780,1440]、原点/尺度不变。
- [人审原话](benchmarks/west-w34-v1-reviewed-v10/human-review.json)：“W3-N、W3-S 均为 V1，接 W3”“W4-N、W4-S 均为 V1，接 W4”。W4-N按窄承载用2×1，另三组2×2，均为AI完整候选；物理孔数/尺寸/精密源落点未批准，不强制V1/V2逐孔重合。
- 旧[W3/W4 V2](benchmarks/west-w34-reviewed-v9/human-review.json)、[W2 V1](benchmarks/west-w2-v1-reviewed-v8/human-review.json)、[W2 V2](benchmarks/west-w2-reviewed-v7/human-review.json)、[W1](benchmarks/west-w1-ends-reviewed-v6/human-review.json)、[F1](benchmarks/west-w1-reviewed-v5/human-review.json)、[N](benchmarks/left-bu-north-reviewed-v4/human-review.json)、[Q1](benchmarks/left-bu-v1-reviewed-v2/human-review.json)、[A的U/D](benchmarks/left-bu-joint-work-v3/human-review.json)继续生效。旧送审answer=null保持，不回写原证据。
- README/site/gh-pages保持；10月29–30日本地修改未提交/推送。skill仍LIMITED_TRIAL_V2；geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。

## 唯一下一步：固定M1范围补齐覆盖缺口

[来源→几何→接口清单](benchmarks/west-w34-v1-reviewed-v10/scoped-M1-coverage.json) · [CSV](benchmarks/west-w34-v1-reviewed-v10/scoped-M1-coverage.csv) · [缺口接续计划](benchmarks/west-w34-v1-reviewed-v10/next-gap-plan.json) · [连续原图](docs/assets/west-w34-v1-reviewed-v10/M1-band-marked.png) · [中段放大](docs/assets/west-w34-v1-reviewed-v10/M1-middle-marked.png)。

- 固定M1原生范围[300,1870,830,2820]，AI列10个可见片段：L01/L02上下主干已建；L03 W4北竖支只建承载片段；L04–L10七个片段未建/归属未知。**COVERAGE_INCOMPLETE**；10条是声明片段清单，不是照片穷尽证明。
- 顺序：补L03余段；独立建立L07/L08中部两横条；核L04/L05/L06细竖支的端部间隙和归属；分开保留L09/L10底部左右片段。新片段不得按同高/邻近合并，不凭相似度指派给旧L1/L2。
- 新几何仍逐事务列变化ID、来源/父包，旧179孔和30条批准保持；新身份/连接歧义出现时才请求人工裁决，不重审W3/W4已审8接口。
- 本批主干接口已接续不代表所有细支路、全部M2/M3导体或全网覆盖。更高金属、真实PDK尺度/DRC未知；禁止自动网表导出。

## 本轮接续、skill与验证

- 按[金属重建skill](skills/silicon-eye-metal-reconstruction/SKILL.md)、[VIA重建skill](skills/silicon-eye-via-reconstruction/SKILL.md)的限定试用规则执行。[两事务](benchmarks/west-w34-v1-reviewed-v10/transaction-log.json)：S1只补上下M1横条/W3台阶/W4窄承载；S2只加四处已审V1及完整候选阵列。无程序修改、不重跑已审全幅。
- 30组完整设计候选包围/间距通过；旧26裁决、165孔边界/中心保持。两事务与当前恢复精确回放。M1原几何被追加后几何包含，其他38金属精确相同。
- 38项来源块/接口扩展/原生裁决适配器测试通过；[固定工程回归](benchmarks/west-w34-v1-reviewed-v10/fixed-regression.json)另31项测试通过、历史样本精确回放。工程回归不是新AI识图评测，未测新准确率；浏览器交互未实测。
- 原图裁片逐像素、来源/静态资源/脚本/SVG/PNG与同坐标前后图检查见verification；来源阵列精密几何未验收，物理数量未知。来源覆盖门仍不完整，不用程序PASS覆盖这一缺口。
- README/site的25文件和gh-pages引用保持。[前入口全文](docs/history/current-task-before-2026-10-30-west-w34-v1-reviewed-v10.md)完整归档；旧pending句是历史阶段，实时入口以30条已审接口和本轮固定覆盖缺口为准。

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
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/west-w34-v1-reviewed-v10/next-request.json --output runs/新的W3W4V1接续目录
# 固定工程回归，不能当新AI识图评测。
.venv/bin/python scripts/check_conductive_regression.py --output runs/新的固定回归/result.json
```

旧声明范围核对仍使用benchmarks/conductive-corridor-closeout-v2/request.json，不扩为左侧五层覆盖率。其它V1/旧中样入口不替代本走廊。历史失败初稿保留于runs/；不得自动重建README/site或发布gh-pages。
