# 同层金属范围扩展：固定批处理入口

针对已有近水平金属，从一个哈希绑定的父包、照片范围、种子及显式设计区间，一次完成范围预检、批量脊线追踪、画布增长、候选接入、保留检查、证据图和固定复核页。无运行时模型调用，也不依赖历史 runs 内的临时脚本。

## 使用

在 silicon-eye 仓库根目录、已有项目虚拟环境中运行；新增可选依赖为 `metal-batch`（SciPy）。当前环境已具备，无需重复安装。

```bash
.venv/bin/python -m silicon_eye.metal_extent_batch \
  --spec configs/metal-extent-batch-m3-replay.json \
  --output runs/my-new-replay --replay
```

示例配置绑定上一轮六线父包，用于软件重放。新生产批次复制配置，填写新的 package_id/date/title、父 manifest 路径及 SHA256、照片来源、frame/layer、bounds、seed_x、targets、groups；指定全新 runs 输出目录，**去掉 `--replay`**。生产页面每组集中裁决，重放页面仅上下文，不重复请求旧判断。

- `bounds` 与 `source_view` 为原生照片裁剪框 `[x0,y0,x1,y1]`，右、下边界不含。
- `seed_x`、`seed_y` 为照片绝对像素坐标，targets 按从上到下排序。
- `native_x` 为候选原生区间，包含端值；追踪采样步长 4px，分组至少保留两个采样点。
- `design_x` 为明确给出的相对设计区间，沿用原导体 y 和宽度；不是自动照片配准或物理长度测量。新增矩形必须接触旧足迹并增加面积。
- `canvas_margin` 默认 20，最小线间距 `minimum_trace_gap_px` 默认 2；算法参数固定并写入 traces.json。
- 新输出目录不得存在，且必须位于项目 runs 内。输入哈希、对象、种子、裁剪框等预检失败时不创建结果；执行阶段失败写 diagnostic.json，不生成成功复核包。

## 输出与边界

- `traces.json`：来源、算法哈希、参数、原生路径、线间距。
- `canvas-{left,right,bottom}/`：确有需要时分别扩画布的独立工作包，保持坐标和旧几何。
- `work/`：候选模型、技术报告及 manifest；`preservation.json`：原对象、锚点、旧 local parts、连接和复核记录保留检查。
- 每组 `*-source.png` 和 `*-design.png`：原图/路径上下对照、旧足迹/新增几何对照。
- `review-spec.json`、`review/index.html`：复用统一固定确认单。
- `timing.json`：各阶段实测、总耗时、配置与入口哈希；人工复核时长为 null，不伪装成零秒。

仅适用于本次验证过的亮脊线、近水平、同帧同层延续。断线、低支持路径、串线、来源变化或越界停止；顶部画布增长尚不支持。没有新增孔、接口、连接、网表，也没有将候选提升为物理真值。算法检查不能保证每条脊线就是目标金属，生产仍需整组复核。正式裁决沿用 review-decision.json 校验归档流程。

## 2026-11-09 实测

最终重放：[计时](../runs/metal-extent-batch-replay-20261109-final/timing.json)、[保留检查](../runs/metal-extent-batch-replay-20261109-final/preservation.json)、[上下文展示页](../runs/metal-extent-batch-replay-20261109-final/review/index.html)。

| 阶段 | 秒 |
| --- | ---: |
| 输入范围/来源预检 | 0.027 |
| 六线追踪 | 1.395 |
| 候选准备 | 0.012 |
| 左右画布扩展及候选接入 | 6.869 |
| 独立保留检查 | 0.002 |
| 两组证据图 | 0.451 |
| 固定复核页 | 0.026 |
| 合计 | **8.785** |

上一轮临时组织流程范围准备至就绪约306秒；本次从**已写好的配置**开始，不能宣称同口径35倍提速。可确认的是：已有配置到整包输出已降为约9秒，重复写脚本/组织工具调用的接入成本被固定入口替代。当前主要程序耗时为三个工作包的技术接入（约78%），识别约16%。本次首次固定入口开发和测试时间不计为未来批次运行时间。

六条路径逐点等于上一轮 traces；全部对象及12处新增矩形与旧批次一致（新包的 part ID、说明和来源路径不同）。保留原始照片和旧包。测试覆盖已知斜率合成脊线、空图和断带拒绝、范围/来源/种子/对象/脱离足迹拒绝、运行失败诊断、禁止覆写、真实六线重放、两组生产裁决及重放免裁决页面。

```bash
.venv/bin/pytest -q tests/test_metal_extent_batch.py \
  tests/test_conductive_left_canvas.py tests/test_conductive_canvas_extension.py
.venv/bin/ruff check silicon_eye/metal_extent_batch.py \
  silicon_eye/ridge_tracing.py tests/test_metal_extent_batch.py
```

这次只验证软件与既有批次一致；不是新增区域独立物理准确率评估。原批用户已在聊天表示通过，正式复核文件归档状态仍按项目原记录保留，本重放不重复要求裁决。
