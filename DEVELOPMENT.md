# 开发与复现

README和[在线Demo](https://xiahongyuu.github.io/SiliconEye/)面向项目展示。本文件面向复现与维护；[CURRENT_TASK.md](CURRENT_TASK.md)仍是唯一实时任务入口，原图、人工裁决和未知状态不因展示整理改变。

## 环境

Python >=3.11；项目当前使用Python 3.12和`.venv`。

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev,segmentation-eval]'
.venv/bin/silicon-eye --help
```

## 展示Demo

展示文件位于`site/`，无在线AI、外部字体或前端框架依赖，可直接打开`site/index.html`。构建参数集中在[configs/portfolio.json](configs/portfolio.json)，来源与导出哈希记录在[site/provenance.json](site/provenance.json)。

首次生成器件样本（输出目录已存在时复用，不覆盖）：

```bash
.venv/bin/silicon-eye annotate review-package \
  --spec benchmarks/review-package-roi2-device-index-v1.json --root . \
  -o runs/portfolio-device-index-v1
.venv/bin/python scripts/build_portfolio.py
python3 -m http.server 8768 --bind 127.0.0.1 --directory site
```

打开`http://127.0.0.1:8768`。修改`site/index.html/style.css/app.js`调整展示；重建只更新精选资产，不修改冻结证据。`scripts/build_portfolio.py`使用项目已有模型读取、SVG绘图和复核输出，不重新进行照片识别。

发布仅包含`site/`，使用Git subtree生成独立`gh-pages`分支。主分支仍保留源代码和开发证据；更新展示时先验证并提交主分支，再执行：

```bash
git subtree split --prefix=site --branch=gh-pages
git push origin main
git push origin gh-pages
```

GitHub Pages使用`gh-pages`分支根目录。推送需要相应授权和本机凭证管理器；命令不配置或保存明文凭证。

## 导体复核样本

```bash
.venv/bin/python -m silicon_eye.conductive_workflow \
  --request benchmarks/stacked-via-review-v2/review-request-v1.json \
  --output runs/新的复核目录
```

程序读取AI已形成的观察与既有裁决，不自动从照片识别材料或导出完整网表。局部几何、已审连接和未知范围分别保留。更多输入协议见[文档导航](docs/README.md)。

## 检查

```bash
.venv/bin/pytest -q tests/test_stacked_via_review.py tests/test_five_layer_geometry.py
.venv/bin/pytest -q tests/test_workspace_archive.py tests/test_portfolio_quality.py
python3 scripts/portfolio_quality.py --check-site
.venv/bin/ruff check scripts/build_portfolio.py scripts/workspace_archive.py scripts/portfolio_quality.py
git diff --check
```

完整测试用`.venv/bin/pytest -q`，耗时和验证范围更大；不要把某次子集通过的数量表述为全项目总测试数或照片识别准确率。

可选浏览器检查：安装Playwright及其Chromium后运行`node scripts/check_portfolio.cjs`；若使用集中安装的运行时，通过`NODE_PATH`与`PLAYWRIGHT_BROWSERS_PATH`指定位置。检查包含桌面/手机布局、切层、器件表、孔组放大及案例链接，截图写入`runs/portfolio-quality-browser-check/`。

## 质量案例与轻量CI

[八任务目录](benchmarks/portfolio-quality-v1/README.md)区分历史验收、人工rubric与两个现有机器评分任务。`python3 scripts/portfolio_quality.py`核对来源哈希并输出历史事实；不调用模型、不生成新准确率。`scripts/build_portfolio.py`将这些记录构建为公开结果卡。

[CI配置](docs/portfolio/ci-workflow.yml)已备好并通过本机稀疏环境检查。当前GitHub OAuth凭证缺少`workflow`权限，服务器拒绝创建工作流，因此尚未在线启用。取得该权限后将配置放到`.github/workflows/portfolio.yml`并推送，再核对实际运行，不能把本机通过说成在线CI通过。

配置中的GitHub Actions仅稀疏检出scripts、site和两个保障测试文件，运行公开资产哈希/链接/指标边界检查、13项保障测试和JavaScript语法检查，不下载多GB历史证据。权限仅contents:read，凭证不持久化，不自动发布页面。这是公开包CI，不是全项目测试或物理验收；完整源证据哈希在本机构建时另查。

工作流使用官方[checkout](https://github.com/actions/checkout)与[setup-python](https://github.com/actions/setup-python)，均固定提交。源文件结构整理先通过导航与轻量发布完成，冻结证据仍留原路径；后续迁移另作依赖/哈希方案，不直接删除或重写Git历史。

## 工作区归档

`runs/`主要为本机实验输出，少量历史图片仍被Git跟踪。归档工具首先保护所有已跟踪、被项目文本引用及含符号链接的运行目录，只处理未被引用的未跟踪运行目录。

```bash
.venv/bin/python scripts/workspace_archive.py plan --archive ../silicon-eye-archives/新的日期
.venv/bin/python scripts/workspace_archive.py apply --archive ../silicon-eye-archives/新的日期
.venv/bin/python scripts/workspace_archive.py verify --archive ../silicon-eye-archives/新的日期
.venv/bin/python scripts/workspace_archive.py restore \
  --archive ../silicon-eye-archives/已有日期 --run 需要恢复的运行目录名
```

原文件删除前，所有文件均按SHA-256备份并验证；同内容只存一份，manifest保留原路径和元数据。备份完成后写入`backed_up`状态，删除阶段可中断接续；恢复只补缺失文件，不覆盖不同内容。原图、冻结交付和Git历史不由此工具清除。归档只是可恢复整理；磁盘实际节省量与归档迁出量分别记录。
