# 金属／层间孔统一读取接口 v1

2026-10-22。实现依据为两组已审层对，不是新的提取模型或通用skill。[当前修订联合页](../assets/conductive-stack-v2/index.html)已按人审更正M2的3×4 V2身份；首份v1仅作为含错误标记的历史保留。

## 接入方式

共同快照增加可选`conductive_layers`锁定引用，指向`conductive_layer_registry`。`joint_layers.load_snapshot`返回`conductors`；`layer_review.records(snapshot, layer)`可按M1／V1／M2／V2／M3读取统一记录，`model_svg`及现有层复核页支持显示和切换这些层。未附加此字段的AA／POLY／CT快照保持原行为。

当前[共同快照v5](../../configs/joint-work-layer-v5.json)的材料输入、原图、预算及未知完整继承v3，仅附加纠错后的导体注册表。不把M层塞入POLY，不把V层塞入CT，也不复制全幅材料数据。v4含原M2错误身份，仅按历史调取。

## 对象记录

| 字段 | 含义 |
| --- | --- |
| `id`、`layer`、`kind` | 原对象编号、明确图层及金属／候选孔／孔组支持区类型 |
| `geometry` | 共同设计像素坐标的正交多边形；保留候选边界状态 |
| `inherited_record` | 原输入记录，保持不变；M1-P08原接续片另存`inherited_local_addition`，仅合成有效几何 |
| `input_package` | 锁定的原模型路径及SHA256 |
| `source_frame`、`source_photo` | 证据照片与原图哈希；照片名不替代孔层对身份 |
| `source_observation` | 孔的原生观察；V1仅保留本批M1的V1证据，V2保留本批M2的V2证据；不再将两者作为同孔配对 |
| `role` | 已审局部链上的候选几何，或仅作隔离上下文 |
| `end_states` | 金属端点／继续出窗未知状态，保持原记录 |

V2-J-EDGE-SUPPORT已在当前模型退休，替换为12个V2候选孔形，归属原物理组J-M2-EDGE-V2。人审确认该组为3行×4列、共12孔；孔边界及尺寸仍是候选。V1的9条记录并非新增9次人工逐孔测量；整个照片／所有Via层的总孔数仍未知。

`source_identity_gate`按本批照片的人审身份拒绝来源层误用；原9对M1/V1→M2/V2坐标及其约4.52像素留出不能作为配准证据。显式Via层身份不同的同孔配对在拟合前直接拒绝。旧历史字节可复现不代表旧语义正确，见[纠错记录](../checkpoints/2026-10-22-m2-via-source-correction.md)。

## 接口与连续链

`reviewed_local_connections`分别保存原接口ID、上下金属ID、Via层、几何对象成员、原裁决记录及人审引用。第一组J1与第二层对K1通过同一M2-J01组装为：

**M1-P08 → V1组 → M2-J01 → J-M2-EDGE-V2 → M3-J-B1**。

`continuous_chain`是这两处已审关系的组合视图，没有新增物理接入判断。`new_physical_connections=0`、`complete_network=false`、`net_edges=[]`、`automatic_network_export_allowed=false`。既有M2／M3出窗端未知，不能把该链当成完整网络。

## 检查与修改边界

- 同一M2必须记录及几何完全一致，只保留一份；全局对象ID不得重复。
- 原模型与spec／report绑定同一交付manifest；原图、模型及人工来源均校验哈希。
- 两处接口必须有相应人审记录，Via成员和承载对象一致；不从金属交叠推导新接口。
- 沿用各原包的逐层宽度／间距、Via规则及双侧包围检查，不引入未经标定的工艺尺寸。
- 加载注册表时，从锁定父包重建适配结果并比较，拒绝偷偷改目的端、几何或漏掉成员；保存共同快照也拒绝未授权改导体对象。
- AA／POLY／CT仍由原质量门及事务接口管理，未知与批准范围不变。

本轮统一的是**读取、验证、保存接续与可视化**接口。现有`layer_review`的修订命令仍只修改AA／POLY／CT；未来导体局部修订应有明确before／after与授权对象，不能借旧材料事务修改M层。精确原图投影、自动识别、全幅扩展和通用skill封装均不由此自动获得。

共同只读复核可直接使用：

```bash
.venv/bin/python -m silicon_eye.layer_review \
  --request configs/metal-stack-review-v2.json --output runs/新的共同复核目录
```

`target_layer`可为上述五层之一，当前仅允许`inspect`；缺少导体注册表时直接失败，不退回POLY或AA视图。


## 已审分支验证的独立坐标边界

`metal_fanout`读取锁定的共同快照及历史人工接口记录，校验来源照片、Via层身份、上下承载、逐层间距、排除关系和限定中段裁决。接口按`lower_metal_id`去重，多个Via组不自动变成多根下层导体；上层交叠亦不产生连接。

当没有合格共同位置时，输出`reviewed_local_fanout_validation`，坐标为`local_relative_design_px`，不是共同注册表。`common_canvas_placement=null`；不得把局部示意几何叠到AA/POLY或作为共同快照导体记录加载。父v5、原导体33条及材料不变。未来合入共同画布需要明确的位置证据和局部事务，不由几何PASS代替。

[首个实例](../assets/metal-fanout-validation-v1/index.html)采用历史A/C接同一M3、邻B不直接接入、中段无其他M2的裁决；不重审已有批准，也不算独立盲测。支持方块表示孔组而非实测单孔；出窗延伸及完整网络保留未知。
