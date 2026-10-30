# 当前任务

## 当前目标与状态

**Q1“几何合理，无明显漏段”、Q2“几何合理，无明显遗漏”已保存。固定M1原生范围[300,1870,830,2820]作为定性工作几何基线收口，无本批待审批。下一步先建立W3/W4邻近M2的连续来源清单。**

- [最新已审入口](docs/assets/west-m1-reviewed-v12/index.html) · [五层切换/原图](docs/assets/west-m1-reviewed-v12/work/index.html) · [工作基线](benchmarks/west-m1-reviewed-v12/working-baseline.json) · [人审原话](benchmarks/west-m1-reviewed-v12/human-review.json)。
- 唯一几何恢复：[next-request](benchmarks/west-m1-reviewed-v12/next-request.json)；[状态](benchmarks/west-m1-reviewed-v12/source-review-state.json)、[报告](docs/reviews/2026-10-30-west-m1-reviewed-v12.md)、[验证](benchmarks/west-m1-reviewed-v12/verification.json)。
- 声明清单12/12已有对应几何；本轮Q1/Q2新审L03–L12共10片段，L01/L02是不变上下文，不扩为整个C-M1-SPINE的全范围批准。[准确批准组件](benchmarks/west-m1-reviewed-v12/reviewed-fragments.json) · [已审覆盖清单](benchmarks/west-m1-reviewed-v12/scoped-M1-coverage-reviewed.json)。
- 当前46金属、30已审局部接口、179设计候选孔；本轮审批接续，整个工作模型和全部几何、原生锚点、旧裁决、孔边界/中心精确保持。原点/尺度/视口[-2700,0,780,1440]不变，无新VIA/网边。
- L09/L10分开，L11主干向下出口、L12左段短回折的本范围表达获通过；出界不是物理终点。定性无明显遗漏不等于全照片穷尽、精密尺寸、PDK DRC或全网完成。
- 旧V1/V2人审继续按其原始范围生效，见前入口归档。本轮不改旧送审answer=null、AI候选字段或原生证据；冻结提案的pending描述仅为历史，不再重问Q1/Q2。
- README/site/gh-pages保持；10月29–30日成果纳入本次归档提交，远端同步以main与origin/main的实时核对为准。skill仍LIMITED_TRIAL_V2；geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。

## 唯一下一步：M2连续来源清单→几何对应→接口未知

[下一范围计划](benchmarks/west-m1-reviewed-v12/next-scope-plan.json)，尚未产生新的M2来源观察/几何/覆盖结果。

- 选择W3/W4邻近的本层M2原生搜索范围[280,1870,850,2840]，以既有W3/W4为锚定上下文；不是把M1边界投影到M2。
- 先清点本范围全部可见M2片段、端点和细支路，逐项对应当前模型或标记缺失/部分/不确定及出界；不先生成零散新接口问题。
- 再用来源绑定的补建/外延事务补缺；旧46金属的ID/锚点、179孔和30裁决保持。出现新身份/连接歧义时才送审，旧W3/W4的8处V1/V2不重问。
- M3的B-U/B-D只作已审承载上下文；所有M3细走线及高层金属另建连续范围清单，不暗示已覆盖。
- 工作接续必须同时读当前next-request、已审基线和准确组件清单；修订已审组件要显式列变化及前后比较，不将本次批准复制给新几何。

## 本轮验收接续与验证

- 批准绑定原送审请求、Q1/Q2范围、原图及规则图、工作模型和来源清单，未新造人审。Q1只审L03–L08，Q2只审L09–L12；精确范围不含全C-M1-SPINE或新连接。
- v12审批接续时无程序/几何修改；提交模型→收口模型→当前恢复全内容/模型哈希精确相同，30裁决/179孔保持，未重跑上轮49项及固定回归31项，证据仍在[上一验证](benchmarks/west-m1-coverage-v11/verification.json)和[固定回归](benchmarks/west-m1-coverage-v11/fixed-regression.json)。
- 来源/人审/组件绑定、旧冻结包、链接/脚本及展示保护核查见verification；浏览器交互未实测。定性几何验收通过不改来源阵列精密资格、物理孔数或正式GDS采用状态。
- 本次归档前另跑252项相关测试及31项固定回归，均通过；模型精确重放、证据引用与展示保护检查通过。[提交前检查](docs/reviews/2026-10-30-github-checkpoint.md)。这不是新AI识图评测。
- README/site的25文件及gh-pages引用保持。[前入口全文](docs/history/current-task-before-2026-10-30-west-m1-reviewed-v12.md)完整归档；其引用的历史VIA人审和全部未知继续生效。

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
# 当前唯一几何恢复入口，输出用新目录。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/west-m1-reviewed-v12/next-request.json --output runs/新的已审M1接续目录
```

固定工程回归沿用scripts/check_conductive_regression.py，按实际变更决定重跑；不当作新AI识图评测。旧范围入口不扩大到本侧五层覆盖率。不得自动重建README/site或发布gh-pages。
