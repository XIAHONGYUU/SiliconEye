# 当前任务入口归档

来源：CURRENT_TASK.md；归档日期：2026-10-22；原文SHA256：274687c27df4bc203bd0db790caef419209f6dce49a5fef9af0d187c431b4f16。

---

# 当前任务

## 当前目标与验收

用户已批准第二组W1相对设计并授权继续。已记录[设计放行原文](benchmarks/metal-short-branch-transfer-v1/design-approval-v1.json)，锁定当时模型／输入／报告／页面。该批准不扩大为原生精确投影、实测孔数或新接口身份。

当前生成W1左侧的N1未审候选：[当前复核页](docs/assets/metal-new-interface-candidate-v1/index.html)、[检查点](docs/checkpoints/2026-10-22-metal-new-interface-candidate.md)、[输入](benchmarks/metal-new-interface-candidate-v1/spec-v1.json)、[首次AI观察](benchmarks/metal-new-interface-candidate-v1/initial-ai-observation-v1.json)、[最终核验](benchmarks/metal-new-interface-candidate-v1/verification-v1.json)。AI初判为短竖M1上端V1候选接到折线M2下端；M2上部亮带未分型。灰色REF-W1为已审参照。状态REVIEW_REQUIRED，只待N1这一项接入裁决。

首次AI判断已在新人工裁决前保存，人工真值、正确性及纠正次数均null；不是严格隔离上下文的盲测。候选只存hypothesized_local_connections，无reviewed_local_connections或网表边。M1(1145,3219)、M2(1109,3255)为AI参考位置；无精确原生或设计映射，不作强制照片投影。几何通过不证明V1身份／真实接入。

42项相关测试通过（40.64s），相关Ruff通过。两组基准在新代码下复跑，各16项模型／报告／图页等产物逐字节相同，清单只记录新代码哈希。新保护拒绝旧设计批准覆盖新接口、批准绑定错误模型、删除未审问题、移动首次参考点凑合、AI自填人工真值。验证档在当前N1 benchmark。

## 第二组已放行设计基准

[W1复核页](docs/assets/metal-short-branch-transfer-v1/index.html)、[既有迁移检查点](docs/checkpoints/2026-10-22-metal-short-branch-transfer.md)和[设计放行](benchmarks/metal-short-branch-transfer-v1/design-approval-v1.json)共同接续。3条M1保持隔离、最小间距9设计像素；M2短竖及宽端部连续，V1组支持区被两层包围；模型重叠不自动并网。第二组是历史已知接口迁移，不计作新盲测成功。

W1沿用历史ID：`R2_corrected_gate_W1_M1_01`、`R2_corrected_gate_W1_V1`、`R2_corrected_gate_W_M2_01`。[历史连接裁决](benchmarks/metal-extension/roi2-W1-V1-M1-review-feedback-v1.json)为M2下端经V1接短竖M1。相对设计现已放行，原生像素中心／孔数仍未实测；6×6支持区不是实测单孔。M1(1244,3220)、M2(1217,3253)参考点保持，不能换到M2上部亮点。历史经CT接AA事实不改，本轮未重新适配CT／AA身份。

## 第一组冻结基准

[已审联合页](docs/assets/m1-v1-m2-joint-reviewed-v2/index.html)、[J1／J2原文](benchmarks/m1-v1-m2-joint-reviewed-v2/human-review-v1.json)、[已审输入](benchmarks/m1-v1-m2-joint-reviewed-v2/spec-v1.json)。橙圈组是V1，M1→V1→M2接入正确；M1原黄色框无V1、M2原黄色框为V2。粗M1右缘无V1，“四排孔的距离”仅为宽度约束，不变成新增V1、精确像素宽度或逐孔数批准。M2上V2仅原生观察，尚未指定M3。J1／J2关闭。

第一组3点拟合、6点同阵列留出误差约4.52原生像素，仍不是独立结构验证；精确投影与外推关闭。W1不套用这组矩阵，也无自身合格精确矩阵。共同画布5860×4587里的W1相对设计已放行，但原生精确对应未核准；当前CT位置仅作定位参照，不产生新的CT包围批准。两组均不导出自动网络，局部已审接入与完整网络分开。

[最初M1已审修订页](docs/assets/m1-geometry-pilot-reviewed-v2/index.html)、[原Q1–Q3裁决](benchmarks/m1-geometry-pilot-reviewed-v2/human-review-v1.json)：原9项M1、95个CT模型包围及原观察折线保持；P06外U两端补条，P07仅细化原横段CT包围，P08只加宽左竖，六条已审竖线不动。精确新尺寸是AI候选；8个`pending_gate_CT_ids`仅表示原生精确投影未核准，不是几何仍漏孔。不重复审批Q1–Q3。

## 当前唯一共同工作层及有效裁决

[共同快照v3](configs/joint-work-layer-v3.json)仍为AA334／POLY696／CT10287；696含G66-P03/P04上端桥，不代表新增MOS。8张5712×4284源图及哈希、相对预算和继承文档不变；历史AA337／POLY700或旧清单不能覆盖当前层。金属与孔仍是伴随模型，未伪装已扩展共同清单；源图和冻结父包不改。

