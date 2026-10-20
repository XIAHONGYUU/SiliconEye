# CT剩余范围候选 v1

当前入口为 `model-v1.json`＋`stage-gate-v1.json`＋`review-questions-v1.json`。整层为HOLD，尚未人工验收；模型中的whole_frame_complete=false，不得因安全子集几何PASS宣布全幅完成。

`selected-contacts-v1.json`是2960条新增安全几何候选，继承7044条原记录形成10004条工作快照；源/设计坐标分开。`quarantined-observations-v1.json`是调查候选台账，含整段来源有反例的路径，不是实际漏孔数。其余proposed/diagnostic/observations文件是中间证据，不是多个有效基准。

`authorization-v1.json`仅保存用户授权执行本轮工作的范围，不是对新物理身份或几何的批准。新的人工裁决须另建追加文件，不覆盖授权或原照片观察。

现有CLI读取冻结参数及候选，复现几何和基础复核图：`.venv/bin/python -m silicon_eye.ct_transfer --spec benchmarks/ct-full-frame-remaining-v1/spec-v1.json --output runs/新的CT剩余复核目录`。

`provenance/`保留本轮实验配方及包装代码快照，供审计，不是新的生产案例脚本/skill入口；其中路径指向本版本，验收后禁止在本目录原地重跑。原始照片不改；新调查应建新版本。CLI复现冻结观察不等于运行时自主视觉Agent已实现。
