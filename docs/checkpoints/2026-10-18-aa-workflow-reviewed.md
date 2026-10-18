# 2026-10-18：AA工作方法阶段固化

用户认可今天形成的提取方法，要求提交Git并更新顶层文档，明天争取封装skill。当前是经过局部实证的工作方法，不是全幅AA精确边界验收。

## 今日产物

从全幅几何优先转为先分清材料：算法基线 → 局部提示 → 颜色/纹理/结构消融 → 代表性笔画 → 多方法分歧 → AI上下文复核 → 人工裁决。

- [当前方法与明日skill边界](../architecture/aa-extraction-workflow-v8.md)
- [算法初比](../aa-segmentation-comparison-v1.md)、[提示试验](../aa-prompted-comparison-v1.md)、[纹理结构消融](../aa-texture-structure-v1.md)、[笔画对照](../aa-scribble-comparison-v1.md)
- [上下文复核说明](../aa-context-review-v1.md)、[Git中可直接查看的复核图](../assets/aa-context-review-v1/review-sheet.png)、[宽范围原图](../assets/aa-context-review-v1/wide-context.png)
- [九条笔画裁决](../../benchmarks/aa-scribble-comparison-v1/human-stroke-review-v1.json)、[Q1–Q4裁决](../../benchmarks/aa-context-review-v1/human-context-review-v1.json)、[Q4定位澄清](../../benchmarks/aa-context-review-v1/Q4-scope-clarification-v1.json)

纹理RF和纹理＋结构RF均在三个种子下通过8个AA及4个非AA中心检查；GrabCut仍误填2个非AA间隙。电阻内部残余误报、外围环精确边界与新窗口迁移尚未解决。算法只产生候选，AI结合整体结构、已有裁决与正向版图经验复核，人决定关键语义。

Q4指电阻外围环下侧AA横条靠电阻内部一侧的边界。**保留外围环，排除电阻内部误报，不得把二者一起裁掉**。原判词不覆盖整环存在/边界/连续性的完整验收；Q框不是可直接修改的材料多边形。

## 恢复和重跑

原始八张照片已在Git中，保持不变。`runs/`与`.venv/`仍忽略；七个关键试验/复核目录有独立证据归档，见[归档索引](../../benchmarks/evidence/aa-workday-2026-10-18-index.json)。这是明确范围的历史证据，不代表所有旧runs均已保存。

仓库根目录内先安装项目与可选依赖：

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev,segmentation-eval]'
# 恢复某个归档；相同文件跳过，不同文件拒绝覆盖
.venv/bin/python -m silicon_eye.evidence_archive \
  --archive benchmarks/evidence/aa-context-review-v1b-evidence.zip --root .
```

需要重跑整个对照链时先恢复索引列出的七个归档，尤其是无提示基线和纹理结构基线。复核页入口 `runs/aa-context-review-v1b/index.html`；各试验文档保留独立重跑命令和冻结参数。

```bash
.venv/bin/python -m silicon_eye.aa_context_review --root . \
  --spec benchmarks/aa-context-review-v1/spec-v1.json \
  --output runs/新的上下文复核目录
```

原环境版本见各verification报告；重跑同一输入需考虑OpenCV/NumPy/sklearn版本差异。冻结源码快照用于解释旧结果，不冒充当前程序运行。

## 明日接续

先做有证据的局部修订对照，再用一个不同窗口验证工作方法；在这个过程中封装实验版AA skill，明确输入、已有工具调用、人工门、未知和失败回退。CT、其他层完整重建、追线与全幅生产验收不纳入该skill首版范围。

当前区域规划skill已存在，职责是理解/评测，不决定分层空间范围；AA skill尚未实现。运行时没有接入独立视觉模型，今天的AI判断由交互Agent执行。

## 提交前验证

324项测试、相关新增/修改代码Ruff、依赖检查通过；Git差异检查使用 `core.whitespace=cr-at-eol` 识别已有CSV的CRLF行尾后通过，哈希锁定的历史CSV不为消除行尾提示而重编码；原始照片无修改。临时目录恢复7个归档共461文件，重新生成复核图与原图逐字节一致，见[恢复核查](../../benchmarks/aa-context-review-v1/checkpoint-verification-v1.json)。顶层文档相对链接已检查。Git未包含.venv或runs目录；未推送远端。
