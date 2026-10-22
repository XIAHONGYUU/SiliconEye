# M2证据身份纠错：3×4 V2

2026-10-22。用户指出联合中样把M2上的孔标为V1有误，确认该M2照片本处为3行×4列、共12个V2。原文及范围见[人工裁决](../../benchmarks/conductive-stack-v2/human-review-v1.json)。

[修订联合页](../assets/conductive-stack-v2/index.html)、[修订数据](../assets/conductive-stack-v2/model.json)、[共同快照v5](../../configs/joint-work-layer-v5.json)、[复跑请求](../../benchmarks/conductive-stack-v2/request-v1.json)、[验证记录](../../benchmarks/conductive-stack-v2/verification-v1.json)。

## 错误与修正

原流程把M1上的V1与M2上的V2当成同一孔组配对，在M2误画V1标框，还把V2只表示为左列的一个支持代理。这是证据身份错误，不是显示标签的小问题。

- M1上的V1保留原照片证据及9个候选几何；当前观察记录不再包含M2上的对应孔点。
- M2整组仅标V2，按人工确认的3×4建立12个规则孔形。编号V2-J-R01-C01至V2-J-R03-C04；尺寸、节距和单孔原生亮点中心仍是AI候选，未作为精确边界测量。
- 原单代理V2-J-EDGE-SUPPORT在当前模型退休；物理组J-M2-EDGE-V2保留编号，并明确从原左列观察扩展为完整本地阵列。不能复活旧代理为额外第13孔。
- M1／M2／M3几何、已审M1→V1→M2及B1承载不变。V2组已确认数量为12；整个照片／所有Via层的总孔数仍未知。

## 撤回错误对应证据

原9对M1/V1到M2/V2点不是同一孔的跨照片观察。原3点拟合、6点留出及约4.52像素残差，**不得继续作为有效配准证据**；状态为REJECTED_DIFFERENT_VIA_LAYER，不能只写成“精度还未核准”。旧包作为错误历史保留，不作为当前身份基准。

当前source_identity_gate按本批照片的人审身份检查来源：M1的V1与M2的V2分开；禁止V1借用M2的V2坐标或照片。拟合工具对显式声明为不同Via层的同孔配对直接拒绝，即使数值残差小。该规则限定于已判定照片内容，不推广为所有工艺去层照片的普遍可见性定律。

## 不扩大的范围

修订后的33条记录为M1九条、V1九个候选孔、M2一条、V2十二孔、M3两条。依旧只有两处既有已审局部接口，没有新增物理接入判断或自动网表边。M2／M3出窗未知、精确投影关闭；AA334／POLY696／CT10287及六处来源／接入限制不变。

[评价更正](../../benchmarks/conductive-stack-v2/evaluation-correction-v1.json)明确记录原M2/V1标记错误和配对无效，不以原测试PASS掩盖；此前K1对B1目的端的批准保持原范围。几何和程序检查通过不代表照片语义天然正确。

```bash
.venv/bin/python -m silicon_eye.conductive_layers \
  --request benchmarks/conductive-stack-v2/request-v1.json --output runs/新的纠错中样目录
.venv/bin/python -m silicon_eye.layer_review \
  --request configs/metal-stack-review-v2.json --output runs/新的纠错共同复核目录
```

当前无需新增人工裁决，旧版v1及快照v4仅按历史调取。继续分支验证时先核对证据帧与Via层，禁止沿用这9对错误坐标或原矩阵。
