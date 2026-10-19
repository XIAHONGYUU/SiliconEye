# 2026-10-19：POLY局部规则复原对照

用户批准五步推进，本轮完成AA冻结、POLY历史接续与首轮局部对照。全幅扩展和skill封装等待局部方法验证。

[打开切换复核页](../assets/poly-reconstruction-v1/index.html)。左侧原始照片，右侧可切换A直接观察、B0算法、B1规则几何、叠加及未知；原始红/蓝人工标注另有链接。

| 视图 | 继承事实 | 本轮新增核查 |
| --- | --- | --- |
| P-H01 横向双栅 | V3两栅材料身份与局部POLY不互连已审 | 蓝色主体位置、宽度是否合理，较黄色是否改善 |
| P-V01 竖向双栅 | ROI2 Q1/Q2身份和粗位置已审 | 蓝色向两侧扩展是否贴合，不将旧core当作完整边界 |
| P-E01 端部上下文 | 同一V3横向案例，不是第三个独立样本 | 遮挡/端部保留未知，暂不判断完整接触引出形状 |

## AI检查与限制

横向两条主体仍分开，竖向两条主体也无交叠。横向候选平均角点移动约2像素；竖向Q1约4.37、Q2约2.58像素。这些是变化量，不是误差或准确率。竖向B1较旧core更宽，可能补回主体宽度，也可能多收了边缘；没有人审前不认定改善。

A主体及搜索域由AI指定，GrabCut不是独立发现。B1暂作几何候选，旧修正mask未被替换。只恢复可见主体片段，横向裁切边和竖向上下边不是已测栅端。CT候选只标遮挡，未分配连接；没有AA→POLY投影、CT重提、器件/网络推断或全幅训练。

## 可复核证据

- [冻结基线](../../benchmarks/poly-reconstruction-v1/baseline-v1.json)、[参数](../../benchmarks/poly-reconstruction-v1/spec-v1.json)、[报告](../../benchmarks/poly-reconstruction-v1/report-v1.json)、[核查](../../benchmarks/poly-reconstruction-v1/verification-v1.json)。
- [通用工具](../../silicon_eye/poly_reconstruction_review.py)、[冻结代码副本](../../benchmarks/poly-reconstruction-v1/source-snapshot-v1.py)。35项相关测试与Ruff通过；原生至布局四角重投影最大误差约0.000055像素，仅验证记录自洽，不验证照片配准或物理尺寸。
- 15项冻结来源哈希、原AA及旧POLY未知mask不变；布局HV、对象无交叠、未知-1、生成清单及页面资源/JS语法通过。浏览器交互未自动实测。
- [限定证据归档](../../benchmarks/evidence/poly-reconstruction-v1d-evidence.zip)、[45项清单](../../benchmarks/poly-reconstruction-v1/evidence-inventory-v1.json)。包含本轮原生窗口/候选/坐标记录及旧原标注、标注坐标、已修POLY和两类未知；空目录恢复后逐项哈希相符。原图在data/，不重复打包；其他旧runs未纳入。

下一步只核查新主体位置与宽度，择优接续，局部方法通过后推进全幅。旧身份/断开关系不重问，没有新增Git提交/推送。

## 后续人工裁决与方法纠偏

[反馈v2](../../benchmarks/poly-reconstruction-v1/human-review-v2.json)：P-H01蓝色位置/宽度合理；P-V01较黄色贴合但明显偏小，完整外形不通过。旧core加小范围法向优化不能恢复完整尺寸。先结合AA沟道及POLY宽上下文识别完整外形，再使用算法修边；新增完整范围门。

[当前上下文页](../assets/poly-reconstruction-context-v2/index.html)仅并列原图，未配准/投影、未重提取或生成新轮廓。原v1报告与页面保留历史，不把本次反馈扩展为完整栅端或全幅批准。
