# BF24／BF25／BF26 局部接触裁决接续

用户回答“这个局部区分正确”，绑定原问题 `B-FINGER-CONTACT-Q1` 和原送审 M1 图，只确认 BF24、BF25、BF26。原问题、26 条来源观察和送审图冻结；裁决另存覆盖记录。

[复核页](../assets/B-short-finger-reviewed-v2/index.html) · [规则几何前后对比](../assets/B-short-finger-reviewed-v2/local-before-after.png) · [五层工作页](../assets/B-short-finger-reviewed-v2/work/index.html) · [原话](../../benchmarks/B-short-finger-reviewed-v2/human-review.json) · [状态接续](../../benchmarks/B-short-finger-reviewed-v2/source-review-state.json) · [验证](../../benchmarks/B-short-finger-reviewed-v2/verification.json)

## 裁决的准确范围

| 来源对象 | 已确认的本处关系 | 仍未确认 |
|---|---|---|
| BF24 | 接上横条 BU | 下端其它接触、精确几何、材料身份升级、V1及完整路径 |
| BF25 | 不直接接 BU 或下方 L1/L2 | 材料身份、跨层去向、全局同网/异网及是否电气悬空 |
| BF26 | 接上横条 BU | 下端其它接触、精确几何、材料身份升级、V1及完整路径 |

本次问题没有独立确认 BF24/BF26 的下端状态，因此在人审记录中保持 unknown，不能由“上端接 BU”顺推下端断开。其余 23 条、BR-C/BR-R 返回区没有随本次回答批准；26 条接续表中只有三条标为本处接触已审。

## 局部工作几何

复用已有局部修订与显式新增金属机制，分两个事务：

1. 在 `C-M1-SPINE` 中添加 `BF24-UPPER` 与 `BF26-UPPER` 两个连接块，边界分别为 [31,1023,37,1110]、[115,1023,121,1110]。只改变这一条 M1 的候选外形，旧骨架、宽度和既有两个横向块精确保持。
2. 通过独立补充来源清单添加 `BF25-M1-CANDIDATE`，中心路径 [76,1055]→[76,1105]，宽度 10。其占用边界为 [71,1050,81,1110]，与已建主干/邻指的最小设计距离 21px，高于原 3px 间距预算。它没有网络编号，也没有被命名为“电气悬空节点”。

以上是规则几何候选。照片中相邻近似 x 为 2967／3020／3071，工作中心以 34／76／118 表达近似等间距结构；没有从照片恢复精确孔、工艺尺度或全幅变换。候选尺寸不属于这次人工批准。

L1/L2 尚未建模，因此 BF25 对下横条的本处未接来自原图人审，不能宣称其与 L1/L2 的设计间距或返回线路已经通过。图中颜色只区分工作片段角色，不代表已确定的不同网络或电容两极。

## 保持与验证

- 当前 32 条金属候选：原 31 条加 BF25；原 30 条 M2/M3 精确保持，既有 M1 占用完整保留，仅附加两个上接指。
- 11 个已审跨层接口、46 个设计候选孔及中心、原生骨架锚点、原预算与 780×1240 画布保持。没有新 V1、孔数批准、跨层接口或 `net_edges`。
- 同层接触裁决保存在来源记录和修订证据中，没有混入仅用于 VIA 的 `reviewed_local_connections`。既有 11 条跨层裁决逐项保持。
- 所有来源、工作模型与父包按哈希绑定；新请求可精确回放。旧补充清单按追加规则保护，原生坐标与工作坐标独立。
- 本轮没有改生产代码，复用既有 workflow。26 项针对性测试通过：新三条来源/几何回归 5 项，既有局部来源 10 项及金属扩展 11 项；Ruff、原始图稿/问题哈希、CSV/HTML 状态、静态资源与脚本语法检查通过。PNG 已目视，浏览器交互未实测。

源裁决范围复核保持 BF24/BF26 下端为未知；第一次构建的可恢复备份位于 `runs/B-short-finger-initial-review-build-v2/`，不作为现行裁决。以本目录 human-review.json 为准。

README/site 的 25 个展示文件及 gh-pages 保持。材料快照、规范导体注册表与 skill 限定能力不变。未提交或推送。

## 下一步

检查 BR-R 长返回线与 L1/L2 的本处接触及是否绕回 BU。原照片已经保留较大邻域，下一阶段沿来源先查返回路径，再决定是否补几何；不从 BF25 本处留缝推导全局分网，也不重问三条已审接触。

```bash
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/B-short-finger-reviewed-v2/next-request.json --output runs/新的B短指接续目录
```
