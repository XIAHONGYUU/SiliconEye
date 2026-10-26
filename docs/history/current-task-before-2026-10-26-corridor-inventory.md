# 当前任务完整归档

来源：CURRENT_TASK.md；归档日期：2026-10-26；原文 SHA256：93ed15077a4f79b83eb90b313860cde628cc469fc0a693035897d95bdd89f4fd。正文原样保留。

---

# 当前任务

## 当前状态与授权

**固定回归集与金属／VIA skill限定能力已整理。** 本轮3项身份／承载任务、5条接口均已审，无新增裁决。本机整理与验证；README、site/、gh-pages冻结，不推送、不采用全层几何或全网。两个skill仍为LIMITED_TRIAL_V2，不因回归通过自动升级。

[能力范围与验收标准](docs/architecture/conductive-skill-qualification-v1.md) · [固定suite](benchmarks/conductive-regression-v1/suite.json) · [本轮验证](benchmarks/conductive-regression-v1/verification.json) · [整理报告](docs/reviews/2026-10-26-conductive-regression-scope.md) · [上轮完整入口归档](docs/history/current-task-before-2026-10-26-regression-scope.md)。

## 固定集与接续范围

- 三项原图任务为V1-S1、V2-R1、V2-R2，五条接口；原图输入包与人审答案分开。新增工程命令回放两个已审包及旧联合快照，并运行既有31项软件测试；不执行AI识别，不产生新的模型准确率。
- V1-S1接A下端已审，仍为数量null、完整孔组包围NOT_EVALUATED的支持代理；V2四组的32个设计孔未获人工数量／精确尺寸批准。未知不得因接续变成事实。
- 三项同芯片历史开发任务，非盲测；外部身份／承载纠正0仅限本批。R2送审前4×2漏排改5×2的内部修订保留，程序不能自动发现整排未声明。
- 已审局部工作几何和接口按原范围收口，不再重审Q1/Q2、V1-S1或V2-R1/R2。未来修改模型／观察策略需按能力文档另跑原图任务，先冻结观察再评分。
- 能力限于来源辅助的M1/M2/M3与V1/V2局部候选、受限修订、审批／未知接续；全幅可见清单、精确照片投影、真实尺度／PDK、陌生芯片、全网尚未合格。尚未提交／推送。

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

对既有R1–R2两条长M2之间的连续走廊先建立全部可见导体、接口及图外端部清单，再核中部交叉、端部和邻线是否遗漏。按候选／明确未知逐项覆盖，只对影响新身份／承载的歧义送审；不再增加互不相连的零散小样，也不把旧批准当全图分母。本轮只整理回归与能力范围，未开始该扩展。

```bash
.venv/bin/python scripts/check_conductive_regression.py --output runs/新的回归目录/result.json
```

已审V1从`benchmarks/v1-new-short-branch-reviewed-v2/next-request.json`恢复；V2从`benchmarks/metal-representative-transfer-reviewed-v2/next-request.json`恢复；旧联合中样从`benchmarks/m1-local-tab-v1/work-next.json`恢复并读相应收口裁决。当前Git基线fcc531a；origin为https://github.com/XIAHONGYUU/SiliconEye.git；本机silicon-eye目录/命令兼容名保留。
