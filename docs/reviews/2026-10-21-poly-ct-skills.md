# POLY／CT 重建skill封装与收尾验证（2026-10-21）

用户批准仓库内分别封装POLY重建、CT重建，并完成统一输入输出、接续约束、独立Agent接续试用三项收尾。本次不重新识别全幅、不改变已审材料，不启动M1／追网，不推送或安装全局skill。

## 交付

- [POLY重建](../../skills/silicon-eye-poly-reconstruction/SKILL.md)与[CT重建](../../skills/silicon-eye-ct-reconstruction/SKILL.md)：各自选择条件、AI结构判断、算法辅助边界、跨层修订和停止条件；UI名称与用户要求一致。
- [共用契约](../architecture/layer-reconstruction-skill-contract-v1.md)与`silicon_eye.layer_review`：复用joint_layers／ct_transfer既有模型和事务，不造第二份材料/AI观察格式；现有typed AgentObservations可绑定，不自动转成几何批准。
- [POLY样稿](../assets/poly-skill-package-v1/index.html)、[CT样稿](../assets/ct-skill-package-v1/index.html)：inspect已有结果，空delta、原快照接续，保留六处未知与全部人审文档；AA／POLY／CT及源图可切换。两页相同局部是有意验证两个skill消费同一份材料事实，不是两次独立图像提取。

## 验证设计与边界

软件测试验证原子事务、对象范围、陈旧父记录、固定预算、拒绝身份/几何退化、未知及已审范围不丢、候选重载和哈希。独立Agent另在不携带本轮聊天历史的情况下，读取skill和当前真实状态，评估一份待采用补丁并生成自己的结果。

固定待评补丁提前保存在`benchmarks/poly-ct-skill-validation-v1/poly-pending.json`及`ct-pending.json`；这是已知问题的对抗回归输入，不是拟采用材料结果。独立试用是**已知芯片、可读当前人审状态的开卷接续测试**，不是视觉盲测；未提供预期答案或提示具体错误。不得据此宣称新芯片泛化或独立识别准确率。没有实测人工纠正次数／耗时，保持null。

本轮三项收尾已完成，以下为实际结果；封装为仓库内人机协作v1，不升级为自主识别系统。当前材料基线仍是共同快照v3，AA334／POLY696／CT10287、六处限制，`automatic_network_export_allowed=false`。新桥和CT几何仍为AI候选，工程闭合不升级为物理完整恢复。


## 实际结果

| 检查 | 结果与证据 |
| --- | --- |
| 两个skill包装 | skill-creator quick_validate各通过；命名、元信息及本地链接可用 |
| 相关软件测试 | `pytest -q tests/test_layer_review.py tests/test_joint_layers.py tests/test_ct_source_ownership.py`：25 passed，103.66s；其中新交付入口10项 |
| 静态/交付检查 | 相关Ruff、git diff --check通过；两个样稿的输入/产物哈希、SVG XML及JavaScript语法、空delta、S3批准范围及六处未知均已核对 |
| 独立POLY试用 | 待评缩短补丁实际退出2；AA局部截面下端延伸为−46.981 px，要求8 px。CT/来源/身份门仍PASS，POLY门独立拒绝。inspect退出0，未要求重做人工审批 |
| 独立CT试用 | 待评归属变更实际退出2；已审身份、AA包围及沟道净距拒绝，来源门仍PASS。inspect退出0，保留共用POLY／紫色源漏身份及未知 |
| 主Agent复核 | 四个Agent包的输入/产物/执行代码哈希及全部继承文档逐一复核；拒绝包没有候选或next_snapshot；inspect明确接续原v3 |

独立产物完整复制进Git可追踪目录：[POLY原始结果](../../benchmarks/poly-ct-skill-validation-v1/poly-forward-trial/result.json)、[CT原始结果](../../benchmarks/poly-ct-skill-validation-v1/ct-forward-trial/result.json)、[主Agent核验](../../benchmarks/poly-ct-skill-validation-v1/primary-agent-verification-v1.json)。原结果内的runs路径是当时实际执行位置，同名包及日志现保存在各自forward-trial目录，不再依赖runs恢复。本轮新增人工问题0，不等同于测得人工纠正次数0；该指标仍null。

POLY初次试用指出：主Agent准备的原待评请求源图窗口[650,1150,1250,1800]未覆盖G26-P01的原生定位范围。原请求与首轮产物原样保留，Agent已在自己的inspect中改用[500,1200,800,1580]；之后主Agent新增`poly-pending-corrected-view-v2.json`重放，同一几何仍被拒绝（退出2）。这次重放不是新的独立/盲测样本。POLY skill补入“先核窗口覆盖、定位轮廓不等于测量边界”的提醒，首轮skill正文也已冻结，未把修复后的指令倒写成首次表现。

样稿已核对静态结构、脚本语法及源裁片；本轮没有声称完成浏览器点击验收。未绕过此前file://浏览限制。候选模型可重载由有效局部修订测试验证；本轮样稿与Agent试用均未采纳新材料几何。

## 收尾结论与下一节点

1. **统一输入输出**：两skill共享锁定快照、现有AI观察格式、局部事务、质量门与同页图层复核；具备可执行命令和真实样稿。
2. **接续规则**：只修改有证据的指定对象，可跨AA/POLY/CT一次事务修订；保留上下文、旧身份退休、六处未知和批准粒度。写候选时现在也保留CT文档原有外层元数据，未把其丢成单一objects列表。
3. **行为验证**：两次独立开卷试用完成，实际拒绝错误局部补丁并安全继续v3；一个视图准备错误被发现并修复，旧试用完整保存。已知问题的防退化与新输入的识别能力仍分别计量。

目前足以发布仓库内的人机协作skill v1；新芯片、陌生视窗识别、精确边界与广泛效率收益尚无统计证据。后续每次新任务继续记录候选、裁决及实际返工，不将软件PASS当成识别准确率。当前不新增人工裁决，也不重跑已审层；下一大阶段可用已审CT锚点建立M1规则几何重建的小样任务。
