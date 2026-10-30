# 当前入口归档

来源：CURRENT_TASK.md；日期：2026-10-29；以下为横向分支扩展前的完整入口。

# 当前任务

## 当前状态与授权

**A／B 已裁决：两处均有V1并接RT-M2-R01；已建立同一区域M1／V1到现有M2／V2／M3的局部候选接续。** 新增1段局部M1竖段及2组V1，原30条金属、9接口、42设计孔/中心及旧裁决精确保持。合计31金属/11已审接口；两组新阵列各两孔仅作设计假设，物理孔数、精确落孔和M1横向分支完整性未知。README/site/gh-pages保护，skill仍LIMITED_TRIAL_V2。本日修改尚未提交/推送。

[原M2/V2/M3覆盖与来源/设计切换页](docs/assets/conductive-corridor-closeout-v2/index.html) · [覆盖汇总](docs/assets/conductive-corridor-closeout-v2/coverage.json) · [限定能力及下一阶段](benchmarks/conductive-corridor-closeout-v2/scope-decision.json) · [核对验证](benchmarks/conductive-corridor-closeout-v2/verification.json) · [本轮报告](docs/reviews/2026-10-29-corridor-scope-closeout.md) · [旧入口完整原文](docs/history/current-task-before-2026-10-29-corridor-scope-closeout.md)。

## 当前成果与不能升级的资格

[当前五层接续复核页](docs/assets/corridor-m1-v1-reviewed-v2/index.html) · [切换工作页](docs/assets/corridor-m1-v1-reviewed-v2/work/index.html) · [原话与逐项裁决](benchmarks/corridor-m1-v1-reviewed-v2/human-review.json) · [当前来源状态](benchmarks/corridor-m1-v1-reviewed-v2/source-review-state.json) · [最新接续请求](benchmarks/corridor-m1-v1-reviewed-v2/next-request.json) · [验证](benchmarks/corridor-m1-v1-reviewed-v2/verification.json) · [本轮报告](docs/reviews/2026-10-29-corridor-M1-V1-reviewed.md) · [裁决前入口全文](docs/history/current-task-before-2026-10-29-M1-V1-reviewed.md)。

- 2026-10-29用户原话“都有”，对应唯一问题CORRIDOR-M1-V1-ENTRY-Q1，确认A/B的V1身份及接R01。原问题/原生框不倒改，新增review覆盖记录；新M1编号映射为AI观察，不把新规则几何和孔数记为人工批准。
- 新C-M1-SPINE仅覆盖照片可见长竖段，A右侧/B左侧横向分支尚未建立。本次不声称M1全覆盖。新增V1采用显式2×1候选组，逐孔和整组包围检查通过，真实孔数/孔中心仍未知；不采用外围宏观变换落孔。
- 工具新增显式追加来源清单及原生M1入口裁决适配：冻结原30条清单/映射，只附加1条M1；禁止续跑替换既有补充清单、偷改层次/原生框/承载、将宏观位置或候选孔数升级为批准。相关102项唯一软件测试通过（首轮101，补充追加保护后17项新接口测试通过；原85项未变），Ruff通过。
- 下方M1入口v1是送审历史；当时unknown/未新增结论保留为历史，实时A/B状态以上述reviewed-v2为准。原30/9覆盖报告保持独立M2/V2/M3范围，不升级为五层照片穷尽性。

[本轮原生宽图](docs/assets/corridor-m1-v1-entry-v1/native-wide-pair.png) · [A/B大邻域局部](docs/assets/corridor-m1-v1-entry-v1/native-A-B-details.png) · [原图切换页](docs/assets/corridor-m1-v1-entry-v1/index.html) · [原送审问题](benchmarks/corridor-m1-v1-entry-v1/review-request.json) · [送审时来源状态](benchmarks/corridor-m1-v1-entry-v1/source-review-state.json) · [验证](benchmarks/corridor-m1-v1-entry-v1/verification.json) · [阶段报告](docs/reviews/2026-10-29-corridor-M1-V1-entry.md) · [前入口完整归档](docs/history/current-task-before-2026-10-29-M1-V1-entry-review.md)。

