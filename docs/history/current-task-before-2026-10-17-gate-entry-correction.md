# 当前任务

## 目标、授权与入口

当前目标：P1（Q1/Q2共栅—MOM P1）全网点亮。只用现有八层照片，检查可见分支；关键物理歧义交由用户裁决，图外延伸保留未知，不要求额外照片。

- 在内层silicon-eye工作；原照片data/不可修改，派生物写runs/，单位为原生像素。
- 已授权本机适配、编号/金属demo及向高层延伸。当前无新GitHub推送、外部视觉服务或平台建设授权。
- 最近已推送main=2d264db8aa4b9b4dd243e5c5606ab3e916dc57aa；之后阶段2/3、工具、case及金属追踪仍有本机未提交修改，保留。
- 当前金属追踪是多层照片→电路/编号/端口点亮架构中的子流程，不声称完整skill或全自动提取已完成。

## 最新验收：电容两端归属已解决

- 用户先确认“G是连接到蓝色的这根弦”，再确认“是的，橙色这异端的梳齿以及右侧母线，才是电容的另外一端。”
- **P1=共栅G/H侧**，此前H→J左延续、K中间纯竖向M2、L1经V1接M1的已审物理链均归P1。
- **P2=橙色梳齿及右侧母线**。旧H/K/L1=P2归属被更正，v7端口冲突解除；不将电容两端并网，不交换电容端口ID。旧金属ID中P2字样用显式别名更正，旧照片/裁决/文件名保留。
- [人审反馈](benchmarks/metal-extension/roi2-MOM-opposite-electrode-review-feedback-v1.json)、[当前伴随拓扑v8](benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v8.json)、[覆盖观察v2](benchmarks/metal-extension/roi2-P1-corrected-coverage-v2.json)、[说明](docs/roi2-MOM-electrodes-reviewed-v8.md)。
- [更正后三层点亮总览](runs/roi2-P1-ports-reviewed-v8/P1-corrected-three-layer-review.png)。电极身份已审，精确掩码及未审跨层接口仍为候选；绿色图像分量扩展不等于整块像素均获人工批准。

## 已确认物理事实与边界

- 同芯片逐层去层显微镜拍屏，原图5712×4284；各层独立原生坐标，鼠标拟合不等于整片精确配准。
- ROI2为两条相邻MOS栅指Q1/Q2；poly局部不直接连，经M1共栅；中间扩散共享源漏，体端共用，外侧源漏共接未知。不指定N/P/S/D/WL；10px/μm未确认。
- P1已审主链：Q1.G→gate端CT→M1中部双横线靠上段→右端V1→M2(A)→V2(A)→M3(A—C)→V2(C)→C侧M2→E(V2)→M3(E—F)→F(V2)→M2(F—G)→G(V2)→H/P1。另有H→J→K/M2→L1/M1。
- C经过鼠标遮挡处连续已审；A/C为同根M3两端。E为所指左侧独有M3的右端，F为其左端。
- 已否决：旧上方宽M1条、D接另一长M3、E接旧M1竖线下端、F/G直接接M1。旧E=V1已撤回，当前E为M2/M3桥接V2，不能恢复旧错误路径。
- 电容类型MOM，中性ID R2_CAP_01，旧R2_MIM_01保留别名；容量、总单元数量、上下极板归属未知。多层重叠不自动证明相接。
- V3旧案的端子并网裁决不借用于ROI2。未知不当断开/同网，材料身份不当精确边界，UI/鼠标不当过孔。

## 唯一下一步与未闭合覆盖

**下一步：先复核六竖线局部配准及独立V1覆盖，再明确A侧M2上三叉U1/U2/U3的真实M1落点；新结构对齐与旧U3共栅像素锚点不一致，不预设三端都落在共栅。** 见[上三叉与M1原图宽图](runs/roi2-P1-MOM-closed-v13/A-upper-fork-interface-review.png)、[剩余接口记录](benchmarks/metal-extension/roi2-P1-remaining-interfaces-v13.json)。不使用撤回的旧仿射作投影；U1/U2只是明确标出的现有端部，不凭邻近推定落点。

