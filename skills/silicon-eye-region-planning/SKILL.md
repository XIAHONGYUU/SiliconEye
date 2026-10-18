---
name: silicon-eye-region-planning
description: Build qualitative device-region observations and evaluation references from multilayer Silicon Eye photographs, consult process documents, and produce layer-switching human review pages. These annotations support understanding and evaluation; full-frame layer reconstruction and network tracing keep their own spatial scope.
---

# Silicon Eye 区域规划

交付粗区域观察图、类别表及可切换源层的复核页，服务于整体结构理解、验证与 Agent 效果评估。AI 观察与推理，脚本校验来源/坐标并出图，人工处理关键类别和范围；分类先为候选。当前是交互式工作流，新增样本的物理正确性仍需复核。

## 与全幅抽取的边界

区域编号是观察/评测索引，不是材料层、器件实例或网络边界。分层复原以完整源视野生成连续材料图层；不按这些框裁割输出、不以器件类别决定跳过像素，也不在框边停止连通遍历。局部窗口用于放大和抽样检查。dummy AA/M1 等角色不改变其材料身份，不据区域类别直接删掉材料。

## 进入与输出

读取当前项目的 CURRENT_TASK.md 和适用 AGENTS.md，使用项目根与环境，不依赖某次聊天、机器绝对路径、固定八层数量或固定区域答案。

输入应有源帧路径、SHA-256、层标签依据、原生尺寸/坐标及输入质量/可用性说明。已有标准照片栈时直接使用。来源或可用性不明时先做最小输入核对；同尺寸不表示同位置。未知尺度可继续用 px，未验收配准不阻断独立原生区域观察。

输出数据与辅助脚本字段见 [区域记录与复核合同](references/contract.md)。保留原图，派生结果写新目录。复用既有区域编号；新对象不按图层或绘图次序改名。

## 判断与回查

- 先看完整视野，再看足够宽的局部，并综合相关层。划分 MOS、电阻、电容、互连及不能解释的结构；按需要区分 dummy、衬底/接触环、测试结构、界面遮挡和混合区域。不要为填满画面强制分类。
- 分开记录器件结构、用途、材料角色和视野有效性。MOS 可采用电容接法；dummy AA 和 dummy 金属是分层角色。形似环或矩形不足以确定器件或电极。
- 工艺概念不明时，按当前项目 `docs/reference/pdk-recognition-guide-v1.md` 和其官方来源索引回查相关章节。若项目无该索引，按当前问题查官方 PDK 的 layer/device/LVS 章节并登记出处。类比用于解释和补查，不直接套用未知芯片的最小尺寸、层号、方阻和电容密度。
- 框是原生粗观察窗，不是精确材料边界。每层独立定位，跨层对应未验证就注明假设，不复制 bbox 或做伪配准投影。框外是未分类，遮挡未知不等于材料不存在。
- 记录候选、替代解释、证据与下一检查；不可辨认时明确 unknown。没有器件归并证据不统计器件数，也不新增端口短接或电气连接。

## 生成与复核

冻结首次观察记录，再用项目 Python 调用本 skill 附带工具：

```bash
python SKILL_DIR/scripts/build_review.py --root PROJECT_ROOT --plan PLAN.json --output NEW_DIRECTORY
```

将 SKILL_DIR 替换为当前加载 skill 所在目录；在现有项目虚拟环境内运行（需 Pillow）。工具只处理 JSON、来源及图稿，不调用视觉模型或修改分类，已有输出拒绝覆盖。

确认页面有全部源层选项、原生全图、宽局部、状态/依据表和原图链接。工具检查不等于浏览器行为或物理分类通过；浏览器受策略限制时保留该限制，用静态图交付，不绕过。

提供按编号一次性回答的完整清单，集中询问会影响下一阶段的差异；不要求逐 CT 批准。复用已有人审，不重新询问其批准范围。支持“一页切换不同层”，不要求把各层预先投影成同一坐标。

保存人工原话、原候选版本及修订，分类、数量、精确几何和连通分别升级。用户只确认某层语义却未给定位时，记录已确认语义与未定位，不猜位置。重导出有效分类并保留历史入口。

## 验收与交接

验证来源哈希、坐标边界、引用/编号一致性，检查图稿可读性。软件检查、Agent 分类效果和人审结论分别报告。同芯片已见图像或已知答案的重放是开发回归，不称独立盲测。

交接时给出整体观察、支持层、类别依据、状态、未知及评测参考；不指定按器件区域切割分层抽取或网络数据。只在当前任务授权范围更新任务入口，不自动提交/推送或调用外部付费模型。
