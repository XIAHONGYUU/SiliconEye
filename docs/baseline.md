# 本机开发初始基线

日期：2026-10-13。此文件记录固定基线，实时状态见 `CURRENT_TASK.md`。

## 来源与布局

- 仓库：`https://github.com/XIAHONGYUU/silicon-eye`，分支 `main`。
- 基线提交：`90695080352f7a8e7396cdfecdd84dacca13a7ad`。
- Git 根目录：`/home/zuoky/project_siliconeyes/silicon-eye`。
- 外层只读 `.git` 占位不是仓库，外层仅导航；不建立第二个 Git 历史。代码、原图与项目文档由内层 Git 管理，以其基线/差异验证。
- Python 3.12.3，`.venv` 可编辑安装 `.[dev]`；SAM 未安装。
- 原图在 `data/test_chip/tile_full/`：sub、implant、aa、poly、m1、m2、m3、m4 八张 JPEG，均为 RGB，5712 × 4284。

## 已验证结果

| 检查 | 基线结果 |
|---|---|
| `python -m pip check` | 通过，无依赖冲突 |
| `silicon-eye --help` | 通过；提供 run、annotate、info |
| `silicon-eye info -c configs/test_chip.yaml` | 通过；八层、一个 tile |
| 原图文件头 | 八张尺寸/模式一致；不代表内容或层语义已确认 |
| `python -m pytest -q` | 无测试，退出码 5；未通过测试验收 |
| `ruff check silicon_eye --no-cache --statistics` | 40 条存量问题，含五条 undefined-name |
| 两张空白 128 × 128 图调用 ORB | 复现 `NameError: name 'target' is not defined`，`stitcher.py:167` |

## 代码检查发现

- `phase1_image/stitcher.py`：ORB 五处未定义变量；ECC 重采样方向待回归验证；homography 使用 `warpAffine`，需要修正；ECC 的 RMSE 写死为 0，不能作为质量证据。
- `pipeline.py`：配准 helper 未接入；图像路径缺少实际 `data/` 前缀；Phase 2 独立执行使用新建 run 目录加载 checkpoint，恢复能力尚未验证。
- `segmenter.py`：规则分割与 SAM 未实现，返回空列表。
- `extractor.py` 与 `layer_matcher.py`：尺寸测量、端子定位、金属/via 追踪仍有 TODO。
- README 的 `run -o` 与实际 CLI 不一致，输出在 `runs/`。

真实图像端到端提取、物理尺寸、器件、连接和 SPICE 正确性均未验证。此次骨架不改动算法与原图，原始代码和图像可从基线提交恢复。
