<!-- 来源：CURRENT_TASK.md；2026-10-20 Q1–Q4反馈落地前完整原文。 -->
# 当前任务

## 目标与授权

2026-10-20：用户授权POLY三项收口：单一有效版本、全幅AA/POLY联合检查、整体复核图及最小新增问题清单。允许本地候选实施、验证和文档更新；无新Git提交/推送授权。昨日4a2fb6c已推送，本文件为唯一实时入口。

## 当前结果

- [收口页](docs/assets/poly-closeout-v1/index.html)、[检查点](docs/checkpoints/2026-10-20-poly-closeout.md)、[唯一有效候选](benchmarks/poly-closeout-v1/model-v1.json)、[检查报告](benchmarks/poly-closeout-v1/report-v1.json)、[验证](benchmarks/poly-closeout-v1/verification-v1.json)。
- 有效703个POLY材料对象：269条旧模板记录被替换，8个ID保持、261个旧ID退休，接入306条来源；全部原记录可追溯。19个电阻类POLY主体不是19个电阻器件。共同坐标为AA工作设计坐标，原生来源和旧已审图册几何另存。
- 下中部140条已审联合几何保持；小栅305条关系接续，只对U05所示关系继承批准。新补160条显式AA关系候选，仍未人审。605条目标AA交叠/伸出预算通过，但有1条非目标AA冲突，严格关系门FAIL；全部703个多边形合法正交、POLY互相正面积交叠0。
- SG-U04-W01经用户确认是POLY电阻、显示位置非AA，撤回旧MOS栅解释；不补AA。共同设计候选按上下AA框架的相对位置构造，不重开材料分类。
- 修正质量门：不能因结构组名含GUARD就将其中器件AA误判为环；使用显式对象角色。未知工艺下相对像素预算不是实际PDK规则。
- 378项测试通过，新增6项回归；相关Ruff、静态资源、SVG/XML、PNG、JS语法及模拟DOM回调通过。浏览器实际渲染未自动实测。质量门仍阻止定稿。

## 唯一下一步：用户一次裁决 Q1–Q4

见[复核页](docs/assets/poly-closeout-v1/index.html)与[问题清单](benchmarks/poly-closeout-v1/issues-v1.json)：

1. Q1：上中排10块AA的栅数是否为2/1/2/1/4/2/4/2/8/4（30条）；旧33条未自动替换。
2. Q2：中部右上是否4+4=8条，下排是否5/2/2/5=14条；旧9/15条仍保留，台阶AA不能用外接框统一栅长。
3. Q3：左中紫框均匀矩形是POLY/宽栅还是仅AA/dummy，旁边旧3+5条有无明显多漏。紫框未填材料。
4. Q4：蓝色AA短条是独立环/AA，还是上方大AA边缘残片。当前G28-P05与其约4工作像素冲突，不能先合并AA、删条或缩栅骗过质量门。

收到裁决后仅修订相应局部并重跑同一门，不从头要求全幅重审。当前状态为收口候选，POLY未正式定稿、skill未封装；不以软件测试或候选几何通过替代材料人审。

## 持续边界与保留结果

- 原始照片、AA输入基线、来源几何及所有锁定输入哈希保持。AA/POLY工作几何与来源坐标分离，新的联合坐标不自动继承旧精确尺寸批准；材料身份、隔离、器件/net编号不得悄改。
- S01/S02八条来源范围、S03-03/04独立身份、U05整排、F05已审范围及U10、18条既有电阻主体、下中部已审联合关系均按原范围接续。
- V3_G1/G2无端部POLY桥，保留两独立水平主体片段；U10不重做来源形状，新的共同坐标位置尚未人审；左沿G67不补照片外闭合。
- R1/R2非AA间隙和近邻竖环隔离保持；原八图、195保留对象与旧网络v33等历史裁决不变。顶部界面遮挡及右沿相邻照片不扩充材料。
- AA仓库skill v1已封装未全局安装。工艺/尺度、器件极性、真实W/L、CT逐孔归属与新网络仍未知；未运行真实PDK DRC/LVS。

## 复现与历史

- `.venv/bin/python -m silicon_eye.poly_closeout --root . --spec benchmarks/poly-closeout-v1/spec-v1.json --output runs/新的收口目录`。
- `.venv/bin/python -m pytest -q`；相关Python文件Ruff；`git diff --check`。
- 原图data/不改，runs/与.venv/不入Git。今日本地工作含宽POLY局部匹配/电阻裁决及本次收口代码、基准、资产、测试、文档；未推送。
- [收口前完整入口](docs/history/current-task-before-2026-10-20-poly-closeout.md)及[昨日完整交接](docs/history/current-task-before-2026-10-20-wide-poly-landmarks.md)保留此前状态和恢复命令；长期顺序见[开发计划](docs/development-plan.md)。
