# 当前任务

## 当前状态与授权

**连续走廊的声明清单/几何/接口核对已完成，限定范围阶段可收口；下一步在同一连续范围接续M1／V1。** 本轮只做核对和下一阶段来源检索，无新几何/接口/人工裁决。当前30声明导体均有对应几何，9已审承载/42设计候选孔/9完整声明组包围通过；这不是照片穷尽或完整网表。C06来源孔组框跨左边界7原生像素，8框在范围内、1框跨界；原始框和批准保持，不裁小/静默扩范围。README/site/gh-pages保护，skill仍LIMITED_TRIAL_V2；本轮本机修改尚未提交/推送。

[当前覆盖与来源/设计切换页](docs/assets/conductive-corridor-closeout-v2/index.html) · [覆盖汇总](docs/assets/conductive-corridor-closeout-v2/coverage.json) · [限定能力及下一阶段](benchmarks/conductive-corridor-closeout-v2/scope-decision.json) · [核对验证](benchmarks/conductive-corridor-closeout-v2/verification.json) · [本轮报告](docs/reviews/2026-10-29-corridor-scope-closeout.md) · [旧入口完整原文](docs/history/current-task-before-2026-10-29-corridor-scope-closeout.md)。

## 当前成果与不能升级的资格

- 30条导体（M2=8/M3=22）、60来源端部、48范围出口均一一核对。范围出口不是物理终点；23条原定性几何保持，7条为后续局部修订候选，不能继承为新几何人审批准。
- 9个已审接口在现模型均已落实，源照片、承载、原话及独立设计坐标保持；9个显式候选组全包络和逐孔包围通过。物理孔数全部未知，照片接口总数/覆盖率、精确源几何/投影、真实PDK、完整网络均未放行。
- C06-V2原生框[2933,2140,2977,2175]跨声明走廊x2940左界。新通用核对入口要求跨界项有原人审绑定和明确范围说明；不会用9/9代表9个完全位于范围内的孔组。
- 08仍为范围内AI未识别明确V2，三条弱M3仍为AI不补建处置；都不是人审物理不存在。05/06局部不连续、03→T01、04→T02、05→E1、06→E2和N1→C-M3-L01均不重问。
- 新增可复用conductive_coverage入口，读取冻结清单、当前workflow和已有证据，生成JSON/CSV核对表，不调用识图或改变几何。18项软件测试通过（新核对9/既有清单9），Ruff通过；CSV/JSON104行、39对象/72 SVG路径、静态资源/JS、展示保护通过。浏览器交互未实测。
- 已启动[M1／V1入口检索](benchmarks/conductive-corridor-closeout-v2/M1-V1-entry-inspection.json)，保存M1/M2独立原生宽图，尚未建立同位置对应或指定V1。旧V1短支路样本位于另一原生区域，只复用方法和质量门，不直接移植其坐标/连接。
- 当前几何与9条批准的接续仍用[最新work包](docs/assets/corridor-0506-joint-reviewed-v3/work/index.html)和[next-request](benchmarks/corridor-0506-joint-reviewed-v3/next-request.json)。原覆盖v1的5接口和中间7接口是历史，冻结不倒改；当前核对表请读closeout-v2。

## 必须接续的裁决与未知

- 2026-10-26用户确认Q1/Q2均已解决：两处定性工作几何已验收，联合中样阶段收口，不再作为待裁决问题。具体像素/物理尺寸、未知路径及全幅坐标资格仍按下述范围保留；原连接批准不重审。
- 中样22条金属、9代理组及两组显式阵列仅覆盖已审清单38条中的11条，非照片覆盖率；独立样本6条金属及两组显式阵列。新局部候选不替换原共同注册表。
- A={T3,L2}、B={T1,L4}，分别经M2/M3接A、B；旧L3不复活。具体返回M2、M3-X/Y及逐孔路径未知。MID-H1/H2本处与U1/U2隔离，不推导全局异网；H1→V1→M2-A、H2→V1→M2-B已审。
- U1/U2同一M1；U1/U3有V1、U2无V1，两处均接N2。U1设计右端1310，原生1945<P08左竖2006的次序保持，不补跨H1/H2竖线。N2上接B1、下经D1接L1，F01–F12等已审承载保持。
- U3宽M1→所圈CT行→对应AA环仅该路径terminal_closed=true，体端/极性、孔数、边界及规范材料ID映射未知。13主分支不等于下层覆盖完成，P0/P5等原范围按归档保留。
- 孔身份策略为M1照片侧V1、M2照片侧V2。J组3×4=12个V2已审；旧九对V1/V2同孔拟合及4.52px残差已撤回，不作配准证据。
- 独立Q1六孔经V1接宽IT1-M2-B，原窄A错误；Q2为M2-B经V2接M3-BUS。A/B同层是否连续未知，亦不同于MID分组。历史ID后缀不决定承载。
- 唯一共同快照[configs/joint-work-layer-v5.json](configs/joint-work-layer-v5.json)：AA334/POLY696/CT10287；八张5712×4284照片和哈希保持。导体注册表仍为[原33记录模型](docs/assets/conductive-stack-v2/model.json)。
- 六处材料未知仍为AA-F01951、AA-F01952、材料H1/H2、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS。V3主体截段历史例外、S1/S2/S3身份、G66上桥、R1/R2、四栅33孔、18电阻、W01与195保留对象按原范围继承，详见完整归档。
- net_edges空、automatic_network_export_allowed=false、complete_network=false；真实尺度/工艺/极性/WL/阻值和完整网表未知。金属与孔skill仍为限定试用v2，未正式通用放行；材料skill资格不变。

## 唯一下一步

以RT-M2-R01/R02现有走廊为上层目标，核清同区域M1／V1的接续入口：先用原生宏观结构与独立标记建立局部同位置关系，再从M1侧确认V1，最后判断对应已审M2。不将M2的V2当V1，不将旧异区域短支路当同位置证据；若源身份/承载仍不清楚，只提出一个有宽上下文的必要问题。

先做一个连续范围的M1→V1→现有M2→已审V2→M3接续，沿用显式候选组和防退化，不启动全幅M1重建或继续无限增加孤立M3案例。当前M1检索裁片相同数字坐标不代表已对齐，禁止直接投影。

```bash
# 几何与批准接续（新输出目录，不覆盖原包）
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/corridor-0506-joint-reviewed-v3/next-request.json --output runs/新的走廊接续目录
# 声明清单核对（输出数据表；本页UI为冻结交付）
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的覆盖核对目录
```

main最后本轮起点66a450a（2026-10-28已推送）；当前2026-10-29核对模块、测试、范围汇总及M1/V1入口检索未提交。其他V1分支仍从`benchmarks/v1-new-short-branch-reviewed-v2/next-request.json`恢复；旧中样从`benchmarks/m1-local-tab-v1/work-next.json`恢复。不得自动重建README/site或发布gh-pages。
