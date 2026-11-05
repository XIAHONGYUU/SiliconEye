# 当前任务入口完整归档

来源：CURRENT_TASK.md；日期：2026-11-05（Asia/Shanghai）。以下为L01 G1/I1实际裁决归档与本次GitHub提交前入口全文。旧等待语句仅为历史状态。

---

# 当前任务

## 当前状态与授权范围

**已转向旧清单明确未覆盖的左侧约x220细M2：冻结整段原生观察，补建一条L01规则几何候选。其短头I1有新V2身份候选，尚未判M3承载；当前只等待新线几何和V2身份两项确认。**

- [新54金属工作候选](docs/assets/w34-left-m2-v1/work/index.html) · [精确接续请求](benchmarks/w34-left-m2-v1/next-request.json) · [22项本轮验证](benchmarks/w34-left-m2-v1/verification.json)。M1=11/M2=18/M3=25；原53金属、34条已审局部连接、188候选设计孔精确保留，未新增模型VIA或电气连接。
- [来源清单](benchmarks/w34-left-m2-v1/source-inventory.json)声明M2=[180,1680,280,2410]窄窗口，仅含L01。原生路径[[220,1750],[248,2365],[222,2366]]，上端可见，向下连续后向左短回折；不是旧S01，也不是最左另两条上下文线。
- 新ID=W34-M2-L01；设计路径[[-2640,50],[-2640,510],[-2666,510]]、宽6为相对候选。依据同一M2照片保持L01短头位于S02与S01之间的次序，未用设计图与M3重叠推导承载。

## 唯一下一步：G1几何与I1身份分别验收

- [固定复核单](docs/assets/w34-left-m2-v1/review/index.html)，预览 http://127.0.0.1:8772/w34-left-m2-v1/review/index.html 。包W34-LEFT-M2-20261105-V1，build=0bb2cde885f74ee0aa03f9e086b65c5b。
- G1只审L01整段上端、竖段、向左回折、长度和邻线间隙；I1只审M2短头橙框[210,2348,262,2380]是否为V2。两项独立，不加重复整体汇总题；绿色REF-S01/02为同帧已审参考，不重问。
- [I1原生观察](benchmarks/w34-left-m2-v1/V2-observation.json)依据M2短头局部亮点及同帧已审短头对照，仍保留identity_confirmed=null、connection_confirmed=null、upper_metal_id=null、physical_cut_count=null。金属亮边/拍屏纹理为替代解释；不先判M3、不逐孔计数。
- 实际导出后check归档：G1通过才固化新线几何；I1通过后才核原图M3承载与完整组包围。任一项未通过按实际意见处理，不由另一项通过自动升级。本次没有新的V1问题。

## 防退化与质量门

- [显式补建请求](benchmarks/w34-left-m2-v1/request.json)只增一条金属，通过统一入口；新来源[补充清单](benchmarks/w34-left-m2-v1/inventory-supplement.json)追加原清单，不改历史。next-request去掉补建声明后精确重放。
- 22项直接检查通过：只新增L01；旧53feature、原17个M2对象及M1/M3/V1/V2对象、34连接/裁决、188候选孔/中心、原画布保持；同帧短头次序和向左转折保持；新M2最小同层间隙约57.43工作单位；M1/M2/M3原图及README/site哈希保护保持。这是工程检查，不是物理身份/尺寸证明。
- [来源图台账](benchmarks/w34-left-m2-v1/view-provenance.json)分开原生宽图与规则坐标；页面提供整段、短头、未标注原图及同坐标新旧设计。固定包和可见图像加载已查，未替人审批。
- [四非孔收口](benchmarks/w34-terminal-v1-reviewed-v2/identity-closeout.json)继续生效：W34-END-N1/N2/N3/S1仅为原M1搜索目标的明确非孔，不重新搜索、不转成新接口，也不推导附近无孔或全局断开。[负例参考](benchmarks/w34-terminal-v1-reviewed-v2/negative-reference-set.json)为人工参考，未冒充自动AI评测。
- 本次仅增加数据/规则候选/复核稿，没有新增生产代码或案例专用脚本，无需重复前轮114项软件测试。历史总回归README哈希漂移FAIL保持，不报整套PASS；diff检查通过。
- skill仍LIMITED_TRIAL_V2；source_to_design_transform=null、geometry_adopted=false、net_edges=[]、complete_network=false。不作真实PDK DRC、GDS采用或全网完成结论。
- [本轮记录](docs/reviews/2026-11-05-w34-left-m2.md)。远端仍[6a217d5](https://github.com/XIAHONGYUU/SiliconEye/commit/6a217d54cf2962abe80a7b34b1bb14d03e630cc7)，后续工作留本地；README/site/gh-pages、AA/POLY/CT、规范注册表保持。

## 旧基线与历史

- [当前已审范围基线](benchmarks/w34-terminal-reviewed-v2/working-baseline.json)及[M3固定窗口基线](benchmarks/w34-m3-reviewed-v2/working-baseline.json)保持；本次54模型中的L01尚未人审，不回写已审53模型。
- [旧接口清点](benchmarks/w34-terminal-extension-v1/interface-sweep.json)接续本区8处V2/4处V1，不包括新I1；旧[四端来源连接](benchmarks/w34-joint-geometry-v1/source-connection-baseline.json)和[身份批准](benchmarks/w34-short-terminal-reviewed-v2/identity-baseline.json)不重审。
- [本次前入口全文](docs/history/current-task-before-2026-11-05-w34-left-m2-candidate.md) · [更早入口](docs/history/current-task-before-2026-11-05-w34-four-non-via-reviewed.md) · [固定确认协议](docs/review-sheet-protocol.md)。

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
# 不重复L01补建事务；新孔和承载尚未加入模型。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/w34-left-m2-v1/next-request.json --output runs/新的L01接续目录
# 使用下一份实际收到的导出，几何与身份裁决分别接续。
.venv/bin/python -m silicon_eye.review_sheet check --package docs/assets/w34-left-m2-v1/review --decision /实际路径/review-decision.json --archive
```

不得自动重建README/site、发布gh-pages或导出完整网表。I1即使为V2，其M3承载仍需独立来源证据。
