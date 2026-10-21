# 当前任务

## 目标与授权／当前结果

2026-10-21：用户要求“完成这三项后收口”。四栅局部修订及CT补全、剩余证据限制复查、整层技术验收均完成；**CT工作层v1已工程收口，受限范围仍为未知，不声称100%物理孔恢复或新增整层人工像素批准**。用户新增授权：先将当前CT收口版本提交并推送GitHub，再全面复查AA／POLY／CT的流程与协作状态。当前准备同步上一远端b9a1683之后的实现、v2～v5和文档；推送后进入流程审计，不自动实施新层、新网表或大范围重构。

本文件是唯一实时入口。[收口页](docs/assets/ct-work-layer-final-v5/index.html)、[检查点](docs/checkpoints/2026-10-21-ct-working-layer-v1-closeout.md)、[阶段门](benchmarks/ct-work-layer-final-v5/stage-gate-v1.json)、[验收清单](benchmarks/ct-work-layer-final-v5/acceptance-checklist-v1.json)。已不需要重复四栅数量裁决或从头逐孔审批。[本轮审计前入口完整原文](docs/history/current-task-before-2026-10-21-workflow-audit.md)保留原状态。[上一入口完整原文](docs/history/current-task-before-2026-10-21-ct-final-v5.md)仅供历史查询。

## 本轮实质修改与保护

- 右上AA-F01804：原五条AI模板G06-P06～P10退休，完整记录保留；按原图四组栅端和五列源漏列，建立G06R-P01～P04四条规则POLY。五到四不存在可靠的一对一身份映射，未伪造旧ID别名。数量依据为AI原图复核，用户授权实施，不改写为新的人工点位标注。
- 新增33条CT＝8栅CT＋25源漏CT；上端引出继承R1B裁决，完整原图支持、固定5px方孔／3px孔距／1px包围和避让预算。当前[CT模型](benchmarks/ct-work-layer-final-v5/model-v1.json)10287条，AA334／POLY695；原10254条CT、原7044条已审记录在v4中的完整内容、全部334 AA和无关691 POLY完整不变。[保护检查](benchmarks/ct-work-layer-final-v5/preservation-check-v1.json)。
- 修复通用ct_transfer接续缺陷：材料别名由当前全部材料生成，后续无关局部修订不再丢失R2等既有合并映射。新增集成回归用例修复前失败、修复后通过；没有新案例生产脚本或调度器。
- 端口盘点：845个几何扩散区域，844个具候选CT；仅余AA-F01744边界片段无直接CT。POLY无当前CT仅V3_G1／G2两历史主体片段，保留旧端子关系；右上四栅及五列源漏区域已都有候选CT。数量不是器件数、准确率或M1连接确认。

## 明确保留的使用限制

[受限清单](benchmarks/ct-work-layer-final-v5/exceptions-v1.json)完整保存5个空间范围：两块小AA的来源对应不足、H1／H2长条的孔位无法可靠区别于亮带／拍屏纹理、一个照片边界器件片段。未补造孔、不认定物理无孔、不删未知；不能据此推断CT或M1接入。V3历史主体截段另列为表达例外，不算新漏孔。

[后续使用约束](benchmarks/ct-work-layer-final-v5/use-contract-v1.json)要求：源支持范围可接续分析；若走线触及受限范围，先回查来源或保留连接unknown；有新照片、可靠局部对应或相应追网需求时重新打开该范围。该约束是交接数据，本轮未新增强制执行的网络导出器。

阶段状态WORK_LAYER_V1_CLOSED_WITH_LIMITATIONS；engineering_closeout_complete=true、whole_frame_complete=false、overall_human_acceptance=false。原数量冲突关闭，不等于证据限制也通过。工作层已冻结，未宣称所有照片中的所有物理孔完整恢复；工艺、尺度、极性、真实W/L、阻值及真实PDK DRC/LVS仍未知。

## 继续保留的既有结论

旧Q1四管下端、Q2 U10下端共用POLY、Q3A上端与内环H3、Q3B/C对应，以及R1A/R1B上端／均匀源漏孔、R2本处连续AA单排孔全部继承。R2统一承载ID和旧材料别名保持；其他位置的近邻环隔离／非AA间隙不受影响。

C/D/F、143橙框、RIGHT6、宽MOS／环／电阻、Q2栅60孔、上方40栅、左侧局部、原661环孔及B孔数精度意见按原范围保留。R2_Q1、V3历史端子、网络v33、S03-03/04、18条电阻、W01电阻身份和195保留对象不改。AA-F00872退休，界面／邻片／照片外G67不补完整。原始8图和父冻结包不改。

## 验证与恢复／下一阶段

整层10287条几何PASS，重叠0、孔距违规0，最小边距4.4px；33新增来源对全部父记录检查3px争用无冲突。458项全量测试通过（19.57s）、65项相关测试通过（5.19s）、相关Ruff通过；父哈希、8原图、材料保护、别名、端口例外、页面资源／层开关检查通过。原图与规则图独立坐标，不做未经验证的投影。浏览器真实渲染未自动实测，几何／测试PASS不代替物理判断。

全幅按5860×4587设计画布展示，不沿用5712×4284照片尺寸；全部AA／POLY／CT覆盖检查通过，避免右侧／下沿预览裁切，几何不变。

- `.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-work-layer-final-v5/spec-v1.json --output runs/新的CT收口目录`：输出须不存在。CLI生成几何，阶段状态、限制与冻结结果见本版本收口包装；provenance仅审计，不原地重跑已冻结包。
- 相关测试：`.venv/bin/python -m pytest -q tests/test_ct_transfer.py tests/test_ct_joint_reconstruction.py tests/test_gate_terminal_localization.py`。`git diff --check`；data/不改，runs/和.venv/不入Git。
- 唯一下一步：先验证GitHub推送与本地HEAD一致，再复查AA／POLY／CT的方法、接口、质量门、接续保护、算法／AI／人工分工及三层联合状态；输出有证据和优先级的审计报告，不擅自修复审计发现或开始M1。
