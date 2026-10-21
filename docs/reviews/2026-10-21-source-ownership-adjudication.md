# S1／S2通过与S3端子身份纠正

2026-10-21。用户裁决原文：

> S1：三身份以及相对位置合理
>
> S2：S2修改合理
>
> S3：紫色为源漏端，蓝色为该mos与右侧mos poly合并并向上打的CT

**S1、S2按显示范围通过；S3前一版将蓝色误登记为AA4左源漏CT，已按裁决纠正为相邻两管共用上端POLY的栅CT。** [新版复核页](../assets/ct-source-ownership-reviewed-v2/index.html)保留原生照片、层切换和规则联合图。原v1页面及冻结包保留历史，不继续作为S3材料身份结论。

## 实际修改

- S1、S2的72条来源修订与其他记录不动。批准限定为三列身份／相对位置和显示的S2修订，不扩展成全幅逐孔或精确边界批准。
- 紫色`CTSD-CTT-RECOVER-AA2-LEFT-GUARD-NETWORK-LOWER-LEFT-CELLS-ROW4-AA3-0-SD01-S000`记录完整保留，确认源漏身份。
- 退休误归属的`CTR-REM-AA2-LEFT-GUARD-NETWORK-LOWER-LEFT-CELLS-ROW4-AA4-0-SD00-000`，保存完整旧记录及全部来源历史；不复用带SD含义的旧编号。
- 蓝色原生观察`[1175,3727]`保持，以`CT-G66-P03-P04-SHARED-TOP-01`登记为POLY栅端CT。新设计位置调整到共用上端POLY，原AA4源漏位置不再保留这条孔。已有POLY CT位于不同的原生亮点，没有重复新增同一孔。
- 按原生图局部索引，对应两栅为`G66-P03`／`G66-P04`；原栅指及AA几何保持，新增`G66-P03-P04-TOP-BUS`表达共用上端POLY。两指实际相交的桥、CT包围、对AA避让均通过。精确桥外框和新设计孔位置是AI规则几何候选，未将用户的身份裁决扩大为新轮廓逐像素批准；native_outline只用于上下文定位。
- AA4左侧是否另有源漏CT没有可靠独立观察。本处新增范围化未知`S3-AA4-LEFT-SD-ACCESS`，不借用共栅CT、不因撤销误报就补孔或断言物理无孔。原5处来源限制保留，当前共6处限制，无需现在新增人工问题。

当前AA334／POLY696／CT10287。POLY多出的1项是桥材料对象，不是多出一个MOS。10286条CT记录与父版本完全相同，全部原AA和695个原POLY记录也相同。未作新M1／netlist推断。

## 把人审结论落实为约束

前一版来源争用归零、几何PASS，并不能证明蓝色属于源漏。该结果是一次明确的**AI材料／端子归属错误**，不能归因于程序已经证明照片正确。

当前材料模型新增`reviewed_contact_constraints`，由`joint_layers.reviewed_contact_errors`消费，分别检查：

1. 蓝色必须为指定共用POLY上的CT，旧AA源漏身份记录不得复活。
2. 指定共用POLY仍包含P03／P04，现有POLY门继续检查桥必须实际连到两个成员。
3. 紫色仍为原AA扩散目标的CT。

身份检查与几何检查分开报告。回归将旧AA记录放回，CT单层几何依然PASS；新的联合门因人审身份约束而FAIL。删除共栅成员也会被拒绝。今后有新证据改变身份时，必须明确修订裁决约束，不通过改轮廓绕过。

## 可回查产物与验证

- [当前共同快照v3](../../configs/joint-work-layer-v3.json)
- [本轮人工裁决](../../benchmarks/ct-source-ownership-reviewed-v2/human-review-v1.json)
- [精确before／after事务](../../benchmarks/ct-source-ownership-reviewed-v2/spec-v1.json)
- [退休记录](../../benchmarks/ct-source-ownership-reviewed-v2/retired-records-v1.json)
- [全幅联合门](../../benchmarks/ct-source-ownership-reviewed-v2/joint-report-v1.json)
- [端子访问盘点](../../benchmarks/ct-source-ownership-reviewed-v2/terminal-access-v1.json)
- [变化台账](../../benchmarks/ct-source-ownership-reviewed-v2/ledger-v1.json)

58项相关测试通过，102.38秒；相关Ruff通过。测试覆盖S1／S2及无关对象保护、S3事务重放、共栅访问、旧错误身份复活拒绝、共享成员丢失拒绝，以及此前的联合质量门反例。全幅几何、来源、人审身份门均PASS，不等于物理全孔恢复或真实PDK DRC/LVS；`automatic_network_export_allowed=false`。

原图、父配置和冻结包未改。本轮是已授权局部修订，尚未提交／推送GitHub。页面图稿已直接检查，JS语法／本地资源可达性已检查；未再次尝试被浏览器策略禁止的file协议自动访问。

下一步可用这次“人审推翻AI身份、依赖层修订、约束防退化”的真实事务验证统一交付包，再封装POLY／CT skill。无需重新验S1／S2，也不应将已撤销的蓝色源漏判断带入后续金属追踪。
