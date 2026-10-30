# 当前入口归档

来源：CURRENT_TASK.md；日期：2026-10-29；以下为 BR-R 返回来源核查前完整原文。

# 当前任务

## 当前目标、状态与授权

**BF24／BF25／BF26局部接触已裁决并落实规则候选。** BF24/BF26本处接上横条BU，已作为两个局部块并入C-M1-SPINE；BF25本处不直接接BU或L1/L2，独立保留为BF25-M1-CANDIDATE，不指定网络或电气悬空状态。当前没有待回复的人审问题，下一步查BR-R长返回线与L1/L2的本处接触及是否绕回BU。

- 用户原话“这个局部区分正确”，只批准这三条的上述接触。BF24/BF26下端是否另有接触没有由本次问题独立确认，保持unknown；精确几何、材料身份升级、V1和完整网络都未获新批准。
- 26条来源清单中只有3条获本处接触确认，其余23条及BR-C/BR-R保持原AI候选/未知。原问题、送审图、原清单冻结，裁决另存覆盖记录，不按类似阵列自动推广。
- 当前32条金属候选（M1=2/M2=8/M3=22）：原31条加BF25独立候选。原30条M2/M3、原M1骨架/宽度及占用、11条已审跨层接口、46个设计候选孔及中心精确保持。无新VIA或net_edges。
- 780×1240规则画布、预算及独立原生坐标保持；source_to_design_transform=null。真实工艺/尺度/孔数/极性/WL/阻值和完整网表未知。金属/VIA skill仍LIMITED_TRIAL_V2。
- README/site/gh-pages保护；本轮仅本地开发，无提交或推送。main起点66a450a（2026-10-28已推送），2026-10-29工作尚未提交。

## 当前接续入口与证据

[三条已审复核页](docs/assets/B-short-finger-reviewed-v2/index.html) · [前后对比](docs/assets/B-short-finger-reviewed-v2/local-before-after.png) · [五层工作页](docs/assets/B-short-finger-reviewed-v2/work/index.html) · [原话/范围](benchmarks/B-short-finger-reviewed-v2/human-review.json) · [当前状态](benchmarks/B-short-finger-reviewed-v2/source-review-state.json) · [26条接续表](docs/assets/B-short-finger-reviewed-v2/reviewed-table.csv) · [验证](benchmarks/B-short-finger-reviewed-v2/verification.json) · [阶段报告](docs/reviews/2026-10-29-B-short-finger-reviewed.md) · [前入口完整归档](docs/history/current-task-before-2026-10-29-B-short-finger-reviewed.md)。

- 分两个事务：先只改C-M1-SPINE的局部外形，再单独以追加来源清单添加BF25。BF24/BF26设计块分别为[31,1023,37,1110]、[115,1023,121,1110]；BF25占用[71,1050,81,1110]，与已建M1最小设计距离21px，沿用3px最低预算。尺寸和坐标均为AI规则候选，不是人工量测。
- L1/L2尚未建模。BF25对下横条的本处未接由原图人审继承，不能声称L1/L2设计间距或返回路径已通过。图中粉/紫色只是工作片段角色，不能当作已确定的不同网络/电容两极。
- 同层接触来源记录没有混入VIA的reviewed_local_connections；跨层记录仍11条。BF25独立候选的材料身份、跨层去向与全局网络未知，不据局部留缝声明无孔或悬空。
- 本轮复用既有workflow，无生产代码变化；26项针对性软件测试通过（新三条5项+局部来源10项+金属扩展11项），Ruff通过。原图/原问题哈希、26行CSV/HTML与3/23状态、旧记录/46孔中心、11组完整候选阵列包围及精确接续检查通过；PNG目视及静态资源/脚本通过，浏览器交互未实测。
- [原26条来源清单](benchmarks/B-short-finger-inventory-v1/observations.json)及[原送审图](docs/assets/B-short-finger-inventory-v1/index.html)保持。14条上接/12条双端见缝原分类仍是送审候选；实时审批看本轮3条覆盖记录。观察上排扩至全支路上下文，没有扩大原工作几何范围或并入下排竖条。

