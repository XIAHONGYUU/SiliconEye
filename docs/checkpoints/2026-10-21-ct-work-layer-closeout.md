# CT工作层全幅收口：进入新增来源裁决门，尚未整层定稿

用户授权继续三项工作：来源问题清理、全幅AA/POLY/CT联合候选、整体验收与工作层冻结准备。本轮已完成技术调查、全幅候选和最终质量初检；来源门发现新实质问题，最终人工验收与正式工作层批准仍待R1A/R1B/R2，不能宣布三项全部通过。

[统一复核页](../assets/ct-work-layer-closeout-v3/index.html)置顶新问题，提供宽视野POLY原图、独立坐标AA参考、规则图、同一全幅模型的AA/POLY/CT/未知开关及分块抽查。旧Q1/Q2/Q3已裁决关系继承，不重新索要逐孔批准。

## 来源清理的实际结果

[8条旧轨迹调查](../../benchmarks/ct-work-layer-closeout-v3/source-reinspection-v1.json)：F01648按左侧可见范围重定位新增1条候选；Q3B环11条、Q3C环5条；复杂环两侧按新独立区间重取106条，中段仍有近邻环归属未知，未声称整段通过。F01951/52两小AA仍缺独立材料来源，H1/H2长AA条的孔位不能从连续亮边／拍屏纹理可靠分开，不自动补孔，也不宣称物理无孔。旧错误轨迹退休，原观察完整保留；旧8条清单不等于8条全部物理恢复。

反例进一步暴露U10环四边、相邻G61环上边和TOP-STEP-1一段的未审定位问题。按完整受影响配方撤回33条未审记录，独立重取，不仅删冲突点保留错误路径余段。全部材料记录和此前7044条CT在v2中的完整记录保持；不重新提取已批AA/POLY，不扩大原人工范围。

[零散20条观察处置](../../benchmarks/ct-work-layer-closeout-v3/residual20-disposition-v1.json)保留原观察和原因：不支持的观察退休，其余由局部端口／环复查替代，而非把旧孔位全部释放。有明确照片支持才产生新候选。

另5条未审CT仅纠正照片来源并保留before/after：G63邻近源漏1条、G66源漏2条和末指上端2条；设计、ID和目标不改。新／重定位来源不因顺序竞争自动变成人工真值；[新增观察不同目标3px内争用检查](../../benchmarks/ct-work-layer-closeout-v3/source-ownership-check-v1.json)通过，但不表示原有所有来源逐点真实。

## 全幅候选与端口证据

当前10226条工作记录＝原10025－撤回33＋新增234；原9987条完整不变，5条只改来源。335 AA和696 POLY对象完整不变（包含上轮已补的U10共用端）。234条为AI候选，数量不是物理确认孔数或器件数。[前后保护检查](../../benchmarks/ct-work-layer-closeout-v3/preservation-check-v1.json)。

新增通用audit_terminal_access盘点：依据已声明AA/POLY关系分解扩散区域，再按同一AA目标匹配CT；普通内部扩散没有CT不判为失败，也不补孔。明确共用POLY桥只有与成员有真实几何交叠才传递候选接入；不凭声明或附近CT借用端口。25px²仅为盘点过滤小碎片的像素参数，不是工艺规则。

846个重建扩散区域中，初查33个没有直接CT记录，经原图支持新增26个区域候选，剩7个保持无直接CT证据（1个定位出照片、6个受限局部检查未见可靠支持）。内部区域可能无孔，该数字不是7处漏检或99%召回率。696 POLY材料只有2个V3主体截段没有本模型直接CT，已审历史端子关系原样保留；也不能把696算MOS数量。[端口表](../../benchmarks/ct-work-layer-closeout-v3/terminal-access-v1.json)、[摘要](../../benchmarks/ct-work-layer-closeout-v3/access-summary-v1.json)。

## 最终门为何仍HOLD

- R1A：左上G01/G02长排的旧栅CT取点可能落在源漏列或环上，需要确认真实引出侧与一处源图栅端锚点。
- R1B：右上G05/G06同类问题须独立确认，不套用左侧或旧Q3的方向。
- R2：上部内环下边A与近邻外环上边B的光学亮带归属不清，需要A／B／各有一排或保留未知的裁决，不能用同一亮点接两环。

[机器可读阶段门](../../benchmarks/ct-work-layer-closeout-v3/stage-gate-v1.json)为HOLD_new_source_correspondence_and_overall_acceptance。模型列出相关待复核CT ID，禁止直接作为全层通过的追网输入。最终冻结的是[待审候选快照](../../benchmarks/ct-work-layer-closeout-v3/freeze-manifest-v1.json)，human_accepted=false、whole_frame_complete=false，不是已批准CT工作层。没有新M1/net结论，没有真实PDK DRC/LVS。

## 验证与恢复

原5px方孔／3px最小孔距／1px包围及避让预算不降；10226条几何PASS，重叠与孔距违规0、最小边距4.4px。457项全量测试通过（18.72s），64项相关测试（4.97s）和相关Ruff通过，实际CLI执行成功。所有父输入及v2锁定JSON哈希验证、86条资源链接／SVG／PNG解码、15个选择器和4个层开关模拟检查通过；全幅、R1A/R1B、R2及U10 PNG目视检查。浏览器真实渲染未自动实测，软件与几何结果不替代来源身份判断。

复现：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-work-layer-closeout-v3/spec-v1.json --output runs/新的CT工作层目录`。provenance保存本轮审计配方，不是新生产案例脚本或CT skill；最终包装附阶段门、端口表、全幅开关、来源问题和冻结清单。不原地覆盖已冻结版本，本轮没有GitHub推送。
