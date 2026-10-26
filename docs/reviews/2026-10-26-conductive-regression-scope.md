# 金属／VIA 固定回归与能力收口

已整理固定集并更新仓库内两个 skill 的接续与能力说明。维持 **LIMITED_TRIAL_V2**；本轮没有重新识图、补人审或扩大几何采用范围。

- [固定 suite](../../benchmarks/conductive-regression-v1/suite.json)：V1-S1、V2-R1、V2-R2 三项，五条接口；原图输入包与含答案的评分记录分开。旧人审、固定任务和漏排修订记录均保持哈希。
- [能力与验收标准](../architecture/conductive-skill-qualification-v1.md)：区分接续回放、软件反例和 AI 原图判断；规定第一版／修订版分别冻结、未知单列、任务／接口两种分母分开，不把历史成绩当新模型成绩。
- [金属 skill](../../skills/silicon-eye-metal-reconstruction/SKILL.md)与[VIA skill](../../skills/silicon-eye-via-reconstruction/SKILL.md)：接入同一固定回归命令，继承旧批准，限定局部候选、受限修订和未知保留；不再将已收口 Q1/Q2 笼统写成待审几何。

复现命令：

```bash
.venv/bin/python scripts/check_conductive_regression.py --output runs/新的回归目录/result.json
```

[执行原记录](../../benchmarks/conductive-regression-v1/execution-result.json)及[验证摘要](../../benchmarks/conductive-regression-v1/verification.json)：245 条去重证据路径经现有来源验证与固定引用检查；两个新已审包完整模型精确回放，共同快照仅运行 ID 随请求变化，其他字段相同；既有 **31 项测试通过**。附加三种运行器破坏检查：输入哈希变化、真值承载换成邻线、取消代理资格均被拒绝，不与 31 项软件测试混算。

两个 skill 格式验证、运行器 Ruff 和 `git diff --check` 通过。54 个执行文件哈希记录了未提交工作树的关键代码、模板、测试与 skill 版本。没有执行新的 AI 识别评测，没有实际浏览器交互验证；工程 PASS 不等于完整像素／物理真值。

README／site 共 25 个文件及本地 gh-pages 引用未变。原始照片、既有工作几何、人审包和历史固定任务未修改；当前任务原文归档至[历史入口](../history/current-task-before-2026-10-26-regression-scope.md)。未提交、未推送。

下一步按已审 R1–R2 两条长 M2 所在的连续走廊，先建全部可见导体／接口／图外端部清单，再逐项对应候选或明确未知，检查中部交叉、端部和邻线遗漏。该步骤检验连续区域覆盖，避免继续积累互不相连的小样；本轮尚未开始扩展。
