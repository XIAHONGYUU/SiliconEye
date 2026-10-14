# 两层局部环试验

用户确认八张照片来自同一颗芯片逐层去层拍摄、手工对准困难，并授权只选取小部分评估。首次范围限定 aa/poly 的中部环邻域，每张裁剪 1250×850 px（约原图面积 4.3%）。读取 JPEG 需要解码原图，但量测、配准和输出只处理局部；不遍历其余六层。

AI 选择横向闭合环作为候选同源结构、给出边界搜索框；脚本量测相对边缘中心并仅求平移。左侧竖向闭合环的外边界四角独立检查，不参与拟合。它们来自一个结构且相关，不等于四个独立结构；剖面交点不代表直接观测到的物理角点。量测质量通过也不能确认同源身份。

输入 [registration-local-ring-v1.json](../benchmarks/registration-local-ring-v1.json) 在求解前固定；工程试验预算 P95 8 / max 12 px 沿用前轮，不包含已认证物理尺度。代码 [registration_local.py](../silicon_eye/registration_local.py) 复用现有边缘量测和证据输出函数。

```bash
.venv/bin/python -m silicon_eye.registration_local \
  --spec benchmarks/registration-local-ring-v1.json \
  --output runs/registration-local-ring-next
```

相对源图路径按执行目录解析，应从仓库根运行；新输出目录禁止覆盖。包含冻结输入、代码快照/哈希、原生与裁剪坐标变换、前后叠加、检查角局部图、结构框和有效范围遮罩。

[结果包](../runs/registration-local-ring-v1r1/report.md)：dx=54.41、dy=177.08 px；独立检查角中位误差由 190.25 降至 21.54 px，P95=24.81、max=24.99 px，未通过原预算。所有点仍为 candidate，acceptance=unknown；即使数字达标也不能自动升级为 confirmed。旋转、尺度和透视未估计，不能推出局部失败的唯一原因。

6 个新增测试和全套 61 个测试通过；相关 Ruff 通过。原图前后哈希一致。若利用这次检查残差选择新模型，需另设未参与选择的最终保留结构；全片/其他层覆盖尚未验证。

## 环轮廓相似变换试验

新增模型 `ring_similarity`，沿声明环四边采样，稳健拟合直线，由四个交点拟合尺度、旋转与平移。四角不是四个独立结构，拟合本身不能确认证据身份。保留边支持至少 75%、P95 ≤4 px；完整保存全部样本和剔除记录。尺度 0.9–1.1、旋转 ≤5°、拟合角最大残差 ≤10 px，诊断验收仍沿用原 8/12 px 预算。

```bash
.venv/bin/python -m silicon_eye.registration_local \
  --spec benchmarks/registration-local-ring-v2.json \
  --output runs/registration-local-ring-similarity-next
```

[新版包](../runs/registration-local-ring-v2r1/report.md) · [测量口径修订与局限](../runs/registration-local-ring-v2r1/review.md)。估计 scale=0.963860、rotation=0.270129°；既有检查角中位 2.89、P95 3.73、max 3.75 px，数字达标，但仍为候选诊断。初版采样检查失败后，明确定义了保留支持残差的统计口径；不是未经观察的预注册算法，不改变独立检查预算。

新增 4 项测试，全套 65 项通过。正式局部验收需冻结模型并增加一个未使用的新保留结构。

## 冻结模型后的新方块检查

新增输入 [registration-ring-square-holdout-v1.json](../benchmarks/registration-ring-square-holdout-v1.json)，不改变 v2r1 的拟合模型/矩阵/预算。检查范围向左扩展以容纳方块，两个裁剪各 1500×850 px，约原图 5.2%；仍仅处理 aa/poly。方块曾出现在早期大范围证据中，因此仅是环模型的新检查结构，不是项目全程严格盲测。

```bash
.venv/bin/python -m silicon_eye.registration_local \
  --spec benchmarks/registration-ring-square-holdout-v1.json \
  --output runs/registration-ring-square-next
```

`frozen_transform` 固定基线 manifest 哈希和原生矩阵；保护拒绝源图/拟合参数/拟合框/预算/矩阵/拟合函数漂移。冻结路径不调用求解器，结果矩阵逐元素相同。分别记录输入文件哈希及格式化输入快照哈希。

[本轮复核包](../runs/registration-ring-square-holdout-v1r2/review.md)：新方块 P95 5.61、max 5.64 px，达到原 8/12 px 预算；中心误差 2.36 px（由同一四角构造）。两处局部检查结构数字达标，物理边界身份仍是候选，acceptance=unknown；不代表全片准确性。新增加 6 项冻结保护测试，全套 71 项通过。

## 固化候选案例与统一入口

[局部候选案例 v1](../benchmarks/local-ring-aa-poly-v1/README.md)保存必要冻结输入和源码快照，两个输入只引用相对项目路径，重跑无需旧 runs/。新增 `silicon-eye register-local --spec <case.json> -o <new-dir>`，保留模块入口。

AI 原图复核支持横向环/竖向环/方块的拓扑对应；亮条、接触点与填充区域随层变化，不能据此确认同一物理材料边界。identity-review.json 仍记录 candidate/unknown，用户只确认报告名，不代表确认这些物理判断。

没有历史 runs/ 的临时目录中，两项案例的矩阵和误差均复现；复用现有运行环境，没有执行完整依赖重装。两个数字检查仍达标，formal acceptance 仍 unknown。全套 71 测试、相关 Ruff 和 Git 差异检查通过。
