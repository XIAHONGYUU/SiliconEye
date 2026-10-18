# Archived CURRENT_TASK.md

Source: CURRENT_TASK.md; archived 2026-10-18 before full-frame extraction direction correction. Original bytes follow.

# 当前任务

## 当前目标与授权

2026-10-18 用户批准调整顶层方向：先标准化输入和建立可修订分层版图，再以统一数据进行器件/网络分析及输出。已授权整理设计、调整计划并提交 Git；本轮不新增远端推送授权，不沿用昨日推送请求扩大本轮范围。

- 内层 silicon-eye 仓库、.venv；原图 data/ 不改，派生试验 runs/。仅用现有八图，没有额外照片，不要求补拍。
- 暂缓原定金属独立重走和 skill 封装；不声称已执行。无新增付费视觉服务或平台；用户本轮授权选区验证后判断是否封装区域规划 skill，已按验证结果封装。
- 最近已核验远端 main=5f78c9c1a63b07680ee0808a98468a23a963fe81；本轮 Git 提交以日志为准。

## 最新状态与唯一下一步

**下一步：进入 M05 内 Q1/Q2 的 AA/poly/CT/M1 分层复原样稿，保留未知与有效区、逐层原生几何及必要局部对齐。** C03 金属电容类别已获用户确认，本轮区域类别复核闭合，不再询问。 旧 21 项不重问。区域规划 skill 已封装为交互式候选/复核流程，不恢复整网扩展或金属 skill 封装。

- [当前区域分类 v3](docs/region-planning-reviewed-v3.md)、[22 项区域记录](benchmarks/region-planning/eight-photo-regions-reviewed-v3.json)、[C03 人审原话](benchmarks/region-skill-validation-v1/C03-human-review-v1.json)、[已审 C03 切层页](docs/assets/region-skill-validation-reviewed-v2/index.html)。22 为区域条目数，不是器件数；未新增 MIM/MOM 子类型、精确边界、跨层配准、端口或网络批准。
- [区域 skill 验证与封装判断](docs/region-skill-validation-v1.md)、[C03 八层切换复核页](docs/assets/region-skill-validation-v1/index.html)、[冻结首次观察](benchmarks/region-skill-validation-v1/first-observation.json)。四帧核心窗口与旧区域框无交叠；仍是同 Agent/同照片开发试验，非盲测。
- [skill 项目源](skills/silicon-eye-region-planning/SKILL.md)已安装 `/home/zuoky/.codex/skills/silicon-eye-region-planning`，源与安装内容哈希一致；已在当前会话可用 skill 列表出现，可按路径读取；UI 选择器行为未实测。默认自动发现策略未禁用。
- 同一工具重放旧 21 项/58 窗口且未改批准；七项持久行为测试、Ruff、skill 格式校验通过。C03 首次 CAP 分类与用户确认一致，仍仅是同照片开发案例，无泛化准确率；自动浏览器 file: 预览被策略拒绝，未绕过，交互未实测。
- [已审区域图表 v2](docs/region-planning-reviewed-v2.md)、[八层切换已审页](docs/assets/region-planning-v2/review.html)、[原话裁决](benchmarks/region-planning/eight-photo-regions-human-review-v1.json)、[已审区域记录](benchmarks/region-planning/eight-photo-regions-reviewed-v2.json)。
- M01–M09、R01、C01/C02、I01–I03 分类正确。U01=宽 MOS 电容接法；U02=一横一竖两个独立衬底 MOS；U03/U04=dummy AA 与 dummy M1；U05=衬底环及上覆金属；U06=界面遮挡。U04 的 M1 原生定位待查，不覆盖 C02。
- 单页切换不同层次已作为后续复核界面需求保留；v1 旧页提供 v2 入口，历史候选页字节另存。区域分类批准不扩大到像素边界、全图配准、端口短接或器件总数。
- [区域图与区域表 v1](docs/region-planning-v1.md)、[八帧离线复核页](docs/assets/region-planning-v1/review.html)、[机读区域记录](benchmarks/region-planning/eight-photo-regions-v1.json)。21 个候选/未知区域、58 个各帧独立原生观察窗，区域数不是器件数；框外未分类。
- [PDK 回查参考](docs/reference/pdk-recognition-guide-v1.md)、[官方来源索引](benchmarks/pdk-reference/sources-v1.json)：已读 GF180/SKY130 相关章节，未安装/镜像完整 PDK，不确定时按问题查原章，不套用工艺参数。
- [图稿检查](docs/region-planning-v1-qa.md)：静态图及来源/坐标/引用检查完成；v1 分类现由 v2 人审接续，HTML 浏览器交互未另行自动验证。当前文档、JSON/CSV、图稿、人审记录及新增 skill/helper/tests 均未提交；原有生产模块未改。
- [顶层设计 v2](docs/architecture/photo-stack-workflow-v2.md)：标准照片栈→区域规划→可修订分层版图→器件/端口与网络联合提取→多种输出。
- [八图初查与下一操作](docs/eight-photo-next-step-2026-10-18.md)、[逐图来源及设计样本](benchmarks/photo-stack/eight-photo-intake-v1.json)。
- 八图完整解码、RGB、5712×4284、字节数和哈希已建档；本轮结合全图总览及 AA/poly/M1 的宽局部图作区域候选判断，未做全图逐像素分类。
- CT/V1/V2 没有独立源图，需从相关照片提取为语义层；照片标签与材料层不可等同。
- 区域粗分类现已审；全图精细配准、材料掩膜、自动并网和器件总数仍未批准，U02 仅有明确的两个 MOS 局部数量。有效区与共同覆盖仍待建立。

## 数据及质量约定

- 原图不可变且可回查；后续正常计算使用重建版图，发现矛盾时修订局部，按依赖重算。
- 保留材料存在/不存在/未知三种状态，另存有效覆盖；native 坐标和公共参考变换分开。每对象有来源、状态、修订和稳定 ID。
- 10 px/μm、N/P、S/D、W/L、工艺规则均未确定。sub/implant 保留来源标签，不新增掺杂语义真值。
- 区域框、材料身份、精确几何、端口和连通分别验收。质量门按用途/区域判断，不以总 PASS 代替物理结论。
- 区域规划已封装交互 skill 与参数化出图工具；输入、分层复原、追线、器件端口、输出、三维、总控和质量复核等其他 skill 仍未实现。

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

- [方向调整前完整入口](docs/history/current-task-before-2026-10-18-layer-reconstruction.md)：保留昨日全部状态、裁决边界与恢复信息。
- [v33 整合前历史](docs/history/current-task-before-2026-10-17-v33-reviewed-network.md)：详细追踪依据及更早入口。
