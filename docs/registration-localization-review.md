# 2026-10-14 定位缺陷修复与同源性审查

本轮从真实输入和现有锚点对照图继续；实时状态见 CURRENT_TASK.md。

## 发现与修复

旧 rectangle_center 使用局部窗口的全局亮度最大值，可能定位到内部条带而非声明的边界；其 ±8 px 的质心积分还可能超出搜索范围。旧 m1 bank 右侧对比度约 2.1/255、sub bank 右侧约 5.4/255，却被当作有效边界。图像复核另发现 FIT-bank 混用了条带主体与包含右侧方块的完整包围框。

本轮限定质心支持范围，要求完整支持和对比度 ≥10/255，采用离声明边界最近的合格局部峰；记录逐边检查。测量不可靠或缺少新质量记录的脚本锚点不进入求解。源照片没有被改动。

三项新回归覆盖弱边界、截断边界、旧记录缺少质量检查，一项覆盖更亮内部条带不得替代目标边界。总计 55 项测试及相关 Ruff 通过。检查有效仅表示局部定位稳定，不确认物理同源性。

## 输入版本和结果

- v3 修正 FIT-bank 为完整包围框，保存原图量测及质量检查，未运行该版本的配准。
- v4 使用同样搜索框修复峰选择后冻结；独立 registration-points-v2.json 不改，预算 P95 ≤8 / max ≤12 px 与原拟合限制不改。
- [本机 v4 复核包](../runs/registration-aa-constrained-v4/review.md)含新锚点对照图和逐层诊断。
- sub/poly/m1 因拟合锚点残差超限被拒绝，独立候选 P95 分别为 115.69 / 98.75 / 75.52 px。implant 被定位质量门拒绝；m2/m3/m4 缺锚点。没有目标层通过。
- 仿射仅作一次诊断，三个拟合点残差接近零，但独立 P95 仍为 134.96 / 159.69 / 122.42 px（sub/poly/m1），不能以更复杂模型的拟合效果替代验收。

此诊断没有发布仿射模型或改变相似变换的既有约束。若据此选择模型，未来需要新的最终保留点。当前证据不足以确定是材料边界/结构定义不同、照片来源不同还是局部几何差异。

## 命令与下一步

```bash
source .venv/bin/activate
silicon-eye register -c configs/test_chip.yaml --data-root data \
  --reference aa --fit-roi 100 200 5400 2200 \
  --points benchmarks/registration-points-v2.json \
  --constraints benchmarks/registration-constraints-v4.json \
  -o runs/registration-aa-constrained-v4-next
```

已向用户请求确认是否同一颗芯片逐层拍摄，以及已有对齐参考或可确定的同源标记。收到事实依据后，再建立空间分散的可靠结构点。当前不盲调模型、不放宽预算、不进入器件提取。原有证据、原图、配置与依赖声明保留；无提交、推送或模型服务调用。
