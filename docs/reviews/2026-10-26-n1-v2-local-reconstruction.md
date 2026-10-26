# N1接A：来源裁决接续与局部包围检查

用户原文“N1接A”已绑定实际送审问题与两张内嵌PNG，记为N1-V2将RT-M2-NARROW接到C-M3-L01。此前V2身份批准继续有效；不再询问这两项，也不把连接批准扩大成孔数或新设计坐标批准。

## 结果与变化范围

- 规则设计中，仅将M2短横头的两个顶点y675改为682，x565/590、宽度10和竖干下端保持。其他29条金属、全部原生锚点、旧4条接口和32个设计孔逐字段保持。M3-A没有移动或加宽。
- 原照片短横头呈横向分布的两个主要亮斑，提出1×2 AI站点候选；保留完整横向占用，不将孔组挤到竖干。候选孔径6、横向节距18，设计中心(568,682)、(586,682)，整组包络[565,679,589,685]。数量、尺寸及精确源到设计映射仍未知。
- 每孔方形、最小间距、逐孔两侧包围通过；对整个声明阵列包络扩大每侧1像素后，[564,678,590,686]仍全部位于M2短横头和M3-A内部。仅声明设计阵列的完整包围PASS，不声称已确认物理孔组穷尽。
- 来源连接已进入模型：5个已审接口、34个设计候选孔，其中旧32个原样保持、新2个仍为AI候选；没有新增net_edges、共同GDS采用或全网导出。

## 接续方式与软件改动

复用统一workflow：先作仅N1的局部金属修订，再作独立的显式接口补建事务。新增`added_interface_ids/interface_extension_evidence`只允许新增列明孔组，绑定父包和每组AI站点记录，旧记录必须完全保持。没有为N1另建绕过质量门的脚本路径。

原生承载问答通过`native_carrier_confirmation`适配，绑定实际问题、内嵌图像、先前V2身份、同一来源快照和工作基线；拒绝夹带数量或几何批准、改变载体身份、越过来源范围。原问题只有首选A获得本次直接批准，其他载体更正仍需显式更正证据。

恢复：

```bash
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/n1-v2-local-reconstruction-v1/next-request.json --output runs/新的N1接续目录
```

新增声明在next-request中移除，已审连接及未知自动继承。工作几何仍是候选，六组已审基线原包保留；本轮没有倒改原审批。

## 验证

77项相关测试、9项清单测试、31项固定回归，共117项不同软件测试通过；它们是工程回归，不是117次AI识图评测。新增负例覆盖未声明接口、夹带旧记录修改、错误载体、伪造数量批准、几何越权、缺失父包/阵列证据、退回未对齐短头及来源视野遗漏。精确接续模型相等，失败只产生diagnostic.json。

Ruff及git diff --check通过。4张原生裁片逐像素对照原照片；SVG/HTML资源与脚本静态检查，新旧规则图和原生并列图已目视检查，未声称浏览器交互已实测。README/site的25文件、gh-pages引用不变。未提交或推送。

## 当前边界与下一步

N1身份与承载已收口，没有新增连接问题需要重问。设计候选的包围已检查，真实孔数、照片精确配准、物理尺寸和PDK DRC继续未知；局部新几何尚无人审批准，不自动升级共同GDS。

下一步回到同一走廊的三条弱带C-U1/C-U2/C-U3，分别检查是否存在真实M3导体；不能因规则图可补线就补出连接。M1/V1及更高层范围不扩展，05/06局部不直连、全局同网未知保持。

- [新旧局部图](../assets/n1-v2-local-reconstruction-v1/before-after-local.png)
- [原生对照](../assets/n1-v2-local-reconstruction-v1/source-detail-pair.png)
- [图层切换页](../assets/n1-v2-local-reconstruction-v1/index.html)
- [人审记录](../../benchmarks/n1-v2-local-reconstruction-v1/human-review.json)
- [整组包围数值](../../benchmarks/n1-v2-local-reconstruction-v1/N1-group-enclosure.json)
- [当前来源状态](../../benchmarks/n1-v2-local-reconstruction-v1/source-fact-state.json)
- [验证](../../benchmarks/n1-v2-local-reconstruction-v1/verification.json)
