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

## CT重提取v2：保留AA/poly基线

[本轮CT检查](../runs/material-review-v2/CT-report.md)及[参数](../benchmarks/material-review-v2.json)：新增显式`ct_profile: narrow_vertical`，允许宽>=3px、高>=5px、0.25<=宽高比<2的亮点组件；灰度>190、局部残差>18及其余限制不变。未配置该字段时仍走legacy，guided默认行为不变。

```bash
.venv/bin/silicon-eye annotate materials \
  --spec benchmarks/material-review-v2.json \
  -o runs/material-review-v2-next
```

v2重新导出的AA/poly mask与已获局部目视认可的v1文件字节完全相同。CT候选分量508→703，新增30075px、旧支持移除0px；30处参与调参的AI目视候选窗口覆盖26→30，不是独立召回率。更多候选也可能包含亮边/拍屏纹理误报，需用户复核，不能根据数量直接认定精度改善。

新增窄CT恢复且不选长亮线、非法模式拒绝两项行为测试；全套127 passed及相关Ruff通过。原图和旧输出保留，未推送。

## CT v2用户批准

2026-10-15用户明确批准当前图的CT v2，认为基本没有问题。[追加复核记录](../benchmarks/material-review-feedback-v2.json)绑定上一条展示的新增支持叠加图、CT mask、报告与manifest哈希。AA/poly与原认可结果文件字节一致，因此三类材料作为当前1500×850局部基线。

原运行证据保持生成时状态，人类批准单独追加，不追改历史输出。该认可仅为本图目视通过，不扩大为全片、其他区域、量化召回率或器件/连接验收。下一步在已配准局部检查MOS沟道候选与CT端子归属。

## 局部MOS结构检查

```bash
.venv/bin/silicon-eye annotate mos \
  --spec benchmarks/local-mos-review-v1.json \
  -o runs/local-mos-review-next
```

要求本机已存在参数绑定的批准记录、材料mask、样片元数据、源照片和冻结配准；任一哈希变化拒绝运行，输出必须为新目录。[检查包](../runs/local-mos-review-v1r1/report.md)给出两处短栅及中央双横带AI候选，包含原图/配准AA/交叠/敏感性四联图。

仅将AA变换到poly裁剪坐标，单位px；交叠不是确认沟道，CT相交/距离不是端子连接。宏观试验12 AA px预算换算13 poly px敏感性半径，不是局部置信界；被CT遮挡的材料及端子、器件数均保持未知。该入口不接入Pipeline确认器件阶段。

2026-10-15后续人工复核：[局部结构批准](../benchmarks/local-mos-review-feedback-v1.json)确认V1/V2各一个MOS，V3为两个MOS共用源/漏扩散区。原运行结果保持生成时未知状态；追加复核记录提供新的局部器件数和共享关系，不据此确认具体CT归属、源漏极性、栅连接或精确尺寸。

## 端子位置与CT归属检查

```bash
.venv/bin/silicon-eye annotate terminals \
  --spec benchmarks/local-terminal-review-v1.json \
  -o runs/local-terminal-review-next
```

[检查报告](../runs/local-terminal-review-v1r1/report.md)提供原图/端子窗口和CT标号图、contacts.csv、manifest.json及connections.mmd。AI在原图上提出检查窗口；脚本仅执行来源校验、窗口归属检查和导出，无运行时模型。窗口是可调整的候选提示，不是材料分割或电气连接证明。

V3的共享扩散关系继承用户确认，中间CT行的位置是新候选；G1/G2在poly mask的同分量证据不自动合并栅。多端子窗口相交记conflict，裁剪外质心或无匹配不强行分配；一个CT分量可包含多处亮斑，分量数量不代表实际触点数。两处目视亮斑漏检候选单独打叉，批准的mask保持原值。仍使用px，源漏极性/体端/金属连接保持unknown。

后续[人工裁决](../benchmarks/local-terminal-review-feedback-v1.json)：V3中间M为共用源漏区；G1/G2未通过局部端部poly相连。两栅保留不同节点，原poly跨栅连通分量24标为拓扑冲突，禁止据此合并。具体像素切割待原图定位；该裁决未批准逐CT连接，也不排除其他位置的金属连接。历史导出保持生成时状态，新的结构判断以追加复核记录为准。

## V3 poly拓扑修正候选

```bash
.venv/bin/silicon-eye annotate poly-repair \
  --spec benchmarks/local-poly-repair-v1.json \
  -o runs/local-poly-repair-next
```

[修正检查包](../runs/local-poly-repair-v1/report.md)给出全景、左右端部的原图/旧新支持/差异。AI在共享M行选择分隔域，脚本从旧poly正支持中撤销该域，分别输出拓扑未知与CT下层未知，绝不将不清楚像素写成已确认非poly。端部及内部桥接同时检查，旧文件不覆盖。

