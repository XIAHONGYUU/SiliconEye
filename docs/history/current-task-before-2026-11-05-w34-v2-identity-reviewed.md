<!-- 来源 CURRENT_TASK.md；2026-11-05四端V2身份裁决接续前原文完整归档 -->

# 当前任务

## 当前目标与状态

**W3/W4邻近M2的G1/G2/COV及整体Q1/Q2均已通过实际导出确认单校验并归档。四条M2定性几何、固定范围“无明显遗漏”已收口；下一步集中裁决S01–S04短端的V2身份，尚不判断M3承载。**

- [本轮已审基线](benchmarks/w34-m2-reviewed-v2/working-baseline.json) · [四条准确批准几何](benchmarks/w34-m2-reviewed-v2/reviewed-fragments.json) · [已审范围覆盖](benchmarks/w34-m2-reviewed-v2/scoped-M2-coverage-reviewed.json)。
- [实际确认记录](docs/assets/w34-m2-coverage-v1/review/review-record.md) · [归档JSON](docs/assets/w34-m2-coverage-v1/review/review-decision.json)；旧送审build=30785baea2e440169f045696a25364eb。它不是演示包。
- M2固定原生范围[280,1870,850,2840]；新S01–S04几何获定性批准，两个旧主干W3/W4只作上下文。6/6声明片段有对应几何，COV为本范围明显可见无遗漏，不扩大为实测边界/物理照片穷尽/全幅M2完成。
- 三条上端、一条下端仍是范围出口；四个短端V1/V2身份和承载不随几何批准而通过。旧46对象、30接口、179候选孔、旧M1基线及材料保持。

## 当前唯一下一步：四个短端的V2身份

- [正式孔身份确认单](docs/assets/w34-short-terminal-v1/review/index.html)，预览 http://127.0.0.1:8772/w34-short-terminal-v1/review/index.html 。包W34-SHORT-TIP-V2-IDENTITY-20261105-V1，build=f2f06bd9e86c4118a743459ab9210868。
- 只问S01/S02/S03/S04橙框是否包含M2→M3的V2；[来源观察](benchmarks/w34-short-terminal-v1/observations.json)保留原生框，四端均可见疑似孔组亮点，identity_confirmed=null，上M3 ID=null，孔数未知。
- 宽邻域、共同局部图、原图和已审M2图可切换；本次不是新孔尺寸/整组包围或连接审批，不重问G1/G2/COV，也不重审W3/W4八处接口。
- M1及M3宽邻域已查看，但新V1或M3具体承载尚未建立可靠对应；不能把M2亮点当V1，不能只按跨帧y坐标认定M3行号。三层坐标保持独立，没有精确投影。
- 用户导出新确认单后，Agent核对新build并用review check --archive归档；身份明确后再检查M3相对对应与完整孔组包围。任一不确定保留，不自动新增孔或接通。

## 工作接续与验证

- 工作模型继续使用[不变的50金属模型/五层页](docs/assets/w34-m2-coverage-v1/work/index.html)，[唯一几何恢复请求](benchmarks/w34-m2-coverage-v1/next-request.json)。必须同时读取已审M2基线和准确组件；冻结提案中的pending是送审历史，不再索要旧批准。
- M1=11/M2=17/M3=22，30已审局部接口、179设计候选孔；本轮没有新孔/接口/网边。原点/尺度/视口[-2700,0,780,1440]保持，source_to_design_transform=null，geometry_adopted=false，net_edges=[]，complete_network=false；skill仍LIMITED_TRIAL_V2。
- [接续验证](benchmarks/w34-m2-reviewed-v2/verification.json)：真实导出版本匹配、范围/必查/边界均有效，所有批准组件绑定，模型精确重放，来源/固定包哈希与原图像素裁片核验通过，当前README/site25文件保持。
- 本轮无程序或几何更改，未重复跑上一批75项软件测试。上一送审[验证](benchmarks/w34-m2-coverage-v1/verification.json)和[说明](docs/reviews/2026-11-05-w34-m2-coverage.md)保留；旧固定回归README历史哈希差异仍单列，未篡改旧基线，未声称整套回归PASS。
- [本次批准与孔身份核查说明](docs/reviews/2026-11-05-w34-m2-reviewed-and-terminal.md)。当前版本已提交并推送GitHub [6a217d5](https://github.com/XIAHONGYUU/SiliconEye/commit/6a217d54cf2962abe80a7b34b1bb14d03e630cc7)，远端main已核对；不改README/site、AA/POLY/CT、规范导体注册表或gh-pages。

## 版本归档检查（2026-11-05）

- 本次提交包含M2四线补建、实际人审归档、已审基线与待裁决V2确认单。44项相关测试通过，两固定包/来源哈希与50金属接续重放通过，README/site25文件保持。详见[提交检查](docs/reviews/2026-11-05-w34-github-checkpoint.md)。
- 四端V2身份尚无新导出；提交和发布源码不改变其判定。后续可独立准备M3原生可见线清单，不能提前批准四端承载。

## 推送后的独立准备（本地草稿）

- [M3原生来源准备](docs/reviews/2026-11-05-w34-m3-native-preparation.md)已整理固定范围内R01–R09九个细线片段和B01局部宽带，合计10个AI来源记录；[编号图](docs/assets/w34-m3-native-inventory-v1/middle-m3-indexed.png)。不是新增10个模型金属，也未赋予S01–S04任何M3承载。
- 原生范围[180,2120,1280,2490]，保留宽邻域及短端/出界状态；[来源清单](benchmarks/w34-m3-native-inventory-v1/source-inventory.json)与[验证](benchmarks/w34-m3-native-inventory-v1/verification.json)。不得仅按行号或跨层y邻近建立连接；后续先与已有M3同帧路径核对，避免重复建模。
- 此准备不新增人工问题；唯一下一步仍为原V2身份确认单导出。M3草稿在6a217d5推送后生成，目前留在本地。

## 固定确认单与历史

- [固定确认单协议](docs/review-sheet-protocol.md)：正式人审以实际导出和check归档为准；页面、算法PASS或聊天口头通过不升级物理/几何批准。
- 11月4日演示包只验证界面，不能移植其答案；11月5日M2实际几何通过只覆盖G1/G2/COV范围，新的孔身份页答案初始空白。
- [本次接续前入口完整归档](docs/history/current-task-before-2026-11-05-w34-m2-accepted.md)及其历史链接保存全部旧裁决/未知；关键项继续如下。

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
# 重放当前已审局部工作几何，不改变其验收范围；输出必须新目录。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/w34-m2-coverage-v1/next-request.json --output runs/新的M2接续目录
# 用户完成本轮V2身份导出后，替换为实际收到的文件路径。
.venv/bin/python -m silicon_eye.review_sheet check --package docs/assets/w34-short-terminal-v1/review --decision /实际路径/review-decision.json --archive
```

未经新裁决不为四短端加VIA或连接。不得自动重建README/site或发布gh-pages。
