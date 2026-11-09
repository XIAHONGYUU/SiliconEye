# 第二轮正常批处理：上方六条M3右侧延续

用户授权正常推进一轮，主要评估等待时间。独立沿用原父包，不采用上一批尚未归档的新增几何。使用现有固定入口，未修改算法或工作流代码。

## 一页复核摘要

- 变化：C-M3-T01–T06 各追加右侧范围 x3670–4500，共6处；原生追踪范围 x2900–4500。旧54个金属、接口、已审连接、锚点和旧足迹保持，无新孔/连接。
- [集中复核页](../../runs/batch-production-round2-20261109/package-final/review/index.html)：仅 EAST 一组，建议预留1–2分钟（估计，尚未实测）。
- [原图与路径](../../runs/batch-production-round2-20261109/package-final/EAST-source.png) · [规则几何](../../runs/batch-production-round2-20261109/package-final/EAST-design.png)。
- AI建议：可送审。逐图检查六条路径沿可见亮线延续，行序未交换；最小线间距15px。新增设计长度是相对候选，范围出口不是物理终点；不据此判断跨层承载。
- [保留检查](../../runs/batch-production-round2-20261109/package-final/preservation.json) PASS；[技术报告](../../runs/batch-production-round2-20261109/package-final/work/report.json)通过；固定页面manifest与证据哈希校验通过。未做浏览器交互测试，也没有物理准确率真值。

## 实测耗时

| 阶段 | 秒 |
| --- | ---: |
| 选范围、查看照片、准备配置 | 39.66 |
| 首次运行、定位种子问题、修正重跑、取得页面 | 47.14 |
| 结果图/保留记录/页面包校验与交接准备 | 62.99 |
| 范围准备至交付检查点 | **149.79** |

成功程序运行 **5.17秒**：追踪0.55秒，画布与候选接入4.28秒，证据与页面0.31秒。这些程序时长已经包含在上表，不重复相加。

首次运行因T03旧锚点y1851亮脊支持不足而拒绝；按x2940原图局部峰值重新选择种子y1804/1828/1848/1867/1887/1902，原锚点不改。拒绝耗时0.55秒，[失败诊断](../../runs/batch-production-round2-20261109/package/diagnostic.json)和[种子修正](../../runs/batch-production-round2-20261109/seed-correction.json)保留。另有一次误用系统Python缺Pillow，立即改回项目虚拟环境，其耗时包含范围准备。

判断：本轮六线一组在约2.5分钟准备完毕，已比原先10–15分钟才交三四条线更适合作为正常节奏，但样本/范围不同，不报严格倍数。主要等待仍在选范围、检查与一次返工，纯程序只需约5秒；当前不值得优先继续优化算法毫秒数。下一批应先从原图确定种子，避免直接照搬近似旧锚点。

初始读取任务入口在计时前，未精确记录；以上不是从用户发消息起的完整响应时长。人工复核/归档仍未发生。最终聊天交付晚于此检查点。

[完整计时](../../runs/batch-production-round2-20261109/wall-timing.json) · [周期记录](../../benchmarks/cycle-time-v1/records/2026-11-09-batch-production-round2.json) · [配置](../../configs/metal-extent-batch-m3-top-east.json)。

复现命令（输出目录必须全新）：

```bash
.venv/bin/python -m silicon_eye.metal_extent_batch --spec configs/metal-extent-batch-m3-top-east.json --output runs/m3-top-east-new
```
