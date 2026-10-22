# 高层金属分支验证

以共同快照v5为锁定父输入，迁移历史A/C已审例，验证一根M3对应多根M2时的枚举、去重与排除逻辑。[复核页](../assets/metal-fanout-validation-v1/index.html)与[请求](../../benchmarks/metal-fanout-validation-v1/request-v1.json)。

- A、C分别经各自V2组接同一根M3两端，来自`roi2-M3-A-C-review-feedback-v1.json`。M3遮挡处连续性沿用该裁决，不伪造像素证据。
- 更晚的`roi2-AC-no-middle-M2-review-feedback-v1.json`确认中间无其他M2、排除邻B直接接入；不能沿用早期清单的“中段未知”要求重复审批，也不能据此断言B全局不同网。
- `metal_fanout`从人审记录直接适配上下导体及Via ID，再检查原图来源／参考位置、双层包围、同层间距和排除关系。按导体ID聚合Via组，两个支持区不等于实测只有两孔。
- 本次没有合格共同坐标配准，故局部规则几何单独展示，原图／宽局部独立显示，保留切层与原图按钮。输出不是共同导体注册表；不得把独立示意位置投影到AA/POLY。
- 当前v5及33条导体、AA/POLY/CT、六处未知不动。未复用撤回的9对跨Via层坐标，未新增物理连接、整网、PDK DRC或新图盲测成绩。

验证命令与当前产物／输入哈希、原图裁片、SVG/JS/链接核验见[核验记录](../../benchmarks/metal-fanout-validation-v1/verification-v1.json)。验证中的合成重复分支只用于去重测试，不写回真实对象。历史来源仍按其原始SHA验证，未改写旧人工记录。

下一步检查B1旁未审相邻M2接口，先核M2上的V2身份，再核B1/B0承载，仅提交新歧义。本轮无须用户重复裁决A/C；无Git提交／推送。
