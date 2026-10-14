# 两处内部区域的材料边界候选

本轮只处理像素标注 v2 的 H-inner/V-inner，分别在 aa/poly 原图中处理，共4个 ROI。用户已确认层语义，但这不确认证据中具体边界的材料身份。坐标为原图像素中心 x/y，所有面积 px²、周长 px；无 μm/W/L。

输入 [local-contours-v1.json](../benchmarks/local-contours-v1.json)先固定参数：7×7 Gaussian、sigma=1.5 px，Otsu 明/暗极性两种解释。脚本输出8张二值支持掩膜和完整 RETR_TREE 轮廓层级，保留全部输出轮廓/孔洞，不做形态闭运算、填洞、按尺寸删除或自动连接。平滑/阈值本身仍可能损失细节，因此保留原生原图裁剪。

轮廓是候选亮度边界，不是确定材料掩膜；每条轮廓记录原生坐标、包围框、层级、polygon_area_px2、周长和 touches_roi_border。mask_area_px2 是非零像素数，不能与多边形面积混为一谈。触及 ROI 边界表示可能截断，closed_material_boundary_confirmed=false。

```bash
.venv/bin/silicon-eye annotate contours \
  --spec benchmarks/local-contours-v1.json \
  -o runs/material-contours-next
```

从仓库根运行，输出目录须不存在，不得写在源图目录。仅允许选 region_candidate，配准控制不参与材料候选生成。源图哈希/尺寸、标注格式、冻结引用及源图对应侧均核验。

[最终候选包](../runs/material-contours-v1r1/report.md)包含各 ROI 原图/两极性对照、8张 PNG 二值掩膜、原生轮廓 JSON、输入/标注/代码快照与状态记录。[开发过程 AI 复核](../runs/material-contours-v1r1/ai-review.json)分别记录周边边框、内部条纹、接触点样亮斑及裁剪端部的替代解释；没有声明运行时模型已接入。

实图结果：aa-H-inner 亮/暗轮廓 8/63，aa-V-inner 42/42，poly-H-inner 75/97，poly-V-inner 91/81。纹理、光照和接触点样亮斑造成多轮廓，不能按轮廓数量计器件。四个 ROI 的至少一种输出均触及裁剪边缘。

7 项新增测试验证孔洞保留、两极性互补、原生坐标、截断标记、弱对比度未知、非法参数、来源/输出保护以及控制对象拒绝。全套109项通过，最后来源关联检查后7项相关测试通过；相关 Ruff、Git diff --check 与输入/原图/冻结参考/源码快照哈希通过。

没有独立人工 mask，因此不报告 IoU 或材料边界准确率。material_ground_truth_ready=false、device_ground_truth_ready=false；主 Pipeline 器件阶段仍 blocked，冻结配准/原框/配置/依赖不变，无外部模型/提交/推送。
