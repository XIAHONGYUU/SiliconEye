# CT工作层收口前入口归档

来源：CURRENT_TASK.md；日期：2026-10-21。以下为原文完整保留。

# 当前任务

## 目标、授权与有效入口

2026-10-21：用户完成Q1／Q2／Q3A/B/C裁决，授权按已有流程受控局部接续。五项人审问题已关闭；本轮本地修订完成，不要求重复审批，不扩大成全幅物理批准，不启动新M1/net追踪。上一远端保存点b9a1683；本轮修改尚未提交，本轮无新增GitHub推送请求。

唯一实时入口为本文件。[修订复核页](docs/assets/ct-full-frame-adjudication-v2/index.html)支持新旧／原图切换；[检查点](docs/checkpoints/2026-10-21-ct-adjudication.md)、[裁决原文与执行范围](benchmarks/ct-full-frame-adjudication-v2/human-review-v1.json)、[阶段门](benchmarks/ct-full-frame-adjudication-v2/stage-gate-v1.json)保留证据。旧入口[完整归档](docs/history/current-task-before-2026-10-21-ct-adjudication.md)，旧v1候选和原验收不覆盖。

## 当前结果及必须继承的裁决

- Q1左侧四管全部从下端引出栅CT，上方原红X为环CT；补8条栅CT候选，恢复16条此前依赖暂缓的源漏候选；不重审四管／2×2和已审AA/POLY。
- Q2 U10两条POLY共用下端，CT在连接处：保留G68-P01/P02，另增G68-BOTTOM-BUS-01及2条CT候选。原U10分指主体保留，旧端部分开假设由本次共用端裁决接续；精确桥尺寸、孔数与位置仍为AI候选，不推断新M1或器件数。
- Q3A：G是上端栅端，不从POLY下端引出；蓝A对应靠近栅极的内侧环AA2-TOP-H3-AA-0，旧H2标记撤回。P02下端2条未审CT撤回；同组P01/P03另3条由AI复查同一环亮条后撤回，不扩写成人工逐点确认。
- Q3B、Q3C：G/A身份关系与对应已确认，已有对象保留；确认身份不自动证明整段旧路径的像素定位。
- G18-P03/P07的5条旧CT来源错落前一排：只重定位照片来源，保留完整before/after及裁决引用，ID、目标、数量、几何和批准范围不变；其余原记录不重算。[保护与来源检查](benchmarks/ct-full-frame-adjudication-v2/preservation-and-source-check-v1.json)。
- [当前CT模型](benchmarks/ct-full-frame-adjudication-v2/model-v1.json)10025条＝原10004－撤回5＋新增26。原7044全部几何／目标保留，7039条记录完整相同，5条仅来源修正；原10004中9994条完整相同。记录数不是确认孔数／器件数。
- [材料模型](benchmarks/ct-full-frame-adjudication-v2/material-model-v1.json)保留全部335 AA与原695 POLY，另加1个共用端POLY。照片原生坐标与规则设计坐标分开；不扩AA／缩CT迁就错误定位，照片证据不覆盖。
- 原C/D/F三排与边孔、F双孔及143橙框批准继承；RIGHT6、宽MOS、环／电阻、Q2栅60孔、上方40栅、左侧局部批准均保留。旧661环孔一致性意见、B孔数精度意见不改；[原7044验收](benchmarks/ct-lower-middle-mos-revision-v2/acceptance-v1.json)。
- R2_Q1、V3_G1/G2历史端子与M1/M2、网络v33、R1/R2非AA间隙、近邻环隔离、S03-03/04独立性、18条电阻、SG-U04-W01电阻身份、195保留对象和8张原照片不改。AA-F00872按人审退休，界面遮挡／邻片／照片外G67不补完整材料。工艺、物理尺度、极性、真实W/L及阻值仍未知。

## 质量状态与唯一下一步

人审问题门PASS_Q1_Q2_Q3_scoped_decisions，pending_human_questions为空；整层HOLD_technical_source_path_reinspection、whole_frame_complete=false。几何PASS只证明安全候选子集，不是真实PDK DRC/LVS、完整层或完整网表。新精确几何不自动取得人工批准。

原5px方孔／3px孔距／1px包围及避让预算不降；10025条整体几何重叠0、孔距违规0、最小边距4.4px；共用端连接检查通过。454项全量测试（19.20s）、相关Ruff、父哈希、43条静态链接与图像检查通过；浏览器真实渲染未自动实测。

**下一步：独立回查8条旧来源路径，不再重问这五项。** [路径清单](benchmarks/ct-full-frame-adjudication-v2/stage-gate-v1.json)来自旧锁定8条清单（旧文误写7）；整段仍暂缓，不因身份已确认而直接释放。原403条调查观察不是实际漏孔数，[新处置台账](benchmarks/ct-full-frame-adjudication-v2/prior-observation-disposition-v1.json)区分已恢复、已撤回、被新观察替代和技术暂缓。先修正原图定位，再按未降预算逐段检查来源及几何；仅有新的实质歧义才提出人工问题。此时不封装CT skill。

## 复现与恢复

- `.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-full-frame-adjudication-v2/spec-v1.json --output runs/新的裁决执行目录`；输出须不存在。最终包装状态／PNG／标记另见版本provenance，只供审计，不原地重跑冻结版本。
- `.venv/bin/python -m pytest -q tests/test_ct_transfer.py tests/test_ct_joint_reconstruction.py tests/test_gate_terminal_localization.py`；相关Ruff及`git diff --check`。照片data/不改，runs/与.venv/不入Git。
- [CT工作流](docs/architecture/ct-reconstruction-workflow-v1.md)保留分工与质量门；新来源纠正接口保留旧观察和设计不变，禁止将普通几何调整当作隐式改源授权。
