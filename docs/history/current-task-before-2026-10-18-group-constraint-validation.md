# CURRENT_TASK archive

Source: CURRENT_TASK.md
Archived: 2026-10-18; before group-constraint validation writeback.

# 当前任务

## 当前目标与授权

2026-10-18 用户批准调整顶层方向：先标准化输入和建立可修订分层版图，再以统一数据进行器件/网络分析及输出。已授权整理设计、调整计划并提交 Git；本轮不新增远端推送授权，不沿用昨日推送请求扩大本轮范围。

- 内层 silicon-eye 仓库、.venv；原图 data/ 不改，派生试验 runs/。仅用现有八图，没有额外照片，不要求补拍。
- 暂缓原定金属独立重走和 skill 封装；不声称已执行。无新增付费视觉服务或平台；用户本轮授权选区验证后判断是否封装区域规划 skill，已按验证结果封装。
- 最近已核验远端 main=5f78c9c1a63b07680ee0808a98468a23a963fe81；本轮 Git 提交以日志为准。

## 最新状态与唯一下一步

**下一步：按顶层 v5 建立结构组/共享参数及正向设计质量门，先用底部阵列、连续 AA 环、重复 MOS 的 AA＋CT 三类对照验证，再扩展全幅。暂停 F01–F12 候选人工验收，不继续逐像素补形或增加候选数量。**

- [当前纠偏设计 v5](docs/architecture/photo-stack-workflow-v5.md)：从逐轮廓正交化改为结构组/参数化模板＋约束重建，再回投原图。单边 H/V 之外必须检查共享尺寸、基线、节距、连续性、合法孔区及重复 CT 模式；当前仅设计，尚未实现新求解/质量门。
- 本轮核查 304 个 AA 的全部边已 H/V，但新增对象无结构组模板，CT 主要按 AA 内亮点局部吸附；缺组级规律和禁区/完整包围检查。287 tests 为旧软件验证，不代表这些新要求通过。
- v1h 保留为开发候选及反例，不进入生产材料/追线；100 个未解决 AA 和旧人审范围保留。旧对象允许在新模型中有来源地修订几何，保留冻结旧版/ID 映射，不自动继承几何批准。
- 本芯片 AA/CT 采用严格 H/V 默认；非正交特殊结构须单独有证据。PDK 用于学习合法材料关系，当前尺度/工艺未知，不套用数值或宣称正式 DRC。重复族模式一致与闭环连续是有范围约束，不自动补成确认孔/连接。
- 残余证据差图可碎片化，不能作为残缺材料层使用。重建几何须规则且表达连续/开口/未知；观察与模板推断分开。当前无新照片处理、测试或 Git 提交/推送。

- [全幅复核稿与一次性清单](docs/full-scene-aa-ct-v1.md)、[最新切层页](runs/full-scene-aa-ct-v1h/index.html)、[冻结模型](benchmarks/full-scene-aa-ct-v1/model-v1.json)、[覆盖表](benchmarks/full-scene-aa-ct-v1/coverage-v1.json)、[输入参数](benchmarks/full-scene-aa-ct-v1/spec-v1.json)、[核查记录](benchmarks/full-scene-aa-ct-v1/result-v1.json)。263 个新增 AA、2743 个新增 CT 正几何候选、928 个新增 CT 待核落点；所有新增人审待定。
- 共 304 个 AA 几何、4149 个 CT 位置记录，不是独立岛/器件/物理孔总数；100 条 AA 观察未解决，7051 个来源亮点未分配给 AA，不据此断言它们是 poly CT。覆盖残余只是观察支持，不是真实漏提/覆盖率。
- 原有 519 个对象及人审字段完全不变；旧 AA 像素图一致。补正鼠标遮挡有效区后移除三个伪 AA。画布扩至 5860×4587，旧坐标和原点不动，原照片仍各 5712×4284。沿用候选变换，精确全图配准、尺度、全幅物理完整性和电气连接未验收。
- F01–F12 只用于显示，不分割材料或阻断网络。已审环/阵列与 P01–P06 不重问；旧算法疑点 79 与相应人审范围保留，不升级为新增逐孔批准。
- 全项目 287 tests、相关 Ruff、原对象/源图/输出核验、几何分离/孔位归属、SVG/静态引用和页面脚本语法通过。浏览器交互未自动实测。最新结果及此前架构/材料工作仍未提交或推送。

