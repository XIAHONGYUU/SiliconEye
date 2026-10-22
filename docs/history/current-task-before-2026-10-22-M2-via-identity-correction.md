# CURRENT_TASK 原文归档

来源：CURRENT_TASK.md
归档日期：2026-10-22
原文SHA256：0d895b71e6ae90de25be424b99c02febf66c29991e6ae684ff88e61dd992dfc4
以下分隔线后为原文完整字节。

---

# 当前任务

## 当前目标与验收

用户批准统一金属／Via接口并生成连续五层联合中样。已完成两处既有人审接口的组装：M1-P08 → V1组 → M2-J01 → J-M2-EDGE-V2 → M3-J-B1；没有新增物理接入判断，不要求重复审批J1/J2、K1。状态SCOPED_REVIEWED_CHAIN_ASSEMBLED，不代表完整网络或全幅金属已恢复。

[当前五层联合页](docs/assets/conductive-stack-v1/index.html)、[检查点](docs/checkpoints/2026-10-22-conductive-stack.md)、[统一读取接口](docs/architecture/conductive-layer-interface-v1.md)、[复跑输入](benchmarks/conductive-stack-v1/request-v1.json)、[最终验证](benchmarks/conductive-stack-v1/verification-v1.json)。22条记录：M1九条、V1九个候选孔、M2一条、V2一个支持区、M3两条；M2去重且几何相同，M1-P08接续片原样合成，其他几何不变。

共同快照升级为[v4](configs/joint-work-layer-v4.json)，AA／POLY／CT输入、原图、预算、未知及批准范围完整继承v3，仅附加锁定conductive_layers注册表。共同加载／检查／保存及layer_review只读复核可读取五层，按层切换与编号突出；当前导体修订事务仍未开放，不能借旧AA／POLY／CT事务修改金属或孔。

局部连接身份已审，边界仍候选。V2小方块为孔组支持代理，真实孔数null。独立精确投影／外推关闭，M2及M3出窗继续未知；B0及其他M1仅作隔离上下文。自动网表边为空，不从交叠自动补连接。原生宽图／4倍局部与设计坐标分开显示。

[第二层对已审包](docs/assets/m2-v2-m3-joint-reviewed-v2/index.html)、[K1人审原文](benchmarks/m2-v2-m3-joint-reviewed-v2/human-review-v1.json)及[独立评价](benchmarks/m2-v2-m3-joint-reviewed-v2/evaluation-result-v1.json)保持：B1目的端判断获直接批准，提交至批准间目的端修订0次；V2身份不算新识别成功，不推断整体准确率。首次AI真值仍null，旧候选／已审包原样保留。

本轮检查覆盖既有材料不变、连续链与双侧包围、重新加载／保存、共同只读入口、来源／产物哈希、SVG／JS／链接，以及六份旧包回放。软件通过不扩大人审范围；详见当前verification。未封装通用金属／Via skill，未扩全幅或追全网。

## N1已审基准

用户答复“确认无误”，N1的V1身份及短竖M1→折线M2下端接入已确认。该例状态SCOPED_REVIEWED_WITH_LIMITATIONS，N1问题关闭，不重复审批。未重算几何，不扩大为实测孔数／精确原生对应／整网批准。

[当前N1已审页](docs/assets/metal-new-interface-reviewed-v2/index.html)、[检查点](docs/checkpoints/2026-10-22-N1-reviewed.md)、[人审原文](benchmarks/metal-new-interface-reviewed-v2/human-review-v1.json)、[可复跑输入](benchmarks/metal-new-interface-reviewed-v2/spec-v1.json)、[最终核验](benchmarks/metal-new-interface-reviewed-v2/verification-v1.json)。已审局部连接存reviewed_local_connections；自动网表边仍为空。

