# 器件跨层编号视图

编号视图是统一复核包的可选输出。它复用case内的器件／栅指ID、原生检查窗口和已审核宏观配准；不创建新器件，不改已有人工事件或连接状态。

```bash
# 新检出先按review-package.md恢复历史审核输入。
.venv/bin/silicon-eye annotate review-package \
  --spec benchmarks/review-package-roi2-device-index-v1.json --root . \
  -o runs/new-device-index
```

打开输出的`device-index.html`，可直接用本地浏览器查看，也可通过仅监听127.0.0.1的静态服务预览。页面提供：

- 选择原有器件编号，同步突出各层对应框与表格行；支持“全部器件”恢复显示。
- AA、poly、M1原生照片窗口，各层分别保留坐标，不将同尺寸或并排显示当成已精确配准。
- 实线表示case已有的原生候选检查窗口；虚线表示已审核宏观变换投影后的查找范围。都不是材料边界、端子落点或金属走线。
- 缺少定位时显示“未定位”和原因，不凭材料片段、同网关系或电路图补框。
- 同一ID的G/A/B/Bulk连接表、原电路图、无标记原像素裁剪、JSON与CSV索引下载。

## 输入与可追溯边界

既有请求增加可选`device_view.windows`。每个窗口显式指定唯一id、frame_id、显示label、原生xywh；可选projection_profile_id必须引用同一包中已通过来源与人审核验的配准记录。窗口及配置进入bundle状态与哈希。

直接定位只读取`geometry_observations`中entity_id与器件ID完全匹配的记录；不从名称或材料卡编号猜设备所属。同器件同源frame有多个窗口时拒绝自动选取。器件ID沿用原case且按ID排序，颜色由ID决定，不以行号/渲染次序重命名。

投影只支持从已审核reference frame到target frame，使用现有target→reference矩阵的逆矩阵。源窗口完整处于同一个已审核凸多边形内才投影；超范围、变换奇点、超出目标原图或显示窗时保留unknown。非凸审核范围不自动外推。本版不把投影结果写回case，也不以该投影推断连接。

导出`device-index.json`包含每个器件每层的状态、源geometry、投影profile、原生多边形、原图路径与哈希、四端引用及同一block_state_id/bundle_id。CSV是便于查看的逐器件逐层索引；JSON与manifest保留完整来源。新增页面/数据/裁剪都进入统一manifest，相关代码哈希一并保存。存在原有电气裁决冲突时只生成诊断，不输出正常编号视图。

## ROI2交付

本机页面：`runs/roi2-device-index-v3/device-index.html`。R2_Q1/R2_Q2仍表示原复核的两条相邻MOS栅指，不决定它们是否组成一个完整器件。

| 层 | 本次显示 |
| --- | --- |
| poly | 两个原生候选检查窗口，沿用case定位 |
| M1 | 通过已接受局部宏观配准生成两处查找位置；不保证精确CT落点 |
| AA | 原图上下文与相同器件ID列表；尚无逐器件定位证据，不绘制器件框 |

三层使用同一组逻辑ID，并不意味着三层均已精确定位。AA单器件定位是后续证据缺口；本次编号查看与状态表达功能已经可用。实际尺度、像素边界、S/D方向、金属端口及走线点亮仍待对应证据和后续实现。

本轮验证：236项测试与相关Ruff通过；来源单独拷贝后23项产物哈希一致，block_state_id保持原值。浏览器实测Q1/Q2选择、恢复全部及层间跳转正常，所有图片加载通过且无横向溢出。该验证不新增物理定位或连接批准。
