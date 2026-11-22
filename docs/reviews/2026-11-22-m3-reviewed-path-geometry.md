# 已审 M3 局部关系接续与几何试做

五组/25对实际裁决均通过，已[校验归档](../../runs/m3-identity-followthrough-20261119/review/review-record.md)。两次导出17/18的答案相同，归档最终18；未使用此前错误批次16。首次交互至最终导出22.909秒，只是页面计时，不是全部分析时间。

## 已完成的接续

- [新来源状态](../../runs/m3-direct-pairs-closeout-20261122/reviewed-source-state.json)精确保留旧2对关系/2条宽边缘，并追加25对，共27条明确直接关系；304候选组/331片段保持，所有整组批准仍为false。
- [已审关系图](../../runs/m3-direct-pairs-closeout-20261122/reviewed-support-paths.json)涉及47片段、20个证据组件。组件仅组织已审关系，不代表20条完整导体，不推导额外成对批准、分支、端点或网表。
- 可复用的`continue_pairs`拒绝重复对、未知片段、已审边缘冲突及未经解释的accepted备注；明确继承旧记录，避免原`apply`只返回本轮记录造成旧事实丢失。

## 下一批只审两项

[固定复核页](../../runs/m3-reviewed-path-geometry-20261122-v2/review/index.html) · [候选与质量门结果](../../runs/m3-reviewed-path-geometry-20261122-v2/candidates.json)

| 项目 | 来源与表达 | 当前状态 |
| --- | --- | --- |
| H01 | G12两片段短直段；局部水平矩形280×10相对像素 | 审矩形表达、线宽有无明显失真 |
| H02 | G16–G18四片段延续；局部水平矩形855×12相对像素 | 同上，不重审三对来源关系 |
| H03 | G25长斜拍路径；亮脊更像宽母线边缘 | 宽度剖面触及取样上限；暂停矩形化，仅参考，无需裁决 |

线宽来自平滑后半对比剖面，仅是照片依据下的候选，不是物理尺寸或DRC真值。原图中的斜拍路径与独立局部矩形分开呈现：没有假装建立全局投影，不能直接拼接进54金属模型。尚未验证邻线间距、实际端点和上下层落点。

AI建议：H01/H02可进入局部几何验收；H03须先识别真实上下边界，不能把单条亮脊当中心扩成窄线。预计核对1–2分钟，未实测。只对H01/H02选择结论，必要时注明偏宽/偏窄；不清楚可保留不确定。

## 验证与恢复

- [核验记录](../../runs/m3-direct-pairs-closeout-20261122/verification.json)：16项相关测试、Ruff、来源哈希、固定包完整性、父模型SHA及独立只读复核通过；不宣称总回归或物理DRC通过。
- 独立复核精确重放新状态、重新计算两处候选，并目视检查三张图；H03没有伪造宽度或矩形。
- 54金属、34局部连接、188候选设计孔、AA/POLY/CT、README/site均未改。没有新增VIA或网表边。
- 所有新几何仍未采用；原始照片、旧送审包和旧批准不覆盖。本轮本地推进，未推送远端。

重跑局部候选需新输出目录：

```bash
.venv/bin/python -m silicon_eye.ridge_regularization \
  --spec runs/m3-direct-pairs-closeout-20261122/geometry-pilot-spec.json \
  --output runs/NEW_GEOMETRY_PILOT
```

实际裁决仍使用固定入口：

```bash
.venv/bin/python -m silicon_eye.review_sheet check \
  --package runs/m3-reviewed-path-geometry-20261122-v2/review \
  --decision /实际路径/review-decision.json --archive
```
