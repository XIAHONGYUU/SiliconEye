# 当前任务

## 任务合同

- **目标**：将当前代码、文档、测试和冻结基准提交到 XIAHONGYUU/silicon-eye 的 origin/main，保留人工示范标注交接。
- **基线**：`XIAHONGYUU/silicon-eye`，main，`90695080352f7a8e7396cdfecdd84dacca13a7ad`；保留前序本机骨架修改。
- **范围**：全部现有源码/文档/测试/冻结基准修改；.venv/ 和 runs/ 继续忽略，原图与已存在数据不改。
- **不变量**：原图、配置、依赖声明及无关算法不变；本轮按用户明确授权推送 origin/main，不调用外部模型、不宣称正式算法验收通过。
- **优先级**：可回查的证据和真实验证优先于功能数量；先设计，再实现。
- **授权**：用户明确要求将现有修改提交远端 GitHub，确认本机 XIAHONGYUU 账号，并选择该 GitHub 账号的 noreply 提交身份；无外部模型调用授权。
- **输出**：本机可重复命令、逐层变换/参数/输入哈希/叠加图/局部图/对应点误差；不将未复核候选点称为人工真值。
- **完成条件**：局部像素坐标/来源哈希/候选与确认状态受校验；首批标注对照图可复核；未知尺度不产生物理尺寸，候选不成为器件真值；测试通过；实际未通过不能被改写为完成配准。
- **证据**：固定历史基线见 docs/baseline.md；本轮验证见 docs/registration-validation.md。
- **停止条件**：缺凭证、源图破坏风险、外部变更或需要人工裁决的物理事实。

## 当前结果

2026-10-14：第4阶段局部标注推进到材料边界候选轮廓；候选生成完成，独立人工材料 mask 与器件真值仍未建立。

- 层语义由用户确认 aa=有源区、poly=多晶硅。仅处理标注 v2 的 H-inner/V-inner，两层合计4个原生 ROI；原图像素单位，不改框或冻结配准。
- benchmarks/local-contours-v1.json 处理参数先固定：sigma=1.5 px、7×7 Gaussian + Otsu 明/暗两极性。脚本保存8张候选二值支持和完整轮廓树；无闭运算/填洞/按尺寸删除/自动连接。
- 每条轮廓有 native_source_pixel_center_xy 坐标、bbox、层级、面积/周长与触边风险。像素面积与多边形面积分开；触边不视作完整材料边界，材料身份 unknown。
- 最终证据 runs/material-contours-v1r1/report.md；四幅对照图已视觉检查。aa-H/aa-V/poly-H/poly-V 明暗轮廓分别8/63、42/42、75/97、91/81。输出轮廓数不是器件数；所有 ROI 至少一种输出触边。
- ai-review.json 记录开发过程复核：周边/内部条纹不同，poly 重复亮斑可能为接触点样或光学/残留特征，竖向端部截断；未调用运行时模型，不凭尺寸确认或补造连接。
- 原图裁剪保留；平滑/阈值也可能损失细节。无独立人工 mask，不计算 IoU/边界准确率，material_ground_truth_ready=false、device_ground_truth_ready=false，设备阶段 blocked。
- 新增7项行为测试；全套109 passed，最后来源关联检查后7项相关测试通过。相关 Ruff、Git diff --check、原图/输入/标注/冻结参考/代码快照哈希通过。
- 原图、标注框、冻结算法/矩阵/预算、配置/依赖和旧证据不变；无提交、无推送、无外部模型。
- 说明 docs/material-contour-candidates.md。

## 命令

```bash
.venv/bin/silicon-eye annotate contours \
  --spec benchmarks/local-contours-v1.json \
  -o runs/material-contours-next
```

从仓库根运行，新输出目录且不位于源图目录；只处理两处内部区域，不是完整设备提取。

## 最新复核：poly 候选有争议

2026-10-14：用户反馈“aa好像是正确的，但是poly好像不是正确的”。不把该初步意见当作精确材料 mask 确认：aa 两个对象仍 candidate，poly 两个对象标为 conflict；源图 aa/poly 层语义已确认这一事实保持不变。

原图复核确认 Otsu 只划分亮暗，未判定重复亮斑、细轨和暗条带的材料身份。因此旧 poly 输出不能作为可接受材料边界，也不把暗极性自动选成答案。本轮保留旧证据，只生成原图观察点和逐对象复核记录：runs/poly-contour-review-v2/report.md、adjudication.json。没有修改代码/算法/阈值/原图/标注框/配准。

已通过聊天文字问题询问：亮点被当作 poly、应提取连续条带、或区域/层图不对。等待这个反馈时完成上述独立复核，不盲调阈值。

## 最新交付：人工示范样片

用户要求亲自示范哪些是 AA、哪些是 poly，本轮按这个方向停止猜测边界。新包 runs/human-annotation-sample-v1/：annotation-sheet.png（3040×940 双图），aa-unmarked.png/poly-unmarked.png（各1500×850），README.md 和映射/哈希 manifest.json。

均来自既有小区域原图，未缩放、配准、增强或叠加候选框/掩膜；左/右仅标明源照片文件名。源图哈希前后相同；两张 PNG 重读与原图裁剪像素逐点一致。保留此前 poly conflict、aa candidate，不把样片文件生成当作标注完成。未改变代码、算法、原始照片或旧证据。

## 本轮 GitHub 开发快照

2026-10-14：用户授权将当前修改提交 origin/main。远端 https://github.com/XIAHONGYUU/silicon-eye.git，已 fetch 核对 main 与本地基线一致；登录账号已核验 XIAHONGYUU（ID 280077814），提交身份采用用户选择的 GitHub noreply，不配置猜测的个人邮箱。

提交内容：配准修复/验收、结构约束、冻结局部案例、Pipeline 候选/阻塞状态、像素标注与轮廓候选、测试、文档和任务记录。.venv/、runs/ 不入提交，原始照片本来已在远端且本轮不改。人工样片保留在本机 runs/human-annotation-sample-v1/，当前不把批量派生输出加入 Git。

本轮全套109 tests passed，修改代码/测试 Ruff 通过；pipeline 未触及网表 helper 的既有 F541/SIM114 两项明确排除。Git diff --check 通过；待提交文件未发现私钥或常见 token 模式。它是开发快照，poly 候选 conflict、材料真值未完成、设备阶段 blocked 的状态保持不变。

代码快照已提交并推送：5912f3523e3456afaec95766ea0d2fdf7825bd86（feat: add audited local registration and pixel annotation workflow）；git ls-remote 核验远端 main 与该提交完全一致。首次 Git 推送缺凭证接口，随后通过 gh 已登录凭证管理接口完成推送，没有读取/输出 token。本条完成记录作为后续文档提交同步；GitHub 开发快照不表示物理边界或器件验收通过。

## 唯一下一步

等待用户在本机样片上标出 AA/poly 示例；收到后按 manifest 面板偏移映射到原图，先复核用户标签与真实目标边界，再据示例调整材料提取方法。此前 poly 阈值结果不可直接用作材料基准。

实际 Git 根目录 /home/zuoky/project_siliconeyes/silicon-eye；外层只读 .git 占位不是仓库。
