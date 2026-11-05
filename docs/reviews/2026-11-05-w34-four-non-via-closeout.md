# 四处V1搜索目标均为非孔：实际裁决收口

2026-11-05收到review-decision（8），对应版本baa23ce29a0445b2a9ae7a5d88e82e37，校验及[归档](../assets/w34-terminal-v1-inspection-v1/review/review-record.md)成功。N1/N2/N3/S1均为needs_revision，备注均明确“非孔”，V1_visible_in_M1=false。没有任何一项通过。

[已裁决观察](../../benchmarks/w34-terminal-v1-reviewed-v2/reviewed-observations.json)按这条明确语义将四个具体搜索目标identity_confirmed置false，状态为REJECTED_SEARCH_TARGET_NON_VIA；connection_confirmed和上下金属仍null。不是一般needs_revision自动映射false，不推导附近无孔、整条线无V1、全局不接或电气终点。原送审观察及照片保持不变。

[本批收口](../../benchmarks/w34-terminal-v1-reviewed-v2/identity-closeout.json)明确0个通过的V1、4个拒绝目标、0个本批待裁决、0个新增接口。现有53金属、34条旧批准连接及188候选设计孔保持。之前四条M2延伸与M3窗口的几何验收不受本次负面身份裁决影响。

[负例参考](../../benchmarks/w34-terminal-v1-reviewed-v2/negative-reference-set.json)保存4个目标的原图/范围/送审证据及实际备注，用于后续人工识别回归；同一芯片的四框不冒充四个独立芯片，未实现或运行自动AI评测。[15项记录与保持检查](../../benchmarks/w34-terminal-v1-reviewed-v2/verification.json)通过，非物理识别算法准确率证明。

这次暴露的是搜索效率问题：未看到明确V1，却因M2有线端而在M1近邻细线处提出搜索框，四处均被否定。后续先核正面孔证据再提出接口，不将每个可见端部强行配孔；不立即换邻框重新索取判断。无需回改已审几何，下一步回到来源清单中明确未覆盖的左侧约x220细M2及其短头，先冻结原图观察，尚不预判V2或M3承载。长期skill规则本轮未改。
