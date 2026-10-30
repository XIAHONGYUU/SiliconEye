# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-30 before finalized N integration and west F1 gate.

# 当前任务

## 当前目标与状态

**Q1／U／D 已审并接续到规则工作几何；已继续向北查到新的 N 孔组，待 V1 身份及 M2 A 承载裁决。** 不重问 Q1、U、D。原14条工作连接均已审，新 N 尚未建为接口。

- [当前复核入口](docs/assets/left-bu-joint-work-v3/index.html) · [五层开关／原图](docs/assets/left-bu-joint-work-v3/S5-north/index.html) · [当前规则几何](docs/assets/left-bu-joint-work-v3/joint-work.png) · [N 两层大图](docs/assets/left-bu-joint-work-v3/N-paired.png)。
- 唯一几何恢复：[next-request](benchmarks/left-bu-joint-work-v3/next-request.json)；[状态](benchmarks/left-bu-joint-work-v3/source-review-state.json)、[报告](docs/reviews/2026-10-29-left-bu-joint-work.md)、[验证](benchmarks/left-bu-joint-work-v3/verification.json)。
- 当前35金属候选（M1=4／M2=9／M3=22），14已审局部接口（V1=3组／V2=11组），80显式设计候选孔。原11接口记录、46孔中心、原骨架／源锚点、旧局部块保持；新孔数及精密几何均未获人审。
- [Q1 原话](benchmarks/left-bu-v1-reviewed-v2/human-review.json)“Q1：是 V1，接 A”；[U/D 原话](benchmarks/left-bu-joint-work-v3/human-review.json)“U：是 V2，接 B-U”“D：是 V2，接 B-D”。规范化适配器标记 actor=AI，实际 human_review 指向原人审文件，不伪造新几何被审。
- README/site/gh-pages 保持；main 起点66a450a，2026-10-29各阶段本地工作尚未提交／推送。金属/VIA skill仍LIMITED_TRIAL_V2；geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。

## 唯一待裁决与下一步

[N 原始请求](benchmarks/left-bu-joint-work-v3/north-review-request.json)：**M1 上方橙框 N 的孔组是否为 V1，并接同一条宽竖向 M2 A？** M1 原生搜索框 [1955,1930,2025,2002]；[N 来源观察](benchmarks/left-bu-joint-work-v3/north-interface-observation.json)保留来源、北向连续部分及已审参照。

- M2 顶端 U 是已审 V2，不是 N 的 V1 证据；无需在 M2 照片上看见 V1，不要求 N 与 U 逐孔重合。孔数未知。
- 北向 M1 已补为候选；N 的孔未加入模型。N 回复前不当作新接口扩网。裁决后再补其来源绑定的完整候选孔组及包围，继续核查上方／横向可见出口。
- 新问题只涉及 N，不重问 Q1／U／D、原 A/B、P1–P5、BF24/25/26。其余支路、全部 VIA 与完整网仍未收口。

## 五阶段接续与质量

- [事务清单](benchmarks/left-bu-joint-work-v3/transaction-log.json)：S1只左扩显示范围；S2只补 C-M1-SPINE、RT-M3-UP/MID/DOWN 局部块及来源；S3单独添加 M2 A 及清单；S4单独增加三组已审接口／完整候选阵列；S5补北向 M1，保留 N 未知。
- 显示范围 [0,0,780,1440]→[-1500,0,780,1440]，画布尺寸2280×1440；负 x 扩展的是设计视口，坐标原点仍[0,0]，旧对象没有平移／缩放。事务后及恢复重放再次比对旧对象和46孔中心。
- 新 Q1 5×2、U 3×3、D 5×3 为 AI 阵列候选，新增34孔；14组完整设计阵列逐孔包围／孔间距检查通过，物理数量、来源精密尺寸和PDK DRC仍未确认。V1/V2层间XY可重叠，不强迫逐孔同心。
- 原始照片、父包、旧人审不覆盖；[局部来源台账](benchmarks/left-bu-joint-work-v3/north-local-part-ledger.json)逐块绑定原生范围。中部 M3 只是交叉，邻近小孔列属于独立 M2，不建立新连接。
- 左扩事务拒绝平移／缩放／夹带几何／未声明改范围；来源适配器拒绝越过原问题的身份／承载／数量／照片或U/D串用。162项独立测试通过；Ruff及差异格式检查，原图裁片／资源／SVG／PNG检查见验证。浏览器交互未实测。冻结的[本轮程序源](benchmarks/left-bu-joint-work-v3/producer-sources.json)用于回查。
- 本轮前入口全文完整归档：[2026-10-29 joint 前](docs/history/current-task-before-2026-10-29-left-bu-joint.md)。以下旧事实／未知仍有效；旧包中的11接口/46孔数字仅属于该历史范围。

