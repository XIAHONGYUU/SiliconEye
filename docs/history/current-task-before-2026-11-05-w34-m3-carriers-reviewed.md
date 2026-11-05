<!-- 来源 CURRENT_TASK.md；2026-11-05 M3承载裁决接续前原文完整归档 -->

# 当前任务

## 当前目标与状态

**S01–S04四个短端的V2身份已由实际导出确认单全部通过并归档。下一步只核对其M3承载：AI候选S01→R09、S02→R07、S03→R04、S04→R03；尚未批准连接，不重问孔身份或旧M2几何。**

- [V2身份基线](benchmarks/w34-short-terminal-reviewed-v2/identity-baseline.json) · [实际身份人审记录](docs/assets/w34-short-terminal-v1/review/review-record.md) · [归档JSON](docs/assets/w34-short-terminal-v1/review/review-decision.json)。原身份包build=f2f06bd9e86c4118a743459ab9210868。
- [已审M2基线](benchmarks/w34-m2-reviewed-v2/working-baseline.json)及[准确组件](benchmarks/w34-m2-reviewed-v2/reviewed-fragments.json)继续生效：G1/G2/COV与整体Q1/Q2通过，四细线定性几何和M2固定范围[280,1870,850,2840]明显可见无遗漏，不扩为全幅完成。
- 四个V2身份已审不包含M3承载、孔数、精确落点或整组包围。身份基线逐项保留M2 ID与原生框，上层/连接仍null；旧冻结提案的unknown字段是其提交历史，不重问已审身份。

## 唯一下一步：四处M3承载固定确认单

- [正式承载确认单](docs/assets/w34-m3-carrier-review-v1/review/index.html)，预览 http://127.0.0.1:8772/w34-m3-carrier-review-v1/review/index.html 。包W34-V2-M3-CARRIERS-20261105-V1，build=44d697560d4d4d459deff4dc34bf47d0。
- 本轮只问S01→R09、S02→R07、S03→R04、S04→R03；若是其它R行，需修改并注明正确行号；看不清保留不确定。不重新问V2是否存在，不逐孔计数。
- [承载提案](benchmarks/w34-m3-carrier-review-v1/carrier-proposals.json)绑定已审身份及独立M3来源；[同一M3照片的连续追踪](benchmarks/w34-m3-carrier-review-v1/same-frame-continuity.json)支持R04–R09依序对应旧M01–M06，仍属AI来源对应。R03暂不绑定旧模型，禁止重复补建或移用别处批准。
- M3本层R行号固定，照片分别保留坐标。宽母线/短端相对结构只支持候选，不是精确配准；旧失败矩阵不外推，不按跨帧y邻近认定连接。尚无合格source_to_source/source_to_design变换。
- 用户实际导出新确认单后，Agent核对build并check归档；按实际承载结果再补来源支持的设计组/局部金属和整组包围。不把本次身份批准交给连接确认适配器。

## 工作模型、验证与版本

- [唯一几何恢复请求](benchmarks/w34-m2-coverage-v1/next-request.json)及[50金属模型/五层页](docs/assets/w34-m2-coverage-v1/work/index.html)不变。必须同时读取已审M2与V2身份基线；源照片、已审原生框与所有旧裁决保持。
- M1=11/M2=17/M3=22，旧30条已审模型局部连接与179候选孔保持；另外新增的是4个来源V2身份事实，尚无新模型接口/孔/网边。原点/尺度/视口[-2700,0,780,1440]保持，geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false，skill仍LIMITED_TRIAL_V2。
- [本轮验证](benchmarks/w34-m3-carrier-review-v1/verification.json)：实际身份导出check归档VALID；固定包及来源哈希核验，模型精确重放，原生裁片像素匹配。六条同帧追踪各35采样点，次序/间距不交叉；这是AI来源辅助，不是人审真值或跨帧变换。
- [本轮说明](docs/reviews/2026-11-05-w34-v2-identity-and-M3-carriers.md)。本轮只改证据、记录与文档，无程序/共同几何更改，未重复上一批44项测试；旧README历史回归差异仍保留，未声称整套回归PASS。
- 已推送版本为[6a217d5](https://github.com/XIAHONGYUU/SiliconEye/commit/6a217d54cf2962abe80a7b34b1bb14d03e630cc7)；本次身份归档、M3草稿及承载提案在其后，当前保留本地。README/site25文件、AA/POLY/CT、规范注册表及gh-pages未改。

## 固定确认单与历史

- [固定协议](docs/review-sheet-protocol.md)：实际导出与check归档才是本批人审事实，不能用演示答案、脚本PASS或一项通过替代其它未知。
- [本阶段前入口完整归档](docs/history/current-task-before-2026-11-05-w34-v2-identity-reviewed.md)保留所有旧裁决/未知及前版本记录；[原生M3清单草稿](benchmarks/w34-m3-native-inventory-v1/source-inventory.json)的10片段不是新模型对象或新网络。

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
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/w34-m2-coverage-v1/next-request.json --output runs/新的四端接续目录
# 用户完成本轮M3承载导出后，替换为实际收到的文件路径。
.venv/bin/python -m silicon_eye.review_sheet check --package docs/assets/w34-m3-carrier-review-v1/review --decision /实际路径/review-decision.json --archive
```

没有承载裁决不加新接口；身份通过不等于精确孔组包围或网络通过。不得自动重建README/site或发布gh-pages。
