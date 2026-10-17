# 端子金属局部高亮demo

**v1选段已被用户否决。当前请使用[gate→CT→M1 v2](gate-ct-metal-review-v2.md)，以下保留原实现说明。**

本轮目标：选择R2_Q1.G，在M1原图副本上高亮一段明确声明的候选金属，保留端子ID、来源与状态。不自动追踪或修改确认电路。

```bash
.venv/bin/silicon-eye annotate review-package \
  --spec benchmarks/review-package-roi2-gate-highlight-demo-v1.json --root . \
  -o runs/new-terminal-demo
```

原包请求可选`terminal_highlights`来源列表。候选记录显式指定case、terminal、原生frame/照片哈希、观察窗口、金属段多边形与锚点；当前只接受AI candidate，不接受自报confirmed。来源、实体、凸多边形、原图/窗口范围、锚点在段内均须通过检查。candidate-mask仅用于显示声明的候选区域，不是材料分割真值。

这不是把器件框当金属。金属段由AI查看原始M1及poly/既有宏观对应后单独声明；脚本只核验和渲染。黄色区域不由同网关系或自动像素分割生成。

本次先选择M1上方公共横条的一小段，作为R2_Q1.G的候选连接；中部横条仍是替代解释。已有人工裁决仅确认Q1/Q2栅经M1同网，没有确认具体CT或路径，因此本demo明确等待用户核查选段，而不写入terminal_maps_to_conductor批准。

本机[原图/高亮对照](../runs/roi2-q1-gate-highlight-demo-v1/terminal-highlight-001-demo.png)可直接在对话/图片预览查看，不依赖本机HTTP服务。另导出原生raw、overlay、候选mask、结构化来源及HTML开关页。紫色十字是候选锚点，不是确认CT落点；两端停止，未展示的延伸未知。HTML通过开关替换原图/高亮副本；受此前浏览器安全策略影响，本轮未通过内置浏览器验收HTML交互，静态图已目视检查。

所有输出进入同一manifest，并绑定输入与代码哈希、bundle_id与不变的block_state_id。本轮243项测试及相关Ruff通过，来源单独拷贝重放29项产物哈希一致；确认网表不变。软件通过不代表候选金属选段已获人工批准。

后续待用户确认选段，再独立记录端子与金属段对应的人工事件。整网自动追踪、跨层过孔扩展和像素精确边界不在本轮范围内。
