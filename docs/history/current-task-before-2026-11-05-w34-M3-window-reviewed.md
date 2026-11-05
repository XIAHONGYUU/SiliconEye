# 当前任务入口完整归档

来源：CURRENT_TASK.md；日期：2026-11-05（Asia/Shanghai）。以下为本次M3窗口验收前入口全文；其等待语句是历史状态，实际新确认单已另行归档通过。

---

# 当前任务

## 当前目标与状态

**上一批四短头/R03/六线西延的联合几何已实际归档通过。固定M3窗口剩余R01/R02/B01已补候选，等待两组增量几何及窗口明显漏段复核；不重审已批准接口。**

- [联合几何实际归档](docs/assets/w34-joint-geometry-v1/review/review-record.md) · [已审工作基线](benchmarks/w34-joint-reviewed-v2/working-baseline.json)。原包G1/G2及整体Q1通过，冻结模型/原始提案保持；几何批准不等于物理孔数、精确投影或GDS采用。
- [最新53金属工作候选](docs/assets/w34-m3-remainder-v1/S2-joint-work/index.html) · [唯一接续请求](benchmarks/w34-m3-remainder-v1/next-request.json) · [本轮技术验证](benchmarks/w34-m3-remainder-v1/verification.json)。M1=11/M2=17/M3=25；34条已审局部连接、188候选孔逐字段保持。孔数/尺寸未获物理真值批准。
- 新增W34-M3-R01/R02，另仅为原RT-M3-MID添加西侧局部块；原宽母线骨架/宽度/锚点不动，没有重复母线，没有新增孔或连接。

## 唯一下一步：本固定窗口增量几何验收

- [固定确认单](docs/assets/w34-m3-remainder-v1/review/index.html)，预览 http://127.0.0.1:8772/w34-m3-remainder-v1/review/index.html 。包W34-M3-REMAINDER-20261105-V1，build=eeffc3a512d54a34b65486a8b73ca3bf。
- G1审R01短段/R02贯穿段的相对位置、长度、次序和间隙；G2审B01与原宽母线对应及西延；整体Q1只审固定窗口九条细线与宽母线局部无明显漏段。不要求逐孔计数，不重问已审四端或七条旧细线。
- [来源→几何→接口清单](benchmarks/w34-m3-remainder-v1/scoped-coverage.json)保留原生M3窗口[180,2120,1280,2490]：声明的10片段已有10对应，其中7项几何已有上一批G2批准，3项新几何待审。10/10是清单有对应，不是照片独立穷尽认证或全部接口覆盖。
- B01在固定窗口下沿仅露上部；更大同一张M3照片可跟至RT-M3-MID旧锚点，支持沿用同一导体ID。规则图完整宽度仍为沿用的相对重建，不是本窗口实测宽度。新R01/R02/B01接口未逐一排查，不能以本轮几何通过推导无孔或全网闭合。
- 收到实际导出后check归档；若通过，固化本窗口几何覆盖，再沿来源清单检查未评估接口/出口。范围出口始终不是物理终点。

## 工程接续与质量门

- [S1只增两金属](benchmarks/w34-m3-remainder-v1/S1-add-request.json)后，[S2只延伸原宽母线](benchmarks/w34-m3-remainder-v1/S2-bus-request.json)；补建和旧几何修订分开执行，next-request去除事务声明并精确重放。
- 15项本轮直接不变量检查通过：旧51金属仅RT-M3-MID追加块，其余逐字段保持；M1/M2/V1/V2、34接口、188孔坐标、旧母线足迹与原生锚点保持；九行来源/设计上下次序一致；局部M3最小间隙7个工作坐标单位；README/site25文件与当前冻结哈希一致。此为当前工程门，不是真实工艺DRC。
- 补建、母线修订和接续重放均由统一入口通过。固定页面manifest/资源校验通过；浏览器检查原图/规则图及宽母线长邻域加载成功，保留大图模式，未替人点击审批。
- 前轮114项相关软件测试、定向Ruff已通过；本轮只变数据/稿件，未重复扩大测试。原历史总回归因早前README哈希漂移仍FAIL，报告保持，不改历史基线或宣称整套PASS。
- [受限确认单接口适配](silicon_eye/conductive_sheet_review.py)仍只消费实际V2身份/承载确认单；不伪造人审statement、孔数或几何批准。见[契约](docs/architecture/conductive-workflow-contract-v1.md)。
- M1原生锚点/预算/材料及画布[-2700,0,780,1440]保持；source_to_design_transform=null、geometry_adopted=false、net_edges=[]、complete_network=false，skill仍LIMITED_TRIAL_V2。不能自动写共同GDS或导完整网表。
- [本轮记录](docs/reviews/2026-11-05-w34-M3-remainder.md)。已推送版本仍[6a217d5](https://github.com/XIAHONGYUU/SiliconEye/commit/6a217d54cf2962abe80a7b34b1bb14d03e630cc7)，之后工作留本地；README/site、AA/POLY/CT、规范注册表及gh-pages不变。

## 基线与历史

- [旧M2已审基线](benchmarks/w34-m2-reviewed-v2/working-baseline.json)、[四端身份](benchmarks/w34-short-terminal-reviewed-v2/identity-baseline.json)、[四条已审来源连接](benchmarks/w34-joint-geometry-v1/source-connection-baseline.json)继续有效；旧冻结包pending语句为提交历史，不重复送审。
- [本次前入口完整归档](docs/history/current-task-before-2026-11-05-w34-joint-geometry-reviewed.md)保留全文；[更早入口](docs/history/current-task-before-2026-11-05-w34-m3-carriers-reviewed.md)及[固定协议](docs/review-sheet-protocol.md)可回查。

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
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/w34-m3-remainder-v1/next-request.json --output runs/新的M3接续目录
# 换成实际收到的下一份导出；不自行填写人审答案。
.venv/bin/python -m silicon_eye.review_sheet check --package docs/assets/w34-m3-remainder-v1/review --decision /实际路径/review-decision.json --archive
```

不得自动重建README/site或发布gh-pages。实际连接批准、已审几何、本轮新增几何和物理未知分开保留。
