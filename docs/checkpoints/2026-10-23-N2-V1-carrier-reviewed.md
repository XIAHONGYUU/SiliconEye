# U1/U3经V1接N2批准与M1横向分支（2026-10-23）

用户“均接到N2”批准两处已审V1的粗承载。[人审原文](../../benchmarks/n2-v1-carrier-reviewed-v8/human-review-v1.json)绑定上轮两个候选、图页、身份事实。新增M1-N2-U1-U2→V1-N2-U1→M2-N2-LEFT-RAIL，以及M1-N2-U3→V1-N2-U3→同一N2。[接续关系](../../benchmarks/n2-v1-carrier-reviewed-v8/reviewed-relations-v1.json)33条局部接口，原31条保持；[本轮路径](../../benchmarks/n2-v1-carrier-reviewed-v8/reviewed-path-summary-v1.json)通过已审N2进入B1/L1组件。这个接口数不是共同33条几何对象或物理孔数。U1/U3同网不意味着合并物理M1图形。

U2无V1、U1/U2同M1继续接续，不补孔、不断线，不重审。新[评价](../../benchmarks/n2-v1-carrier-reviewed-v8/evaluation-result-v1.json)仅比较两个粗承载判断与人审；精确落点、孔包围、矩阵／边界未批准，不当独立盲测或像素准确率。

## 新一轮独立检查

检查M1照片[0,1700,5712,2950]整体横带及左／中／右上下文，从U1/U3沿横向看上／下M1延伸（当前只是原图范围候选，照片左侧出图未知）。U2附近两条细横向结构的材料／接通仍不清楚，保留 `MID-H1`、`MID-H2`，不因十字交会并网；它们不复用既有材料未知H1/H2的ID。

[当前大字页](../assets/n2-v1-carrier-reviewed-v8/index.html)、[事前分支观察](../../benchmarks/n2-v1-carrier-reviewed-v8/M1-branch-observation-v1.json)、[请求](../../benchmarks/n2-v1-carrier-reviewed-v8/request-v1.json)保存完整横向范围[0,1750,2360,2860]、4倍宽局部[1250,2140,2170,2430]。只请判断两结构是否属于M1并与U1/U2接通，还是其他层／残影／隔离；材料／接通真值全null。五处窄x剖面的平滑／亮度峰仅定位本图细线，不是材料识别或跨层拟合。

## 可读性修复与验证

原渲染器会把裁窗外的整图标注压进局部，干扰H1/H2观察。新增显式选项hide_off_window_labels，只在本页新样式开启；默认渲染保持。字号按宽图提升为40源像素，底框、引线、全宽／原尺寸入口保持。

- `.venv/bin/pytest -q tests/test_metal_via_pilot.py`：38 passed（49.57s）；本轮实际重跑。
- `.venv/bin/ruff check silicon_eye/metal_via_pilot.py`：通过。
- 10张默认历史图重新渲染逐字节不变，两份原图裁片像素一致；91处引用SHA、33接口人审来源、2新接口、U2不造孔、两M1不误合并、两MID候选不采用、10链接与1段JS语法通过。
- 已看整幅／局部标图；未测浏览器交互。[核验](../../benchmarks/n2-v1-carrier-reviewed-v8/verification-v1.json)与[交付清单](../assets/n2-v1-carrier-reviewed-v8/manifest.json)保存结果。

没有新坐标矩阵、V1/V2同孔配对或自动网表边。共同v5／33导体、材料、旧包和照片不改；其他M1/V1、X1/X2、照片外未知与整网未完成状态保持。此次未提交／推送。

[前入口完整归档](../history/current-task-before-2026-10-23-N2-V1-carrier-reviewed.md)来源CURRENT_TASK.md、2026-10-23，头后payload 17121 bytes，SHA256 `31209568834631f9bfc5288cdf0e2eb0aa0570fb7b2289ce83d8be0d90e6cdf6`，逐字节核验一致；历史链保持。
