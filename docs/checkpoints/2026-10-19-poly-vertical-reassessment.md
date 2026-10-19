# 2026-10-19：重新判断竖向POLY主体与端部

[打开本轮复核页](../assets/poly-vertical-reassessment-v3/index.html)。旧黄色为上一轮B1，新蓝色为当前Agent从宽上下文重新观察的主体候选，橙色为上下端过渡待核范围。两个MOS器件既有编号保持，不因重绘生成新器件。

## 判断与来源

结合原图连续条带、相邻重复结构以及已审器件身份，本轮仍判断为相邻竖向MOS栅指，不是CT亮点列或电阻。AA照片中的竖向沟道纹理只用于定性支持方向和阵列关系；没有精细AA/POLY配准，不作逐像素投影。

两条栅体重新观察了上下范围和左右边缘，而非按倍数扩张旧core。候选原生四角由AI观察声明，脚本只绘图和正交化，没有重新运行GrabCut或宣称算法自动识别。旧B1包含在新主体候选中，但包含关系仅证明接续，不证明新边界正确。

- Q1来源四角：(1739,2707)、(1774,2706)、(1781,2839)、(1746,2840)。
- Q2来源四角：(1795,2706)、(1830,2705)、(1837,2837)、(1802,2838)。
- 与旧B1相比，新候选显式恢复了更多上下延伸，并重新观察了两侧范围；真实尺寸尚待用户评估，不报告物理W/L。
- 主体范围之外的端部过渡/接触引出仍为未知；橙色框不是新增POLY，也不是非POLY标签。蓝色端边不是已确定的物理终止，不声称完整引出已恢复。

## 一次核查清单

1. 按两条竖向MOS栅指的主体与端部过渡表达是否合理？不重问已审POLY材料身份。
2. 蓝色新轮廓的左右范围、上下长度是否接近实际？如仍有误请指出方向。
3. 橙色端部待核范围是否合理，是否有明显遗漏的扩宽/引出？本轮不判断CT归属和新增连接。

## 复现与技术核查

[参数/AI观察](../../benchmarks/poly-vertical-reassessment-v3/spec-v1.json)、[报告](../../benchmarks/poly-vertical-reassessment-v3/report-v1.json)、[绘图工具](../../benchmarks/poly-vertical-reassessment-v3/render_review.py)、[核查](../../benchmarks/poly-vertical-reassessment-v3/verification-v1.json)。

在仓库执行：

```bash
PYTHONPATH=. .venv/bin/python benchmarks/poly-vertical-reassessment-v3/render_review.py --spec benchmarks/poly-vertical-reassessment-v3/spec-v1.json --output runs/新的目录
```

原图及15项冻结输入哈希不变；原生/规则几何无交叠、规则几何HV、旧B1包含、局部矩阵重投影自洽检查通过；Ruff、页面JS语法、切换资源和相对链接检查通过。浏览器交互未自动实测。本轮仅生成复核资产，无生产提取代码变更；不添加镜像测试，软件门不证明材料/尺寸验收。完整资产保存在docs/assets，可独立查看，不依赖被忽略的runs目录。

旧横向P-H01批准保留，AA模型与旧POLY修正未改。没有新增CT、网络或器件结论；全幅POLY与skill封装等待局部方法通过。开发输出v3a/b为绘图格式调整，不计独立实验。

## 人工验收完成

用户确认：主体与端部基本合理；蓝色范围基本接近实际，可以通过，无明显方向偏差；无遗漏扩宽或引出。[原话记录](../../benchmarks/poly-vertical-reassessment-v3/human-review-v1.json)、[采用状态](../../benchmarks/poly-vertical-reassessment-v3/acceptance-v1.json)、[四个对象的局部工作模型](../../benchmarks/poly-vertical-reassessment-v3/accepted-local-model-v1.json)、[已审页](../assets/poly-vertical-reassessment-v3/reviewed.html)。

采用v3两条竖向主体原坐标，不改绘图，不增加端部扩展；本轮端部遗漏疑点关闭。旧v1偏小结果保留失败证据，v3改善来自AI重新观察，不归功于同一算法自动扩展。两处局部案例门已通过，可以推进全幅候选；不证明全幅材料完整性或POLY skill已通过。
