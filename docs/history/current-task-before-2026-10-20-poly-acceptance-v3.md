<!-- 归档来源：CURRENT_TASK.md；日期：2026-10-20。以下为替换前完整原文。 -->
# 当前任务

## 目标与授权

2026-10-20：继续POLY三项收口，依据用户Q1–Q4反馈作局部修订、验证及复核稿；无新提交/推送授权。昨日4a2fb6c已推送。本文件为唯一实时入口。

## 最新结果与生效裁决

- [v2修订页](docs/assets/poly-closeout-v2/index.html)、[检查点](docs/checkpoints/2026-10-20-poly-closeout-v2.md)、[唯一有效候选](benchmarks/poly-closeout-v2/model-v1.json)、[原话/裁决](benchmarks/poly-closeout-v2/human-review-v1.json)、[验证](benchmarks/poly-closeout-v2/verification-v1.json)。v1保留作历史，不再作为最新有效状态。
- Q1：用户指出旧图过大、偏移过多，替代更贴近。已用30条较小/AA相对位置候选替换旧33条；是偏好方案落地，不扩大为精确边界批准。
- Q2：左上、右上、下方各多一个，9/9/15→8/8/14。左上按G29+G30合计9→8，不是从两个组分别各删1。台阶AA上的栅按局部高度复原，中央4条为2短2长，未用AA外接框。
- Q3：中央为人工确认的宽POLY MOS；左侧为两块AA各2个MOS，共4个。右侧更细、更密，用户推测大于4。当前采用5条AI候选，5不是用户确认的具体数量。
- Q4：AA-F00872为人工确认的旧AA误提，已从有效AA层退休；原图与旧模型不改。该处保持大MOS，G28-P05未缩短，原假冲突解除。
- 有效POLY699个材料对象，AA336个；74条旧POLY候选退休、新增70条。335个历史旧ID退休，记录和来源保留。19个电阻类POLY主体不是19个电阻器件。
- 675条明确AA目标关系通过目标交叠、局部横截面伸出、非目标AA检查；全部多边形合法正交，POLY互相正面积交叠0，已声明结构冲突0。不是材料真值或真实PDK DRC通过。
- 382项全套测试通过，最新锁定记录下10项相关检查通过；Ruff、资源/SVG/XML/PNG、JS语法与模拟DOM回调通过。浏览器真实渲染未自动实测。

## 唯一下一步

请核对[v2页Q3右侧](docs/assets/poly-closeout-v2/index.html#Q3)的5条细密栅及本次整体修订的尺寸、位置。AA灰度暗沟道在sigma=3/4/5/6均为5谷，POLY局部6列亮峰辅助支持5个间隔，但只作为AI候选证据，不确定CT归属。待核记录[R1](benchmarks/poly-closeout-v2/issues-v1.json)。

不重问Q4误提身份、不重跑全幅AA/已审区域。通过显示复核后再决定POLY阶段冻结；当前仍为候选，未宣告全幅定稿或skill封装完成。

## 持续边界

- 本轮之外的有效对象逐字段保留：下中部140条联合几何、U05、S01/S02来源范围、S03-03/04独立性、U10、18条旧电阻主体及SG-U04-W01电阻均保持。Q3新宽MOS和SG-U04-W01是不同对象。
- AA误提只退休用户明确指定的AA-F00872；禁止扩展删除其他AA或退休已审无关POLY。旧源层及照片不覆盖，设计坐标、旧图册坐标、原生来源分别保留。
- 部分新原图轮廓为既有变换导出的定位估计，已明确标记，不能用作精确照片边界真值。Q3的主体观察与AI灰度支持另记；不能用算法峰谷直接定义电连接。
- V3两水平主体保持隔离，无局部POLY桥；U10原形状不重做，照片外的G67不补闭合。顶部界面遮挡、右沿邻片不扩充材料。
- R1/R2非AA间隙、近邻环隔离、原八图、195保留对象与旧网络v33历史裁决保持。AA仓库skill v1未全局安装，POLY skill尚未封装。
- 工艺/尺度、极性、真实W/L、CT逐孔归属、阻值和新增网络仍未确认；相对像素预算不是真实PDK规则，未做DRC/LVS。

## 复现与历史

- `.venv/bin/python -m silicon_eye.poly_closeout --root . --spec benchmarks/poly-closeout-v2/spec-v1.json --output runs/新的反馈修订目录`。
- `.venv/bin/python -m pytest -q`；相关Ruff；`git diff --check`。
- data/原图不改；runs/、.venv/不入Git。本地待提交含今日宽POLY匹配/电阻裁决、v1收口及本轮v2反馈修订代码、基准、复核资产和文档。
- [本轮前完整入口](docs/history/current-task-before-2026-10-20-poly-feedback-v2.md)、[前阶段入口](docs/history/current-task-before-2026-10-20-poly-closeout.md)保留原状态与恢复命令；长期顺序见[开发计划](docs/development-plan.md)。
