# CT工作层v1工程收口：四栅补齐、受限范围复查、整层技术验收

用户授权“完成这三项后收口”。[工作层页面](../assets/ct-work-layer-final-v5/index.html)已生成同一模型的全幅AA／POLY／CT／未知开关、12个抽查窗口、四栅前后比较、原图观察及受限范围表。三项工程任务完成，没有新增必须由用户逐孔裁决的问题；未把证据不足改写为物理孔全部恢复。

## 1. 四栅及CT局部修订

原图四组上端栅亮条与五列源漏CT支持四栅结构，旧G06-P06～P10是五条未审AI模板。全部旧记录在[退休台账](../../benchmarks/ct-work-layer-final-v5/retired-material-records-v1.json)保留，新建G06R-P01～P04，不伪造五到四的一对一身份别名。AA-F01804不动，普通矩形栅等宽、等距、正交，四栅分出五个扩散区域。

新增33条CT：四栅上端各2条，共8条；五列源漏各5条，共25条。原始取峰窗口、灰度／残差及源坐标保存在[观察表](../../benchmarks/ct-work-layer-final-v5/optical-observations-v1.json)。阈值205／20未降低，不以格点补没有来源支持的孔。引出侧继承已确认R1B；四栅数量来自AI原图复核，用户授权实施，未改写为新的人工点位或像素批准。

当前10287 CT、334 AA、695 POLY。v4原10254条CT完整相同，原7044已审记录在v4中的内容完整相同，全部334 AA、无关691 POLY完整相同。新增栅仅跨对应AA，不触及其他AA／POLY，正好形成五列扩散窗口；[保护检查](../../benchmarks/ct-work-layer-final-v5/preservation-check-v1.json)。

## 2. 剩余来源限制复查及处置

受限范围均保留于机器可读[例外清单](../../benchmarks/ct-work-layer-final-v5/exceptions-v1.json)，保持空间范围、原材料ID、证据引用、重新打开的条件；没有把“已复查”写成“孔已确认”。

| 范围 | 本轮检查与结论 | 使用边界 |
| --- | --- | --- |
| AA-F01951／AA-F01952 | 回查AA模型旧全局定位及AA／POLY照片，旧投影不足以独立建立两个小AA与照片的对应；无已知相关栅端 | 保留AA候选，CT不恢复；不借邻近环亮点 |
| H1／H2长条 | AA及POLY上沿可见亮带；局部孔不能与连续亮边／拍屏纹理可靠区分，H1部分贴照片边缘；M1连续不能证明介质接触孔 | 保留CT未知，不推断M1接入或物理无孔 |
| AA-F01744边界片段 | 既有端口调查的照片定位超出当前图像，现有照片无法补全 | 保留端口未知，不虚构完整器件 |

V3_G1／V3_G2另外作为历史主体截段例外处理，其旧局部端子／案例记录仍可回查，不是本轮新发现的两个漏孔。845个重建扩散区域中844个有候选CT，剩一个为上述AA-F01744；仅两个V3主体片段没有本模型直接CT。该统计不是器件数、漏检率、准确率或实际金属接入确认。

上述5个空间范围仍是开放的证据限制。它们没有待强行补齐的槽位，也不需要重复逐孔审批；有新图、可靠局部对应或新走线需求依赖该范围时再打开。[后续使用约束](../../benchmarks/ct-work-layer-final-v5/use-contract-v1.json)明确不得根据这些范围推断CT／M1连接；当前未实现一个自动强制此约束的新网络导出器。

## 3. 整层验收和接续问题修复

[整层技术验收清单](../../benchmarks/ct-work-layer-final-v5/acceptance-checklist-v1.json)核查了四栅结构、全CT几何、父记录保护、来源争用、材料别名、端口例外和受限范围。旧R1A／R1B／R2／Q1／Q2／Q3等已审结论继承，不重跑无关区域。

发现并修复通用ct_transfer接续缺陷：原alias_map只收集本次修改对象，下一次无关局部修订会丢失旧材料合并映射。现在从当前全部有效AA／POLY对象收集别名，R2和左阶梯共享AA等别名持续可解析。新增真实局部执行的回归测试：修复前失败、修复后通过，验证后续增加无关POLY时旧AA别名及CT不丢失。没有新增生产案例脚本或调度器。

验证结果：

- 整层10287条CT几何PASS，重叠0、孔距违规0、最小边距4.4px；固定5px方孔／3px孔距／1px包围及避让预算不降。33个新增来源对全部父点检查3px争用，无重复或冲突。
- 全量458项测试通过（19.57s），相关65项通过（5.19s），相关Ruff通过；父冻结文件与8张原图哈希、全部保护范围及别名检查通过。
- 页面本地资源、SVG／PNG和12个窗口检查；图层数量与模型一致。四栅原图／规则PNG及全幅图目视检查。浏览器真实渲染未自动实测；软件通过、几何通过、AI对应判断、人工物理批准分别记录。

全幅显示另做[画布覆盖检查](../../benchmarks/ct-work-layer-final-v5/canvas-coverage-check-v1.json)：设计画布为5860×4587，照片为5712×4284，两者不可混用。收口页使用设计画布，全部AA／POLY／CT被覆盖；修正旧预览沿用照片尺寸造成的右侧／下沿裁切，只改显示边界，不改已有几何或来源坐标。

[阶段门](../../benchmarks/ct-work-layer-final-v5/stage-gate-v1.json)：WORK_LAYER_V1_CLOSED_WITH_LIMITATIONS，engineering_closeout_complete=true。原数量冲突已解决，本轮无待人工重复裁决事项。**whole_frame_complete=false、physical_all_CT_recovered=false、overall_human_acceptance=false**：工程收口不改写开放证据限制，不代表100%物理恢复、新增整层人工像素批准或实际PDK DRC/LVS。新M1／net、极性、真实尺寸、阻值等未生成。

## 恢复与下一阶段

`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-work-layer-final-v5/spec-v1.json --output runs/新的CT收口目录`生成几何；收口包装另附验收、限制和阶段状态。所有输入哈希锁定，[冻结清单](../../benchmarks/ct-work-layer-final-v5/freeze-manifest-v1.json)保存工作层与展示资产。provenance为此次审计配方，不是新生产案例接口或CT skill，不在冻结目录重跑。

本轮未提交或推送GitHub。任务入口与README修订前原文分别完整保存在[任务归档](../history/current-task-before-2026-10-21-ct-final-v5.md)及[README归档](../history/2026-10-21-before-ct-final-v5-README.md)。CT工程阶段收口，下一阶段可讨论M1重建及其质量门，本轮不自动启动新层。
