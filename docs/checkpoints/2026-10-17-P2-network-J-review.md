# P2全网点亮推进：停在J公共电极归属

用户授权继续到全网点亮或必须人工裁决。当前以已审H/P2为起点，保留已审gate/P1关系，不穿越电容传播高亮。

## 新交付

- [宽范围原图、候选点亮及J/左邻单元放大图](../../runs/roi2-P2-network-trace-v5/P2-visible-network-J-review.png)
- [原尺寸候选点亮图](../../runs/roi2-P2-network-trace-v5/M3-P2-visible-candidate-wide-native.png)
- [两倍大图](../../runs/roi2-P2-network-trace-v5/M3-P2-visible-candidate-wide-2x.png)
- [原生尺寸mask](../../runs/roi2-P2-network-trace-v5/M3-P2-visible-candidate-mask-native.png)
- [来源、固定参数、阈值试验、决策停点](../../benchmarks/metal-extension/roi2-P2-network-candidate-v5.json)
- [验证清单](../../runs/roi2-P2-network-trace-v5/manifest.json)

## 本轮发现

从H原生参考线附近最大亮脊(2000,4007)为种子，先检查本电极，再扩大到整张M3宽度。局部可见候选含7条清晰横指及左汇流条。扩大后，H所在亮线在J约(1640,4025)处看似向左连续，进一步接入左邻单元的同侧汇流条约(730,4060)，最终出照片左边；两条汇流条还延伸到图底。

此前只点亮H参考段便判断“H可见段完整”过早：现在发现横向可见范围还可向左扩展，该扩展及跨单元共同电极身份尚未确认。不得以先前A内的窗口边界作为实际导体端点。右侧其他电极未因空间邻近接入。

## 固定脚本检查

只对派生灰度图执行GaussianBlur(kernel15×3,sigmaX2.3,sigmaY0.7)，在M3原生ROI [0,3880,5712,4284]做阈值135的8邻域亮度连通域；无膨胀、闭运算或缺口补线。125/135/145三组阈值均出现同一类左向与底向延伸。主mask原生包围范围x0..2503、y3983..4283；对侧汇流条探针(2502,4110)在三组中均属于另一图像连通分量。

阈值稳定/对侧图像分量分开不等于物理同网或异网，也不证明mask为精确材料边界。mask以原尺寸5712×4284保存，不重采样后再追踪。x2050处7条横指只是在此可见范围内的提取计数，不代表完整电容指数量或全电极边界。

## 必须裁决的节点

**J处：H是否作为同一条P2金属向左连续，并接到左邻电容单元的同侧汇流条？**

这会把一个已审电容端口的像素定位扩展成跨相邻单元的公共电极关系，超出原H局部确认范围。暂保留橙色候选，不写入已确认同网或电容数量。J确认后才继续统一该公共分量与其他层接口。

另外，照片左边和底边都是来源覆盖缺口。即使J确认，仍不能凭当前照片宣布全网完整；照片外终点及M2/M3全部接口归属尚未知。附近M2顶部排/F-G支路不能仅凭接近或亮点补接。当前没有足以建立另一条确定过孔边的独立定位证据，暂不扩P1/P2。

## 校验与状态

来源哈希、现有case来源/人审事件/schema、原生mask支撑/边界触及/右邻范围检查通过，图稿目视检查。case v14 state_id仍为702dbe14c70bd5961b7307b5f3458301202aa370a8b9be372ce2940ddd044e67；伴随拓扑v3及原人工记录未改，无新确认并网。只有派生观察/图稿，未改生产代码，未重跑全套软件测试，未推送GitHub。

## 后续确认：J处向左继续；新停点K跨层接口

用户原文“H在J处向左继续”；[反馈](../../benchmarks/metal-extension/roi2-J-left-continuation-review-feedback-v1.json)确认局部同层向左连续，不将它解释为已批准全部左邻电容端口、M2过孔或图外网络。[伴随拓扑v4](../../benchmarks/metal-extension/roi2-gate-MIM-topology-reviewed-v4.json)登记这条局部连续关系，原P1和case v14不变。

复看原生M3，K约(730,4060)处有清晰T形可见连接，可沿图像连续结构推进同层候选。不能因此自动确认左邻单元的所有物理端口身份。继续核查M2，邻近顶部接入排与向上支线可能是跨层接口，但无独立落点证据；新停点为K的M2/M3接入，而不是重复询问J。

[更新宽图/原图对照](../../runs/roi2-J-left-reviewed-v6/J-confirmed-P2-K-interface-review.png)显示J已审、全宽同层mask及K两层检索框。检索框不是过孔位置，M2/M3在此未精确配准；[追踪记录v6](../../benchmarks/metal-extension/roi2-P2-network-after-J-candidate-v6.json)保留其未知。照片左/底边仍被截断，必须另保留覆盖缺口，不以人审连续性关闭图外终点。来源、既有case来源/事件/schema及状态不变检查通过。无生产代码变更、未全套重测、未推送。

