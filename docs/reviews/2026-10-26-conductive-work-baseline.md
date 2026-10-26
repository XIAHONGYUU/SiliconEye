# 连续五层复核与联合工作快照

本轮接续用户批准的第一、二项：复核现有五层几何，整理能够持续开发的工作基线。基线fcc531a；README、site及gh-pages按哈希保护，不更新远端展示。

[统一开发复核入口](../assets/conductive-work-baseline-v1/work/index.html) · [Q1静态对照](../assets/conductive-work-baseline-v1/static-review/Q1-comparison.png) · [Q2静态对照](../assets/conductive-work-baseline-v1/static-review/Q2-comparison.png) · [工作快照](../assets/conductive-work-baseline-v1/work/snapshot.json) · [接口说明](../architecture/conductive-work-snapshot-v1.md)。

## 第一项：五层中样工程收口，保留两处宏观评审

本轮重新查看已有M2原生标记图、人工定性反馈和当前完整孔组；通过原统一workflow接续两处样本。模型与stacked-via-review-v2完全一致，接续新增变化ID为空，13条已审接口不丢失。没有为了产生新版本而再次修改几何。

| 项目 | 反馈前→当前工作候选 | 本轮状态 |
| --- | --- | --- |
| Q1 | 保留原V1范围，只继承既有V2下移；实际切孔投影相交72设计px²；V2为已审3×4数量，V1的9孔仍为AI数量候选 | 规则/包围/接续检查通过；请仅判断当前相对重叠是否合理 |
| Q2 | 保留六孔V1及宽B承载；继承M2-B由38×115改为38×74、V2整组34×60；占宽89.5%、高81.1%，切孔投影相交90设计px²；两组数量均已有绑定人审 | 规则/包围/接续检查通过；请仅判断当前整组占用及重叠是否合理 |

橙色为V1，浅黄色轮廓为V2；静态图左列为反馈前、右列为当前候选，上排保留上下文、下排显示完整孔组。放大视窗检查会拒绝把旧/新孔组裁掉一部分。

这些是规则模型测量，不是独立照片配准精度。具体新坐标、孔径/间距、精确边界仍为候选；本轮不重复审批已有连接，也不要求逐孔测量。[AI复核说明](../../benchmarks/conductive-work-baseline-v1/source-assessment.json)。

## 第二项：可接续工作快照已建立

新入口`silicon_eye.conductive_snapshot`复用原workflow实际重放、材料加载器、来源校验及SVG绘图；不增加案例专用识别流程。

- AA334、POLY696、CT10287继续引用材料v5；旧33记录导体注册表保持不变。
- 两个局部域共41个对象表示，13条接口裁决、2个结构组、1条端子连接继承；原ID不改，用域名限定查找键，禁止跨画布误合并。
- 8帧原生坐标与来源保留。材料画布、中样画布、独立样本画布分开；未建立到材料画布的变换，不伪造统一叠投。
- U3已审CT→AA环路径继续存在，但具体CT/AA材料ID映射仍未知。材料六处未知与A/B具体返回路径候选均保留。
- 当前工作包可重载，下一轮request锁定其manifest；新快照会拒绝丢失旧域、稳定ID、接口/分组/端子裁决或材料未知。
- `work_snapshot_ready=true`表示接续可用，完整共同几何采用、跨画布投影及整网导出仍关闭。

## 验证与使用

33项不同测试通过，覆盖工作快照、原堆叠孔和五层几何；其中新工作快照16项。代码/模板、静态图、来源哈希和相关链接分别检查。两处底层包接续结果原样；新快照继续重放也保持对象/裁决/未知。完整记录见[verification.json](../../benchmarks/conductive-work-baseline-v1/verification.json)。

浏览器自动化环境中的临时浏览器已不存在；随后浏览器工具因URL安全策略拒绝file://本机页面。没有换协议或浏览器绕过。采用静态几何图、SVG/XML、实际生成JS语法/JSON及文件链接核对；**本轮网页实际交互未测**，不沿用旧公开Demo的交互成绩。

```bash
.venv/bin/python -m silicon_eye.conductive_snapshot --request configs/conductive-work-baseline-v1.json --output runs/新的工作快照
.venv/bin/python -m silicon_eye.conductive_snapshot --request benchmarks/conductive-work-baseline-v1/work-next.json --output runs/新的接续验证
```

第一项工程检查和送审包完成，几何验收仍待本页Q1/Q2；第二项工作快照已交付，但不提前采用未审全幅几何。用户确认后再按范围推进覆盖；原图、旧审批及公开展示均不变。本轮未推送GitHub。
