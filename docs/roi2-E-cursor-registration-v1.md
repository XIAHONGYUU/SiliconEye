# E处鼠标锚点局部配准 v1

用户提供两张照片鼠标位置不变这一对应约束，并提出E接“下面第一根只有左侧有、右侧没有的M3”。原文及来源见[用户输入](../benchmarks/metal-extension/roi2-E-cursor-anchor-user-input-v1.json)。物理对应仍候选，未因“认为”自动批准。

## 结果与复核入口

- [鼠标到E完整上下文及末端放大叠图](../runs/roi2-E-cursor-registration-v1/E-cursor-aligned-review.png)
- [原像素M3窗口](../runs/roi2-E-cursor-registration-v1/M3-native-context.png)
- [M2变换到同一M3坐标窗口](../runs/roi2-E-cursor-registration-v1/M2-warped-to-M3-context.png)
- [红青叠图](../runs/roi2-E-cursor-registration-v1/M3-red-M2-cyan-overlay.png)
- [变换矩阵、来源、参数与敏感性](../benchmarks/metal-extension/roi2-E-cursor-registration-candidate-v1.json)

M2的E近似点(3278,3807)投影到M3(3316.92,3830.42)，与所指左侧独有M3的右端约(3320,3830)邻近；支持用户提出的目标身份。没有以该M3端点作拟合点。

## 脚本执行与限制

只在原生窗口[3160,3240,3380,3460]提取鼠标白色轮廓，HSV V>=230、S<=55，取最大连通分量。OpenCV findTransformECC，仿射，初始窗口平移(39,26)，500次/epsilon 1e-7，高斯7，inputMask=None。变换方向M2原生→M3原生；图像用该前向仿射warpAffine，未误用逆矩阵。复用现有registration_audit.overlay生成M3红/M2青图。

ECC 0.9954，二值轮廓IoU 0.909，轮廓拟合距离P95为1px。未参与拟合的黄色UI区域中心偏差约0.13px；该检查仍属于同一屏幕标记，不是独立芯片结构验证。六组阈值试验使E投影范围x3315.61..3320.70、y3828.30..3832.04，相对主方案最大偏移4.34px；此范围是阈值敏感性，不是置信区间或物理误差预算。

E位于鼠标轮廓之外约465px，属于外推。鼠标不动不单独证明层间芯片显示未平移/缩放；用户约束、局部畸变及原生坐标粗点仍影响精度。本结果可用于集中核查该M3对应，尚未获得精确芯片结构配准用途验收，不外推整片或其他区域。只有拟合成功不能证明电气接通。

当前case v11未改，无新确认边。E曾误定V1后被更正、旧D侧M3及旧M1竖线的否决保持有效。下一人审仅核查图示E是否对应所指出M3右端；通过后才能把该M3纳入gate网络并检查全导体分支。来源哈希、case来源/人审事件与状态不变、矩阵正逆往返及图稿目视检查通过。无生产代码修改、无全套测试重跑、未推送。

## E目标人审通过（case v12）

用户确认“是的，就是指的这一根M3的右端”；[独立裁决](../benchmarks/metal-extension/roi2-E-M3-endpoint-review-feedback-v1.json)绑定图稿与变换。E→指定M3右端已确认，M2/M3桥接按层次归一为V2，不恢复旧V1结论。批准目标身份不批准整片精确配准或每个像素边界。

[case v12](../benchmarks/block-case-v1-roi2-E-M3-endpoint-reviewed-v12.json)新增Q1.G到R2_M3_E_segment_01的确认映射，无新端子并网；来源/事件/schema/导出及矩阵不变检查通过。[沿线点亮图](../runs/roi2-E-M3-reviewed-v12/E-M3-lit-F-review.png)、[范围/分支观察](../benchmarks/metal-extension/roi2-E-M3-extent-candidate-v1.json)保留几何候选与未知。

原图亮线右端粗中心约(3320,3840)，先前投影点(3317,3830)只是近似参考，不以二者约10px差当配准误差测量。向左可见段约到F=(2485,3871)，尚未确定F过孔；附近M2短端约(2470,3838)仅候选。该处距鼠标远，逆投影约(2446,3839)，有约24px横向偏差，不作精准落点。中段其他接入及全网覆盖仍未知，未自动并入M2 F或M4，无生产代码变更/全套重测/推送。

## F→M2已确认（case v13）

用户原文“F 通过过孔接到右下图紫圈所示的 M2 短端”；[独立反馈](../benchmarks/metal-extension/roi2-F-M2-review-feedback-v1.json)绑定前次图稿与观察。[case v13](../benchmarks/block-case-v1-roi2-F-M2-reviewed-v13.json)确认Q1.G到R2_M2_F_segment_01局部映射，M2/M3过孔归一为V2，不推定新器件端子。

[点亮图](../runs/roi2-F-M2-reviewed-v13/F-M2-lit-G-review.png)沿显式原生M2候选路径(2478,3839)→(2459,3841)→(2458,3957)→G约(2438,3959)，未并入相邻平行竖线或底部阵列。[新观察](../benchmarks/metal-extension/roi2-F-M2-extension-candidate-v1.json)中G的过孔身份/目标导体均未知，几何及其他分支覆盖未验收。M1/M2/M3原生宽窗口同时保留，不把未配准的图并排当对应。

