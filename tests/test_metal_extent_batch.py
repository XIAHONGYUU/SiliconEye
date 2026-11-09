"""Batch failure guards plus a source-bound six-line regression against the prior run."""

import copy
import tempfile
from pathlib import Path

import numpy as np
import pytest

from silicon_eye.metal_extent_batch import preflight, read, ref, run
from silicon_eye.review_sheet import load_package
from silicon_eye.ridge_tracing import trace

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "configs/metal-extent-batch-m3-replay.json"


def test_known_ridges_and_blank_failure():
    y, x = np.mgrid[:100, :201]
    image = sum(220 * np.exp(-(((y - (seed + x * 0.03)) / 1.3) ** 2)) for seed in [20, 60])
    tracks = trace(image, [20, 60], 0, 200)
    for seed, track in zip([20, 60], tracks, strict=True):
        assert not track["unknown_spans"]
        assert max(abs(py - (seed + px * 0.03)) for px, py in track["points"]) <= 1
    with pytest.raises(RuntimeError, match="No supported ridge"):
        trace(np.zeros((100, 201)), [20], 0, 200)
    image[:, 90:120] = 0
    with pytest.raises(RuntimeError, match="No supported ridge"):
        trace(image, [20], 0, 200)


@pytest.mark.parametrize(
    "change,match",
    [
        (lambda s: s.update(bounds=[-1, 0, 20, 30]), "Crop outside"),
        (lambda s: s["targets"].append(s["targets"][0]), "duplicate"),
        (lambda s: s["targets"][0].update(seed_y=2450), "seed order"),
        (lambda s: s["targets"][0].update(id="ABSENT"), "Unknown metal"),
        (lambda s: s["photo"].update(sha256="0" * 64), "hash changed"),
        (lambda s: s["groups"][0].update(design_x=[-4000, -3900]), "Detached"),
        (lambda s: s["groups"][0].update(native_x=[0, 250]), "outside trace"),
    ],
)
def test_preflight_rejections(change, match):
    spec = read(SPEC)
    change(spec)
    with pytest.raises(ValueError, match=match):
        preflight(ROOT, spec)


def test_six_line_replay():
    spec = read(SPEC)
    before = ref(ROOT, ROOT / spec["parent"]["path"])
    with tempfile.TemporaryDirectory(dir=ROOT / "runs", prefix="batch-test-") as tmp:
        output = Path(tmp) / "result"
        result = run(ROOT, SPEC, output, replay=True)
        assert result["status"] == "PASS"
        assert all(v >= 0 for v in result["stages_seconds"].values())
        assert (
            read(output / "traces.json")["tracks"]
            == read(ROOT / "benchmarks/batch-production-v1/traces.json")["tracks"]
        )
        old = read(ROOT / "benchmarks/batch-production-v1/sample.json")
        new = read(output / "sample.json")
        assert new["canvas_bounds"] == old["canvas_bounds"]
        for layer, features in old["features_by_layer"].items():
            for a, b in zip(features, new["features_by_layer"][layer], strict=True):
                a, b = copy.deepcopy(a), copy.deepcopy(b)
                # New package identity differs; every existing and appended rectangle must agree.
                for f in [a, b]:
                    for p in f.get("local_parts", []):
                        p.pop("id", None)
                        p.pop("basis", None)
                assert a == b
        preservation = read(output / "preservation.json")
        assert preservation["added_parts"] == 12
        load_package(output / "review")
        assert all(
            i["review_mode"] == "context" and not i["required"]
            for i in read(output / "review-spec.json")["items"]
        )
        with pytest.raises(ValueError, match="new directory"):
            run(ROOT, SPEC, output, replay=True)
    assert ref(ROOT, ROOT / spec["parent"]["path"]) == before


def test_failed_recognition_has_diagnostic_not_review(monkeypatch):
    import silicon_eye.metal_extent_batch as batch

    def fail(*args):
        raise ValueError("Unsupported trace span")

    monkeypatch.setattr(batch, "recognize", fail)
    with tempfile.TemporaryDirectory(dir=ROOT / "runs", prefix="batch-failure-") as tmp:
        output = Path(tmp) / "result"
        with pytest.raises(ValueError, match="Unsupported trace"):
            batch.run(ROOT, SPEC, output)
        assert read(output / "diagnostic.json")["stage"] == "recognition"
        assert not (output / "review").exists()


def test_production_review_uses_group_decisions():
    from silicon_eye.metal_extent_batch import evidence
    from silicon_eye.review_sheet import build

    spec = read(SPEC)
    _, _, original, _ = preflight(ROOT, spec)
    sample = read(ROOT / "benchmarks/batch-production-v1/sample.json")
    tracks = read(ROOT / "benchmarks/batch-production-v1/traces.json")["tracks"]
    with tempfile.TemporaryDirectory(dir=ROOT / "runs", prefix="batch-review-") as tmp:
        output = Path(tmp)
        evidence(ROOT, output, spec, tracks, original, sample, False)
        build(ROOT, output / "review-spec.json", output / "review")
        _, review = load_package(output / "review")
        assert len(review["items"]) == 2
        assert all(
            i["required"] and i["review_mode"] == "decision" and i["checks"]
            for i in review["items"]
        )
