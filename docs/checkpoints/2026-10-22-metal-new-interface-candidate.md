# 第二组设计放行，第三组N1新候选待审

用户原文：“设计批准放行，继续推进”。[第二组设计放行记录](../../benchmarks/metal-short-branch-transfer-v1/design-approval-v1.json)锁定当时spec、模型、报告与页面。放行所示相对设计、隔离和承载表达；不转移为精确原生投影、实测孔数、所有金属或整网批准。

## 本轮新增候选

[打开N1复核页](../assets/metal-new-interface-candidate-v1/index.html)。选取W1左侧相邻的短竖M1及折线形M2短支路，右侧灰色REF-W1保留为已审参照。两张原图各有宽上下文、4倍局部、原图／观察线切换；共同设计图可切候选M1／V1／M2、已审参考及AA／POLY／CT。

**AI先判：** M1-N1-STUB上端亮点为V1候选，接到M2-N1-BENT-STUB的下端。M2上部亮带未自动判为V1或V2。M1参考点(1145,3219)、M2参考点(1109,3255)只是AI观察位置，不是已验证孔中心或精确映射。

此判断及替代解释先保存在[首次AI观察](../../benchmarks/metal-new-interface-candidate-v1/initial-ai-observation-v1.json)，再生成设计候选和复核页。目前没有N1人工真值，正确性与纠正次数均为null。这不是严格隔离历史上下文的盲测，不以生成成功或几何自洽计作识别正确。

## 唯一新问题

**N1：橙圈处是否为V1，并把左侧短竖M1（N1）接到左侧折线M2（N1?）的下端？** 右侧灰色REF-W1为已审参照；若不对应，请指出正确端部。

第一组J1／J2、第二组W1接入和本次设计放行均不重审。后续N1裁决另存为人审记录，首次AI观察与候选不回写成事先已知答案；评价结果单独对照记录。

## 几何与使用边界

候选三条M1保持隔离，最小间距9设计像素；M2帽部与短竖连通；6×6孔组支持区及2像素包围落在两层内。支持区不是实测单孔，物理孔数仍null。M2和上横M1在模型中有重叠，未生成无来源接入；这不宣称照片已证实该处物理无孔。

灰色参考设计是冻结模型的显示，不并入新候选对象表。上下文横线记录指向已审邻线作为观察参照，不把窗口截段自动变成新增物理网络。新共同画布位置只是AI相对定位，未改当前AA334／POLY696／CT10287或建立新CT归属。

精确M1↔M2、原生→设计映射仍无独立放行；原图不作强制投影。状态`REVIEW_REQUIRED`，候选连接只在`hypothesized_local_connections`，`reviewed_local_connections=[]`，自动网络导出关闭。

## 固定检查与接续

- 两组基准在新代码下复跑，各16项模型、报告、图页等产物逐字节不变；执行清单仅记录新代码哈希。比较详见[基准回放核验](../../benchmarks/metal-new-interface-candidate-v1/baseline-replay-verification-v1.json)。
- 42项相关测试通过（40.64s），包括设计放行不得覆盖N1物理身份、旧批准绑定错误模型时拒绝、未审候选不得删审批问题、首次参考点不得移位凑合、AI不得自填人工真值。此前隔离、无来源增孔、V1/V2区分及旧几何保护继续测试。
- 复用现有工具的候选模式，不另建案例脚本或通用skill。Ruff、来源／产物哈希、SVG、JS、本地链接及归档检查见[最终核验](../../benchmarks/metal-new-interface-candidate-v1/verification-v1.json)。已直接查看原图裁片与规则图，未声称浏览器点击验收。

[输入](../../benchmarks/metal-new-interface-candidate-v1/spec-v1.json)、[模型](../assets/metal-new-interface-candidate-v1/model.json)、[报告](../assets/metal-new-interface-candidate-v1/report.json)。复跑：

```bash
.venv/bin/python -m silicon_eye.metal_via_pilot \
  --spec benchmarks/metal-new-interface-candidate-v1/spec-v1.json \
  --output runs/新的N1候选目录
```

只待N1裁决；不扩全幅、不追整网、不填造工艺尺寸。本轮未提交／推送GitHub。
