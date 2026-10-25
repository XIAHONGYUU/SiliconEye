<!-- Source: CURRENT_TASK.md; archived 2026-10-25; original bytes=8418; sha256=00bdc9d9d0563b37a39fac580140e223439852292ea48a37e33aaac0b07250db -->
# 当前任务

## 当前目标与授权

用户授权按V1整组→连续五层→独立区域迁移→skill收口依次推进。现已交付P08连续路径和窗口外宽B样本的整组几何候选，两个仓库内skill更新为限定试用v2；新增几何待Q1/Q2验收。不扩材料层、全图或整网，不重复审既有连接，不新增人工数量批准。此前GitHub存档86bd6a2之后的修改仍未提交/推送。

[最新复核入口](docs/assets/five-layer-geometry-v1/index.html) · [连续五层中样](docs/assets/five-layer-geometry-v1/review/index.html) · [独立迁移](docs/assets/five-layer-geometry-v1/independent/index.html) · [交付报告](docs/reviews/2026-10-24-five-layer-geometry.md) · [验证](benchmarks/five-layer-geometry-v1/verification-v1.json)。此前[J组12孔交付](docs/reviews/2026-10-24-medium-v2-array.md)和[质量根因复查](docs/reviews/2026-10-24-conductive-quality-review.md)按需回查。

## 当前结果与质量资格

| 项目 | 结果与边界 |
| --- | --- |
| 中样来源形状 | 前轮R-M2-3已修为左返（570→526）；本轮仅P08增局部承载矩形，所有金属骨架/宽度和原生路径保持；旧反向负例仍拒绝 |
| 六孔防退化 | 从实际继承人审记录核数量，候选同时删除阵列/数量字段也不能退回单框 |
| 已知12孔事实 | J-M2-EDGE-V2的3×4=12已按精确成员ID迁移为完整设计阵列；M2包围最小1.5/M3为18，满足预算1，未改变金属；具体来源尺寸仍待验收 |
| 分项质量 | 程序检查、声明来源转折、局部承载、孔组几何、来源尺寸/边界、端部/覆盖分别报告。可交复核包，完整共同几何/整网/正式通用skill不放行 |
| 当前范围 | 中样22条金属、9个代理组+V1/V2两组显式阵列，仍表示已审清单38条中的11条；不是照片覆盖率。独立样本6条金属+两组显式阵列；几何均未验收 |
| 新增候选 | P08 V1：AI观察3×3，局部M1包围4.5/M2包围1.5；独立宽B的V2：AI观察3×2，M2包围11.5/M3包围33。仅已有连接继承，不新增人工孔数事实 |

已知相对规则几何不要求与畸变照片逐像素贴合；仍要有相对宽度、开口、隔离和邻层承载依据。通过调整金属包住孔组只是AI几何提案，不能倒用作照片边界证明。真实微米尺度/PDK未知不妨碍相对规则重建，但当前不声明真实工艺DRC通过。

## 必须继承的人工事实

- **A={T3,L2}，B={T1,L4}，分别经M2/M3接A、B。** [当前分组](benchmarks/mid-ab-structural-hypothesis-v11/grouping-state-v3.json)及[最新更正](benchmarks/mid-ab-structural-hypothesis-v11/grouping-human-correction-v3.json)优先；旧L3不复活为A成员、不推导全局断开。具体返回M2、M3-X/Y及逐孔路径仍未知。本次R-M2-3几何方向修正不新增连接。
- MID-H1/H2为M1，本处与U1/U2的M1隔离，不推导全局异网；H1→V1→M2-A、H2→V1→M2-B已审。U1/U2同一M1，U1/U3有V1、U2无V1；两处均接N2。精确中间走向未恢复，不虚构跨H1/H2的竖线。
- N2上接M3-B1，下经D1接M3-L1；J01/F04、F01–F12等已审承载保持。13主分支不等于下层覆盖完成。U3宽M1→所圈CT行→对应AA环已审，仅该端子路径terminal_closed=true；体端/极性、孔数、边界和规范材料ID映射仍未知。[U3已审状态](benchmarks/n2-u3-terminal-reviewed-v2/reviewed-state-v2.json)。其他分支/P0/P5等按归档原范围保留，不因未画撤销。
- 本批孔来源策略M1照片侧V1、M2照片侧V2；J组M2孔组已确认为3×4 V2，不重审。旧九对V1/V2同孔拟合与约4.52px残差已撤回，不能当配准依据或借M3亮点证明V2。
- U1设计右端早已从1700修至1310，保留原生1945<P08左竖2006的次序；此次不复活旧越界。来源次序/转折门不等于跨层配准或原生路径识别全正确。
- 独立样本Q1六孔经V1接**宽IT1-M2-B**，原窄A候选错误；历史ID IT1-V1-A的后缀不表示当前承载。Q2仍为M2-B经V2接M3-BUS，两项不重审。[实际Q1更正](benchmarks/metal-independent-q1-correction-v2/q1-human-carrier-correction-scoped-v3.json)。六孔数量已知；2列×3行及孔径/间距/位置、B边界仍是候选。A/B是否同层连续未知；独立样本A/B不同于MID分组。

