# aa/poly 局部环候选案例 v1

本案例只覆盖 aa/poly 的中部环邻域，两个检查结构是左侧竖向环和独立方块。原图约 4.3–5.2% 的区域；目标→参考的矩阵、拟合方法和 8/12 px 工程预算均冻结。`candidate` 是当前证据等级，没有人工物理边界确认。

## 运行

从项目根目录运行，输出目录须不存在：

```bash
.venv/bin/silicon-eye register-local \
  --spec benchmarks/local-ring-aa-poly-v1/vertical-ring.json \
  -o runs/local-ring-vertical-next

.venv/bin/silicon-eye register-local \
  --spec benchmarks/local-ring-aa-poly-v1/square.json \
  -o runs/local-ring-square-next
```

只需项目代码、依赖和哈希匹配的两张原图；不依赖旧 runs/。亦支持原 `python -m silicon_eye.registration_local` 入口。

## 固定输入

- `baseline/`：从原 `registration-local-ring-v2r1` 包逐字节复制的拟合 manifest、输入及三个代码快照，保留原哈希。快照仅作冻结比对，不执行这些历史代码。
- `vertical-ring.json`：曾用于模型诊断的竖向环检查。
- `square.json`：模型冻结后的新方块检查；该区域曾出现在早期大范围证据中，不是项目全程严格盲测。
- `identity-review.json`：开发过程中的 AI 原图复核，支持区域位置/拓扑对应，物理材料边界同源性仍 unknown。没有声称运行时已接入视觉模型。

竖向环 P95=3.73、max=3.75 px；方块 P95=5.61、max=5.64 px。两项 `numeric_budget_met=true`，`acceptance=unknown`。四角在同一结构内相关，中心指标同样从四角计算。

三处原图位置关系支持候选结构身份；不同层的内部条纹、接触点和填充亮度不应当作同一边界。误差只代表本地几何检查，不证明整片、其他层、器件或连接正确。

[可迁移复现记录](../../runs/local-case-portability-v1/reproducibility.json)来自仅含 benchmarks/ 和源图链接的临时工作目录，使用既有 venv/项目代码；不是重新安装依赖的完整洁净构建。两项误差复现差 <1e-10 px，矩阵逐元素相同。

[统一 CLI 输出](../../runs/local-case-cli-v1/report.md)。本轮全套 71 测试和相关 Ruff 通过；无算法/预算修改、无原图改写、无推送。
