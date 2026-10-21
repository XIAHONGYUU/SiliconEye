"""Reproduce bounded source corrections without moving approved design records."""

import copy
import json
from pathlib import Path

from silicon_eye.ct_transfer import apply_source_correspondence_corrections
from silicon_eye.joint_layers import audit_joint, load_snapshot

ROOT = Path(__file__).resolve().parents[1]


def test_source_ownership_replay_preserves_all_geometry_and_blocks_reintroduced_alias():
    before = load_snapshot(ROOT, ROOT / "configs/joint-work-layer-v1.json")
    after = load_snapshot(ROOT, ROOT / "configs/joint-work-layer-v2.json")
    base = ROOT / "benchmarks/ct-source-ownership-v1"
    patches = json.loads((base / "source-corrections-v1.json").read_text())["changes"]
    review = json.loads((base / "AI-source-review-v1.json").read_text())
    ref = after["values"]["contacts"]["source_reinspection_ref"]
    replayed = apply_source_correspondence_corrections(
        before["contacts"], patches, review["authorized_source_correspondence_ids"], ref
    )
    assert replayed == after["contacts"]
    assert len(patches) == 73 and len(replayed) == 10287
    assert before["materials"] == after["materials"]
    assert before["values"]["unknown"] == after["values"]["unknown"]
    assert before["values"]["use_contract"] == after["values"]["use_contract"]
    assert before["values"]["human_review"] == after["values"]["human_review"]
    changed = {c["id"] for c in patches}
    for old, new in zip(before["contacts"], after["contacts"], strict=True):
        if old["id"] not in changed:
            assert old == new
        else:
            assert new["source_correspondence_history"][-1]["before"] == old["source_evidence"]
            for field in old.keys() | new.keys():
                if field not in {"source_evidence", "source_correspondence_history"}:
                    assert old.get(field) == new.get(field)
    report = audit_joint(
        replayed, after["materials"], after["manifest"]["budget"], before["contacts"]
    )
    assert report["geometry_status"] == report["source_gate"]["status"] == "PASS"
    assert not report["source_gate"]["new_conflicts"]
    assert not report["source_gate"]["inherited_unresolved"]
    # Old G34 source points must not silently return to the lower AA guard.
    regressed = copy.deepcopy(replayed)
    key = "CTT-LL-G34-G05-S000"
    original = next(c for c in before["contacts"] if c["id"] == key)
    next(c for c in regressed if c["id"] == key)["source_evidence"] = original["source_evidence"]
    failure = audit_joint(regressed, after["materials"], after["manifest"]["budget"], replayed)
    assert failure["geometry_status"] == "PASS"
    assert failure["status"] == failure["source_gate"]["status"] == "FAIL"
    assert failure["source_gate"]["new_conflicts"]


def test_human_s3_adjudication_retires_false_diffusion_and_preserves_s1_s2():
    from silicon_eye.ct_joint_reconstruction import audit_contacts
    from silicon_eye.ct_transfer import apply_reviewed_record_changes, audit_terminal_access
    from silicon_eye.joint_layers import reviewed_contact_errors

    before = load_snapshot(ROOT, ROOT / "configs/joint-work-layer-v2.json")
    after = load_snapshot(ROOT, ROOT / "configs/joint-work-layer-v3.json")
    base = ROOT / "benchmarks/ct-source-ownership-reviewed-v2"
    spec = json.loads((base / "spec-v1.json").read_text())
    old_id = after["manifest"]["retired_contact_ids"][0]
    new_id = "CT-G66-P03-P04-SHARED-TOP-01"
    bus = "G66-P03-P04-TOP-BUS"
    purple_id = "CTSD-CTT-RECOVER-AA2-LEFT-GUARD-NETWORK-LOWER-LEFT-CELLS-ROW4-AA3-0-SD01-S000"
    replay = apply_reviewed_record_changes(
        before["contacts"], spec["contact_changes"], [old_id, new_id]
    )
    assert replay == after["contacts"]
    assert len(replay) == 10287
    assert all(c["id"] != old_id for c in replay)
    blue = next(c for c in replay if c["id"] == new_id)
    old_blue = next(c for c in before["contacts"] if c["id"] == old_id)
    assert blue["source_evidence"] == old_blue["source_evidence"]
    assert blue["landing_material"] == "POLY" and blue["POLY_target"] == bus
    assert "AA_target" not in blue
    assert next(c for c in replay if c["id"] == purple_id) == next(
        c for c in before["contacts"] if c["id"] == purple_id
    )
    old_by_id = {c["id"]: c for c in before["contacts"]}
    assert sum(c == old_by_id.get(c["id"]) for c in replay) == 10286
    assert after["materials"]["AA_objects"] == before["materials"]["AA_objects"]
    assert after["materials"]["objects"][:-1] == before["materials"]["objects"]
    assert len(after["values"]["unknown"]["unknown_scopes"]) == 6
    assert (
        after["values"]["use_contract"]["restrictions"][:-1]
        == before["values"]["use_contract"]["restrictions"]
    )
    assert not reviewed_contact_errors(replay, after["materials"])
    access = audit_terminal_access(replay, after["materials"])
    for key in ["G66-P03", "G66-P04"]:
        assert (
            new_id
            in next(r for r in access["POLY_materials"] if r["material_id"] == key)["contact_ids"]
        )
    # Merely keeping cuts geometrically valid cannot override the human material decision.
    wrong = [c for c in replay if c["id"] != new_id] + [old_blue]
    assert (
        audit_contacts(wrong, after["materials"], after["manifest"]["budget"])["status"] == "PASS"
    )
    rejected = audit_joint(wrong, after["materials"], after["manifest"]["budget"], replay)
    assert rejected["status"] == "FAIL" and rejected["reviewed_identity_status"] == "FAIL"
    assert any(
        e["reason"] == "rejected_contact_identity_resurrected"
        for e in rejected["reviewed_contact_constraint_errors"]
    )
    disconnected = copy.deepcopy(after["materials"])
    next(p for p in disconnected["objects"] if p["id"] == bus)["member_POLY_ids"] = ["G66-P04"]
    assert any(
        e["reason"] == "reviewed_shared_POLY_members_changed"
        for e in reviewed_contact_errors(replay, disconnected)
    )
