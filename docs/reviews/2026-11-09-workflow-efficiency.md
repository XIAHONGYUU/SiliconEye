# 工作流效率最小包与仓库减负评估（2026-11-09）

本轮只调整流程入口、计时和度量，不改变已审几何、连接、原图或当前待审候选。当前批次 `M3-BATCH-EXTENTS-20261109-V1` 仍为 `ready_for_review`。

## 已落地

- `CURRENT_TASK.md` 改为单页：目标、三行队列、当前批次、唯一下一步、生效边界、完成条件。
- 新增 `DECISIONS.md`：稳定决定与未决项按 ID 保存，避免每轮复制全部不变量。
- 新增 `docs/history/CHANGELOG.md`：一行一个事务；完整入口快照只在阶段边界保留。
- 新增 `benchmarks/cycle-time-v1/`：模板、说明、当前批次记录和 `scripts/cycle_time.py`。
- 固定确认页新增 `review_started_at` / `review_exported_at` 自动记录；`review check` 计算 `review_seconds` 并写入 `review-record.md` 与 summary。旧 decision 不带计时仍可校验。
- 新增 `benchmarks/batch-production-v1/review-digest.md`：当前待审批次的一页摘要。
- 上一入口完整原文归档为 `docs/history/current-task-before-2026-11-09-workflow-efficiency.md`。

## 验证

```bash
.venv/bin/pytest -q tests/test_review_sheet.py tests/test_cycle_time.py
.venv/bin/python scripts/cycle_time.py benchmarks/cycle-time-v1/records/*.json
.venv/bin/ruff check silicon_eye/review_sheet.py scripts/cycle_time.py tests/test_review_sheet.py tests/test_cycle_time.py
```

实际结果见本轮回复；页面计时是墙钟时间（首次交互到导出），不是活跃工时，也不作为人审质量指标。

## 仓库减负评估

当前工作区约 16GB：

| 部分 | 约占用 | 说明 |
| --- | ---: | --- |
| `runs/` | 8.2GB | 205 个目录、66,607 个文件；其中 `via-rf-comparison-20261106` 4.1GB |
| `docs/assets/` | 3.0GB | 3,724 个全部被 Git 跟踪的文件；前 15 个 PNG 合计 2.49GB |
| `.git/` | 2.2GB | pack 1.65GB，另有约 498MB loose objects |
| `benchmarks/` | 825MB | 含约 276MB evidence ZIP |
| `.venv/` | 1.6GB | 可重建 |
| `data/` | 96MB | 原始照片，保留 |

### 最大单项：ilastik 运行时

`runs/via-rf-comparison-20261106/algorithm/` 中约 4.0GB 是运行时、安装包和下载分片：

- `ilastik-1.4.2-Linux.tar.bz2` 448MB
- `ilastik-1.4.2-Linux.complete.tar.bz2` 650MB
- `runtime/` 解压运行时约 2.7GB
- `runtime.part-*`、`ilastik-source.tar.gz` 等约 200MB

真正证据（`result/`、`result-reload/`、`logs/`、`labels/`、`dataset/`、`judge/`、`review/`）合计约 7.9MB；证据 ZIP 已保存 224 个相关文件。建议保留证据，清理运行时。`runs/` 不在 Git 中，清理不改历史；但这是删除操作，须先确认证据 ZIP 哈希和重放所需文件。

### 第二项：`docs/assets` 全量进入 Git

3.0GB 中大量是全幅源图副本和模型 JSON；仅四个 `O-source/O-raw` 文件就约 140MB，前 15 个 PNG 合计 2.49GB。Git 已对相同 blob 去重，但工作树、备份和 Agent 搜索仍承担全量。建议：

1. 新增资产政策：新全幅图只存一份共享源或只存裁片/缩略图，完整证据放外部归档；Git 只留 manifest、哈希和小图。
2. 先做内容哈希去重，找出重复的全幅图；更新引用后再删除重复副本，不直接批量删。
3. 新增大二进制走 Git LFS 或独立证据仓库；**不重写现有 Git 历史**，避免旧提交哈希和展示引用失效。

### 其他可选动作

- `workspace_archive.py plan` 当前只能归档 44 个未被引用目录、约 395MB；228 个目录被文本引用保护。该保护规则偏保守，但安全。
- `runs/via-rf-comparison-20261106` 被文档引用，因此归档工具不会整体处理；需要单独的“保留证据、清理 runtime”清单，不能直接套用整目录归档。
- `.git` 有约 498MB loose objects 和若干 unreachable 对象；确认无需要的未引用提交后，可用 `git gc --prune=now` 收紧，但不要用 `filter-repo`/BFG 重写历史。
- `benchmarks/evidence` 中 276MB ZIP 与 `runs/`、`docs/assets` 有重叠；先按 SHA-256 建索引，再决定哪些 ZIP 可外移，不能只看文件名。

### 建议顺序

1. 保留并通过哈希验证 ilastik 证据 ZIP；清理 4.0GB runtime/安装包/分片（需用户确认）。
2. 对 44 个未引用 runs 执行 `workspace_archive.py apply` 到外部归档（约 395MB，可恢复）。
3. 对 `docs/assets` 做重复哈希和引用清单，先替换重复全幅图，再谈 LFS/外移。
4. 最后评估 `git gc`；不重写历史。

预计前两步可在不损失证据的前提下减少约 4.4GB 工作区占用；`docs/assets` 的进一步减重取决于引用改造，不能承诺一次性释放 3GB。
