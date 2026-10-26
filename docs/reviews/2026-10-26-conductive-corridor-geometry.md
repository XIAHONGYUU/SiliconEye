# 连续走廊22个金属片段补建

已为上轮清单中的22个未建模片段建立规则几何：M2新增5段，M3新增17段；当前共8条M2、22条M3，声明清单30/30都有几何对应。新几何均为正交候选，未自动批准，也没有从交叉重叠新增孔或连接。

[打开补建前后／独立原图复核页](../assets/conductive-corridor-geometry-v1/index.html) · [最终统一包](../assets/conductive-corridor-geometry-v1/revised/index.html) · [覆盖变化](../../benchmarks/conductive-corridor-geometry-v1/coverage-change.json) · [验证](../../benchmarks/conductive-corridor-geometry-v1/verification.json)。

## 补建和保持范围

| 层次 | 新增 | 保持旧对象 |
|---|---|---|
| M2 | C-M2-03/04上沿折角，05左短折角，06边界亮块，08左下竖线 | R01、R02两长线与NARROW窄折线 |
| M3 | T01–T06上部六线，M01–M06中部六线，E1/E2左边界短线，L01/L03下部细线及EDGE最下沿线 | UP/MID/DOWN宽母线及THIN1/THIN2 |

旧8个金属、四个V2组及其32个设计孔完整保持，孔中心、来源锚点、已审接口和人审引用不变。V2孔数/尺寸仍未取得本组人工几何批准。C-U1～C-U5继续未知，不把弱明暗带补成M3，不判断N1端部为V2，也不合并05/06。

原图来源路径保留倾斜；规则设计在独立780×1240画布上横平竖直。新增上／中部两组六线分别用19/21设计像素节距，细线宽8；这些是AI依据照片布局作出的规则候选，不是物理测量或PDK DRC。原图与设计图分开显示，未作照片投影。

## 复用入口与自主修订

原修订事务不允许增删ID。本轮在同一`conductive_workflow`加入显式金属扩展：声明新增名单、绑定来源清单和父包，旧feature/interface逐字段保留；只能加金属，不能夹带新增孔、承载变化或旧几何修改。旧接续/局部修订行为保留，未新增案例专用执行脚本。

首次补建保留在`work/`及[request.json](../../benchmarks/conductive-corridor-geometry-v1/request.json)。AI对照来源后发现新E1/E2长度偏短，使用既有局部修订事务，只改这两条新边界短线的设计长度，原生路径不变：[修订依据](../../benchmarks/conductive-corridor-geometry-v1/length-revision-evidence.json)。以同帧730像素可见横向跨度对应610设计像素作为相对长度候选，105→88、58→48；不是跨帧变换，也不是人工批准。

最终包为`revised/`，其余28个金属及四个孔组与首次补建相同；与最初已审基线相比，旧对象仍完全不变。初稿及修订保留，不把自主修订隐藏为一次生成即正确。

```bash
# 复现完整过程；每个输出使用新目录
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/conductive-corridor-geometry-v1/request.json --output runs/新的补建
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/conductive-corridor-geometry-v1/request-v2.json --output runs/新的局部修订
# 接续最终结果，不重复声明新增或修订
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/conductive-corridor-geometry-v1/next-request.json --output runs/新的接续
```

修订请求绑定已保存的首次包，不会自动改为上述新目录；若将新目录作为事务父包，需重新绑定相应manifest。下一次接续已经实际运行，完整模型与最终包一致。

## 验证和未完成项

- 正交、宽度/间距、来源折线转向、22条附加同帧次序及完整设计孔组包围检查通过；没有降低预算，M2/M3最小间距分别约为17.03/10设计像素。
- 64项专项测试通过（含10项补建事务、45项原workflow、9项台账）；另31项固定回归与1项最终来源长度修订检查通过，共96项不同测试。它们不是96次AI识别或独立芯片评测。
- 拒绝未声明新增、改旧宽度、移动新增原生路径、漏映射、同层重叠、行序颠倒、提案未绑定以及无父包扩展；验证新增后可原样接续。
- 37个页面/资产本地链接、SVG XML、JS语法、JSON数据、manifest和下一次实际接续通过。只复用原图裁片，无新增照片副本；实际浏览器交互未自动验证。

30/30只表示**上轮声明片段已建模**。旧8个对象的来源端部仍是部分覆盖；五项疑点、原图物理穷尽性、M1/V1对应及全五层覆盖没有通过，因此不能声称完整GDS或全网完成。新22段尚待定性几何复核；四条旧连接不重审。

README/site的25个文件与本地gh-pages引用不变。skill维持限定试用v2，未提交或推送。上一实时入口完整归档至[历史文件](../history/current-task-before-2026-10-26-corridor-geometry.md)。下一节点是对新增22段作一轮批量几何复核，重点看数量、相对次序、短线比例及隔离。
