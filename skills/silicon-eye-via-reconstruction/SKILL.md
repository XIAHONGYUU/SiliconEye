---
name: silicon-eye-via-reconstruction
description: Reconstruct V1/V2 observations and regular via-group support candidates between declared adjacent metal layers in Silicon Eye, checking source identity, enclosure and scoped human decisions. Trial skill for interface reconstruction; not CT extraction, measured full via arrays or automatic net tracing.
---

# 层间孔重建（仓库内限定试用 v2）

读取CURRENT_TASK和锁定快照，先确定层对、来源照片、上下金属及旧批准。CT连接AA/POLY与M1，仍由CT skill处理；本skill当前验证范围为M1/V1/M2及M2/V2/M3的小范围孔组，不宣称全层逐孔恢复。

## 先判断接口，再规则化

- AI在原生照片中找孔组，保留宽上下文。来源帧与孔层是两项记录：本批已审策略为M1侧V1、M2侧V2，不把它写成所有拍摄工艺通用规则。不能把M2亮点当V1或把M3亮点借作V2。
- 分别寻找下层和上层承载，检查邻近替代导体、是否真实接入、是否存在间隙。跨层先核局部结构对应；没有合格变换就并列原图，不作像素投影。上下几何重叠不能产生孔或连接批准。
- **同层孔间距与跨层投影分开检查。** V1与V2处在不同高度，可以有平面投影重叠，不能为满足同层间距而将两组错开；分别检查V1的M1/M2包围与V2的M2/M3包围。本批用户确认存在这类重叠，但具体偏移量仍需来源依据。允许投影重叠不等于两层是同一个物理孔，也不恢复已撤回的V1/V2同孔拟合。工艺特有叠孔限制另查对应PDK，不能将未知工艺默认写成禁止。
- 对已知多孔组保留全组横向/纵向占用，用规则单孔阵列检查尺寸、间距与两侧包围，不能缩成一个小支持框后声称能被窄金属承载。孔总数本身不决定金属宽度，还要看实际排列和横向占用。尚未辨清阵列时采用明确标为候选的组级支持区，执行两侧包围。当前统一入口支持**孔组支持区或显式设计阵列**；两者都不能自动当作实测几何。已知人工孔数须从继承人审记录接续，即使候选删掉数量/阵列字段，也不能退回单框。无需为此逐孔向用户求批，优先AI核原图并让人裁决影响承载的歧义。
- 候选记录带稳定ID、层对、来源帧、原生窗口、设计支持区及上下金属ID。`connection_confirmed`初始null，AI不得填成人审true。根据邻层证据微调设计几何需显式限定变化对象，不移动原生锚点掩盖错误对应。

## 同一入口完成复核与接续

按[统一契约](../../docs/architecture/conductive-workflow-contract-v1.md)准备观察样本和运行请求：

```bash
.venv/bin/python -m silicon_eye.conductive_workflow --request REQUEST.json --output runs/NEW_DIR
```

已验证接续样例用`benchmarks/five-layer-geometry-v1/review-request-v1.json`及同目录`independent-request-v1.json`；实际工作基线由CURRENT_TASK指定。P08连续路径的V1为AI观察3×3、V2为既有人审3×4；中样其余9组仍为代理。独立区域六孔V1接宽B与B经V2接M3均已审，新增3×2 V2仅为AI阵列候选；原窄A假设只保留为错误历史。输入是AI已形成的观察/几何候选，不是命令自动从照片辨孔。

人工记录必须绑定实际送审请求和接口ID/层对/上下金属；命令验证来源对应后才加入已审连接。拒绝审批夹带新承载或换照片；人审未看清的接口保留null，禁止用通过的另一个接口替代。父包继承旧审批；冲突不能静默覆盖，需要另作明确更正。人工纠正未审接口的承载时，用契约的carrier_correction记录实际旧送审包及before/after身份；不移动原生锚点、不连带撤销其他批准，已审接口的替换仍须另作事务。

输出与金属skill共用分层复核页、模型、质量门、局部变化和manifest；只新增必要的人工问题。硬FAIL只留诊断。不得因工程通过或一次局部批准采用共同层、补不存在的孔、导出完整网络或认定真实PDK DRC通过。试用能力与未测范围见[报告](../../docs/reviews/2026-10-24-conductive-workflow-trial.md)。

复核页必须显示整组孔所在的原生窗口；来源帧正确但送审宽图/放大图未覆盖孔组时拒绝交付。质量报告分别写“承载已审”“完整设计阵列已检查”“来源阵列几何未验收”。一个小支持框的包围只证明这个框能放下，不能让整个孔组或完整skill放行；不以现有38条已审清单当作全部可见接口清单。

迁移已审组时按原成员ID和既有人审绑定行列/数量，不能旋转行列或换到另一孔组。中样与独立样本复用regular_group_cuts和同一SVG渲染；完整阵列要逐孔显示，不能数学已算12孔、图上仍画一个实心大框。现有金属能覆盖时保持其几何，不为凑包围而拉伸。

没有人工逐孔数量时，也可先交AI观察的规则阵列：`array_source_evidence`绑定`kind=via_array_observation`记录，含接口ID、层、照片哈希、原生范围、rows/columns和逐站点`row,column,native_xy`，`count_status=candidate_not_human_count`。脚本检查身份、站点完整性、范围及行列次序；它不验证像素识别正确。既有人工数量优先，AI观察不能替换已审数量。新增排列和尺寸仍单独复核，不把连接批准写成数量批准，不因数量未知自动否决有依据的整组承载候选。

固定示例孔径不能替代照片占用比例。局部设计像素的尺寸/pitch有独立来源依据时，可用`cut_array_candidate.geometry_parameters={cut_size_px,pitch_xy,basis}`调整整组，必须绑定`array_source_evidence`；全局最小孔径、间距和包围不变，组内孔保持方形和等尺寸。局部画布的数值不当成真实工艺孔径。人工只补充孔数或定性重叠时，用绑定旧送审包的几何反馈记录；孔数与具体新坐标批准分别保存。

交付与金属skill共同的复核包：同坐标新旧设计、独立来源照片切换、完整孔组和上下承载；不在未配准的照片上投影。当前限定试用覆盖同芯片V1/V2整组迁移与局部修订；待本轮几何验收后再选择结构类扩展，不承诺全层逐孔恢复或陌生芯片准确率。
