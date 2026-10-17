# 最小AI观察格式与历史任务基准

观察格式由`silicon_eye/schemas/agent_observation.py`实现。它描述AI新提出的判断，不接受AI自报confirmed或human；原人工裁决仍独立保存。

每份记录绑定一个带哈希的local_photo_task，包含task_id、run_id、purpose（live_observation/historical_reexpression/synthetic_fixture）、producer、model_id/prompt_version（历史未记录可为null）与observations。每条观察包含：

| 字段 | 含义 |
| --- | --- |
| id / subject_ids | 观察ID与任务中的稳定对象/端子ID |
| predicate / scope_id | 材料身份、器件存在、同网/隔离、局部物理相连或端子导体关联；作用域不得混用 |
| status / value | candidate+有证据判断值，或unknown+null；不接受confirmed |
| evidence_refs / rationale | 原图来源ID与判断/不确定原因 |
| location | 可选原生frame及检查窗口；窗口不是材料边界 |
| boundary_status / boundary_polygon_xy | 边界unknown，或显式候选多边形；不接受像素真值批准 |

材料identity仅为aa/poly/ct；MOS存在用device_exists。电气不连使用different_net，而非局部poly不连推断；unknown不能带一个确定的值。当前最小关系格式按显式二元关系比较，不声称完成复杂图语义评测。

例：对象已经人工认定为poly，但精确边界未知，应把“人工认定”放在独立裁决记录。新的AI观察仍为candidate，引用对应输入和既有裁决作为证据；不能只让AI把状态写成confirmed。

## 两批种子与迭代

[种子清单](../benchmarks/agent-eval/index.json)按现有可追溯成果分为V3开发闭环、ROI2复核闭环，每批一个局部多层任务，各10条参考断言，共20条；不虚构成五个任务。它们来自同一芯片且已有开发/修正历史，都是historical_development，不是独立盲测集。任务提供命名的对象复核槽位，因此当前也不测全图器件发现率。

input.json只含原图/原生窗口/对象槽位/范围和任务，不含reference标签；reference.json只收已有人审依据的事实与明确未解决关系。ROI2材料只有身份和大致位置标签，没有像素掩膜真值。V3未单独建立材料标签的部分不借用ROI2答案。

后续每轮追加新批次/参考版本/运行记录，不覆盖旧参考。先冻结任务与模型输出，再做人工复核；将新裁决追加为后续参考版本，既记录纠正前结果，也保留纠正后状态。新任务应在模型调参前保留一部分未见样本，不能重复用同一组样本调参后宣称泛化。

## 初期质量门

工具`agent_evaluation`比对参考覆盖的明确断言：正确、错误、漏掉已知事实、无证据确定断言、明确保留未知、漏填未知。输出参考外断言供人工审查，不能自动当错误或正确。

所有参考已知断言必须匹配，未知须显式保留、无额外未评断言，才通过本轮“参考断言门”；这不是整块物理质量或完整Agent任务通过。全部回答未知不能通过。局部几何、器件发现、推理时间和人审负担暂未评分。

```bash
# 复制一批observations-template.json，填入本轮实际AI输出后运行；不要把模板当预测成绩。
python -m silicon_eye.agent_evaluation \
  --reference benchmarks/agent-eval/roi2-seed-v1/reference.json \
  --observations runs/actual-agent-observations.json --root . \
  --output runs/new-evaluation.json
```

输出父目录须存在；输出已存在则拒绝覆盖；格式/来源错误返回1，断言门未通过返回2。单元测试中填参考答案的合成记录只检查评分器，不是模型运行成绩。

**现在没有新的Agent成绩，也没有测得人工纠正次数。** 两批evaluation_runs为空，human_corrections为null。可先用CSV手记介入次数/耗时，不能让Agent自己写0充当无返工。

参考规范化有来源，但哈希/actor检查不能自动证明自然语言到标签的语义正确；参考修正也必须追加版本。校验边界是任务原图和声明的人审记录，不递归要求恢复所有旧图稿。

## 与统一复核包的关系

已接入[显式适配器](observation-adapter-v1.md)：新观察绑定既有统一包，生成独立的新case proposal、unknown卡和材料观察卡，再由统一包导出。既有人工事件保持不变；检查窗不生成材料mask，AI候选不转成人工批准。历史转写样稿用于核查接口，不计新Agent成绩。
