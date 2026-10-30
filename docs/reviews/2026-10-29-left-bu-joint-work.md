# 左侧五层规则几何接续与北向新接口

Q1 的 V1 接 M2 A、U 的 V2 接 B-U、D 的 V2 接 B-D 已保存原人审，并进入工作候选。继续向北补 M1 后，在上方发现新 N 孔组；N 的 V1 身份及同一 M2 A 承载仍待裁决，不混入已审14接口。

[完整复核页](../assets/left-bu-joint-work-v3/index.html) · [五层开关／各层原图](../assets/left-bu-joint-work-v3/S5-north/index.html) · [规则几何大图](../assets/left-bu-joint-work-v3/joint-work.png) · [N 两层原生大邻域](../assets/left-bu-joint-work-v3/N-paired.png)。

## 结果与边界

- 工作对象35条金属：M1=4、M2=9、M3=22；14已审局部跨层接口，80显式设计候选孔。新增Q1 5×2、U 3×3、D 5×3只是AI完整阵列候选，孔数及精密尺寸未批准。14组设计阵列的包围／间距通过，不等于实测照片或工艺DRC。
- 原11接口、46孔中心、旧源锚点／骨架／局部块保持。左扩视口至[-1500,0,780,1440]，坐标原点不动，未平移或压缩旧对象。照片坐标与设计坐标仍分开；没有新的投影矩阵。
- 中部M3是上下文交叉；M2 A旁边的小孔列属于另一个M2，无新V2事实不自动连接。N尚未作为接口或候选孔加入工作层；完整网络和其余支路未知。

## 可恢复的分步事务

1. S1只左扩视口，旧对象／接口／审查记录再次全量比对。
2. S2添加来源绑定的M1左返回和M3上／中／下宽带局部块；旧骨架不改。
3. S3添加M2 A和独立清单，旧记录完全保持。
4. S4添加三组完整设计孔阵列，机械适配既有人审，不把当前几何当作曾送审内容。
5. S5继续补北向M1，保存N未知。

[事务记录](../../benchmarks/left-bu-joint-work-v3/transaction-log.json) · [唯一恢复请求](../../benchmarks/left-bu-joint-work-v3/next-request.json)。不得为了纳入左侧源位置修改旧坐标或回到较早模型另起样本。

来源决策适配器为AI记录，核验原问题、原人审原话、源照片、原生孔组范围、两侧来源对象和局部块；模型里的human_review指向真实原人审。身份与承载可接续，数量／尺寸不随之转移。上下端答案串用被拒绝。

## 验证与下一门

162项独立测试通过：分批119、55、16次执行，部分适配器用例重复；不是190个不同用例。覆盖旧回放、只左扩范围、负坐标几何、完整候选孔、原裁决保持、适配器越权／串用拒绝。Ruff、差异格式、来源裁片、静态资源、SVG和PNG检查见[verification.json](../../benchmarks/left-bu-joint-work-v3/verification.json)。浏览器开关交互未实测；程序通过不证明新的物理连接。

[N待裁决请求](../../benchmarks/left-bu-joint-work-v3/north-review-request.json)：M1橙框N是否为V1并接M2 A？M2顶端U已确认为V2，不重问；不要求在M2上看见V1或逐孔上下重合。裁决后才补N接口及完整候选阵列，继续上方横向出口。

README/site的25文件及gh-pages保持，无提交／推送。skill仍LIMITED_TRIAL_V2，geometry_adopted=false，net_edges=[]，complete_network=false。[程序冻结源](../../benchmarks/left-bu-joint-work-v3/producer-sources.json)和原始证据可回查。
