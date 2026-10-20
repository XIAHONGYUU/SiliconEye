"""Regression checks for scope supersession, protected evidence and release gates."""

import copy
import json
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from silicon_eye.geometry_reconstruction import object_polygon
from silicon_eye.poly_closeout import apply_count_approval, audit, consolidate, revise_feedback
from silicon_eye.scene_geometry import load_locked

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def inputs():
    spec = json.loads((ROOT / "benchmarks/poly-closeout-v1/spec-v1.json").read_text())
    names = [
        "parent",
        "inventory",
        "AA",
        "small_joint",
        "lower_joint",
        "wide_review",
        "wide_match",
        "U05_review",
    ]
    return spec, {name: load_locked(ROOT, spec["inputs"][name]) for name in names}


def build(spec, d):
    return consolidate(
        d["parent"],
        d["inventory"],
        d["AA"],
        d["small_joint"],
        d["lower_joint"],
        d["wide_review"],
        spec,
        d["wide_match"],
        d["U05_review"],
    )


def test_scope_replacement_not_appending_duplicate_templates(inputs):
    spec, d = inputs
    model = build(spec, d)
    replaced_groups = {g for groups in spec["replace_scope_groups"].values() for g in groups}
    retained = {o["id"] for o in d["parent"]["objects"] if o.get("group_id") not in replaced_groups}
    observed = {o["id"] for o in d["inventory"]["objects"]}
    ids = [o["id"] for o in model["objects"]]
    assert set(ids) == retained | observed
    assert len(ids) == len(set(ids)) == 703
    assert len(model["supersession_ledger"]) == 269
    assert sum(x["action"] == "retired_scope_template" for x in model["supersession_ledger"]) == 261
    assert model["unobserved_slots"] == 2


def test_sources_and_existing_relative_approvals_are_not_rewritten(inputs):
    spec, d = inputs
    snapshot = copy.deepcopy(d)
    model = build(spec, d)
    assert d == snapshot
    by_id = {o["id"]: o for o in model["objects"]}
    for source in d["inventory"]["objects"]:
        assert by_id[source["id"]]["native_outline"] == source["native_outline"]
    for old in d["parent"]["objects"]:
        if old["id"] in spec["protected_source_ids"]:
            assert by_id[old["id"]]["legacy_record"] == old
    for accepted in d["lower_joint"]["derived_objects"]:
        assert (
            by_id[accepted["source_poly_id"]]["layout_outline"] == accepted["joint_layout_outline"]
        )
    assert model["AA_objects"] == d["AA"]["objects"]
    assert not Polygon(by_id["V3_G1"]["layout_outline"]).intersects(
        Polygon(by_id["V3_G2"]["layout_outline"])
    )
    assert not Polygon(by_id["S03-03"]["layout_outline"]).intersects(
        Polygon(by_id["S03-04"]["layout_outline"])
    )


def test_resistor_and_active_inside_guard_named_group(inputs):
    spec, d = inputs
    model = build(spec, d)
    by_id = {o["id"]: o for o in model["objects"]}
    resistor = by_id["SG-U04-W01"]
    assert resistor["kind"] == "resistor_POLY_body"
    assert resistor["AA_target"] is None
    assert "human_confirmed" in resistor["acceptance"]["material"]
    p = Polygon(resistor["layout_outline"])
    assert all(
        p.intersection(object_polygon(o)).area < 1e-7
        for o in model["AA_objects"]
        if o["id"] in model["guard_AA_ids"]
    )
    strip = "AA2-LEFT-GUARD-NETWORK-SHARED-GUARDS-1"
    assert by_id["G61-P01"]["AA_target"] == strip
    assert strip not in model["guard_AA_ids"]
    report = audit(model)
    assert not any("guard" in w["reason"] for w in report["warnings"])
    assert report["polygon_geometry_status"] == "PASS"
    assert report["errors"] == [
        {"id": "G28-P05", "reason": "non_target_AA_overlap", "AA_ids": ["AA-F00872"]}
    ]
    assert report["release_status"].startswith("BLOCKED")
    assert len(report["human_review_issues"]) == 4


def test_conflicting_or_impossible_new_relation_is_rejected(inputs):
    spec, d = inputs
    changed = copy.deepcopy(spec)
    changed["new_joint_relations"][0]["object_ids"] = ["R2_poly_Q1_support"]
    with pytest.raises(ValueError, match="existing reviewed"):
        build(changed, d)
    changed = copy.deepcopy(spec)
    changed["new_joint_relations"][0]["width_px"] = 10000
    with pytest.raises(ValueError, match="infeasible"):
        build(changed, d)
    changed = copy.deepcopy(spec)
    changed["guard_AA_ids"] = []
    with pytest.raises(ValueError, match="guard roles"):
        build(changed, d)


def test_quality_gate_detects_regression_not_just_file_success(inputs):
    spec, d = inputs
    model = build(spec, d)
    target = next(o for o in model["objects"] if o["AA_target"])
    target["layout_outline"] = [[0, 0], [100, 0], [100, 100], [0, 100]]
    report = audit(model)
    assert report["geometry_status"] == "FAIL"
    assert any(e["reason"] == "explicit_target_AA_missed" for e in report["errors"])
    model = build(spec, d)
    model["objects"][1]["layout_outline"] = model["objects"][0]["layout_outline"]
    assert audit(model)["positive_area_overlap_pairs"]


