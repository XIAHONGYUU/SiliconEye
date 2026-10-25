# 2026-10-25 求职展示与工作区整理

用户批准将项目改为三分钟可理解的展示入口，同时保留原有开发证据。开发基线为`fa3e1c7`，本地恢复分支`archive/pre-portfolio-20261025`。本次不更改材料层、物理结论或金属审批。

| 成果 | 交付 |
| --- | --- |
| 1 开发基线 | 原未提交金属工作已保存为fa3e1c7；原README和CURRENT_TASK完整归档 |
| 2 三分钟README | 项目问题、实际图、三个案例、个人能力、真实进展和开发入口 |
| 3 三个精选案例 | 材料重建、器件编号与连接、五层导体联合复核；附输入来源和限制 |
| 4 个人贡献 | 明确领域判断/架构/验收及AI辅助实现；附简历表述 |
| 5 轻量Demo | 无框架静态页面，约0.8MB；切层、编号联动、孔组放大；支持手机与本地直接打开 |
| 6 GitHub展示信息 | description、topics、homepage已更新；独立gh-pages构建成功并核对公网文件 |
| 7 文档入口 | README面向展示，DEVELOPMENT面向复现，docs/README负责导航，CURRENT_TASK唯一实时入口 |
| 8 可恢复瘦身 | 328个无引用运行目录做SHA去重归档，保留跟踪证据与依赖闭包；普通Git打包，无历史重写 |
| 9 验证 | 24项相关测试、导体原样重放、归档全量校验与恢复抽检、来源哈希、链接和实际浏览器交互 |

## 体积与恢复

整理前活动仓库15,198,879,744字节；归档、恢复抽检及普通Git打包后约9,400,659,968字节，计量包含Git、虚拟环境和保留运行目录。后来新增少量报告/提交会略有变化。

迁出内容5,578,336,614字节，SHA去重后实际存储2,701,324,395字节。**归档迁出不等于释放磁盘**：去重节省2,877,012,219字节，普通Git打包另约节省203MB；归档仍占约2.71GB磁盘。冻结docs/assets及其模型/审批依赖保留，不为展示重写历史或破坏哈希引用。

归档在仓库外但项目目录内：`../silicon-eye-archives/2026-10-25/manifest.json`，3532个唯一对象已逐一校验。恢复抽检`v3-adapter-smoke-input-v1`的2个文件哈希一致，依赖闭包检查无缺失。恢复命令见[开发指南](../../DEVELOPMENT.md)。此本机归档不上传GitHub。

## 验证与限制

- 新归档工具7项行为测试，加既有堆叠孔/五层几何回归，共24项通过；并非全项目总测试数或识别准确率。
- 归档后重放`stacked-via-review-v2/review-request-v1.json`，model/report与冻结结果逐字节一致。
- 已确认输入/资产哈希，原README字节相同，SVG/XML、JavaScript语法、Ruff与本轮链接检查通过。
- Playwright Chromium在1440×1000与390×844检查切层、编号、端子表、来源层、局部电路图、孔组缩放及案例深链接；无页面错误、图片缺失或横向溢出。发现并修复hash切换不更新内容的问题，保留首轮失败和复核报告。
- 展示未调用在线AI；器件框不表示精确边界；五层仍为候选几何；不声称整网、完整GDS、真实工艺DRC/LVS或仿真就绪网表。

[检查记录](../../benchmarks/portfolio-v1/verification.json) · [浏览器记录](../../benchmarks/portfolio-v1/browser-verification.json) · [展示QA](../../benchmarks/portfolio-v1/visual-review-v2.md) · [发布回执](../../benchmarks/portfolio-v1/publication.json)。

展示内容提交`8bf2833`，Pages提交`e4115de`，后者与GitHub实际构建提交一致。[公开Demo](https://xiahongyuu.github.io/silicon-eye/)根页面及17个公开文件HTTP读取成功，SHA与本机一致；远端README字节一致。GitHub简介、7个topics及主页地址已核对。Pages在gh-pages推送后已启用，创建API返回409后以实际GET结果确认来源正确，未重复创建。

旧任务和全部人工事实见[整理前任务原文](../history/current-task-before-2026-10-25-portfolio.md)。发布后继续V1/V2投影重叠与Q2占用比例的局部复核。
