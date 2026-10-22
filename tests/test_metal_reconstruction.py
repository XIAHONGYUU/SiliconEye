"""Metal pilot checks must reject false joins and retain source/projection limits."""

import copy
import json
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from silicon_eye.geometry_reconstruction import digest
from silicon_eye.metal_reconstruction import (
    column_correspondence,
    contact_audit,
    feature_polygon,
    geometry_audit,
    reviewed_features,
    run,
    stroke,
)

ROOT = Path(__file__).resolve().parents[1]


def feature(key, x):
    return dict(id=key, design_path=[[x, 10], [x, 80]], design_width=8)


def test_orthogonal_stroke_retains_u_opening_and_rejects_diagonal():
    p = stroke([[10, 10], [10, 40], [40, 40], [40, 10]], 6)
    assert p.geom_type == "Polygon" and p.is_valid
    assert p.intersection(Polygon([[20, 10], [30, 10], [30, 30], [20, 30]])).area == 0
    with pytest.raises(ValueError, match="orthogonal"):
        stroke([[0, 0], [10, 3]], 4)
    with pytest.raises(ValueError, match="repeated"):
        stroke([[0, 0], [0, 0]], 4)


def test_geometry_blocks_crossed_conductors_and_narrow_gap():
    budget = dict(minimum_width_px=6, minimum_gap_px=3)
    features = [feature("A", 20), feature("B", 40)]
    report, _ = geometry_audit(features, budget, [100, 100])
    assert report["status"] == "PASS"
    features[1]["design_path"] = [[30, 10], [30, 80]]
    report, _ = geometry_audit(features, budget, [100, 100])
    assert report["status"] == "FAIL"  # 2px edge gap, with no positive-area overlap.
    features[1]["design_path"] = [[10, 40], [60, 40]]
    assert geometry_audit(features, budget, [100, 100])[0]["status"] == "FAIL"


def test_weak_width_and_duplicate_identity_cannot_be_hidden():
    budget = dict(minimum_width_px=6, minimum_gap_px=3)
    f = feature("A", 20)
    f["design_width"] = 5
    assert geometry_audit([f], budget, [100, 100])[0]["status"] == "FAIL"
    with pytest.raises(ValueError, match="Duplicate"):
        geometry_audit([feature("A", 20), feature("A", 40)], budget, [100, 100])


def test_partial_x_check_never_qualifies_exact_ct_projection():
    c = dict(
        fit=[dict(id="a", m1_x=0, poly_x=10), dict(id="b", m1_x=10, poly_x=20)],
        holdout=[dict(id="c", m1_x=20, poly_x=30)],
        scope="small sample",
        tolerance_native_px=1,
    )
    r = column_correspondence(c)
    assert r["x_status"] == "PASS"
    assert r["y_status"] == "NOT_QUALIFIED" and not r["precise_CT_projection_allowed"]
    c["holdout"][0]["poly_x"] = 34
    assert column_correspondence(c)["x_status"] == "FAIL"
    c["holdout"][0]["id"] = "a"
    with pytest.raises(ValueError, match="Holdout"):
        column_correspondence(c)


def test_ct_enclosure_does_not_self_confirm_connection():
    f = feature("A", 20)
    p = stroke(f["design_path"], f["design_width"])
    cuts = [dict(id="C", layout_outline=[[18, 20], [22, 20], [22, 24], [18, 24]])]
    claim = [dict(metal_id="A", contact_ids=["C"])]
    row = contact_audit([f], [p], cuts, claim, 1)[0]
    assert row["geometry_status"] == "PASS"
    assert not row["electrical_connection_confirmed"]
    cuts[0]["layout_outline"] = [[21, 20], [25, 20], [25, 24], [21, 24]]
    assert contact_audit([f], [p], cuts, claim, 1)[0]["geometry_status"] == "FAIL"


