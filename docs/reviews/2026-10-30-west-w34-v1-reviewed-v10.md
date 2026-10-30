# W3/W4四V1接续与固定M1覆盖缺口

保存原话“W3-N、W3-S 均为 V1，接 W3”“W4-N、W4-S 均为 V1，接 W4”，绑定原请求、源观察及四份原生大图。四处新V1均接对应M2；身份/承载裁决不覆盖孔数、尺寸或精密投影。按金属/VIA重建skill限定试用规则，先只给C-M1-SPINE追加上下横条、W3台阶、W4窄承载，再加入三组2×2与一组2×1(W4-N)完整AI候选阵列。W4-N未套用宽台阶模板，物理数量仍未知。

[复核页](../assets/west-w34-v1-reviewed-v10/index.html) · [五层切换](../assets/west-w34-v1-reviewed-v10/S2-W34-V1/index.html) · [规则几何](../assets/west-w34-v1-reviewed-v10/joint-work.png) · [恢复请求](../../benchmarks/west-w34-v1-reviewed-v10/next-request.json)。同页可切换同坐标前后设计。

现有39金属、30已审局部接口、179设计候选孔。旧26条批准、165孔边界/中心和旧骨架/宽度/源锚点/原局部块保持；只M1追加4块，其他38金属完全相同，原点/视口/尺度不变。两事务/恢复精确回放，30组完整设计候选的包围与间距通过。来源阵列精密几何、物理孔数/尺寸与真实PDK DRC未验收。

本轮从继续逐点加样本转为固定范围覆盖核查。[M1来源→几何→接口清单](../../benchmarks/west-w34-v1-reviewed-v10/scoped-M1-coverage.json)限定原生范围[300,1870,830,2820]，声明10个AI可见片段：2个上下主干已建，1个W4北竖支仅承载局部已建，另7个细横条/竖支/底部片段未建或归属未知。W3/W4本批8个V1/V2接口全部已审、工作层均已接续；这不意味着所有细支路或M2/M3导体已覆盖。覆盖门明确为COVERAGE_INCOMPLETE，清单条数不充当照片穷尽证明。

[连续原图](../assets/west-w34-v1-reviewed-v10/M1-band-marked.png) · [中段放大](../assets/west-w34-v1-reviewed-v10/M1-middle-marked.png) · [CSV](../../benchmarks/west-w34-v1-reviewed-v10/scoped-M1-coverage.csv) · [接续计划](../../benchmarks/west-w34-v1-reviewed-v10/next-gap-plan.json)。先补L03余段，再独立补L07/L08中部两横条、查L04/L05/L06细竖支，L09/L10底部左右片段分开保留。来源片段ID不是电气ID；不按邻近/同高合并，不把中段横线凭相似度分给旧L1/L2。只有新身份/连接歧义才送审，旧接口不重问。

38项相关来源/接口测试通过；[固定工程回归](../../benchmarks/west-w34-v1-reviewed-v10/fixed-regression.json)另有31项测试通过、历史模型精确回放和245条证据路径核对。它不是AI重新识图，未测新准确率；浏览器交互未实测。原图裁片/静态链接/脚本/前后SVG/PNG与旧对象防退化见[验证](../../benchmarks/west-w34-v1-reviewed-v10/verification.json)。程序未改，README/site的25文件及gh-pages保持，无提交/推送。skill仍LIMITED_TRIAL_V2，source_to_design_transform=null，geometry_adopted=false，net_edges=[]，complete_network=false。
