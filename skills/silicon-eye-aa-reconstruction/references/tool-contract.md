# 工具契约与恢复

在项目根使用 `.venv/bin/python`，先读CURRENT_TASK并检查原图/已审状态。以下命令均要求新的输出目录；SPEC和NEW_DIR是任务决定的实际路径，不把历史例子当新图输入。

AI先直接识别材料与结构，再决定是否调用下列算法工具改善具体细节；工具目录不是必经流水线。A直接路径可复用现有几何生成/渲染代码，不必先跑RF或生成稠密mask。完整方法见项目docs/architecture/aa-extraction-workflow-v9.md。

## 复用工具

| 意图 | 现有模块 | 适用边界 |
| --- | --- | --- |
| 全幅矢量层接续与明确范围修订 | silicon_eye.aa_layer_revision | 固定模型/逐对象来源/显式变化域；不是全图识别模型，详见[全幅验证](full-frame-validation.md) |
| 简单阈值/全局样本RF/GrabCut探索 | silicon_eye.aa_segmentation_eval | 训练/开发窗口信息必须分别标注 |
| 局部人审中心提示 | silicon_eye.aa_prompted_eval | 原中心身份需锁定裁决；采样邻域不是自动已审 |
| 颜色/纹理/方向结构消融 | silicon_eye.aa_texture_eval | 同提示不同特征，已见开发窗口不称盲测 |
| 多明暗笔画、多算法对照 | silicon_eye.aa_scribble_eval | 笔画与检查中心避让，新增笔画candidate |
| 同坐标分歧与上下文复核 | silicon_eye.aa_context_review | 当前历史复核渲染器含S03/S05展示限制；不能直接当通用全图入口 |
| 粗形状先验下的竖环/台阶/折线验证 | silicon_eye.aa_shape_validation | 需旧粗轮廓或明确AI候选，非自主发现形状 |
| 已审语义下的源图边界定位 | silicon_eye.aa_semantic_revision | 仅有明确上下顺序、近横向的局部带状结构 |

通用命令形态：`.venv/bin/python -m 模块 --root . --spec SPEC --output NEW_DIR`。模块均有 `--help`，按实际匹配的实验文档与锁定spec格式创建新任务，不要求每次依次执行所有模块。

## 带状局部修订协议

`aa_semantic_revision`读取source `{path,sha256}`、settings和cases；可选锁定human_review/clarification/baseline_manifest。其schema示例见项目 `benchmarks/aa-semantic-revision-v1/spec-v1.json`，示例坐标不可迁移到新图。

每case：
- `id`、`native_bbox=[left,top,right,bottom]`、`x_span=[left,right]`指定被处理范围；不是批准的稠密材料框。
- `semantics`注明材料角色来自AI还是已有人工证据。
- `curves`为稳定ID、`kind=rise/fall/valley`、原生y搜索范围；AI负责选择哪条图像边缘有材料意义，脚本只定位候选曲线。横向/纵向平滑与搜索带是待验证参数，不是工艺DRC。
- `regions`引用曲线，指定above/below/between/around和候选材料0/1，margin保留未知带。曲线越序/证据不足时列保持未知；贴框边的区域需记录censored_at_crop。
- `human_check_source`可选，锁定既有局部提示spec，只读取该case非训练checks。没有真值就不生成分数。
- `comparison_overlay`可选，锁定前一候选叠加图，不决定新材料结果。

输出：states.npy三态、raw.png、revision-overlay.png（绿AA/蓝非AA）、unknown-overlay.png、边界假设图、report/spec/manifest和复核页。**绿色/蓝色都还是推断候选**。候选范围之外也会显示unknown；材料真未知和本轮未处理的详细范围要结合case定义读取，不自动并入非AA。

本节横向工具不适用竖环、阶梯、不规则多边形、任意旋转结构或全幅。有粗结构先验时可用下节形状验证工具；否则保留算法候选、标出待核，不强行套横向模型，也不新增案例专用坐标程序。

## 验证样例与停止点

仓库已有八图和昨日七份证据归档；恢复入口见 `docs/checkpoints/2026-10-18-aa-workflow-reviewed.md`。不覆盖冲突文件。

本次开发调用：

```bash
.venv/bin/python -m silicon_eye.aa_semantic_revision --root . \
  --spec benchmarks/aa-semantic-revision-v1/spec-v1.json \
  --output runs/新的AA局部复核目录
```