## 共同层与保留范围

唯一共同快照仍为[configs/joint-work-layer-v5.json](configs/joint-work-layer-v5.json)：AA334/POLY696/CT10287、八张5712×4284照片和哈希不变；导体注册表仍引用[原33记录模型](docs/assets/conductive-stack-v2/model.json)。本轮新中样仍为局部候选，不替换原共同注册表；原图、材料和旧审批不改。

S1/S2/S3身份、G66-P03/P04上端桥与蓝色栅CT、退休ROW4-AA4-SD00、四栅与33孔、R1A/R1B上端、R2连续AA单排孔、R2_Q1、V3端子/v33网络、S03-03/04、18电阻、W01及195保留对象均按原范围继承。

六处材料未知：AA-F01951、AA-F01952、材料H1/H2（不同于MID-H1/H2）、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS；最后一处不借栅CT推源漏有/无孔。V3主体截段历史例外生效。未知只限制依赖，不触发整层重做。

net_edges空、automatic_network_export_allowed=false、complete_network=false、共同几何采用关闭。真实尺度、工艺、极性、W/L、阻值及完整网表未知。

## 使用与验证

[金属试用skill](skills/silicon-eye-metal-reconstruction/SKILL.md)、[层间孔试用skill](skills/silicon-eye-via-reconstruction/SKILL.md)限定试用v2已同步完整孔组、AI观察证据绑定和局部承载修订；未安装全局、未正式通用放行。[统一契约](docs/architecture/conductive-workflow-contract-v1.md)与[追网约定](docs/metal-tracing-workflow-v1.md)继续适用。POLY/CT原skill范围不变。

```bash
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/five-layer-geometry-v1/review-request-v1.json --output runs/新的质量复查目录
```

独立样本用benchmarks/five-layer-geometry-v1/independent-request-v1.json。旧trial/main含已发现的反向折线，仅作历史/负例，不再作当前恢复入口。输入是AI观察，命令不自动识别照片或追网；新事务只能修改声明对象，原生锚点/快照/预算/人审范围不能静默改变。未审接口改承载必须实际人工更正绑定旧送审包；退休/合并ID或更换已审接口仍需另作事务。

本轮相关七个测试文件分两批94+47共141项通过，另对最终来源复用版重跑9项不重复计数；Ruff、两skill格式、CLI交付重放、来源裁片像素、165项输入/8项交付哈希及71条本地链接通过，见verification。未做浏览器交互、新芯片盲测或真实工艺DRC。24个来源视图复用17个，新增7个必要视图。

## 唯一下一步、Git与归档

唯一下一步为最新复核页的两项新增几何验收：Q1核P08局部承载与V1整组范围，Q2核独立宽B内V2整组位置/占用。不重审连接、不默认批准AI孔数；若有偏差只修对应对象，通过后按结构类型分批迁移剩余代表组，不重做已审区域。

Git基线HEAD=86bd6a27c0ee2b57148ef18d83331e18567ec664，已推送并核对远端。此后新增整组迁移代码、source views、样本/验证/报告、skill例子和当前入口为本机未提交改动，未再次推送。原始照片、材料与旧批准保持。

[本次整理前入口完整归档](docs/history/current-task-before-2026-10-24-conductive-quality-review.md)保留Q1更正、四项交付和更早归档链，已核原字节与SHA。CURRENT_TASK仍为唯一实时操作入口，历史按需调取。

[本次GitHub存档前入口](docs/history/current-task-before-2026-10-24-github-quality-snapshot.md)保存原文、字节数与SHA；[提交范围检查点](docs/checkpoints/2026-10-24-github-quality-snapshot.md)记录范围与验证。

[整组迁移前入口完整归档](docs/history/current-task-before-2026-10-24-medium-v2-array.md)保存本次先推送授权及质量复查状态，原字节与SHA核对一致。[本轮检查点](docs/checkpoints/2026-10-24-medium-v2-array.md)记录先后顺序和未提交范围。

[本轮推进前入口完整归档](docs/history/current-task-before-2026-10-24-five-layer-geometry.md)保留原文、字节数和SHA，已核对原文完整；所有仍生效的裁决与未知继续保留。
