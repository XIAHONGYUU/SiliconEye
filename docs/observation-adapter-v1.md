# AI观察到case／材料卡的最小适配

适配器接收既有统一包请求和一份新AI观察，校验后生成新case、独立适配卡和统一复核包。原case、照片、材料卡、人工事件均不覆盖；不调用模型，不新增人工批准。

```bash
# 新检出先按docs/review-package.md恢复历史证据，再运行：
.venv/bin/python -m silicon_eye.observation_adapter \
  --package benchmarks/review-package-roi2-v1.json \
  --observations benchmarks/agent-adapter/roi2-historical-observations-v1.json \
  --root . --output runs/new-observation-adaptation
```

输出目录须在root内且不存在。打开`review/index.html`查看图文稿；`review/report.md`保留原统一包入口，`case.json`是新版本，`adaptation.json`逐条记录去向、来源和与既有人审的比较。`package-request.json`可用原review-package命令重新导出到另一个新目录。没有外部服务或新依赖。

## 显式映射

| 新观察 | 输出与边界 |
| --- | --- |
| device_exists、same_net、different_net、joined_in_region、terminal_maps_to_conductor候选 | 追加无审核事件的case proposal；使用既有实体类型和完全相同的作用域，不改旧claim |
| 上述关系为unknown | 只写unknown卡；不为适配布尔schema虚构true/false，也不改已有人审 |
| material_identity | 独立材料卡，可为AA/poly/CT；不伪装为电气claim、不覆盖旧已审材料 |
| 原生检查窗口 | 来源与尺寸一致才显示原图裁剪；位置索引橙框只表示观察窗口，不是材料边界 |
| 边界unknown | 不生成多边形、核心/包络或掩膜 |
| 显式candidate多边形 | 仅材料卡显示候选线，必须在原生窗口内，不转为像素真值 |

允许追加任务明确声明且哈希/尺寸验证通过的新原图frame（例如V3任务的AA证据）；不推断它与旧frame已配准，也不替换已有frame。检查task/case ID、原图哈希和尺寸、frame绑定、实体类型、关系作用域、窗口与多边形范围。暂只支持已有实体；新器件发现、重命名、实体归并、隐式坐标换算和作用域猜测均拒绝。器件窗口保留在卡片，不自动替代既有case几何或物理尺寸。

一致候选显示“与既有人审一致”，不升级为confirmed；相反候选显示差异，仍展示已有确认电路。unknown遇到已有确认，保留旧决策；AI候选不进入已确认并网。脚本比较只涉及明确断言/现有闭包，不代替物理复核，范围外差异可能仍需人判断。

统一包新增可选`observation_adaptations`来源列表，读取时重新执行适配推导，并逐项比较卡片和派生case，防止改卡片后脱离输入。原包不提供该字段时行为不变；输入与输出、适配/渲染代码均记录哈希。

适配输入先完整预检，失败不发布输出；新输入目录以暂存目录发布。若后续渲染失败，已发布的有效case/适配输入保留用于诊断，`review/`不留不完整正常包。禁止覆盖已有目录。

## 本次样稿与核查范围

ROI2样稿输入位于`benchmarks/agent-adapter/roi2-historical-observations-v1.json`。这是把既有人工复核结果重新表达为新观察格式，purpose为historical_reexpression；不是新的视觉识别或盲测。材料检查窗口由旧候选包络外加少量留白确定，仅帮助找位置；未把旧包络当精确真值。

本机交付：`runs/roi2-observation-adapter-v3/review/index.html`。10条卡片：6条器件/关系候选、3条材料候选、1条外侧连接未知。保留已批准材料图、宏观叠图、电路图和四端表，额外提供三层原生位置索引。

请主要核查：对象能否对应原图；候选、已有人审和未知是否清楚；电路/材料/来源之间是否容易切换。无需重新逐个确认CT或精确边缘。像素分割、W/L和整网金属点亮不属于这次实现。

## 样稿可用性验收

用户已确认：索引与材料卡容易对应、状态区分清楚、方便核对。[反馈原文与样稿哈希绑定](../benchmarks/agent-adapter/roi2-usability-review-feedback-v1.json)单独保存，不改原样稿或物理审核记录。本阶段可用性验收通过；后续开发节点为同组照片的器件跨层编号视图，金属端口/路径需另有定位证据。
