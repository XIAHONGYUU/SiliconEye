<!-- Source: CURRENT_TASK.md; archived 2026-10-19 before POLY-AA correspondence review. Original content below. -->
# 当前任务

## 目标与授权

2026-10-19：继续推进并复核上方小栅结果。授权本地实施与验证；没有新的Git提交/推送授权。唯一实时入口为本文件；[开发计划](docs/development-plan.md)、[完整前入口](docs/history/current-task-before-2026-10-19-poly-small-batch.md)保留其他阶段及历史恢复信息。

## 当前结果与唯一下一步

- **上方九组小栅AI复核稿**：[页面](docs/assets/poly-small-gate-batch-v2/index.html)、[检查点](docs/checkpoints/2026-10-19-poly-small-gate-batch.md)、[来源清单](benchmarks/poly-small-gate-batch-v2/source-inventory-v1.json)、[验证](benchmarks/poly-small-gate-batch-v2/verification-v1.json)。覆盖F01–F04原U01–U09，共27段与Q01专门窗口；左下U12–U17及整芯片不在本轮范围。
- 原305条来源观察保持，用户新增确认Q01是一个宽POLY栅，登记SG-U04-W01，现共306条主体观察（80条U04小栅+1宽栅）。8条显示范围已审；S03两条及宽栅是身份确认，不扩大到精确边界/电连接。298条未合并观察的layout_outline为空。306不是MOS器件数量。
- [Q01人工裁决](benchmarks/poly-small-gate-batch-v2/human-review-v1.json)关闭该材料分类歧义；宽矩形来源轮廓仍为AI候选。撤回的3条小栅匹配不恢复。666个原对象和原305条来源观察保持不变，已审联合图、F05、U10、S01/S02及S03裁决继承。
- 81条AA拓扑对应仍是假设。此前17项相关测试通过；本次无代码改动，核对新增对象、唯一ID、来源哈希、保持性及链接。新观察尚未并入共同AA设计几何，实际PDK DRC/LVS未完成。
- **唯一下一步**：接续当前306条来源清单，明确宽POLY及复杂小栅的AA对应，生成共同设计几何并核对正交、匹配、伸出与避环；对已有81条对应假设先做结构验证。保留来源证据，不因约束冲突回退已确认材料身份，不重问S01/S02/S03及Q01身份。其余新候选没有被本次身份裁决整批批准。

## 生效裁决与方法边界

- [联合版图架构](docs/architecture/layout-reconstruction-v1.md)：原始照片/来源坐标与设计坐标分开；相对关系和正向结构约束优先。工作AA/POLY可据证据定向联合修订，材料身份、隔离、器件/net编号不能被几何修订悄改。
- AA采用[已审入口](docs/assets/aa-full-frame-workflow-v1/reviewed.html)和[模型](benchmarks/aa-full-frame-workflow-v1/model-v1.json)。R1/R2之间非AA、两近邻竖环隔离；AA仓库skill v1已封装未全局安装，不重开整幅审查。全幅稠密精度和跨芯片泛化未知。
- POLY下方140条联合关系及F05显示范围通过；U10形状和18条电阻主体等既有范围保持。普通MOS不自动补凸形/狗骨头；POLY不能被AA统一裁剪。V3两栅没有局部端部POLY桥，远处金属同网不改变该裁决。
- [小栅已审基线](benchmarks/poly-small-mos-local-v3/accepted-local-model-v1.json)：S01/S02来源显示范围累计8条通过；S03-03/04独立身份通过，未扩大为7条精确边界或电连接批准。当前候选模型继承此基线，保护ID随版本接续。
- CT分布可辅助判断数量、端部和独立性，不单凭亮点分配材料、孔归属或电网络。旧修正mask的0不是确认非POLY，拓扑/CT遮挡未知保持。照片外不猜连接，照片左沿不闭合残缺对象。
- AI主导、算法辅助细节，所有比较按相同成图标准。原图不可改；物理尺度/工艺、N/P、真实W/L未知，相对像素预算不冒充PDK数值。POLY skill不封装。
- 原八图、195保留对象和旧网络v33等历史裁决维持；区域分类不成为跨区域走线边界。[完整归档](docs/history/current-task-before-2026-10-19-poly-small-batch.md)含前轮资产、解释与恢复命令。

## 接续与复现

- 当前候选模型：[链接](benchmarks/poly-small-gate-batch-v2/model-v1.json)。父模型666对象不变；298条新来源观察位于unmerged_local_observations，不是已应用材料层。
- 定位实验：`.venv/bin/python -m silicon_eye.poly_gate_matching --root . --spec benchmarks/poly-small-gate-batch-v1/matching-spec-v1.json --output runs/新目录`。
- AI已裁定的来源候选：`.venv/bin/python -m silicon_eye.poly_local_revision --root . --spec benchmarks/poly-small-gate-batch-v2/spec-v1.json --output runs/新的复核目录`。本入口不重跑首尾插值模板；历史spec仅用于复现历史。
- 原始照片在data，.venv/与runs/不入Git；复核资产/基准在仓库。45项旧输入恢复方式见前入口与benchmarks/evidence/poly-reconstruction-v1d-evidence.zip。
- 当前工作树含多阶段未提交修改，不覆盖/清理；本轮新增匹配模块、两处测试及小栅批量基准/资产，修改局部复核器以保留已审颜色和跨窗口去重。匹配和复核开发输出a/b不是独立准确率实验。
