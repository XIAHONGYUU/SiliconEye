# 固定M1范围补齐与覆盖验收

原清单中L03部分竖支和L04–L10七个未建片段已补入工作几何。对相同原生范围[300,1870,830,2820]独立扫图发现旧清单漏了L11主干向下出口、L12底部左段回折，也一并补入；未扩大统计范围。旧10片段清单不回写，修正清单12/12均有对应几何，不将声明清单对应率当作照片穷尽或全网覆盖率。

[集中验收页](../assets/west-m1-coverage-v11/index.html) · [五层切换/原图](../assets/west-m1-coverage-v11/S3-L09-return/index.html) · [联合图](../assets/west-m1-coverage-v11/joint-work.png) · [完整局部图](../assets/west-m1-coverage-v11/local-full-after.png) · [覆盖清单](../../benchmarks/west-m1-coverage-v11/scoped-M1-coverage.json)。同页可切换修订前后同坐标设计及无标记原图，原图和设计是独立坐标域，没有未验证投影。

按金属/VIA skill限定规则，三个事务分别补旧主干的L03余段/L11、增加七个独立M1 ID、给新L09补L12回折。原C-M1-SPINE追加两块，新L09追加一块；其他38个旧金属、旧骨架/宽度/源锚点/原局部块、30条人审与179孔边界/中心保持。现在46金属（M1=11/M2=13/M3=22）、30已审接口、179候选孔，无新VIA或网边，原点/视口/尺度不变。

L04/L05/L06保持独立片段，端部不因邻近而桥接；L07/L08分别建中部上下横条，不凭同高/外观指派旧L1/L2；L09/L10左右分开，L12接L09并向下，L11从下宽主干向下出本范围，两者保持间隙。L11/L12的下沿只是本次范围截断，原图范围外仍有继续，不能称物理终点。

同层正交、宽度/间距、30组完整候选孔包围通过；6项来源次序与10项局部留隙通过。来源次序调用既有source_order_audit独立检查新增组，不改写已冻结的旧次序契约。三事务和当前恢复精确回放，49项局部来源/金属/接口测试通过，[固定工程回归](../../benchmarks/west-m1-coverage-v11/fixed-regression.json)另31项测试通过、历史模型精确回放；不是新AI准确率评测。

[Q1原图](../assets/west-m1-coverage-v11/source-middle-marked.png) · [Q1规则图](../assets/west-m1-coverage-v11/local-middle-after.png) · [Q2原图](../assets/west-m1-coverage-v11/source-bottom-marked.png) · [Q2规则图](../assets/west-m1-coverage-v11/local-bottom-after.png) · [验收请求](../../benchmarks/west-m1-coverage-v11/coverage-review-request.json)。只需验两组新几何：Q1竖支/中部横条次序、长度、留隙；Q2底部左右片段/新出口/短回折及遗漏。旧接口/孔数不重审。工程对应PASS与视觉来源验收PENDING_HUMAN分开，后者未获批准。

来源/原图裁片/资源/脚本/新旧设计与PNG核查见[验证](../../benchmarks/west-m1-coverage-v11/verification.json)。程序未改，浏览器交互未实测，物理孔数/源精密几何/PDK尺度与全网未知。README/site的25文件及gh-pages保持，无提交/推送；skill仍LIMITED_TRIAL_V2，source_to_design_transform=null，geometry_adopted=false，net_edges=[]，complete_network=false。下一步按Q1/Q2验收局部更正或收口该固定M1范围，再选相邻层连续范围覆盖。
