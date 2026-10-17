<!-- Source: CURRENT_TASK.md; archived 2026-10-17 before electrode-resolution v8. Original bytes follow. -->
# 当前任务

## 目标、授权与入口

当前目标：按用户最新指令切回P1（Q1/Q2共栅—MOM P1）全网点亮；沿已审链核查全部可见分支，P2只作独立参照。只用现有照片，不要求照片外补图；未审接点保留候选，不跨电容并网。

- 工作目录为内层silicon-eye；原照片data/不可修改，派生物在runs/，单位保留原生像素。
- 用户授权本机适配、编号/金属demo及向更高层延伸；普通本机修改与校验可继续。当前无新GitHub推送、外部视觉服务或平台建设授权。
- 阶段1“补齐GitHub证据”已推送并核验main=2d264db8aa4b9b4dd243e5c5606ab3e916dc57aa；阶段2/3和后续适配、case、图稿均有本机未提交工作，保留用户修改。
- 原三项目标为证据补齐、最小AI观察/历史基准、对照原workflow设计多层照片→电路图/编号/端口与点亮架构。当前金属追踪是其中细子流程，不冒充完整skill或全自动提取。

## 当前已审物理状态

- **最新更正优先**：G接此前蓝色H已确认；以下历史P1/P2称谓不再作为当前物理电极映射。端口归属冲突以v7纠偏记录为准，既有物理连接保留，不解释为电容短接。

- 同芯片逐层去层显微镜拍屏，原图5712×4284；每层独立原生坐标，不凭同尺寸或鼠标拟合推断整片准确。
- ROI2：两条相邻MOS栅指Q1/Q2，poly局部不直接连、经M1共栅；中间扩散共享源漏、体端共用；外侧源漏共接未知。不指定N/P/S/D/WL，不自动合并为一个器件。
- AA片段/poly主体身份及粗位置确认；精确边界/WL仍未知，10px/μm未确认。
- 已审链：Q1.G→gate端CT→M1中部双横线靠上段→右端连接处V1→M2(A)→V2(A)→M3(A—C)→V2(C)→C侧M2。C竖线经过鼠标遮挡处连续，C下段映射已确认。
- A、C分别接同根M3左右端已确认；后续E接另一根M3右端、F接该M3左端及所示M2短端均已审。F过孔为M2/M3桥接V2，不证明全网已提完。
- D接所示另一根长M3已被用户否决；不再将那根M3的出框当本网络的证据，D照片外精确去向未知。
- E接旧选M1竖线下端已否决；历史E=V1结论已撤回。最新用户确认E不接M1、M1未见对应孔而M2见孔，认为应接M3。随后用户确认E接所示左侧独有M3右端，M2/M3桥接归一为V2；旧E=V1结论不恢复。
- 用户确认F/G均不直接接所示M1，而经V2接M3；G下方接所指电容的一端（旧称MIM，最新用户更正为MOM）。结合已审链，该端与Q1/Q2共栅网同网。随后用户指定另一端P2为下方所指三个方形电容中最左侧最上方非贯通金属，并以M2顶部连接判读；蓝色H像素参考身份/显示位置随后获确认。P2具体外部节点、容量、上下极板及精确G侧M3路径未知，不将电容两端并网。
- 用户确认L1：P2中间M2经V1接M1边缘金属；M1↔V1↔M2↔V2↔M3所示链已审。电容类型更正MOM，中性ID R2_CAP_01保留旧R2_MIM_01端口别名，旧源/裁决不覆盖。多层叠置不自动批准任意重叠或另一电极并网。
- V3旧案两MOS共享中间扩散，Q1.G/Q1.B/Q2.G/Q2.A同网；额外并网无证据、Bulk各自未知，不将其裁决借到ROI2。

## 最新case与来源

- [case v14](benchmarks/block-case-v1-roi2-G-M3-MIM-reviewed-v14.json)：新增Q1.G到R2_M3_G_MIM_access_01确认映射；其他端子映射及端子矩阵不变。
- state_id：702dbe14c70bd5961b7307b5f3458301202aa370a8b9be372ce2940ddd044e67；见[v14导出](runs/roi2-G-MIM-reviewed-v14/circuit/manifest.json)。
- [A/C裁决](benchmarks/metal-extension/roi2-M3-A-C-review-feedback-v1.json)、[C/D/E初次反馈](benchmarks/metal-extension/roi2-C-D-E-review-feedback-v1.json)、[E层次更正](benchmarks/metal-extension/roi2-E-via-layer-correction-v2.json)；原记录不覆盖，更正显式绑定历史源。
- [gate/CT/M1裁决](benchmarks/terminal-highlights/roi2-q1-gate-ct-m1-review-feedback-v1.json)、[M1/V1/M2裁决](benchmarks/metal-extension/roi2-M1-V1-M2-review-feedback-v1.json)。旧上方宽M1横条候选已否决，不再重用。

## 当前结果与唯一下一步

用户给出M2/M3鼠标不变约束，并认为E接“下面第一根只有左侧有、右侧没有的M3”。已完成鼠标白色轮廓仿射拟合与六组阈值敏感性，未用目标M3端部拟合。

