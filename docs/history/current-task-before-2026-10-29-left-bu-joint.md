# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-29 before approved U/D working integration.

# 当前任务

## 当前目标、状态与授权

**Q1 的 V1 身份及接 M2 A 已确认；已沿 A 查到上、下两端的新 V2 候选 U／D，待集中裁决身份及 M3 承载。** 不重问 Q1，不按投影交叉自动连接中部 M3。

- [当前复核页](docs/assets/left-bu-v1-reviewed-v2/index.html) · [U 两层并排](docs/assets/left-bu-v1-reviewed-v2/U-paired.png) · [D 两层并排](docs/assets/left-bu-v1-reviewed-v2/D-paired.png) · [当前状态](benchmarks/left-bu-v1-reviewed-v2/source-review-state.json) · [报告](docs/reviews/2026-10-29-left-bu-v1-reviewed.md) · [验证](benchmarks/left-bu-v1-reviewed-v2/verification.json)。
- [Q1 人审原话](benchmarks/left-bu-v1-reviewed-v2/human-review.json)为“Q1：是 V1，接 A”；来源层为 M1，孔组框 [1990,2664,2042,2765]，接 LEFT-M2-A-CANDIDATE。只确认身份和承载，孔数、精密落点、重合、几何未批准。原送审页及 answer=null 请求原样冻结，不回写历史。
- 工作几何仍从 [BR-R work-v3 next-request](benchmarks/BR-R-return-work-v3/next-request.json) 恢复，[五层工作页](docs/assets/BR-R-return-work-v3/work/index.html)不变：34 金属候选、11 已审工作接口、46 设计孔中心，780×1440，旧坐标保持。新 Q1 是额外保存的第 12 条来源接口事实，尚未并入工作几何；不混报为 12 条已包围验收的工作接口。
- 未修改程序／模型，不新增网号。geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。README/site/gh-pages 保持；未提交／推送。main 起点 66a450a；2026-10-29 各阶段工作尚未提交。skill 仍 LIMITED_TRIAL_V2。

## 唯一当前裁决批次与下一步

[U／D 原始请求](benchmarks/left-bu-v1-reviewed-v2/review-request.json)有两项：

- **U（LEFT-M2-A-V2-U）**：M2 A 上端孔组 [1935,1898,2008,1965] 是否为 V2，并接紫色 B-U／RT-M3-UP 宽母线？
- **D（LEFT-M2-A-V2-D）**：M2 A 下端孔组 [1942,2695,2008,2795] 是否为 V2，并接粉色 B-D／RT-M3-DOWN 宽母线？
- 本次仅判新身份与承载，孔数未知；M3 自身亮孔不能反充 V2 证据。两层并排各用原生坐标，未错误投影，尚未声称精密孔组包围通过。
- U/D 未裁决前不将它们作为已接通接口继续扩网。裁决后先明确左扩来源／工作坐标范围、构造整组候选、联合修订及包围检查，再接续几何；禁止压缩、平移旧工作或移动 46 孔中心。
- 原 P1–P5、BF24／25／26、原 A/B、Q1 不重复审核；不逐孔审批。来源裁决不等于规范层采用或全网完成。

## 本次接续与覆盖边界

- 原 R3/R4→左侧回折／中央 BR-C／BU 的 AI 来源观察按[上一包](benchmarks/R3-R4-left-continuation-v1/source-observations.json)保持；BU 向上／向西仍有未穷尽出口。Q1 的回复没有顺带批准这些精密几何或所有邻支路。
- M2 A 在此次原生宽图内连续，自上端 U 延伸至下端 D。右侧中部小孔列是另一 M2 对象；没有按中部 M3 的交叉建立连接，也不以本次未检出证明其它 VIA 不存在。
- M3 上／下宽带在原图连续到旧走廊 B-U／B-D，是 AI 承载候选关联；不改旧 M3 局部 native_path，不以外推直线替代来源。上下层各自图片保留原生范围，source_to_design_transform=null。
- [接续来源记录](benchmarks/left-bu-v1-reviewed-v2/source-continuation.json)与[6组裁片记录](benchmarks/left-bu-v1-reviewed-v2/source-panels.json)保留来源、坐标、未知及中部排除项；无标记照片区逐像素一致，旧包／模型／程序与 25 个展示文件保持。静态资源、脚本和 PNG 检查，浏览器切换未实测。本轮无程序变更，不重跑此前 127 项测试。
- [本轮前入口全文](docs/history/current-task-before-2026-10-29-left-bu-v1-reviewed.md)完整归档，以下旧裁决／未知继续有效。

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
# 唯一当前几何恢复入口；输出使用新目录。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/BR-R-return-work-v3/next-request.json --output runs/新的BR-R接续目录
# 仅旧 M2/V2/M3 声明范围覆盖核对
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的覆盖核对目录
```

前入口全文完整归档于[本轮核查前](docs/history/current-task-before-2026-10-29-R3-R4-left.md)。其它 V1 从 benchmarks/v1-new-short-branch-reviewed-v2/next-request.json 恢复，旧中样从 benchmarks/m1-local-tab-v1/work-next.json 恢复。历史初稿在 runs/B-short-finger-initial-review-build-v2、runs/corridor-m1-v1-pre-resource-reuse-v2 保留，不作当前裁决。不得自动重建 README/site 或发布 gh-pages。
