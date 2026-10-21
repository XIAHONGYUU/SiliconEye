# CT来源裁决落地：上端栅CT、连续AA及单排CT

用户的[R1A／R1B／R2裁决原文](../../benchmarks/ct-work-layer-reviewed-v4/human-review-v1.json)完整保存。R1A与R1B均为上端栅CT、蓝T带正确、源漏均匀；R2只有一排孔，AA连续。这三个来源问题关闭，不表示整层或任意新增坐标已获批准。

[复核页](../assets/ct-work-layer-reviewed-v4/index.html)包含统一全幅层开关、局部前后规则图、独立坐标的宽视野原图和唯一新增数量问题。未重新提取无关材料，也不要求重新验所有孔。

## 修订及保护

- 上方四组的211条旧未审CT整段替换，避免沿用误落源漏列或下环的top/bottom标签。G01、G02、G05和G06前5指共32条栅指，独立测得64个上端候选；三个已能完整对应的AA体测得175个源漏候选，按共同直行、节距及材料窗口规则表达。总新增239条，均保留照片坐标和局部取峰窗口。
- 新栅端观察与H3旧引用冲突，未以先导出的记录胜出。完整82条未审H3来源路径重新检查：独立定位上方环亮带后测峰，只改来源；设计几何、ID及原证据在source_correspondence_history完整保留。
- R2原AI“两个隔离环”的解释撤回。以AA2-UPPER-INNER-B-AA-0为保留ID，合并AA2-UPPER-COMPLEX-GUARD-AA-0-split01并保留旧别名和两份原来源；334个AA对象中的这个合并体为新边界候选，不推广为其他环相连。
- 241条原复杂环CT改用统一AA承载身份；其中106条未审侧段候选对齐中央已审行，共326条构成单行13px格点，有证据才保留槽位，不补满缺槽。中央220条完整记录不变。新增AA补接面积不接触其他AA对象；仅此处AA连续，不升级为新M1或net连接。
- 当前10254条CT＝10226－211＋239。9692条v3父记录完整相同，241条改材料身份／局部设计，82条仅改来源。原7044条在v3中的记录全部完整不变，696 POLY、无关333 AA完整不变。原材料及CT批准范围不扩大。[保护检查](../../benchmarks/ct-work-layer-reviewed-v4/preservation-check-v1.json)、[逐项台账](../../benchmarks/ct-work-layer-reviewed-v4/ledger-v1.json)。

## 新发现的一处数量冲突

右上末段AA-F01804，旧材料有G06-P06～P10五条POLY；原图目前可分辨四个上端短亮条和五列源漏CT。上端引出侧已确认，数量仍需核对，不能让CT去适配一个可能多余的栅。

该块旧未审CT撤回，五条材料记录暂保留、明确写入unresolved_material_ids；没有新CT贴上五条旧栅。独立[4条替代几何](../assets/ct-work-layer-reviewed-v4/COUNT-alternative.svg)仅用于比较，不进入工作模型，也不擅自替换既有材料编号。

人工只需裁决 **R1B-COUNT：这一块是否应为4条栅？** [宽视野编号原图](../assets/ct-work-layer-reviewed-v4/COUNT-caps.png)、[不标记上下文](../assets/ct-work-layer-reviewed-v4/COUNT-context.png)、[较大窗口放大图](../assets/ct-work-layer-reviewed-v4/COUNT-inset.png)。这不是重问R1B方向，也不是逐孔复核。

[阶段门](../../benchmarks/ct-work-layer-reviewed-v4/stage-gate-v1.json)为HOLD_R1B_material_count_and_overall_acceptance；whole_frame_complete=false、overall_human_acceptance=false。冻结的是待审候选，不能直接作为已批准整层追网输入。即使数量问题关闭，仍需一次整体工作层验收，不能声称芯片全部物理CT已恢复。

## 仍未知及验证

两小AA、H1/H2长条可见性未知不补孔。端口盘点仍有846个几何扩散区域、7个无直接CT证据，内部区域可以无孔，不能当7处漏检。POLY无直接CT共7个＝V3两历史截段＋本轮暂停的G06末5指，不虚构接入。其他已确认的近邻环隔离、非AA间隙、旧Q1/Q2/Q3以及网络v33均保持。

10254条几何PASS：重叠0、孔距违规0、最小边距4.4px，5px方孔／3px孔距／1px包围及避让预算不降。新增239条和修正82条来源对全部记录做3px范围跨目标争用检查，无冲突。原7044、父冻结文件哈希、材料合并只涉及授权范围、单行节距、页面资源／SVG／PNG检查通过；64项相关测试通过（4.83s），相关Ruff通过。局部PNG已目视；浏览器真实渲染未自动实测。数据检查、软件测试、AI对应判断与物理人审分开，不是实际工艺DRC/LVS或准确率。

复现：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-work-layer-reviewed-v4/spec-v1.json --output runs/新的CT裁决目录`。原始照片及父冻结包不改；provenance为审计配方，不是新增生产案例接口或CT skill。当前入口及README修订前完整原文分别保存在[任务归档](../history/current-task-before-2026-10-21-ct-R1-R2-reviewed.md)与[README归档](../history/2026-10-21-before-ct-R1-R2-reviewed-README.md)。本轮未提交或推送GitHub。
