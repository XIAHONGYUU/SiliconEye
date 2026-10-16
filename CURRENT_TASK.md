# 当前任务

## 目标与授权

用户本轮要求依次完成：

1. 补齐GitHub示例缺失证据，验证新检出重放后提交一版GitHub。
2. 制定最小AI观察格式，按已有V3/ROI2两批结果建立可迭代评测种子集。
3. 对照项目原workflow完善顶层架构：同位置多层照片输入，电路图/器件标号/金属端口与高亮输出，明确skill边界及未实现项。

阶段1允许提交推送；阶段2/3先本机实现/设计与验证，不擅自新增物理结论、调用外部视觉服务、安装PDK或建设平台。

## 已确认事实与边界

- 原始照片来自同一芯片逐层去层拍屏；每张保持独立原生像素坐标，不能凭同尺寸推断配准。
- V3：两MOS共享中间扩散；Q1.G/Q1.B/Q2.G/Q2.A同网，外侧A/B对应M1上下横条；额外并网无证据，Bulk各自未知。M2-P2对应V3组，但路径/端子映射未知。
- ROI2：两条相邻MOS栅指，poly局部不直接连、经M1共栅；中间共享源漏、体端共用，外侧M1共接未知。不自动归并为单个MOS或默认体端接电源。
- ROI2 AA片段与两poly主体身份/大致位置确认；精确多边形/像素边界、CT落点、W/L仍未知。
- ROI2 M1→poly限定两框宏观透视叠图已确认；不外推AA细配准、其他区域/整芯片或尺寸精度。
- 10px/μm仍为未确认假设，不换算真实W/L；未知不当隔离或同网，不借用跨案例批准。

## 最新工具与验收

- 统一包入口：`silicon-eye annotate review-package --spec benchmarks/review-package-roi2-v1.json --root . -o 新目录`。
- 首次运行需先恢复证据：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/roi2-reviewed-inputs-v1.zip --root .`。
- [说明](docs/review-package.md)；[ROI2固定结论](docs/checkpoints/2026-10-16-roi2-reviewed.md)；[顶层纠偏](docs/workflow-realignment-2026-10-16.md)。
- 统一包的block_state_id：4aab154bbcb952acbcdce88f129b82ebacd28e7e633167ce39f807ff9b59c02f。
- 本轮全套200项测试通过（新增4项恢复测试），此前196项测试通过，原GitHub main为10058081e693e2b920812e7dbef87e7ecce535c8；本轮证据恢复新增测试与新检出验证以本轮结果为准。
- 已归档9项历史runs审核输入，原字节/路径/裁决哈希不改，runs本身仍不整体提交。不是全部历史runs恢复包。

## 当前进度与唯一下一步

阶段1已通过：干净的暂存Git检出起初没有runs，恢复9项归档后重放，17项产物哈希及bundle_id与原结果完全一致；200 tests、相关Ruff与diff检查通过。当前提交推送阶段1，随后在本机推进阶段2/3；无第三ROI或模型平台扩展。

评测暂按V3、ROI2两批组织，均为参与过开发和人工修正的历史种子集，不是盲测/独立跨芯片样本；参考答案仅覆盖已确认事实和明确未知。

## 未完成能力

运行时自动材料/器件提取未接入；统一包重放既有判断。顶层照片栈输入、器件稳定编号、端子→金属证据与交互高亮需明确架构，不能把局部宏观配准或逻辑节点冒充精确物理网络。

## 历史与恢复

- [本次精简前完整原文](docs/history/current-task-through-2026-10-16-unified-package.md)保留所有阶段过程与裁决来源。
- [更早入口原文](docs/history/current-task-through-2026-10-16.md)。

精简仅整理入口；原始证据/批准记录未改，未完成的重放、AI观察、评测与顶层设计均已保留。