## K处只接中间纯竖向M2（伴随拓扑v5）

用户原文“在M2上只接入了中间的纯竖向M2”；[独立反馈](../../benchmarks/metal-extension/roi2-K-middle-M2-review-feedback-v1.json)确认所示K接口只有中间直线接入，左右带横向结构的邻线不接入此接口。局部排除不等于全局异网。

[伴随拓扑v5](../../benchmarks/metal-extension/roi2-gate-MIM-topology-reviewed-v5.json)新增P2→K过孔(V2)→R2_P2_K_middle_M2_01，未改变原gate/P1关系。保留approximate原生M2路径(679,4045)→(681,4100)→(683,4200)→(685,4283)为AI显示几何，不是像素边界或每个点都获人审。[选择图](../../runs/roi2-K-M2-reviewed-v7/K-middle-M2-selected-review.png)、[宽范围2倍图](../../runs/roi2-K-M2-reviewed-v7/M2-middle-vertical-wide-2x.png)、[原图局部4倍](../../runs/roi2-K-M2-reviewed-v7/M2-K-detail-raw-4x.png)保留辨认上下文。

沿选定竖线检查到照片底边，当前没有足以继续定义图外导体/终点的证据。M3图左/图底也仍截断。全网尚未闭合，下一所需是覆盖出口以外的照片或可核实连接证据，不能把边界当断开，也不通过电容并入P1。其他未逐一定位的跨层接口继续保留未知。

来源哈希、case来源/人审/schema/状态与原P1关系保持检查通过；case v14不变，伴随拓扑v5仅记录P2侧已审接口。无生产代码修改，未全套重测，未推送。

## 只使用现有照片继续：新停点L1的M2/M1连接

用户明确没有出口之外照片，要求继续图内追踪。此前“补图才可继续”不是当前推进条件；照片外仍unknown，但先核查图内其他接口。

[四层调查](../../benchmarks/metal-extension/roi2-P2-existing-stack-survey-v8.json)检查中间M2可见段及M1/M3/M4上下文。未找到可稳定追踪的同层横向分叉；M1电容边缘有竖向金属/规则亮点阵，不能确定是M2经V1接入还是下层结构可见。M4只见邻近大金属，没有足以新增V3映射的证据。

在下方阵列ROI [500,4070,1100,4284]用5组初始位移尝试局部ECC仿射，4组未收敛、1组相关约0.49且落到不同周期相位。[试验原始结果](../../runs/roi2-P2-existing-stack-survey-v8/M2-M1-array-registration-trials.json)全部不作为接受变换，没有生成伪精确叠图或把候选配准当连接证据。

[宽范围原图及放大图](../../runs/roi2-P2-existing-stack-survey-v8/L1-M2-M1-wide-review.png)提供一次接口级裁决：中间M2是否还通过V1接到M1电容边缘金属？无需逐亮点核对；紫框为独立原生检索范围，非配准落点。不因为此前F/G不接M1就借用该裁决到K/L1。

新增边为0，case v14/伴随拓扑v5不变；来源、case来源/事件/schema、原生裁剪像素与状态校验通过。没有生产代码更改或全套重测，未推送。若人审也无法确定，保留L1未知并作为现有输入下的明确停止点，不能补出图外线路。

## L1确认，电容类型更正为MOM（当前伴随拓扑v6）

用户回复“是的，这类MOM都是这样进行操作的，多层金属重叠”；[人审反馈](../../benchmarks/metal-extension/roi2-MOM-L1-review-feedback-v1.json)绑定L1问题与图稿。确认P2中间M2经V1接M1边缘金属，所示P2的M1↔V1↔M2↔V2↔M3链已审；类型从此前MIM更正为MOM，不能因此自动并入任意层重叠、其他电容或P1。

[伴随拓扑v6](../../benchmarks/metal-extension/roi2-gate-MOM-topology-reviewed-v6.json)使用中性R2_CAP_01及P1/P2，显式保留旧R2_MIM_01及端口别名。所有历史JSON/图片/裁决及case v14源不修改；case v14保留MOS导出用途，旧文件名中MIM不再作为当前电容类型。[三层关系图](../../runs/roi2-MOM-L1-reviewed-v9/MOM-P2-reviewed-stack.png)仅显示已审端口连接，不声称每个横指的像素边界已审。

[M1延伸观察](../../benchmarks/metal-extension/roi2-MOM-L1-M1-continuation-candidate-v9.json)记录粗竖线参考(712,4035)向下到(720,4283)，上端附近未见可可靠接到上方粗横线的桥接，不能据此断言全局断开或外部电源归属。M4接入与未审的跨层边仍未知。后续按两电极为单位整体复核，不逐亮点裁决。

来源/人审绑定、显式ID别名下P1关系不变、P1/P2未并网、case来源/事件/schema和原state复算通过。局部重复阵列配准仍未接受；不能把人审连接升级成精确像素配准。无生产代码修改、无全套测试重跑、未推送。
