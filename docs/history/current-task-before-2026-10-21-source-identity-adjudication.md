# 当前任务入口归档

来源：CURRENT_TASK.md；日期：2026-10-21；正文SHA256：0af01a0b06126bb5b8702b7419a091bc09d4c0ee785fe4949c44256f668f231b

---

# 当前任务

## 最新授权与结果

2026-10-21用户要求解决三处来源归属。已完成AA／POLY／M1结构回查并仅修订73条CT来源记录；原16对争用变为0，新增争用0，联合几何与来源门均PASS。原图、材料／CT几何及已审连接均未改动。新版本是AI来源修订工作版本，未新增逐孔人工批准；本机修改尚未提交／推送，远端仍为此前已核对的 `6e5bb17fc024f1410f49a580e2e5100eda35e2a6`。

本文件为唯一实时入口。[实施与验收报告](docs/reviews/2026-10-21-joint-continuation/report.md)、[接续机器核验](docs/reviews/2026-10-21-joint-continuation/verification.json)、[本轮来源核验](benchmarks/ct-source-ownership-v1/verification-v1.json)、[当前共同快照v2](configs/joint-work-layer-v2.json)；[三处来源修订说明](docs/reviews/2026-10-21-source-ownership.md)、[层切换与前后复核页](docs/assets/ct-source-ownership-v1/index.html)、[本阶段前入口原文](docs/history/current-task-before-2026-10-21-source-ownership.md)。[实施前入口完整原文](docs/history/current-task-before-2026-10-21-joint-continuation.md)保留原审计发现及全部既有边界；[实施前审计](docs/reviews/2026-10-21-aa-poly-ct/report.md)是历史状态，不再作为当前缺陷状态。

## 现在可以接续什么

- 共同快照锁定AA334／POLY695／CT10287，设计画布5860×4587，原图5712×4284，以及原8图哈希、预算、原5处来源限制、原人审范围和3处已修订来源记录。AA337／POLY700历史文件不再作为当前几何输入。
- `joint_layers`解析退休别名、校验跨层引用，拒绝循环／悬挂／错误层和显式退休ID复活。AA工具有当前视图，多份合并来源分别保留，不能自动当作精确单投影。
- POLY门已接受G68明确桥与成员的2对合法相交；断桥及任意其他栅交叠仍失败。G26按阶梯共享AA局部截面检查，已审几何不用为消除假警报而改动。
- CT局部修订必须通过AA＋POLY＋CT＋全量源点争用联合门，两个退化反例在写出前被拒绝。指定`joint_snapshot`才能声明接续当前共同版本，输入及预算须吻合。
- 当前全幅**三层几何及来源门PASS**。三处旧来源争用已通过源点修订消除；恢复G34旧取点会被门拦住。没有自动整网放行；PASS仍不代表全孔物理真值或新人工批准。旧v1共同清单及全部冻结原文保留。
- AA与CT各完成一次无变化接续及候选清单重载：三层全部对象逐条相同，未知、限制和人审保留；未借此要求用户重审。470项测试通过（69.76s），相关Ruff通过。软件测试不替代材料与Agent判断质量。

AA已有仓库人机协作skill；此前已适配工具接口，未封装POLY／CT专用skill，未证明新芯片泛化。完整复核包统一与独立Agent任务评测仍待推进。

## 本轮三处来源修订及仍保留的限制

[修订事务和台账](benchmarks/ct-source-ownership-v1/ledger-v1.json)：S1外围环误用右边中部MOS环，邻接宽MOS源漏又误用外围环，共修66条；S2栅端搜索窗口扫到下方环，修6条；S3相邻MOS源漏上下错开，AA4旧修订向下漂移到AA3，修1条。全部设计坐标、承载目标、M1／net字段不变，10214条CT记录完全相同。所有旧观察追加保留于source_correspondence_history。

新增固定回归及相关CT测试33项通过（28.29s）；确认73条事务可重放、全部几何／限制保留、恢复错误来源会被拒绝。修订记录与任何目标在内的其他源点3px内均无近邻争用。页面图像已直接检查、JS语法通过；浏览器工具策略禁止自动打开file协议，未执行浏览器交互截图验证，无需绕过。

原[5处来源限制](benchmarks/ct-work-layer-final-v5/exceptions-v1.json)继续保留：AA-F01951、AA-F01952、H1、H2、照片边界AA-F01744；V3两主体截段的历史端子例外另列。原CT工程收口仍成立，未升级为100%物理孔恢复或整层人工像素批准。

## 继续生效的用户裁决与保护范围

- 四栅G06R-P01～P04及33条CT已补齐，原五模板退休；R1A／R1B上端、均匀源漏孔、R2本处连续AA单排孔及旧Q1／Q2／Q3继续生效。R2材料别名、原10254父CT和原7044已审记录保持；其他近邻环隔离／非AA间隙不受影响。
- C/D/F、143橙框、RIGHT6、宽MOS／环／电阻、Q2栅60孔、上方40栅、左侧局部、原661环孔及B孔数精度意见按原范围保留。R2_Q1、V3历史端子、网络v33、S03-03/04、18条电阻、W01电阻身份、195保留对象不改。
- 原8图和所有父冻结包不改。物理尺度、工艺、极性、真实W/L及阻值未知；相对像素规则不是实际PDK DRC/LVS。未启动新M1／net，未扩大提取范围。

## 唯一下一步与恢复

下一步将这次有真实照片证据的来源事务作为接续验证样本，补统一复核包对来源／限制的稳定交付，再推进POLY／CT skill封装及少量留出任务评测。复核页供用户按S1／S2／S3抽查；若有新反馈，沿原生位置局部改，不重验全部孔。

- 当前联合检查：`.venv/bin/python -m silicon_eye.joint_layers --snapshot configs/joint-work-layer-v2.json --output runs/新的联合检查目录`。
- AA／CT局部spec添加带哈希`joint_snapshot`；输出`joint-snapshot.json`为可重载候选，继承的阶段／use-contract／人审不等于新候选批准。当前AA入口只做已存在对象细化；分裂／合并须同步处理跨层引用，合并AA细化须先提供新局部对应。
- 接续重放样例、纯层API、CLI状态解释和验证路径见实施报告。`runs/`仅本地，`data/`与冻结包不改；`git diff --check`和相关测试。实施前原审计脚本在新代码下结果会改变，不能当成原历史状态的完全复现。