- [配准复核图](runs/roi2-E-cursor-registration-v1/E-cursor-aligned-review.png)、[技术说明](docs/roi2-E-cursor-registration-v1.md)、[矩阵/来源/参数](benchmarks/metal-extension/roi2-E-cursor-registration-candidate-v1.json)。
- E M2(3278,3807)→M3约(3316.92,3830.42)，支持所指左侧独有横线右端对应。鼠标轮廓P95约1px，黄色UI检查约0.13px；六组阈值E最大偏移4.34px。均为屏幕标记/敏感性指标，不是芯片结构误差保证。
- E在鼠标附近拟合支撑外约465px，芯片跨层显示是否另有移动、局部畸变及粗点误差未独立闭合。不得称精确芯片结构配准已验收。
- 唯一下一步：用户最新明确“G是连接到蓝色的这根弦”，确认G→此前蓝色H；不再询问该接点。见[新裁决](benchmarks/metal-extension/roi2-G-blue-H-review-feedback-v1.json)、[当前拓扑纠偏v7](benchmarks/metal-extension/roi2-gate-MOM-topology-resolution-v7.json)、[原图及更正宽图](runs/roi2-G-blue-H-reviewed-v2/G-H-corrected-wide-review.png)。H曾标P2/另一端，与gate链曾归P1发生端口归属冲突；P1/P2物理映射暂挂，不把两端短接、不自行交换编号。H/J/K/L1既有物理连接保留，可归入G/H物理网络追踪；掩码扩展仍为候选。当前需复核橙色相对梳齿是否才是另一电极，或此前另一端定位有误；A下分叉、中段M2接入及M4仍未闭合，未宣告全网完成。
- C侧全部金属点亮仍未完成；中段额外M2接入、M4及照片外覆盖仍未知。

## 已有工具与未提交交付

- 统一复核包：`.venv/bin/silicon-eye annotate review-package --spec benchmarks/review-package-roi2-v1.json --root . -o 新目录`；[说明](docs/review-package.md)。
- 新检出先恢复9项历史审核输入：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/roi2-reviewed-inputs-v1.zip --root .`。不是全部runs归档。
- [观察格式](docs/agent-observations-v1.md)、[V3/ROI2历史评测种子](benchmarks/agent-eval/index.json)、[适配说明](docs/observation-adapter-v1.md)、[顶层照片栈架构](docs/architecture/photo-stack-workflow-v1.md)。种子参与过开发修正，不是盲测/跨芯片评价，无新Agent分数/耗时/纠正次数。
- agent_observation/agent_evaluation、observation_adapter/cards、device_index、terminal_highlight及review_package扩展和测试均仍有未提交修改；不覆盖或清除。
- 观察→材料卡/既有case显式适配可用性已审；[反馈](benchmarks/agent-adapter/roi2-usability-review-feedback-v1.json)。历史重放样稿不是新AI识别成绩。
- 器件编号图已批准；[反馈](benchmarks/agent-adapter/roi2-device-index-review-feedback-v1.json)，保留Q1/Q2稳定ID。AA逐器件精确定位仍未知。
- terminal_highlight支持显式凸多边形候选及gate/CT上下文，不是自动追踪。正式PhotoStack入口、完整物理导体图、PortAnchor事件与整网自动点亮/skill尚未实现。MOM两端身份/位置描述及跨层边只在有来源的伴随拓扑中表达，通用case的电容schema/导出尚未实现。
- 最后一次生产代码检查248 tests及相关Ruff通过；独立源重放30产物一致。后续为观察/裁决/图稿工作，只做相应来源/schema/状态/导出/图像检查，不声称测试等于物理正确。

## 验证与预览边界

- 来源哈希、人工原话绑定、case schema、确认矩阵及端子状态通过既有工具复算；L1及MOM类型保持已审；本轮新增P1覆盖候选与图像分量检查，不新增人审连接；原case v14与P1关系保留，伴随拓扑v6使用中性电容ID及显式旧别名，无P1/P2并网；失败的局部配准仍未接受，不能以人审接口确认替代精确变换验收；图稿已目视检查，原图未改。未新增生产代码或全套重测，未推送。
- 内置浏览器访问本机预览被安全策略拒绝，不能改用其他浏览器/CDP绕过。对话直接提供静态图片与绝对路径原图，不声称localhost已可用。
- [M1/M2无缩放宽图来源](runs/roi2-E-original-evidence-v1/manifest.json)；[M3原生宽图](runs/roi2-E-M3-review-v1/m3-wide-native.png)。局部裁剪共享坐标范围不代表已配准。
- Q2逐CT映射不因共栅补齐；未知不当断开/同网，材料身份不当精确边界，鼠标/UI标记不当芯片过孔。

## 完整历史与恢复

- [本次精简前完整入口](docs/history/current-task-through-2026-10-16-E-layer-correction.md)：保留阶段2/3、历次编号/金属demo、裁决、命令、未提交状态和恢复信息。
- [统一包阶段原文](docs/history/current-task-through-2026-10-16-unified-package.md)、[更早入口](docs/history/current-task-through-2026-10-16.md)。
- 本次仅归档当前入口历史，原始证据、既有人工记录及旧case不改；恢复开发前优先读取本入口和AGENTS.md。