- [复核稿与六项清单](docs/orthogonal-aa-polygons-v1.md)、[最新单页切换入口](runs/orthogonal-aa-polygons-v1b/index.html)、[固定观察与参数](benchmarks/orthogonal-aa-polygons-v1/spec-v1.json)、[冻结模型](benchmarks/orthogonal-aa-polygons-v1/model-v1.json)、[核查记录](benchmarks/orthogonal-aa-polygons-v1/result-v1.json)。默认看 P01–P04，另有 P05/P06 与完整上下文；粉色为新增 AA。
- [本次人审](benchmarks/orthogonal-aa-polygons-v1/human-review-v1.json)：用户确认“P01-P06全部正确”。[已审状态模型](benchmarks/orthogonal-aa-polygons-v1/model-v1-reviewed.json)、[状态核查](benchmarks/orthogonal-aa-polygons-v1/review-verification-v1.json)保留原图、519 个对象几何/算法状态及延续语义；原 513 个对象/人审字段完全不变。精确尺寸、全幅覆盖和连接仍未验收；此次仅状态写入，不重复测试。
- P01–P04 是四个已审镜像台阶；P05/P06 是已审折线局部材料段，橙色截口表示向上/下继续到未建模 AA，不代表断开或独立 AA 岛。全部保留在同一全幅空间，未建模处为未知。新增对象不带 CT、器件或连接判断。
- 新增完整正交多边形表示及拟合，绘图、像素图、落点和分离检查读取凹轮廓而非外包框；保留缺口、凹角和折线间隙，拒绝自交、塌陷或自动接触。相对单位，未恢复真实工艺尺度或消除全图畸变。
- 从已审父模型接续，原有 513 个对象及人审字段完全不变，旧 AA 像素图逐像素一致。新样稿共有 41 个 AA 几何记录（含两个局部段），不是独立 AA 岛或器件数量。
- 正交多边形样稿阶段全项目 279 tests、相关 Ruff 与证据核查通过；此为历史阶段记录，最新全幅核查见上。
- [前版方向 v4](docs/architecture/photo-stack-workflow-v4.md)。此前 [AA/CT 样稿验收](docs/geometry-reconstruction-v2.md)、[首次人审](benchmarks/geometry-reconstruction-v1/human-review-v1.json)、[三环排列人审](benchmarks/geometry-reconstruction-v1/human-review-v2.json)、[已审父模型](benchmarks/geometry-reconstruction-v1/model-v2-reviewed.json)继续生效：35 个旧 AA 结构/dummy 排列、120 个 CT 存在/大致定位、三环整体排列合理且无明显遗漏。旧 79 个脚本疑点保留，不作为整体排列问题反复询问；精确尺寸、全图覆盖/配准和电气连接仍未验收。

- 用户已授权先抽取 AA 与 AA 上 CT。[方法、输出与限制](docs/full-frame-aa-ct-v1.md)、[全幅叠图切层页](runs/full-frame-aa-ct-v1b/index.html)、[冻结运行记录](benchmarks/full-frame-aa-ct-v1/result-v1.json)、[参数](benchmarks/full-frame-aa-ct-v1/spec-v1.json)。AA 原生、CT/poly 原生与候选投影分开；原图未改，画布 5712×4284，单位 px。
- AA 亮度支持与几何补全分开，中央独立 AA/外环回归检查通过；暗 AA 内部仍有漏提，不能声称完整精确复原。8767 个 CT 支持连通块中，1123 为 AA 内部候选、7168 为待核，均不是物理通孔计数；其余不据此判为 poly CT。
- 候选配准锚点覆盖不足，宏观叠图已看，不代表精确落点通过。原图有效区、未知状态、源哈希、变换和每支持块记录保留。未调用外部视觉模型，算法候选不是新增人工批准。
- 新增全幅模块及测试、CT 筛选性能改进；全项目 265 tests、相关 Ruff、输出哈希和静态 HTML 引用检查通过。浏览器交互未实测。当前新增材料输出及此前区域/架构工作均未提交；runs/ 为本地派生结果。

