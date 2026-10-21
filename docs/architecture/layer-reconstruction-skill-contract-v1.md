# POLY／CT skill 共用交付契约 v1

两个仓库skill分别承担POLY和CT的AI判断，共用现有联合模型与一个薄交付入口，不新增调度平台，也不替代block/case材料卡。原生照片是不可改证据，设计几何是可局部修订的全幅规则模型。当前路径从CURRENT_TASK获取，不能固化在skill内。

## 输入

`python -m silicon_eye.layer_review --request REQUEST --output NEW_DIR`，在项目根使用`.venv/bin/python`执行。请求由`layer_review.ReviewRequest`严格校验，额外字段被拒绝。示例见`configs/poly-skill-review-v1.json`与`configs/ct-skill-review-v1.json`。

- `schema_version=1`，`document_kind=layer_reconstruction_review`，`id`。
- `target_layer=POLY|CT`；`mode=inspect|revise`。
- `snapshot={path,sha256}`锁定当前`joint_layers`共同快照，不单独加载旧AA/POLY。加载时核对模型、预算、全部8图与裁决来源哈希。
- `authorized_ids={AA:[],POLY:[],CT:[]}`只是本次允许修改对象的操作范围，**不构成人工材料批准**；inspect不接受范围或更改。
- `changes`每项含`layer,id,before,after,reason,evidence:[{path,sha256}]`；新增before=null，删除after=null。精确旧记录必须相同，跨层修改一次应用后检查；不得靠修改预算/审查约束/未知绕过质量门。
- `windows`每项含安全文件名`id`、`layout_bounds=[l,t,r,b]`及`source_windows={aa:[l,t,r,b],poly:...,m1:...}`。必须在各自画布内。窗口是复核导航，不能作为材料边界；两类坐标不能混用。
- 可选`observations`引用既有`agent_observations`格式，继承`PhotoTask`、source、scope、candidate/unknown语义；只绑定并验证记录，不自动改几何，也不升级人工身份。格式继续使用`docs/agent-observations-v1.md`，不另造AI观察表。

新输入的身份判断和几何建模由Agent完成；本入口是已建立共同快照的复核/局部事务交付器，**不是图像识别算法或新照片自动重建器**。需要新建时先落实照片栈与AA/POLY对应，再进入同一契约。

## 输出与接续

新目录原子写入，已存在目录不覆盖；原图/父快照不改。

| 文件 | 含义 |
| --- | --- |
| request.json／delta.json | 原请求及逐ID前后变化，无变化时delta为空 |
| joint-report.json | AA/POLY/CT几何、来源争用、已审身份分别检查，网络导出始终关闭 |
| continuation-context.json | 原画布/照片坐标、锁定预算、阶段、全部人审/限制/未知/来源复查文档原样继承 |
| index.html、窗口SVG／PNG | 可切换AA/POLY/CT、未知范围和源图；旧/新并列；不伪造照片投影 |
| manifest.json | 锁定输入、关键执行代码与产物哈希、对象数和下一快照；可复核重跑 |
| joint-snapshot.json及两模型 | 仅通过硬门的revise生成，可用`joint_layers.load_snapshot`重载；inspect继续引用父快照，不复制全模型 |

`FAIL`保留拒绝诊断与提出的几何视图，**不生成候选快照**、next_snapshot=null，命令退出2。格式/路径/陈旧父记录错误在写入前拒绝，退出1。`REVIEW_REQUIRED`可生成带限制的候选，不算通过或可追网。PASS只证明实现覆盖的技术检查，不证明完整物理恢复。所有候选均未自动采用、未新增人工批准；更新当前任务/采纳候选须根据实际证据和任务授权。

算法或skill文档变化不会使材料结果失效。只针对具体失败范围提出事务；对比目标细节的源图证据与质量、其他对象不退化、六处未知/人审限制保留。真正改变旧裁决时先获得新裁决并建立新版本约束，不修改冻结父包来放行。

## 和现有接口的关系

`joint_layers.load_snapshot/write_snapshot/audit_joint`保留模型接续与联合门；`ct_transfer.apply_reviewed_record_changes`校验逐对象旧新及范围，统一交付只负责组装它们。AA局部修改是联合事务的伴随层，不改变AA skill的AI主导方法。block review入口仍服务case/材料卡/电路审批，不能伪造case来承载全幅层。

物理尺度、工艺、真实W/L与精确边界批准未知。相对design-rule检查与材料语义门互补，不能冒充真实PDK DRC/LVS。网络导出和新M1识别不在这两个skill内。
