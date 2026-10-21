---
name: silicon-eye-poly-reconstruction
description: Reconstruct or locally revise regular POLY geometry from Silicon Eye multilayer chip photos, jointly checking AA channels, terminal leads, resistors and CT. Use for POLY recovery and scoped continuation of reviewed layouts; not metal tracing or automatic transistor/netlist confirmation.
---

# POLY重建

仓库内v1，人机协作。定位含`CURRENT_TASK.md`与`silicon_eye/`的项目根，先读取当前任务所指共同快照、批准范围和未知；历史文档的数量、坐标与预算不能覆盖它。封装不使既有结果失效，不默认重跑全图。

## 判断与执行

1. **接续或新建**：有共同快照则接续；复核视窗只是导航，材料保持全幅连续编号。新输入无快照时先建立照片来源、层名、可见范围、原生坐标及设计坐标，再形成候选；现有交付工具消费已建立的快照，不会自动识别新图。
2. **先认结构**：POLY照片包含AA信息。结合AA照片中的沟道暗线、POLY照片的连续轮廓、端部亮条以及CT/M1上下文。MOS须有合理的AA交叠与沟道两端延伸；电阻可以没有AA，不能强行补AA来通过MOS检查。AA环与栅引出分开。
3. **再重建几何**：源图可倾斜、拉伸，设计图保持正交、同阵列规则。普通栅通常用矩形，不为放孔习惯性做狗骨形；宽栅、共用端部与引出必须有本图依据。两栅经M1相连不等于POLY相连；已确认的POLY共用端必须实际接触各成员。
4. **局部修订**：算法仅辅助具体边界/亮点，不强制生成mask或重采样。照片不匹配时优先检查局部对应与阵列间距，再以跨层证据微调AA/POLY；不能只修本层使图好看。保留稳定ID；身份改变须显式退休/新增、同步引用，不把不同对象强行别名合并。
5. **联合检查与交付**：按[共用交付契约](../../docs/architecture/layer-reconstruction-skill-contract-v1.md)生成inspect或revise请求。几何、来源、已审身份分别检查；比较旧/新及未变化对象。硬FAIL只交拒绝诊断，不接续失败几何。关键新歧义才集中请人裁决。

原图与历史冻结包不改；无来源的规则化补全不允许。工艺/尺度未知时使用快照锁定的相对预算，不能声称真实PDK DRC通过。精确边界候选、未知接入和已确认身份分开；未知不是非材料或不连接。当前skill不授予追M1、导网表、推送GitHub或全局安装权限。

## 工具与验证范围

现有`poly_closeout.audit`与`joint_layers.audit_joint`负责固定检查；`poly_closeout.run`是历史构建入口，不能当作当前接续入口。统一命令为`.venv/bin/python -m silicon_eye.layer_review --request REQUEST --output NEW_DIR`。具体结构与限制见[契约](../../docs/architecture/layer-reconstruction-skill-contract-v1.md)，只按需读[POLY方法记录](../../docs/architecture/poly-reconstruction-workflow-v1.md)，其中历史参数须服从当前快照。

AI负责判断，脚本不新增身份事实；程序PASS不替代人审，也不证明完整物理恢复。版本测试范围查[封装验证报告](../../docs/reviews/2026-10-21-poly-ct-skills.md)。
