# 配准核心修复验证

日期：2026-10-13。代码来源基线为 `90695080352f7a8e7396cdfecdd84dacca13a7ad`，当前修复是本地未提交修改。实时状态见 CURRENT_TASK.md。

## 设计先行

先完成 [AI/脚本职责与验证合同](ai-script-validation.md)，再实现脚本承担的配准核心。AI 的参考区域建议、真实图复核和模型增益比较尚未接入。

## 实现变化

- ECC 矩阵转换成统一的 target → reference 方向，彩色目标图保持颜色。
- 显式提供 inputMask，修复当前 OpenCV 的 ECC 调用兼容问题。
- 修复 ORB 未定义变量；短近邻列表和特征/匹配不足返回明确失败。
- similarity / affine 使用 warpAffine，homography 使用 warpPerspective。
- 真正计算 ORB 内点重投影距离的均方根，包含透视除法；ECC 的 rmse / inlier_ratio 为 None，correlation 单独报告。
- valid_mask 排除没有完整插值覆盖的边缘；无重叠为失败。
- 参数/输入错误抛 ValueError；预期算法失败保留目标副本和原因；auto 保留 attempts。

## 验证结果

```bash
.venv/bin/python -m pytest tests/test_registration.py -q
# 38 passed
.venv/bin/ruff check silicon_eye/phase1_image/stitcher.py tests/test_registration.py
# All checks passed
```

- 固定 NumPy 种子 17，OpenCV 测试种子 0，384 × 384 图；不依赖下载或真实大图。
- ECC：正负整数位移和亚像素位移，灰度/彩色均覆盖。
- ORB：旋转缩放、仿射剪切、透视变换，灰度/彩色均覆盖。
- 上述有真实变换的用例使用未参与 ORB 拟合的独立网格检查：最大恢复误差 ≤1 px，同层内部图像 RMSE 下降超过 50%。
- 验证不同尺寸、输入不被修改、失败不伪装成结果、auto 回退、短近邻、估计失败、奇异/非有限矩阵和内点不足。
- 独立构造内点残差检验 RMS 定义；排除外点，并覆盖透视坐标除法。
- 明确验证亚像素边界的有效掩膜及无重叠失败。
- 全包 Ruff 从初始 40 条减为 33 条；剩余为其他文件存量问题，未宣称全包通过。
- `git diff --check` 通过；data、configs、pyproject.toml 与基线无差异。

## 接口与使用

```python
from silicon_eye.phase1_image.stitcher import Stitcher

# reference 和 target 为 cv2.imread 得到的 uint8 BGR 数组或 uint8 灰度数组。
result = Stitcher().register_layers(reference, target, method="auto")
if result["success"]:
    aligned = result["warped"]
    coverage = result["valid_mask"]
else:
    reason = result["reason"]
```

`matrix` 一律将目标图 x/y 坐标映射到参考图。输出新增加 method、reason、matrix_direction、correlation、valid_mask、attempts。rmse / inlier_ratio 可为 None，调用者需按方法处理。当前仓库没有其他 register_layers 调用点，所以管线尚未依赖旧行为。

## 未验证范围

真实八层照片、跨层语义、物理尺度与配准质量尚未验证；合成同层测试阈值不外推到跨层。成功仅表示算法返回有效估计，重复纹理或局部错位仍需独立验收。ECC 当前只估计平移，多 tile 拼接仍未实现。视觉模型和推理模型的实际增益尚未验证。

下一任务：建立真实照片验收入口，保存变换与叠加图，使用独立可对应结构评估。

实现依据：[OpenCV ECC](https://docs.opencv.org/4.x/dc/d6b/group__video__track.html)、[几何变换](https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html)。
