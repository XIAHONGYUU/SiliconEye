# M1小样Q1–Q3已审：端部补条与左环加宽

用户确认Q1位置、长度及隔离准确；Q2基本形状合理，但M1应覆盖CT，端部缺两段短横线；Q3上下横线合理，左侧M1应更粗。原文保存在[人审记录](../../benchmarks/m1-geometry-pilot-reviewed-v2/human-review-v1.json)。本次记录并实施已有裁决，不重新询问Q1–Q3。

[打开已审修订页](../assets/m1-geometry-pilot-reviewed-v2/index.html)：保留原图/观察线、AA/POLY/CT/M1切层、全图定位与修订前图；新增裁决摘要，无待重复审批清单。[初版](2026-10-21-m1-geometry-pilot.md)及其输入/产物保留历史，不覆盖。

## 局部修订

| 范围 | 结果 | 批准和候选边界 |
| --- | --- | --- |
| P01–P05、P09 | 六条竖向金属的记录和几何完全不动 | 用户确认所示位置、长度和隔离；不自动变成原图逐像素边界批准 |
| P06外U | 在两端已有CT对位置补两段短横向M1，同属P06 | 补条方向/必要性来自Q2；具体包围边界为AI实施值，不增加导体或改变基本U形 |
| P07内U | 保留原折线及宽度参数，仅对原横段增加局部包围带 | 原6 px条带不足以满足当前CT的5 px孔＋双侧1 px包围，按“金属覆盖CT”微调为8 px局部横段；不是新增第三条走线 |
| P08外围环段 | 左竖局部由14 px加宽到22 px，中心线不变 | Q3授权加宽，22 px是相对像素候选；上下横段在左竖修订带之外保持完全相同 |

M1对象仍为9项，只修改P06/P07/P08；所有原设计折线、主宽度、原生观察线和端点状态均不变。局部补片以同一导体内的参数化部件保存，必须与原主体正面积相接，不允许生成孤立金属。P08上下右端继续出窗，未封环或补全未知。

AA334／POLY696／CT10287当前共同层完全不动。M1仍作为引用该快照的已审结构伴随层保存，未冒充已扩展共同清单或整层M1完成。

## 检查与结论

- 9项几何有效、正交、连续；两条U及其他对象没有误并。最小对象间距约7.57设计像素，大于当前小样3 px预算。
- 原87个源漏CT包围通过；新增两组栅端检查共8个CT也通过。95个是本次小样的模型包围检查数，不是新生成孔数，不代表全幅CT或M1接入全恢复。
- 原六处来源限制、全部既有裁决、来源照片哈希不变。Q1已审记录精确保持；P08横段在变更带外精确保持；预算、旧接入组及8孔来源限制不得通过修订输入消失。
- 20项相关软件测试通过（11.14s）；相关Ruff、git diff --check、产物/输入哈希、SVG XML与JavaScript语法通过。已直接查看修订后规则图；没有声称浏览器点击验收。

状态为`SCOPED_REVIEWED_WITH_LIMITATIONS`，`requires_user_action_now=false`：本轮结构裁决与更正已落实。全部8个栅CT在**设计模型**中已被M1包围；精确**原生照片**投影仍未独立核准，旧`pending_gate_CT_ids`保留的正是这一来源限制，不表示模型仍漏孔，也不重复请求用户审批。新精确尺寸不因本次实施而升级成人工逐像素批准。

不生成新网络批准或自动网络边；未启动V1/M2重建、全幅M1或追网。原结构批准可接续使用，未知只限制依赖它的具体投影/接口，不强制重跑已审层。

## 恢复入口与下一步

- [修订spec](../../benchmarks/m1-geometry-pilot-reviewed-v2/spec-v1.json)锁定父输入、人审记录及明确before/after；[逐对象变化](../../benchmarks/m1-geometry-pilot-reviewed-v2/delta-v1.json)、[机器核验](../../benchmarks/m1-geometry-pilot-reviewed-v2/verification-v1.json)。
- [模型](../assets/m1-geometry-pilot-reviewed-v2/model.json)、[报告](../assets/m1-geometry-pilot-reviewed-v2/report.json)、[继承上下文](../assets/m1-geometry-pilot-reviewed-v2/continuation-context.json)区分已审结构、新几何、原生投影限制与电气状态。
- 复跑：`.venv/bin/python -m silicon_eye.metal_reconstruction --spec benchmarks/m1-geometry-pilot-reviewed-v2/spec-v1.json --output runs/新的M1已审修订目录`，使用新目录，不修改父包/原图。

下一节点为M1／V1／M2联合小样：先在M1原图核对V1接口，再检查M2对应与包围；按具体接口验证局部映射，不套用旧的精确CT投影、不重审Q1–Q3，也不要求全层重新人审。本轮仅完成当前局部裁决实施。
