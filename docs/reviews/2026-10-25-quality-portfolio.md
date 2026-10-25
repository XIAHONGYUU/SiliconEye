# 展示质量与历史评测整理

基线53a1dcf。用户批准按“纠错案例→小型评测→可信结果进首页”的顺序优化，并补充样本说明与轻量CI。评价报告中的旧版展示描述未沿用，原始材料/金属事实和人工裁决不变。

## 交付

1. [六孔承载纠错案例](../portfolio/quality-case.md)：并列旧窄A/代理孔与修正宽B/六孔模型，原生M1/M2照片独立展示；精确尺寸仍为候选。
2. [8任务目录](../../benchmarks/portfolio-quality-v1/README.md)：六项人工rubric、两项沿用机器评分器；每项绑定输入/参考/考点和限制，20条历史部分参考中16条已知、4条未解决。
3. 首页结果卡：AA三项已知任务历史验收、8项任务目录、本页展示的两条AI失败记录；工作层对象规模与六处未知区域分开说明。新模型运行0、留出任务0，准确率与人审总成本保持null。
4. [来源说明](../portfolio/data-sources.md)：按用户既有陈述说明光学显微镜与手工拍屏来源；不冒认SEM/开放训练集或替第三方声明许可。
5. [公开包CI配置](../portfolio/ci-workflow.yml)：固定官方Actions提交，contents:read，稀疏检出公开包和两个保障测试。无自动模型调用、无自动部署、无完整项目测试或物理验收声明。

## 验证

- 来源目录审核：20个证据文件逐项SHA匹配，构建来源/公开资产全部匹配。
- 32项相关测试通过：公开口径保障、归档保障、现有Agent评分器、堆叠孔规则；另5项六孔承载回归通过，共37项不同测试。未合并重复的13项稀疏环境测试。
- 在不含历史证据/项目依赖的临时稀疏目录，公开包检查与CI对应13项测试通过。
- Ruff、JS语法、SVG/XML、相关Markdown/HTML链接、原始README/CURRENT_TASK归档字节及源模型未改检查通过。
- Playwright Chromium在1440×1000和390×844验证案例、结果卡、任务rubric、原生证据展开与已有切层/器件/孔组交互。手机窄表列问题已改为卡片并复核。无页面错误、缺图或横向溢出。

[本轮检查记录](../../benchmarks/portfolio-quality-v1/verification.json) · [浏览器记录](../../benchmarks/portfolio-quality-v1/browser-verification.json) · [展示QA](../../benchmarks/portfolio-quality-v1/visual-review-v2.md) · [发布/CI回执](../../benchmarks/portfolio-quality-v1/publication.json)。

## 实际发布

展示内容已推送至main的535e159，Pages为6417cc9并构建成功。根页面及23个公开文件HTTP读取成功、SHA与本机一致；远端README字节一致。发布回执保存实际提交和CI待启用原因；后续回执提交不改变展示内容。

## 在线CI权限阻塞

GitHub拒绝推送工作流，明确要求当前OAuth凭证具备`workflow`权限。CI配置移到docs/portfolio/ci-workflow.yml供审阅，本机对应13项检查通过；线上CI尚未启用，不用本机通过代替在线结果。展示和评测数据继续正常发布。

## 未完成与边界

本轮整理并没有重新运行视觉Agent，不能把“历史证据核对通过”叫作8/8识别正确。H01–H06仍是人工rubric；H07/H08已有独立输入包与评分器，但尚无本轮实际预测。未来先冻结新的未经人审修改输出，再评分与记录人审负担；留出须在调试前确定。

没有移走冻结证据或重写Git历史。大文件迁移需另作引用/哈希/下载恢复方案。原开发待审的V1/V2重叠与Q2几何仍保留，不因展示通过而批准。
