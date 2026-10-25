# 从一次错误承载，改进质量门

**问题：AI看到了孔，却把孔组接到了错误的金属。** 这是已发生并留档的失败，不是为演示合成的故障。

原候选把IT1-V1-A接到窄IT1-M2-A。旧模型用一个小代理方框表示孔组，局部包围检查可以通过，却没有约束真实孔组的完整范围。用户指出：圈内为六孔，承载应为宽IT1-M2-B。

## 判断与修订

- 领域判断：先核六孔组的整体占用，再确定承载，不能只看一个代理框是否落在交叠区。
- 已审结论：该V1孔组把M1环片段连接到宽M2-B；历史稳定ID后缀A不代表承载A。
- 工程修订：保留观察数量、生成完整规则孔组，检查各孔及整组的上下金属承载，并绑定原生来源与实际人工更正。
- 保留未知：六孔数量和承载已审；2×3、孔径、间距和具体B边界仍候选，A/B同层连续性未知。

[线上纠错案例](https://xiahongyuu.github.io/SiliconEye/#quality)同时展示来源M1/M2照片和旧/修正模型。照片分别保留原生坐标，规则图不是配准后的照片投影。

## 证据链

| 环节 | 原记录 |
| --- | --- |
| 原送审及错误候选 | [原模型](../assets/conductive-workflow-trial-v1/final-independent/model.json) |
| 人工更正原文与准确范围 | [承载裁决](../../benchmarks/metal-independent-q1-correction-v2/q1-human-carrier-correction-scoped-v3.json) |
| 原错误与纠正次数 | [评测记录](../../benchmarks/metal-independent-q1-correction-v2/evaluation-v3.json) |
| 修正几何与资格 | [修正模型](../assets/metal-independent-q1-reviewed-v3/model.json) |
| 后续完整孔组/来源/承载质量契约 | [统一协议](../architecture/conductive-workflow-contract-v1.md) |

这能证明一次错误的发现、纠正及规则改进路径。它不能单独证明其他孔组都正确，亦不意味着精确几何已获得人工批准。

## 结果如何量化

[八任务基准](../../benchmarks/portfolio-quality-v1/README.md)将历史记录、机器评分入口和人工rubric整理到一起。公开结果卡分开给出：AA三项历史验收、两条展示用失败记录、两个机器评分任务和未测项。不存在全项目统一准确率，未记录的人审成本不填0。
