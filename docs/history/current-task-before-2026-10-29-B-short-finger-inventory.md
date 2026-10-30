# 当前入口归档

来源：CURRENT_TASK.md；日期：2026-10-29；以下为 B 短指清点前的完整原文。

# 当前任务

## 当前目标、状态与授权

同一走廊的 A 右侧／B 左侧 M1 横向主干已补查，在原工作范围内建立两块正交局部几何，仍属于同一个 `C-M1-SPINE`。当前阶段没有新的人审问题；下一步沿 B 左支清点向下短指及与下方平行条的隔离，再补几何和新接口来源。

- 只修改一条 M1 候选外形，保留原生/设计骨架与宽度参数、30 条 M2/M3、11 条已审接口和全部 46 个设计候选孔中心。当前金属 31 条（M1=1/M2=8/M3=22），V1 2 组、V2 9 组。未新增接口或 `net_edges`。
- A/B 的 V1 身份及接 `RT-M2-R01` 已由用户原话“都有”确认，直接继承；新 M1 几何、孔数和精确原生落点未获人审批准。不重问 A/B 或其它已审承载。
- 工作规则坐标画布仍为 780×1240；原生图坐标独立，`source_to_design_transform=null`。物理孔数、工艺尺寸、完整网络未知。金属/VIA skill 仍 `LIMITED_TRIAL_V2`。
- README、site、gh-pages 受保护；本轮仅本地开发，不发布。main 起点 66a450a（2026-10-28 已推送），2026-10-29 的工作均尚未提交。

## 当前验收入口与证据

[横向分支复核页](docs/assets/corridor-m1-horizontal-branches-v1/index.html) · [五层切换工作页](docs/assets/corridor-m1-horizontal-branches-v1/work/index.html) · [前后对比](docs/assets/corridor-m1-horizontal-branches-v1/before-after.png) · [来源清单](benchmarks/corridor-m1-horizontal-branches-v1/source-ledger.json) · [当前状态](benchmarks/corridor-m1-horizontal-branches-v1/source-review-state.json) · [验证](benchmarks/corridor-m1-horizontal-branches-v1/verification.json) · [本轮报告](docs/reviews/2026-10-29-corridor-M1-horizontal-branches.md) · [前入口完整归档](docs/history/current-task-before-2026-10-29-M1-horizontal-branches.md)。

- A-RIGHT 来源约 (3143,1960) → (3670,1949)，在 x3670 出工作范围，宽图中继续向右到约 x5175 下拐；B-LEFT 约 (3155,2780) → (2940,2788)，在 x2940 出范围，宽图中继续向左到约 x1682 下拐。两处都不是物理终点，外侧回路未建模。
- A/B 主干在本轮范围内未见明显断口，是 AI 来源观察，不升级为精密边界或人工几何验收。B 横带在约原生 y2780，旧近似骨架锚点 y2800 保持；都在已审 B 站点内，不据此平移孔或伪造精确投影。
- 两个局部块分别为 [179,264,655,276]、[12,1011,191,1029]，均与原骨架正面积连接，合并后有效正交多边形并覆盖原占用。主干宽度为规则候选，不是物理量测。
- A 内侧平行短条、B 下方短指/两条横条、外侧返回及其它疑似 V1 都未自动并入。没有用亮度峰值、形态相似或正向设计常识补连接。
- 复用 `local_parts`，新增可选的通用局部来源账本质量检查：原图/层次、来源范围与主方向、设计矩形逐块对应，禁止遗漏、矛盾及接续时丢弃绑定。未增加案例专用生产脚本。
- 本轮 115 项相关软件测试通过（10 项新局部来源/修订用例），Ruff及静态资源/脚本语法通过；原物件/裁决/孔中心保护、11 组完整候选阵列包围与精确接续通过。4 张无标记裁片逐像素一致，PNG 已目视；浏览器交互未实测。

## 必须继承的来源裁决与未知

- [A/B 原话](benchmarks/corridor-m1-v1-reviewed-v2/human-review.json)绑定原 M1 来源框 A=[3125,1930,3175,2010]、B=[3130,2775,3180,2845]及 R01。框是来源站点，不是实测孔组外框；每组 2×1 仅为设计假设。其它 R02 的 V1 未查清，不声明无孔。
- 原 9 个 V2：R01/R02 上端接 RT-M3-UP，下端接 RT-M3-DOWN；N1→C-M3-L01，03→T01，04→T02，05→E1，06→E2。05/06 本处 M2 不连续，不推导全局异网。08 无明确 V2 是 AI 范围内观察，不是物理不存在。
- C06 原生框 [2933,2140,2977,2175] 跨原走廊 x2940 左界，保留原框及人审绑定，不裁切或扩大范围掩盖。三条弱 M3 不补建仍是 AI 处置，不是人审不存在。
- 外方阵宏观搜索只作定位，ORB 保留点 P95约129px及首版边界触带结果均已拒绝；修正版约2.5px外部参照残差不代表内部孔精度。不能复活旧九对 V1/V2 同孔拟合或4.52px残差。V1从M1侧识别，V2从M2侧识别。
- 原 M1 补充清单仅竖段，原 30 条来源清单/映射保持。新横向段由独立局部来源账本补充；原 M2/V2/M3 覆盖核对仍限定原范围，不声称五层穷尽覆盖。
- 其它区域的 A={T3,L2}/B={T1,L4}、H1/H2 局部隔离、U1/U2同M1、U1/U3经V1接N2、U3已审CT→AA环端子路径及精确范围按[前入口归档](docs/history/current-task-before-2026-10-29-M1-horizontal-branches.md)保留，不转移到本走廊。
- 唯一材料快照为 [joint-work-layer-v5](configs/joint-work-layer-v5.json)，AA334/POLY696/CT10287；导体规范注册表仍为[原33记录模型](docs/assets/conductive-stack-v2/model.json)。六处材料未知 AA-F01951、AA-F01952、材料H1/H2、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS 保持。
- 新候选不等于规范注册表采用或全图配准；`net_edges=[]`、`geometry_adopted=false`、`complete_network=false`、自动网络导出禁止。真实工艺/尺度/极性/WL/阻值和完整网表未知。

## 唯一下一步与恢复

沿 B 左支建立向下 M1 短指清单，区分接上横条、接下方平行条或证据不清；先观察后补几何。若出现新的接口身份/承载歧义，再给宽图和较大邻域原图集中裁决；不重复审批 A/B，不要求逐孔计数。不把工作范围出口当终端，不跨照片凭像素直接投影。

```bash
# 保持31条金属、11条接口及46个候选孔中心；输出须为新目录
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/corridor-m1-horizontal-branches-v1/next-request.json --output runs/新的M1横向分支接续目录
# 仅原M2/V2/M3清单核对，不能升级为五层覆盖率
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的覆盖核对目录
```

M2/M3原图及新M1无标记图按哈希复用，新增标记图独立保存。此前重复资源首次构建备份在 runs/corridor-m1-v1-pre-resource-reuse-v2；其它V1分支从 benchmarks/v1-new-short-branch-reviewed-v2/next-request.json 恢复，旧中样从 benchmarks/m1-local-tab-v1/work-next.json 恢复。不得自动重建README/site或发布gh-pages。
