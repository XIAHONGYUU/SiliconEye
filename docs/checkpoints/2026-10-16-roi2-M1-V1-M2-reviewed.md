# ROI2 gate连接已复核至M2

用户确认：“核对无误，这处M1的确是连接到下图黄色短竖向段的上端”。[反馈原文与图稿绑定](../../benchmarks/metal-extension/roi2-M1-V1-M2-review-feedback-v1.json)独立保存。

已确认链条为R2_Q1.G→gate端CT→所示M1局部段→两条平行M1连接处V1→M2短竖段上端。新增[case v7](../../benchmarks/block-case-v1-roi2-gate-M1-V1-M2-reviewed-v7.json)用既有terminal_maps_to_conductor及human事件登记R2_Q1.G到R2_M2_gate_segment_01；原M1对应保留，所有旧case、候选和否决保留。

此确认限定局部对应；没有新增端子并网、没有自动登记Q2的独立CT路径或其他器件连线。case来源/图片尺寸/人工事件/schema核验通过，四端连接矩阵及同网组与v6一致。新状态ID：1162eb1eebc51165ed0f6481cb6f02fd6eeb1812a69d995fe8681ce99924de37。

## 下一段观察（尚未获批）

[图稿](../../runs/roi2-M2-to-M3-survey-v1/M2-path-V2-review.png)显示绿色已审M2入口和黄色AI延伸候选。可见短竖段接叉形横条，支路向下延伸至另一组叉形结构；中途右向短支路末端约(2231,3332)为V2搜索候选。没有将相邻长竖线、下方平行回路或孤立亮块自动并入。

[声明观察](../../benchmarks/metal-extension/roi2-M2-extension-V2-candidate-v1.json)保存原生路径、候选V2窗口与来源。亮端可能只是金属末端，CT/V2身份不能由亮度自动确定，因此先核查其是否为V2，再选择对应M3。M3存在多条重复平行线且此处没有已接受的跨层配准，当前不指定M3导体、不高亮M3/M4。

本轮无生产代码改动；用现有case验证和block导出检查映射升级/矩阵不变，核对来源哈希，并目视检查复核图。未重跑全套测试，之前248 tests不作为本次识别正确的证据。未推送GitHub。

## 后续V2复核

用户随后确认所圈亮端为V2，[反馈原文](../../benchmarks/metal-extension/roi2-V2-review-feedback-v1.json)另存。M3对应仍候选：[对照图](../../runs/roi2-V2-M3-review-v1/V2-M3-review.png)、[case v8](../../benchmarks/block-case-v1-roi2-V2-reviewed-M3-proposed-v8.json)。v8仅追加未审M3提案，确认端子映射与矩阵保持v7状态；不把V2身份确认当作特定M3轨道批准。

## M3条件延伸

进一步检查候选M3可见路径，末段存在屏幕鼠标和黄色UI标记遮挡，未将其当作V3，也没有补画遮挡区连接。[扩展复核图](../../runs/roi2-V2-M3-review-v1/V2-M3-extended-review-v3.png)和[新观察](../../benchmarks/metal-extension/roi2-M3-conditional-extension-v2.json)保留此缺口。M3接入对应仍需复核，M4未赋予gate网络。
