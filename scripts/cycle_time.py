"""Validate and summarize batch cycle-time records.

Usage:
    python scripts/cycle_time.py benchmarks/cycle-time-v1/records/*.json
    python scripts/cycle_time.py --json benchmarks/cycle-time-v1/records/*.json

The record is evidence about process latency, not about geometry or approval.
Missing timestamps stay null; this tool never invents a start or end time.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

SCHEMA_VERSION = 1
STATES = (
    "queued",
    "preparing",
    "ready_for_review",
    "in_review",
    "accepted",
    "rejected",
    "committed",
)
TIMESTAMP_FIELDS = (
    "queued_at",
    "ready_at",
    "review_sent_at",
    "review_started_at",
    "review_done_at",
    "accepted_at",
    "committed_at",
)
ORDER = (
    ("queued_at", "ready_at"),
    ("ready_at", "review_sent_at"),
    ("review_sent_at", "review_started_at"),
    ("review_started_at", "review_done_at"),
    ("ready_at", "accepted_at"),
    ("accepted_at", "committed_at"),
)


def parse_timestamp(value, field):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO 8601 string or null")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO 8601 timestamp") from exc
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def load_record(path):
    return json.loads(Path(path).read_text())


def validate_record(record):
    errors = []
    if not isinstance(record, dict):
        raise ValueError("Cycle-time record must be a JSON object")
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    batch_id = record.get("batch_id")
    if not isinstance(batch_id, str) or not batch_id.strip():
        errors.append("batch_id must be a non-empty string")
    if record.get("state") not in STATES:
        errors.append("state must be one of: " + ", ".join(STATES))
    parsed = {}
    for field in TIMESTAMP_FIELDS:
        try:
            parsed[field] = parse_timestamp(record.get(field), field)
        except ValueError as exc:
            errors.append(str(exc))
    human = record.get("human_review_minutes")
    if human is not None and (
        not isinstance(human, (int, float)) or isinstance(human, bool) or human < 0
    ):
        errors.append("human_review_minutes must be a non-negative number or null")
    if not errors:
        for earlier, later in ORDER:
            if parsed.get(earlier) and parsed.get(later) and parsed[later] < parsed[earlier]:
                errors.append(f"{later} must not be before {earlier}")
    if errors:
        raise ValueError("\n".join(errors))
    return record, parsed


def _seconds(start, end):
    if start is None or end is None:
        return None
    return round((end - start).total_seconds(), 3)


def metrics(record, parsed):
    review_seconds = _seconds(parsed.get("review_started_at"), parsed.get("review_done_at"))
    human_minutes = record.get("human_review_minutes")
    if human_minutes is None and review_seconds is not None:
        human_minutes = round(review_seconds / 60, 3)
    return {
        "batch_id": record["batch_id"],
        "state": record["state"],
        "queue_to_ready_seconds": _seconds(parsed.get("queued_at"), parsed.get("ready_at")),
        "ready_to_review_start_seconds": _seconds(
            parsed.get("ready_at"), parsed.get("review_started_at")
        ),
        "review_wait_seconds": _seconds(
            parsed.get("review_sent_at"), parsed.get("review_started_at")
        ),
        "review_seconds": review_seconds,
        "human_review_minutes": human_minutes,
        "lead_time_seconds": _seconds(parsed.get("ready_at"), parsed.get("accepted_at")),
        "ready_to_commit_seconds": _seconds(parsed.get("ready_at"), parsed.get("committed_at")),
    }


def summarize(records):
    rows = []
    for path in records:
        record, parsed = validate_record(load_record(path))
        rows.append(dict(metrics(record, parsed), record=str(path)))
    return rows


def _average(rows, key):
    values = [row[key] for row in rows if row[key] is not None]
    return round(sum(values) / len(values), 3) if values else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    rows = summarize(args.records)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    for row in rows:
        print(
            f"{row['batch_id']}: state={row['state']} "
            f"lead_time_seconds={row['lead_time_seconds']} "
            f"review_wait_seconds={row['review_wait_seconds']} "
            f"review_seconds={row['review_seconds']} "
            f"human_review_minutes={row['human_review_minutes']}"
        )
    if len(rows) > 1:
        print(
            "summary: "
            f"batches={len(rows)} "
            f"avg_lead_time_seconds={_average(rows, 'lead_time_seconds')} "
            f"avg_human_review_minutes={_average(rows, 'human_review_minutes')}"
        )


if __name__ == "__main__":
    main()
