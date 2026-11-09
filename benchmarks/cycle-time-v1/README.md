# 批次周期记录

本目录记录批次从准备到归档的实际周期，用于判断时间花在准备、等待人审、返工还是集成。它是流程证据，不是几何、物理或人审质量指标。

## 记录规则

- 一个批次一个 JSON，复制 `template.json` 后填写；缺失的时间保持 `null`，不补造。
- `ready_at` 是候选和复核材料可送审的时间；`review_sent_at` 是实际交给用户的时间。
- `review_started_at` / `review_done_at` 由固定确认页自动记录（首次交互/导出），也可由用户补记。
- `accepted_at` 只在本批裁决归档后填写；`committed_at` 只在本地 checkpoint 后填写。
- `human_review_minutes` 优先用实际记录；没有记录时由 `review_seconds / 60` 推导，并注明来源。

## 计算

```text
queue_to_ready       = ready_at - queued_at
review_wait          = review_started_at - review_sent_at
review_seconds       = review_done_at - review_started_at
lead_time            = accepted_at - ready_at
ready_to_commit      = committed_at - ready_at
```

跨批次只比较 `lead_time`、`review_wait`、`human_review_minutes` 和返工次数；不把 Agent 准备时间与识别计算时间相加成“总加速倍数”。

## 命令

```bash
.venv/bin/python scripts/cycle_time.py benchmarks/cycle-time-v1/records/*.json
.venv/bin/python scripts/cycle_time.py --json benchmarks/cycle-time-v1/records/*.json
```

当前记录：[records/](records/)（第一批、第二轮、扩大批、全幅清查）。
