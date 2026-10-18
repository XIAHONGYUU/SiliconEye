# 区域分类复核 v3：追加 C03

2026-10-18。用户确认：“C03这一排结构是属于金属电容”。此前 21 项人审记录保持，当前汇总为 22 个区域条目，不是 22 个器件。

- [C03 已审八层切换页](assets/region-skill-validation-reviewed-v2/index.html)。
- [完整区域记录 v3](../benchmarks/region-planning/eight-photo-regions-reviewed-v3.json)。
- [C03 人审原话](../benchmarks/region-skill-validation-v1/C03-human-review-v1.json)与[已审局部记录](../benchmarks/region-skill-validation-v1/reviewed-plan-v2.json)。
- [此前 21 项区域与裁决](region-planning-reviewed-v2.md)。
- [首次候选及流程验证](region-skill-validation-v1.md)，原始候选和验证快照不覆盖。

| 对象 | 当前确认 | 保留未知 |
| --- | --- | --- |
| SE_RGN_C03 上边缘一排结构 | 金属电容类别 | MIM/MOM 子类型、单元数量、容量、两极、精确掩膜、跨层对应、端口和网络 |

首次 AI 的 CAP 区域分类与本次人工判断一致；这里只是一个同芯片、已见照片开发样本，不能给出泛化准确率。软件检查仍不替代物理判断。

区域规划 skill 已在当前会话可用列表出现。用户可继续使用同页切层复核；自动浏览器交互仍因 file: 策略未实测，不扩大用户此次类别确认。

区域规划阶段的本轮类别复核已闭合。用户随后明确分层抽取面向完整视野，见[全幅方向 v3](architecture/photo-stack-workflow-v3.md)。M05/Q1Q2 仅作观察/评测或抽样位置，不作为实施边界；不重复询问 C03 类别。
