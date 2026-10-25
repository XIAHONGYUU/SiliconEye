# 当前任务

## 当前目标与授权

用户已批准将GitHub仓库及展示品牌统一为SiliconEye。本轮基线c179e64；更新现有仓库名称、主页链接、本机origin、README/简历/展示页，并核对Pages与远端身份。仅名称与入口迁移，保留原始照片、模型、历史审批及CI权限阻塞状态。本机目录、Python包与silicon-eye命令保持兼容。

[展示主页](site/index.html) · [在线Demo](https://xiahongyuu.github.io/SiliconEye/) · [开发指南](DEVELOPMENT.md) · [案例与证据](docs/portfolio/cases.md) · [首轮整理报告](docs/reviews/2026-10-25-portfolio.md) · [质量优化报告](docs/reviews/2026-10-25-quality-portfolio.md)。

## 本轮质量优化

- 已加入六孔承载纠错案例、历史结果卡和8任务目录：2个现有机器评分任务、6个人工rubric。20条部分参考中16条已知、4条未解决；没有新模型预测或独立留出成绩。
- 历史证据20文件、构建来源42文件与公开资产18项均校验；相关37项不同测试通过，CI对应13项在本机稀疏环境通过。来源/原模型不变。
- [本轮验证](benchmarks/portfolio-quality-v1/verification.json)、[评测协议](benchmarks/portfolio-quality-v1/README.md)和[发布回执](benchmarks/portfolio-quality-v1/publication.json)保存口径与实际状态；公开页面约1.17MB。原开发裁决不因展示或CI通过改变。
- [优化前入口完整归档](docs/history/current-task-before-2026-10-25-quality-portfolio.md)保留53a1dcf时原文、字节数与SHA。

## 首轮展示与整理结果

- 开发基线提交`fa3e1c7`；本地恢复分支`archive/pre-portfolio-20261025`保持该提交。原README完整保存在[历史原文](docs/history/2026-10-25-before-portfolio-README.md)。
- 展示直接读取已有共同层、器件包和五层候选，不重跑识别、不改原图或人工结论。[来源与哈希](site/provenance.json)绑定源基线；[构建配置](configs/portfolio.json)集中管理选样。
- 交互包括AA/POLY/CT切层、R2_Q1/R2_Q2编号与端子联动、M1/V1/M2/V2/M3切层及孔组放大。器件框是检查范围，AA未逐器件定位；A/B不强行指定源漏。展示数据冻结，无在线AI调用。
- 原图、材料身份、已审连接及候选几何分别表达；不宣称完整GDS、全芯片自动提取、真实工艺DRC/LVS或仿真就绪网表。
- 首批328个未引用/未跟踪运行目录归档到仓库外`../silicon-eye-archives/2026-10-25`。5,578,336,614字节内容去重存为2,701,324,395字节，节省2,877,012,219字节；活动工作区约15.2GB→9.4GB。Git普通打包约再节省0.20GB，无历史重写。
- 逐文件SHA校验完成，恢复抽检通过；依赖闭包审计无缺失。归档后的导体重放model/report与冻结结果完全一致。已跟踪证据与被引用运行目录不清理。
- 本轮相关测试24项通过，包含归档工具7项；桌面1440×1000、手机390×844实际浏览器交互检查通过。[检查记录](benchmarks/portfolio-v1/browser-verification.json)及[汇总](benchmarks/portfolio-v1/verification.json)不代表照片识别准确率。
- 展示内容提交`8bf2833`，Pages提交`e4115de`；[发布回执](benchmarks/portfolio-v1/publication.json)保存实际远端构建、文件哈希及仓库信息。后续回执提交不更改展示内容。

## 恢复与接续

```bash
.venv/bin/python scripts/workspace_archive.py verify --archive ../silicon-eye-archives/2026-10-25
.venv/bin/python scripts/workspace_archive.py restore --archive ../silicon-eye-archives/2026-10-25 --run 需要恢复的目录名
.venv/bin/python scripts/build_portfolio.py
```

开发入口原文已完整归档到[展示整理前CURRENT_TASK](docs/history/current-task-before-2026-10-25-portfolio.md)，含字节数和SHA；以下仍生效事实必须接续，不能因展示整理撤销。

## 原开发任务的事实与未决项

[最新金属复核入口](docs/assets/stacked-via-review-v2/index.html) · [连续五层](docs/assets/stacked-via-review-v2/review/index.html) · [独立样本](docs/assets/stacked-via-review-v2/independent/index.html) · [金属修订报告](docs/reviews/2026-10-25-stacked-via-correction.md)。

- 用户已认可Q1的V1范围基本合适，并指出V1/V2投影应重叠；Q2六个V2占满M2并可与V1重叠。新偏移量、孔径/间距、Q2的3×2排列及金属精确边界仍为候选；原连接批准不重审。共同几何与全网尚未放行。
- 中样22条金属、9代理组及两组显式阵列仅覆盖已审清单38条中的11条，非照片覆盖率；独立样本6条金属及两组显式阵列。新局部候选不替换原共同注册表。
- A={T3,L2}、B={T1,L4}，分别经M2/M3接A、B；旧L3不复活。具体返回M2、M3-X/Y及逐孔路径未知。MID-H1/H2本处与U1/U2隔离，不推导全局异网；H1→V1→M2-A、H2→V1→M2-B已审。
- U1/U2同一M1；U1/U3有V1、U2无V1，两处均接N2。U1设计右端1310，原生1945<P08左竖2006的次序保持，不补跨H1/H2竖线。N2上接B1、下经D1接L1，F01–F12等已审承载保持。
- U3宽M1→所圈CT行→对应AA环仅该路径terminal_closed=true，体端/极性、孔数、边界及规范材料ID映射未知。13主分支不等于下层覆盖完成，P0/P5等原范围按归档保留。
- 孔身份策略为M1照片侧V1、M2照片侧V2。J组3×4=12个V2已审；旧九对V1/V2同孔拟合及4.52px残差已撤回，不作配准证据。
- 独立Q1六孔经V1接宽IT1-M2-B，原窄A错误；Q2为M2-B经V2接M3-BUS。A/B同层是否连续未知，亦不同于MID分组。历史ID后缀不决定承载。
- 唯一共同快照[configs/joint-work-layer-v5.json](configs/joint-work-layer-v5.json)：AA334/POLY696/CT10287；八张5712×4284照片和哈希保持。导体注册表仍为[原33记录模型](docs/assets/conductive-stack-v2/model.json)。
- 六处材料未知仍为AA-F01951、AA-F01952、材料H1/H2、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS。V3主体截段历史例外、S1/S2/S3身份、G66上桥、R1/R2、四栅33孔、18电阻、W01与195保留对象按原范围继承，详见完整归档。
- net_edges空、automatic_network_export_allowed=false、complete_network=false；真实尺度/工艺/极性/WL/阻值和完整网表未知。金属与孔skill仍为限定试用v2，未正式通用放行；材料skill资格不变。

## 唯一下一步

待用户补齐GitHub凭证的workflow范围后，将已备好的CI配置放回.github/workflows/portfolio.yml，推送并核对真实运行。用户可在本机执行`gh auth refresh -h github.com -s workflow`完成授权；不使用本机通过代替在线结果。展示主体已完成，不重复发布。

原开发待接续项仍为**V1/V2重叠关系与Q2整组占用比例的局部复核**；不重问已审连接，不因展示或测试通过批准具体几何，不扩全图或重做材料层。

重放入口：
```bash
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/stacked-via-review-v2/review-request-v1.json --output runs/新的局部复核目录
```

命令读取已有AI观察，不自动识别照片。独立样本用同目录independent-request-v1.json；旧trial/main仅历史/负例。人审更正须绑定实际旧送审包，事务不得静默改变原生锚点、快照、预算或审批范围。
