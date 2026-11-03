# 2026-11-03 固定验收确认单工具

## 目标与范围

本轮只交付“固定验收确认界面与归档工具”，解决每次人审临时生成不同页面、不同问题词表和不同答案 JSON 的问题。范围是 AA、POLY、CT、METAL、VIA、REGION 共用同一模板；不产生新的来源观察、几何、孔、连接或人审事实。

当前研究任务不变：唯一下一步仍是 W3/W4 邻近 M2 连续来源清单。

## 交付

- silicon_eye/review_sheet.py：构建、校验、归档和阶段预设。
- silicon_eye/review_sheet.html：固定单页模板；总览、逐项确认、整体问题、边界与未批准、导出五个固定分区。
- silicon-eye review build/check/preset：CLI 入口；python -m silicon_eye.review_sheet 等价。
- docs/review-sheet-protocol.md：固定协议、字段、词表、命令和边界。
- configs/review-sheet-demo-m2.json：真实 W3/W4 邻近 M2 证据的演示定义。
- tests/test_review_sheet.py：构建、哈希、预设、决策校验、归档和防篡改测试。

固定产物：

    review-spec.json
    index.html
    manifest.json
    review-decision.json
    review-record.md

固定结论：通过、需修改、不确定、不适用。通过要求全部必查项为真；需修改要求备注非空；必须勾选边界确认后才能导出。

## 验证

| 检查 | 结果 |
| --- | --- |
| pytest tests/test_review_sheet.py | 25 passed |
| pytest tests/test_review_sheet.py tests/test_block_review.py | 40 passed |
| ruff check silicon_eye/review_sheet.py tests/test_review_sheet.py | All checks passed |
| py_compile 两个新增 Python 文件 | 通过 |
| 页面逻辑脚本 node --check | 通过（数据 payload 单独解析） |
| 模板反引号残留检查 | 无 |
| 演示包构建 | 4 项、4 必答、3 个整体问题、5 张证据、5 个去重资源 |
| jsdom 页面交互 | 4 项/3 问题渲染；未完成时导出被阻止；需修改缺备注报错；通过缺必查项报错；覆盖项未通过时整体问题不能判通过；补齐后进度 8/8；导出 JSON 含 4 项答案/3 个整体问题并触发 review-decision.json 下载 |
| 校验归档 | 冒烟包 check --archive 写入 review-decision.json 与 review-record.md；重复校验幂等；页面篡改被拒绝 |
| 固定工程回归 | scripts/check_conductive_regression.py 返回 PASS_SCOPED_ENGINEERING_REGRESSION |
| 负面路径 | 缺必答项、未知/重复 ID、未勾必查、缺备注、未确认边界、错 build_id、错 actor、未知检查项、整体问题掩盖未通过覆盖项均被拒绝 |

浏览器交互用 jsdom 模拟，未在真实 Chrome/Firefox 中做像素级视觉验收；页面为纯静态 file:// 可用，不启动服务。

## 未改变

- 未改工作模型、来源照片、179 个候选孔、30 组已审接口、旧 human-review.json。
- 未运行新 AI 识图评测，未产生新 M2 观察或几何。
- 未修改 README/site/gh-pages，未推送远端。
- 演示包明确标注“非送审”，不构成人审或几何授权。

## 边界与下一步

本工具只记录对送审声明的判断；构建成功、页面操作或聊天口头通过都不等于精确尺寸、物理孔数、PDK/DRC、完整网表或共同几何采用。后续人审应先按协议生成送审定义并构建固定页面，再以 review-decision.json 归档。

当前唯一下一步仍为 M2 连续来源清单→几何对应→接口未知；本工具可作为该批次的固定确认入口。
