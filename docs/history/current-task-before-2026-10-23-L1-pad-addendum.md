# Current task archive

Source: CURRENT_TASK.md
Archived: 2026-10-23
Payload begins after the following delimiter.

<!-- ORIGINAL CURRENT_TASK BYTES -->
# 当前任务

## 当前L1整段M2分支复核

用户要求沿L1的M3检查所有接入M2分支。已扫描照片内整段连续宽母线，左端出照片、右端约x5150收口；主清单13处：D1已审，F01–F12共12处新增V2→M2接入候选，尚待裁决。另有左侧P0–P5小短端未知，不计入主清单，也不宣布不接。

[当前复核页](docs/assets/l1-m2-fanout-v1/index.html)、[事前观察／完整清单](benchmarks/l1-m2-fanout-v1/initial-ai-observation-v1.json)、[请求](benchmarks/l1-m2-fanout-v1/request-v1.json)、[检查点](docs/checkpoints/2026-10-22-L1-M2-fanout.md)、[核验](benchmarks/l1-m2-fanout-v1/verification-v1.json)。页面含整条横带、四个重叠分区及4倍宽局部、分支表与原图／两层切换；两层各用原生坐标，不做未核准投影。

F01–F03为左侧M2下端，F04复用现有M2-J01的下端延伸／新接入候选，不重建第二个J01；F05–F12各自上下延伸，均计同一根本地连续M2。D1复用N2原M2与V2组。通过既有fanout_inventory按下层ID去重为13，不能把孔数或上下两个方向当成分支数；仅D1本处已审，不把13说成全部已确认。

左侧P0在照片边界、P1–P5小焊盘／短端更靠近下方细M3通道，但缺少可靠对应，保持未知。右侧X1在宏观L1右端之外，目的端未知；中部X2只在M3照片见孔阵列，留作更高层前沿，不作为M2→M3的V2证据。左端照片外及P组未解决，不能宣布全部可见接口确认或整网完成。

本轮只提交两组新增裁决：F01–F12是否各经V2接入L1（可整批批准或列例外）；P0–P5是否有接L1的小短端，或仍未知。新候选的逐项评价真值均null，孔数／边界／精确投影未知。M1 U1/U2/U3、既有材料六处未知不变，不能由本次M2清单顺带批准。

[已审R1/D1](docs/assets/n2-downstream-interfaces-reviewed-v2/index.html)完整保留：B1 → 上端V2 → N2窄M2（连续至下端收口）→ D1下端V2 → L1。L1沿用稳定ID M3-N2-LOWER-BUS-CANDIDATE，身份批准不重分配ID；不重审D1／R1／N2，不把B1与L1合成同一金属图形。[N2上端](docs/assets/b1-neighbor-interface-reviewed-v2/index.html)和[A/C历史验证](docs/assets/metal-fanout-validation-v1/index.html)按需调取。

复用source_panels及fanout_inventory，未新增案例脚本／提取算法或共同几何。18份原图裁片逐像素一致，哈希、页面链接与JS语法检查通过；未执行浏览器交互测试。当前共同快照仍v5、33条导体，全部材料和未知保持；新已审接口0，自动网表边为空。

## 已审共同五层基准

用户纠正：本批M2照片本处孔阵列仅为V2，3行×4列共12个，不能标作V1。已完成来源／数量修订，状态SCOPED_REVIEWED_CHAIN_SOURCE_CORRECTED。M1上的V1及既有局部接入保留，M1／M2／M3几何不动；没有新增物理连接判断或待重复审批问题。

[当前纠错五层页v2](docs/assets/conductive-stack-v2/index.html)、[纠错检查点](docs/checkpoints/2026-10-22-m2-via-source-correction.md)、[人审原文](benchmarks/conductive-stack-v2/human-review-v1.json)、[复跑请求](benchmarks/conductive-stack-v2/request-v1.json)、[验证记录](benchmarks/conductive-stack-v2/verification-v1.json)、[评价更正](benchmarks/conductive-stack-v2/evaluation-correction-v1.json)。旧v1／快照v4仅保留错误历史，不能作为当前孔层身份或配准基准。

共同快照更新为[v5](configs/joint-work-layer-v5.json)，材料输入、照片、预算和六处未知完整继承v3；导体33条记录为M1九条、V1九个候选孔、M2一条、V2十二孔、M3两条。V2-J-EDGE-SUPPORT在当前模型退休；新增V2-J-R01-C01至V2-J-R03-C04归属原物理组J-M2-EDGE-V2，其范围由旧左列扩展为本处整组。已确认本组V2数量12，精确边界仍候选，照片／所有Via层总孔数仍未知。

