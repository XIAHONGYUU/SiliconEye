# 当前任务入口归档

来源：CURRENT_TASK.md；归档日期：2026-10-21。以下原文完整保留，原文SHA256：871992e1854d18c926ad7a6a52fad3c46d02d8dcb20d7cf490423850044882be。

---

# 当前任务

## 最新用户裁决与执行结果

2026-10-21用户确认S1三列身份／相对位置合理、S2修订合理，并纠正S3：紫色为源漏端，蓝色是该MOS与右侧MOS的POLY合并后向上引出的CT。S1／S2已按显示范围记录通过；S3前版AI把蓝色登记为AA4左源漏的判断已撤销，不能继续沿用。

已实施局部修订并验证：原紫色记录完整保留；错误AA源漏CT编号退休，以新编号登记蓝色共用POLY栅CT；新增G66-P03／P04上端桥，原AA和两栅几何保留。全幅几何、来源及人审身份约束均PASS；58项相关测试通过（102.38s），相关Ruff通过。新桥／孔精确轮廓仍是AI规则几何候选，不扩大人工批准。

本文件为唯一实时入口。[当前共同快照v3](configs/joint-work-layer-v3.json)、[新版复核页](docs/assets/ct-source-ownership-reviewed-v2/index.html)、[裁决实施报告](docs/reviews/2026-10-21-source-ownership-adjudication.md)、[机器核验](benchmarks/ct-source-ownership-reviewed-v2/verification-v1.json)、[全幅联合门](benchmarks/ct-source-ownership-reviewed-v2/joint-report-v1.json)。[本阶段前入口完整原文](docs/history/current-task-before-2026-10-21-source-identity-adjudication.md)及此前归档保留原过程。本机代码与产物尚未提交／推送，远端仍为已核对的6e5bb17。

## 当前有效工作层与质量门

- AA334／POLY696／CT10287。POLY新增1项是桥材料，不是新MOS。10286条CT记录与父v2相同，全部334 AA及695个原POLY记录相同。
- S1／S2的72条来源修订不动；批准为列身份／相对位置及显示修订，不扩为全层逐孔／精确边界批准。原16对来源争用仍为0，新争用0。
- 紫色源漏CT保留在ROW4-AA3目标。蓝色新ID为CT-G66-P03-P04-SHARED-TOP-01，目标为G66-P03-P04-TOP-BUS；原误归属的ROW4-AA4-SD00记录退休，旧观察与历史完整存档。G66-P03／P04映射依据局部原生图索引；共用上端POLY身份由用户确认。
- `reviewed_contact_constraints`被联合门消费：拒绝旧AA身份复活、蓝色改回AA、共用成员丢失和紫色目标改变。反例中旧错误记录的CT几何仍PASS，但身份门FAIL；几何与来源无争用不等于材料身份正确。
- 共同快照保留原8图哈希、设计画布5860×4587、原生照片5712×4284、相对预算、既有人审和限制。退休别名、G68合法桥、G26阶梯AA局部截面、AA适配与局部变化域保护继续生效。历史AA337／POLY700不得覆盖当前结果。
- AA已有仓库人机协作skill；POLY／CT专用skill、完整统一交付及独立Agent留出评测尚待完成。软件测试不替代物理事实或Agent判断评测。

## 保留未知与使用边界

原5处来源限制继续保留：AA-F01951、AA-F01952、H1、H2、边界AA-F01744；V3两主体截段的历史端子例外另列。本次撤销AA4左源漏误报后，新增局部未知S3-AA4-LEFT-SD-ACCESS：是否另有源漏CT没有独立证据，不借用蓝色栅CT，不补孔或断言无孔。当前共6处限制，无需现在新增人工问题。

原工程收口及既有范围化批准保留，不升级为100%物理CT恢复、整层像素批准、M1连接或网表。`automatic_network_export_allowed=false`；物理尺度、工艺、极性、真实W/L及阻值仍未知，无真实PDK DRC/LVS。

## 继续生效的用户裁决与保护范围

- 四栅G06R-P01～P04及33条CT、R1A／R1B上端、均匀源漏孔、R2本处连续AA单排孔和旧Q1／Q2／Q3继续生效；其他近邻环隔离／非AA间隙不变。父记录在历史冻结包保存，不把原父CT条数当成当前每条均不可纠错。
- C/D/F、143橙框、RIGHT6、宽MOS／环／电阻、Q2栅60孔、上方40栅、左侧局部、原661环孔及B孔数精度意见按原范围保留。R2_Q1、V3历史端子、网络v33、S03-03/04、18条电阻、W01电阻身份、195保留对象不改。
- 原照片和全部父冻结包不改，不启动新M1／net，不重跑全幅提取。旧v2来源修订及其报告保留历史，其S3蓝色源漏解释已由本轮裁决覆盖。

## 唯一下一步与恢复

用本次“人审推翻AI身份→局部POLY／CT修订→联合身份门防退化”的事务验证统一交付入口，再推进POLY／CT skill及少量留出任务评测。不重验S1／S2，不把退休源漏身份带入后续追网。

- 当前联合检查：`.venv/bin/python -m silicon_eye.joint_layers --snapshot configs/joint-work-layer-v3.json --output runs/新的联合检查目录`。
- 局部spec添加带哈希joint_snapshot；当前AA工具只细化已有对象，身份／分合变化需显式before／after事务并同步跨层引用。多观察合并AA须先建立局部对应，不能套用单一旧投影。
- 新候选清单可重载，但继承阶段／use-contract／人审不等于新几何批准。`runs/`仅本地，源照片与历史冻结包不改；变更后执行相关测试、Ruff和`git diff --check`。