- [前版全幅方向 v3](docs/architecture/photo-stack-workflow-v3.md)：完整源图→完整材料图层→场景级器件与连通分析。M05 只是区域观察编号，不能切割图层或阻断网络；局部窗口只用于显示/抽样检查。
- [当前区域分类 v3](docs/region-planning-reviewed-v3.md)、[22 项区域记录](benchmarks/region-planning/eight-photo-regions-reviewed-v3.json)、[C03 人审原话](benchmarks/region-skill-validation-v1/C03-human-review-v1.json)、[已审 C03 切层页](docs/assets/region-skill-validation-reviewed-v2/index.html)。22 为区域条目数，不是器件数；未新增 MIM/MOM 子类型、精确边界、跨层配准、端口或网络批准。
- [区域 skill 验证与封装判断](docs/region-skill-validation-v1.md)、[C03 八层切换复核页](docs/assets/region-skill-validation-v1/index.html)、[冻结首次观察](benchmarks/region-skill-validation-v1/first-observation.json)。四帧核心窗口与旧区域框无交叠；仍是同 Agent/同照片开发试验，非盲测。
- [skill 项目源](skills/silicon-eye-region-planning/SKILL.md)已安装 `/home/zuoky/.codex/skills/silicon-eye-region-planning`，源与安装内容哈希一致；已在当前会话可用 skill 列表出现，可按路径读取；UI 选择器行为未实测。默认自动发现策略未禁用。
- 同一工具重放旧 21 项/58 窗口且未改批准；七项持久行为测试、Ruff、skill 格式校验通过。C03 首次 CAP 分类与用户确认一致，仍仅是同照片开发案例，无泛化准确率；自动浏览器 file: 预览被策略拒绝，未绕过，交互未实测。
- [已审区域图表 v2](docs/region-planning-reviewed-v2.md)、[八层切换已审页](docs/assets/region-planning-v2/review.html)、[原话裁决](benchmarks/region-planning/eight-photo-regions-human-review-v1.json)、[已审区域记录](benchmarks/region-planning/eight-photo-regions-reviewed-v2.json)。
- M01–M09、R01、C01/C02、I01–I03 分类正确。U01=宽 MOS 电容接法；U02=一横一竖两个独立衬底 MOS；U03/U04=dummy AA 与 dummy M1；U05=衬底环及上覆金属；U06=界面遮挡。U04 的 M1 原生定位待查，不覆盖 C02。
- 单页切换不同层次已作为后续复核界面需求保留；v1 旧页提供 v2 入口，历史候选页字节另存。区域分类批准不扩大到像素边界、全图配准、端口短接或器件总数。
- [区域图与区域表 v1](docs/region-planning-v1.md)、[八帧离线复核页](docs/assets/region-planning-v1/review.html)、[机读区域记录](benchmarks/region-planning/eight-photo-regions-v1.json)。21 个候选/未知区域、58 个各帧独立原生观察窗，区域数不是器件数；框外未分类。
- [PDK 回查参考](docs/reference/pdk-recognition-guide-v1.md)、[官方来源索引](benchmarks/pdk-reference/sources-v1.json)：已读 GF180/SKY130 相关章节，未安装/镜像完整 PDK，不确定时按问题查原章，不套用工艺参数。
- [图稿检查](docs/region-planning-v1-qa.md)：静态图及来源/坐标/引用检查完成；v1 分类现由 v2 人审接续，HTML 浏览器交互未另行自动验证。区域阶段文档、JSON/CSV、图稿、人审记录及新增 skill/helper/tests 均未提交；本轮材料模块变动见上。
- [原顶层设计 v2](docs/architecture/photo-stack-workflow-v2.md)保留历史；其局部分层路线已由 v3 接续。
- [八图初查与下一操作](docs/eight-photo-next-step-2026-10-18.md)、[逐图来源及设计样本](benchmarks/photo-stack/eight-photo-intake-v1.json)。
- 八图完整解码、RGB、5712×4284、字节数和哈希已建档；本轮结合全图总览及 AA/poly/M1 的宽局部图作区域候选判断，未做全图逐像素分类。
- CT/V1/V2 没有独立源图，需从相关照片提取为语义层；照片标签与材料层不可等同。
- 区域粗分类现已审；全图精细配准、材料掩膜、自动并网和器件总数仍未批准，U02 仅有明确的两个 MOS 局部数量。有效区与共同覆盖仍待建立。

