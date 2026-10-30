# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-30 before recording Q1/Q2 scoped M1 visual acceptance.

# 当前任务

## 当前目标与状态

**固定M1范围几何已补齐：原1个部分片段、7个未建片段，以及独立复查发现的L11/L12两处漏项均有对应几何。声明清单12/12工程对应通过，等待Q1/Q2两组视觉覆盖验收。旧30条接口裁决不重审。**

- [当前集中验收页](docs/assets/west-m1-coverage-v11/index.html) · [五层切换/原图](docs/assets/west-m1-coverage-v11/S3-L09-return/index.html) · [联合图](docs/assets/west-m1-coverage-v11/joint-work.png) · [完整局部规则图](docs/assets/west-m1-coverage-v11/local-full-after.png)。同页支持同坐标前后设计及原图切换。
- 唯一几何恢复：[next-request](benchmarks/west-m1-coverage-v11/next-request.json)；[状态](benchmarks/west-m1-coverage-v11/source-review-state.json)、[报告](docs/reviews/2026-10-30-west-m1-coverage-v11.md)、[验证](benchmarks/west-m1-coverage-v11/verification.json)。
- 当前46金属候选（M1=11/M2=13/M3=22），30已审局部接口，179设计候选孔。只原C-M1-SPINE加2个来源块，新增7个独立M1 ID，并给新L09补1个来源回折块；旧骨架/宽度/源锚点/原块、30人审及179孔边界/中心保持，其余38个旧金属不变。视口[-2700,0,780,1440]、原点/尺度不变。
- [修正后的覆盖清单](benchmarks/west-m1-coverage-v11/scoped-M1-coverage.json) · [CSV](benchmarks/west-m1-coverage-v11/scoped-M1-coverage.csv) · [独立来源复查](benchmarks/west-m1-coverage-v11/source-rescan.json)。固定原生范围仍[300,1870,830,2820]，没有扩大统计范围；L11主干向下出口、L12左段末端回折是旧10片段清单漏项，旧清单完整保留。
- 旧[W3/W4 V1](benchmarks/west-w34-v1-reviewed-v10/human-review.json)、[W3/W4 V2](benchmarks/west-w34-reviewed-v9/human-review.json)、[W2 V1](benchmarks/west-w2-v1-reviewed-v8/human-review.json)、[W2 V2](benchmarks/west-w2-reviewed-v7/human-review.json)、[W1](benchmarks/west-w1-ends-reviewed-v6/human-review.json)、[F1](benchmarks/west-w1-reviewed-v5/human-review.json)、[N](benchmarks/left-bu-north-reviewed-v4/human-review.json)、[Q1](benchmarks/left-bu-v1-reviewed-v2/human-review.json)、[A的U/D](benchmarks/left-bu-joint-work-v3/human-review.json)继续生效。无新VIA/人审/网边，未合并电气ID。
- README/site/gh-pages保持；10月29–30日本地修改未提交/推送。skill仍LIMITED_TRIAL_V2；geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。

## 唯一下一步：Q1/Q2固定范围几何验收

[验收请求](benchmarks/west-m1-coverage-v11/coverage-review-request.json)，只验新几何及本范围可见覆盖，不重判旧VIA、孔数或全局网络。

- **Q1：L03–L08** 竖支/细邻线/中部两横条：位置、长度、上下次序、端部留隙及可见覆盖是否合理？[原图大邻域](docs/assets/west-m1-coverage-v11/source-middle-marked.png) · [规则图](docs/assets/west-m1-coverage-v11/local-middle-after.png) · [完整局部图](docs/assets/west-m1-coverage-v11/local-full-after.png)。
- **Q2：L09–L12** 底部左右片段分开，L11主干向下出口、L12左段回折是否合理且无明显遗漏？[原图大邻域](docs/assets/west-m1-coverage-v11/source-bottom-marked.png) · [规则图](docs/assets/west-m1-coverage-v11/local-bottom-after.png)。原图橙线为y2820统计边界，出界不是物理终点。
- 原图与设计分别保留独立坐标，不直接投影。12/12是声明清单工程对应；视觉来源验收仍PENDING_HUMAN，物理照片穷尽性未知，不写全画幅或全网完成。
- 通过后收口本固定M1范围候选，再选择M2/M3连续范围覆盖；若有修改，只修列明片段，不移动旧179孔，不重审已审接口。

## 本轮接续、skill与验证

- 依[金属skill](skills/silicon-eye-metal-reconstruction/SKILL.md)及[VIA skill](skills/silicon-eye-via-reconstruction/SKILL.md)限定规则，[三事务](benchmarks/west-m1-coverage-v11/transaction-log.json)：S1补旧主干延续；S2新增7段独立M1；S3给新L09补短回折。无程序修改、不重跑已审全幅。
- 30组完整候选孔包围、金属正交/宽度/间距通过；[6项同帧来源次序](benchmarks/west-m1-coverage-v11/scoped-source-order.json)、[10项局部留隙](benchmarks/west-m1-coverage-v11/gap-checks.json)通过。L09/L10不桥接，L07/L08不指派给旧L1/L2；局部留隙不证明全局异网。
- 三事务/当前恢复精确回放，旧30人审、179孔和旧金属原始信息保持。49项相关测试通过；[固定工程回归](benchmarks/west-m1-coverage-v11/fixed-regression.json)另31项通过、历史样本精确回放。不是AI重新识图准确率评测。
- 原图裁片逐像素、来源/资源/脚本/SVG/PNG、同坐标前后图检查见verification；浏览器交互未实测，物理数量/源精密几何/工艺尺度/真实PDK DRC未知，全部M2/M3细支路及高层金属未覆盖。
- README/site的25文件及gh-pages引用保持。[前入口全文](docs/history/current-task-before-2026-10-30-west-m1-coverage-v11.md)完整归档；旧pending句保留为历史阶段，实时状态以本入口为准。

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
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/west-m1-coverage-v11/next-request.json --output runs/新的固定M1接续目录
# 固定工程回归，不能当新AI识图评测。
.venv/bin/python scripts/check_conductive_regression.py --output runs/新的固定回归/result.json
```

旧声明范围核对入口不扩为本侧五层覆盖率；其它V1/旧中样入口不替代本走廊。历史失败初稿保留于runs/；不得自动重建README/site或发布gh-pages。