来源、人审事件、schema、导出及状态检查通过；仅Q1.G增加F局部M2映射，确认矩阵与其他端子行保持v12不变。无生产代码更改、无全套重测、未推送。

## F/G接M3、G接MIM一端（case v14）

用户确认“F与G均没有接到M1……而是接到了M3，而在下方接入的是MIM电容那一端”；[独立反馈](../benchmarks/metal-extension/roi2-F-G-M3-MIM-review-feedback-v1.json)绑定M1/M2/M3宽范围图。F/G局部不接M1不等于整个gate网络与M1隔离。

[case v14](../benchmarks/block-case-v1-roi2-G-M3-MIM-reviewed-v14.json)新增gate到G侧M3接入导体的确认映射，不编造精确落点/几何。确认矩阵及其他端子行不变，来源/人审/schema/导出通过。G是M2/M3桥接，按层次记V2。

[MIM伴随拓扑记录](../benchmarks/metal-extension/roi2-gate-MIM-topology-reviewed-v1.json)明确所指MIM一端与Q1/Q2共栅网同网，[局部关系图](../runs/roi2-G-MIM-reviewed-v14/gate-MIM-topology.png)显示电容隔开的两端。临时ID R2_MIM_01及P1/P2仅作稳定引用，不推定电容单元数量、容量或上下极板；P2去向未知，不能将电容两端并网。

现有v1 case只支持MOS，不把MIM伪装为MOS，也不声称通用导出已支持电容。伴随结构记录保留证据并供后续类型扩展使用。完整金属范围/G侧M3路径/其他分支尚未闭合，MIM一端达到为本次连接追踪节点，下一重点为定位另一端并补局部电路关系，而不是继续逐CT追问。无生产代码变更、无全套测试重跑、未推送。

## 2026-10-17：MIM另一端P2定位描述已给出

[用户原话与来源](../benchmarks/metal-extension/roi2-MIM-other-terminal-review-feedback-v1.json)指定：下方三个方形电容的最左端最上面那条，金属未贯穿全图，可结合M2已伸到电容顶部的连接判读。[伴随拓扑v2](../benchmarks/metal-extension/roi2-gate-MIM-topology-reviewed-v2.json)将P2描述身份记录为已审，具体外部节点仍未知。图片最上方不等于工艺上极板，所指三个不等于全芯片总数；不擅自确定三联组像素范围、P2精确中心线或把两端并网。

[宽范围复核图](../runs/roi2-MIM-other-terminal-review-v1/MIM-P2-wide-review.png)并排保留M2/M3相对位置上下文，原生窗口均为[1200,3450,4200,4284]，但不是精确跨层像素配准。[电路关系图](../runs/roi2-MIM-other-terminal-review-v1/gate-MIM-P2-located-topology.png)展示P1接共栅网、P2定位到顶部非贯通金属但外部去向未明。

case v14未改，全部端子映射/矩阵不变；原P1关系不变，P2无新外部same_net断言。来源/像素裁剪及case来源/事件/状态复算通过，未改生产代码、未全套重测、未推送。下一步先落实这条有限长度金属的具体走向与末端，再追外部连接；不能以未定位的语义窗口宣称全金属点亮已完成。

## 2026-10-17：将P2描述落实到H实图候选

用户重复定位描述，上一轮只保存语义与未标线宽图不足以核查。本轮新增[H实图候选](../runs/roi2-MIM-P2-marked-v3/P2-H-wide-marked-review.png)，在当前选定的三块电容A/B/C中，把A顶边有限段标蓝H；M2顶部接入排标黄，附A顶部原图与同区域标注对照。

[候选坐标与来源](../benchmarks/metal-extension/roi2-MIM-P2-pixel-candidate-v1.json)记录M3 H约(1640,4025)→(2470,3990)，M2顶部排约(1640,4005)→(2420,3973)。这是AI将已审描述映射到像素的提议，三联组选择和H边界/导体身份均待图像复核，不能用已审语义替代像素批准。未把原G点当P2落点，未在此声称精准配准。

原图哈希、case来源/事件/schema与v14状态不变检查通过。无新生产代码、未重跑全套测试、未推送。下一步只核对这张具体H图，避免继续抽象复述或重复请求已经提供的描述。

## 2026-10-17：H确认执行，伴随拓扑v3

用户原文“蓝色H候选无误，确认执行”；[独立反馈](../benchmarks/metal-extension/roi2-MIM-H-review-feedback-v1.json)绑定H候选、旧图及拓扑。H身份及粗原生位置正式关联MIM P2，[伴随拓扑v3](../benchmarks/metal-extension/roi2-gate-MIM-topology-reviewed-v3.json)保留该确认，不将其提升为精确材料边界或全部M2黄色排过孔的批准。

[新已审宽图](../runs/roi2-MIM-H-reviewed-v4/H-P2-reviewed-with-context.png)蓝色显示H，橙色为观察到的左侧纵向汇流条延伸候选，约(1640,4025)向下到(1649,4283)触及原图底边。[追踪记录](../benchmarks/metal-extension/roi2-H-continuation-candidate-v1.json)保留覆盖缺口；相邻电极/B/C/外部供电不自动接入。整个P2外部走向及边界完整性仍未知。

确认case v14和P1同网关系不变；来源哈希、case来源/事件/状态、P1/P2未并网检查通过，图稿目视核查。无生产代码修改，无全套测试重跑，未提交推送。
