# 可接续导体工作快照 v1

本接口将已验证的局部导体包与材料共同v5关联，管理版本、来源、稳定ID、已审接口、结构组、端子路径及未知。它是开发接续包，不替代共同v5，不自动采用几何或生成整网。

## 使用

```bash
# 从冻结包和明确请求重新构建；目标目录必须不存在
.venv/bin/python -m silicon_eye.conductive_snapshot \
  --request configs/conductive-work-baseline-v1.json --output runs/新的工作快照目录
# 从本轮工作快照接续，额外检查旧ID/裁决/未知/坐标域不丢失
.venv/bin/python -m silicon_eye.conductive_snapshot \
  --request benchmarks/conductive-work-baseline-v1/work-next.json --output runs/新的接续目录
```

两个底层包继续通过原来的`silicon_eye.conductive_workflow`产生；本接口不增加照片识别器、案例专用提取器或独立审批系统。

## 输入

`kind=conductive_work_snapshot_request`，`schema_version=1`。

- `material_snapshot`：材料v5的路径和SHA。对象、别名、CT归属和8张照片由既有加载器校验。
- `domains`：每个局部坐标域的稳定名称、当前package manifest、下一轮底层接续请求、反馈前比较包、允许的既有几何差异、必须保持的层，以及本轮宏观问题/视窗/原人审反馈。
- `parent_work_snapshot`：可选，上一工作包manifest。新建时无此项，接续时必须继承原域、稳定对象、已审接口/分组/端子及材料未知。
- `material_geometry_adoption`、`cross_canvas_projection`、`automatic_network_export_allowed`均须显式为false。

每个包在汇总前实际重放其next_request：必须得到完全相同的模型、零新增变化ID和技术检查PASS。单纯对篡改后的模型重新计算SHA，不能让它伪装成原样接续。相对反馈前包的变化另列；不是本轮重复修改。

## 输出与坐标

`manifest.json`绑定输入/交付哈希；`snapshot.json`保存工作状态；`report.json`分开报告接续资格与几何待审；`index.html`提供两处新旧规则图、切层、孔组放大、原生宽图与完整放大图、ID索引和裁决/未知。

原ID不改名；`domain::original_id`是版本查找键，防止局部画布中的同名对象被误合并。几何仍从锁定包按原ID读取，快照不重新复制或重建材料模型。

材料画布5860×4587、中样1800×1550、独立样本1100×570分别记录。`native_frames`保留8帧5712×4284的原生像素空间和照片引用；局部设计画布到材料画布的placement/transform仍为null，不允许借相同名字、视觉叠加或任意平移伪造配准。

当前41项是两个局部域的对象表示，不是全芯片导体数，也不与原注册表33项相加当覆盖率。旧33记录注册表保持其引用；未建立全图变换时不覆盖它。

## 材料端子与资格

U3的M1→CT→AA环连接继续保留，但`canonical_CT_object_ids`及`canonical_AA_object_ids`仍为空。路径已审不授权猜选附近CT/AA ID。六处材料未知、A/B已审分组和未定具体返回路径均保留。

`work_snapshot_ready=true`仅表示来源、重放和限定状态汇总可用。`canonical_geometry_adoption`、`material_canvas_registration`、`complete_network_export`继续为false。孔数已审、设计阵列、孔径/节距/精确边界资格分开；历史限制原文不删，当前结构化数量记录优先解释已明确范围。

复核只问Q1重叠关系、Q2整组占用两处宏观变化；不重复审连接，不要求逐孔精确测量。本轮源码/模板新增不影响README、site或gh-pages。
# VIA尺寸局部修订（2026-10-26补充）

用户确认“先保持落点，缩小孔径”。工作候选尺寸可以规则化，不能把照片亮斑外径直接当成设计孔径，也不能为填满承载金属而放大孔。不同VIA层不默认同孔径；本次统一为6仅是Q2的局部候选约定，不是工艺规则。

统一workflow请求可声明`preserve_via_center_ids`：绑定父包并逐站点比较设计中心，拒绝数量变化、移动和重排；孔径可以变，原生来源、承载关系和最小孔宽/间距/包围规则继续继承。该检查不证明旧设计中心与照片已精确配准。

工作快照分别记录单孔尺寸、中心清单、切孔实际相交面积和孔组外包络相交面积。已审定性“组间重叠”检查包络，单孔相交仅报告；不能靠扩大孔径制造重叠，更不能由交叠推导连接。最新示例为[保中心缩孔](../../configs/via-center-preserving-v1.json)。

