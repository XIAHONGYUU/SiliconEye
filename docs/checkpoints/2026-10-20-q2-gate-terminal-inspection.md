# Q2栅端与引出专项检查

2026-10-20。按用户要求，保留已审源漏和环，只专项检查栅端及引出。

[统一复核页](../assets/q2-gate-terminal-inspection-v1/index.html)按A上左8条、B上右8条、C下部14条分组，图中QG01–QG30为本页索引，逐条映射原POLY稳定ID，不新增器件编号。每组可切换POLY端部范围、紧凑亮峰、纯原图、M1原图及候选引出区、局部配准候选和叠图。

本轮实际检查30条POLY的60个上下端、60个侧向范围。紫线和端部框是源图派生定位，非精确材料边界；光学峰有完整台账，不能当作孔数或CT身份。

## 观察结论

- A/B/C下端短亮条有较集中的紧凑光学响应，值得作为栅CT候选区优先人审；上端部分响应靠近既有源漏孔列或来自网格，不能仅凭亮度归为栅CT。
- 拍屏背景网格也会产生大量局部极大值。完整宽松观察保留，仅在可选显示中绘制既有legacy紧凑形态支持的峰；筛选仍不证明孔身份，横向融合的真实孔列也可能被它排除。
- M1原图内标出A-L1/A-L2、B-L1、C-L1/C-L2五个走线/引出候选范围。C上下均存在M1走线候选，不能预设所有栅都由下端接出或同属一个栅网。区域框不是已确认M1段/栅连接。
- 三组局部配准采用各自外围环的四角候选拟合，并以未参与拟合的源漏列做横向检查。中位/最大误差A为3/8px、B为2.5/9px、C为5.5/12px；预设最大6px门均未通过，纵向亦未独立验收。因此只提供候选对照，不精确投影接触点、不用此叠图确定CT或导通。

## 当前边界与人审节点

原1825个CT及全部AA/POLY输入哈希保持不变，无新增CT、无几何修订或网表变化。30条栅主体仍保留，栅CT及引出归属未知。本轮没有把未完成的归属判断写成“没有栅CT”。

只需先裁决[三组问题](../../benchmarks/q2-gate-terminal-inspection-v1/review-questions-v1.json)：A、B的下端短亮条是否包含栅CT；C实际引出在上端、下端还是分组不同。可按图中QG编号指出例外；看不清继续未知。位置/身份确认后，才按正向结构约束细化端部及候选CT，不重复验收源漏和环。

[参数与来源](../../benchmarks/q2-gate-terminal-inspection-v1/spec-v1.json)、[逐栅观察](../../benchmarks/q2-gate-terminal-inspection-v1/observations-v1.json)、[独立对应检查](../../benchmarks/q2-gate-terminal-inspection-v1/report-v1.json)、[AI观察汇总](../../benchmarks/q2-gate-terminal-inspection-v1/assessment-v1.json)、[验证](../../benchmarks/q2-gate-terminal-inspection-v1/verification-v1.json)。源与父快照哈希、30唯一稳定ID/120搜索区、静态资源、PNG、模拟切换与相关Ruff通过；14项相关保留/证据测试通过。真实浏览器渲染未自动实测。

复现：`.venv/bin/python scripts/build_gate_terminal_review.py --spec benchmarks/q2-gate-terminal-inspection-v1/spec-v1.json --output runs/新的栅端专项复核目录`。该工具只产出照片复核台账，不改材料或接触模型。

## 人审方向收口

用户确认“A,B下方短亮条包含栅CT；实际全部在下端引出”。[原话](../../benchmarks/q2-gate-terminal-inspection-v1/human-review-v1.json)及[30条逐栅状态](../../benchmarks/q2-gate-terminal-inspection-v1/terminal-status-v1.json)已记录。A/B栅CT区域身份与A/B/C下端引出方向已解决；逐栅孔数、精确边界、共栅与M1段归属尚未确认。原问题与观察台账保留为历史，不改写光学峰为已确认孔。原1825 CT及材料快照不变，本次新增CT为0；下一步只沿下端细化候选。
