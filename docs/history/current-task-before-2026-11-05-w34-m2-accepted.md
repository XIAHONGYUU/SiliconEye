<!-- 来源 CURRENT_TASK.md；2026-11-05批准接续前原文完整归档 -->

# 当前任务

## 当前目标与状态

**W3/W4 邻近 M2 的连续来源清单与四条补建候选已完成工程检查，正式固定复核页已生成，等待 G1、G2、COV 三项人工几何/覆盖判定。旧接口不重审。**

- [正式复核页](docs/assets/w34-m2-coverage-v1/review/index.html)，本机预览 http://127.0.0.1:8772/w34-m2-coverage-v1/review/index.html 。包 W34-M2-COVERAGE-20261105-V1，build 30785baea2e440169f045696a25364eb；新页初始未答，与已完成的演示包分开。
- [本轮说明](docs/reviews/2026-11-05-w34-m2-coverage.md) · [固定送审定义](benchmarks/w34-m2-coverage-v1/review-spec.json) · [工程验证](benchmarks/w34-m2-coverage-v1/verification.json)。
- M2 原生固定范围 [280,1870,850,2840]；两条既有主干 W3/W4 加四条细线 S01–S04，共六个声明片段，见[来源清单](benchmarks/w34-m2-coverage-v1/source-inventory.json)和[范围覆盖](benchmarks/w34-m2-coverage-v1/scoped-coverage.json)。6/6是清单对应，不是照片穷尽或全幅完成。
- G1：S01/S02/S03 的左/右/左回折、短端高低次序与邻线间隙。G2：S04 的右短头、与W3分开及向下出界。COV：固定红框内有无明显漏段；范围外不算完成。
- 四条新金属ID W34-M2-S01～S04均为AI候选，未获人审。三条上端及一条下端是范围出口，不是物理终点；四个短端的潜在VIA身份/承载均未查明，不声明没有孔。
- 当前候选50金属（M1=11/M2=17/M3=22）；旧46金属、30接口与179候选孔逐字段保持。没有新孔、新连接或网边，已有W3/W4八处V1/V2身份与承载不重问。

## 已审基线与候选接续

- **已审基线仍是 v12**：[M1定性收口](docs/assets/west-m1-reviewed-v12/index.html)、[准确批准片段](benchmarks/west-m1-reviewed-v12/reviewed-fragments.json)、[原人审](benchmarks/west-m1-reviewed-v12/human-review.json)。M1固定原生范围[300,1870,830,2820]本批无待审批；L03–L12获批，L01/L02只是既有上下文，不扩成整个C-M1-SPINE批准。
- [候选工作模型与五层页](docs/assets/w34-m2-coverage-v1/work/index.html) · [补建请求](benchmarks/w34-m2-coverage-v1/request.json) · [候选下一请求](benchmarks/w34-m2-coverage-v1/next-request.json)。next-request已去除补建声明，精确接续全部50对象，但不代表四个新增对象已通过人审。
- 原点/尺度/视口[-2700,0,780,1440]不变；source_to_design_transform=null、geometry_adopted=false、net_edges=[]、complete_network=false；skill仍LIMITED_TRIAL_V2。AA/POLY/CT、规范导体注册表、README/site和gh-pages未改。

## 检查结果与边界

- 75项相关测试通过；统一补建事务、正交/来源折线方向/间距和旧整组孔包围检查通过。另有7项同帧来源次序与5项局部间距检查通过；原图裁片像素精确，原生照片不变。
- 父包和全部来源/模型资源哈希已核验；候选下一请求精确重放相同模型；179个候选孔含位置/边界、30条接口及原材料快照精确保留。
- 历史固定回归报FAIL：Showcase changed: README.md。旧套件保护的10月README在此前固定确认单工具提交中已更新；本轮不覆盖旧冻结基线，也未修改README。原报告[历史回归结果](benchmarks/w34-m2-coverage-v1/historical-fixed-regression.json)保留。当前冻结的README/site共25文件保持。
- 工程通过不代表AI识图精度、真实PDK DRC或人审几何通过。固定范围内明显可见完整性仍待COV判断，四个新短端接口仍未知。

## 唯一下一步：回收本轮正式确认单

1. 用户在正式页审G1/G2/COV，填写整体Q1/Q2并确认范围边界，导出review-decision.json。可不确定；不逐孔计数。
2. Agent读取实际导出文件，运行固定review check --archive，核对build/问题范围及哈希后归档；不把演示包答案或聊天简写复制为新批准。
3. 依据实际裁决局部修订或接续；通过几何也不自动新增VIA。之后仅在这四条新细线端部核查真实接口，先来源孔身份，再相邻承载。

## 固定确认单与历史

- 固定工具[协议](docs/review-sheet-protocol.md)，所有新批次先build，再由实际人审导出并check归档。不能通过构建成功、点击或聊天口头“通过”制造物理/几何批准。
- 2026-11-04的演示包runs/review-sheet-refined-v1已归档用户5/5，仅验证界面使用，不批准新金属或接口。
- [前入口完整归档](docs/history/current-task-before-2026-11-05-w34-m2-review.md)保存v12收口和演示状态；其中历史裁决及未知继续生效，关键项如下。

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
# 接续本轮未审候选；输出必须新目录，不重复执行added_metal_ids事务。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/w34-m2-coverage-v1/next-request.json --output runs/新的M2候选接续目录
# 用户完成导出后，以实际收到的文件路径替换，才可归档。
.venv/bin/python -m silicon_eye.review_sheet check --package docs/assets/w34-m2-coverage-v1/review --decision /实际路径/review-decision.json --archive
```

不得自动重建README/site或发布gh-pages。仅有人工确认单归档后才更新本批几何验收状态。
