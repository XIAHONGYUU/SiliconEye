# 原文归档

来源：CURRENT_TASK.md；日期：2026-10-21；原文SHA256：1dfe8a654f6580155838dcf1742c545870b77bb7ca30e43d9aa087d6a4aad009。以下完整保留原文，历史状态不作为当前入口。

---

# 当前任务

## 目标与授权

2026-10-21：继续CT来源清理、全幅联合候选和工作层验收准备。用户已完成R1A／R1B／R2裁决，本轮按裁决局部修订；整层尚未批准，不启动新M1/net，不封装CT skill。本轮无新增GitHub推送授权，上一远端b9a1683；今日v2／v3／v4、通用实现及文档仍在本地工作树。

本文件是唯一实时入口。[最新复核页](docs/assets/ct-work-layer-reviewed-v4/index.html)、[检查点](docs/checkpoints/2026-10-21-ct-R1-R2-reviewed.md)、[裁决原文](benchmarks/ct-work-layer-reviewed-v4/human-review-v1.json)、[阶段门](benchmarks/ct-work-layer-reviewed-v4/stage-gate-v1.json)。分块仅为统一全幅模型的复核窗口。[上版入口完整原文](docs/history/current-task-before-2026-10-21-ct-R1-R2-reviewed.md)按需调取，不作为待办。

## 本轮已确认与局部修订

- R1A／R1B：栅CT实际上端引出，蓝T带正确，源漏孔均匀。G01／G02／G05及G06前5指按独立观察重新定位；替换整组211条未审CT，新增239条候选（64栅CT、175源漏CT）。未继续沿用误落源漏／下环的旧top/bottom标签，不重跑无关区域。
- 同一反例暴露H3未审环路径跨入栅端：82条整段重新测来源，设计几何和ID不变，完整before/after及原来源历史保留。不能以旧引用先导出便认定旧归属正确。
- R2：只有一排CT，AA连续。撤回此前AI拆成两条隔离环的解释；保留AA2-UPPER-INNER-B-AA-0，将相邻复杂环材料并入并保留旧ID别名与两份原来源。241条CT更新承载ID，其中106条未审侧段对齐中央已审行，统一13px节距；中央220条记录不变。只确认此处AA连续，不扩展为M1或新net结论。
- 当前[模型](benchmarks/ct-work-layer-reviewed-v4/model-v1.json)10254 CT＝10226－211＋239；334 AA／696 POLY。原7044条在v3中的完整记录不变；696 POLY和无关333 AA完整不变。R2新增AA面积不接触其他AA对象；[前后保护](benchmarks/ct-work-layer-reviewed-v4/preservation-check-v1.json)。对象数量不是器件数或准确率。

## 唯一待人工裁决

**R1B-COUNT：右上末段原图目前可分辨4组上端栅亮条、5列源漏孔，旧POLY为5条。是否应改为4条栅？**

[宽视野编号原图](docs/assets/ct-work-layer-reviewed-v4/COUNT-caps.png)、[放大原图](docs/assets/ct-work-layer-reviewed-v4/COUNT-inset.png)与[4条替代几何](docs/assets/ct-work-layer-reviewed-v4/COUNT-alternative.svg)。对应AA-F01804、G06-P06～P10；旧材料保留并列为数量冲突，该块旧未审CT已撤回，不为多余栅生成CT。4条替代方案未进入工作模型。引出侧已确认，不再重复提问或逐孔审批。

阶段门HOLD_R1B_material_count_and_overall_acceptance；whole_frame_complete=false。R1A／R1B／R2原问题已关闭，新增数量冲突与最终整体验收仍未通过。[冻结清单](benchmarks/ct-work-layer-reviewed-v4/freeze-manifest-v1.json)冻结待审候选，不是批准工作层。

## 继续保留的边界与未知

- 旧Q1四管下端栅CT、Q2 U10下端共用POLY、Q3A上端及内环H3对应、Q3B/C对应不改。C/D/F、143橙框、RIGHT6、宽MOS／环／电阻、Q2栅60孔、上方40栅、左侧局部、原661环孔及B孔数精度意见按原范围保留。
- R2_Q1、V3历史端子、网络v33、其他位置R1/R2非AA间隙及近邻环隔离、S03-03/04、18条电阻、W01电阻身份和195保留对象不改。AA-F00872退休，界面／邻片／照片外G67不补完整。
- 8条旧来源轨迹、20条零散观察的调查见v3，不代表全部物理恢复。两小AA、H1/H2长条孔位可辨识度未知；846个重建扩散区域仍有7个无直接CT证据，内部扩散可无孔，不当漏检。POLY无直接CT为V3两历史主体截段和本次暂缓的G06末5指，不虚构端口。工艺、物理尺度、极性、真实W/L及阻值未知，无真实PDK DRC/LVS。

## 验证、恢复与唯一下一步

10254条几何PASS，重叠0、孔距违规0、最小边距4.4px；5px方孔／3px孔距／1px包围及避让预算保持。239新增与82修正来源做3px跨目标争用检查，无冲突。父冻结哈希、原7044保护、局部材料合并、来源历史、页面资源及层开关检查通过；64项相关测试（4.83s）和相关Ruff通过。本轮只改数据／审计配方／文档，沿用通用接口；几何和软件通过不代替物理判断，浏览器真实渲染未自动实测。

唯一下一步：取得R1B-COUNT数量裁决后，仅局部处理AA-F01804的POLY及CT，再检查整层门和准备一次整体工作层验收；不从头复核全部CT。

- `.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-work-layer-reviewed-v4/spec-v1.json --output runs/新的CT裁决目录`；输出须不存在。版本provenance只作审计，不原地重跑冻结包。
- `.venv/bin/python -m pytest -q tests/test_ct_transfer.py tests/test_ct_joint_reconstruction.py tests/test_gate_terminal_localization.py`；相关Ruff；`git diff --check`。data/不改，runs/与.venv/不入Git。[CT工作流](docs/architecture/ct-reconstruction-workflow-v1.md)保存长期规则。
