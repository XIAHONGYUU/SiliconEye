# 对应点复核、拟合约束与误差预算

2026-10-13 本轮完成；实时下一步仅在 CURRENT_TASK.md。前序证据和源图保持不变。

## 输入与预算

- benchmarks/registration-points-v2.json：将四层各六个粗点改为各五个边界中心，共 20 点；去除语义依据不足的 LL-6。点的位置由源图独立量测，未使用配准矩阵或残差。
- benchmarks/registration-constraints-v2.json：四层各三个上部具名结构，共 12 个独立拟合锚点，与下部验证点分离；保存源图哈希、矩形边界搜索区域和量测细节。
- 同源性由 AI 目视复核，亮边中心由脚本量测。结构跨物理层的几何含义仍未获人工确认，所有点保持 candidate。
- 预先锁定宏观试验预算 P95 ≤ 8 px、max ≤ 12 px。目标分配是参考定位 3 px、目标定位 3 px、几何模型 2 px；这不是认证的不确定性，不能外推器件提取精度。
- 预先锁定拟合约束：scale 0.9–1.1、|rotation| ≤ 5°、|translation| 每轴 ≤ 400 px、anchor residual max ≤ 10 px、拟合点凸包面积 ≥ 100000 px²。基于照片整体方位/视野相近的观察，属于试验先验，非工艺事实。

## 命令

```bash
source .venv/bin/activate
silicon-eye register -c configs/test_chip.yaml --data-root data \
  --reference aa --fit-roi 100 200 5400 2200 \
  --points benchmarks/registration-points-v2.json \
  --constraints benchmarks/registration-constraints-v2.json \
  -o runs/registration-aa-constrained-next
```

constraints 模式用原图坐标下的结构点拟合 similarity，不运行 ORB，不使用验证点。它使用冻结预算，拒绝 CLI threshold 覆盖以及 affine/homography 切换。缺少可靠锚点的层不回退到无约束匹配。

每层记录区分 proposal_matrix_native、被求解约束接受的 matrix_target_to_reference_native、结构拟合 checks 和独立 budget_check。被拒绝的候选变换只做诊断，不生成已对齐图片。AI 候选点即使数值满足预算也不能直接成为 confirmed。

## 结果与恢复

[本机重验收报告](../runs/registration-aa-constrained-v2r2/review.md)包含上部锚点对照图、原图/局部图、全部约束检查和独立误差。没有目标层通过。

poly 的拟合约束通过，但独立 P95 41.82 px / max 44.90 px 超预算；sub/implant/m1 因锚点残差超 10 px 被拒绝；m2/m3/m4 没有可靠锚点。旧矩阵在同一新版点集上的诊断保存于 baseline-on-v2-points.json，不混用 v1/v2 点的误差。

恢复时沿用已保存的输入；真实运行发现 NumPy 布尔值序列化错误，补了结构模式端到端测试并修复。中断包保留在 registration-aa-constrained-v2，补记 failure.json；v2r1 完成后完善了预算状态字段，v2r2 的点、预算与矩阵未改变。

测试总计 51 项通过，覆盖精确 similarity、异常缩放/旋转/平移拒绝、退化/矛盾锚点、源图哈希、预算冻结和验证点隔离、边界中心量测、结构模式完整证据包、缺锚点不回退以及候选不冒充人工真值。

下一步需要复核上部结构同源性与中心定义，并增加分散的精确独立点；不能通过放宽预算或事后删除失败点让本轮通过。原图、配置与依赖声明不变，未提交、未推送。
