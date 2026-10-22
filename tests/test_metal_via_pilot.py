"""Joint material checks must not turn plausible geometry into electrical truth."""

import copy
import json
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import box

from silicon_eye.geometry_reconstruction import digest
from silicon_eye.metal_via_pilot import (
    interface_audit,
    local_correspondence,
    reviewed_interface,
    run,
)
from silicon_eye.review_package import Inputs

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "benchmarks/m1-v1-m2-joint-pilot-v1/spec-v1.json"
REVIEWED_SPEC = ROOT / "benchmarks/m1-v1-m2-joint-reviewed-v2/spec-v1.json"
TRANSFER_SPEC = ROOT / "benchmarks/metal-short-branch-transfer-v1/spec-v1.json"
CANDIDATE_SPEC = ROOT / "benchmarks/metal-new-interface-candidate-v1/spec-v1.json"
ADJUDICATED_SPEC = ROOT / "benchmarks/metal-new-interface-reviewed-v2/spec-v1.json"


def spec():
    return json.loads(SPEC.read_text())


def test_both_bearings_are_required_even_when_layers_overlap():
    s = spec()
    lower, upper = box(2110, 1942, 2193, 1996), box(2109, 1898, 2193, 2312)
    report = interface_audit(s["cuts"], lower, upper, s["via_budget"])
    assert report["status"] == "PASS"
    assert not report["electrical_connection_confirmed"] and not report["count_complete"]
    for a, b in [(box(2110, 1942, 2178, 1996), upper),
                 (lower, box(2109, 1898, 2178, 2312))]:
        report = interface_audit(s["cuts"], a, b, s["via_budget"])
        assert report["status"] == "FAIL"
        assert any(e["reason"] == "missing_lower_or_upper_enclosure" for e in report["errors"])


@pytest.mark.parametrize("change", ["layer", "evidence", "empty"])
def test_overlap_is_not_via_evidence_and_layer_pair_is_typed(change):
    s = spec()
    if change == "layer":
        s["cuts"][0]["layer_pair"] = ["M2", "M3"]
    elif change == "evidence":
        s["cuts"][0]["observation_id"] = None
    else:
        s["cuts"] = []
    with pytest.raises(ValueError):
        interface_audit(s["cuts"], box(0, 0, 6000, 5000),
                        box(0, 0, 6000, 5000), s["via_budget"])


def test_overlapping_or_irregular_cuts_fail_without_changing_other_layers():
    s = spec()
    broad = box(0, 0, 6000, 5000)
    cuts = copy.deepcopy(s["cuts"])
    cuts[1]["bounds"] = cuts[0]["bounds"]
    r = interface_audit(cuts, broad, broad, s["via_budget"])
    assert any(e["reason"] == "cut_gap_failed" for e in r["errors"])
    cuts = copy.deepcopy(s["cuts"])
    cuts[4]["bounds"] = [v + (1 if i % 2 == 0 else 0)
                         for i, v in enumerate(cuts[4]["bounds"])]
    r = interface_audit(cuts, broad, broad, s["via_budget"])
    assert any(e["reason"] == "irregular_array_pitch" for e in r["errors"])


def test_same_array_holdout_cannot_launder_independent_registration():
    s = spec()
    r = local_correspondence(s["observations"], s["fit_ids"], 5)
    assert r["same_array_holdout_status"] == "PASS"
    assert r["maximum_holdout_error_px"] < 5
    assert r["independent_structure_status"] == "NOT_QUALIFIED"
    assert not r["precise_projection_allowed"] and not r["extrapolation_allowed"]
    s["observations"][4]["m2_xy"][1] += 20
    assert local_correspondence(s["observations"], s["fit_ids"], 5)[
        "same_array_holdout_status"
    ] == "FAIL"


def test_degenerate_or_reused_fit_points_are_rejected():
    s = spec()
    with pytest.raises(ValueError, match="distinct"):
        local_correspondence(s["observations"], ["A11", "A11", "A31"], 5)
    with pytest.raises(ValueError, match="Collinear"):
        local_correspondence(s["observations"], ["A11", "A12", "A13"], 5)


