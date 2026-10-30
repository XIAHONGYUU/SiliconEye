# Current-task archive

Source: CURRENT_TASK.md
Archived: 2026-10-29 before recording the Q1 decision and M2 A end review.

# 当前任务

## 当前目标、状态与授权

**R3／R4 向左的 AI 来源核查已推进到新 V1 候选 Q1，等待身份及 M2 承载裁决。** 已检查中央 BR-C、左侧回折、BU，并继续查到 BU 上方宽 M1 孔组。不是重审旧 P1–P5，也不是完成全网。

- [新复核页](docs/assets/R3-R4-left-continuation-v1/index.html) · [双层并排大图](docs/assets/R3-R4-left-continuation-v1/Q1-paired.png) · [当前状态](benchmarks/R3-R4-left-continuation-v1/source-review-state.json) · [报告](docs/reviews/2026-10-29-R3-R4-left-continuation.md) · [验证](benchmarks/R3-R4-left-continuation-v1/verification.json)。
- 几何仍从 [BR-R work-v3 next-request](benchmarks/BR-R-return-work-v3/next-request.json) 恢复，[五层工作页](docs/assets/BR-R-return-work-v3/work/index.html)不变。34 金属候选（M1=4／M2=8／M3=22），11 已审跨层接口，46 设计孔中心；画布 780×1440，旧坐标保持。
- 本轮只增加来源观察，未改工作模型／程序，未新增已审接口／网号。geometry_adopted=false、source_to_design_transform=null、net_edges=[]、complete_network=false。
- README/site/gh-pages 保护；仅本地开发，未提交／推送。main 起点 66a450a；2026-10-29 各阶段工作尚未提交。金属／VIA skill 仍 LIMITED_TRIAL_V2。

## 唯一待裁决与下一步

[R34-LEFT-Q1 请求](benchmarks/R3-R4-left-continuation-v1/review-request.json)：**M1 橙框 Q1 是否为 V1，并把 BU 向上的宽 M1 接到 M2 蓝框 A 的宽竖段？** 仅判身份／承载，孔数未知；M2 本身亮点另为上层接口／V2 候选，不作为 V1 身份证据。

- M1 孔组搜索框 [1990,2664,2042,2765]；M2 A 上下文 [1945,2520,2008,2800]。外方阵参照只用于宽段搜索，没有内部孔精度资格，不投影到工作几何。
- 新跨层事实会改变连接，脚本检查或宏观定位不能替代裁决。Q1 回复前不添加接口、不按已接通继续追踪 M2 A。
- 裁决后沿 M2 A 核查，再做来源绑定的联合候选修订及整组包围。BU 上方 M1 仍向北、向西出视图，不能当作物理端点。
- 不再问 P1–P5、BF24／25／26、原 A／B，不逐孔审批。新几何若超工作范围必须显式处理坐标和范围，不挤缩旧几何。

## 本次来源判断与检查

- R3 宽横条可向左追到中央 BR-C 及左竖返回；R4 底部宽横条左折向上至 BU。中央 BR-C 可见接 R3／BU，下端与 R4 本处留隙，不推导全局异网。这些是 AI 来源候选，非人审几何批准。
- 原生彩线不是规则 GDS；未新增设计变换。细邻线、其余短指、支路所有孔及完整网络未随本次核查批准。
- [观察](benchmarks/R3-R4-left-continuation-v1/source-observations.json)含来源哈希、路径、原生范围、开放出口及覆盖边界；[裁片记录](benchmarks/R3-R4-left-continuation-v1/source-panels.json)含放大／边距。
- 5 组无标记图照片区逐像素保持；检查来源／范围／资源／脚本及旧工作保持性，宽图与并排 PNG 目视。浏览器交互未实测。本轮无程序变更，不重跑此前 127 项测试。

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
# 唯一当前几何恢复入口；输出使用新目录。
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/BR-R-return-work-v3/next-request.json --output runs/新的BR-R接续目录
# 仅旧 M2/V2/M3 声明范围覆盖核对
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的覆盖核对目录
```

前入口全文完整归档于[本轮核查前](docs/history/current-task-before-2026-10-29-R3-R4-left.md)。其它 V1 从 benchmarks/v1-new-short-branch-reviewed-v2/next-request.json 恢复，旧中样从 benchmarks/m1-local-tab-v1/work-next.json 恢复。历史初稿在 runs/B-short-finger-initial-review-build-v2、runs/corridor-m1-v1-pre-resource-reuse-v2 保留，不作当前裁决。不得自动重建 README/site 或发布 gh-pages。
