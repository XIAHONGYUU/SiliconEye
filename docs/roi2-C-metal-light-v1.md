# C侧金属点亮复核 v1

目标：从已审C侧M2接入点延伸，将所有相连金属点亮。当前完成可见M2全段的候选点亮与两个跨层去向调查；尚未完成全部确认网络，不能称为全网提取完成。

- [全幅复核图](../runs/roi2-C-metal-light-v1/C-all-metal-review.png)
- [路径、原生坐标、缺口及来源](../benchmarks/metal-extension/roi2-C-all-metal-trace-candidate-v1.json)
- [现有高亮格式的逐直段候选](../benchmarks/terminal-highlights/roi2-C-extension-v1)
- [来源/几何/case状态检查](../runs/roi2-C-metal-light-v1/verification.json)

C接入约M2(3275,3308)。可见竖线沿x约3255..3257向下到y3807，中间D亮短支约(3278,3404)，底部E约(3278,3807)。鼠标遮挡y3340..3397部分，显示留空；不凭接近而补接。

D可能对应M3(3320,3437)附近长横线，与原A—C的M3不同。候选长横线可见范围从原照片左边界约(0,3545)到右端约(5108,3378)；向左超出原图，是物理覆盖缺口。没有接受的M2/M3精确配准，这处对应仍需人工判断。

E可能接M1孤立竖线下端约(3347,3744)，其上端约(3348,3444)靠近横向金属但未确认接通。仅点亮该候选竖线，不扩展到附近横条；M2→M1过孔/对应仍未审。M4局部图已检查，未找到足以建立新连接的证据。

待集中确认：C竖线在鼠标遮挡处是否连续；D是否接所示另一根M3；E是否接所示M1竖线下端。它们决定后续是否允许扩展，不以“继续推进”替代物理批准。即使确认，D侧M3出照片的覆盖缺口仍保留。

黄色路径为AI显式候选，脚本按现有TerminalHighlight格式校验逐直段多边形并生成标注副本/mask；不是自动分割、精确边界或新确认事实。原图、旧候选、人工记录及case v9不变。本轮无生产代码变更，无全套测试重跑，未推送GitHub。

## 用户复核更正（v10，以本节为当前结论）

[人工反馈](../benchmarks/metal-extension/roi2-C-D-E-review-feedback-v1.json)确认C连续，否决D接所示另一M3、E接所示M1竖线下端，并确认E下端有V1。上述旧候选保留为历史，不再参与当前高亮。D的原话包含超出图片，不据此补出具体走向，也不再把被否决长M3的左端出框解释成当前网络的覆盖事实。

[新case v10](../benchmarks/block-case-v1-roi2-C-continuity-E-V1-reviewed-v10.json)仅添加已确认C下段M2映射。V1身份在反馈中保存，不强造schema谓词。端子矩阵与其他端子行不变，未加入被否决M1/M3。

[更正复核图](../runs/roi2-C-E-V1-review-v2/E-V1-M1-review.png)并排展示E端与M1原图检索窗，1—5仅相邻横线的检索编号，非落点候选批准。当前没有可靠精确配准，不能唯一判定E下端V1对应哪根M1；需要这个关键对应，才能继续点亮。所有已审C连续性与A/C对应保留，精确边界仍未知。

## E层次更正（v11，替代上节E=V1）

[最新人工反馈](../benchmarks/metal-extension/roi2-E-via-layer-correction-v2.json)确认E不接M1，观察到M2有孔、M1无对应孔，认为应接M3。历史“E下端V1已确认”现已撤回，原文及旧case保留。M2孔的观察已确认，V2/M3去向仍为候选，不能仅凭孔在哪张照片上出现确认具体目标。

[case v11](../benchmarks/block-case-v1-roi2-E-via-layer-corrected-v11.json)采用中性过孔ID，不改变确认端子映射与矩阵。[M3宽范围原生裁剪](../runs/roi2-E-M3-review-v1/m3-wide-native.png)未缩放/增强/标注；已检查局部多条横线，尚不能唯一定位E目标。M2/M3精准配准未验收，不以同像素或旧D候选替代对应。
