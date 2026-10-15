# 用户示例引导的 AA/poly 重提取

2026-10-15：用户提供 annotation-sheet-market.png，红色为部分 AA 正例，蓝色为几乎全部 poly 正例；随后明确第二张图亮点是 CT，CT 可接触 AA 或 poly。涂色是位置/形状示范，不是精确像素真值。

[输入参数](../benchmarks/guided-materials-v1.json)固定原样片、人工涂色样片、样片映射和冻结配准引用的 SHA256。当前依赖本机 runs/ 中的人工样片；没有将用户图片自动上传或假称可在缺少这些文件的检出中重跑。

## 方法与职责

AI 在开发过程中理解示例、区分三类结构并复核输出；运行时脚本从原图取像素，从修改前后差异/颜色读正例，不把涂色后的图片交给分割。未涂色像素逐点一致，面板保持原生1:1坐标。

在正例周围8 px有限搜索带使用 GrabCut，5轮、固定随机种子；正例内部腐蚀区域作为强前景，外侧作为算法上下文，不是人工材料负例。此过程细化已提示位置，没有训练或证明未标注区域自动识别。

poly 侧以亮度残差/紧凑小块形状产生 CT 定位候选，只在提示邻域排除可见支持。CT下方材料未知，不因 CT 打孔位置判断是 AA/poly、不填洞或补连接。该检测仍可能漏CT或混入亮边，不能称为完整 CT 真值。

AA只返回示范附近的候选，未标注AA不当负例。冻结配准将部分AA候选映到poly图上作上下文检查，不硬裁剪poly，也不要求栅引出部分全部在AA内。输出均为native px，未改原图/配准/旧阈值实验。

```bash
.venv/bin/silicon-eye annotate guided \
  --spec benchmarks/guided-materials-v1.json \
  -o runs/guided-materials-next
```

[本轮报告](../runs/guided-materials-v1r2/report.md)包含 AA 红色、poly 蓝色叠加，CT未知支持、搜索域/域外未知、正例掩膜、原生轮廓树和来源/代码快照。[AA/poly上下文图](../runs/guided-materials-v1r2/poly-with-aa-context.png)。用户原标注和源图哈希前后核验一致。

新增11项测试涵盖标注差分/颜色、图像尺寸或非标注修改拒绝、原始图像不变、真实合成边界细化、域外未知、CT排除与底层未知、缺正例/非法参数拒绝、端到端原图使用/身份变换上下文与映射/哈希保护。全套120项通过；相关 Ruff、Git diff --check 与来源/输入/代码快照校验通过。

依赖同一人工示例作提示，不能用这些示例的重合程度作独立IoU或准确率。部分确定前景区域直接受标注约束；需要用户复核后，再在未提供提示的保留区域验证泛化。material_status=candidate、accuracy_evaluated=false、device_ground_truth_ready=false；无器件/连接/μm输出，无本轮提交或推送。

## AA v2纠错：不得扩张合并独立块

用户否定v1 AA：中心块与内环没有连接。v1 AA输出撤回为conflict；此前120项测试没有覆盖这项拓扑错误，不能据测试通过宣称真实材料正确。

新增 [v2输入](../benchmarks/guided-materials-v2.json)：AA最大扩展2px；引入无依据合并拒绝门，并记录用户指定的中心/内环原生检查点。若候选吞并多个分开的提示组件，将无依据新增像素标为topology_unknown；不把所有分开涂色区域断言成物理隔离。

[修正报告](../runs/guided-materials-v2r1/report.md)显示中心/内环由相同分量变为不同非零分量，保留暗间隙，7个提示对应7个输出分量。AA支持面积181608→160787 px²，不能称为精度提升量；较小搜索带可能保守收缩材料范围。poly输出逐像素保持不变。

```bash
.venv/bin/silicon-eye annotate guided \
  --spec benchmarks/guided-materials-v2.json \
  -o runs/guided-materials-v2-next
```

新增环内独立块/误桥连两项回归；原先“输出必须扩大”检查改为强内部保留且不超出已知合成材料，因为增长本身不是成功标准。全套122项通过，相关Ruff与来源/源码哈希、Git差异校验通过。用户反馈回归不等同独立材料mask验收；尚不开放器件/连接推断。

## AA / poly / CT 顺序提取检查

用户接受中心块/内环断开修正后，要求同一区域三类材料分别输出。新增 `annotate materials`，在现有1500×850区域内生成独立二值mask、源图像素单独提取图、叠加和native轮廓/分量包围框。

```bash
.venv/bin/silicon-eye annotate materials \
  --spec benchmarks/material-review-v1.json \
  -o runs/material-review-next
```

[按顺序检查](../runs/material-review-v1/report.md)：01-AA红、02-poly蓝、03-CT黄。AA示例邻域严格保留v2修正，邻域外Gaussian/Otsu扫描只产生未复核候选；保留拓扑门和中心块/内环检查。该新增AA仍可能漏掉暗区域内部，不能视为全域完整真值。poly逐像素不变。CT按既有紧凑亮斑定位器扫描第二图全部区域，不限于poly提示范围；不按CT位置判断底层材料。

AA/poly/CT候选支持分别417130/74618/90309 px；连通分量50/26/508，仅为输出几何统计，不是材料对象或接触孔的确认数量。AA确认的间隙仍保留，poly mask复核逐点一致，原图及既有输入哈希不变。3项新增测试验证已知AA邻域保留/间隙不并/未标候选扫描、CT全域可检和异常尺寸拒绝；全套125项通过，相关Ruff和Git差异校验通过。主设备阶段仍未开放，未提交/推送本轮修改。

## 2026-10-15 用户复核版本

用户反馈“除了CT有漏检之外其他的还好”，并要求更新GitHub版本。[复核记录](../benchmarks/material-review-feedback-v1.json)固定了本地报告/三类mask哈希与原始意见：AA/poly在当前局部目视可接受，CT明确存在漏检。该记录不等于精确人工像素真值或全片通过，未测CT召回率，也尚未标出漏检位置。

本次保存代码、参数、125项测试和复核结论为开发快照，不在此提交内继续调整CT。后续优先补充漏检位置标注、改进CT召回，并将已接受的AA/poly作为不得退化的局部比较基线。人工标注图和大体积运行图按既有规则留在本机runs/，远端参数依赖这些本机输入，未宣称无输入即可重跑。
