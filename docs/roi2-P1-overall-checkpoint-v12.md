# P1整体点亮复核：v12

用户“中间无M2接入”确认A—C所指M3中段没有额外M2接口。结合已有两端确认，该段分支复核已完成；邻近B不画入这根M3，不推断B在全局必为不同网。

## 已审内容

| 内容 | 当前状态 |
|---|---|
| Q1/Q2共栅经CT/M1/V1/M2(A)至M3(A—C) | 既有接口已审 |
| A—C两端接入、中段无额外M2 | 已审，当前段复核闭合 |
| C/E→第二根M3(E—F)→F/G→H | 既有接口已审 |
| 电容P1=G/H侧，P2=橙色梳齿及右侧母线 | 电极身份已审，不并网 |
| H→J→K中间M2→L1/M1 | 既有物理链保留并归入P1 |
| 下三叉M2经V1接M1 4/5/6，再经CT接下方MOS扩散端 | 局部接口已审，源漏/器件数量未知 |

[当前拓扑v12](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v12.json)、[新增人审反馈](../benchmarks/metal-extension/roi2-AC-no-middle-M2-review-feedback-v1.json)、[整体覆盖记录](../benchmarks/metal-extension/roi2-P1-overall-coverage-v12.json)。

## 整体图与下一处裁决

[P1已审路径整体图](../runs/roi2-P1-overall-review-v12/P1-reviewed-route-overview.png)按每层原生坐标分别绘制，没有做新的跨层投影。绿色是已审路线参考及图像分量候选；M2下三叉同层走向仍是可见连续性参考，橙色P2是另一电极。线宽、分量边界及遮挡区均不表示精确分割已经验收。

当前显示的是已确认路径，不能宣告全网物理覆盖完成。剩余重点是[MOM区域额外出口](../runs/roi2-P1-overall-review-v12/MOM-P1-extra-exits-wide-review.png)：除H/J/K/L1之外，是否还有P1向外的M1/M2接入或V3/M4接口。现有照片未找到可靠额外接点，不把未找到当成已证实没有。电容内部未审多层指状线边界仍保留未知；不因多层重叠补接，不穿过电容介质或MOS沟道扩网。

照片边界之外保持未知，不要求额外照片。源哈希、确认范围及P1/P2未并网检查通过；图稿已目视检查。无新变换、无生产代码修改、无全套重测、无推送。旧单锚点错误投影仍撤回。

## v13：MOM额外出口已审无，剩余A上三叉

用户“没有其他金属向外引出”闭合现有照片MOM P1出口问题；见[反馈](../benchmarks/metal-extension/roi2-MOM-P1-no-extra-exits-review-v1.json)、[当前拓扑v13](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v13.json)。旧v12图中的MOM出口未决提示为历史状态。该裁决不覆盖其他区域或照片外；精确像素分割仍非本阶段验收对象。

汇总可见M2支路后，A上三叉尚有U1/U2落点未明确，U3到共栅M1已审。用[原图宽图](../runs/roi2-P1-MOM-closed-v13/A-upper-fork-interface-review.png)核对是否同一M1，而不是用错误旧变换强行投影。若同一导体不新增独立网，若其他导体则继续追踪；仍未提前宣告整网完成。
