---
name: silicon-eye-metal-reconstruction
description: Reconstruct or locally revise regular M1/M2/M3 metal candidates from Silicon Eye photographs, preserving reviewed interfaces and unknowns through the unified review workflow. Trial skill for evidence-guided geometry reconstruction; not autonomous segmentation, full-net tracing or canonical GDS adoption.
---

# 金属重建（仓库内试用 v1）

定位含CURRENT_TASK.md的项目根，读取当前快照、批准、未知及目标范围。复用已审结果；评审窗口不是切断导体的边界。现已验证M1/M2/M3及相邻V1/V2的小范围配置，不将它扩为所有工艺、全画幅或陌生芯片准确率保证。

## 观察与重建

- AI先查看原生照片及邻层：导体的整段走向、转角、支路、端部、真实间隙和上下接口。算法可辅助具体问题；命令本身不做图像识别。原始观察、规则几何和电气批准分开。
- 在独立设计坐标恢复正交边界。对称/等间距阵列须有来源支持；未看清的端部保留未知，不为整齐而补连。不要因为上层同网就合并不同物理金属ID。
- 同层除了宽度、间距，还核对来源中的左右/上下次序，必要时声明`source_order_checks`。核对每条折线的转折方向与支路开口，不能为了匹配推测连接把向左返回改成向右；统一入口比较原生/设计的带符号转折，明显反向会拒绝，斜向不明确时保留未评估。跨层坐标不是同一照片，不能套同帧次序或未经验证的投影；V1/V2不能当同孔配对。
- 新候选采用[统一契约](../../docs/architecture/conductive-workflow-contract-v1.md)的`conductive_layer_observations`。已有样本保持原格式及哈希，由同一入口适配。已审连接继续保留，设计几何仍为候选。
- 修订只改列明对象的设计路径/宽度等字段；提供父包、`allowed_changed_ids`及AI修订依据。更换照片、原生锚点、接口身份、退休/合并ID属于新证据问题，当前试用事务会拒绝，不能借局部微调绕过。

## 执行与接续

统一命令：

```bash
.venv/bin/python -m silicon_eye.conductive_workflow --request REQUEST.json --output runs/NEW_DIR
```

当前样例：`benchmarks/conductive-quality-review-v1/medium-request-v1.json`、`benchmarks/conductive-quality-review-v1/independent-request-v1.json`。旧trial/main含已查出的R-M2-3反向折线，只作负例历史；旧独立候选窄A承载已被实际人工更正，不作为当前起点。先读请求及当前状态，输出必须用新目录，原图/冻结包不改。固定执行规则检查来源、正交、间距、孔组包围与变化范围；硬失败只交diagnostic.json，不能采用失败几何。

父包按manifest绑定；接续自动继承接口审批，检查U3等已审端子不丢失。人工裁决只问影响身份/连接的新歧义，不重复问已审接口，也不逐孔计数代替连接判断。未知不等于断开，可标`deferred_unknown_ids`继续其他工程工作。

交付统一复核页、候选模型、质量门报告和来源manifest，说明变化ID、保留批准和未覆盖范围。现有试用入口不修改共同v5/AA/POLY/CT，不自动导网表、推送或安装全局skill。质量门PASS不是物理真值/真实PDK DRC；验证范围见[试用报告](../../docs/reviews/2026-10-24-conductive-workflow-trial.md)。

质量交付要分别列出：程序检查、声明来源形状、已审承载、孔组表示/尺寸资格、可见范围与未知端部。11/38已审清单记录不是照片覆盖率；规则图包围PASS、零待裁决或端子闭合均不能表述成完整几何验收。更改金属以容纳孔组只是一份AI提案，不能反过来证明照片支持该边界。按[本轮复查](../../docs/reviews/2026-10-24-conductive-quality-review.md)使用当前入口，不重审已批准连接。
