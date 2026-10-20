# 上方同环小MOS：三类CT整批审批稿

2026-10-20。用户要求先把本批源漏、栅极与环CT全部处理，再提交审批。选定上方UPPER-INNER-B同一外围环内全部40条栅：左侧G55/U06的10个更小MOS，右侧Q1的30条长栅。此范围不是全照片上半部所有MOS，亦不是原CT01小样片。

[整批复核页](../assets/ct-upper-small-mos-v1/index.html)提供O整组、T左侧10个、L/M/R右侧30条分段、RT/RB完整上下环；T与R含左右环及角部。各卡切换AA/POLY/CT联合图、源图标记、纯原图、M1原图区域对照。M1独立坐标的裁剪范围均有原始bbox和源照片哈希，不作精确孔位投影。

| 类型 | 候选数 | 覆盖 |
| --- | ---: | --- |
| 源漏CT | 280 | 左侧10器件各4孔；右侧40扩散列各6孔 |
| 栅端CT | 80 | 40条栅各两处实际强峰；左10上端、右30下端候选 |
| 环CT | 413 | 上186、下211、左6、右10 |
| 本批新增 | 773 | 三类均已处理，未获人工批准 |

原1885条完整记录及AA/POLY保持不变，候选快照共2658孔。另51个环检查槽位仍未知：上34、下9、左6、右2，独立橙框，不计孔。它们可能是弱信号、相位或定位问题，不能解释成实际无孔，也不自动继承上批橙框批准。

## 方法和质量边界

- 源漏列从照片显式匹配到对应AA/POLY扩散窗口，真实搜索峰的亮度/残差和栅体对比均保留。左侧源峰较弱采用175灰度/16残差门；右侧180/16。类型阈值是本照片工作参数，不是工艺尺寸规则。
- 对右侧长栅使用实际共同六行结构，不将下端反射边缘额外计成第七行。设计行共同起点915、节距14；左侧两行共同925/936。源图坐标和设计坐标分开，显式共同相位不改写原图测量。既有材料最后一个小MOS的位置保留，未为成图调整AA/POLY。
- 栅端基于相邻源漏列定位，再沿端部亮条提取真实峰。左10上端、右30下端是本批独立AI候选，未套用Q2“全部下端”的人审结论。左侧强峰门210、右侧225，残差18，全部40条均得到两处支持，不按阵列期待补孔。设计孔为5px方孔、同栅间距10，端部包围与AA避让通过。
- 环顶为连续反射带，宽松峰含拍屏网格。顶部固定相位以同环源图节距14.5作为结构先验，从实际观测中一槽一峰选择；它不同于可靠逐孔真值，未选点保留。其余边局部间距追踪。四边设计节距13，缺观察/相位不确定仍以橙框表示。
- M1仅交叉检查区域和引出结构，没有确立具体M1段、共栅或电气网络。精确尺度/真实工艺DRC未知。

[完整参数](../../benchmarks/ct-upper-small-mos-v1/spec-v1.json)、[源漏/环拟合及排除项](../../benchmarks/ct-upper-small-mos-v1/fits-v1.json)、[栅端测量](../../benchmarks/ct-upper-small-mos-v1/gate-measurements-v1.json)、[门端测量参数](../../benchmarks/ct-upper-small-mos-v1/measurement-spec-v1.json)、[别名到稳定栅ID](../../benchmarks/ct-upper-small-mos-v1/gate-aliases-v1.json)、[候选CT](../../benchmarks/ct-upper-small-mos-v1/model-v1.json)、[覆盖和未知](../../benchmarks/ct-upper-small-mos-v1/coverage-v1.json)。

## 审批及验证

只需按[清单](../../benchmarks/ct-upper-small-mos-v1/review-questions-v1.json)一次核对T、L/M/R及外围环：源漏与栅孔材料归属/位置、左上右下的栅端方向、橙框是否可确认。旧1885记录不重验。三类候选均完成处理，但51未知槽位尚不等于提取齐全，需如实裁决。

2658孔整体门PASS，无重叠、孔距、包围、沟道/AA避让违规。所有源漏搜索点支持与门体对比通过。435项全套测试和相关Ruff通过，新增上端测量方向测试、共同设计相位不改写照片证据的测试；输入/旧验收哈希、静态资源/SVG/PNG及模拟切换通过。真实浏览器渲染未自动实测。[验证记录](../../benchmarks/ct-upper-small-mos-v1/verification-v1.json)。

复现：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-upper-small-mos-v1/spec-v1.json --output runs/新的上方小MOS_CT目录`。

栅端测量：`.venv/bin/python scripts/build_gate_terminal_review.py --spec benchmarks/ct-upper-small-mos-v1/measurement-spec-v1.json --output runs/新的上方栅端测量目录`。重建读取锁定观测，不重跑已审提取。
