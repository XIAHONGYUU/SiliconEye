# 当前任务

## 当前目标与授权

2026-10-18 用户批准调整顶层方向：先标准化输入和建立可修订分层版图，再以统一数据进行器件/网络分析及输出。已授权整理设计、调整计划并提交 Git；本轮不新增远端推送授权，不沿用昨日推送请求扩大本轮范围。

- 内层 silicon-eye 仓库、.venv；原图 data/ 不改，派生试验 runs/。仅用现有八图，没有额外照片，不要求补拍。
- 暂缓原定金属独立重走和 skill 封装；不声称已执行。无新增付费视觉服务、平台或生产 skill 实现。
- 最近已核验远端 main=5f78c9c1a63b07680ee0808a98468a23a963fe81；本轮 Git 提交以日志为准。

## 最新状态与唯一下一步

**下一步：以八图为样本生成整体区域规划图及区域表，分类 MOS 阵列、电容/电阻候选、主要互连和未知；随后选既有 Q1/Q2 局部做 AA/poly/CT/M1 分层复原样稿。** 不先恢复整网扩展，也不先创建 skill。

- [顶层设计 v2](docs/architecture/photo-stack-workflow-v2.md)：标准照片栈→区域规划→可修订分层版图→器件/端口与网络联合提取→多种输出。
- [八图初查与下一操作](docs/eight-photo-next-step-2026-10-18.md)、[逐图来源及设计样本](benchmarks/photo-stack/eight-photo-intake-v1.json)。
- 本轮已核对八图完整解码、RGB、5712×4284、字节数和哈希，并查看全图缩略总览；未逐区域全分辨率判读。
- CT/V1/V2 没有独立源图，需从相关照片提取为语义层；照片标签与材料层不可等同。
- 初查允许粗区域规划，不批准全图精细配准、材料掩膜、自动并网或器件计数。有效区与共同覆盖仍待建立。

## 数据及质量约定

- 原图不可变且可回查；后续正常计算使用重建版图，发现矛盾时修订局部，按依赖重算。
- 保留材料存在/不存在/未知三种状态，另存有效覆盖；native 坐标和公共参考变换分开。每对象有来源、状态、修订和稳定 ID。
- 10 px/μm、N/P、S/D、W/L、工艺规则均未确定。sub/implant 保留来源标签，不新增掺杂语义真值。
- 区域框、材料身份、精确几何、端口和连通分别验收。质量门按用途/区域判断，不以总 PASS 代替物理结论。
- skill 候选包含输入、规划、分层复原、追线、器件端口、输出、三维、总控和质量复核；尚未实现，不先建空壳。

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
- 5f78c9c 提交前 248 tests 及相关 Ruff 通过；本轮仅文档、源图清单与缩略图变动，不冒充本轮重测或物理真值。

## 按需历史

- [方向调整前完整入口](docs/history/current-task-before-2026-10-18-layer-reconstruction.md)：保留昨日全部状态、裁决边界与恢复信息。
- [v33 整合前历史](docs/history/current-task-before-2026-10-17-v33-reviewed-network.md)：详细追踪依据及更早入口。