def test_real_joint_candidate_preserves_reviews_parent_geometry_and_unknowns():
    s = spec()
    refs = [s["parent_M1_spec"], s["parent_M1_model"], s["parent_M1_report"]]
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        out = Path(temp) / "delivery"
        r = run(ROOT, SPEC, out)
        assert r["status"] == "REVIEW_REQUIRED"
        assert r["M1_geometry"]["status"] == r["M2_geometry"]["status"] == "PASS"
        assert r["via_geometry"]["candidate_cut_count"] == 9
        assert r["inherited_CT_model_enclosure_count"] == 95
        assert len(r["inherited_unknown_scopes"]["unknown_scopes"]) == 6
        assert not r["precise_projection_allowed"] and not r["automatic_network_export_allowed"]
        model = json.loads((out / "model.json").read_text())
        original = json.loads((ROOT / s["parent_M1_model"]["path"]).read_text())
        assert model["inherited_M1_objects"] == original["objects"]
        assert not model["net_edges"] and not model["adopted_into_joint_snapshot"]
        assert model["proposed_M1_addition"]["metal_id"] == "M1-P08"
        assert r["unknown_edge_column"]["cut_count"] is None
        manifest = json.loads((out / "manifest.json").read_text())
        for path, sha in manifest["verified_inputs"].items():
            assert digest(ROOT / path) == sha
        for name, sha in manifest["artifacts"].items():
            assert digest(out / name) == sha
        assert all(digest(ROOT / ref["path"]) == ref["sha256"] for ref in refs)


def test_failed_interface_does_not_export_a_candidate_model():
    s = spec()
    s["cuts"][0]["bounds"] = [2300, 1950, 2306, 1956]
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        request = Path(temp) / "bad.json"
        request.write_text(json.dumps(s))
        out = Path(temp) / "rejected"
        assert run(ROOT, request, out)["status"] == "FAIL"
        assert (out / "report.json").is_file()
        assert not (out / "model.json").exists()
        assert not (out / "index.html").exists()


def test_human_connection_review_cannot_alter_geometry_or_add_fourth_v1_column():
    s = json.loads(REVIEWED_SPEC.read_text())
    r = reviewed_interface(Inputs(ROOT), s)
    assert r["decisions"]["M1_box_V1_present"] is False
    assert r["decisions"]["M2_box_via_layer"] == "V2"
    assert r["width_and_edge_constraints"]["pixel_width"] is None
    for key in ("cuts", "M2_features", "observations"):
        changed = copy.deepcopy(s)
        changed[key].append(copy.deepcopy(changed[key][0]))
        with pytest.raises(ValueError, match="baseline geometry"):
            reviewed_interface(Inputs(ROOT), changed)


def test_v2_or_width_decision_cannot_be_laundered_into_extra_v1():
    s = json.loads(REVIEWED_SPEC.read_text())
    review = reviewed_interface(Inputs(ROOT), s)

    class Evidence:
        def document(self, ref):
            return spec()

        def human(self, ref):
            return changed_review

    changed_review = copy.deepcopy(review)
    changed_review["decisions"]["M2_box_via_layer"] = "V1"
    with pytest.raises(ValueError, match="identity"):
        reviewed_interface(Evidence(), s)
    changed_review = copy.deepcopy(review)
    changed_review["width_and_edge_constraints"]["new_cut_creation_authorized"] = True
    with pytest.raises(ValueError, match="extra V1"):
        reviewed_interface(Evidence(), s)


