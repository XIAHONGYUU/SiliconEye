# 2026-10-19：顶层整理、AA局部修订与实验版skill

## 本轮完成

- README改为项目导航与实际能力，完整旧愿景归档；开发计划只保留阶段顺序；CURRENT_TASK只保存当前授权、验收、边界、下一步。AGENTS长期规则与固定baseline不变。
- 使用现有Q1–Q4裁决与Q4环定位澄清，按AI材料语义与源图边界证据生成S05局部修订候选。不是按复核框直接清除像素；保护环横条，保留暗AA内部与非AA间隙。
- 同一工具在S02生成不同窗口候选。该窗曾见于早期算法探索，不能称盲测；本轮材料角色尚未人工确认。
- 新增仓库内[实验版AA skill](../../skills/silicon-eye-aa-reconstruction/SKILL.md)，通过skill-creator结构校验与当前Agent实际协议回放；未安装全局、未做独立Agent评测，未完成材料验收。

## 查看与核查

[打开交互对照页](../../runs/aa-semantic-revision-v1d/index.html) · [一张完整复核图](../assets/aa-semantic-revision-v1/review-sheet.png)。

绿色为候选AA，蓝色为候选非AA；未着色是未知，不当作背景。另存processing-domain.png与原生列范围，区分本轮未处理范围和处理域内尚不确定的部分。候选贴窗口边的延续不是材料真实断点。

本工具由AI指定材料角色和边界搜索范围，再在原图的横向局部结构中定位上升/下降边缘及间隙低谷；不足证据、越序或冲突保持未知。没有自动材料语义识别，没有任意形状/竖环/阶梯AA或全幅恢复能力。预设margin=3像素仅为开发不确定带，不是实测误差或PDK尺寸。

S05原6个检查中心正确6、错误0、未知0。它们未参与拟合，但该窗及错误已被反复观察，成绩只作开发回归。图中电阻内部、环横条和暗AA核心已区分，部分亮暗过渡带仍未赋材料标签。语义约束已审不等于新精确边界通过。

**请一次判断两项：**

1. S05：环横条、间隙、暗AA内部与未知过渡带的处理是否合理？
2. S02：两块AA内部与中间非AA间隙的材料身份是否认对？

通过后再决定边界细化和方法扩展；当前不写正式AA几何、CT或连接，不因界面整齐或检查点正确越过材料门。

## 验证与恢复

328项测试通过；新增4项验证真实间隙/暗内部、边缘未知、弱证据失败回退、未知中心不误计为正确背景和越界拒绝。相关Ruff、源图/输入/代码/输出哈希、三态及处理范围、源码协议回放一致、页面JS语法通过。软件检查不证明材料正确，浏览器交互未自动实测。

[参数与AI假设](../../benchmarks/aa-semantic-revision-v1/spec-v1.json) · [结果](../../benchmarks/aa-semantic-revision-v1/report-v1.json) · [技术核查](../../benchmarks/aa-semantic-revision-v1/verification-v1.json) · [源代码](../../silicon_eye/aa_semantic_revision.py)。

```bash
.venv/bin/python -m silicon_eye.evidence_archive \
  --archive benchmarks/evidence/aa-semantic-revision-v1d-evidence.zip --root .
.venv/bin/python -m silicon_eye.aa_semantic_revision --root . \
  --spec benchmarks/aa-semantic-revision-v1/spec-v1.json \
  --output runs/新的AA语义修订目录
```

对照依赖昨日笔画候选；缺失时按[昨日检查点](2026-10-18-aa-workflow-reviewed.md)恢复相应归档。实际重放见runs/aa-semantic-skill-replay-v3，状态数组与发布候选完全一致；这只是同Agent按skill协议调用，并非自动发现或独立评测。

原始照片和此前算法/模型/裁决未改动；本轮不提交/推送Git。旧顶层正文与Git上一提交逐字节一致，保存在docs/history/2026-10-19-before-top-level-*；原文相对链接按其原位置理解。此前v33网络、195对象与100疑点的原记录完整保留。

## 后续裁决：过渡区实际有两条邻近AA环

[用户裁决](../../benchmarks/aa-semantic-revision-v1/human-semantic-review-v1.json)指出S05未知过渡带包含两条相邻很近的AA环，S02材料关系合理。此前只保留一条、把另一条留unknown并不完整；“保留未知”不能代替结构完整性检查。

复用原算法和不确定带参数，仅在[spec-v2](../../benchmarks/aa-semantic-revision-v1/spec-v2.json)增加第二环的边缘假设，生成[新版候选页](../../runs/aa-semantic-revision-v2a/index.html)。只将4345个unknown候选像素改为AA，不改已判AA/非AA像素；S02数组保持完全一致。原6个中心仍全部正确，两环核心在处理列内均存在，未被AA桥合并。精确边界、完整闭环、父器件归属与电气连接仍未批准。

[新版图](../assets/aa-semantic-revision-v2/revision-overlay.png)与[核查](../../benchmarks/aa-semantic-revision-v1/verification-v2.json)。下一步仅确认新增第二环局部段是否对应正确，不重复询问S02材料身份。软件和旧裁决不改写；新证据可用benchmarks/evidence/aa-semantic-revision-v2a-evidence.zip恢复。

## 两环局部位置与间隙已验收

用户确认“位置与两条环之间间隙合理”，[验收记录](../../benchmarks/aa-semantic-revision-v1/human-two-ring-review-v1.json)绑定spec-v2与新版局部图。S02材料关系、S05两条AA环的局部位置/间隙均完成本轮人审；不再重复询问。完整内外精确边界、全周闭合、父器件归属、电气连接与全幅覆盖仍未批准。

实验版skill已完成这两个局部案例的同Agent执行与人工闭环。第二环是用户指出后由AI补充语义、脚本定位，不是算法自主发现；结构完整性检查必须保留，不能将未知带视为完成。下一阶段再冻结该局部回归基准、选择不同结构扩展验证，现有横向边界工具不宣称支持任意AA形状。
