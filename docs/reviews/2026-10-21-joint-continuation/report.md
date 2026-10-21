# 三层接续与联合质量门实施记录

2026-10-21。承接用户“完成上述接续与联合检查”。本轮修改工具接口和检查，没有重新提取照片、改写冻结几何或增加人工批准；未提交或推送远端。

**结果：共同快照及AA／POLY／CT联合检查已经接通。当前全幅三层几何PASS；来源状态仍为REVIEW_REQUIRED，保留3处共16对旧来源争用。允许带限制接续局部工作，不允许据此宣称整层来源无误或自动全网放行。**

## 完成内容

| 项目 | 实现及验收 |
| --- | --- |
| 同一有效版本 | `configs/joint-work-layer-v1.json`锁定AA334／POLY695／CT10287、原8图、设计／原生坐标、相对预算、人工范围、5处原限制及新来源回查。旧AA337／POLY700仅作为历史，AA历史文件仅补来源定位上下文 |
| 引用接续 | 检查重复ID、别名冲突／循环／悬挂、错误层目标；在关系视图解析退休环编号，保留冻结原文。显式退休ID不能重新成为当前对象 |
| POLY合法结构 | G68桥仅对明确成员且实际相交的2对重叠放行；断开的成员仍失败，任意其他栅相交仍失败。G26以本栅宽度上的阶梯AA截面验证端部，不再错误使用共享AA整个外框 |
| 联合硬门 | AA正交、有效性及交叠＋POLY目标AA／端部／共享桥＋CT方孔／间距／承载／避让＋来源争用。局部CT修订即使修改AA／POLY，也必须先通过联合检查才写出 |
| 当前AA工具适配 | `joint_snapshot`选择最新AA记录，保留POLY／CT及限制；合并AA的多份来源观察分别保留，支持多块来源叠图，禁止把单一旧投影当完整合并对应。合并AA的图像细化仍须先给新局部对应 |
| 局部修订和后续重载 | `replace_layer`支持有范围约束的AA／POLY／CT修订；`write_snapshot`输出可重新载入的候选清单，来源限制与既有人审不丢。新清单明确是candidate，不继承成新的人工批准 |
| 来源门 | 在全量CT上检查同源帧、不同承载目标的3原生像素争用。新增／变更的争用拒绝；完全相同旧争用继续列REVIEW_REQUIRED，不能悄悄标PASS。该3px不是工艺最小孔距 |

入口代码：[joint_layers.py](../../../silicon_eye/joint_layers.py)。现有局部接口：[ct_transfer.py](../../../silicon_eye/ct_transfer.py)、[aa_layer_revision.py](../../../silicon_eye/aa_layer_revision.py)。当前POLY检查：[poly_closeout.py](../../../silicon_eye/poly_closeout.py)。

## 验证结果

- 全量软件测试：470 passed，69.76秒；最后补充输出路径预检及退休保护后，4项针对性检查通过（3.12秒）；相关Ruff通过。
- 两个已复现反例已成为入口回归：截短栅、扩AA使邻居交叠，都保持CT单层PASS，但联合检查FAIL，而且输出目录尚未生成。
- 合法结构回归：共栅桥通过、断桥失败、无关重叠失败；当前G26局部截面通过，无需调整已审几何。
- 当前全幅检查：AA无交叠、POLY无错误、CT孔距等规则通过；最小CT边距4.4px。5条POLY关系警告仍可见，不作为新材料事实或隐含网连接。
- 现有AA和CT入口各做一次不改几何的接续验证：全部334 AA、695 POLY和10287 CT对象记录逐条相同；未知、使用限制、人审和历史阶段记录完整保留；输出的共同清单均可重新载入。没有借此重新向用户提出已关闭问题。
- 对原8图及所有锁定输入复核SHA256，均未改变。无新增M1、网络或器件结论。

详见[机器核验](verification.json)、[全幅联合报告](joint-report.json)。这些是工程检查，不是实际PDK DRC/LVS，也不证明新芯片的Agent泛化。AA／CT no-op仅验证接续，未冒充一次识别质量提升。

