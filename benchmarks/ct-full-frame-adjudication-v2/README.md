# CT人工裁决执行 v2

有效入口是model-v1.json＋stage-gate-v1.json＋human-review-v1.json。五项人审问题已关闭，整层因8条旧来源路径技术回查保持HOLD。前版及旧批准不覆盖，新精确几何不是人审像素真值。

本轮新增26条CT候选、撤回5条未审下端栅CT、仅修正5条G18来源；10025条工作记录。原7044几何和目标全保留；335 AA与原695 POLY完整保留，另加一个共用端POLY。preservation-and-source-check-v1.json、connection-check-v1.json、ledger-v1.json保存保护及范围检查。

复现：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-full-frame-adjudication-v2/spec-v1.json --output runs/新的裁决执行目录`。基础CLI输出几何／材料／记录和基础页面；最终包装另附人审门与整层门状态、前后图和标记。provenance仅供审计，不是新增生产案例脚本或已封装skill，不原地重跑覆盖冻结版本。
