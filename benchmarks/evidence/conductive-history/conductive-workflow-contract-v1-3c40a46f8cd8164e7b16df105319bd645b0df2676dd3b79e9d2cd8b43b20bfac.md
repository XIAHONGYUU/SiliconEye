# 金属／层间孔统一试用契约 v1

入口：`.venv/bin/python -m silicon_eye.conductive_workflow --request REQUEST --output NEW_DIR`。本契约供仓库内金属/层间孔两个试用skill共用，保留已验证的M1/M2/M3、V1/V2小范围能力。它消费AI已形成的观察与候选，不自动调用视觉模型、识别新照片、精确配准或采用共同层。阶段进度只见CURRENT_TASK。

## 输入与阶段

运行请求`kind=conductive_reconstruction_workflow`、`schema_version=1`：

| 字段 | 用途 |
| --- | --- |
| `sample` | 观察/几何样本的相对路径和SHA256；支持新标准`conductive_layer_observations`，及已有两类样本的兼容适配 |
| `frames` | 本次复核所需照片帧，不得遗漏已重建金属的来源层 |
| `reviews` | 本轮新增人工记录引用；不填AI自批结果 |
| `parent` | 接续/修订时的父包manifest引用；旧接口审批自动继承，不要求重新提交 |
| `allowed_changed_ids`、`revision_evidence` | 仅修订时声明实际变化ID和AI提案/原因/来源；未声明变化或空泛替代均拒绝 |
| `added_metal_ids`、`extension_evidence` | 显式补建：声明新增金属ID和绑定父包/来源清单的AI提案；不得增孔、改旧对象或改接口 |
| `limits` | 保留的未知及覆盖边界；接续不能静默删掉父包限制 |
| `deferred_unknown_ids` | 仍待裁决但暂缓处理的接口，只可取自当前pending；不改变物理真值 |
| `questions` | 待裁决ID对应的可读问题，只显示仍待定的问题 |
| `source_panel_spec` | 可选，绑定宽图/放大图/标记配置；只改变视图，不改变物理对应 |
| `source_assets` | 可选，复用已保存原图/标记裁片引用；原图裁片必须逐像素匹配声明照片和窗口 |

没有parent为新建/检查；parent加相同sample为接续；parent加已声明变化为修订。均用同一命令。已有样例在`benchmarks/conductive-workflow-trial-v1/`，先读JSON参数再使用；输出目录必须新建。

显式金属补建仍使用同一命令与原画布/预算。样本绑定`visible_inventory`及`inventory_geometry_mapping=[{observation_id,metal_id}]`，要求声明清单中的全部金属片段与当前对象一一对应。新增对象的原生路径必须与清单完全相同；旧对象仍保留原锚点，清单中的延伸观察只记为部分来源范围，不能倒改旧锚点。事务检查针对所有既有对象。

`extension_evidence={actor:AI,reason,parent,inventory,added_metal_ids,sources}`须与实际请求一致。新增仅能是金属，旧feature和interface逐字段不变，旧批准/孔中心/限制自动接续；不能同时以补建名义微调旧几何、换承载或退役对象。可附`additional_source_order_checks`检查新增结构的同帧次序，沿用原`source_order_checks`；已有清单/映射/附加次序不能在后续接续中静默改写。对倾斜平行来源线可比较相同端的极值次序，不把它当像素配准或几何间距。

完成补建后的下一请求以新包为parent，移除`added_metal_ids/extension_evidence`，原样sample和限制继续回放。`changed_object_ids`仅指旧对象变化，补建名单另在`added_metal_ids`报告。清单30/30已建模只表示声明片段有几何，不证明照片穷尽、旧端部完整、疑点解决或人工几何验收。示例：`benchmarks/conductive-corridor-geometry-v1/request.json`；反例测试：`tests/test_conductive_metal_extension.py`。

## AI观察样本

新样本采用`kind=conductive_layer_observations`，包含：