[首次AI观察](benchmarks/metal-new-interface-candidate-v1/initial-ai-observation-v1.json)及[原始候选](docs/assets/metal-new-interface-candidate-v1/index.html)保持原样，其人工真值字段仍null作为事前记录。新[评价记录](benchmarks/metal-new-interface-reviewed-v2/evaluation-result-v1.json)单独对照人工真值：本例身份／接入判断均正确，提交至批准间发生的这两项修订为0；不代表全项目返工数或整体准确率，不是严格隔离上下文的盲测。

45项相关测试通过（45.87s），相关Ruff通过；新门拒绝审批夹带几何、来源点、基准变化。两组基准及原N1候选在新代码下复跑，各16项模型／报告／图页等产物逐字节保持。输入／产物哈希、SVG／JS／链接和归档完整性核验见当前verification。

N1的M1(1145,3219)、M2(1109,3255)仍是AI参考位置；无合格精确映射，不强制照片投影。M2上部亮带未分型，灰色REF-W1仅为已审参照；支持区不是实测单孔。N1批准只新增一条有人工依据的局部接口记录，不合并邻横线或自动追网。

## 第二组已放行设计基准

[W1复核页](docs/assets/metal-short-branch-transfer-v1/index.html)、[既有迁移检查点](docs/checkpoints/2026-10-22-metal-short-branch-transfer.md)和[设计放行](benchmarks/metal-short-branch-transfer-v1/design-approval-v1.json)共同接续。3条M1保持隔离、最小间距9设计像素；M2短竖及宽端部连续，V1组支持区被两层包围；模型重叠不自动并网。第二组是历史已知接口迁移，不计作新盲测成功。

W1沿用历史ID：`R2_corrected_gate_W1_M1_01`、`R2_corrected_gate_W1_V1`、`R2_corrected_gate_W_M2_01`。[历史连接裁决](benchmarks/metal-extension/roi2-W1-V1-M1-review-feedback-v1.json)为M2下端经V1接短竖M1。相对设计现已放行，原生像素中心／孔数仍未实测；6×6支持区不是实测单孔。M1(1244,3220)、M2(1217,3253)参考点保持，不能换到M2上部亮点。历史经CT接AA事实不改，本轮未重新适配CT／AA身份。

## 第一组冻结基准

[已审联合页](docs/assets/m1-v1-m2-joint-reviewed-v2/index.html)、[J1／J2原文](benchmarks/m1-v1-m2-joint-reviewed-v2/human-review-v1.json)、[已审输入](benchmarks/m1-v1-m2-joint-reviewed-v2/spec-v1.json)。橙圈组是V1，M1→V1→M2接入正确；M1原黄色框无V1、M2原黄色框为V2。粗M1右缘无V1，“四排孔的距离”仅为宽度约束，不变成新增V1、精确像素宽度或逐孔数批准。第一组旧包中V2保留当时的原生观察；当前新增的K1裁决已在第二层对已审包将其承载关联到M3-J-B1，不回写冻结旧包。J1／J2关闭。

第一组3点拟合、6点同阵列留出误差约4.52原生像素，仍不是独立结构验证；精确投影与外推关闭。W1不套用这组矩阵，也无自身合格精确矩阵。共同画布5860×4587里的W1相对设计已放行，但原生精确对应未核准；当前CT位置仅作定位参照，不产生新的CT包围批准。两组均不导出自动网络，局部已审接入与完整网络分开。

[最初M1已审修订页](docs/assets/m1-geometry-pilot-reviewed-v2/index.html)、[原Q1–Q3裁决](benchmarks/m1-geometry-pilot-reviewed-v2/human-review-v1.json)：原9项M1、95个CT模型包围及原观察折线保持；P06外U两端补条，P07仅细化原横段CT包围，P08只加宽左竖，六条已审竖线不动。精确新尺寸是AI候选；8个`pending_gate_CT_ids`仅表示原生精确投影未核准，不是几何仍漏孔。不重复审批Q1–Q3。

## 当前唯一共同工作层及有效裁决

[共同快照v4](configs/joint-work-layer-v4.json)的材料部分完整继承[v3](configs/joint-work-layer-v3.json)，仍为AA334／POLY696／CT10287；696含G66-P03/P04上端桥，不代表新增MOS。8张5712×4284源图及哈希、相对预算和继承文档不变；历史AA337／POLY700或旧清单不能覆盖当前层。金属与孔以可选注册表接入共同快照，不改变旧材料容器或原始照片；冻结父包不改。

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

