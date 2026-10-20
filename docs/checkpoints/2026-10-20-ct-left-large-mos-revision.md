# 左侧CT：分项审批及局部修订v2

用户已逐项反馈A–F，并补充确认A是阶梯最右G25/G26共享源漏。保留[原话与范围](../../benchmarks/ct-left-large-mos-revision-v2/human-review-v1.json)。

[新页面](../assets/ct-left-large-mos-revision-v2/index.html)只请复核A/C/F；E显示已批准修订的执行结果。每卡保留前版联合图、原图、标记原图和独立坐标M1，可查看专项宽视野原图。

## 执行与批准边界

- **A**：人审确认同一阶梯组G25/G26共用扩散，保留右侧两条环的隔离。两条AA在有效模型合并为AA-LEFT-STAIR-SHARED-56；旧AA5/6作为别名及完整父记录保留。G25/G26的AA目标和相关23条CT记录局部调整，源图证据不改。G26主体宽40→30、中心左移15；共享CT列位于两栅之间，短栅右侧扩散保留。共享区域只记录源/漏未指定，不命名新net。
- **A左宽MOS**：照片中是裁剪残片。原AA宽280.53相对单位，而POLY宽116；保留右侧邻接关系，将AA左界收至393，得到约132.67宽；POLY下端1636→1681.3986覆盖AA下端，左边继续标为观察范围。原照片范围不改，不声称物理左端点。新增右侧6个源漏候选及8个上端栅候选；G26上端新增2个栅孔。A精确新形状仍待审。
- **B**：用户批准连接关系，指出个别源漏多孔、栅孔少孔但不影响结果。455个显示候选原样保留；标为关系级通过/逐孔细节保留意见，不偷换为逐孔精确真值。
- **C**：用户确认上下两条外端亮带是环，中间两条是MOS栅。保留环与源漏，给上排5条宽POLY下端及下排5条宽POLY上端分别增加237个实测候选。没有据此自动宣布5条栅同层连在一起或建立net。新CT精确位置/数量待局部复核。
- **D**：373个显示候选通过，原样保留。这里按显示窗口裁剪范围锁定，窗口外不延伸批准。
- **E**：执行原展示并获批的AA-W04右缘989→995，恢复原方案29个右端源漏孔。孔的原图证据与原方案完整相同，不重复审批。
- **F**：第2栅补2孔，第3栅补另一孔并将已有单孔按双孔相位左移6相对px。三个新孔由邻栅相位和实际局部灰度/残差支持，阈值185/16；证据类型context_seeded_2d_patch_support_not_independent_peak_count、algorithm_detected=false，保留弱信号身份。没有按数量虚构强峰。

## 有效快照与复现

[CT候选](../../benchmarks/ct-left-large-mos-revision-v2/model-v1.json)、[材料候选](../../benchmarks/ct-left-large-mos-revision-v2/material-model-v1.json)、[逐记录前后台账](../../benchmarks/ct-left-large-mos-revision-v2/ledger-v1.json)、[分项批准](../../benchmarks/ct-left-large-mos-revision-v2/scoped-acceptance-v1.json)。分项文件锁定只表明证据快照固定，不代表4940条CT全部获批。

新增285：A16、C237、E29、F3。完整候选4940，旧4631条完整记录不变，24条只在授权局部修订；原2709已审基准逐记录完全不变。有效材料695个POLY、335个AA；AA数量减少是共享区域合并，不是MOS数量减少。692个无关POLY和332个无关AA记录完全不变。

复现：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-left-large-mos-revision-v2/spec-v1.json --output runs/新的左侧CT局部修订目录`。

新增通用的局部前后记录接续入口，明确检查授权ID、父记录一致及旧源证据不变，失败即拒绝写出；沿用既有测量、方孔、包围、间距与联合图工具，不重跑B/D或全幅提取。

## 验证与下一门

4940孔整组几何PASS：重叠0、最小间距违规0，AA/POLY包围与沟道避让通过。442全套测试、相关Ruff、源/父哈希与静态资源/模拟切换通过；A/C/F规则预览已目视检查。真实浏览器渲染未测，实际工艺DRC、M1/net与全幅完整性仍未知。旧661孔细节意见保持。

下一门只复核A共享AA及宽MOS匹配、C新栅CT、F三个补孔及双孔相位；B/D不重新审批，E按已批方案执行完成。

## 验收追记：A／C／F合理批准

2026-10-20，用户逐项确认“A：合理批准；C：合理批准；F：合理批准”。[本次原话](../../benchmarks/ct-left-large-mos-revision-v2/human-review-v2.json)、[最终分项状态](../../benchmarks/ct-left-large-mos-revision-v2/scoped-acceptance-v2.json)、[验收锁定](../../benchmarks/ct-left-large-mos-revision-v2/acceptance-v1.json)。上文待审描述保留为生成时状态；当前这三项已通过，不重复审批。

锁定4940孔工作快照、695 POLY与335 AA及变更台账，模型和原图观察记录不重写。B连接级/孔数意见、旧661几何细节意见、未知检查空位和F弱信号身份保留；不静默升级其他继承候选，不自动确认C跨5栅共栅、M1或net。

本次仅写入人审状态与锁定文件；既有442测试结果不重跑，核对全部原锁定哈希、2709已审记录和静态资源链接。下一步按既定顺序处理中下部尚未覆盖的MOS CT，本轮结果作为接续和防退化基准。
