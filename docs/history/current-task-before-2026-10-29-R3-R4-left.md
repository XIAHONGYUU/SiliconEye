# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-29 before R3/R4 leftward source review.

# 当前任务

## 当前目标、状态与授权

**BR-R返回已接续到当前工作候选，显式下扩及S1/S2/S3完成。** 在用户确认“P1–P5均正确”并要求继续推进后，画布仅向下增加200设计像素：780×1240→780×1440；原点、旧坐标和孔中心保持。当前34条金属候选（M1=4/M2=8/M3=22），仍为原11个跨层接口和46个设计孔中心。没有待回复的新源问题。

- 已审P1上接BU，P2/P3的L1/L2本处不直接接BR-R，P4/P5接R3宽横条/R4底部左折条。已审来源不再重问，不能从本处留隙推导全局异网。
- 本次启用工作候选下扩，不等于人工批准精密几何或物理范围。geometry_human_approved=false、source_to_design_transform=null；不新增VIA、网号或规范层采用。
- S1只扩画布；S2只在C-M1-SPINE附加BRR-DOWN/R3/R4三个局部块；S3独立追加L1/L2候选片段及清单。旧M1骨架/宽度/原四块、BF25、30条M2/M3、11条跨层裁决及46孔中心保持。
- README/site/gh-pages保护；本轮仅本地开发，尚未提交/推送。main起点66a450a（2026-10-28已推送），2026-10-29工作尚未提交。金属/VIA skill仍LIMITED_TRIAL_V2，物理工艺/尺度/孔数/极性/WL/阻值和完整网表未知。

## 当前入口与验收证据

[当前复核页](docs/assets/BR-R-return-work-v3/index.html) · [五层切换工作页](docs/assets/BR-R-return-work-v3/work/index.html) · [前后对比](docs/assets/BR-R-return-work-v3/work-before-after.png) · [当前状态](benchmarks/BR-R-return-work-v3/source-review-state.json) · [最新请求](benchmarks/BR-R-return-work-v3/next-request.json) · [验证](benchmarks/BR-R-return-work-v3/verification.json) · [报告](docs/reviews/2026-10-29-BR-R-return-work.md) · [前入口全文](docs/history/current-task-before-2026-10-29-BR-R-work-v3.md)。

- [S1包](docs/assets/BR-R-return-work-v3/canvas-only/index.html)只扩底边，整份sample除canvas_wh外相等，输出对象/接口/审批来源再次比对；禁止宽度/缩小/非整数变化、平移/缩放/换原点、改预算或夹带几何/新审批/原图变化。无声明的父包画布改变仍被拒绝。
- [S2包](docs/assets/BR-R-return-work-v3/M1-return/index.html)只改既有M1局部外形；[S3包](docs/assets/BR-R-return-work-v3/work/index.html)单独加BRR-L1/L2-CANDIDATE。扩展事件沿父包继承，恢复不会重复扩展。
- M1原图宽图/放大图已包含下部返回，新增局部来源记录到原生y3200；原有M1及M2/M3来源范围不重写。工作y1240与原生y3000不是同一边界，未借图层范围或残差伪造配准。
- L1/L2在当前相对设计中与BR-R竖段各留26px，仅是候选工作间距，不是照片测量或PDK。左侧局部端部是出界继续，不是物理终点。灰/粉/紫色不是已确定的网络或电容极性。
- 127项相关软件测试通过，含19项新下扩原子性/保持性测试；Ruff、差异格式、三阶段精确回放、原坐标/46孔中心、11组完整候选阵列包围通过。新M1两张无标记裁片逐像素一致，静态资源/SVG/脚本与PNG目视通过；浏览器交互未实测。
- [P1–P5原话](benchmarks/BR-R-return-reviewed-v2/human-review.json)、[原送审图](docs/assets/BR-R-return-inspection-v1/index.html)与[旧未采用预案](docs/assets/BR-R-return-reviewed-v2/index.html)保留历史，当前以work-v3接续。旧预览不是当前work，也不能无父包另起模型绕过扩展检查。

## 必须接续的裁决与未知

- BF24/BF26本处上接BU，BF25本处不接BU或L1/L2，独立保留为候选，不是已确定的悬空节点。BF24/BF26下端仍未知；其余23条短指、BR-C、约y3090/y3158细条、全局返回及材料细节没有随P1–P5批准。
- A/B的V1身份及接RT-M2-R01已审；原生框A=[3125,1930,3175,2010]、B=[3130,2775,3180,2845]是站点范围而非孔组精确边界，2×1仍是设计假设。R02其它V1未查清，不声明无孔。
- 原9个V2：R01/R02上端接RT-M3-UP、下端接RT-M3-DOWN；N1→C-M3-L01、03→T01、04→T02、05→E1、06→E2。05/06本处M2不连续，不推导全局异网。08无明确V2、三条弱M3不补建均为AI处置，不是人审不存在。
- C06原生框[2933,2140,2977,2175]跨原走廊x2940左界，保留原框及裁决，不以裁切或扩范围掩盖。原M2/V2/M3覆盖核对仍限原范围，不升级为五层穷尽覆盖。
- A右支在原生x3670出旧局部范围，约x5175下拐；B左支在x2940出范围，约x1682下拐，外侧回路未建模。R3/R4本次左端也仅局部出口。旧骨架B近似y2800与横带约y2780的差别不用于移动孔。
- 外方阵宏观搜索仅定位；ORB保留点P95约129px及首版触带已拒绝。修正版约2.5px外部参照不代表内部孔精度；旧九对V1/V2同孔拟合及4.52px残差不可复活。V1从M1侧、V2从M2侧判断。
- 其它区域A={T3,L2}/B={T1,L4}、H1/H2局部隔离、U1/U2同M1、U1/U3经V1接N2、U3已审CT→AA环端子路径及范围按[前入口全文](docs/history/current-task-before-2026-10-29-BR-R-work-v3.md)保持，不转移到本走廊。
- [材料快照v5](configs/joint-work-layer-v5.json)为AA334/POLY696/CT10287；规范导体注册表仍[原33记录](docs/assets/conductive-stack-v2/model.json)。六处材料未知AA-F01951、AA-F01952、材料H1/H2、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS保持。net_edges=[]、geometry_adopted=false、complete_network=false，自动网络导出禁止。

## 唯一下一步与恢复

沿R3/R4向左检查当前照片可见连续部分与接口，先核原生来源再补候选几何。保留出界继续和全局未知；不重问P1–P5、BF24/25/26或A/B，不移动旧孔。仅在新的接触/层次歧义时提供宽图和大邻域图集中裁决。

```bash
# 当前唯一几何恢复入口；输出须为新目录。无需重复声明canvas_extension_evidence。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/BR-R-return-work-v3/next-request.json --output runs/新的BR-R返回接续目录
# 仍仅原M2/V2/M3声明范围，不给出五层覆盖率
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的覆盖核对目录
```

图像资源按哈希复用；新M1视图只保存一份。历史初稿备份在runs/B-short-finger-initial-review-build-v2及runs/corridor-m1-v1-pre-resource-reuse-v2，不作现行裁决。其它V1分支从benchmarks/v1-new-short-branch-reviewed-v2/next-request.json恢复，旧中样从benchmarks/m1-local-tab-v1/work-next.json恢复。不得自动重建README/site或发布gh-pages。
