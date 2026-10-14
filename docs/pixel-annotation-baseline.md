# 局部像素标注合同

本轮仅为 aa/poly 相同局部建立可复核结构标注草案，不是已确认器件/分割真值。用户明确确认 aa 为实际有源区层、poly 为实际多晶硅层；物理尺度仍未知。原图与配准参数不变。

- 坐标：每层原始源图像素 x/y；bbox=[x,y,width,height] 表示半开区间。参考画面与目标画面坐标不能直接混用，冻结矩阵只作为坐标变换引用，不自动传递几何真值。
- 输入：源图路径、哈希、尺寸和局部范围；冻结配准包的路径/哈希；每条标注 id、源图、bbox、几何定义、角色/用途、生产者、状态及证据。
- 状态：candidate/confirmed/conflict/unknown；confirmed 需要显式人工确认记录。层语义的人工确认不传播到对象边界或器件身份。
- 当前形状只有 bbox，定义为观察区域，不代表精确材料掩膜。当前对象器件类型 unknown、端子/连接无已知数据；不导出 DeviceList 或 μm/W/L。
- 三处配准控制结构只作 fitting/diagnostic，不能作为独立器件 holdout；两处嵌套区域只作 annotation_candidate，不自动确认为 MOS 或无源器件。
- 复核入口检查范围、原图哈希/尺寸、冻结输入和状态，再输出两层标注图、逐对象源图裁剪和摘要。渲染成功与基准准备完成分开报告；原始像素不改写。

首次草案先固定标注框再渲染；若人工修订，另存新版本并记录理由，保留原版本。只有相应标签/边界及用途经独立复核，才能将其用于器件/分割准确率验收；同一配准控制不得冒充保留真值。

## 实现与首次草案

格式实现于 schemas/pixel_annotation.py，复核入口实现于 pixel_annotations.py。冻结配准引用沿用 benchmarks/local-ring-aa-poly-v1/baseline/manifest.json；不重新拟合，不把目标标注自动复制成参考层真值。

[当前标注 v2](../benchmarks/local-pixel-annotations-v2.json)保存10条源图 ROI 和5组显式跨层候选对应；[初版 v1](../benchmarks/local-pixel-annotations-v1.json)保留，并以 previous_input_sha256 引用。黄色为三处配准控制区域，青色为两处内部区域；每层各5条。v2 只增加跨层对应记录，没有改变原框。两种控制/候选用途不得混用。

用户在本轮问答中确认 aa=有源区层、poly=多晶硅层，sources.layer_status=confirmed 且保留确认记录。几何对象和跨层对应全部 candidate；尺度 unknown，device_type unknown，terminals 空。roi 定义是观察范围而非精确材料 mask。

```bash
.venv/bin/silicon-eye annotate review \
  --input benchmarks/local-pixel-annotations-v2.json \
  --output runs/pixel-annotation-next
```

相对路径按仓库根解析；输出目录必须不存在。格式校验后，脚本核验真实源图哈希/尺寸和冻结配准引用，再输出两层标注图、10份逐对象原图裁剪、标注快照、源码快照和状态摘要。

[复核包](../runs/pixel-annotation-review-v2r1/report.md)。geometry_status_counts={candidate:10}，correspondence_status_counts={candidate:5}；device_ground_truth_ready=false，segmentation_ground_truth_ready=false。渲染完成不表示人工标注基准完成。

19 项新增测试覆盖越界/非有限/空框、重复或未知对象、未复核 confirmed 拒绝、控制对象不能用作 holdout、伪造已知器件/物理尺度拒绝、来源/尺寸验证、输出保护，以及确认 ROI 不传播为器件或材料 mask 真值。全套102项通过；最后报告补充层语义摘要后，19项相关测试重验通过。相关 Ruff、源图/引用/输入/源码快照哈希与 Git 差异检查通过。

下一步只在两处内部候选区域建立精确材料边界草案与复核方法，继续像素单位；有独立的边界/器件基准前主 Pipeline 的器件阶段保持 blocked。