两栅代表点通过全图8连通分离验证；可见栅保护带、域外poly、AA/CT和M共享关系不变。不同带宽的拓扑检查仅验证候选稳健性，不等同精确像素边界验收。下游使用`02-poly-mask.png`时必须同时保留`poly-topology-unknown.png`与`retired-CT-underlying-unknown.png`；mask的0只表示没有当前正支持。该版本未自动替换已批准材料基线或逐CT归属。

后续用户“核对正确”：[修正批准记录](../benchmarks/local-poly-repair-feedback-v1.json)将本次修正版及两类未知域固定为后续局部CT归属检查基线。原运行manifest保持生成时状态，批准单独追加；范围为本次局部目视修正，不扩大为精确像素真值或逐CT连接批准。

## 逐CT视觉核对与候选导出

```bash
.venv/bin/silicon-eye annotate ct-audit \
  --spec benchmarks/ct-terminal-audit-v1.json \
  -o runs/ct-terminal-audit-next
```

[逐项核对包](../runs/ct-terminal-audit-v1r2/report.md)包含90条原有CT分量的AI看图记录、per-contact.csv、原生坐标和图格索引；运行时仅脚本校验/导出，不调用AI。AI记录显式写入参数，脚本不以窗口命中冒充视觉审阅；缺项、重复或试图自动确认为电气连接时拒绝运行。

75个分量保留端子候选、7个弱亮斑存在性不确定、7个在MOS ROI外排除、C311为疑似纹理误报。14个分量含多个可见亮斑，禁止把分量数量当真实CT数量。P1/P2为既有漏检候选，P3为新增窄亮斑/条纹歧义，均未改CT mask。

必须使用获批修正版poly及两类未知mask；交叠只作诊断，CT轮廓同时碰到两栅正支持也不合并栅，未知域不能充当材料负例。当前逐CT判断仍为AI候选，需与已有人工结构批准区分；异常点和归属复核后再生成CT修正。

## 器件与M1网络检查（当前采用）

用户调整工作粒度：关注MOS、尺寸、四端连接；逐CT审阅留作诊断历史，不作为后续推进门槛。接触区域用于支持网络判断，只将影响网络拓扑的歧义交给人工。

```bash
.venv/bin/silicon-eye register-local \
  --spec benchmarks/registration-local-poly-m1-v1.json \
  -o runs/registration-local-poly-m1-next
.venv/bin/silicon-eye annotate networks \
  --spec benchmarks/device-m1-network-v1.json \
  -o runs/device-m1-network-next
```

网络参数绑定已生成的配准manifest；重跑配准到新目录后，需显式更新绑定路径/哈希再用于新网络实验。保持旧实验参数不变，另存新版本。

[四MOS网络检查包](../runs/device-m1-network-v1r1/report.md)：AI看图提出局部M1中心线路线与接触组归属，脚本验证来源、M1-native/poly-native变换与有效覆盖，导出器件—网络候选图及原图对照。彩线非自动分割金属边界，不据路线几何邻近自动并网。

七个局部网络均为候选，体端及源漏极性未知。V3两物理栅仍分开，但允许提出“经M1接到同网”的新假设；这与人工确认poly端部不连并不矛盾。几何尺寸仅显示可见支持的px跨度及截面长度，窗口截断/CT遮挡/配准会影响数值，不当真实W/L。独立环四角检查满足宏观预算，不代表微小接触已验收。

后续[网络复核记录](../benchmarks/device-m1-network-feedback-v1.json)：用户确认V1/V2细支路与底部U形M1在当前局部保持断开；不扩大为远处或M2不连接。V3关系尚待查看更清晰照片和M2后判断。

[原生M1/M2参考包](../runs/m1-m2-reference-v1/report.md)按`benchmarks/m1-m2-reference-v1.json`裁剪现有JPEG解码像素，输出无缩放、无叠加、无锐化PNG；原生坐标与哈希记录在manifest。M1-V3细节未作配准重采样；M2只提供宏观搜索区域及更大上下文，没有合格局部变换，不能当精确对应或用同尺寸合并。缩小定位图单独保存。

最新[人工拓扑复核](../benchmarks/device-m1-m2-topology-feedback-v1.json)确认V3_G1/G2至少经M2同网。两栅物理身份与poly分离保持；公共栅网络N3_G与共享扩散N3_M是否连接仍未知，不能沿用旧N3_MG整体并网作为已确认结论。[更新器件表与图](../runs/device-m1-m2-reviewed-v1/report.md)单列这两个关系。M2精确过孔路径仍未由脚本核验，本次确认来源为用户。
