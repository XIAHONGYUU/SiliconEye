"""The public quality gate must reject stale assets and invented evaluation claims."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "portfolio_quality", Path(__file__).resolve().parents[1] / "scripts/portfolio_quality.py"
)
quality = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quality)


@pytest.fixture
def site(tmp_path):
    public = tmp_path / "site"
    public.mkdir()
    (public / "asset.txt").write_text("frozen view")
    (public / "index.html").write_text('<a href="asset.txt">evidence</a>')
    (public / "provenance.json").write_text(
        json.dumps({"artifacts": {"asset.txt": quality.sha(public / "asset.txt")}})
    )
    (public / "quality-report.json").write_text(
        json.dumps(
            dict(
                new_model_runs=0,
                new_model_accuracy=None,
                global_unknown_rate=None,
                held_out_task_count=0,
            )
        )
    )
    return tmp_path


def test_stale_public_view_fails_even_when_the_file_exists(site):
    (site / "site/asset.txt").write_text("outdated geometry")
    with pytest.raises(ValueError, match="Stale public artifact"):
        quality.check_site(site)


@pytest.mark.parametrize(
    "field,value",
    [
        ("new_model_accuracy", 1.0),
        ("global_unknown_rate", 6 / 11317),
        ("held_out_task_count", 1),
    ],
)
def test_historical_catalog_cannot_turn_into_new_scores(site, field, value):
    path = site / "site/quality-report.json"
    report = json.loads(path.read_text())
    report[field] = value
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        quality.check_site(site)


def test_broken_link_and_path_escape_fail(site):
    for link in ("missing.svg", "../outside.txt"):
        (site / "site/index.html").write_text(f'<a href="{link}">source</a>')
        with pytest.raises(ValueError, match="Missing local site target"):
            quality.check_site(site)


def test_changed_historical_evidence_is_rejected_before_aggregation(tmp_path):
    directory = tmp_path / "benchmarks/portfolio-quality-v1"
    directory.mkdir(parents=True)
    evidence = tmp_path / "record.json"
    evidence.write_text('{"result":"original"}')
    suite = {"evidence": {"record": {"path": "record.json", "sha256": quality.sha(evidence)}}}
    (directory / "suite.json").write_text(json.dumps(suite))
    evidence.write_text('{"result":"corrected-after-the-fact"}')
    with pytest.raises(ValueError, match="Evidence changed"):
        quality.audit_catalog(tmp_path)