## 必须保持的范围、裁决与未知

- A/B的V1身份及接RT-M2-R01已审，不重问。A来源框[3125,1930,3175,2010]、B=[3130,2775,3180,2845]是站点范围，不是精确孔组外框；每组2×1仍是设计假设，R02其它V1未查清，不声明无孔。
- A右支在x3670出原工作范围，宽图中约x5175下拐；B左支在x2940出范围，约x1682下拐。出界继续不是物理终点，外侧回路未建模。原骨架B近似锚点y2800与横带约y2780的差别不用于平移孔或伪造精确配准。
- 当前走廊3短指是BF24/25/26；BR-R在约x3100处是较长布线上下文，不能混作短指。BR-C与BR-R是邻域框，不是整块排除区。L1/L2左、右段分开，不跨中央返回区合并；BF13正下方在中央布线间隔，未假设有连续横条。
- 原9个V2：R01/R02上端接RT-M3-UP，下端接RT-M3-DOWN；N1→C-M3-L01，03→T01，04→T02，05→E1，06→E2。05/06本处M2不连续，不推导全局异网。08无明确V2是AI范围观察，不是物理不存在；三条弱M3不补建亦不是人审不存在。
- C06原生框[2933,2140,2977,2175]跨原走廊x2940左界，保留原框及人审绑定，不以裁切/扩范围掩盖。原M2/V2/M3覆盖核对仍限原范围，不宣称五层穷尽覆盖。
- 外方阵宏观搜索仅定位。ORB保留点P95约129px及首版边界触带均已拒绝；修正版约2.5px外部参照残差不代表内部孔精度。旧九对V1/V2同孔拟合及4.52px残差不得复活。V1从M1侧识别，V2从M2侧识别。
- 其它区域A={T3,L2}/B={T1,L4}、H1/H2局部隔离、U1/U2同M1、U1/U3经V1接N2、U3已审CT→AA环端子路径及其范围按[前入口完整归档](docs/history/current-task-before-2026-10-29-B-short-finger-reviewed.md)保持，不转移到本走廊。
- 材料快照[joint-work-layer-v5](configs/joint-work-layer-v5.json)为AA334/POLY696/CT10287，规范导体注册表仍[原33记录](docs/assets/conductive-stack-v2/model.json)。六处材料未知AA-F01951、AA-F01952、材料H1/H2、边界AA-F01744、S3-AA4-LEFT-SD-ACCESS保持。geometry_adopted=false、net_edges=[]、complete_network=false、自动网络导出禁止。

## 唯一下一步与恢复

检查原M1照片BR-R长返回线：分别核L1、L2与它的本处接触，再核是否绕回BU；先原生来源、后几何，不用BF25留缝推导全局分网。不重问BF24/25/26或A/B的已审接触，不能把BF24/BF26下端未知自动改成已审断开。遇到新的接触歧义才给宽图和较大邻域图集中裁决。

```bash
# 保持32条金属候选、11条跨层接口、46个孔中心；输出须为新目录
.venv/bin/python -m silicon_eye.conductive_workflow --request benchmarks/B-short-finger-reviewed-v2/next-request.json --output runs/新的B短指接续目录
# 仅原M2/V2/M3范围核对，不能升级为五层覆盖率
.venv/bin/python -m silicon_eye.conductive_coverage --request benchmarks/conductive-corridor-closeout-v2/request.json --output runs/新的覆盖核对目录
```

图像资源按哈希复用。首次三条构建的可恢复备份在runs/B-short-finger-initial-review-build-v2，不作为当前裁决；现行记录见本轮human-review。此前重复资源备份在runs/corridor-m1-v1-pre-resource-reuse-v2。其它V1分支从benchmarks/v1-new-short-branch-reviewed-v2/next-request.json恢复，旧中样从benchmarks/m1-local-tab-v1/work-next.json恢复。不得自动重建README/site或发布gh-pages。