- 方阵内部ORB匹配独立保留区P95约129px，拒绝；外边界首版因FBL定位触搜索带边界也拒绝。按原图修正同一间隔边界种子后，保留35px测量带及20/50px宏观预算，4拟合点/另2方阵保留点约2.5px内。没有V1/V2参与拟合，仍只作搜索，不能据此认证内部落孔/全图配准。
- M1来源搜索框A=[3125,1930,3175,2010]、B=[3130,2775,3180,2845]，不作为已确认孔组框。亮边可能为CT、金属边缘及拍屏调制；送审时这些字段为null；现A/B身份和接R01由reviewed-v2覆盖确认，精确孔位/数仍未知。R02板边未建立清楚V1，暂不分散提问，不声明无孔。
- 8张原生裁片逐像素一致，旧模型完整回放相等；源哈希、矩阵方向/保留点残差复算、测量带、静态资源/JS、PNG目视和25展示文件/gh-pages保护检查通过。此项为送审阶段检查；当前新增代码/几何及软件检查见reviewed-v2，浏览器交互仍未实测。

- 30条导体（M2=8/M3=22）、60来源端部、48范围出口均一一核对。范围出口不是物理终点；23条原定性几何保持，7条为后续局部修订候选，不能继承为新几何人审批准。
- 9个已审接口在现模型均已落实，源照片、承载、原话及独立设计坐标保持；9个显式候选组全包络和逐孔包围通过。物理孔数全部未知，照片接口总数/覆盖率、精确源几何/投影、真实PDK、完整网络均未放行。
- C06-V2原生框[2933,2140,2977,2175]跨声明走廊x2940左界。新通用核对入口要求跨界项有原人审绑定和明确范围说明；不会用9/9代表9个完全位于范围内的孔组。
- 08仍为范围内AI未识别明确V2，三条弱M3仍为AI不补建处置；都不是人审物理不存在。05/06局部不连续、03→T01、04→T02、05→E1、06→E2和N1→C-M3-L01均不重问。
- 新增可复用conductive_coverage入口，读取冻结清单、当前workflow和已有证据，生成JSON/CSV核对表，不调用识图或改变几何。18项软件测试通过（新核对9/既有清单9），Ruff通过；CSV/JSON104行、39对象/72 SVG路径、静态资源/JS、展示保护通过。浏览器交互未实测。
- 已启动[M1／V1入口检索](benchmarks/conductive-corridor-closeout-v2/M1-V1-entry-inspection.json)，保存M1/M2独立原生宽图，入口仅形成外围宏观搜索参照，A/B现已有V1身份/接R01裁决；内部精确对应仍未建立，当前裁决按reviewed-v2接续。旧V1短支路样本位于另一原生区域，只复用方法和质量门，不直接移植其坐标/连接。
- 当前五层接续用上述reviewed-v2；[旧30金属/9接口包](docs/assets/corridor-0506-joint-reviewed-v3/work/index.html)和[旧请求](benchmarks/corridor-0506-joint-reviewed-v3/next-request.json)保持冻结。原覆盖v1的5接口和中间7接口是历史，冻结不倒改；当前核对表请读closeout-v2。

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

沿同一照片补查A右侧、B左侧的M1连续横向分支，先建来源清单再补局部几何，检查其它接口；不重问A/B身份或R01承载，不要求逐孔计数。遇到新的层次/承载歧义才贴宽图及大邻域原图集中裁决；不能从规则几何或亮边自动补连接。

```bash
# 新输出目录；保持31条金属、11条局部接口和所有孔中心
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/corridor-m1-v1-reviewed-v2/next-request.json --output runs/新的五层接续目录
# 仅原M2/V2/M3声明范围的核对；不得称为五层穷尽覆盖
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的覆盖核对目录
```

main本轮起点66a450a（2026-10-28已推送）。2026-10-29核对模块、测试、范围汇总、M1/V1入口实验及本轮裁决/候选接续未提交。资源按哈希复用旧M2/M3图，新M1图只保存一份；首次重复资源的构建完整备份在runs/corridor-m1-v1-pre-resource-reuse-v2。其他V1分支从benchmarks/v1-new-short-branch-reviewed-v2/next-request.json恢复；旧中样从benchmarks/m1-local-tab-v1/work-next.json恢复。不得自动重建README/site或发布gh-pages。