重要撤回：原9对M1/V1→M2/V2不是同孔对应，原3点拟合／6点留出及约4.52像素残差无效，状态REJECTED_DIFFERENT_VIA_LAYER。不得继续作为低精度配准或独立验证使用。旧数值记录原样归档但不再是当前证据；当前V1只保留M1观察，不含M2孔坐标。显式声明为不同Via层的同孔配对在拟合前拒绝。

source_identity_gate按本批人审照片身份检查M1/V1及M2/V2，拒绝V1借用M2像素／照片。源图原生坐标与候选设计几何分开；独立精确投影／外推关闭，M2及M3出窗延伸未知，B0及其他M1仅作隔离上下文。规则孔阵列满足间距和双侧包围，但不声称真实PDK DRC。

既有已审局部链仍为M1-P08 → V1组 → M2-J01 → J-M2-EDGE-V2 → M3-J-B1；K1的B1承载不变。只读共同接口、按层切换、原图／宽局部与编号突出继续可用，新增分别只看V1或V2的按钮。自动网表边仍为空，未扩全幅或追全网，未封装通用skill。

原包／原图、旧AI判断与审计历史不改写。本轮验证区分旧包可复现和旧语义正确：历史回放不再计为M2身份通过；原M2/V1错标与错误配对明确记入评价更正，不以软件PASS抵消。

## N1已审基准

用户答复“确认无误”，N1的V1身份及短竖M1→折线M2下端接入已确认。该例状态SCOPED_REVIEWED_WITH_LIMITATIONS，N1问题关闭，不重复审批。未重算几何，不扩大为实测孔数／精确原生对应／整网批准。

[当前N1已审页](docs/assets/metal-new-interface-reviewed-v2/index.html)、[检查点](docs/checkpoints/2026-10-22-N1-reviewed.md)、[人审原文](benchmarks/metal-new-interface-reviewed-v2/human-review-v1.json)、[可复跑输入](benchmarks/metal-new-interface-reviewed-v2/spec-v1.json)、[最终核验](benchmarks/metal-new-interface-reviewed-v2/verification-v1.json)。已审局部连接存reviewed_local_connections；自动网表边仍为空。

[首次AI观察](benchmarks/metal-new-interface-candidate-v1/initial-ai-observation-v1.json)及[原始候选](docs/assets/metal-new-interface-candidate-v1/index.html)保持原样，其人工真值字段仍null作为事前记录。新[评价记录](benchmarks/metal-new-interface-reviewed-v2/evaluation-result-v1.json)单独对照人工真值：本例身份／接入判断均正确，提交至批准间发生的这两项修订为0；不代表全项目返工数或整体准确率，不是严格隔离上下文的盲测。

45项相关测试通过（45.87s），相关Ruff通过；新门拒绝审批夹带几何、来源点、基准变化。两组基准及原N1候选在新代码下复跑，各16项模型／报告／图页等产物逐字节保持。输入／产物哈希、SVG／JS／链接和归档完整性核验见当前verification。

N1的M1(1145,3219)、M2(1109,3255)仍是AI参考位置；无合格精确映射，不强制照片投影。M2上部亮带未分型，灰色REF-W1仅为已审参照；支持区不是实测单孔。N1批准只新增一条有人工依据的局部接口记录，不合并邻横线或自动追网。

## 第二组已放行设计基准

[W1复核页](docs/assets/metal-short-branch-transfer-v1/index.html)、[既有迁移检查点](docs/checkpoints/2026-10-22-metal-short-branch-transfer.md)和[设计放行](benchmarks/metal-short-branch-transfer-v1/design-approval-v1.json)共同接续。3条M1保持隔离、最小间距9设计像素；M2短竖及宽端部连续，V1组支持区被两层包围；模型重叠不自动并网。第二组是历史已知接口迁移，不计作新盲测成功。

W1沿用历史ID：`R2_corrected_gate_W1_M1_01`、`R2_corrected_gate_W1_V1`、`R2_corrected_gate_W_M2_01`。[历史连接裁决](benchmarks/metal-extension/roi2-W1-V1-M1-review-feedback-v1.json)为M2下端经V1接短竖M1。相对设计现已放行，原生像素中心／孔数仍未实测；6×6支持区不是实测单孔。M1(1244,3220)、M2(1217,3253)参考点保持，不能换到M2上部亮点。历史经CT接AA事实不改，本轮未重新适配CT／AA身份。