## 来源热点回查与仍保留的范围

已重新查看3张原生坐标宽视野图。成对标记确实落在同一批亮特征上，说明两个目标不能继续把它们当作独立来源支持。仅凭这张层图，还不能判定应改哪一侧原生坐标、是否存在重复物理观察，或是否需要修订材料归属。因此没有删孔、移孔或改网；相关目标继续受限。

| 热点 | 数量 | 本轮处理 |
| --- | --- | --- |
| 中部MOS环／左侧共享环 | 9对 | 同一竖向亮点列重复引用；保持来源归属未知 |
| G34-P05／邻环 | 6对 | 同一横向亮点排重复引用；POLY与环身份需要可靠上下层局部对应 |
| 左下ROW4-AA3／AA4 | 1对 | 同一亮点附近重复引用；不凭邻近距离裁决扩散归属 |

[回查记录及全部IDs](source-reinspection.json)、[原始热点与图像证据](../2026-10-21-aa-poly-ct/report.md)。自动检测只能发现矛盾，不裁决物理身份。原5处来源限制和历史V3主体截段例外继续生效；原工程收口保留，新联合门未将其升级为无人复核放行。

## 使用及接续规则

在仓库内检查当前共同版本，输出必须是新目录：

```bash
.venv/bin/python -m silicon_eye.joint_layers --snapshot configs/joint-work-layer-v1.json --output runs/新的联合检查目录
```

CLI遇到FAIL退出1；PASS或REVIEW_REQUIRED退出0，具体采用必须读取JSON的`report.status`和`source_gate`，不能把退出0当作材料批准。`automatic_network_export_allowed`始终为false；本轮未实现网络导出器。

AA／CT的现有局部spec增加一个带SHA256的`joint_snapshot`引用。AA的`base`必须等于清单内当前materials；CT的materials、contacts、unknown_sites必须与清单一致。父孔预算不能放宽。旧历史spec仍能回放，但未指定共同清单时不代表接续当前版本。

- AA：当前入口支持已有对象的局部细化。分裂／合并／身份变化不能只改AA而遗留其他层引用，须通过显式材料before／after事务同步处理；多观察合并AA不得自动套用单个旧投影。
- AA／POLY关系几何调整可走现有CT局部修订接口的`material_changes`，不必重新提CT；只授权实际变化的ID，保留明确before／after及证据。纯层API为`replace_layer(snapshot, layer, records, authorized_ids)`。
- 输出`joint-snapshot.json`记录新的候选材料和CT引用；原阶段、use-contract和人审是继承上下文，不能当作新候选的批准。审阅采用后再更新当前入口指向；不覆盖冻结包。
- 各层修改完成必须做联合检查。新增来源争用／几何退化不能通过包装绕过；既有来源疑点始终随包保留。

可重放接续样例（不重新提取）：

```bash
.venv/bin/python -m silicon_eye.ct_transfer --spec docs/reviews/2026-10-21-joint-continuation/noop-spec.json --output runs/新的CT接续目录
.venv/bin/python -m silicon_eye.aa_layer_revision --root . --spec docs/reviews/2026-10-21-joint-continuation/noop-aa-spec.json --output runs/新的AA接续目录
```

## 下一步

共同版本与几何联合门已接通，可以保留这些产物继续局部工作。优先对上述3个热点准备AA／POLY／M1可靠局部对应，解决来源归属，再做一次带真实新证据的局部修订验收；仍无法判断时集中提交最少的人工问题。POLY／CT skill封装、完整复核包统一和独立Agent任务评测仍是后续工作，本轮没有声称完成。

前一轮审计报告是实施前状态；其F01／F02及F04对应接续部分已由本轮处理，F03、F05完整交付入口、F06独立Agent评测和F07维护问题未整体关闭。旧审计复现脚本依赖当时的实现；在当前已修代码上运行，结果会相应变化，不能与原审计证据直接等同。
