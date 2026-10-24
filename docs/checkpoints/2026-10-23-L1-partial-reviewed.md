# L1左侧裁决与大字版（2026-10-23）

用户本轮确认F01–F03三组V2接入L1，并裁决下方两根细M3。最初编号“6”经用户明确更正为5，最终中间细M3接P0/P1/P4-UP/P5，最下方细M3接P2/P3/P4-LOW。最初原文及澄清均保存在[人审记录](../../benchmarks/l1-partial-reviewed-v3/human-review-v1.json)；不解释为P0/P5各自短接两条线。新增10条来源层局部关系：3处F接口＋7处P观察子端。孔数／精确几何未批准。

[已审局部关系](../../benchmarks/l1-partial-reviewed-v3/reviewed-relations-v1.json)、[评价](../../benchmarks/l1-partial-reviewed-v3/evaluation-result-v1.json)、[大字复核页](../assets/l1-partial-reviewed-v3/index.html)、[渲染请求](../../benchmarks/l1-partial-reviewed-v3/request-v1.json)、[核验](../../benchmarks/l1-partial-reviewed-v3/verification-v1.json)。F04–F12依旧待审；D1沿用。原清单13处主接入现4处已审、9处待审。下方细M3承载在本处区分，但不由此断言全局不同网；不导自动网表或改共同注册表。

## 字号修订

用户反馈旧编号小；source_panels新增可选source_label_style，使用Pillow字体大小、深色框、引线；默认路径不变。新图采用30px字体／6px内边距，宽图最低显示1400px，窄屏可横向滚动。P组与Z2–Z4均重新生成大字定位图，原图无改动。未来按最终显示比例选择字号与分区，不把30当通用工艺数字。复核可读性已写入金属／Via架构约定。

## 验证

- `.venv/bin/pytest -q tests/test_metal_via_pilot.py`：38 passed，58.10s。
- `.venv/bin/ruff check silicon_eye/metal_via_pilot.py`：通过。
- 16份宽／4倍原图裁片逐像素一致；10张无新样式的旧图回放逐字节一致。
- 38次路径／SHA引用核对，37项页面链接、动态图片与1段JS语法通过；已查看P组两层和Z3 M2宽图。
- 共同快照／33条注册表、事前F观察及D1已审文件与HEAD一致；无新精确变换，自动net_edges为空。未测浏览器交互。

## 接续

下一步只裁决大字页Z2–Z4的F04–F12归属L1，不重审本轮已审组。收到后回查获准M2分支。此次改动未提交／推送远端。

[前入口归档](../history/current-task-before-2026-10-23-L1-partial-review.md)：来源CURRENT_TASK.md，2026-10-23，头后原文17625 bytes，SHA256 `120548dbb18b25b52ff1bf367e2bfa233e4306aeeaed403bdff0e54678aae22c`，已逐字节核验。更早P补证入口归档链保持。