原spec-v1中S05已有语义/中心检查，S02当时只有AI材料假设。后续用户已确认S02材料关系并纠正S05为两条邻近环，spec-v2生成第二环候选；S05两环局部位置/间隙也已确认，精确边界与整环未审；实际接续以CURRENT_TASK最新裁决为准，不重复询问已审身份/位置，停在尚未通过的边界或范围门，不以skill调用成功越过它。测试应包含无边界证据返回unknown、真实间隙不被填充、暗内部不挖孔；不能只检文件生成。

## 竖环、台阶与折线的粗先验路径

有已审粗形状或明确AI候选拓扑时，使用 `silicon_eye.aa_shape_validation`，不将横向带状工具硬套过去。真实开发输入见 `benchmarks/aa-shape-validation-v1/spec-v1.json`。

- 每case提供原生bbox、对象外轮廓/孔、片段延续标记和待检查的组件/孔数。轮廓只作粗定位，不当作本轮材料结果；旧结构验收不批准派生样本的全部像素。
- 在粗AA内部和外侧窄带派生AI样本，RF与GrabCut使用相同抽样像素。来源照片决定候选分割；GrabCut额外硬固定这些样本，因此不是无先验公平竞赛，也不证明能发现遗漏的结构。
- 保存每种方法的二值候选、三态/处理域、源图、派生样本、旧轮廓、分歧和完整报告。拓扑检查同时看原候选及未知带后的AA核心。
- 组件数须区分先验锚定的目标结构与范围边缘截到的未建模邻居。目标内断裂/孔变化应失败；边缘未建模组件或小碎片保留为NEEDS_REVIEW，不直接说成目标环断裂，也不删除像素掩盖问题。
- P05/P06式局部折线保留continuation_ports；贴取样/处理边界的端口不是物理断点。不能从两个断开的局部对象推出电气隔离或从图面相邻推出相连。

```bash
.venv/bin/python -m silicon_eye.aa_shape_validation --root . \
  --spec benchmarks/aa-shape-validation-v1/spec-v1.json \
  --output runs/新的AA形状复核目录
```

结构门PASS只说明此粗先验和范围下的候选目标保持了预期组件/孔；位置、凹角、真实间隙和材料仍需看原图复核，不自动写正式GDS或整层。当前三种形状都是已见案例回归，无独立真值像素，不报IoU或自主发现能力。

本轮V01/P01/B01新候选整体合理性已获用户确认，记录在项目 `benchmarks/aa-shape-validation-v1/human-review-v1.json`。这是案例级人工门，不追溯改写原报告的PASS/NEEDS_REVIEW，也不把全部算法的边缘碎片当稠密真值。后续可作已知局部回归，不重复询问同样的形状身份。

## 全幅外推实验（非坐标汇总入口）

**接续限制**：本模块会重训并推断全图，没有只汇总模式；坐标整理/分块展示不得调用它。默认入口阻止运行，仅隔离算法实验可显式使用`--experimental-full-frame`，该开关不代表质量门通过。先执行[比较契约](quality-contract.md)，没有既有比较/质量证据不得替换主线。

`silicon_eye.aa_native_canvas`读取照片、来源哈希、有效范围/操作排除区、训练样本、局部候选及其处理域/裁决、模型设置和复核网格。例见项目 `benchmarks/aa-native-canvas-v1/spec-v1.json`。

- 一个全幅原生states.npy是唯一候选层；局部仅整数平移，复核块不能成为独立版图或引入连接断点。跨边界上下文和来源必须可回查。
- 用单一模型做有halo的全幅推断，避免独立块模型的接缝。局部训练在全幅外推仍可能误涂/漏检，阈值是未校准模型设置，不是准确率。
- 已有上下文复核的局部候选在其处理域显式优先，连unknown带一并保留。全图模型与局部分歧单独显示；同等级局部矛盾回unknown，不多数票。局部优先不是逐像素真值批准。
- 保存源像素坐标、三态、有效/处理域、局部贡献、模型分数及分歧；二值AA图不能单独当最终材料层。
- 网格只用于质量复核，core无缝分区并带额外上下文；候选占比/未知占比不作准确率。AI逐块检查环、内部连续性、背景误涂和来源冲突，记录需修订/待核；已知失败先阻断替换，只有尚无裁决的新问题才交人复核。

```bash
.venv/bin/python -m silicon_eye.aa_native_canvas --root . \
  --spec benchmarks/aa-native-canvas-v1/spec-v1.json --experimental-full-frame \
  --output runs/新的全幅原生AA目录
```

本轮全图外推仍约49.4%unknown，12块无整块验收。保留为隔离实验，先比较旧成果与变更域，不要求12块从头人审；不以全幅文件成功生成宣称恢复完成；不按整个复核框清除材料或覆盖外围环。
