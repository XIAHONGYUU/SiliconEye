# 新V1端部／短支路：V1-S1迁移候选

[统一复核入口](../assets/v1-new-short-branch-v1/index.html) · [实际workflow送审包](../assets/v1-new-short-branch-v1/candidate/index.html) · [事前AI观察](../../benchmarks/v1-new-short-branch-v1/initial-ai-observation.json) · [固定Agent任务](../../benchmarks/v1-new-short-branch-v1/fixed-task.json)。

## 新接口与来源判断

选择旧N1/W1下方另一排的独立M1短指：原生路径约[1153,3374]→[1153,3412]，上端紧凑亮区[1143,3369,1164,3393]提出V1候选。它与此前N1上排接口、旧材料归属S1均不同，稳定接口ID为`V1-S1-GROUP`。

历史宽图中出现过该排背景，但没有这个接口的人审记录。因此本轮是一个新接口判断，不是未见图像盲测，也不复用旧N1/W1的批准。

较合理的承载候选是蓝色A：M2折线从右侧短帽返回至左侧竖段，原生路径约[1138,3321]→[1118,3321]→[1120,3417]；以其下端接入M1亮区。附近B/C保留作替代解释或上下文，不把它们的未接入候选写成“无孔”或全局异网。

V1只从M1侧照片提出；M2蓝框只标A的承载端。原图宽图及放大图独立切换，不将未配准图强行投影，不用M2上的亮点冒充V1。

## 几何与质量资格

复用现有金属/VIA两个限定试用skill和统一workflow，新增样本参数而不新增提取器。局部设计含3条M1、3条M2和1个V1孔组支持代理；保持正交、同层间距、来源次序和折线转向。

亮区内部暂不能可靠逐孔拆分，6×6设计支持区只用于接口候选，不等于一孔、不声称完整阵列占用或全孔组包围。质量报告明确保留`GROUP_SUPPORT_PROXY`、`full_group_design_enclosure=NOT_EVALUATED`、人审孔数未知，禁止共同几何采用和整网输出。

31项相关测试通过（本轮4项，既有27项回归）。错配旁边M2、将M2来源冒作V1、反转折线三类反例被阻断。原样接续模型完全相同，裁片与原图逐像素核对；72项来源/交付哈希、SVG/XML、生成JS语法及HTML链接通过。静态规则图和原生标记图已检查，HTML实际交互未自动验证。

旧联合基线41对象、13条已审接口及本轮先前已审4条V2接口保持，Q1/Q2、R1/R2不重审。README/site的25项文件哈希和gh-pages引用保持。完整记录见[验证](../../benchmarks/v1-new-short-branch-v1/verification.json)。

## 唯一新裁决与接续

**下方一排独立M1短指上端橙框亮点，是否为V1，并接到蓝色A短折线M2的下端？** 若实际是B/C或其他金属，请指出。无需逐孔计数。

当前人审真值、身份/承载是否正确、人工纠正次数均为null；不能由软件检查通过代填。收到裁决后再绑定本次送审包和复核导航追加，不改事前观察。

```bash
.venv/bin/python -m silicon_eye.conductive_workflow \
  --request benchmarks/v1-new-short-branch-v1/next-request.json \
  --output runs/新的V1接续
```

只交付本机候选，未提交或推送；不宣称完整孔层、全网、真实工艺DRC或skill正式通用放行。
