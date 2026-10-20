# 中部MOS：48处人工确认与栅端诊断

2026-10-20。用户补充批准上一版全部48处橙色虚框作为CT，并要求评估栅极未可靠辨认的原因。

[更新复核页](../assets/ct-middle-mos-confirmed-v2/index.html)、[补充原话](../../benchmarks/ct-middle-mos-confirmed-v2/human-review-v1.json)、[锁定范围](../../benchmarks/ct-middle-mos-confirmed-v2/acceptance-v1.json)。

48个新增CT（24源漏＋24环）均明确以AA为落点，证据类型human_confirmation、algorithm_detected=false；不编造亮度峰/残差。原图中心只是原复核格点估计，不冒充人工精确点标。原1777条完整记录与AA/POLY材料不改，当前共1825孔。Q2本地共1034（654源漏＋380环）；旧661几何细节的保留意见未升级。原始橙框、批准前模型与台账保留。

全组几何门通过，纵向孔列的人审晋级保持column0/row槽位语义。429全套测试通过，相关Ruff和静态资源/切换验证通过；未自动实测真实浏览器渲染。[验证](../../benchmarks/ct-middle-mos-confirmed-v2/verification-v1.json)。

## 栅端问题的实质

[详细诊断](../../benchmarks/ct-middle-mos-confirmed-v2/gate-assessment.md)：栅极主体已经有30条POLY记录；上一轮51条取样路径全部AA，因此没有新增栅CT是流程未覆盖的结果，不能说成照片无法识别。现有POLY端部是候选范围和派生定位，不是精确接触区。原图下端亮边与真实孔需要专项区分，且上下端/侧向延伸未完整逐栅检查，也没有可靠局部M1反查。

本次仅确认48个AA检查槽位，不能据此确认栅CT。下一步应专项核查完整POLY端部及引出，再关联候选CT，必要时用可靠配准的M1交叉核对；不重跑已批准源漏和环，不因靠近POLY就改判栅孔。
