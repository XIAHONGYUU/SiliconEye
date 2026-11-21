# 当前任务

## 当前目标与授权

用户要求先提交GitHub，再继续推进。已核验11月19日实际导出，G01/G05/G24均通过；本次接续三项结果并保存可恢复证据，不再重问。当前唯一待审批次为五组/25对新的局部来源关系。

## 当前队列

| 项目 | 状态 | 下一步 |
| --- | --- | --- |
| 672来源记录分流 | 完成，原始分类保持 | 不当作672条金属身份 |
| G01/G05/G24实际裁决 | 已归档、接续重放一致 | 两对直接关系 + 两条宽金属边缘记录，不传播批准 |
| 风险局部化 | AI来源分析，未采用 | 保留原始片段、局部区间和身份unknown |
| M3-DIRECT-RELATIONS-20261119-V1 | ready_for_review | 仅判IDENTITY-01～05，每组5对 |

## 最新交付与裁决

- [本批一页摘要](docs/reviews/2026-11-21-m3-source-relations.md) · [五组固定复核页](runs/m3-identity-followthrough-20261119/review/index.html) · [拟审25对](runs/m3-identity-followthrough-20261119/relation-rules.json)。旧G01/G05/G24/G07不在新提案内，不能由相似结构类推批准。
- [三项实际记录](runs/m3-triage-20261111/verified/review-final/review-record.md)：G01确认RIDGE-0005/0006同一局部来源路径；G05确认0017/0019；G24确认0360/0356为宽金属边缘，不建立独立细导体。实际导出2026-11-19，首次交互至导出59.635秒，不是总分析时间。
- [已接续来源状态](runs/m3-identity-followthrough-20261119/reviewed-source-state.json)：304候选分组、仅2对已审直接关系、2条已审边缘记录，所有group_human_approved=false。原333稳定候选排除2条边缘后为331；不是331条已确认导体。
- [风险诊断](runs/m3-identity-followthrough-20261119/verified-diagnostics/summary.json)：231个分叉风险片段局部化为291个来源区间；其中260新来源候选、25旧路径上下文、6局部旧路径重合。62阈值不稳定分为16长度筛选/采样表示原因和46原始亮度不稳定；均不代表物理身份已解决。
- [来源工作集](runs/m3-identity-followthrough-20261119/source-working-set.json)分别保存331稳定片段、16筛选恢复候选、260局部来源区间；单位不同，不能相加为金属数。20外围边缘风险及其它未知继续保留。

## 当前父基线与保护

- [当前已审范围基线](runs/m3-wide-inventory-20261109/reviewed-baseline.json)绑定LOWER-SAFE工作包、扩大批实际裁决和历史父基线，54金属、34已审局部连接、188候选设计孔保持。新分组/区间未接入几何或网表。
- 全幅清单8区域accepted只认可来源清单，不授予672片段的身份/几何/连接。扩大批六组accepted及前两批几何裁决保持，见[DECISIONS.md](DECISIONS.md)。
- L01几何G1、短头V2身份I1已审，M3承载/上层ID/物理孔数仍未知，不重审；四处M1非孔N1/N2/N3/S1保持否定，不推导全局断开。
- source_to_design_transform=null、geometry_adopted=false、net_edges=[]、complete_network=false，skill为LIMITED_TRIAL_V2。六处材料、BF25/返回路径、旧配准拒绝、AA/POLY/CT及其它未知按稳定决定和历史保持。

## GitHub与验证节点

- [本增量证据恢复说明](benchmarks/github-checkpoint-2026-11-21/README.md) · [核验记录](benchmarks/github-checkpoint-2026-11-21/verification.json)。99文件按内容去重70块，压缩约6.83MB；临时恢复99文件SHA和2套最终固定包通过。克隆先恢复[前一节点](benchmarks/github-checkpoint-2026-11-11/README.md)，再恢复本增量，runs链接才可用。
- 本次8项相关测试、Ruff、当前来源/实际裁决/父包哈希、三项应用精确重放和规则成员互斥检查通过。README/site25文件对提交前HEAD保持，未发布gh-pages。
- 只读代码审查未发现当前三项输入的提交阻塞。source_review_apply尚无通用的关系/边缘交叉规则拒绝；当前输入和新25对已单独验证不与已审边缘重合，不能把此检查称为通用冲突解决。
- GitHub提交/同步以Git引用为准；本页不写自引用commit SHA。历史总回归的旧README哈希失败保持，不宣称本次运行全套。周期记录见[cycle-time-v1](benchmarks/cycle-time-v1/README.md)。

## 唯一下一步

在五组固定页判断IDENTITY-01～05并导出review-decision.json。每组只接受明确列出的5对直接关系；有错误备注具体G编号，不清楚可保持uncertain。收到实际导出后校验归档，再按具体裁决接续；不得让整条AI候选链变成人审身份，或升级为电气连接。等待时不产生依赖此裁决的新决定。

## 节奏与恢复

- WIP=1：一个工程事务、一个待审批批次；默认周二/周五各30分钟复核可按用户安排调整。稳定边界见[DECISIONS](DECISIONS.md)，历史变化见[CHANGELOG](docs/history/CHANGELOG.md)。
- 本轮有效旧分流使用runs/m3-triage-20261111/verified/，有效后续诊断使用runs/m3-identity-followthrough-20261119/verified-diagnostics/；其余过程输出仅为历史。
- 导出后用 `.venv/bin/python -m silicon_eye.review_sheet check --package runs/m3-identity-followthrough-20261119/review --decision /实际路径/review-decision.json --archive`。不改原图、旧送审包或展示页。
