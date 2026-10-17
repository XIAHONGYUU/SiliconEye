# CURRENT_TASK 原文归档

来源：CURRENT_TASK.md；归档日期：2026-10-16。完整保留精简前原文，历史候选/裁决以各自后续更正为准。

---

# 当前任务

## 目标与授权

用户本轮要求依次完成：

1. 补齐GitHub示例缺失证据，验证新检出重放后提交一版GitHub。
2. 制定最小AI观察格式，按已有V3/ROI2两批结果建立可迭代评测种子集。
3. 对照项目原workflow完善顶层架构：同位置多层照片输入，电路图/器件标号/金属端口与高亮输出，明确skill边界及未实现项。

阶段1允许提交推送；阶段2/3及后续适配在本机实现/设计与验证。用户追加授权“先完成适配与样稿，我来核查与使用”，随后批准“直接推进到编号视图完成”。随后授权完成R2_Q1 gate金属高亮demo。用户最新授权从已审M1局部段向M2/M3及更高层延伸；范围扩大但每次跨层仍需证据。本轮不擅自推送、升级候选为物理批准、调用外部视觉服务、安装PDK或建设平台。

## 已确认事实与边界

- 原始照片来自同一芯片逐层去层拍屏；每张保持独立原生像素坐标，不能凭同尺寸推断配准。
- V3：两MOS共享中间扩散；Q1.G/Q1.B/Q2.G/Q2.A同网，外侧A/B对应M1上下横条；额外并网无证据，Bulk各自未知。M2-P2对应V3组，但路径/端子映射未知。
- ROI2：两条相邻MOS栅指，poly局部不直接连、经M1共栅；中间共享源漏、体端共用，外侧M1共接未知。不自动归并为单个MOS或默认体端接电源。
- ROI2 AA片段与两poly主体身份/大致位置确认；精确多边形/像素边界、精确CT落点、W/L仍未知；后续R2_Q1 gate端CT归属与局部M1选段已单独获批。
- ROI2 gate端CT→M1局部段→右端连接处V1→M2短竖段上端已获独立人审；V2及A/C两端接入同一M3已确认；M2长支路整体几何与全部分支覆盖仍未知。
- ROI2 M1→poly限定两框宏观透视叠图已确认；不外推AA细配准、其他区域/整芯片或尺寸精度。
- 10px/μm仍为未确认假设，不换算真实W/L；未知不当隔离或同网，不借用跨案例批准。

## 最新工具与验收

