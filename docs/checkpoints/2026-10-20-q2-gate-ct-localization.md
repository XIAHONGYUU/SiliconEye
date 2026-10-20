# Q2 POLY下端CT位置候选

2026-10-20。用户确认A/B下方短亮条包含栅CT、本组全部下端引出，并要求依据这些信息及M1继续判断孔位置。

[位置复核页](../assets/q2-gate-ct-localization-v1/index.html)显示30条栅的60个POLY CT候选：A8栅16孔、B8栅16孔、C14栅28孔。当前1885孔快照，原1825条完整记录及全部AA/POLY保持不变。紫色为新增POLY接触，灰蓝为保留孔；本轮只请求复核新增位置/每栅两孔，不重验源漏与环。

## 定位依据

1. 旧POLY原图四边形是派生定位，部分端部与实际照片存在偏差。因此用每条栅两侧已经匹配的源漏CT列作为局部锚点，在二者之间寻找下端亮条；下方环限制搜索范围，避免把环孔错归栅极。
2. 先沿纵向亮度剖面定位下端亮条，再沿横向剖面寻找实际峰，不直接把拍屏网格或所有局部极大值当成孔。保留原始测量和旧端点y定位用于比较。
3. 本照片候选采用平滑亮度≥225、背景残差≥18的强峰门；阈值是本照片的相对工作参数，不是工艺DRC。30条下端均保留两处强峰；QG24、QG30各有一处较弱峰，完整留在台账，未当第三孔输出。孔数是AI候选，未冒充用户已逐孔批准。算法允许实际零/一/两峰，不因阵列规则补成两孔。
4. 设计坐标中，CT放在各自POLY的下端、AA之外；5px方孔、12px设计节距、统一端部相对相位。AA、POLY主体与端部都无需修改即通过原有包围和避让预算。
5. M1用于交叉核对器件区域和下端引出方向；旧局部投影精度门仍未通过，不把M1像素盲投影成孔，不据此确认M1段归属、共栅或网络。页面的M1模式是独立坐标原图候选区域，不能当作同坐标切换。

[测量参数](../../benchmarks/q2-gate-ct-localization-v1/measurement-spec-v1.json)、[逐栅原图测量](../../benchmarks/q2-gate-ct-localization-v1/measurements-v1.json)、[重建参数](../../benchmarks/q2-gate-ct-localization-v1/spec-v1.json)、[来源观察](../../benchmarks/q2-gate-ct-localization-v1/source-observations-v1.json)、[CT候选](../../benchmarks/q2-gate-ct-localization-v1/model-v1.json)、[覆盖](../../benchmarks/q2-gate-ct-localization-v1/coverage-v1.json)、[质量门](../../benchmarks/q2-gate-ct-localization-v1/report-v1.json)、[待判清单](../../benchmarks/q2-gate-ct-localization-v1/review-questions-v1.json)。

## 验证与复现

1885孔整组无重叠、孔距/包围/避让违规。60个新孔均明确归属自己的POLY，M1包围与net_id仍未知。433项全套测试及相关Ruff通过；新增合成测试验证旧端部定位偏差可以由实际源峰修正、零/一/两峰不强补、弱第三峰不晋级。静态资源/SVG/PNG及模拟切换通过，真实浏览器渲染未自动实测。[验证记录](../../benchmarks/q2-gate-ct-localization-v1/verification-v1.json)。

测量：`.venv/bin/python scripts/build_gate_terminal_review.py --spec benchmarks/q2-gate-ct-localization-v1/measurement-spec-v1.json --output runs/新的栅端测量目录`。

重建：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/q2-gate-ct-localization-v1/spec-v1.json --output runs/新的栅CT候选目录`。第二步使用锁定测量，不重新提取已审区域；改变测量须更新测量/观察引用和哈希后再重建，不能静默换源。

## 位置与孔数验收完成

用户明确回复“孔位置及每栅两孔合理”。[原话](../../benchmarks/q2-gate-ct-localization-v1/human-review-v1.json)与[锁定范围](../../benchmarks/q2-gate-ct-localization-v1/acceptance-v1.json)确认本次A/B/C的60个POLY CT。原算法观察及候选字段保持历史原样，几何不修改。当前1885孔为接续快照；M1具体段归属、共栅与物理尺寸不在批准范围，旧661几何细节保留意见未升级。下一批进入上方小MOS，不重复验收本组。
