# 入口原文归档

来源：CURRENT_TASK.md；归档日期：2026-11-06。下方原文完整保留。

# 当前任务

## 当前状态与本次停止边界

**L01新线几何G1与短头V2身份I1已由实际确认单通过归档。用户要求先提交Git/GitHub，后续分析下次继续；本次不开展M3承载分析。**

- [实际确认记录](docs/assets/w34-left-m2-v1/review/review-record.md) · [最新已审工作基线](benchmarks/w34-left-m2-reviewed-v2/working-baseline.json) · [I1已审V2身份](benchmarks/w34-left-m2-reviewed-v2/V2-identity-reviewed.json)。实际版本0bb2cde885f74ee0aa03f9e086b65c5b，G1/I1均accepted。
- [54金属工作模型](docs/assets/w34-left-m2-v1/work/index.html) · [唯一接续请求](benchmarks/w34-left-m2-v1/next-request.json)。M1=11/M2=18/M3=25；34条已审局部连接、188候选设计孔保持。I1尚未建为模型VIA或连接；物理孔数/尺寸未知。
- L01=W34-M2-L01，原生[[220,1750],[248,2365],[222,2366]]，窄窗口M2=[180,1680,280,2410]；设计正交路径[[-2640,50],[-2640,510],[-2666,510]]，宽6为本批已审相对几何，不是实测尺度或共同GDS采用。
- I1原生框[210,2348,262,2380]的V2身份已审；connection_confirmed=null、upper_metal_id=null、physical_cut_count=null。**身份通过不等于M3承载通过，也不以设计图重叠推导连接。**

## 下次唯一下一步：核I1的M3承载

- 下次恢复后，从原生M3照片建立局部结构对应、比较邻近替代导体，核I1接哪条M3；未有合格投影时分别并列原图，不直接投影或靠行号/设计y510指定。
- G1几何和I1身份不重审；只对影响新承载的歧义提交固定确认单。承载实际通过后再检查完整组上下包围，必要时限定微调，之后才允许增加模型接口。
- 本轮到提交/推送完成即停止；不提前生成承载候选、不增加新网络分析任务。L01上端接口仍未知，不因可见线端强配V1。
- [四非孔收口](benchmarks/w34-terminal-v1-reviewed-v2/identity-closeout.json)继续生效：W34-END-N1/N2/N3/S1均是已拒绝M1搜索目标，不重问、不建孔，不推导附近无孔或全局断开。

## 工程与质量记录

- [本批22项几何/保持检查](benchmarks/w34-left-m2-v1/verification.json)通过；统一入口显式补建L01、next-request重放通过；原53feature、原17个M2对象和M1/M3/V1/V2、34连接、188孔中心及画布保持。
- [提交前检查](benchmarks/w34-left-m2-reviewed-v2/release-checks.json)：114项相关测试本次重新运行通过，定向Ruff通过；固定确认单资源与归档校验通过，diff检查通过。旧历史总回归README哈希漂移FAIL原样保留，不宣称整套PASS。
- 本批包含受限[固定确认单V2连接接续适配](silicon_eye/conductive_sheet_review.py)及[拒绝/接续测试](tests/test_conductive_sheet_review.py)，供旧四短头已审连接使用；L01的承载尚未确认，未使用适配器生成新连接。契约见[统一入口](docs/architecture/conductive-workflow-contract-v1.md)。
- README/site当前25文件、M1/M2/M3原图、AA/POLY/CT及规范注册表保持，未发布gh-pages。原始送审包、旧人审与否定记录不改写；当前批准以新的已审基线为准，冻结pending是历史。
- skill仍LIMITED_TRIAL_V2；source_to_design_transform=null、geometry_adopted=false、net_edges=[]、complete_network=false。工程通过不等于真实PDK DRC、全幅金属完成或完整网表。
- 本次GitHub提交包括本地尚未推送的联合几何、M3覆盖、四条M2延伸、四非孔裁决、L01及全部实际确认单。提交/远端同步状态以Git记录为准；不在文档写入会自引用改变的本次提交哈希。

## 基线与历史

- [原53金属范围基线](benchmarks/w34-terminal-reviewed-v2/working-baseline.json)、[M3固定窗口基线](benchmarks/w34-m3-reviewed-v2/working-baseline.json)、[四端来源连接](benchmarks/w34-joint-geometry-v1/source-connection-baseline.json)及[身份](benchmarks/w34-short-terminal-reviewed-v2/identity-baseline.json)保持。
- [原接口清点](benchmarks/w34-terminal-extension-v1/interface-sweep.json)的8处V2/4处V1不包括新I1；I1身份记录与34条已审模型连接区分。[四负例参考](benchmarks/w34-terminal-v1-reviewed-v2/negative-reference-set.json)是人工参考，未宣称自动AI评测。
- [本次前入口全文](docs/history/current-task-before-2026-11-05-w34-left-m2-reviewed-push.md) · [本轮L01说明](docs/reviews/2026-11-05-w34-left-m2.md) · [固定确认协议](docs/review-sheet-protocol.md)。

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

## 下次恢复

```bash
# 先读最新已审基线；不重复L01补建，不重问G1/I1，不复活四非孔目标。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/w34-left-m2-v1/next-request.json --output runs/新的L01接续目录
```

本次推送后停止。下次仅核新V2的M3承载；不得自动重建展示页、发布gh-pages或导完整网表。