- 统一包入口：`silicon-eye annotate review-package --spec benchmarks/review-package-roi2-v1.json --root . -o 新目录`。
- 首次运行需先恢复证据：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/roi2-reviewed-inputs-v1.zip --root .`。
- [说明](docs/review-package.md)；[ROI2固定结论](docs/checkpoints/2026-10-16-roi2-reviewed.md)；[顶层纠偏](docs/workflow-realignment-2026-10-16.md)。
- 统一包的block_state_id：4aab154bbcb952acbcdce88f129b82ebacd28e7e633167ce39f807ff9b59c02f。
- 本轮全套200项测试通过（新增4项恢复测试），此前196项测试通过，原GitHub main为10058081e693e2b920812e7dbef87e7ecce535c8；后续观察/评测新增11项行为测试，最终全套211 tests与相关Ruff通过。
- 已归档9项历史runs审核输入，原字节/路径/裁决哈希不改，runs本身仍不整体提交。不是全部历史runs恢复包。

## 当前进度与唯一下一步

阶段1已通过：干净的暂存Git检出起初没有runs，恢复9项归档后重放，17项产物哈希及bundle_id与原结果完全一致；200 tests、相关Ruff与diff检查通过。阶段1已推送main并核验远端2d264db8aa4b9b4dd243e5c5606ab3e916dc57aa。阶段2/3已在本机完成下述交付，尚未提交推送；无第三ROI或模型平台扩展。

评测暂按V3、ROI2两批组织，均为参与过开发和人工修正的历史种子集，不是盲测/独立跨芯片样本；参考答案仅覆盖已确认事实和明确未知。

唯一下一步：按E→M3方向核查过孔及具体导体。用户最新更正：E不接M1，M1未见孔/M2见孔；原E=V1身份已撤回，V2及M3去向为候选，尚无具体M3批准。[更正来源](benchmarks/metal-extension/roi2-E-via-layer-correction-v2.json)，[M3原生宽图](runs/roi2-E-M3-review-v1/m3-wide-native.png)。case v11确认矩阵/端子映射保持v10，禁止沿旧M1候选或D侧已否决M3扩网。

## 本机第2/3项交付

- [观察格式](docs/agent-observations-v1.md)：schemas/agent_observation.py支持原生窗口、材料/器件/关系候选和unknown，边界与身份分离，AI不能自报confirmed或返工次数。
- [两批种子](benchmarks/agent-eval/index.json)：V3/ROI2各一个任务、各10条参考，共16条已知/4条未定。原始人审记录哈希绑定；尚无新Agent运行成绩，纠正次数/耗时均未测量。
- agent_evaluation.py只比对部分参考断言；全部unknown不能通过，有参考外断言需复核。不评估像素定位、完整器件发现或总体物理质量。
- [顶层架构](docs/architecture/photo-stack-workflow-v1.md)：正式输入为同区域多层照片，共用器件/端子/导体身份，电路图/编号/端口标注/点亮作为独立输出；区分逻辑同网与物理导体图。当前统一包只是复核/导出子流程。
- 正式PhotoStackManifest、PortAnchor/金属高亮、skill仍为设计待实现；跨层编号视图已实现可选输出。不把旧微米schema强填为假尺寸。README增加实现范围与架构入口，保留原目标。
- 新代码/基准/架构/README和当前入口是第2/3项未提交工作。全套211 tests、相关Ruff、种子哈希/文档链接检查通过，未新增物理结论。

## 本轮适配与样稿（可用性已验收）

- [适配说明](docs/observation-adapter-v1.md)：observation_adapter.py生成新case proposal、unknown卡和材料卡；不修改原case/人审事件，不把窗口当边界，不自动并网。统一包重算并核对适配来源和派生结果。
- [可视样稿](runs/roi2-observation-adapter-v3/review/index.html)；[结构化适配](runs/roi2-observation-adapter-v3/adaptation.json)；[验证记录](runs/roi2-observation-adapter-v3/verification.json)。ROI2共10卡，来自历史结论转写，不是新AI识别或成绩。
- 样稿含原图位置索引、材料窗口、既有材料图/宏观叠图及电路/四端表；细边界、CT落点、W/L仍未批准。
- 226 tests、相关Ruff及diff检查通过；ROI2来源单独拷贝重放27项产物哈希一致，已确认矩阵/器件/端子/人工事件不变；V3独立case适配通过，未借用ROI2裁决。
- ROI2 bundle_id：b8d56080844c8653367c8ebe9e389a1dae5d27c1e45ade870afe5144cc0a3ce0。
- 浏览器预览：http://127.0.0.1:8765/review/index.html（仅本机，进程结束后需重启）；重启：`.venv/bin/python -m http.server 8765 --bind 127.0.0.1 --directory runs/roi2-observation-adapter-v3`。
- 用户已确认索引/材料卡易对应、状态区分清楚、连接/照片方便核对；[反馈原文及样稿绑定](benchmarks/agent-adapter/roi2-usability-review-feedback-v1.json)。仅可用性验收，不新增边界/连接批准或Agent成绩。
- 本轮及前述第2/3项均未提交推送；原始照片/人审来源未改，运行时不调用视觉模型，未创建skill。

## 器件跨层编号视图（已获用户批准）

- [使用说明](docs/device-index-v1.md)；[固定请求](benchmarks/review-package-roi2-device-index-v1.json)；[本机页面](runs/roi2-device-index-v3/device-index.html)；[重放验证](runs/roi2-device-index-v3-validation.json)。
- 用户确认“批准，编号图无误”；[原文及图像哈希绑定](benchmarks/agent-adapter/roi2-device-index-review-feedback-v1.json)。接受编号与显示的粗定位对应，AA逐器件定位仍未知，不新增精确边界/端口/连接批准。
- 复用R2_Q1/R2_Q2稳定栅指ID，可选编号跨层突出并关联四端表，导出JSON/CSV及原像素裁剪。poly沿用原生候选窗口，M1只在已审核范围内逆变换投影；AA缺少逐器件定位，明确显示未定位。不是边界、CT落点或金属路径批准。
- 236 tests与相关Ruff通过；单独复制声明证据重放23项产物哈希一致，block_state_id仍为4aab154bbcb952acbcdce88f129b82ebacd28e7e633167ce39f807ff9b59c02f。
- 浏览器已实测Q1/Q2切换、恢复全部、分层跳转、4张图片加载正常、无横向溢出；四端表和已确认网络不变。本轮未提交推送。
- 预览：http://127.0.0.1:8766/device-index.html；重启：`.venv/bin/python -m http.server 8766 --bind 127.0.0.1 --directory runs/roi2-device-index-v3`。

## 未完成能力

运行时自动材料/器件提取未接入；统一包重放既有判断。已有器件稳定编号与跨层查看；顶层照片栈输入、端子→金属证据与走线交互高亮仍未实现，不能把局部宏观配准或逻辑节点冒充精确物理网络。

## 历史与恢复

- [本次精简前完整原文](docs/history/current-task-through-2026-10-16-unified-package.md)保留所有阶段过程与裁决来源。
- [更早入口原文](docs/history/current-task-through-2026-10-16.md)。

精简仅整理入口；原始证据/批准记录未改，未完成的重放、AI观察、评测与顶层设计均已保留。

## 预览访问补充

用户报告看不到本机视图。内置浏览器安全策略拒绝访问该本机URL，未绕过策略；提供[离线静态编号图](runs/roi2-device-index-static-v1/device-index.png)直接在对话/文件预览查看。静态图从原编号JSON与哈希验证的照片生成，不修改原包或原始输入；交互页面当前可访问性未确认。

## R2_Q1.G金属高亮demo v1（已被用户否决）

- [说明与重放](docs/terminal-highlight-demo-v1.md)；[显式候选](benchmarks/terminal-highlights/roi2-q1-gate-m1-candidate-v1.json)；[静态对照图](runs/roi2-q1-gate-highlight-demo-v1/terminal-highlight-001-demo.png)。
- AI选择上方公共横条局部段，黄色高亮；紫色十字仅候选锚点。Q1/Q2 gate经M1同网已有裁决，但具体段/CT落点未确认，不用逻辑同网填物理路径。
- 统一包支持terminal_highlights候选来源，输出原图/叠图/候选mask/JSON/静态demo/HTML开关页。独立凸多边形与锚点只用于显示，不能当材料真值；不改原图或case。
- 243 tests、相关Ruff通过；来源单独拷贝重放29项产物一致，确认block_state_id保持原值。本轮静态图已目视检查，未绕过浏览器限制验证HTML交互；未推送GitHub。

## Gate→CT→M1 v2（对应关系已获人工确认）

- 用户要求先定位gate上的CT，再找M1；[旧上方横条否决](benchmarks/terminal-highlights/roi2-q1-gate-upper-bar-rejection-v1.json)保留原文/图像绑定。原有编号及逻辑同网批准不变。
- [说明](docs/gate-ct-metal-review-v2.md)；[显式候选](benchmarks/terminal-highlights/roi2-q1-gate-ct-m1-candidate-v2.json)；[复核图](runs/roi2-q1-gate-ct-highlight-v2/terminal-highlight-001-ct-bridge.png)。
- poly候选CT为gate下端扩展亮斑簇，中心(1756,2831)，投影M1约(1731.48,2956.91)；候选M1锚点(1732,2966)，高亮中部双横线靠上局部段。偏移9.1px、搜索范围16px均不证明准确落点；CT归属/CT→M1均candidate。
- contact_bridge接入既有高亮入口，验证源frame/CT窗口/已审配准/逆投影/搜索范围；图稿同屏展示gate/CT/金属链条。248 tests及Ruff通过，独立来源重放30项产物一致，已确认block_state_id不变；未推送。

## Gate/CT/M1本次裁决落盘

- 用户原文“CT归属与M1选段确认无误”；[独立裁决](benchmarks/terminal-highlights/roi2-q1-gate-ct-m1-review-feedback-v1.json)绑定原候选与复核图哈希，旧候选/否决/图稿均保留。
- [case v6](benchmarks/block-case-v1-roi2-gate-ct-m1-reviewed-v6.json)新增确认的R2_Q1.G→R2_M1_gate_segment_01，已用既有block入口导出[状态](runs/roi2-gate-ct-m1-reviewed-v6/report.md)。只登记选段对应，不新增同网；Q2逐CT映射不自动补齐。
- 来源/人工事件/schema验证通过，确认连接矩阵和同网组与v5一致；仅Q1.G的导体映射变为confirmed。精确边界、CT像素落点、段外延伸仍未知；高亮原候选记录不覆盖，下次需显式适配人工批准。未提交推送。

## 向高层延伸：停在M1→M2过孔证据

- [本轮调查](docs/roi2-upper-metal-survey-v1.md)；[观察/候选配准](benchmarks/metal-extension/roi2-gate-upper-metal-survey-v1.json)；[复核图](runs/roi2-upper-metal-survey-v1/M1-M2-review-v2.png)。
- M1上横段可见右端折返回下横段，作为延伸候选；M2叉形仅搜索对象，尚未分配gate网。红圈约(1727,3009)是候选交叠位置，未看到可靠V1接通证据。
- M2/M3/M4原图均在，最高M4；旧M2 ORB失败，旧M3变换未被本区验收，不沿用为接触定位。两阵列8对新AI对应点仅拟合候选affine，没有独立检查或人审，不以3.51px拟合残差宣称精度。
- 6项来源哈希/schema/原人工事件及既有确认状态复算通过，case v6状态不变。没有新生产代码或全套重测；M1→M2为unknown，M3/M4尚未接入gate网络，未推送。

## V1位置更正（用户已指出M1连接处）

- [用户原文与来源](benchmarks/metal-extension/roi2-v1-M1-join-feedback-v1.json)：V1在M1照片侧、两条平行M1的连接处；具体像素中心仍为AI粗定位，未批准M2连接。
- [新观察](benchmarks/metal-extension/roi2-v1-M1-to-M2-endpoint-candidate-v2.json)；[对照图](runs/roi2-v1-turn-review-v1/V1-M1-M2-review.png)。M1约(2355,2957)，M2候选短竖段上端约(2278,3028)，旧候选affine投影约(2284.7,3003.2)，偏差约25.7px，不当精确配准或接通证明。
- 旧M2左侧叉形搜索不作为当前V1位置；新M2端部/局部段仍candidate，未改确认case/网表，未推进M3/M4，未推送。原照片与旧观察保留。

## M1→V1→M2已确认，下一停点V2

- [本阶段checkpoint](docs/checkpoints/2026-10-16-roi2-M1-V1-M2-reviewed.md)；[人工反馈](benchmarks/metal-extension/roi2-M1-V1-M2-review-feedback-v1.json)；[case v7](benchmarks/block-case-v1-roi2-gate-M1-V1-M2-reviewed-v7.json)。Q1.G确认关联M1/M2两个局部段；矩阵及同网组不变，新state_id为1162eb1eebc51165ed0f6481cb6f02fd6eeb1812a69d995fe8681ce99924de37。
- [M2延伸/V2观察](benchmarks/metal-extension/roi2-M2-extension-V2-candidate-v1.json)；[复核图](runs/roi2-M2-to-M3-survey-v1/M2-path-V2-review.png)。黄色路径为AI候选；短支路亮端约(2231,3332)为V2搜索候选，身份及对应M3未确认。
- 来源哈希/schema/人工事件/原生尺寸、case导出及矩阵不变验证通过；无新生产代码或全套测试重跑。旧M2候选和历史配准保留，不升级为精确落点。未推送。

## V2已确认，M3对应候选待复核

- 用户原文“确认为V2”；[反馈](benchmarks/metal-extension/roi2-V2-review-feedback-v1.json)绑定原图稿；确认所示短亮端V2身份，不自动批准每段黄色M2几何或特定M3导线。
- [新观察](benchmarks/metal-extension/roi2-V2-M3-candidate-v1.json)；[对照图](runs/roi2-V2-M3-review-v1/V2-M3-review.png)：M3候选为下方细横线左端约(2252,3369)，本轮原图结构判读，未使用已审跨层变换，需人审排除相邻平行线。
- [case v8](benchmarks/block-case-v1-roi2-V2-reviewed-M3-proposed-v8.json)保存V2 image_feature及M3未审proposal；[导出](runs/roi2-V2-M3-review-v1/circuit/report.md)。来源/schema/人工事件/像素尺寸通过，M3 claim仍candidate，确认端子映射及矩阵与v7完全一致。无生产代码变更或全套重测，未推送。

## M3条件追踪与遮挡检查

- [观察](benchmarks/metal-extension/roi2-M3-conditional-extension-v2.json)；[扩展复核图](runs/roi2-V2-M3-review-v1/V2-M3-extended-review-v3.png)。M3仍未获对应批准，只按候选下横线向右检查。
- 靠近末段约(3230,3325)附近有拍屏鼠标/黄色UI标记，不是芯片过孔；遮挡处不补连续线。末端身份/V3仍未知，M4未归入gate网。
- 已核对6项来源哈希、case schema/事件与导出状态，M3 claim仍candidate，Q1.G确认导体仍仅M1/M2。无代码变更、无全套重测；当前必须核查V2是否对应所示M3左端，不能用近邻或继续指令替代物理确认。

## 整根M3的M2分支清单（候选，完整性未闭合）

- 用户要求找到M3后找出其全部连接M2；不再只追一条上行路径。此要求不等于批准此前M3对应。
- [观察清单](benchmarks/metal-extension/roi2-M3-M2-fanout-candidate-v1.json)；[复核图](runs/roi2-M3-M2-fanout-review-v1/M3-all-M2-review.png)。A为已审V2身份所在位置，C为右侧M2顶部亮端新候选；两处到M3的边均未确认。
- B/D保留为邻线排查；C/D可能同属一条M2，不能按亮端数量算不同导体。中段交叠与鼠标遮挡仍unknown，M2连接总数未知，不能宣称只有两条。
- 来源哈希、原生坐标与case确认状态复算通过；未改原图、人工裁决或case，未并网、未推送。

## A/C接入同一M3已确认（case v9）

- 用户原文“A、C 分别连接图中这根 M3 的左右两端”；[独立裁决](benchmarks/metal-extension/roi2-M3-A-C-review-feedback-v1.json)绑定旧图/候选哈希，不覆盖原记录。
- [case v9](benchmarks/block-case-v1-roi2-M3-A-C-reviewed-v9.json)确认Q1.G→M3及右侧局部M2 C；[分支清单v2](benchmarks/metal-extension/roi2-M3-M2-fanout-reviewed-v2.json)、[确认图](runs/roi2-M3-M2-reviewed-v9/M3-A-C-confirmed.png)。两处接入已审，完整连接数量仍未知，B/D及C侧其他器件端子不自动补齐。
- 来源/人工事件及导出通过；矩阵、其他端子行不变，Q1.G新增M3/C段映射，state_id为a6bcb7b5f1bc5af30083ce50324db08bff8f7ca09cee5e82291caae38c5dc8aa。中段目视复看未发现可靠第三接通证据，不能据此判定不存在。无代码变更、未推送。

## C侧金属全范围点亮调查（待跨层复核）

- [复核图](runs/roi2-C-metal-light-v1/C-all-metal-review.png)和[记录](benchmarks/metal-extension/roi2-C-all-metal-trace-candidate-v1.json)：C侧M2可见部分延伸到y约3807；鼠标处留空。D中间短支可能接另一长M3，E底部短端可能接M1孤立竖线下端。新延伸均候选，不增加确认边。
- D候选M3向左出原图边界；M4无可靠边，不能宣布全网完成。来源/既有高亮schema/凸多边形及锚点/case来源与状态检查通过，v9 state不变。无生产代码变更、未推送。

## C/D/E裁决更正与E下端V1（case v10）

- [用户原话及旧图绑定](benchmarks/metal-extension/roi2-C-D-E-review-feedback-v1.json)：C连续；D在现有图片中不接另一根M3；E不接旧选M1下端，但E下端存在V1。D照片外精确路径不自行推断，否决不转成异网。
- [更正观察](benchmarks/metal-extension/roi2-C-E-V1-reviewed-v2.json)；[case v10](benchmarks/block-case-v1-roi2-C-continuity-E-V1-reviewed-v10.json)。确认Q1.G到C下段M2，V1身份保存在独立来源，M1具体落点未知；旧D长M3/旧M1竖线不再点亮。
- 原生M1放大检索窗有多条横线，尚无唯一V1落点，不以相邻位置选段。来源/人审事件/schema/导出通过，端子矩阵与其他端子行不变；state_id为bb08203fdd7095dcbe5768c885ded5ee06909516be7e78c5ea312a6cf530e1c0。无代码变更、未推送。

## E过孔层次再次更正（v11，以本条为当前结论）

- 用户确认E不接M1，M1未见对应孔而M2见孔，认为应接M3；[新反馈](benchmarks/metal-extension/roi2-E-via-layer-correction-v2.json)显式撤回历史E=V1结论，旧记录不覆盖。V2/M3仍为方向候选，未把“应该”写成具体M3确认。
- [case v11](benchmarks/block-case-v1-roi2-E-via-layer-corrected-v11.json)改用层次中性的E过孔feature ID，保留C连续与D否决；来源/事件/schema/导出通过，确认矩阵和端子映射与v10一致。M3局部多条横线尚不能唯一确定落点，提供无缩放宽范围裁剪，不构造精确叠图。未推送。
