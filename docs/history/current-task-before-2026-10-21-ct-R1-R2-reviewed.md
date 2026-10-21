# 原文归档

来源：CURRENT_TASK.md；归档日期：2026-10-21；原文SHA256：a70d1d7b246ec0c69ad1428d867a45c1b393c6f92c6c4926dbe7d5a3318fe019。以下保留修订前完整原文，历史状态不作为当前任务。

---

# 当前任务

## 目标与授权

2026-10-21：用户授权推进来源清理、全幅联合图及整体验收／工作层冻结。已完成技术调查、候选整理和最终质量初检，**整层尚未批准**；停在新增R1A／R1B／R2来源裁决门。旧Q1/Q2/Q3裁决关闭、不重审，不要求逐孔复核，不启动新M1/net。本轮无新增GitHub推送授权，上一远端b9a1683，今日v2/v3及实现／文档仍在本地工作树。

唯一实时入口为本文件。[复核页](docs/assets/ct-work-layer-closeout-v3/index.html)、[检查点](docs/checkpoints/2026-10-21-ct-work-layer-closeout.md)、[新问题清单](benchmarks/ct-work-layer-closeout-v3/review-questions-v1.json)、[阶段门](benchmarks/ct-work-layer-closeout-v3/stage-gate-v1.json)保存当前状态。全幅AA/POLY/CT/未知可独立切换，分块只是同一模型的复核窗口。[前入口完整归档](docs/history/current-task-before-2026-10-21-ct-work-layer-closeout.md)。

## 当前输出与保护边界

- [CT模型](benchmarks/ct-work-layer-closeout-v3/model-v1.json)10226条＝原10025－撤回33＋新增234；9987条完整相同，5条仅纠正来源并保留before/after。新增是候选，不是确认孔数；[保护检查](benchmarks/ct-work-layer-closeout-v3/preservation-check-v1.json)。原7044在v2中的记录完整不变（v2已有5条G18来源历史修正），原批准不扩大。
- [材料](benchmarks/ct-work-layer-closeout-v3/material-model-v1.json)335 AA／696 POLY对象完整不变，含U10共用端。8条旧路径逐项调查：左短AA、Q3B/C环及复杂环两侧有新观察；两小AA、H1/H2条带及复杂环中段保留未知，未声称全物理恢复。20条零散观察完整处置，不按旧槽位自动放行。
- 源反例牵出相邻未审G61环、TOP-STEP-1和U10环配方；整段撤回后独立重取，共33条未审CT退休，不只删冲突点。原始照片和旧观察不覆盖；不扩AA／缩CT迁就错误定位。
- 新通用端口证据盘点按同AA目标和显式几何共用POLY关系统计，内部扩散缺CT不判失败、不补孔。846个重建扩散区域有839个具候选CT记录，7个无直接证据（不等于漏7孔）；696 POLY有2个V3主体截段保留旧端子关系。不是器件数量、召回率或已确认M1接入。[端口表](benchmarks/ct-work-layer-closeout-v3/terminal-access-v1.json)。
- 旧Q1四管下端栅CT／上侧环CT，Q2 U10共用下端POLY，Q3A仅上端且A对应内环H3、Q3B/C对应确认全部继承。[裁决原文](benchmarks/ct-full-frame-adjudication-v2/human-review-v1.json)不改。
- C/D/F、143橙框、RIGHT6、宽MOS／环／电阻、Q2栅60孔、上方40栅、左侧局部及原661环孔和B孔数精度意见均保留。R2_Q1、V3历史端子、网络v33、R1/R2非AA间隙、近邻环隔离、S03-03/04、18条电阻、W01电阻身份、195保留对象不改。AA-F00872退休，界面／邻片／照片外G67不补完整。

## 质量状态与唯一下一步

几何PASS：10226条重叠0、孔距违规0，最小边距4.4px；5px方孔／3px孔距／1px包围及避让预算保持。新取点不同目标3px内争用检查通过。457项全量测试（18.72s）、64项相关测试（4.97s）、相关Ruff、父哈希、86条资源、15个选择器与4层开关模拟检查通过；宽视野PNG已目视，浏览器真实渲染未自动实测。

来源门仍HOLD_new_source_correspondence_and_overall_acceptance，whole_frame_complete=false。模型与阶段门列出需复核来源的CT ID，禁止作为整层已通过直接追网。[冻结清单](benchmarks/ct-work-layer-closeout-v3/freeze-manifest-v1.json)冻结待审候选，human_accepted=false，不是批准层。工艺、物理尺度、极性、真实W/L、阻值和新M1/net仍未知，无真实PDK DRC/LVS，此时不封装CT skill。

**唯一下一步：收到新增来源裁决后局部修订，再重检整层门。**
1. R1A：左上G01/G02长排，确认真实栅CT引出侧与一处源图锚点；紫色旧G可能在源漏列或环，蓝T只是候选带。
2. R1B：右上G05/G06独立确认同类来源，不套用其他组方向。
3. R2：上部内环下边A和近邻外环上边B，POLY图U亮带孔归A、B、各有一排或仍未知；不把同一点接两环。
这些不是旧Q1/Q2/Q3，不重新验全部CT。不能因候选文件写出、端口有记录或几何PASS跳过来源身份门。

## 复现与恢复

- `.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-work-layer-closeout-v3/spec-v1.json --output runs/新的CT工作层目录`；输出须不存在。最终包装附HOLD门、前后保护、层开关和问题原图；版本provenance仅审计，不是生产案例脚本或已封装skill，不覆盖冻结版本。
- `.venv/bin/python -m pytest -q tests/test_ct_transfer.py tests/test_ct_joint_reconstruction.py tests/test_gate_terminal_localization.py`；相关Ruff；`git diff --check`。data/不改，runs/与.venv/不入Git。[CT工作流](docs/architecture/ct-reconstruction-workflow-v1.md)保留质量规则与经验。
