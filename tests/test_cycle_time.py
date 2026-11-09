"""Cycle-time records must compute latency without inventing missing timestamps."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "cycle_time", Path(__file__).resolve().parents[1] / "scripts/cycle_time.py"
)
cycle_time = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cycle_time)


def record(**overrides):
    value = {
        "schema_version": 1,
        "batch_id": "TEST-BATCH",
        "state": "in_review",
        "queued_at": "2026-11-09T08:00:00+00:00",
        "ready_at": "2026-11-09T09:00:00+00:00",
        "review_sent_at": "2026-11-09T09:05:00+00:00",
        "review_started_at": "2026-11-09T10:00:00+00:00",
        "review_done_at": "2026-11-09T10:12:30+00:00",
        "accepted_at": "2026-11-09T10:20:00+00:00",
        "committed_at": "2026-11-09T10:25:00+00:00",
        "human_review_minutes": None,
    }
    value.update(overrides)
    return value


def test_metrics_compute_wait_review_and_lead_time():
    parsed_record, parsed = cycle_time.validate_record(record())
    result = cycle_time.metrics(parsed_record, parsed)

    assert result["queue_to_ready_seconds"] == 3600.0
    assert result["review_wait_seconds"] == 3300.0
    assert result["review_seconds"] == 750.0
    assert result["human_review_minutes"] == 12.5
    assert result["lead_time_seconds"] == 4800.0
    assert result["ready_to_commit_seconds"] == 5100.0


def test_missing_timestamps_stay_null_and_explicit_human_minutes_win():
    parsed_record, parsed = cycle_time.validate_record(
        record(
            queued_at=None,
            review_started_at=None,
            review_done_at=None,
            human_review_minutes=7.25,
        )
    )
    result = cycle_time.metrics(parsed_record, parsed)

    assert result["queue_to_ready_seconds"] is None
    assert result["review_seconds"] is None
    assert result["human_review_minutes"] == 7.25
    assert result["lead_time_seconds"] == 4800.0


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"schema_version": 2}, "schema_version"),
        ({"batch_id": ""}, "batch_id"),
        ({"state": "waiting"}, "state must"),
        ({"review_started_at": "not-a-time"}, "ISO 8601"),
        (
            {
                "review_started_at": "2026-11-09T10:00:00+00:00",
                "review_done_at": "2026-11-09T09:00:00+00:00",
            },
            "must not be before",
        ),
        ({"human_review_minutes": -1}, "human_review_minutes"),
    ],
)
def test_invalid_records_are_rejected(overrides, message):
    with pytest.raises(ValueError, match=message):
        cycle_time.validate_record(record(**overrides))
