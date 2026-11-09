# 决策与生效边界

本文件保存跨轮稳定的决定、未决项和流程规则；实时队列只放在 `CURRENT_TASK.md`。历史原文和旧“下一步”在 `docs/history/`，不能覆盖本文件或当前入口。

状态：`active` 生效；`pending_review` 等待人审；`unknown` 未决；`superseded` 已被替代。

## D001 当前工作基线

- 状态：`active`
- 决定：工程主线父基线为 `w34-left-m2-reviewed-v2`；54 个金属对象（M1=11、M2=18、M3=25），34 条已审局部连接，188 个候选设计孔。
- 权威来源：[working-baseline.json](benchmarks/w34-left-m2-reviewed-v2/working-baseline.json)、[接续请求](benchmarks/w34-left-m2-v1/next-request.json)
- 边界：计数是当前工作模型计数，不等于全芯片完成、物理孔数或完整网表。

## D002 L01 与 V2 身份

- 状态：`active`（几何/身份已审；承载未知）
- 决定：L01 几何 G1 与短头 V2 身份 I1 已由实际确认单通过归档；I1 的承载、上层金属 ID、物理孔数仍未知；未建新 VIA 或连接。
- 权威来源：[身份记录](benchmarks/w34-left-m2-reviewed-v2/V2-identity-reviewed.json)、[确认记录](docs/assets/w34-left-m2-v1/review/review-record.md)
- 边界：身份通过不等于承载通过；不得用设计图重叠、行号或跨帧邻近直接指定 M3。

## D003 四个 M1 非孔搜索目标

- 状态：`active`
- 决定：`W34-END-N1`、`N2`、`N3`、`S1` 均是已拒绝的 M1 搜索目标；不重审、不建孔。
- 权威来源：[identity-closeout.json](benchmarks/w34-terminal-v1-reviewed-v2/identity-closeout.json)
- 边界：不能由四个负例推导附近无孔或全局断开。

## D004 当前 M3 批量外延

- 状态：`pending_review`
- 决定：`C-M3-M01` 至 `C-M3-M06` 的左右 12 处外延是候选；`M3-BATCH-EXTENTS-20261109-V1` 的 WEST/EAST/Q1 归档前不采用，旧基线继续生效。
- 权威来源：[复核摘要](benchmarks/batch-production-v1/review-digest.md)、[本轮报告](docs/reviews/2026-11-09-batch-production.md)
- 边界：不新增导体身份、孔、接口或连接；两端是范围出口，不是物理终点。

## D005 证据与输出资格

- 状态：`active`
- 决定：当前 `source_to_design_transform=null`、`geometry_adopted=false`、`net_edges=[]`、`complete_network=false`；skill 仍为 `LIMITED_TRIAL_V2`；自动网表导出禁止。
- 权威来源：[导体统一协议](docs/architecture/conductive-workflow-contract-v1.md)、[能力限定](docs/architecture/conductive-skill-qualification-v1.md)
- 边界：软件测试通过、页面构建成功或口头“通过”都不等于物理事实或共同几何采用。

## D006 仍未决的范围

- 状态：`unknown`
- 决定：六处材料未知、BF25 与返回路径、旧配准拒绝项、AA/POLY/CT 保护边界，以及其它局部承载裁决继续按历史原文生效；不在本文件重解释。
- 权威来源：[上阶段入口原文](docs/history/current-task-before-2026-11-06-algorithm-pilot.md)
- 边界：历史文件中的“下一步”不是当前任务指令。

## D007 工作流节奏（2026-11-09 起）

- 状态：`active`
- 决定：
  - `CURRENT_TASK.md` 保持单页；稳定规则进本文件；事务变化一行记入 `docs/history/CHANGELOG.md`，不再每轮生成完整入口快照。
  - 双车道、WIP=1：一个工程事务 + 一个待审批次；等待人审时可做不依赖裁决的安全工作，但不得 adoption。
  - 每批记录周期到 `benchmarks/cycle-time-v1/records/`；固定确认页自动记录首次交互/导出时间。
  - 默认复核窗口为每周二、周五各 30 分钟，可按用户安排调整；批次提前准备一页摘要。
- 边界：流程提速不改变证据等级；未归档裁决前，候选不能写成已批准。