- 当前五层中样：`.venv/bin/python -m silicon_eye.conductive_layers --request benchmarks/conductive-stack-v1/request-v1.json --output runs/新的五层中样目录`。
- 共同只读复核：`.venv/bin/python -m silicon_eye.layer_review --request configs/metal-stack-review-v1.json --output runs/新的五层共同复核目录`。
- M2/V2/M3基准：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/m2-v2-m3-joint-reviewed-v2/spec-v1.json --output runs/新的第二层对已审目录`。
- 当前N1已审：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/metal-new-interface-reviewed-v2/spec-v1.json --output runs/新的N1已审目录`。
- 初始候选回放：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/metal-new-interface-candidate-v1/spec-v1.json --output runs/新的N1目录`。
- 短支路：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/metal-short-branch-transfer-v1/spec-v1.json --output runs/新的短支路目录`。
- 第一组：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/m1-v1-m2-joint-reviewed-v2/spec-v1.json --output runs/新的基准目录`。
- 当前共同层：`.venv/bin/python -m silicon_eye.joint_layers --snapshot configs/joint-work-layer-v4.json --output runs/新的联合检查目录`。
- POLY／CT统一复核：`.venv/bin/python -m silicon_eye.layer_review --request configs/poly-skill-review-v1.json --output runs/新的复核目录`，CT用`configs/ct-skill-review-v1.json`。inspect不生成新模型；revise明确before／after和授权对象；硬失败只留诊断。

输出目录均须新建。原生定位不等于精确投影，多观察合并AA不能套单一旧矩阵。AI观察沿用候选／确认／冲突／未知边界；脚本不生成人工批准。`runs/`仅本地，需要接续的输入和交付已保存benchmarks／docs/assets。

## 唯一下一步与未提交状态

唯一下一步：在该五层模型中验证一个真实的高层向多根下层金属的分支及隔离对照，复用旧结论，只提交新增歧义；然后按效果评估金属／Via skill封装。已审接口不重问，精确投影／全幅／整网仍按各自证据门处理，不自动扩展。

本机HEAD核对为a769561；此前远端同版本的核验为历史记录，本轮没有联网／推送。M1初版及修订、两层对联合小样、K1已审包及本次五层注册表／共同快照适配、短支路迁移代码／测试、页面与文档均为未提交本地改动。保留用户和此前任务的改动，本轮未创建通用skill、未扩网、未改全局Git配置。

[本次迁移前入口完整原文](docs/history/current-task-before-2026-10-22-short-branch-transfer.md)保留全部前阶段状态、历史链接、原恢复命令与批准范围；更早归档按其中链接调取。归档原文SHA256与完整性已核对。

[本次设计放行与N1推进前入口完整原文](docs/history/current-task-before-2026-10-22-new-interface-candidate.md)保留迁移阶段状态、全部历史链接与未提交说明；归档SHA256和原文完整性已核对。

[本次N1裁决前入口完整原文](docs/history/current-task-before-2026-10-22-N1-adjudication.md)保留原N1待审状态、首次观察与历史恢复链接；原文SHA256及完整性已核对。

[本次第二层对验证前入口完整原文](docs/history/current-task-before-2026-10-22-m2-v2-m3-pilot.md)保留N1已审状态、全部有效裁决、未提交说明及恢复命令；原文SHA256和完整字节归档已核对。

[本次K1裁决前入口完整原文](docs/history/current-task-before-2026-10-22-B1-adjudication.md)保留原候选状态、全部裁决、未提交说明和恢复命令；原文SHA256及完整字节归档已核对。

[本次五层组装前入口完整原文](docs/history/current-task-before-2026-10-22-five-layer-stack.md)保留K1已审状态、旧快照、全部裁决及未提交说明；原文SHA256和完整字节归档已核对。
