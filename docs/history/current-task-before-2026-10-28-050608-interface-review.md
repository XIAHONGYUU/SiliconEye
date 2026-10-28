# 当前任务

## 当前状态与授权

**03／04局部联合修订完成，完整声明V2候选孔组包围通过；身份与承载无需重复审批。** 已承接用户人工判断03→T01、04→T02。只改C-M2-03和C-M2-04的相对设计路径；其他28金属（全部22条M3）、旧5接口和34孔记录完全保持。工作模型现30金属、7条已审承载接口、38设计候选孔。新尺寸/排列仍为候选，物理孔数/精确照片投影/真实PDK/全网不放行。README、site/、gh-pages保护，skill仍LIMITED_TRIAL_V2；当前工作未提交/推送。

[新旧联合图](docs/assets/upper-cap-joint-revision-v1/before-after-upper-bank.png) · [局部复核页](docs/assets/upper-cap-joint-revision-v1/index.html) · [走廊工作图/图层切换](docs/assets/upper-cap-joint-revision-v1/work/index.html) · [整组包围](benchmarks/upper-cap-joint-revision-v1/group-enclosure.json) · [最新来源状态](benchmarks/upper-cap-joint-revision-v1/source-review-state.json) · [验证](benchmarks/upper-cap-joint-revision-v1/verification.json) · [阶段报告](docs/reviews/2026-10-28-upper-cap-joint-revision.md) · [本轮前CURRENT_TASK完整原文](docs/history/current-task-before-2026-10-28-upper-cap-joint-revision.md)。

## 最新结果与边界

- 03设计路径改为[[185,10],[185,35],[211,35]]，保留向右横头，并留出25设计像素竖干，不将竖干压到5像素；04改为[[640,30],[640,54],[665,54]]，横向整体左移25设计像素，使短横头在T02持续走线范围内。原生锚点、短横头长度/宽10、稳定ID及源范围出口保持。新坐标是相对设计候选，不是测量结果。
- C03-V2完整候选包络[185,32,211,38]，每侧包围1后[184,31,212,39]；C04-V2为[640,51,665,57]，加包围后[639,50,666,58]。整个包络及每个显式孔均被两层金属包围；孔径6、最小间距3、每侧包围1，沿用相对设计预算而非真实PDK。
- 两组各用两孔作工作假设；相同占用包络的三孔备选也通过尺寸/间距/包围检查。不据此断言物理数量，不以单孔代理或挪到竖干凑PASS。来源孔组穷尽、精确孔心、工艺尺寸仍未知。
- 复用统一入口先做两条M2修订，再单独补两个接口。新增通用批量承载裁决适配，将已交付问题、身份裁决及用户原话绑定，防止重问或把承载批准扩大为孔数/几何批准；原始人审文件不改。
- 65项相关软件测试通过（新适配8、原workflow45、接口扩展12）；31项固定工程回归通过，非AI准确率。4张来源裁片逐像素一致；最新next-request回放完全一致；静态页面/JS、PNG目视及展示保护通过。浏览器交互未实测。
- [身份“均为V2”](benchmarks/upper-cap-03-04-reviewed-v2/human-review.json)、[承载原话“我个人判断03接T01,04接T02”](benchmarks/upper-cap-03-04-carrier-reviewed-v3/human-review.json)冻结保留。旧落点诊断已由本候选修订接续，不再是当前待处理失败。
- N1仍经V2接C-M3-L01，物理孔数null；其两候选中心(568,682)/(586,682)及完整包络[565,679,589,685]保持。05/06在图示局部没有直接连续M2，不合并ID、global_same_net=null。
- [30条清单覆盖核对](benchmarks/conductive-corridor-coverage-v1/coverage.json)仍为原清单范围，60端点/48来源范围出口保持；旧覆盖报告5接口是历史，本阶段为7。剩余C-M2-05/06/08尚无已确认接口，不意味着物理无孔。
- [三条M3弱带AI处置](benchmarks/m3-weak-band-review-v1/source-review-state.json)保持：不补建，非人审物理不存在。CU2拟提问已在提出前撤回，不复活为待答。

## 必须接续的裁决与未知

- 2026-10-26用户确认Q1/Q2均已解决：两处定性工作几何已验收，联合中样阶段收口，不再作为待裁决问题。具体像素/物理尺寸、未知路径及全幅坐标资格仍按下述范围保留；原连接批准不重审。
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

按走廊清单核查C-M2-05、C-M2-06、C-M2-08的其余可见接口：先从M2原生照片核V2身份及源范围，再匹配M3承载。不重问03/04、N1或05/06局部不连续；不从交叉/相似坐标自动造连接。

当前局部修订无需重跑或重复审批身份与承载。继续开发时从下列请求恢复，并读取本阶段source-review-state；新坐标仍为可调整候选，旧共同注册表不自动替换。

```bash
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/upper-cap-joint-revision-v1/next-request.json --output runs/新的走廊接续目录
```

其他V1分支从`benchmarks/v1-new-short-branch-reviewed-v2/next-request.json`恢复；旧联合中样从`benchmarks/m1-local-tab-v1/work-next.json`恢复。main最后推送243bf87，当前弱带/覆盖/03-04各阶段及本轮适配代码、测试、候选均未提交。origin=https://github.com/XIAHONGYUU/SiliconEye.git；本机目录及silicon-eye命令兼容名保留。
