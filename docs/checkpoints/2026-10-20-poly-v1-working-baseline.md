# POLY v1 工作基线：本轮复核收口

2026-10-20。用户批准Q1、Q2、Q4，并明确Q3右侧为6条MOS。

- [统一复核页](../assets/poly-closeout-v3/index.html)、[有效模型](../../benchmarks/poly-closeout-v3/model-v1.json)、[原话记录](../../benchmarks/poly-closeout-v3/human-review-v1.json)、[基线锁定](../../benchmarks/poly-closeout-v3/stage-acceptance-v1.json)。旧v1/v2保留历史。
- Q3右侧5条AI候选退休，改为6条正交矩形栅。采用AA约束的等间距布局；数量已确认，新生成的精确边界仍未知。其他对象的几何及原生定位不变。
- 共700个POLY材料对象、336个AA对象，676条明确AA目标关系；这些不是器件总数。已声明几何错误与POLY正面积互相交叠均为0。
- 保留5项AA关系未明确验证的警告，详见[报告](../../benchmarks/poly-closeout-v3/report-v1.json)。原生定位估计、照片边界碎片、物理尺度等未知继续保留；工作基线可供CT阶段引用，不宣称全幅材料真值或真实PDK DRC通过。
- 原先灰度五谷推断五个MOS被人工纠正。原始观察未改写，[Agent失败样本](../../benchmarks/poly-closeout-v3/agent-evaluation-v1.json)单独记录，不能把稳定峰谷数当器件数量真值。
- 383项测试、相关Ruff通过；输入哈希、HTML资源、SVG/XML/PNG检查通过。浏览器真实渲染未自动实测。[验证记录](../../benchmarks/poly-closeout-v3/verification-v1.json)。

下一步可在锁定AA/POLY基线上建立CT候选与归属复核，区分AA端、POLY端和未知；不以CT候选自动宣告电连接。本轮未启动CT实现，未封装POLY skill，未提交或推送Git。