- **上一版单点平移已被用户否决**，保留[runs旧图](runs/roi2-A-upper-fork-overlay-v1/A-upper-fork-overlay-review.png)仅作历史。按用户六竖线对应标准生成[新叠图](runs/roi2-A-six-lines-registration-v2/six-lines-aligned-overlay-review.png)、[独立下排覆盖检查](runs/roi2-A-six-lines-registration-v2/independent-lower-tip-coverage-review.png)、[参数](benchmarks/metal-extension/roi2-A-six-lines-registration-candidate-v2.json)：上端1/3/5拟合相似变换，2/4/6留出偏差1.51/4.57/0.46px；下排六处M1端部候选均目视落入M2竖线范围，非独立人工V1身份批准。U1/U2/U3新投影靠近下排M1指状端部，旧U3→M1(2355,2957)像素锚点撤回；已有导体级人审连接保留，落点冲突待复核。不得凭新图自动归共栅。
- 用户指出六线拟合后M2仍应下移以覆盖上方M1 V1。已生成[下移0/5/10/15px四档对照](runs/roi2-A-six-lines-downshift-v3/downshift-comparison.png)及[原图参考](runs/roi2-A-six-lines-downshift-v3/native-reference.png)，固定六线尺度/旋转，仅改纵向平移；尚未选择/批准新变换，连接不改写。应以真实V1覆盖及线对应一起判断，不能仅靠端点残差选优。
- 用户“没有其他金属向外引出”确认现有照片内MOM P1除H/J/K/L1外没有其他出口，[人审记录](benchmarks/metal-extension/roi2-MOM-P1-no-extra-exits-review-v1.json)、[当前拓扑v13](benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v13.json)。MOM出口复核闭合，不重复询问、不扩展为其他区域全无V3/M4；照片外仍unknown。
- A—C中段无M2、456经V1接M1并经CT接下方MOS扩散端均已审；源漏、器件数量不指定；不穿过MOS沟道或电容介质扩网。P1/P2保持分开。
- 已确认路径见[P1整体点亮稿](runs/roi2-P1-overall-review-v12/P1-reviewed-route-overview.png)，其标题中的MOM额外出口未决提示已由v13裁决解决；整体可见覆盖尚有U1/U2未明确，不能提前宣告全网完成。
- 新记录全部源哈希、MOM裁决范围、无P1/P2并网检查通过；图稿目视检查通过，原图未改。无新变换或生产代码、无推送。
- AI观察支持A竖线向下接三叉顶部；阈值120/140时五个参考点同分量，160/180碎裂。作为候选延伸，未自动批准跨层连接。
- 仍未完成：A上三叉U1/U2落点、未审像素边界/MOM各层精确指状线、MOM范围外其他未识别M4/V3接口、照片外延伸。**未宣告全网完成。**
- 本轮M4宏观复查没有足够证据新增P1接口。图外未知不作为中断所有图内工作的理由。

## case、配准与验证

- 通用[case v14](benchmarks/block-case-v1-roi2-G-M3-MIM-reviewed-v14.json)仍为MOS部分最新case；state_id=702dbe14c70bd5961b7307b5f3458301202aa370a8b9be372ce2940ddd044e67，见[v14导出](runs/roi2-G-MIM-reviewed-v14/circuit/manifest.json)。电容及新增V1物理关系以伴随拓扑v13为准，通用case尚不支持电容导出。
- v8来源哈希、端口映射、无P1/P2并网检查通过；v14 schema/来源/状态复算不变。图稿已目视检查；原图未改，本轮无生产代码修改、无全套重测、无推送。
- 最后一次生产代码检查248 tests及相关Ruff通过；独立源重放30产物一致。这些结果不证明真实物理连接。
- [E鼠标配准说明](docs/roi2-E-cursor-registration-v1.md)、[矩阵/参数](benchmarks/metal-extension/roi2-E-cursor-registration-candidate-v1.json)：E M2(3278,3807)→M3约(3316.92,3830.42)；鼠标P95约1px、六组阈值E最大偏移4.34px，只是屏幕标记/敏感性指标。拟合支撑外约465px，不是芯片结构精度验收。
- 电容区域M1/M2配准曾失败，未接受；人工接口确认不替代精确变换验收。

## 工具、未提交工作与预览

- 统一包：`.venv/bin/silicon-eye annotate review-package --spec benchmarks/review-package-roi2-v1.json --root . -o 新目录`；[说明](docs/review-package.md)。
- 历史9项输入恢复：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/roi2-reviewed-inputs-v1.zip --root .`；不是全部runs归档。
- [观察格式](docs/agent-observations-v1.md)、[历史评测种子](benchmarks/agent-eval/index.json)、[适配说明](docs/observation-adapter-v1.md)、[顶层架构](docs/architecture/photo-stack-workflow-v1.md)。历史种子参与开发，不是盲测或跨芯片成绩。
- agent_observation/evaluation、observation_adapter/cards、device_index、terminal_highlight和review_package扩展及测试仍未提交，不覆盖。适配可用性与编号图已审，Q1/Q2 ID保持。
- terminal_highlight为显式候选几何显示，不是自动追踪；完整PhotoStack入口、物理导体图、PortAnchor事件、整网自动点亮/skill尚未实现。不新增案例专用生产脚本。
- 本机浏览器预览被安全策略拒绝，不改用其他浏览器/CDP绕过；交付静态图及绝对路径。

## 完整历史

- [本轮电极纠偏前完整入口](docs/history/current-task-through-2026-10-17-G-H-port-resolution.md)：原文完整保留，含v7冲突及未提交状态。
- [E层次更正前入口](docs/history/current-task-through-2026-10-16-E-layer-correction.md)、[统一包阶段](docs/history/current-task-through-2026-10-16-unified-package.md)、[更早入口](docs/history/current-task-through-2026-10-16.md)。
- 仅精简当前入口；原始证据、旧裁决与旧case不覆盖。
