# Archived CURRENT_TASK.md

Source: CURRENT_TASK.md; archived 2026-10-18 before layer-reconstruction direction change. Original bytes follow.

# 当前任务

## 当前目标与授权

本轮目标：从Q1/Q2真实共栅入口追踪并点亮现有照片内可识别分支。本轮已识别分支的点亮及端点类别复核完成，汇总为v33；不等同于证明完整物理网无遗漏。

- 只用现有八层照片，原图data/不可修改；派生图runs/，原生像素单位。没有额外照片，不要求用户补拍。
- 在内层silicon-eye工作，使用.venv。已授权本机开发、复核、金属追踪；用户已授权将现有开发、今天经验与产物提交并推送 GitHub；没有付费/外部视觉服务或平台建设授权。
- 最近已推送main=2d264db8aa4b9b4dd243e5c5606ab3e916dc57aa；本次提交覆盖之后的工具、case、阶段2/3和金属追踪修改；新提交状态以 Git 日志和远端核验为准。
- 用户要求追踪完成后统一复盘；本轮不另建案例专用生产脚本，不启动全面架构扩展。

## 最新结果与唯一下一步

**唯一下一步：2026-10-18 按[金属点亮流程 v1](docs/metal-tracing-workflow-v1.md)重走同一组照片，保存首次结果与纠正记录，再评估封装局部金属追踪 skill。** 今天复盘已固化，不提前创建 skill；同样本重走是开发回归，不是独立盲测。当前不再重复询问已确认的六处CT或B电极归属。

- 最终五项图稿已冻结为[可恢复证据归档](benchmarks/evidence/README.md)，历史中间 runs 不在本次归档范围。
- [v33复核说明](docs/roi2-gate-network-reviewed-v33.md)
- [统一静态入口](runs/roi2-gate-network-reviewed-v33/index.html)
- [金属总览](runs/roi2-gate-network-reviewed-v33/gate-network-metal-overview.png)与[连接摘要](runs/roi2-gate-network-reviewed-v33/gate-network-connection-summary.png)
- [当前伴随拓扑v33](benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v33.json)、[覆盖记录](benchmarks/metal-extension/roi2-gate-network-coverage-v33.json)
- [W1经CT接AA裁决](benchmarks/metal-extension/roi2-W1-CT-AA-review-v1.json)与[已审宽图](runs/roi2-gate-network-reviewed-v33/W1-CT-AA-reviewed.png)

## 本轮仍生效的物理事实

- 照片为同芯片逐层去层显微镜拍屏，各层5712×4284，手拍有变形，各层坐标独立；鼠标拟合不是整片配准。
- Q1/Q2为相邻MOS栅指，poly局部不相连，经M1共栅。中间扩散共享源漏，体端共用，外侧扩散是否共接未知。N/P、S/D、W/L、10px/μm未确定。
- 用户接受C/D局部显示并否决旧U3 gate入口，现工作入口为右侧长M2约(2315,2985..2990)。局部显示/导体身份不批准精确像素边界或全局变换。
- T→N04/M3；N04接J1、T、J2、J3、J4五处M2，各经V1下接五根M1长竖指，再经CT到AA扩散端，均已审。
- S1/S2两V2均接L01/M3右端向上短竖段；L01左端接W/M2；W下端经V1到W1短M1；W1经CT接AA扩散端，均已审。W1不自动并相邻M1横线。
- B落最下方M1长横线，右转入梳齿绿色母线/横齿；绿色M1/M2/M3经V1/V2同电极已审，橙色对极隔离。精确掩码及过孔数量未知。
- 六份AA接入记录只表示观察位置，不等于六个器件或六个隔离扩散区；不把整AA矩形并网，不穿过沟道/电容介质扩网。

## 历史物理子图与纠偏边界

- 旧gate→A→电容P1入口错误，gate归属挂起；原A/C、E/F/G等已审物理接口保留，不能借其恢复旧gate归属。旧E=V1、F/G直接接M1均已否决。
- 旧R2_CAP_01为MOM：P1=G/H侧，H在J向左，接中间纯竖K/M2→L1/M1；P2=橙色梳齿及右侧母线，两端隔离。旧ID带P2但实际属于P1的历史记录保留别名纠偏。
- 用户已确认旧MOM P1在现照片内无其他出口、A—C中段无M2，456接下方MOS扩散端；不重复询问，也不扩展为全芯片无V3。
- 新B梳齿电极不自动等同旧R2_CAP_01，不分配容量/单元数量。V3旧案的端子裁决不借用于本轮。

## 未决事项与验证限制

- 未识别接口、未验收M3/M4配准区域、照片外延伸仍未知；本轮无足够证据新增M4接口。原始像素精确掩码、器件参数和其他网尚未完成。
- 通用case v14仍含旧gate→A/电容关系，不能作为当前整网输出；以v33伴随拓扑为准。通用case导出尚待适配，本轮未改case或生产代码。
- 本轮检查源哈希、确认连接/材料边、对极隔离和图稿，不以脚本PASS替代物理结论。本次提交前重跑248项测试全部通过，相关新增/修改代码Ruff通过；均不代表物理真值。

## 保留的开发工作、恢复入口

- observation/evaluation、adapter/cards、device_index、terminal_highlight、review_package及测试纳入本次提交，保留历史人工判断及其边界。适配可用性、编号图已审，Q1/Q2 ID保持。
- [观察格式](docs/agent-observations-v1.md)、[适配说明](docs/observation-adapter-v1.md)、[顶层架构](docs/architecture/photo-stack-workflow-v1.md)、[历史基准种子](benchmarks/agent-eval/index.json)。参与开发的数据不是盲测成绩。
- 统一复核包：`.venv/bin/silicon-eye annotate review-package --spec benchmarks/review-package-roi2-v1.json --root . -o 新目录`，见[说明](docs/review-package.md)。通用工具不自动追踪整网；PhotoStack、物理导体图、skill化仍未实现。
- 旧9项证据恢复：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/roi2-reviewed-inputs-v1.zip --root .`，不是全部runs归档。
- 浏览器预览曾被安全策略拒绝，不用CDP绕过；静态图用绝对路径交付。

## 按需历史

- [v33整合前完整入口](docs/history/current-task-before-2026-10-17-v33-reviewed-network.md)：原文完整保留，含逐轮配准/追踪依据及未提交开发状态。
- [gate入口纠偏前](docs/history/current-task-before-2026-10-17-gate-entry-correction.md)、[G/H端口更正前](docs/history/current-task-through-2026-10-17-G-H-port-resolution.md)。
- 更早历史入口和裁决可由完整归档继续追溯；原始证据与历史批准不覆盖。