- S1三列身份／相对位置与S2显示修订已批准。72条来源修订保留；旧16对争用及新争用均0，不扩大为全层逐孔／像素批准。
- S3：紫色为ROW4-AA3源漏CT；蓝色为G66-P03／P04共用POLY向上栅CT。蓝色ID `CT-G66-P03-P04-SHARED-TOP-01`，目标`G66-P03-P04-TOP-BUS`；旧ROW4-AA4-SD00错误CT退休。新桥／孔几何仍AI候选。
- 身份硬门拒绝蓝改AA、紫色目标改变、退休身份复活和共用成员丢失；来源／几何无争用不能代替身份批准。退休别名、G68合法桥、G26阶梯AA局部截面、AA最新层适配、变化域保护继续有效。
- 四栅G06R-P01～P04及33孔、R1A／R1B上端及均匀源漏、R2本处连续AA单排孔、旧Q1／Q2／Q3与邻环隔离保留。C/D/F、143橙框、RIGHT6、宽MOS／环／电阻、Q2栅60孔、上方40栅、左侧局部、661环孔及B孔数精度意见保留原范围。
- R2_Q1、V3端子、网络v33、S03-03/04、18电阻、W01身份及195保留对象不改。未通过本次迁移修订AA／POLY／CT。

六处来源／接入限制：AA-F01951、AA-F01952、H1、H2、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS。最后一处既不独立证明另有源漏孔，也不证明无孔；不能借蓝色栅CT或补孔。V3两主体截段历史端子例外继续有效。未知只限制依赖，不因此重做全层。

`automatic_network_export_allowed=false`。物理尺度、工艺、极性、真实W/L及阻值未知，没有真实PDK DRC/LVS；工程PASS、局部批准不升级为100%物理恢复或整层网表。

## 工具边界与恢复

[POLY skill](skills/silicon-eye-poly-reconstruction/SKILL.md)、[CT skill](skills/silicon-eye-ct-reconstruction/SKILL.md)、[共用契约](docs/architecture/layer-reconstruction-skill-contract-v1.md)、[封装验证报告](docs/reviews/2026-10-21-poly-ct-skills.md)保持。历史25项封装检查及无本轮聊天Agent试用证据按检查点调取；这是已知芯片开卷接续，不证明陌生图准确率，未实测返工数仍null。skill在仓库，未安装全局。

[金属／孔架构评估](docs/architecture/metal-via-skill-boundary-assessment-v1.md)保持“两个通用skill＋逐层／层对配置和质量门”方向；CT与追网分开。当前只完成两类M1／V1／M2已知样本迁移，未创建通用金属/Via skill、未验证另一层对或全幅金属重建。`joint_layers`／`layer_review`仍覆盖AA/POLY/CT，不把金属塞进POLY字段。

- 新候选：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/metal-new-interface-candidate-v1/spec-v1.json --output runs/新的N1目录`。
- 短支路：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/metal-short-branch-transfer-v1/spec-v1.json --output runs/新的短支路目录`。
- 第一组：`.venv/bin/python -m silicon_eye.metal_via_pilot --spec benchmarks/m1-v1-m2-joint-reviewed-v2/spec-v1.json --output runs/新的基准目录`。
- 当前共同层：`.venv/bin/python -m silicon_eye.joint_layers --snapshot configs/joint-work-layer-v3.json --output runs/新的联合检查目录`。
- POLY／CT统一复核：`.venv/bin/python -m silicon_eye.layer_review --request configs/poly-skill-review-v1.json --output runs/新的复核目录`，CT用`configs/ct-skill-review-v1.json`。inspect不生成新模型；revise明确before／after和授权对象；硬失败只留诊断。

输出目录均须新建。原生定位不等于精确投影，多观察合并AA不能套单一旧矩阵。AI观察沿用候选／确认／冲突／未知边界；脚本不生成人工批准。`runs/`仅本地，需要接续的输入和交付已保存benchmarks／docs/assets。

## 唯一下一步与未提交状态

唯一下一步：收录N1裁决——橙圈是否为V1，并把左侧短竖M1接到左侧折线M2下端。若不对应，先按用户所指修正；裁决另存，不改首次AI观察。第一组J1/J2、第二组W1及设计放行均不重审。之后再评估候选准确性与扩幅，不凭几何PASS直接并网。

本机HEAD核对为a769561；此前远端同版本的核验为历史记录，本轮没有联网／推送。M1初版及修订、两组联合小样、短支路迁移代码／测试、页面与文档均为未提交本地改动。保留用户和此前任务的改动，本轮未创建通用skill、未扩网、未改全局Git配置。

[本次迁移前入口完整原文](docs/history/current-task-before-2026-10-22-short-branch-transfer.md)保留全部前阶段状态、历史链接、原恢复命令与批准范围；更早归档按其中链接调取。归档原文SHA256与完整性已核对。

[本次设计放行与N1推进前入口完整原文](docs/history/current-task-before-2026-10-22-new-interface-candidate.md)保留迁移阶段状态、全部历史链接与未提交说明；归档SHA256和原文完整性已核对。
