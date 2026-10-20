# CT迁移反馈后的局部修订

2026-10-20。用户认可W1宽MOS与E1电阻上端，指出邻侧六管栅端不能任意延伸，R1环横纵漏孔。

[复核页](../assets/ct-transfer-revision-v2/index.html)支持规则联合图、源图标记、纯原图切换。只需检查两处变化。

1. 六管共栅：保持六指、共栅关系与11孔，按原图栅孔横向高度和已审宽MOS相对端部，将共栅带底部1516缩至1507，孔y下降量-5。源图两组栅孔y中位1319/1320接近，原规则图的额外下伸缺乏依据。精确边界仍为候选；未将邻管尺寸当作工艺测量。
2. 环：旧记录只含稀疏观察，且旧顶部孔列相位/节距排除了真实亮点。此次直接读原图带状灰度剖面，均值后sigma2平滑，局部最大、亮度≥185、局部对比≥6，再按照片节距拟合。横向32、纵向15个候选，所有峰及未选观察均保留，不凭格点补孔。侧边ROI延长至y2065，顶部范围保持局部。

[参数与输入锁定](../../benchmarks/ct-transfer-revision-v2/spec-v1.json)、[人审反馈](../../benchmarks/ct-transfer-revision-v2/human-review-v1.json)、[修订台账](../../benchmarks/ct-transfer-revision-v2/ledger-v1.json)、[质量门](../../benchmarks/ct-transfer-revision-v2/report-v1.json)、[验证](../../benchmarks/ct-transfer-revision-v2/verification-v1.json)。

72个CT完整记录未改，11孔仅改设计几何；原34个环候选退休到台账，替换为47候选，总数130。全部AA、694个无关POLY、六栅指子记录不变。旧v5锁定与v1迁移文件不覆盖，新几何未冒充已审。

423项测试和相关Ruff通过；测试包括均匀亮带不造孔、缺峰保留空槽、阻止已审孔及来源证据变化、阻止无关材料变化。静态SVG/PNG、链接和模拟切换通过，未自动实测真实浏览器渲染。

范围仅左上环子段、局部相对几何；不声称全幅CT、真实工艺DRC、M1包围或电气网络完成。未提交/推送本轮CT工作。

## 本次人审收口

用户逐项回复“1.评审通过；2.评审通过”。[追加裁决](../../benchmarks/ct-transfer-revision-v2/human-review-v2.json)及[验收锁定](../../benchmarks/ct-transfer-revision-v2/acceptance-v1.json)确认本次显示范围；不改写原模型候选字段、原始亮度证据或旧快照。后续以130 CT和本版材料模型为基准，只扩展未覆盖范围。
