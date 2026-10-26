# 金属／VIA代表结构迁移：R1、R2人审通过

用户于2026-10-26分别答复“R1：身份与承载正确”“R2：身份与承载正确”。本批局部迁移验证状态为**SCOPED_TRANSFER_VALIDATED**；没有剩余的本批待裁决接口。

## 本次裁决

| 人审任务 | 绑定的局部接口 | 已确认关系 |
| --- | --- | --- |
| R1 | RT-V2-U1、RT-V2-U2 | 均为V2，分别将R01、R02两条M2接到RT-M3-UP（B-U宽母线） |
| R2 | RT-V2-D1、RT-V2-D2 | 均为V2，分别将两条M2接到RT-M3-DOWN（B-D宽母线） |

[已审复核入口](../assets/metal-representative-transfer-reviewed-v2/index.html)继续保留层开关、M2/M3原生照片切换与下部完整放大图。[实际workflow包](../assets/metal-representative-transfer-reviewed-v2/reviewed/index.html)有4条已审连接、0条待裁决接口。原图问号是送审时图注，保留原证据，当前资格以已审记录为准。

四条接口记录分别绑定原始送审请求/页面/manifest、用户看到的复核导航及整组裁决；同一次人审覆盖两个组，不报成四次独立人工任务。未修改M2/M3、孔中心、孔径或原生锚点，未再次要求用户批准旧Q1/Q2。

## Agent评测结果与范围

[结果文件](../../benchmarks/metal-representative-transfer-reviewed-v2/evaluation-result.json)从送审前[固定任务](../../benchmarks/metal-representative-transfer-v1/fixed-tasks.json)追加生成，原文件不覆盖。

- 2/2送审任务的孔层身份、承载判断得到确认，对应4条局部连接记录。
- 本次人审身份/承载纠正次数为0，仅指这两项送审判断，不是项目历史返工次数，也不是零内部修订。
- 送审前下部4×2漏排、经AI自检改为5×2的记录继续保留。它是一次涉及D1/D2的内部数量假设修订，不被“人审纠正为0”掩盖；5×2仍未获得人工数量批准。
- 本次是同一已知芯片的空间迁移，有上下文，样本量为两项任务。不能据此给出跨芯片准确率、全画幅可靠性或无需人审的结论。

本次确认的是接口身份和承载。上端3×2、下部5×2、所有尺寸/间距、精确照片对应仍为AI几何候选；规范材料ID映射、未建模支路和完整网表未知。旧基线13接口与本批4接口分包保留，没有自动拼成共同网络。

## 接续与工程验证

```bash
.venv/bin/python -m silicon_eye.conductive_workflow \
  --request benchmarks/metal-representative-transfer-reviewed-v2/next-request.json \
  --output runs/新的已审迁移接续
```

本轮通过统一workflow验证人工记录绑定，确认全部几何对象与送审版一致，四条批准在下一次原样接续中保留。没有代码/几何变更，不重复计算上一轮27项测试成绩为新增测试。来源、审批与复核页检查见[本轮验证](../../benchmarks/metal-representative-transfer-reviewed-v2/verification.json)。HTML实际交互未自动验证。

README、site/和gh-pages保持；原材料v5、原图、旧41对象基线及其裁决不变。本轮未提交或推送。金属／VIA skill仍为限定试用v2，本次不正式通用放行。

下一步优先核清一处真正新的V1端部或短支路对应，补充本批未覆盖的新V1迁移证据，再评估更大覆盖；R1/R2不重开。