## 第一组历史基准（错误跨孔层配对已撤回）

[已审联合页](docs/assets/m1-v1-m2-joint-reviewed-v2/index.html)、[J1／J2原文](benchmarks/m1-v1-m2-joint-reviewed-v2/human-review-v1.json)、[已审输入](benchmarks/m1-v1-m2-joint-reviewed-v2/spec-v1.json)。橙圈组是V1，M1→V1→M2接入正确；M1原黄色框无V1、M2原黄色框为V2。粗M1右缘无V1，“四排孔的距离”仅为宽度约束，不变成新增V1、精确像素宽度或逐孔数批准。第一组旧包中V2保留当时的原生观察；当前新增的K1裁决已在第二层对已审包将其承载关联到M3-J-B1，不回写冻结旧包。J1／J2关闭。

第一组原3点拟合／6点留出约4.52像素的计算来自V1到V2错误配对，现已撤回为配准依据；它不再是有效的同阵列验证。精确投影与外推关闭。W1不套用这组矩阵，也无自身合格精确矩阵。共同画布5860×4587里的W1相对设计已放行，但原生精确对应未核准；当前CT位置仅作定位参照，不产生新的CT包围批准。两组均不导出自动网络，局部已审接入与完整网络分开。

[最初M1已审修订页](docs/assets/m1-geometry-pilot-reviewed-v2/index.html)、[原Q1–Q3裁决](benchmarks/m1-geometry-pilot-reviewed-v2/human-review-v1.json)：原9项M1、95个CT模型包围及原观察折线保持；P06外U两端补条，P07仅细化原横段CT包围，P08只加宽左竖，六条已审竖线不动。精确新尺寸是AI候选；8个`pending_gate_CT_ids`仅表示原生精确投影未核准，不是几何仍漏孔。不重复审批Q1–Q3。

## 当前唯一共同工作层及有效裁决

[共同快照v5](configs/joint-work-layer-v5.json)的材料部分完整继承[v3](configs/joint-work-layer-v3.json)，仍为AA334／POLY696／CT10287；696含G66-P03/P04上端桥，不代表新增MOS。8张5712×4284源图及哈希、相对预算和继承文档不变；历史AA337／POLY700或旧清单不能覆盖当前层。金属与孔以可选注册表接入共同快照，不改变旧材料容器或原始照片；冻结父包不改。

- S1三列身份／相对位置与S2显示修订已批准。72条来源修订保留；旧16对争用及新争用均0，不扩大为全层逐孔／像素批准。
- S3：紫色为ROW4-AA3源漏CT；蓝色为G66-P03／P04共用POLY向上栅CT。蓝色ID `CT-G66-P03-P04-SHARED-TOP-01`，目标`G66-P03-P04-TOP-BUS`；旧ROW4-AA4-SD00错误CT退休。新桥／孔几何仍AI候选。
- 身份硬门拒绝蓝改AA、紫色目标改变、退休身份复活和共用成员丢失；来源／几何无争用不能代替身份批准。退休别名、G68合法桥、G26阶梯AA局部截面、AA最新层适配、变化域保护继续有效。
- 四栅G06R-P01～P04及33孔、R1A／R1B上端及均匀源漏、R2本处连续AA单排孔、旧Q1／Q2／Q3与邻环隔离保留。C/D/F、143橙框、RIGHT6、宽MOS／环／电阻、Q2栅60孔、上方40栅、左侧局部、661环孔及B孔数精度意见保留原范围。
- R2_Q1、V3端子、网络v33、S03-03/04、18电阻、W01身份及195保留对象不改。未通过本次迁移修订AA／POLY／CT。

六处来源／接入限制：AA-F01951、AA-F01952、H1、H2、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS。最后一处既不独立证明另有源漏孔，也不证明无孔；不能借蓝色栅CT或补孔。V3两主体截段历史端子例外继续有效。未知只限制依赖，不因此重做全层。

`automatic_network_export_allowed=false`。物理尺度、工艺、极性、真实W/L及阻值未知，没有真实PDK DRC/LVS；工程PASS、局部批准不升级为100%物理恢复或整层网表。

