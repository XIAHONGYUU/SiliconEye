# Gate→CT→M1复核 v2

**最新裁决：用户确认“CT归属与M1选段确认无误”。[独立反馈](../benchmarks/terminal-highlights/roi2-q1-gate-ct-m1-review-feedback-v1.json)已绑定原图稿，[case v6](../benchmarks/block-case-v1-roi2-gate-ct-m1-reviewed-v6.json)登记R2_Q1.G到该局部M1段。精确边界/CT像素落点/延伸仍未知。下文保留候选提出时的说明。**

v1直接选择上方宽公共横条，未提供gate接触点证据，被用户明确否决。原候选/图稿保留，[否决原文与哈希绑定](../benchmarks/terminal-highlights/roi2-q1-gate-upper-bar-rejection-v1.json)独立保存；v1不得作为当前gate金属结论。

本轮遵循用户要求：先在候选gate上找CT，再从CT找M1。对原生poly和M1逐图放大观察后，AI作出以下新候选，脚本只检查/投影/渲染。

1. 延续已审R2_Q1栅指窗口，沿其下端找到亮斑簇；poly原生CT候选窗口为[1743,2820,28,22]，中心约(1756,2831)。这是gate下端扩展处的一组亮斑，与两侧竖向源漏CT列分开选择；亮度本身不证明其物理归属。
2. 用已接受ROI2 M1→poly宏观变换的逆矩阵投影CT窗口和中心，落至M1约(1731.48,2956.91)。源窗口须完整处于已审宏观范围内。
3. 在原生M1局部图上，将中部双横线中靠上的一条作为落点附近的金属候选；显示锚点(1732,2966)，距投影中心约9.1px。16px是本次查找范围，不是实测配准精度/验收误差预算。保留未知，不据接近就批准接触或电气连接。
4. 黄色只显示声明的局部段，段外延伸未知，不追踪整网、不改case确认网表。

[复核图](../runs/roi2-q1-gate-ct-highlight-v2/terminal-highlight-001-ct-bridge.png)：紫框=原栅指检查窗；青框=poly候选CT；青圈/十字=M1投影搜索位置；黄段/紫十字=候选金属与显示锚点。请先复核青框CT是否在所选gate上，再核查M1选段。两项当前均为candidate。

```bash
.venv/bin/silicon-eye annotate review-package \
  --spec benchmarks/review-package-roi2-gate-ct-highlight-v2.json --root . \
  -o runs/new-gate-ct-metal-review
```

`terminal_highlight.contact_bridge`显式保存gate源frame、CT窗口/中心、源上下文、已审核配准profile及目标搜索范围。导出中保留原生来源、gate geometry、CT投影多边形、偏移，以及ct_on_gate/ct_to_metal两项候选状态。脚本拒绝未知端子、非G端子、缺失配准、超范围CT、投影不支持或锚点超出声明搜索范围；不将距离校验解释为接触已确认。

本轮248项测试、相关Ruff通过；复制声明证据到独立目录重放30项产物一致，block_state_id仍为原已审值。静态图已目视检查，没有调用浏览器绕过先前安全限制。没有修改原照片、原有人工裁决或候选v1，也没有推送GitHub。