def test_reviewed_local_edge_is_recorded_without_inventing_an_m3_connection():
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        out = Path(temp) / "delivery"
        report = run(ROOT, REVIEWED_SPEC, out)
        assert report["status"] == "SCOPED_REVIEWED_WITH_LIMITATIONS"
        assert report["electrical_connection_confirmed"]
        assert report["electrical_connection_scope"]["lower_metal_id"] == "M1-P08"
        assert not report["human_questions"] and not report["requires_user_action_now"]
        assert not report["precise_projection_allowed"]
        assert report["source_correspondence"]["independent_structure_status"] == "NOT_QUALIFIED"
        assert not report["automatic_network_export_allowed"]
        model = json.loads((out / "model.json").read_text())
        assert len(model["V1_cuts"]) == 9
        assert model["native_only_V2_observations"][0]["layer_pair"] == ["M2", "M3"]
        assert model["native_only_V2_observations"][0]["upper_metal_id"] is None
        assert not model["native_only_V2_observations"][0]["M3_connection_confirmed"]
        assert not model["net_edges"] and len(model["reviewed_local_connections"]) == 1
        old = json.loads((ROOT / "docs/assets/m1-v1-m2-joint-pilot-v1/model.json").read_text())
        assert model["inherited_M1_objects"] == old["inherited_M1_objects"]
        assert model["V1_cuts"] == old["V1_cuts"]
        page = (out / "index.html").read_text()
        assert "J1／J2 已裁决" in page
        assert "本轮一次核对清单" not in page


def test_known_short_branch_transfer_retains_baseline_and_avoids_overlap_join():
    s = json.loads(TRANSFER_SPEC.read_text())
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        out = Path(temp) / "delivery"
        r = run(ROOT, TRANSFER_SPEC, out)
        assert r["status"] == "KNOWN_EXAMPLE_TRANSFER_VERIFIED_WITH_LIMITATIONS"
        assert all(a["status"] == "PASS" for a in r["geometry"].values())
        assert r["via_geometry"]["status"] == "PASS"
        assert r["geometry"]["M1"]["minimum_gap_px"] >= 3
        assert r["overlap_controls"][0]["overlap_area_px2"] > 0
        assert not r["overlap_controls"][0]["inferred_connection"]
        assert not r["overlap_controls"][0]["physical_absence_confirmed"]
        assert r["physical_cut_count"] is None
        assert r["new_physical_connections"] == 0
        assert not r["precise_projection_allowed"] and not r["requires_user_action_now"]
        assert len(r["baseline_unknown_scopes"]["unknown_scopes"]) == 6
        assert r["baseline_human_decisions"]["M2_box_via_layer"] == "V2"
        model = json.loads((out / "model.json").read_text())
        assert not model["net_edges"] and not model["adopted_into_joint_snapshot"]
        assert model["reviewed_local_connections"][0]["via_id"] == s["via_group_id"]
        assert model["source_to_design_transform"] is None
        manifest = json.loads((out / "manifest.json").read_text())
        for path, sha in manifest["verified_inputs"].items():
            assert digest(ROOT / path) == sha
        for name, sha in manifest["artifacts"].items():
            assert digest(out / name) == sha


def test_short_finger_extension_into_neighbor_is_rejected_without_model():
    s = json.loads(TRANSFER_SPEC.read_text())
    s["features_by_layer"]["M1"][0]["design_path"][0][1] = 3107
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        path = Path(temp) / "request.json"
        path.write_text(json.dumps(s))
        out = Path(temp) / "rejected"
        r = run(ROOT, path, out)
        assert r["status"] == "FAIL" and r["geometry"]["M1"]["status"] == "FAIL"
        assert not (out / "model.json").exists()


@pytest.mark.parametrize("mistake", ["extra_via", "pad_endpoint", "source_trace"])
def test_transfer_blocks_unobserved_via_or_moving_known_endpoint(mistake):
    s = json.loads(TRANSFER_SPEC.read_text())
    if mistake == "extra_via":
        s["interface_support_regions"].append(copy.deepcopy(s["interface_support_regions"][0]))
        message = "Unsupported extra via"
    elif mistake == "pad_endpoint":
        s["observations"][0]["m2_xy"] = [1212, 3205]
        message = "another source bright spot"
    else:
        s["native_traces"]["m2"][0]["points"][1][0] += 15
        message = "Native trace changed"
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        path = Path(temp) / "request.json"
        path.write_text(json.dumps(s))
        with pytest.raises(ValueError, match=message):
            run(ROOT, path, Path(temp) / "rejected")


