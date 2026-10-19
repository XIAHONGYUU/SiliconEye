# 2026-10-19：从照片投影转向AA相对约束的POLY重建

[打开v3复核页](../assets/poly-full-frame-v3/index.html)。页面下方将上版联合规则图与本轮AA约束重建并列。照片拟合点和来源叠加另放在可展开证据区，不能当作最终设计位置。

## 人工反馈与本轮处理

[反馈](../../benchmarks/poly-full-frame-v3/human-review-v1.json)：普通MOS通常为矩形，批量凸形/狗骨头不合适；U10正确；F05大MOS偏小且缺gate连接范围；联合图POLY相对AA偏上、侵环、未伸过下端；右侧短排有栅不交叠AA。用户明确以重建GDS的相对关系和正向设计验证为核心，允许有依据地联合修订AA/POLY工作几何。

- **撤回普通MOS的批量宽端部模板**：保留端部长度，改为等宽矩形；没有用删掉端部来换矩形。当前664个矩形对象（含18条电阻，不是664个MOS）。U10两条已审显示几何为独立保留例外，原生轮廓和原规则坐标不改。
- **U10通过**：[采用记录](../../benchmarks/poly-full-frame-v3/U10-acceptance-v1.json)。不新增器件数或CT连接结论。
- **F05大MOS新候选**：暂定位为U01宽MOS G27/G28，扩大完整矩形高度及接触侧范围，在下拉框F05-GATE单独展示。这个定位解释与新增边界未获人工确认；不能声称gate接触点已经正确恢复或分配CT。
- **下中部联合重建**：140条已有候选按明确行→器件AA关系、共享列和观察宽度重建。数量/ID不因满足规则而增加，原生照片证据与4个既有局部已审记录不改。

## 结构关系如何修正

不对POLY作一次整图下移，而是分别用指定器件AA的范围确定矩形栅体上下端、共同有效横向范围确定匹配排共享列。栅两端伸出、与环AA间距、非目标AA隔离分别检查；空间不够时报告冲突，禁止偷偷缩栅、挪AA或合并材料来换PASS。

本轮可只调整POLY满足关系，AA模型不动；将来AA确有证据矛盾时可提出独立的AA工作候选，不把AA摄影坐标永久冻结为GDS坐标。

| 在当前AA模型和指定关系上的检查 | 原投影候选 | 本轮重建候选 |
| --- | --- | --- |
| 指定AA无交叠 | 2 | 0 |
| 与环AA有面积交叠 | 92 | 0 |
| 上端未满足本轮伸出预算 | 12 | 0 |
| 下端未满足本轮伸出预算 | 140 | 0 |
| 与非目标器件AA有交叠 | 0 | 0 |

原无交叠对象为G41r2-P11/G43r2-P11。本轮指标使用明确的目标AA重新核查，与上版“最近AA距离超预算1处”不是同一个指标。表格是对所构造候选的几何自洽检查，不是新发现并独立证实的缺陷总数、材料准确率或真实工艺DRC结果。

预算是相对布局像素：本例栅宽30/32、两端伸出8、避环至少3、侧边余量8、栅间距至少8；这些只是当前候选工作参数，不能套用为本芯片PDK数值。目标AA关联、器件数量和真实边界仍依赖照片与人工检查。结构合理不等于制造数据已经恢复。

## 原始证据、设计候选与输出关联

[完整模型](../../benchmarks/poly-full-frame-v3/model-v1.json)的working_reconstruction_layers指定AA版本和joint/report.json中140条joint_layout_outline作为下中部设计候选。旧layout_outline是摄影来源复核画布，不冒充最终AA共同版图；照片坐标、局部已审坐标和新重建坐标分别保存。

[联合记录](../assets/poly-full-frame-v3/joint/report.json)保留photo_projected_layout_outline、明确AA目标、重建坐标、逐对象约束检查。普通源图未被挪动或扭曲；[顶层架构](../architecture/layout-reconstruction-v1.md)固化这一区别。

照片对应失败时禁止画误导叠加；但明确AA/器件关系的设计候选不再依赖照片拟合门，可以单独生成规则图，该失败路径有独立测试。本轮来源对应仍为AI候选，原6.35/7.98px残差仅供照片证据追溯，不作为本次设计位置目标。

## 验证、范围与下一门

[参数](../../benchmarks/poly-full-frame-v3/spec-v1.json)、[前后比较](../../benchmarks/poly-full-frame-v3/before-after-v1.json)、[核查](../../benchmarks/poly-full-frame-v3/verification-v1.json)、[约束实现快照](../../benchmarks/poly-full-frame-v3/constraint-source-snapshot-v1.py)。

30项相关测试及Ruff通过；包括照片对应失败不阻止已明确AA关系的设计候选、无空间时不能缩栅骗过避环门、普通凸形模板拒绝、已审范围保留、目标交叠/伸出/隔离与共同列检查。4个既有局部和U10两条显示几何不变、18条电阻规则几何不变、15项冻结来源不变，原生/复核规则几何不交叠，U19/U22排除范围无交叠；页面JS/资源/SVG核查通过。浏览器交互未自动实测。

本轮没有完成全幅AA/POLY联合布局；其他区域的新材料/边界仍待核，20个详细形状观察框、右沿U21等未关闭。没有真实PDK DRC、LVS、物理W/L或新增CT/网络结论，没有Git提交/推送。

下一门只核查联合图的真实相对关系与F05-GATE扩大范围是否包含实际gate连接处；U10不重问，不要求重审所有块或逐个CT。

```bash
.venv/bin/python -m silicon_eye.poly_full_frame --root . --spec benchmarks/poly-full-frame-v3/spec-v1.json --output runs/新的目录
```

代码与页面快照、完整资产分别保存在benchmarks/poly-full-frame-v3与docs/assets/poly-full-frame-v3。开发a–d为实现/显示构建，不是多次独立评测。
