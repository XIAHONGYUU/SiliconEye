---
name: silicon-eye-aa-reconstruction
description: Recover and review AA material candidates from Silicon Eye chip photographs using representative scribbles, multiple segmentation methods, and AI contextual judgment. Use for AA extraction, disagreement review, or scoped material revision; output includes unknown regions and human gates, not automatic full-chip GDS or CT recovery.
---

# Silicon Eye AA reconstruction（实验版）

支持项目中的AA材料候选与复核。尚无全幅生产验收；交互Agent承担AI材料判断，不声称脚本自动理解器件。先定位含silicon_eye/、CURRENT_TASK.md的项目根，遵守当前授权与既有裁决。

## 根据当前证据接续

- 没有材料样本：看原图及宽上下文，选少量AA/非AA明暗笔画，身份先记candidate。保留未知与替代解释；新笔画不得追溯记为human_confirmed。
- 有样本但候选不可靠：复用颜色/纹理RF、结构RF与GrabCut等现有工具，控制训练信息预算，检查窄间隙、暗AA漏空与非AA误报，不只选最好分数或最好种子。
- 多方法有分歧：同一原生坐标并列原图、候选和分歧。AI结合器件/整体结构与已审事实复核；同源算法一致不等于正确，不简单投票或并集融合。
- 有已审语义但边界不清：有源图边界证据才修订；边界不确定则保留unknown，不按问题框裁切。适用横向带状结构时，可用现有边界定位工具，见[工具契约](references/tool-contract.md)。该工具不能处理任意AA形状。竖环/台阶/折线可在有粗结构先验时走同一契约中的多方法形状验证路径，不能把旧轮廓直接填成新结果。
- 要扩展范围：先选不同窗口，冻结输入、假设与失败条件，再执行；没有该窗人工材料真值时只交付候选，不报准确率。不要把已调过的窗口称为盲测。

## 会改变判断的结构经验

电阻内部非AA与外围AA环必须分别识别，排除内部误报不能误删环。暗AA内部纹理不是自动缺口；真实非AA间隙不能因平滑连片而消失。很窄的未知过渡带也可能包含第二条邻近环，应核查结构条数，不把留unknown当成完整性通过。环、重复结构和正向设计经验帮助解释照片，不能替代本图证据或未知工艺的数值规则。不为“通常如此”补出环、连接或精确边界。

原生照片可倾斜；先定位材料，再进入后续正交几何阶段。AA、poly与CT身份/归属分开，本skill不推进CT、其他层完整重建或走线。

## 数据、质量门与交付

复用项目既有JSON/ID/CLI，不写案例坐标专用脚本。原始照片不改；输出新目录，锁定来源/参数/代码/裁决，保留旧报告。记录AI判断、固定算法、人工裁决各自的责任。样本批准、区域语义、精确边界、完整mask分别升级。

像素状态明确保存 `-1未知、0候选非AA、1候选AA`，另存有效/处理范围；未处理或未知不能算背景。框边延续不是实际断点；局部候选不当作全幅版图。

质量检查依次覆盖：来源/坐标 → 样本冲突与训练检查分离 → 已审中心错误/未知 → 区域内部覆盖/真实间隙/外围环保留 → 精确边界。中心全对仍需要区域复核；未知计数单列，不用unknown提高正确率。无边界证据时停止该部分修订并给出宽上下文，而不是填平。

一次性交付可查看的原图/前后候选、未知区、AI假设和编号核查清单，集中请求影响下一步的判断。完整材料与边界批准前，停止正式几何/CT更新。软件测试通过不等于图像真值通过。

## 项目参考与限制

只按需读取[工具契约](references/tool-contract.md)中的横向带状或粗先验形状路径。更完整的方法设计在项目 `docs/architecture/aa-extraction-workflow-v8.md`；历史例子在 `benchmarks/aa-*`，不可将它们的坐标当新图默认值。

本仓库skill尚未安装到全局发现目录；可在当前对话按明确路径读取执行。此实验版经过同一Agent的S05开发回放、S02迁移及竖环/台阶/折线粗先验回归，S02材料关系、S05两环局部位置/间隙以及V01/P01/B01新候选整体合理性已审，逐像素边界、未建模范围和全幅仍未审，不声称独立Agent评测或新芯片泛化。调用本skill不附带Git提交/推送、外部模型服务或自动安装授权。