def test_new_candidate_cannot_inherit_prior_designs_physical_approval():
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        out = Path(temp) / "delivery"
        report = run(ROOT, CANDIDATE_SPEC, out)
        assert report["status"] == "REVIEW_REQUIRED"
        assert report["requires_user_action_now"]
        assert report["human_questions"][0]["id"] == "N1"
        assert "local_connection" not in report and "historical_statement" not in report
        assert report["hypothesized_local_connection"]["status"] == (
            "AI_candidate_not_human_reviewed"
        )
        assert report["initial_AI_evaluation"]["human_ground_truth"] is None
        assert report["initial_AI_evaluation"]["correction_count"] is None
        assert report["via_geometry"]["status"] == "PASS"
        assert report["source_correspondence"]["status"] == "NOT_QUALIFIED"
        assert not report["automatic_network_export_allowed"]
        model = json.loads((out / "model.json").read_text())
        assert model["reviewed_local_connections"] == [] and model["net_edges"] == []
        assert len(model["hypothesized_local_connections"]) == 1
        page = (out / "index.html").read_text()
        assert "第三组：W1左侧新短支路N1" in page
        assert "已知样本迁移回放，不是新盲测" not in page


@pytest.mark.parametrize("mistake", ["prior_model", "question_removed"])
def test_candidate_requires_correct_release_and_pending_review(mistake):
    s = json.loads(CANDIDATE_SPEC.read_text())
    if mistake == "prior_model":
        s["released_design"]["model"] = s["baseline"]["model"]
        message = "Released design reference changed"
    else:
        s["human_questions"] = []
        message = "explicit review question"
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        request = Path(temp) / "request.json"
        request.write_text(json.dumps(s))
        with pytest.raises(ValueError, match=message):
            run(ROOT, request, Path(temp) / "delivery")


def test_frozen_initial_candidate_cannot_move_to_make_a_fit():
    s = json.loads(CANDIDATE_SPEC.read_text())
    s["observations"][0]["m2_xy"] = [1109, 3220]
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        request = Path(temp) / "request.json"
        request.write_text(json.dumps(s))
        with pytest.raises(ValueError, match="Frozen candidate reference"):
            run(ROOT, request, Path(temp) / "delivery")


def test_ai_candidate_cannot_supply_its_own_ground_truth():
    s = json.loads(CANDIDATE_SPEC.read_text())
    initial = json.loads((ROOT / s["evidence"]["initial_candidate"]["path"]).read_text())
    initial["evaluation"]["human_ground_truth"] = "confirmed"
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        initial_path = Path(temp) / "invalid-observation.json"
        initial_path.write_text(json.dumps(initial))
        s["evidence"]["initial_candidate"] = dict(
            path=str(initial_path.relative_to(ROOT)), sha256=digest(initial_path)
        )
        request = Path(temp) / "request.json"
        request.write_text(json.dumps(s))
        with pytest.raises(ValueError, match="unreviewed AI origin"):
            run(ROOT, request, Path(temp) / "delivery")


def test_adjudicated_candidate_retains_initial_judgment_and_only_confirms_local_edge():
    original = json.loads(CANDIDATE_SPEC.read_text())
    initial_ref = original["evidence"]["initial_candidate"]
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        out = Path(temp) / "delivery"
        report = run(ROOT, ADJUDICATED_SPEC, out)
        assert report["status"] == "SCOPED_REVIEWED_WITH_LIMITATIONS"
        assert not report["human_questions"] and not report["requires_user_action_now"]
        assert report["local_connection"]["status"] == "human_confirmed_local_interface"
        assert report["new_physical_connections"] == 1
        assert report["evaluation_result"]["identity_correct"]
        assert report["evaluation_result"]["destination_correct"]
        assert report["initial_AI_evaluation"]["human_ground_truth"] is None
        assert not report["precise_projection_allowed"]
        assert not report["automatic_network_export_allowed"]
        model = json.loads((out / "model.json").read_text())
        assert len(model["reviewed_local_connections"]) == 1
        assert model["hypothesized_local_connections"] == [] and model["net_edges"] == []
        assert model["physical_cut_count"] is None
        assert model["objects_by_layer"] == original["features_by_layer"]
        assert model["V1_support_regions"] == original["interface_support_regions"]
        assert digest(ROOT / initial_ref["path"]) == initial_ref["sha256"]
        page = (out / "index.html").read_text()
        assert "N1身份与接入已确认" in page and "请只裁决N1" not in page


