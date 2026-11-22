# 当前任务

## 当前目标与授权

接续用户实际导出并继续金属重建。25对来源关系、H01/H02及R01–R10十组均已实际归档，合计12处局部形状/线宽通过。用户授权先提交GitHub再继续；本节点打包保存验收结果，推送后推进H03宽母线上下边界分析。当前没有待审批批次。H03及阵列边缘风险保持暂停；展示README/site保持。

## 当前队列

| 项目 | 状态 | 下一步 |
| --- | --- | --- |
| 672来源分流与风险局部化 | 保持 | 片段/区间不是导体数 |
| G01/G05/G24及新25对 | 全部限定范围归档 | 不重审、不传播整链批准 |
| 已审直接关系接续 | 完成，27关系/2边缘 | 20组件只作证据组织 |
| H01/H02局部矩形与线宽 | 已归档accepted | 仅局部表达，作为防退化基线，不重审 |
| R01–R10十组局部几何 | 已归档accepted | 与H01/H02合计12处局部已审，不重审 |
| H03等5处数值暂停及1处阵列边缘语义暂停 | hold | 先找真实二维边界，不由亮脊伪造中心/线宽 |

## 最新证据与验收状态

- [十组摘要](docs/reviews/2026-11-22-m3-ten-group-geometry.md) · [十组实际记录](runs/m3-geometry-ten-groups-20261122-final/review/review-record.md)。实际导出21的R01–R10均accepted、无备注，20答案相同；21.077秒仅页面交互至导出。旧页面仅作记录，不再待审。
- [12处局部已审基线](runs/m3-local-geometry-reviewed-20261122/local-baseline.json)精确保留H01/H02，追加R01–R10；只接受独立局部矩形/线宽，尚未授予全局坐标、间距、端点、孔或网络。
- [H01/H02实际记录](runs/m3-reviewed-path-geometry-20261122-v2/review/review-record.md)均accepted、无备注；实际导出19，交互至导出7.53秒，非总分析时间。[局部已审基线](runs/m3-geometry-ten-groups-20261122-final/reviewed-local-baseline.json)保留形状、线宽批准及H03暂停；全局geometry_adopted仍false。
- [25对实际记录](runs/m3-identity-followthrough-20261119/review/review-record.md)：IDENTITY-01～05均accepted、无备注；最终导出18与17答案一致。首次交互至最终导出22.909秒，非总分析时间。导出16为旧W34批次，已拒绝跨批应用，[路由记录](runs/m3-export-routing-20261122/routing-check.json)保持。
- [新来源状态](runs/m3-direct-pairs-closeout-20261122/reviewed-source-state.json)：保留旧2对关系/2条边缘，追加25对；304候选组/331稳定片段保持，所有group_human_approved=false。不是331条已审导体。
- [直接关系图](runs/m3-direct-pairs-closeout-20261122/reviewed-support-paths.json)：27直接关系涉及47片段，组成20个证据组件。组件不授予整条导体身份、额外成对批准、分支或端点；其余AI邻居不继承批准。
- [十组候选](runs/m3-geometry-ten-groups-20261122-final/generated/candidates.json)均在独立局部坐标中，跨度345–1241、线宽9–15相对像素。R02左端出照片范围，不是物理终点。不能直接拼到全局模型。
- [选择与排除](runs/m3-geometry-ten-groups-20261122-final/selection.json)：20组件中2处已审、5处数值宽度暂停；剩余13处数值候选又被AI排除1处[孔阵列上缘](runs/m3-geometry-ten-groups-20261122-final/semantic-hold.json)，不把亮点行测成独立窄线。选剩余12处中的10处，组件13/15延后未批准。原直接关系均保留。
- 旧[风险诊断](runs/m3-identity-followthrough-20261119/verified-diagnostics/summary.json)及[工作集](runs/m3-identity-followthrough-20261119/source-working-set.json)保持：291局部区间（260新候选/25旧上下文/6局部旧重合）、16筛选恢复候选、20外围风险；不同单位不可相加为金属数。

## 父基线与保护

- [已审范围基线](runs/m3-wide-inventory-20261109/reviewed-baseline.json)绑定LOWER-SAFE工作包；54金属、34已审局部连接、188候选设计孔不变。全幅8区域接受只认可来源清单，不授予672片段身份/几何/连接。
- D009–D012的[限定裁决](DECISIONS.md)保持精确范围；G24的0360/0356为宽金属边缘，不创建独立细导体。G07保持分离项，不由新组件推导连接。
- L01几何G1/短头V2身份I1已审，M3承载/上层ID/物理孔数仍未知，不重审；M1非孔N1/N2/N3/S1保持否定，不推导全局断开。
- source_to_design_transform=null、geometry_adopted=false、net_edges=[]、complete_network=false；skill为LIMITED_TRIAL_V2。六处材料、BF25/返回路径、旧配准拒绝、AA/POLY/CT及其它未知按稳定决定与历史保持。

## 验证与恢复

- [十组核验](runs/m3-geometry-ten-groups-20261122-final/verification.json)：来源哈希、10不同新集合/10决策、正交、已审邻接、父模型SHA通过，并经独立只读检查；不是物理DRC或全局拼接通过。上轮16项相关测试保持，本轮未改源码或旧送审包。
- 十组已审权威build=46968448cede423686f965444d9e6631，仅final/review与实际裁决可用。无final后缀初版及generated/review只是过程；修正新最终spec的十处范围说明，不修改旧生成器以免破坏已审来源哈希。
- 新增continue_pairs保留旧记录，并拒绝重复对/未知片段/已审边缘冲突及有未解释备注的accepted。原apply仍不是通用跨动作冲突求解器；本轮只追加同路径对，不更改边缘分类。
- 当前局部候选重跑：`.venv/bin/python -m silicon_eye.ridge_regularization --spec runs/m3-geometry-ten-groups-20261122-final/pilot-spec.json --output runs/NEW_GEOMETRY_PILOT`。只读原图、拒绝覆写输出。
- [11月22日增量归档](benchmarks/github-checkpoint-2026-11-22/README.md)包含125文件、78唯一数据块、约20.15MB；临时恢复125文件SHA/两套新固定包通过，16项相关测试/Ruff、三套实际裁决及25展示文件/父模型保护检查通过。[验证](benchmarks/github-checkpoint-2026-11-22/verification.json)；依赖11月11日/21日父恢复。提交/远端同步以Git引用为准。

## 唯一下一步

先提交并核验GitHub远端，再推进H03宽母线的真实上下边界。保留已审关系、12处局部形状和所有未知；用宽带二维/双边界证据生成候选，不能继续将单条亮脊当中心扩宽。没有可信候选前不创建新待审批批次；需要新几何判断时仍使用固定确认单。

WIP=1：一个工程事务、一个待审批次。稳定边界见[DECISIONS](DECISIONS.md)，事务历史见[CHANGELOG](docs/history/CHANGELOG.md)，周期记录见[cycle-time-v1](benchmarks/cycle-time-v1/README.md)。原图、旧送审包、旧批准与展示页不覆盖。