## 数据及质量约定

- 原图不可变且可回查；后续正常计算使用重建版图，发现矛盾时修订局部，按依赖重算。
- 保留材料存在/不存在/未知三种状态，另存有效覆盖；native 坐标和公共参考变换分开。每对象有来源、状态、修订和稳定 ID。
- 10 px/μm、N/P、S/D、W/L、工艺规则均未确定。sub/implant 保留来源标签，不新增掺杂语义真值。
- 区域框、材料身份、精确几何、端口和连通分别验收。质量门按用途/区域判断，不以总 PASS 代替物理结论。
- 区域观察已封装交互 skill 与参数化出图工具；职责已收窄为整体理解/评测支线，不决定分层抽取范围。输入、分层复原、追线、器件端口、输出、三维、总控和质量复核等其他 skill 仍未实现。

## 既有已审事实与恢复入口

- [v33 最终复核稿](docs/roi2-gate-network-reviewed-v33.md)、[伴随拓扑](benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v33.json)、[覆盖记录](benchmarks/metal-extension/roi2-gate-network-coverage-v33.json)。
- Q1/Q2 相邻栅指，poly 局部不连，经 M1 共栅；中间扩散共享、体端共用，外侧扩散共接未知。原生窗口见[旧任务输入](benchmarks/agent-eval/roi2-seed-v1/input.json)，不是材料边界或统一坐标。
- 当前长 M2 入口保留；T→N04→J1/T/J2/J3/J4 五 M2/M1→CT→AA 已审；S1/S2→L01 右端短竖→左端 W/M2→W1/M1→CT→AA 已审。B→底部 M1 长横及绿色 M1/M2/M3 梳齿同电极，橙色对极隔离。
- 六处 AA 接入不是六器件；不穿 MOS 沟道/电容介质。照片外、未识别接口及 M3/M4 精确配准未知，未证明物理全网无遗漏。
- 旧 gate→A→P1 归属已撤回；保留历史物理子图。旧 E=V1、F/G 直接接 M1 已否决；旧 MOM P1/P2 裁决保留，不与新 B 电极自动合并。
- 通用 case v14 仍带历史错误入口，不能代替 v33。旧观察、编号和高亮工具保留，不冒充已实现整网追踪。
- [昨日走线协议](docs/metal-tracing-workflow-v1.md)待分层样稿可用后复用。开发过的同芯片数据只算回归，不算盲测。
- 证据恢复：`.venv/bin/python -m silicon_eye.evidence_archive --archive benchmarks/evidence/roi2-network-reviewed-v33.zip --root .`；旧九项示例输入用同目录 roi2-reviewed-inputs-v1.zip。不是全部 runs 历史。
- 统一包：`.venv/bin/silicon-eye annotate review-package --spec benchmarks/review-package-roi2-v1.json --root . -o 新目录`。浏览器预览曾被策略拒绝，不用 CDP 绕过；用静态图交付。
- 区域 skill 封装时全项目 255 tests、相关 Ruff、skill 格式检查通过；当前仅追加人审及派生页，不重复软件测试，不以脚本成功替代物理结论。

## 按需历史

- [全幅纠偏前完整入口](docs/history/current-task-before-2026-10-18-full-frame-correction.md)：保留原 M05 局部样稿方向供复盘，不作为当前任务。
- [方向调整前完整入口](docs/history/current-task-before-2026-10-18-layer-reconstruction.md)：保留昨日全部状态、裁决边界与恢复信息。
- [v33 整合前历史](docs/history/current-task-before-2026-10-17-v33-reviewed-network.md)：详细追踪依据及更早入口。