@pytest.mark.parametrize("field", ["features_by_layer", "observations"])
def test_adjudication_cannot_change_approved_candidate_geometry_or_reference(field):
    s = json.loads(ADJUDICATED_SPEC.read_text())
    if field == "features_by_layer":
        s[field]["M1"][0]["design_width"] += 1
    else:
        s[field][0]["m1_xy"][0] += 1
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        request = Path(temp) / "request.json"
        request.write_text(json.dumps(s))
        with pytest.raises(ValueError, match="cannot revise frozen geometry"):
            run(ROOT, request, Path(temp) / "delivery")


PAIR_SPEC = ROOT / "benchmarks/m2-v2-m3-joint-pilot-v1/spec-v1.json"


def test_v2_uses_declared_pair_and_still_requires_both_bearings():
    s = json.loads(PAIR_SPEC.read_text())
    cuts, budget = s["interface_support_regions"], s["via_budget"]
    broad = box(1900, 1840, 2520, 2320)
    r = interface_audit(cuts, broad, broad, budget, layer_stack=s["layer_stack"])
    assert r["status"] == "PASS" and not r["electrical_connection_confirmed"]
    assert not r["count_complete"]
    with pytest.raises(ValueError, match="Wrong via layer pair"):
        interface_audit(cuts, broad, broad, budget)  # V1 default cannot accept V2.
    wrong = copy.deepcopy(cuts)
    wrong[0]["layer"] = "V1"
    with pytest.raises(ValueError, match="Wrong via layer pair"):
        interface_audit(wrong, broad, broad, budget, layer_stack=s["layer_stack"])
    for lower, upper in [(broad, box(2200, 1900, 2500, 2100)),
                         (box(2200, 1900, 2500, 2100), broad)]:
        r = interface_audit(cuts, lower, upper, budget, layer_stack=s["layer_stack"])
        assert r["status"] == "FAIL"
        assert r["errors"][0]["reason"] == "missing_lower_or_upper_enclosure"


def test_new_pair_preserves_m2_and_does_not_forge_m3_destination_or_hole_count():
    s = json.loads(PAIR_SPEC.read_text())
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as tmp:
        out = Path(tmp) / "delivery"
        r = run(ROOT, PAIR_SPEC, out)
        m = json.loads((out / "model.json").read_text())
        b = json.loads((ROOT / s["baseline"]["spec"]["path"]).read_text())
        assert r["status"] == "REVIEW_REQUIRED"
        assert r["via_geometry"]["status"] == "PASS"
        assert r["via_geometry"]["support_region_count"] == 1
        assert "candidate_cut_count" not in r["via_geometry"]
        assert r["via_geometry"]["physical_cut_count"] is None
        assert m["objects_by_layer"]["M2"] == b["M2_features"]
        assert m["inherited_native_V2"]["identity_status"] == "human_confirmed"
        assert not m["inherited_native_V2"]["M3_connection_confirmed"]
        assert m["physical_cut_count"] is None
        assert m["reviewed_local_connections"] == [] and m["net_edges"] == []
        assert r["new_physical_connections"] == 0
        assert not r["precise_projection_allowed"] and not r["extrapolation_allowed"]
        assert not r["automatic_network_export_allowed"]
        assert r["source_correspondence"]["matrix"] is None
        assert len(r["human_questions"]) == 1
        control = r["overlap_controls"][0]
        assert control["overlap_area_px2"] > 0 and not control["inferred_connection"]
        assert not control["physical_absence_confirmed"]
        assert (out / "m3-wide-raw.png").exists()
        assert not (out / "m1-wide-raw.png").exists()
        assert 'data-layer="M3"' in (out / "joint-design.svg").read_text()
        assert 'data-layer="V2"' in (out / "joint-design.svg").read_text()
        assert 'data-layer="V1"' not in (out / "joint-design.svg").read_text()


