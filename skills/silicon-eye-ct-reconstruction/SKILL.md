---
name: silicon-eye-ct-reconstruction
description: Reconstruct and locally revise regular CT cuts from Silicon Eye photographs using source correspondence and joint AA/POLY bearing identity, with scoped human review and regression protection. Use for gate, diffusion, guard-ring or resistor contact recovery; not via-layer extraction or automatic M1/network inference.
---

# CT重建

仓库内v1，人机协作。定位项目根，先读`CURRENT_TASK.md`与其当前共同快照；携带已有AA/POLY、CT、照片哈希、相对预算、批准范围与未知接续，不能重建一份孤立CT层或重复索取已审结论。

## 判断与执行

1. **确定承载材料再找孔**：分别识别源漏AA、环AA、栅端/电阻POLY及共用POLY。CT照片亮点不是材料分类器，不能按“最近AA”分配归属。M1只辅助定位/解释引出，不凭M1连续证明孔或电连接。
2. **锁定本图对应**：并列源图宽上下文、AA/POLY、CT候选。设计位置与原生亮点分开记录；若邻近几列互相借用了亮点，先检查对应关系，不能靠平移设计图掩盖。配准未验证时不直接投影，更不能用固定行搜索替代端子身份判断。
3. **规则重建**：使用快照当前相对预算检查正交方孔、最小间距、包围、沟道净距。沿同一环/阵列保持有依据的尺寸与节距规律，例外须有来源；规则和峰值算法只是候选工具，不补未经观测的孔，不为规律抹掉真实开口。数量精细误差与连接身份错误分别报告。
4. **跨层修订**：已确认的共用栅引出可要求局部POLY桥或端部微调，必要时修AA；须有证据、精确before/after和影响ID，最后一次性联合检查，不能先采用暂时失配的层。共用桥须实际连接成员。保留退休身份；几何合理不能推翻人工材料归属。
5. **保留未知并交付**：未独立观测到源漏CT，不等于缺孔或无孔；不借用附近栅CT、不自动补孔。按[共用交付契约](../../docs/architecture/layer-reconstruction-skill-contract-v1.md)执行；只重算相关对象/依赖，交旧新模型、源图窗口、变化记录、全部继承限制、联合门及必要的新问题。

原图/冻结基准不改。新图无共同快照时先建立来源和坐标、AA/POLY候选，现有交付命令本身不做识别。全幅层不能按审查窗口裁断；不用重新逐孔人审代替接续。精确孔轮廓仍可为候选；不把工程收口、软件PASS或无来源争用说成100%物理孔恢复、真实工艺DRC或网络确认。未知只阻塞依赖它的范围。

## 工具与验证范围

统一入口`.venv/bin/python -m silicon_eye.layer_review --request REQUEST --output NEW_DIR`消费当前联合快照；`ct_transfer.apply_reviewed_record_changes`执行定点事务，`joint_layers.audit_joint`独立检查AA/POLY/CT几何、来源争用和人审身份。`ct_transfer`旧spec不是所有事务的通用CLI，不把函数级历史spec直接喂给它。局部峰值/行拟合可复用`ct_transfer`与`ct_joint_reconstruction`工具，由AI检查孔列归属。

按需读[CT方法记录](../../docs/architecture/ct-reconstruction-workflow-v1.md)，历史预算不能替换当前预算。交付格式与候选重载见[契约](../../docs/architecture/layer-reconstruction-skill-contract-v1.md)，评测边界见[封装验证报告](../../docs/reviews/2026-10-21-poly-ct-skills.md)。调用不附带M1/全网点亮、外部模型、Git推送或全局安装授权。
