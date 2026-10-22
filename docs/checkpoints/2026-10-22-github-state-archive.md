# 2026-10-22 GitHub状态存档

本次用户授权“将现在状态存档并提交github”，提交基于main的a769561。归档范围为自该父提交以来的本机M1／金属层对／五层适配、来源纠错、已审局部关系及L1待复核产物，不改变人工批准范围。

## 恢复入口

- 唯一当前入口：[CURRENT_TASK](../../CURRENT_TASK.md)；存档前原文及SHA256：[完整归档](../history/current-task-before-2026-10-22-github-state-archive.md)。
- 当前共同层：[v5](../../configs/joint-work-layer-v5.json)，仍为AA334／POLY696／CT10287及33条导体；材料／六处既有未知保持。
- 当前已审路径：[R1／D1已审页](../assets/n2-downstream-interfaces-reviewed-v2/index.html)，B1 → 上端V2 → N2 M2 → 下端D1 V2 → L1。
- 当前待裁决：[L1分支页](../assets/l1-m2-fanout-v1/index.html)，D1已审，F01–F12新增候选，P0–P5未知。批量存档不是批量批准。
- [来源纠错](2026-10-22-m2-via-source-correction.md)与[统一接口](../architecture/conductive-layer-interface-v1.md)；旧9对V1→V2配对及4.52像素残差已撤回为配准证据。

## 保存范围与边界

保存源代码、测试、配置、benchmark中的事前判断／人工裁决／事后评价、静态复核页与原生裁片、当前入口历史链。两张历史裁决图片原在被忽略的runs目录，现按原路径明确纳入Git，字节／SHA256不改：

- `runs/roi2-M3-M2-fanout-review-v1/M3-all-M2-review.png`
- `runs/roi2-P1-diffusion-reviewed-v11/AC-extra-M2-interface-review.png`

只纳入必要的这两张历史输入，不提交整个runs或虚拟环境。原始data照片不修改。旧包、旧AI误判与新纠错记录分别保留；旧包可回放不算旧语义正确。局部几何检查不是PDK DRC；原图精确投影、共同几何落位和完整网络仍受各阶段记录限制。未封装通用金属／Via skill。

## 验证与恢复

[存档验证记录](../../benchmarks/state-archive-2026-10-22/verification-v1.json)保存相关测试、来源哈希及Git暂存范围检查。软件通过不替代F/P人工裁决。

```bash
.venv/bin/python -m silicon_eye.joint_layers --snapshot configs/joint-work-layer-v5.json --output runs/新的存档恢复检查目录
.venv/bin/python -m silicon_eye.layer_review --request configs/metal-stack-review-v2.json --output runs/新的五层复核目录
```

静态L1页可直接本地打开。需要重绘证据图时，按[L1检查点](2026-10-22-L1-M2-fanout.md)调用已有source_panels。Git提交及远端同步结果以实际commit、分支和远端SHA为准，不在提交内容中预写自身提交哈希。

下一步仍是接收F01–F12及P组裁决，之后回查获准M2支路；M1 U1/U2/U3、照片左侧之外、孔数和精确边界等未知不会因本次上传消失。
