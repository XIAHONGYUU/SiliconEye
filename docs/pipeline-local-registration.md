# 主流程局部配准接入与阶段检查

2026-10-14：当前完成分工设计、配准核心及局部候选验收工具，并把冻结 aa/poly 案例接入主 Pipeline 的显式 `registration` 阶段。物理材料边界仍未人工确认，器件/连接/网表闭环未建立。

| 项目阶段 | 当前可验证结果 |
|---|---|
| AI/脚本分工与验证设计 | 完成；当前 AI 在开发过程中选结构、复核原图，运行时尚未接入视觉模型 |
| 配准核心与局部验收 | 合成测试通过；两处局部检查达到 8/12 px 试验预算；结构身份仍 candidate |
| 主流程加载/配准接入 | 本轮完成显式局部阶段、路径解析和状态保护，仅加载 aa/poly |
| 人工局部标注基准 | 尚未建立；层语义/物理尺度与结构真值仍需相应证据 |
| 器件提取、跨层连接、网表验收 | 尚未打通；现有骨架/helper 不能作为已完成实现 |

## 本轮发现与修复

旧 `_build_tile_set` 在工作目录的 test_chip/ 下搜索照片，忽略实际 data/test_chip/，找不到时仍虚构 PNG 路径。现在显式 data-root、返回绝对 JPEG 路径；缺图、歧义和未知层拒绝；局部案例仅解析所选两层，不重验收八层。

主流程以前调用单 tile pass-through，没有跨层配准步骤；未实现的分割返回空列表后可写空 device checkpoint 并打印完成。现在 `registration` 调用既有局部验收入口，设备阶段明确 blocked；候选上游禁止继续设备/网表，缺少已验证设备 checkpoint 也禁止阶段2。旧 helper 未重写，不声称 checkpoint 恢复或外部 DeviceList 导入已实现。

## 使用

从仓库根运行，输出目录须不存在且不得位于 data-root 内：

```bash
.venv/bin/silicon-eye run -c configs/test_chip.yaml \
  --data-root data --stages registration \
  --registration-spec benchmarks/local-ring-aa-poly-v1/square.json \
  -o runs/pipeline-local-next
```

输出 `pipeline_manifest.json`、重定位源图路径的 `local_registration_input.json` 和 `registration/` 证据包。原 spec 的哈希与派生输入哈希分开保留；只改变数据路径，不改变冻结拟合、预算或矩阵。

阶段状态包括 candidate/blocked/failed/complete。候选配准数值达标仍显示 candidate、acceptance=unknown；执行完成不是人工确认。`run` 默认阶段1/2 此时返回 blocked、退出码2，而非空输出成功；显式 registration 能运行并退出0。这是有意纠正原先成功语义。

## 验证

新增12项测试覆盖 JPEG/data-root 解析、未选层跳过、缺图/歧义/未知层拒绝、非法阶段、未实现分割不产出 checkpoint、候选上游阻止下游、失败记录和输出目录保护。全套83项通过。

实际命令验收：[单局部阶段](../runs/pipeline-local-v2/pipeline_manifest.json)、[候选阻止下游](../runs/pipeline-local-gated-v1/pipeline_manifest.json)、[默认阶段阻塞](../runs/pipeline-default-blocked-v1/pipeline_manifest.json)、[汇总证据](../runs/pipeline-local-v2/verification.json)。冻结矩阵与既有检查误差完全一致；两张原图前后哈希一致；无设备或 SPICE 输出。

CLI/新增测试 Ruff 通过；pipeline 新增代码检查通过，仍有未触及网表 helper 的两个既有 lint 项 F541/SIM114，检查明确排除它们，没有宣称仓库全量 lint 通过。原图、配置、依赖和冻结案例不变，无提交、无推送。

下一步仅设计同一局部区域的像素坐标标注基准，明确 AI 候选、人工确认和缺失物理事实；在独立标注基准建立之前不开放器件阶段。
