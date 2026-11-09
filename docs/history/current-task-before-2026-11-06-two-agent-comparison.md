# 入口原文归档

来源：CURRENT_TASK.md；归档日期：2026-11-06。下方原文完整保留。

# 当前任务

## 当前目标与授权

2026-11-06用户授权直接做图像算法对照。本轮已完成四个M2局部窗口的 Otsu / GrabCut / SAM 2.1 tiny 实际运行，以及已知V1正负例模板匹配；仅产生候选掩膜和评估证据，不采用几何、不分析新承载、不改网络。

## 最新结果

- [实验报告](docs/reviews/2026-11-06-metal-algorithm-pilot.md) · [只读对照页](runs/metal-algorithm-pilot-20261106/review-v2/index.html) · [冻结参数](benchmarks/metal-algorithm-pilot-v1/spec-v1.json) · [原始指标](benchmarks/metal-algorithm-pilot-v1/report-v1.json)。
- CPU两线程：四窗SAM推理合计10.716秒、模型加载另0.642秒；Otsu合计0.0017秒、GrabCut0.114秒。提示准备与人工修正时间未测，不宣称整体提速。
- L01/S03/W4三个窗口中SAM/Otsu均命中9个AI正检查点、0/9非目标误命中；GrabCut在W4塌缩。不是人工像素真值、IoU或全幅精度。
- S04原检查点2/3与第二提示偏右，排除整个窗口的稀疏汇总。原参数/输出原样保留，不把检查点选偏归罪于算法。[后置审计](benchmarks/metal-algorithm-pilot-v1/post-run-audit.json)。
- 模板B正例0.829、四非孔0.547–0.622；预设阈值0.50全部负例误报，0.65/0.80在本批分开。一个正例和四个已知负例，不据此批准全图阈值或孔身份。
- [证据ZIP](benchmarks/metal-algorithm-pilot-v1/evidence-v1.zip)包含掩膜/图/固定页面/代码快照；[环境](benchmarks/metal-algorithm-pilot-v1/environment.json)及[包版本](benchmarks/metal-algorithm-pilot-v1/environment-freeze.txt)记录CPU SAM安装。模型/源码在本机runs，照片未上传。
- 本轮新脚本、测试、benchmarks、报告和本入口留本地，未提交/推送。已有README/site、已审模型和裁决未改变；只读页不要求重审旧对象。
- 36项相关测试、定向Ruff、pip check、diff及固定页面包哈希校验通过；[验证记录](benchmarks/metal-algorithm-pilot-v1/verification.json)。浏览器交互未实测，不宣称完整项目回归通过。

## 唯一下一步

若继续算法验证，先固定新窗口并核对原生参考/提示，做人工直接处理与SAM辅助修正的计时对照；保留本轮作开发回归。现有结果尚不能支持全幅推广、精确轮廓采用或宣称人工减负。不要仅因推理完成而扩大实现范围。

## 暂停的工程主线与仍生效边界

- L01几何G1及短头V2身份I1已实际通过；[当前工作基线](benchmarks/w34-left-m2-reviewed-v2/working-baseline.json)、[身份记录](benchmarks/w34-left-m2-reviewed-v2/V2-identity-reviewed.json)、[接续请求](benchmarks/w34-left-m2-v1/next-request.json)。54金属：M1=11/M2=18/M3=25；34局部连接、188候选设计孔保持。
- I1原生框[210,2348,262,2380]，承载/上层ID/物理孔数未知；未建新VIA或连接。本轮不分析M3承载。后续恢复工程主线时按原入口核局部来源对应及替代导体，不靠设计重叠指定M3。
- N1/N2/N3/S1四个M1搜索目标仍为“非孔”，不重审、不建孔；不能推导附近无孔或全局断开。
- L01上端未知；已审几何/身份不升级到共同精确几何、物理尺度或完整网络。source_to_design_transform=null、geometry_adopted=false、net_edges=[]、complete_network=false，skill仍LIMITED_TRIAL_V2，自动网表导出禁止。
- 其它局部承载裁决、六处材料未知、BF25与返回路径未知、旧配准拒绝项、AA/POLY/CT保护及所有未解决问题，完整保留在[上阶段入口原文](docs/history/current-task-before-2026-11-06-algorithm-pilot.md)。原历史总回归README哈希漂移FAIL不改写，不宣称全套PASS。

## 重跑本轮

```bash
.venv/bin/python -m silicon_eye.metal_algorithm_pilot --spec benchmarks/metal-algorithm-pilot-v1/spec-v1.json --output runs/metal-algorithm-pilot-20261106/new-result
```

输出用新目录。原始S04分数须连同后置审计阅读。不得自动修改正式几何、README/site、发布gh-pages或推送Git。
