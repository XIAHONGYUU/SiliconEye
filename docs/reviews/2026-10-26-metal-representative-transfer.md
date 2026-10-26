# 金属／VIA代表结构迁移验证

本批将已收口的联合中样作为防退化基准，新增右侧原生范围[2940,1730,3670,3000]的局部观察。区域与上一中样/上方独立小样空间分离，但仍是同一芯片、有历史上下文，不是陌生芯片盲测。

## 产物与范围

- [统一复核入口](../assets/metal-representative-transfer-v1/index.html)：保留M2/M3原生照片切换、规则图分层开关、大字孔组标记、原图链接和下部完整放大图。
- [当前统一workflow输出](../assets/metal-representative-transfer-v1/corrected/index.html)含3条M2、5条M3、4组显式V2阵列，共32个候选设计孔。8条金属及4组孔共12条局部候选记录，未并入材料v5或旧41对象工作快照。
- **R1**：两条平行长M2的上端U1/U2，暂按3×2阵列，候选承载为M3紫色B-U宽母线。
- **R2**：同两条M2的下部D1/D2，修订后暂按5×2阵列，候选承载为粉紫色B-D宽母线。
- **N1**：旁边折线窄M2及中部母线/细线作为上下文。保留同层间距；没有声明来源孔的模型交叉不生成接口，也不据此断言物理无孔。
- 本轮新证据集中于M2/V2/M3。新V1短支路的对应依据不足，未补造连接；已收口V1案例只作回归，不计为新增识别。

## 同一流程如何迁移

继续使用仓库内金属和层间孔两个限定试用skill及`silicon_eye.conductive_workflow`，本轮不修改提取/重建执行代码。变化为新的观察数据、来源窗口和参数；没有新增案例专用提取器。

原有最小孔宽6、孔间距3、包围1，以及金属正交/间距和来源转折方向检查保持。新孔完整逐个表示，没有缩成一个代理框。孔中心及尺寸仍为相对设计候选，不是照片配准或PDK尺寸。

```bash
.venv/bin/python -m silicon_eye.conductive_workflow \
  --request benchmarks/metal-representative-transfer-v1/request-v2.json \
  --output runs/新的迁移输出
.venv/bin/python -m silicon_eye.conductive_workflow \
  --request benchmarks/metal-representative-transfer-v1/next-request.json \
  --output runs/新的迁移接续
```

## 暴露的问题与修正

初稿下部采用4×2，声明内的规则检查通过，但原图自检看到末排亮点仍在框外。该初稿在人工送审前被AI退回，重新观察为5×2。保留[初稿输出](../assets/metal-representative-transfer-v1/candidate/index.html)和[来源复查记录](../../benchmarks/metal-representative-transfer-v1/source-reinspection-v2.json)，没有把初稿改写成首次即正确。

局部亮度行剖面辅助复查亮点位置，不作为独立真值。软件校验完整站点清单，不能发现一整排从观察清单中漏掉；因此必须保留AI对原图完整性的复核。来源复查、规则几何检查和人审连接是三项不同资格。

## 验证与结论

27项相关测试通过：新区域4项及既有23项回归；包括错配窄承载、反转折线方向、遗漏阵列站点三类拒绝案例。修订版原样接续，模型完全一致，变化ID为空，重用裁片逐像素匹配源图；补充下部原图裁片、SVG/XML、JS语法及本机HTML链接检查通过。

旧基线重新加载并验证182项来源引用，41对象、13已审接口、2结构组、1端子路径及材料未知保持，Q1/Q2继续收口。README/site的25项文件哈希和gh-pages引用不变。HTML实际交互未测，没有绕过之前的本机URL浏览器限制。

**工程执行与防退化验证通过；新区域AI身份/承载判断仍待R1/R2人审。** 本轮没有新人工批准，不能报识别准确率、泛化能力或完整金属层完成。既有skill仍为限定试用v2，不正式通用放行。

[固定任务与待评测指标](../../benchmarks/metal-representative-transfer-v1/fixed-tasks.json)已在新人工裁决前保存。身份正确、承载正确和人工纠正次数暂为null；收到实际裁决再记录，不能把工程PASS填成AI正确。

本轮无需逐孔计数；只需确认R1两组上端V2是否接B-U、R2两组下部V2是否接B-D。其他可见但未建模支路保持未知。[完整验证记录](../../benchmarks/metal-representative-transfer-v1/verification.json)。未提交或推送，公开展示保持。
