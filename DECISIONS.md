# 决策与生效边界

本文件保存跨轮稳定的决定、未决项和流程规则；实时队列只放在 `CURRENT_TASK.md`。历史原文和旧“下一步”在 `docs/history/`，不能覆盖本文件或当前入口。

状态：`active` 生效；`pending_review` 等待人审；`unknown` 未决；`superseded` 已被替代。

## D001 当前工作基线

- 状态：`active`
- 决定：当前已审几何来源为 `runs/m3-wide-inventory-20261109/reviewed-baseline.json`，绑定扩大批 LOWER-SAFE 工作包、扩大批裁决和之前的已审合并基线；历史父基线 `w34-left-m2-reviewed-v2` 继续保留。当前计数仍为 54 个金属对象（M1=11、M2=18、M3=25），34 条已审局部连接，188 个候选设计孔。
- 权威来源：[当前已审范围基线](runs/m3-wide-inventory-20261109/reviewed-baseline.json)、[历史父基线](benchmarks/w34-left-m2-reviewed-v2/working-baseline.json)、[接续请求](benchmarks/w34-left-m2-v1/next-request.json)
- 边界：计数是当前工作模型计数，不等于全芯片完成、物理孔数或完整网表；全幅 M3 来源清单的 accepted 只批准清单，不新增几何、身份或连接。

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

- 状态：`accepted`
- 决定：`C-M3-M01` 至 `C-M3-M06` 的左右 12 处外延已由 `M3-BATCH-EXTENTS-20261109-V1` 实际导出并归档 accepted；后续已合并入当前已审范围基线。旧 54 金属、34 条连接和 188 个候选孔保持。
- 权威来源：[第一批复核记录](runs/batch-production-20261109/review/review-record.md)、[复核摘要](benchmarks/batch-production-v1/review-digest.md)、[本轮报告](docs/reviews/2026-11-09-batch-production.md)
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

## D008 全幅 M3 来源清单

- 状态：`accepted`
- 决定：`M3-FULL-INVENTORY-20261109-V1` 的 8 个区域全部 accepted；全幅 5712×4284 共 672 个亮脊线片段，其中 30 个旧路径上下文、642 个未分配或部分新增。只认可来源片段清单，不批准身份、端点、几何、连接或物理孔数。
- 权威来源：[复核记录](runs/m3-wide-inventory-20261109/final/review/review-record.md)、[复核决定](runs/m3-wide-inventory-20261109/final/review/review-decision.json)、[本轮报告](docs/reviews/2026-11-09-m3-full-inventory.md)
- 边界：片段数不是导体数；区域级通过不是 672 条逐项真值验证；不得直接把清单塞入 54 金属模型或网表。

## 2026-11-09 批量范围裁决归档

- M3-BATCH-EXTENTS-20261109-V1 的 WEST/EAST/Q1 与 M3-TOP-EAST-20261109-V1 的 EAST 已由实际导出文件校验归档，分别见 [第一批](runs/batch-production-20261109/review/review-record.md)、[第二批](runs/batch-production-round2-20261109/package-final/review/review-record.md)。仅接受声明的相对范围几何，不升级精确投影/物理端点/跨层连接。
- 两批已审parts精确合并至 [范围工作基线](runs/batch-expanded-20261109/reviewed-baseline.json)；历史接口/未知不变。随后 M3-EXPANDED-20261109-V1 六组已 accepted，详见下节。

## 2026-11-09 扩大批实际归档与全幅边界

- M3-EXPANDED-20261109-V1六组均accepted，实际导出已校验归档；LOWER身份检查随组接受，[记录](runs/batch-expanded-20261109/review-final/review-record.md)。精确投影、物理端点、跨层承载和完整网表不在批准范围。
- 最新已审几何来源为[基线绑定](runs/m3-wide-inventory-20261109/reviewed-baseline.json)。新全幅M3清查只生成原生片段清单，不新增金属身份或规则几何；不能把672片段计为672导体。