## 必须接续的裁决与未知

- P1 上接 BU，P2/P3 的 L1/L2 本处不接 BR-R，P4/P5 接 R3/R4。只判局部，不推导异网。BF24/BF26 本处上接 BU；BF25 本处不接 BU/L1/L2，仍独立候选而非已确定悬空节点。BF24/26 下端、其余 23 指和细邻线仍未知。
- A/B 的 V1 身份及接 RT-M2-R01 已审；原生框 A=[3125,1930,3175,2010]、B=[3130,2775,3180,2845]，2×1 仍为设计假设。R02 其它 V1 未查清，不声明无孔。
- 原 9 个 V2：R01/R02 上端接 RT-M3-UP、下端接 RT-M3-DOWN；N1→C-M3-L01、03→T01、04→T02、05→E1、06→E2。05/06 本处 M2 不连续，不推导全局异网。08 无明确 V2、三条弱 M3 不补建是 AI 处置，非人审不存在。
- C06 原生框 [2933,2140,2977,2175] 跨旧走廊 x2940；保持原框／裁决。旧 M2/V2/M3 覆盖仅限旧声明范围，不升级五层穷尽覆盖。
- BR-R work-v3：S1 只下扩 200px，S2 只加原 M1 的 BRR-DOWN/R3/R4 局部块，S3 另加 L1/L2；原骨架／宽度／四块及旧对象、11 接口、46 孔保持。详见[前入口全文](docs/history/current-task-before-2026-10-29-R3-R4-left.md)。
- A 右支约原生 x5175 下拐；B 左支与 R3/R4 左端原先均为出界而非物理终点。旧骨架 B 近似 y2800 与横带约 y2780 的差别不能用于移动孔；BF25、细邻条与完整返回仍未知。
- 外方阵宏观搜索不等于内部 VIA 精度；ORB 保留点 P95 约129px及首版触带已拒绝。旧九对 V1/V2 同孔拟合和 4.52px 残差不可复活；V1 从 M1 侧、V2 从 M2 侧判断。
- 其它区域 A={T3,L2}/B={T1,L4}、H1/H2 局部隔离、U1/U2 同 M1、U1/U3 经 V1 接 N2、U3 CT→AA 环端子路径按历史保持，不转移到本走廊。
- [材料快照 v5](configs/joint-work-layer-v5.json)为 AA334/POLY696/CT10287；规范导体注册表仍[原33记录](docs/assets/conductive-stack-v2/model.json)。AA-F01951/1952、材料 H1/H2、边界 AA-F01744、S3-AA4-LEFT-SD-ACCESS 六处材料未知保持。物理工艺／尺度／孔数／极性／WL／阻值未知，自动网络导出禁止。

## 恢复

```bash
# 当前唯一几何接续入口；输出用新目录，勿恢复到旧 work-v3。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/left-bu-joint-work-v3/next-request.json --output runs/新的左侧接续目录
# 仍仅旧 M2/V2/M3 声明范围，不能作为左扩五层覆盖率
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的旧范围覆盖核对
```

其它 V1 从 benchmarks/v1-new-short-branch-reviewed-v2/next-request.json 恢复，旧中样从 benchmarks/m1-local-tab-v1/work-next.json 恢复；均不能替代本走廊入口。历史初稿在 runs/B-short-finger-initial-review-build-v2、runs/corridor-m1-v1-pre-resource-reuse-v2 保留。不得自动重建README/site或发布gh-pages。