def test_approval_does_not_spread_and_matched_rows_stay_aligned(inputs):
    spec, d = inputs
    model = build(spec, d)
    for obj in model["objects"]:
        if obj["geometry_method"] == "explicit_small_AA_relation":
            assert ("human_accepted" in obj["acceptance"]["joint_geometry"]) == (
                obj["relation_record"]["scope"] == "U05"
            )
    rows = [[o for o in model["objects"] if o["group_id"] == gid] for gid in ["G33", "G34"]]
    assert len(rows[0]) == len(rows[1])
    for upper, lower in zip(*rows, strict=True):
        assert [p[0] for p in upper["layout_outline"]] == [p[0] for p in lower["layout_outline"]]


@pytest.fixture(scope="module")
def revision_inputs():
    settings = json.loads((ROOT / "benchmarks/poly-closeout-v2/spec-v1.json").read_text())
    refs = settings["inputs"]
    return (
        settings,
        load_locked(ROOT, refs["revision_parent"]),
        load_locked(ROOT, refs["AA"]),
        load_locked(ROOT, refs["revision_feedback"]),
    )


def revised(values):
    settings, parent, aa, feedback = values
    return revise_feedback(parent, aa, settings, feedback, ROOT)


def test_feedback_counts_and_right_inference_not_blanket_approval(revision_inputs):
    model = revised(revision_inputs)
    assert len(model["objects"]) == 699
    assert len(model["AA_objects"]) == 336
    assert [
        sum(o["group_id"] == scope for o in model["objects"]) for scope in ["Q1", "Q2", "Q3"]
    ] == [30, 30, 10]
    right = [o for o in model["objects"] if "RIGHT" in o["id"]]
    assert len(right) == 5
    assert all("human only estimated" in o["count_status"] for o in right)
    assert all(
        Polygon(o["layout_outline"]).bounds[2] - Polygon(o["layout_outline"]).bounds[0] == 12
        for o in right
    )
    assert all(p["all_counts_match"] for p in model["profile_evidence"])
    report = audit(model)
    assert report["geometry_status"] == "PASS"
    assert not report["errors"] and not report["positive_area_overlap_pairs"]
    assert len(report["human_review_issues"]) == 1
    assert report["release_status"].startswith("BLOCKED")


def test_retiring_false_aa_does_not_shorten_mos_or_change_other_accepted_work(revision_inputs):
    parent = revision_inputs[1]
    frozen = copy.deepcopy(parent)
    model = revised(revision_inputs)
    assert parent == frozen
    current = {o["id"]: o for o in model["objects"]}
    retired = {
        o["id"]
        for o in model["supersession_ledger"]
        if o.get("reason") == "new human feedback rejects count/geometry"
    }
    for obj in parent["objects"]:
        if obj["id"] not in retired:
            assert current[obj["id"]] == obj
    assert "G28-P05" in current
    assert model["AA_retirements"][0]["id"] == "AA-F00872"
    assert not any(o["id"] == "AA-F00872" for o in model["AA_objects"])


def test_stepped_aa_uses_local_height_instead_of_outer_bbox(revision_inputs):
    model = revised(revision_inputs)
    gates = [o for o in model["objects"] if o["AA_target"] == "AA2-MIDDLE-MOS-A2-0"]
    assert len(gates) == 4
    bottoms = [Polygon(o["layout_outline"]).bounds[3] for o in gates]
    assert bottoms[0] == bottoms[1] < bottoms[2] == bottoms[3]
    assert all(o["relation_cross_section"] for o in gates)


def test_feedback_cannot_retire_unapproved_extra_aa_or_frozen_poly(revision_inputs):
    settings, parent, aa, feedback = revision_inputs
    changed = copy.deepcopy(settings)
    changed["revision"]["retire_AA_ids"].append("AA-W02")
    with pytest.raises(ValueError, match="exceeds explicit"):
        revise_feedback(parent, aa, changed, feedback, ROOT)

    changed = copy.deepcopy(settings)
    changed["revision"]["replace_groups"]["Q1"].append("G36")
    with pytest.raises(ValueError, match="approved object"):
        revise_feedback(parent, aa, changed, feedback, ROOT)


def test_human_six_overrides_five_without_rewriting_profile_evidence():
    spec = json.loads((ROOT / "benchmarks/poly-closeout-v3/spec-v1.json").read_text())
    parent = load_locked(ROOT, spec["inputs"]["revision_parent"])
    aa = load_locked(ROOT, spec["inputs"]["AA"])
    approval = load_locked(ROOT, spec["inputs"]["count_approval"])
    frozen = copy.deepcopy(parent)
    model = apply_count_approval(parent, aa, spec, approval)
    assert parent == frozen
    assert len(model["objects"]) == 700
    right = [o for o in model["objects"] if o["id"].startswith("CL3-Q3-RIGHT")]
    assert len(right) == 6
    assert all(o["count_status"].startswith("human_confirmed_six") for o in right)
    assert model["profile_evidence"] == parent["profile_evidence"]
    assert model["algorithm_evaluation"]["previous_AI_count"] == 5
    assert model["algorithm_evaluation"]["human_count"] == 6
    assert model["AA_objects"] == parent["AA_objects"]
    for obj in parent["objects"]:
        if obj["id"] not in spec["final_count_revision"]["old_ids"]:
            current = next(o for o in model["objects"] if o["id"] == obj["id"])
            assert current["layout_outline"] == obj["layout_outline"]
            assert current["native_outline"] == obj["native_outline"]
    report = audit(model)
    assert report["geometry_status"] == "PASS"
    assert report["release_status"] == "READY_FOR_CT_working_baseline"
    assert not report["human_review_issues"]
    incorrect = copy.deepcopy(approval)
    incorrect["right_MOS_count"] = 7
    with pytest.raises(ValueError, match="explicit human"):
        apply_count_approval(parent, aa, spec, incorrect)
