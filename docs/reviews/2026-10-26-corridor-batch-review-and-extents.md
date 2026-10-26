# 走廊新增几何复核与旧端部补齐

已将两项工作推进到统一人工验收节点：新增22段按四组完成AI来源复核，旧8个对象的可见范围补成端部候选；目前六组均为人工待定，没有把用户“先推进”的指令当作几何批准。

[打开R1–R6复核页](../assets/conductive-corridor-batch-review-v1/index.html) · [实际工作包](../assets/conductive-corridor-batch-review-v1/work/index.html) · [分组与问题](../../benchmarks/conductive-corridor-batch-review-v1/groups.json) · [范围证据](../../benchmarks/conductive-corridor-batch-review-v1/source-extent-evidence.json) · [验证](../../benchmarks/conductive-corridor-batch-review-v1/verification.json)。

| 组 | 内容 | AI处理结果／人工需看 |
|---|---|---|
| R1 | 新增M2五段 | 上沿两折角保留；修订左短段位置、左下竖段长度。看数量、相对位置和局部隔离；05/06图外连续性仍未知。 |
| R2 | M3上部六线 | 来源数量和次序一致，保留等宽、19设计像素节距；看排列及与宽母线的关系。 |
| R3 | M3中部六线 | 原21节距偏大，按同帧结构关系改为15，整体仍在中部宽母线上方；看紧凑排列是否贴合。 |
| R4 | M3其余五段 | E1/E2长度修订保留；最下沿线位置改回更合理的相对高度；看短段、可见端点和次序。 |
| R5 | 旧M2三线 | 三个下沿出界端部补候选；N1上端原设计偏上，修订到中部母线下方。只审几何，不审N1孔身份。 |
| R6 | 旧M3五线 | 五条横线左右范围补候选，十个端部继续标出界，不当真实线终点。 |

本轮18个对象的设计字段发生显式修订：旧8个对象及10个新增片段。**全部原生锚点、金属编号、四个已审V2接口、32个设计孔和孔中心不变。** 原几何包保留，没有把今天的修订倒写到原结果。

位置修订使用同帧结构与现有设计站点的相对关系。M2上／下孔组来源中点约1922/2715，对应当前设计站点184/865，仅用于AI选择纵向设计候选；没有输出或批准2D照片变换，也没有跨层用V1/V2中心配对。M3中部六线以UP/MID的位置关系约束，最下沿线保持在下部母线之后；这些仍须人工定性验收。

## 旧锚点与新范围分开保存

通过同一`conductive_workflow`的普通局部修订执行，不新增案例专用工具。样本绑定独立`source_extent_evidence`，逐对象保留原`native_path`，新增`visible_native_path`、端部状态及相应设计候选。八条旧金属共13个走廊出界端部被记账：M2下沿3个、M3左右10个。

七条旧金属的新多边形覆盖原材料；N1因为原上端位置错误，显式列为端点重定位，不能混称为纯外延。它是否含V2仍是C-U4未知。旧锚点路径仍较短是历史保留，不代表本轮忘记补候选；声明范围的候选已建立，精确来源边界资格仍未通过。

后续需要只改一个点时，可新建范围证据绑定当前父包，列明实际变化ID再修订；无需改原生锚点，也不会把范围记录锁成无法调整。既有记录不可静默丢弃。来源/设计不匹配、漏掉旧对象、把AI记录伪装成人工批准、纯外延却删去旧材料等会被拒绝。

```bash
# 复现本轮修订；不覆盖旧包
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/conductive-corridor-batch-review-v1/request.json --output runs/新的批量复核候选
# 接续最终候选，无重复修改
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/conductive-corridor-batch-review-v1/next-request.json --output runs/新的接续
```

## 验证与下一节点

74项专项测试、31项固定回归通过，共105项不同软件测试；不把重复试跑累加。专项含范围证据接续、后续单点修订、旧孔/批准保留、漏对象、错来源、缩掉原材料和伪造批准等检查。正交、间距、来源转折及次序、原设计孔组包围通过，实际接续完整模型相同。

复核页六组数据、22项页面/资产链接、SVG XML、JS语法、manifest及JSON模型绑定通过。已查看静态分层与联合几何图；实际浏览器交互未自动验证。页面复用原图裁片，无新增照片副本。

尚待用户按R1–R6集中裁决；本轮未批准任何新几何或连接。C-U1～C-U5均保留未知，M1/V1及更高层未纳入，物理穷尽、真实PDK、精确投影和全网仍未放行。不会因六组几何批准自动消除这五项未知。

README/site的25个文件及本地gh-pages引用保持，未提交或推送；金属/VIA skill仍为限定试用v2。旧实时入口完整归档到[历史文件](../history/current-task-before-2026-10-26-corridor-batch-review.md)。下一步仅接续六组人审，不重复审批四条旧接口。
