# PDK 回查与照片区域识别参考 v1

2026-10-18。已在线阅读 GF180MCU 与 SKY130 官方公开文档的相关章节，供本项目 AI 判断材料、器件和接口时回查。本文是阅读摘要与问题索引，不是芯片工艺鉴定、完整 PDK 安装或对当前照片的 DRC/LVS 通过声明。

## 先分清三件事

- 工艺/掩膜层：制造及 CAD 中的定义，可能包含照片看不到的注入、阻硅化或识别标记。
- 去层照片：在某一步暴露出的可见表面，可同时出现不同材料、残留与孔；文件名不能独自决定所有像素语义。
- 本项目语义层：从照片建立的 AA/poly/CT/M1/V1 等几何与未知图，需要自己的来源和验收。

不同 CMOS 工艺可借鉴结构关系；接触路径、器件标记、精确尺寸和电气参数必须按具体工艺区分。当前芯片工艺未知，10 px/μm 未校准；不移植 GF180/SKY130 的 GDS 编号、最小线宽、方阻或电容密度。

## 官方来源和回查入口

| ID | 已读官方章节 | 遇到什么问题回查 | 页面内查找词 |
| --- | --- | --- | --- |
| GF-L | [GF180 4.1 Drawn layer definition](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_04_1.html) | AA/poly/contact/via 的用途；dummy、器件标记与实体的区别 | COMP, Contact, Via1, RES_MK, CAP_MK, Dummy |
| GF-R | [GF180 10.1 P+ Poly Resistor](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_10_01.html) | 为什么长 poly 不足以确认电阻；端点与有效电阻体 | SAB, RES_MK, PRES.9 |
| GF-C | [GF180 10.4.1 MIM Option A](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_10_4_1.html) | 电容上下极板、过孔归属、MIM 结构 | FuseTop, bottom plate, MIM.10 |
| SKY-L | [SKY130 Layers Reference](https://skywater-pdk.readthedocs.io/en/main/rules/layers.html) | 材料组合、派生识别区域、tap 与 diffusion 区别 | poly_licon1, prec_resistor, tap, top_plate |
| SKY-S | [SKY130 Summary of Key Periphery Rules](https://skywater-pdk.readthedocs.io/en/main/rules/summary.html) | 接触/互连的连接层关系与包围规则 | licon, li, mcon, via, Connectivity |
| SKY-D | [SKY130 Device Details](https://skywater-pdk.readthedocs.io/en/main/rules/device-details.html) | MOS、各种电阻、MIM 和多层金属电容区别 | Generic resistors, MiM capacitors, Vertical Parallel Plate |

这些 URL 是可更新的 main/latest 文档，记录的是 2026-10-18 阅读时间，不冒充固定工艺版本。机读索引见 [sources-v1.json](../../benchmarks/pdk-reference/sources-v1.json)。本地保存摘要和索引，未镜像完整官方正文；若离线且摘要不足，保留未知，之后回查原章，不能声称已读取未缓存章节。

## 可借鉴的事实及限制

GF-L：COMP 用于有源扩散及相关互连；Poly2 用于栅和互连；Contact 连接 Metal1 与 Active 或 Poly2；Via1/Via2 分别连接相邻金属层。其目录也区分 dummy 与器件标记。[GF-L](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_04_1.html)

GF-R：该 P+ poly 电阻的电阻体与 Poly2、SAB 相关，并有 RES_MK 识别要求。照片只看到长条，可能缺少足以确认其类型的标记或工艺信息。[GF-R](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_10_01.html)

GF-C：Option A 用 FuseTop 和 Metal2 定义两极板，对底板接口也有专门约束。它说明电容的层组合和接法与工艺选项有关，不能把通用“M2 看见孔”当作任意工艺的完整连接规则。[GF-C](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_10_4_1.html)

SKY-L/S：SKY130 有 licon、li、mcon 等不同接触/本地互连层；材料组合还用于派生识别区域。不能把本项目的 CT 名称直接映射为 SKY130 全部接触路径。[SKY-L](https://skywater-pdk.readthedocs.io/en/main/rules/layers.html)、[SKY-S](https://skywater-pdk.readthedocs.io/en/main/rules/summary.html)

SKY-D：电阻可使用不同材料；MIM 是介质隔开的金属极板，VPP 使用多层金属细线。电阻或电容分类需要结构和端点，不以矩形/梳齿外形单独确认。[SKY-D](https://skywater-pdk.readthedocs.io/en/main/rules/device-details.html)

## 将知识用于本项目：观察与验证顺序

以下是本项目的判断策略，属于从工艺关系推导出的检查方法，不是官方对本芯片的结论。

| 目标 | 先找什么 | 跨层验证什么 | 常见替代解释/限制 |
| --- | --- | --- | --- |
| MOS 候选 | 重复栅指、扩散块、两侧接触区域 | poly 与 AA 的相对关系，栅端与扩散端的 CT/M1 接入 | 重复线不是 MOS 数量；tap、MOS 电容、dummy、特殊器件可能相似；缺阱/注入信息不定 N/P |
| 电阻候选 | 连续长条或折返电阻体及两端接口 | 是否在场区、是否存在周期栅-扩散交叠，接线是否可解释为两端电阻 | 普通互连、多指 MOS、电容和环均可相似；不可凭线长计算阻值 |
| 金属电容候选 | 交错梳齿或成组极板 | 两个隔离电极、各自母线及上下层过孔 | 单块金属、大矩形、重复填充不等于电容；不跨介质并网 |
| 互连 | 连续导体、转折、端头与孔组 | 每接口两侧金属及局部配准 | 相交不等于相连；不套用其他工艺层序 |
| 环/方阵/大板 | 包围结构、规则方块、宽片 | tap 接入、跨层存在性、功能端点 | 可能是保护、dummy、测试、器件或互连，保留未知 |

正向版图思维用来提出解释和选择补查位置。发现不理解的结构时，按“问题→来源 ID/章节→查阅结果→对当前候选的影响→剩余未知”记录，不用工艺常识直接填上确认边。若已有人审范围，原批准不因阅读其他 PDK 被覆盖。

## 后续 Agent 的按需回查路径

1. 从当前任务和区域记录读取原生位置、可见层及已审事实。
2. 先查本页关键词与对应官方章节；涉及材料组合查层表，涉及器件分类查 device/LVS 章节，涉及接口查接触规则。
3. 把来源事实与照片观察分开记；注明类比是否依赖尚不可见的层。
4. 仍有多种解释且影响拓扑时，生成足够宽的源图对照，让人工只裁决关键差异。

当前 [区域规划 v1](../region-planning-v1.md) 已引用这些来源。以后增加工艺知识直接在该索引扩展来源和问题，不另建无出处的“经验真值”。

## 本芯片的人审实例：与 PDK 类比分开

2026-10-18 [区域裁决](../../benchmarks/region-planning/eight-photo-regions-human-review-v1.json)确认：U01 为宽 MOS 并采用电容接法；U02 为独立衬底的一横一竖两个 MOS；U03/U04 为 dummy AA，M1 上有 dummy M1；U05 为衬底环及上覆金属；U06 为界面遮挡。这些是用户对本照片的判读，不是 GF180/SKY130 自动套用的规则。

后续遇到宽矩形、同心结构和规则方块，应优先查阅该[已审实例及范围](../region-planning-reviewed-v2.md)，再回查工艺文档补足解释。MOS 的电容用途不改变其 MOS 结构身份，亦不自动给出端口短接；dummy 不等于任意邻近金属悬空或可直接删除。U04 的 M1 仅确认语义，尚无独立定位框，不借此改变 C02。

## 2026-10-18 补读：正向设计质量门

本次在线复核如下官方来源，并用于 [v5 重建架构](../architecture/photo-stack-workflow-v5.md)，未执行规则 deck 或安装完整 PDK。

- [GF180 Layout Information §3](https://gf180mcu-pdk.readthedocs.io/en/latest/physical_verification/design_manual/drm_03.html)：存在绘制网格约束，poly/metal 允许 45°、90°转折。故当前 H/V 是本样本的重建约束，不是 GDS 或所有工艺的普遍限制，不移植微米网格。
- [GF180 官方 Contact DRC](https://foss-eda-tools.googlesource.com/globalfoundries-pdk/libs/gf180mcu_fd_pr/+/refs/heads/main/rules/klayout/drc/rule_decks/contact.drc)：关注 CO.1/2 孔尺寸及孔距、CO.3/4/6 材料包围、CO.7 邻沟道距离、CO.10/11 沟道与场区禁孔；材料归属不只靠亮点或 AA 包含关系。此处取关系检查方法，不套具体阈值。
- [SKY130 periphery rules](https://skywater-pdk.readthedocs.io/en/main/rules/periphery.html#licon)：licon.1/2/3 是尺寸/间距/形状，licon.4/5/8/11/17 涉及层间归属、包围和邻栅/混合落点；存在例外，且 licon/li/mcon 路径不能直接等同本项目 CT。

重复单元孔数/模式一致是有范围设计先验，不是上述 PDK 对所有器件规定的相同孔数。当前工艺、尺度及相关材料层不齐，正式工艺数值 DRC 待定；先实现结构/组规律/合法区检查与来源回投，不能把未知记作通过。
