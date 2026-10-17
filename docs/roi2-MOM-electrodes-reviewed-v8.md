# MOM电极归属更正与P1可见网络

用户确认：“是的，橙色这异端的梳齿以及右侧母线，才是电容的另外一端。”结合上一轮“G是连接到蓝色的这根弦”，现在物理归属已闭合：

- P1为Q1/Q2共栅连接的G/H侧，包含此前确认的H→J向左延续、K中间纯竖向M2、L1经V1接M1的物理链。
- P2为橙色梳齿及右侧母线。此前把H/K/L1叫作P2是端口归属错误，已更正；不是电容两端短接。
- 电极身份确认不等于精确掩码、所有跨层孔或全部阵列归属确认。旧文件名带P2的H侧掩码仍可作为图像候选使用，不覆盖历史文件。

## 当前记录和图稿

[人审原话与来源](../benchmarks/metal-extension/roi2-MOM-opposite-electrode-review-feedback-v1.json)、[当前拓扑v8](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v8.json)和[覆盖观察v2](../benchmarks/metal-extension/roi2-P1-corrected-coverage-v2.json)。v8取代v7暂挂冲突作为当前解释，旧裁决原文和源哈希不变。旧金属ID中的P2字样通过显式别名映射到当前P1金属ID；电容P1/P2端口ID本身不交换。

[更正后三层总览](../runs/roi2-P1-ports-reviewed-v8/P1-corrected-three-layer-review.png)：绿色为P1已审链参考及图像分量候选，橙色为已确认身份的P2电极候选边界，黄色为A侧M2下方三叉延伸候选。三层保持各自原生坐标；参考线不是精确分割，也不表达通过照片遮挡区的像素边界已知。

[A侧M1/M2宽图](../runs/roi2-P1-ports-reviewed-v8/A-lower-fork-M1-M2-review.png)：可见A所在M2竖线向下到达三叉顶部，作为AI同层连续候选。选取ROI[2000,3000,320,600]，高斯7×3、sigma=(1.4,0.6)，8连通，不补断口。阈值120、140时五个参考点同属非背景分量；160、180发生断裂。该结果支持检查连续结构，但不能替代跨层过孔证据。下方三个端部是否经V1接入M1尚不明确，不能把邻近M1直接并网。

当前仍不能宣告全网完成：A下分叉跨层去向、A—C中段额外M2接入、MOM各层完整电极范围、M4/V3落点仍有未闭合处。M4原图已作宏观复查，无足够证据新增P1接口；图外去向保持未知，不要求额外照片。

## 验证

v8全部源文件哈希、当前端口映射、P1/P2未被并网检查通过。原case v14继续通过schema、来源和状态复算，state_id仍为702dbe14c70bd5961b7307b5f3458301202aa370a8b9be372ce2940ddd044e67。通用case尚不支持电容，当前电容结论在伴随拓扑中，不伪装成通用导出已实现。图稿已目视检查。原始照片未改；未新增生产代码、未全套重测、未推送GitHub。

## A侧叠图撤回

用户指出先前单锚点粗仿射未对准，三条M2应落在左侧M1且可见V1。旧叠图及投影点不再作为落点参考；源哈希与矩阵回算通过不能挽救结构对应错误。先核对[原图标记](../runs/roi2-A-V1-correspondence-review-v2/A-V1-correspondence-wide-review.png)和[纠正记录](../benchmarks/metal-extension/roi2-A-overlay-rejection-and-V1-markers-v2.json)，再拟合新局部变换。V1存在已由用户指出，当前仅需明确原生标记身份，未新增拟合或电连接。

## A侧456身份确认及局部重投影

用户“是456三条线”明确M2 L/M/R到M1 4/5/6，结合前一轮V1说明，三处物理接口写入[拓扑v9](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v9.json)。不恢复旧粗仿射。新[局部投影](../runs/roi2-A-456-local-overlay-v3/A-456-corrected-local-overlay-review.png)只用外侧4/6拟合相似变换，中间5作为未参与拟合的同组检查，约5px残差；不是独立结构验收或整片精度保证。仅显示M2端部附近约60px段，不外推全三叉与上游旧V1点。方向、点回算、来源绑定和图稿目视检查通过；更精确的中心、材料端子身份与整网覆盖仍未闭合。

## 456局部投影验收与材料接口下一步

用户“确认无误”接受已展示的局部投影；见[反馈](../benchmarks/metal-extension/roi2-A-456-overlay-review-feedback-v1.json)与[当前拓扑v10](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v10.json)。范围不扩展到整叉/整幅精度或源漏判断。沿三条M1暂未发现明确同层新分支，含CT的poly照片上下文支持下方MOS阵列扩散端接入候选；见[整组宽图](../runs/roi2-A-456-material-survey-v4/M1-to-CT-array-interface-review.png)。引用既有已审M1/poly宏观profile作上下文，一次重采样，未拟合新精确CT变换。暂不赋器件端子或源漏，不把金属止于可见位置解释成电气断开。

## 456扩散接入已审，回到整网覆盖复核

用户“核对判断正确”批准整组三条M1经CT接下方MOS阵列扩散端，[当前拓扑v11](../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v11.json)记录为确认接口；不指定源漏、器件数量或未审端子。该分支到器件端子为止，不把MOS沟道当金属继续遍历。下一处整导体接口为M3 A—C的额外M2接入完整性；[宽图](../runs/roi2-P1-diffusion-reviewed-v11/AC-extra-M2-interface-review.png)保留两层各自原始坐标，没有使用试算变换作精确投影。B只作邻近短端候选，不能凭接近判同网。源绑定、确认状态及P1/P2未并网检查通过，仍不宣告全网完成。