- `snapshot`：锁定快照引用，含原照片及各自原生尺寸、已声明孔层来源策略。当前沿用共同v5，无快照的新图先标准化输入，不能套用旧图身份/尺度。
- `canvas_wh`：局部规则设计画布，与原生照片分开。
- `features_by_layer`：按M1/M2/M3组织，每对象至少`id,layer,source_frame,native_path,design_path,design_width,label,label_xy,role,end_states`。原生折线可以倾斜，设计折线须正交；稳定ID不因同网被合并。
- `interfaces`：每个孔组支持候选至少`id,layer,layer_pair,source_frame,native_bounds,lower_metal_id,upper_metal_id,bounds,observation_id,status=candidate,connection_confirmed=null`。来源窗口是照片观察，bounds为设计支持区，不能当单孔计数或精确投影。
- `metal_budget,via_budget`：有单位和相对规则依据的配置；本批为相对设计像素，不是已知工艺尺寸。父包修订不能削弱预算。
- `source_order_checks`：可选显式同帧关系，形如`axis=x, first={id,extreme=max}, second={id,extreme=min}`，表示来源和设计中first都应在second之前。不得用不同照片帧做此检查。
- `source_panels`：每帧的wide/detail原生窗口，以及观察/原生标线/孔组标记配置。宽上下文不能被狭小单孔窗口替代。

AI负责来源判断、结构解释、替代假设与几何候选；脚本检查正交、间距、来源身份、包围、声明次序、修订范围和审批接续。脚本不从重叠推导连接，不把规则化补全当照片事实。

## 人工裁决与接续

新统一包的人工记录含`actor=human`、用户原文`statement`、`sources`以及`decisions`。只有收到用户实际裁决才能写人工记录；程序校验结构和来源绑定，不能验证一段文字是否真实来自人。

`sources`绑定输出目录中的`submitted_request=request.json`、`submitted_page=index.html`、`submitted_manifest=manifest.json`及各自SHA。decisions只声明`interface_id,via_layer,lower_metal_id,upper_metal_id,connection_confirmed`；命令通过已提交包找到原样本并核对层对、承载、原生支持窗口及金属原生锚点。旧Q2原生样本的审批格式继续适配，不改旧证据。

- true：仅确认该接口接入，几何/孔数仍候选或未知。
- null：未决，继续pending，不算断开。
- false：只否决当前候选解释，不证明没有孔或全局断开。

接续自动携带旧审批。显式冲突会停止，需单独记录更正，当前试用版不静默覆盖旧真值。未审候选不能在输入直接填true。

## 局部修订与输出

父包按manifest重新加载。只允许列明的设计几何/显示字段变化；照片快照、预算、画布和来源次序门不能变，原生锚点和接口身份不能借微调移动。新增/退休/合并ID、改来源或改承载需另作明确事务，超出试用接口时停止，不伪造别名。

成功输出`model.json,report.json,request.json,index.html,manifest.json`，需要时生成宽图与完整放大图；复用裁片时检查其哈希和原图像素。model分开保存事前候选、已审连接、待定/暂缓接口、已审U3端子、范围限制。report给出变化ID和质量门结果，几何不自动写入共同v5或AA/POLY/CT。net_edges空、整网/自动导出/精确投影/共同几何采用均关闭。

硬失败只写`diagnostic.json`并以非零退出，不写成功模型/页面。目录已存在则不覆盖。未测试浏览器实际交互时明确区分HTML/SVG/JS检查与交互验收。固定样本回放和软件测试不等于新照片识别准确率；试用结果见[验证报告](../reviews/2026-10-24-conductive-workflow-trial.md)。

## 已观察孔组与人工承载更正

有多孔数量证据时，接口可提供`cut_array_candidate={rows,columns,origin_xy}`及`count_evidence`人工记录引用；尺寸和pitch从既有via_budget读取，`bounds`必须等于全阵列包络。脚本逐孔检查方形、间距、阵列pitch和两侧包围，不能把六孔缩成一个6×6支持框。人工孔数与AI候选排列/尺寸分开保存；没有明确阵列时旧组级代理仍是未验证孔组占用的候选，不能用其单框包围声称多孔占用已通过。

人工只审连接、未审逐孔数量时，可附`array_source_evidence`引用AI观察：`actor=AI,kind=via_array_observation,interface_id,layer,source_frame,source_photo,native_bounds,rows,columns,count_status=candidate_not_human_count,sites=[{row,column,native_xy}]`。接口ID在中样适配器中绑定reviewed_id，在原生统一观察中绑定id。照片和范围须与当前接口一致，站点需完整、唯一、位于原生组内并保持行列次序。检查只验证AI记录自洽，不证明照片检测正确；人审孔数仍未知，来源尺寸资格不提升。已有明确人工行列/数量时继续走更严格的继承校验，不能由AI记录替换。