def test_real_pilot_preserves_joint_layer_and_blocks_precise_projection():
    spec_path = ROOT / "benchmarks/m1-geometry-pilot-v1/spec-v1.json"
    spec = json.loads(spec_path.read_text())
    manifest = json.loads((ROOT / spec["snapshot"]["path"]).read_text())
    refs = [spec["snapshot"], *manifest["inputs"].values(), *manifest["source_photos"].values()]
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        output = Path(temp) / "delivery"
        report = run(ROOT, spec_path, output)
        assert report["status"] == "REVIEW_REQUIRED"
        assert report["geometry"]["status"] == "PASS"
        assert report["column_correspondence"]["x_status"] == "PASS"
        assert not report["precise_CT_projection_allowed"]
        assert sum(r["CT_count"] for r in report["CT_support_candidates"]) == 87
        assert len(report["pending_gate_CT_ids"]) == 8
        context = json.loads((output / "continuation-context.json").read_text())
        assert len(context["inherited_documents"]["unknown"]["unknown_scopes"]) == 6
        model = json.loads((output / "model.json").read_text())
        assert len(model["objects"]) == 9 and not model["adopted_into_joint_snapshot"]
        assert model["unprocessed_is_unknown"]
        assert all(o["net_id"] is None for o in model["objects"])
        assert not (output / "joint-snapshot.json").exists()
        for ref in refs:
            assert digest(ROOT / ref["path"]) == ref["sha256"]
        bad = copy.deepcopy(spec)
        bad["column_correspondence"]["holdout"][0]["poly_x"] += 20
        bad_spec = Path(temp) / "bad-spec.json"
        bad_spec.write_text(json.dumps(bad))
        rejected = run(ROOT, bad_spec, Path(temp) / "rejected")
        assert rejected["status"] == "FAIL"
        assert rejected["geometry"]["status"] == "PASS"
        assert not rejected["precise_CT_projection_allowed"]


def test_local_parts_must_be_connected_and_sized():
    f = feature("A", 20)
    f["local_parts"] = [dict(id="end", bounds=[10, 70, 30, 80], basis="Scoped correction")]
    p = feature_polygon(f, 6)
    assert p.geom_type == "Polygon" and p.area > stroke(f["design_path"], 8).area
    f["local_parts"][0]["bounds"] = [60, 60, 70, 70]
    with pytest.raises(ValueError, match="join"):
        feature_polygon(f, 6)
    f["local_parts"][0]["bounds"] = [19, 20, 21, 25]
    with pytest.raises(ValueError, match="minimum"):
        feature_polygon(f, 6)


def test_reviewed_m1_revision_keeps_approved_geometry_and_encloses_all_gate_cuts():
    from shapely.geometry import box

    from silicon_eye.review_package import Inputs

    parent = json.loads((ROOT / "benchmarks/m1-geometry-pilot-v1/spec-v1.json").read_text())
    spec_path = ROOT / "benchmarks/m1-geometry-pilot-reviewed-v2/spec-v1.json"
    spec = json.loads(spec_path.read_text())
    reviewed_features(ROOT, Inputs(ROOT), spec)
    old = {o["id"]: o for o in parent["features"]}
    new = {o["id"]: o for o in spec["features"]}
    changed = {key for key in old if old[key] != new[key]}
    assert changed == {"M1-P06", "M1-P07", "M1-P08"}
    for key in ("M1-P01", "M1-P02", "M1-P03", "M1-P04", "M1-P05", "M1-P09"):
        assert old[key] == new[key]
    for key in changed:
        assert old[key]["design_path"] == new[key]["design_path"]
        assert old[key]["source_path"] == new[key]["source_path"]
    # Outside the corrected left band, both horizontal guard arms stay exact.
    before = feature_polygon(old["M1-P08"])
    after = feature_polygon(new["M1-P08"])
    assert before.symmetric_difference(after).difference(box(2171, 1944, 2193, 2262)).area == 0
    assert after.area > before.area
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        report = run(ROOT, spec_path, Path(temp) / "reviewed")
        assert report["status"] == "SCOPED_REVIEWED_WITH_LIMITATIONS"
        assert report["geometry"]["status"] == "PASS"
        assert sum(r["CT_count"] for r in report["CT_support_candidates"]) == 95
        assert all(r["geometry_status"] == "PASS" for r in report["CT_support_candidates"])
        assert len(report["pending_gate_CT_ids"]) == 8
        assert not report["human_questions"] and not report["requires_user_action_now"]
        assert not report["precise_CT_projection_allowed"]
        assert not report["automatic_network_export_allowed"]


@pytest.mark.parametrize("field", ["pending_gate_CT_ids", "budget"])
def test_reviewed_revision_cannot_erase_source_limits_or_relax_budget(field):
    from silicon_eye.review_package import Inputs

    spec = json.loads((ROOT / "benchmarks/m1-geometry-pilot-reviewed-v2/spec-v1.json").read_text())
    spec[field] = [] if field == "pending_gate_CT_ids" else {}
    with pytest.raises(ValueError, match="fixed context"):
        reviewed_features(ROOT, Inputs(ROOT), spec)
