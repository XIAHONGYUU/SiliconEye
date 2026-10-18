# 区域记录与复核合同

区域记录是辅助观察与评测索引，不是全幅材料图层的分割合同。后续分层抽取及连通图保持完整场景范围，不能由本记录的 bbox 裁割。

使用有版本 JSON 即可。工具兼容当前项目 region-planning v1/v2 的来源与区域字段；没有实现自动识别、人工裁决合并或 PhotoStack 全接口。不要为调用工具修改已有人审状态。

## 工具所需最小结构

```json
{
  "plan_id": "scene-regions-run-01",
  "sources": {
    "layer_a": {
      "path": "data/example.jpg",
      "sha256": "ACTUAL_SOURCE_SHA256",
      "width": 1000,
      "height": 800
    }
  },
  "regions": [{
    "region_id": "region-01",
    "label": "R01",
    "category": "UNKNOWN",
    "title": "待解释的重复结构",
    "status": "candidate",
    "views": [{"source_layer": "layer_a", "bbox_xyxy": [100, 100, 400, 300]}],
    "observation": "描述直接可见的形态和支持层",
    "alternative_explanations": "可替代的结构解释",
    "next_check": "决定类别的最少补查"
  }]
}
```

以上只是字段示例，源路径/哈希/尺寸必须替换为真实输入，不生成假数据。

- `sources` 的 key 与 `views.source_layer` 一致；路径相对项目根且不得逃逸，SHA-256 用于核验只读源图。
- `bbox_xyxy` 使用原生左上原点、x 向右 y 向下、半开范围，必须在源帧内；每帧独立取值。不是 μm 或公共显示坐标。
- 常用类别：MOS、CAP、RES、INTERCONNECT、DUMMY、SUBSTRATE_RING、EXCLUDED_UI、UNKNOWN；其他类别允许扩展。状态保留输入原值，不因渲染而升级。
- 支持可选 `device_structure`、`functional_use`、`material_roles`、`unknowns`、`pdk_refs`、`human_review_ref` 和来源修订字段；计划 JSON 原样随页面保存，避免信息在出图时丢失。
- 区域可重叠；区域数与过孔数均不等于器件实例数。分类已确认且没有精确边界时仍保留粗几何状态。
- 没有某层定位时不补造 view。人审说明“某层为 dummy”等可仅存 material_roles 与定位未知。

## 工具行为与限制

`build_review.py` 先检查源图、尺寸、唯一 ID、状态与几何，再在新目录发布 `index.html`、原样 `plan.json` 和 `validation.json`。已有输出拒绝覆盖，禁止输出到原始 data/。页面包含各源层切换、原生全图、带邻域的局部和区域表。

图像以内嵌 JPEG 作显示，原照片仍可通过链接打开；移动页面到别处可能改变原图链接，不影响嵌图。显示缩放不改变 plan 中的原生几何。生成的局部视图不代表配准。

`physical_classification_verified=false` 表示脚本没有验证物理分类，即使输入已有人审。报告真实浏览器检查状态，不把静态 HTML 存在当作交互通过。

## 人审与后续调用

提供“编号 / 位置 / 当前分类 / 希望核对的差异”清单。保留用户原话并链接首次候选的哈希；生成新有效状态，不覆盖原记录。除非用户明确否决，不撤销既有物理事实。

重放已审案例只验证工具与记录能否复用；分类效果需另存未经修正的模型输出，并与有范围的人工参考比较。缺参考的部分不计正确或错误。当前同照片经验不能证明跨芯片效果。
