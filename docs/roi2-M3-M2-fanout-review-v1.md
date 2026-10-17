# ROI2 整根M3的M2分支复核 v1

用户要求：这根M3可能连接两根M2，找到M3后需找出全部连接M2。本轮将检查范围从单条上行路径改为整根候选导体；用户尚未批准之前的M3身份。

- [完整复核图](../runs/roi2-M3-M2-fanout-review-v1/M3-all-M2-review.png)
- [原生坐标、来源哈希及覆盖缺口](../benchmarks/metal-extension/roi2-M3-M2-fanout-candidate-v1.json)
- [图稿来源清单](../runs/roi2-M3-M2-fanout-review-v1/manifest.json)

| 位置 | M2原生像素约值 | 观察与状态 |
| --- | --- | --- |
| A | 2231,3332 | 用户已确认V2身份；与M3候选左端2252,3369的对应仍未审 |
| C | 3275,3308 | 右侧竖向M2顶部向右亮端，可能接M3右端3320,3330；新V2/连接均候选 |
| B | 2330,3300 | 邻近M2短端，需要排除相邻M3，连接未知 |
| D | 3275,3404 | 右侧较低短端，可能与C同一M2；不可重复计为不同导体 |

中段M2搜索带2380..3150、3230..3400存在多处交叠，未有可靠跨层配准或V2证据。鼠标/UI遮挡部分右侧M2及候选M3，遮挡处不补线。各层坐标分别记录，不用近邻偏移证明连接。当前未能确定全部连接，也不能认定恰好两根M2。

下一人审集中核查A、C是否对应所示同一根M3；此后继续排查中段及遮挡。即使A/C批准，也仅新增这两处对应，完整性仍需独立闭合。过孔数和不同M2导体数分别记录。

本轮仅新增观察与图稿。case v8未改，M3仍candidate，确认端子映射与矩阵不变；M4暂缓。图稿目视检查、来源哈希及现有case来源/状态复算记录见runs内verification.json。无生产代码变更，未重跑全套软件测试，未提交推送GitHub。

## 后续人审：A/C均确认

用户确认“A、C 分别连接图中这根 M3 的左右两端”。[独立反馈](../benchmarks/metal-extension/roi2-M3-A-C-review-feedback-v1.json)保留原话及旧图哈希；[v9 case](../benchmarks/block-case-v1-roi2-M3-A-C-reviewed-v9.json)登记gate到M3及M2 C的确认映射，[新图](../runs/roi2-M3-M2-reviewed-v9/M3-A-C-confirmed.png)展示结果。上文是原候选阶段，不覆盖历史状态。

M3跨遮挡的电气连续性随“同一根M3”对应获得确认，但被遮挡的像素形状仍未知。A/C是两个局部接入，不代表两条独立电网或只有两处连接。[清单v2](../benchmarks/metal-extension/roi2-M3-M2-fanout-reviewed-v2.json)仍标记coverage incomplete。中段原生窗口复看未见足以新增第三连接的清晰V2，继续保留未知；B/D及C所接其他器件端子均未裁决。

来源/人工事件/schema及导出验证通过；确认矩阵、其他端子映射不变，仅Q1.G增加M3/C段。未改生产代码，未重跑全套测试，未推送。