## 工具边界与恢复

[POLY skill](skills/silicon-eye-poly-reconstruction/SKILL.md)、[CT skill](skills/silicon-eye-ct-reconstruction/SKILL.md)、[共用契约](docs/architecture/layer-reconstruction-skill-contract-v1.md)、[封装验证报告](docs/reviews/2026-10-21-poly-ct-skills.md)保持。历史25项封装检查及无本轮聊天Agent试用证据按检查点调取；这是已知芯片开卷接续，不证明陌生图准确率，未实测返工数仍null。skill在仓库，未安装全局。

[金属／孔架构评估](docs/architecture/metal-via-skill-boundary-assessment-v1.md)保持“两个通用skill＋逐层／层对配置和质量门”方向；CT与追网分开。当前完成两类M1／V1／M2已知样本迁移及N1先判后审接口确认；M2／V2／M3已通过相对几何门且K1局部承载已确认，精确对应尚未核准。未创建通用金属/Via skill，未完成全幅金属重建。`joint_layers`／`layer_review`已支持上述导体注册表的加载／只读复核，旧材料修订事务仍只覆盖AA/POLY/CT，不把金属塞进POLY字段。

- 当前五层中样：`.venv/bin/python -m silicon_eye.conductive_layers --request benchmarks/conductive-stack-v2/request-v1.json --output runs/新的纠错五层中样目录`。
- 共同只读复核：`.venv/bin/python -m silicon_eye.layer_review --request configs/metal-stack-review-v2.json --output runs/新的纠错共同复核目录`。
- M2/V2/M3历史回放（孔组支持／旧来源状态，不作当前身份基准）：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/m2-v2-m3-joint-reviewed-v2/spec-v1.json --output runs/新的第二层对已审目录`。
- 当前N1已审：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/metal-new-interface-reviewed-v2/spec-v1.json --output runs/新的N1已审目录`。
- 初始候选回放：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/metal-new-interface-candidate-v1/spec-v1.json --output runs/新的N1目录`。
- 短支路：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/metal-short-branch-transfer-v1/spec-v1.json --output runs/新的短支路目录`。
- 第一组历史回放（其M1/V1→M2/V2配对已撤回，不可用作配准）：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/m1-v1-m2-joint-reviewed-v2/spec-v1.json --output runs/新的基准目录`。
- 当前共同层：`.venv/bin/python -m silicon_eye.joint_layers --snapshot configs/joint-work-layer-v5.json --output runs/新的联合检查目录`。
- POLY／CT统一复核：`.venv/bin/python -m silicon_eye.layer_review --request configs/poly-skill-review-v1.json --output runs/新的复核目录`，CT用`configs/ct-skill-review-v1.json`。inspect不生成新模型；revise明确before／after和授权对象；硬失败只留诊断。

输出目录均须新建。原生定位不等于精确投影，多观察合并AA不能套单一旧矩阵。AI观察沿用候选／确认／冲突／未知边界；脚本不生成人工批准。`runs/`仅本地，需要接续的输入和交付已保存benchmarks／docs/assets。

## 唯一下一步与Git存档范围

唯一下一步：等待F01–F12及P组裁决，按实际批准绑定事前评价与下层ID，再回查获准M2分支。保留照片左端之外、P组及M1 U1-U3的未知，不因其他候选获批而宣称完整；不重问D1、R1和N2。

本次Git存档基于父提交a769561，覆盖M1重建小样、两组层对接口、五层统一读取／来源纠错、N2及R1/D1已审关系和L1最新待复核清单，以及相应代码／测试／原图证据／历史归档。金属与Via通用skill尚未封装，全幅金属／完整网络尚未验收；候选与批准状态保持原范围。

[本次GitHub存档检查点](docs/checkpoints/2026-10-22-github-state-archive.md)保存范围、恢复入口和验证；[存档前当前入口完整原文](docs/history/current-task-before-2026-10-22-github-state-archive.md)已按原字节及SHA256归档。补入两张原被忽略的历史裁决证据图，保持原路径与哈希，使必要输入随版本保存。提交与远端SHA以Git记录核验；不改全局Git配置、不改原始照片。

[本次L1分支检查前入口完整原文](docs/history/current-task-before-2026-10-22-L1-fanout-inspection.md)完整保留R1／D1已审状态、方法、证据及未提交说明；归档原始字节及SHA256已核对，更早历史按归档链接调取。