局部承载变化复用金属`local_parts`，不增加导体ID。P08例子只增加与原骨架正面积相接的照片支持矩形，原生路径、设计骨架、其他宽度和已审连接保持。全孔组必须受上下金属包围，同层间距也须通过；不能把扩宽后的几何检查当作照片边界已被批准。

V1与V2可在XY投影重叠，间距门只比较同一孔层。分别检查各自相邻金属的包围；它们不是同一个物理孔，不能用跨层孔中心建立同孔配准。整组尺寸不能照搬6px示例：有`array_source_evidence`时，允许`cut_array_candidate.geometry_parameters={cut_size_px,pitch_xy,basis}`选择局部设计尺寸和节距；只可改这两个几何量，不可降低全局minimum_cut_width/gap/enclosure。选择仍是来源支持的候选，不是实际PDK尺寸。

用户只补充孔数/定性重叠时，几何反馈与原连接审批分开：`kind=via_group_geometry_feedback,actor=human,statement,decisions.interface_id,observed_cut_count,scope_signature,sources`，sources绑定旧submitted_request/page/manifest及来源照片。`scope_signature`须匹配旧送审接口与当前候选的来源/承载身份。可作为`count_evidence`载入已知数量，另记`observed_group_count_facts`，不替换既有连接审批或把新坐标自动批准。数量、排列、相对位置和精确尺寸分别表述。

人工明确指出承载错误时，新review仍绑定实际旧送审包，增加`carrier_correction={before,after}`完整接口signature，并在decisions写正确承载。只可修改上下金属ID，不能改层对、源帧或原生支持窗口；父包修订须显式列出变化对象和提案依据。已审其他接口必须保持；当前没有允许撤销或替换已确认接口的机制。稳定ID的历史后缀不是承载语义，保留ID并明确更正后的关系。

解决旧pending后，若需撤下它独有的待审限制，request的`resolved_limits`用“原限制全文→人工review引用”显式列出；该review须声明完全匹配的`resolves_limit_texts`，且本次确实解决父包该pending接口。不能用Q1裁决消除A/B连续性等无关未知；已解决限制与依据继续留在模型历史中。软件能检查记录绑定与声明范围，文字判断仍由AI/人工负责。

实际首例见[Q1承载更正](../reviews/2026-10-24-independent-Q1-carrier-correction.md)。旧样本与旧质量门结果保留，不能把今天的人工更正倒写为初次候选已正确。

## 中样复查后的质量分项

统一入口现在在report.quality中分开输出下列状态，复核页同步展示；原status只代表技术交付，不是几何采用资格。

| 维度 | 执行内容 | 不能推出的结论 |
| --- | --- | --- |
| 程序/来源完整性 | 哈希、裁片像素、来源层对、正交、间距、包围、变化范围与旧批准 | 照片对应正确或真实工艺DRC通过 |
| 声明来源形状 | 比较原生与设计的带符号转折，允许同轴点合并与小幅拍摄歪斜；清晰反向硬拒绝，斜向模糊为NOT_EVALUATED | 原生路径本身识别无误、宽度正确、照片已配准 |
| 承载身份 | 已审/待定/否决分别记录 | 已审连接自动批准具体边界、孔径、排列和间距 |
| 孔组几何 | 每组明确proxy或显式阵列；已知人工数量须与完整候选一致，不能删字段规避；原生孔组须落在送审窗口内 | 单代理框包围等于完整孔组包围，或相对阵列等于实测阵列 |
| 覆盖与预算 | 表示对象数、已审清单分母、原生端部状态、尚未建立的测量预算 | 既有审批清单等于全部可见对象；11/38等于照片覆盖率 |

本批原生帧未声明镜像，带符号转折一致性作为当前约定；未知来源若有镜像应先在输入标准化阶段核清，不能直接反转设计绕过。检查只消费声明路径，不做像素检测。

readiness分别输出review_package、canonical_geometry_adoption、complete_network_export、unrestricted_skill_release。当前可交复核包，后三项始终关闭；所有旧几何、审批记录和冻结页保持。新复查的[中样输入](../../benchmarks/conductive-quality-review-v1/medium-request-v1.json)已纠正R-M2-3返回方向；旧中样现应被新门拒绝，不能再拿旧PASS替代新复查。原trial固定包仍是当时事实，当前验证见[质量复查报告](../reviews/2026-10-24-conductive-quality-review.md)。
