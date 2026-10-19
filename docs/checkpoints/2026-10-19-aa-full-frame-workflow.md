# AA全幅工作流：复用、定向修订与封装前验证

> 后续局部裁决与封装：用户确认R1/R2间为非AA，横向结果基本正常，左右竖向环虽近仍分离。模型核对无重叠且间隙为正，几何不需重算。[已审入口](../assets/aa-full-frame-workflow-v1/reviewed.html)、[人工裁决](../../benchmarks/aa-full-frame-workflow-v1/human-review-v1.json)、[核对](../../benchmarks/aa-full-frame-workflow-v1/ring-separation-verification-v1.json)、[采用状态](../../benchmarks/aa-full-frame-workflow-v1/acceptance-v1.json)。该关键关系已闭合，仓库skill封装为v1人机协作版本；原执行报告保留待核历史状态。全幅稠密完整性未扩大批准。

2026-10-19。用户授权继续使用验证流程，重点推进全画幅，最终达到可封装skill标准。本轮执行AI/现有工具协作，不训练全图模型，不改原图、旧模型、人审记录或CT；尚不宣称完整AA层已经验收。

[全幅复核页](../assets/aa-full-frame-workflow-v1/index.html) · [冻结参数](../../benchmarks/aa-full-frame-workflow-v1/spec-v3.json) · [模型](../../benchmarks/aa-full-frame-workflow-v1/model-v1.json) · [质量报告](../../benchmarks/aa-full-frame-workflow-v1/report-v1.json) · [AI逐块初检](../../benchmarks/aa-full-frame-workflow-v1/ai-review-v1.json) · [核查](../../benchmarks/aa-full-frame-workflow-v1/verification-v1.json)。页面保存于docs/assets，可脱离runs直接查看；原生图5712×4284与共同重建画布5860×4587通过逐对象来源对应，不能盲目重叠两种坐标。

## 实际修改

| 修改 | 证据/做法 | 状态 |
| --- | --- | --- |
| 上方相邻AA | 根据F01–F04既有“两条被识别为一条”的裁决，拆开模板相交的上下轨道；复用边缘定位工具测量源边界 | 两组件、HV几何保持；源边界仍为AI候选 |
| 左上大MOS间横环 | F05–F06已确认没有环，只移除原模板误补的横条，不改变MOS本体或外围AA | 按已有语义修订，不再问同一问题 |
| 左下大MOS间横环 | 同样按F09裁决移除误补横条，保留外围环及MOS | 按已有语义修订 |
| 蓝色台阶AA | 纳入用户已确认更贴合的B1原生轮廓，记录向现有共同版图坐标的映射 | 原生轮廓逐点相同，不重复验收 |
| 电阻/MOS环源图对应 | 旧模型使用全局反投影时偏离自身记录角点；改用原对象native_corners及孔的对应，保留正交版图几何 | 原图对齐与间隙改善，精确全环边界未升级批准 |

336个旧对象中只修改6个目标，330个非目标对象字典内容完全相同，72个保留AA对象完全相同；上方目标拆分后共337个对象。这个数目不是覆盖率、器件数或正确率。

所有有效正交多边形通过，重建几何面积交叠0；每处材料变更限制在声明范围，范围外差异只存在浮点舍入量（小于0.05 px²的数值工作容限，不是工艺DRC）。已批准B1原生轮廓与原验收文件逐点一致。源图对应变更不推电气连接。

## 图像与质量验证

- AI查看全幅、F01–F12全部宏观范围及关键宽上下文；这些是复用的观察窗口，没有要求人重新逐块标注。未发现需推倒整图重新提取的依据，但F09旧环结构问题仍未准确定位，不宣称全幅完整性通过。
- 回查原有12个非训练检查中心：旧全幅几何6/12符合已有标签，新版12/12符合。两处误补横环及环的源图投影解释了差异。检查中心此前已见，不是盲测；不将其表述为整图100%准确。[逐点证据](../../benchmarks/aa-full-frame-workflow-v1/center-regression-v1.json)。
- 上方边缘首轮存在局部错误峰值。限定在相邻可靠轨迹附近，要求实际梯度支持，修复575列；5190列通过本次定位条件，最右30列在搜索跨度外，保留候选对应而不宣称精确证据。纯版图几何始终为HV，没有沿照片波纹生成不规则GDS。
- 100条历史算法疑点只作空间对照，不自动当作100处缺AA，也不按与候选重叠比例关闭；另存[历史疑点对照](../../benchmarks/aa-full-frame-workflow-v1/legacy-observation-crosscheck-v1.json)。整体完整性靠材料与上下文复核。

## 当前真正需要人工介入的事项

[原图定位图](../assets/aa-full-frame-workflow-v1/Q-F09-RING/source.jpg)标R1外环、R2内环，保留宽上下文；旧轮廓与本轮轮廓均可切换。用户此前指出“F09右侧中间环的结构错了”，尚不能确定指的是哪条环、哪一段或与相邻环的关系。该处没有擅自修形，也不重新询问是不是AA。需定位该具体结构问题后继续修订；不要求重验全部F/N块。

## 软件与封装状态

新增通用silicon_eye.aa_layer_revision按锁定数据处理明确范围：既有脚本执行布尔/正交拟合、边缘定位、来源映射、检查和渲染，AI仍负责材料/结构判断。案例坐标保存在spec，不写入模块。不是一个自主识别整层的神经模型。

相关34项测试通过，含误补横条删除后的外围保护、越界拒绝、意外组件拆分拒绝、局部映射不改变远端坐标、无图像梯度不得补边界；相关Ruff与输入/输出哈希、页面资源检查通过。浏览器交互尚未自动实测。开发中发现并修复局部映射误夹取远端坐标与空索引问题，已留负例；未以改阈值绕过材料门。

当前达到全幅可重放技术入口和已知案例局部改善证据，实验版skill补入[封装条件](../../skills/silicon-eye-aa-reconstruction/references/full-frame-validation.md)。关键F09结构问题、全幅材料完整性尚未闭合，因此不将skill升级为全幅正式验收版本，也不假称独立Agent/新芯片泛化、精确像素真值或效率优势。

```bash
.venv/bin/python -m silicon_eye.aa_layer_revision --root . \
  --spec benchmarks/aa-full-frame-workflow-v1/spec-v3.json --output runs/新的全幅修订目录
```

被测skill与源代码在benchmark中冻结。spec-v1/v2和前几轮输出保留作开发/定位证据，当前工作版本为v1d；不是多次独立成功案例。父模型、原始裁决和三任务证据不追溯覆盖；此版本仍为独立全幅工作候选。