@pytest.mark.parametrize("change", ["move_via", "move_m2", "fake_m3_center", "hide_question",
                                   "change_m3", "claim_connection", "wrong_stack"])
def test_new_pair_rejects_evidence_drift_or_inherited_approval(change):
    s = json.loads(PAIR_SPEC.read_text())
    if change == "move_via":
        s["source_regions"]["m2"][0]["bounds"][0] += 10
    elif change == "move_m2":
        s["features_by_layer"]["M2"][0]["design_path"][0][0] += 5
    elif change == "fake_m3_center":
        s["observations"] = [dict(id="fake", m2_xy=[1944, 1929], m3_xy=[1944, 1929])]
    elif change == "hide_question":
        s["human_questions"] = []
    elif change == "change_m3":
        s["features_by_layer"]["M3"][0]["design_width"] += 5
    elif change == "claim_connection":
        s["interface_support_regions"][0]["electrical_connection_confirmed"] = True
    else:
        s["layer_stack"] = ["M1", "V1", "M2"]
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as tmp:
        path = Path(tmp) / "invalid.json"
        path.write_text(json.dumps(s))
        out = Path(tmp) / "delivery"
        with pytest.raises(ValueError):
            run(ROOT, path, out)
        assert not out.exists()


PAIR_REVIEWED_SPEC = ROOT / "benchmarks/m2-v2-m3-joint-reviewed-v2/spec-v1.json"


def test_reviewed_v2_records_only_the_scoped_b1_connection():
    parent = json.loads(PAIR_SPEC.read_text())
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as tmp:
        out = Path(tmp) / "delivery"
        r = run(ROOT, PAIR_REVIEWED_SPEC, out)
        m = json.loads((out / "model.json").read_text())
        assert r["status"] == "SCOPED_REVIEWED_WITH_LIMITATIONS"
        assert r["human_questions"] == [] and not r["requires_user_action_now"]
        assert r["local_connection"]["upper_metal_id"] == "M3-J-B1"
        assert r["local_connection"]["connection_confirmed"]
        assert r["new_physical_connections"] == 1
        assert r["evaluation_result"]["destination_correct"]
        assert not r["evaluation_result"]["identity_re_evaluated"]
        assert m["objects_by_layer"] == parent["features_by_layer"]
        assert m["V2_support_regions"] == parent["interface_support_regions"]
        assert len(m["reviewed_local_connections"]) == 1
        assert m["hypothesized_local_connections"] == [] and m["net_edges"] == []
        assert m["physical_cut_count"] is None and not r["precise_projection_allowed"]
        assert not r["automatic_network_export_allowed"] and not r["extrapolation_allowed"]
        assert r["source_correspondence"]["matrix"] is None
        initial = Inputs(ROOT).document(parent["initial_observation"])
        assert all(v is None for v in initial["evaluation"].values())
        page = (out / "index.html").read_text()
        assert "K1已确认" in page and "只需确认M3承载金属" not in page
        assert "跨层承载关系待审" not in page


@pytest.mark.parametrize("change", ["geometry", "source", "budget"])
def test_pair_review_cannot_smuggle_geometry_source_or_rule_changes(change):
    s = json.loads(PAIR_REVIEWED_SPEC.read_text())
    if change == "geometry":
        s["features_by_layer"]["M3"][0]["design_path"][0][1] += 1
    elif change == "source":
        s["source_regions"]["m2"][0]["bounds"][0] += 1
    else:
        s["via_budget"]["enclosure_px"] = 0.1
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as tmp:
        request = Path(tmp) / "request.json"
        request.write_text(json.dumps(s))
        with pytest.raises(ValueError, match="cannot revise frozen geometry or evidence"):
            run(ROOT, request, Path(tmp) / "delivery")
