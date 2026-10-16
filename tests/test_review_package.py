"""Behavior checks for source-bound unified export and conservative acceptance."""

import hashlib
import json
import shutil

import numpy as np
import pytest
from PIL import Image

from silicon_eye.review_package import run_package


def write(path, value):
    path.write_text(json.dumps(value))


def ref(root, name):
    return dict(path=name, sha256=hashlib.sha256((root / name).read_bytes()).hexdigest())


@pytest.fixture
def pack(tmp_path):
    root = tmp_path / "sources"
    root.mkdir()
    target = np.zeros((40, 40, 3), np.uint8)
    target[9, 8] = [12, 220, 31]
    reference = np.zeros_like(target)
    reference[12, 10] = target[9, 8]
    Image.fromarray(reference).save(root / "ref.png")
    Image.fromarray(target).save(root / "target.png")
    human = dict(actor="human", statement="reviewed", sources={})
    write(root / "human.json", human)
    case = dict(
        schema_version=1, document_kind="block_case", case_id="example", revision="one",
        source_base="repository_root",
        sources={"photo": ref(root, "ref.png"), "other": ref(root, "target.png"),
                 "human": ref(root, "human.json")},
        frames=[dict(id=id, source_ref=src, unit="px", coordinates="xy_half_open",
                     size_wh=[40, 40]) for id, src in [("ref", "photo"), ("target", "other")]],
        scopes=[dict(id="electrical", domain="electrical_case", extent="one MOS")],
        entities=[dict(id="Q", kind="device", class_label="MOS")]
                 + [dict(id="Q."+r, kind="terminal", device_id="Q", role=r)
                    for r in ["G", "A", "B", "Bulk"]],
        claims=[dict(id="exists", predicate="device_exists", subject_ids=["Q"],
                     scope_id="electrical", value=True, intent="proposal", producer="AI",
                     evidence_refs=["photo"])],
        review_events=[dict(id="e", claim_id="exists", verdict="confirm", actor="human",
                            source_refs=["human"], source_statement="reviewed")],
        review_inventory=dict(source_refs=["human"], event_ids=["e"],
                              registration_policy="explicit"),
        export_request=dict(mode="current", rendering="from_resolved_state_only",
                            unknown_electrical_relations="preserve",
                            network_labels_are="presentation_only_not_entity_identity"),
    )
    write(root / "case.json", case)
    h = [[1, 0, 2], [0, 1, 3], [0, 0, 1]]
    write(root / "frozen.json", dict(matrix=h))
    write(root / "gate.json", dict(
        case_id="example", sources=dict(frozen_transform=ref(root, "frozen.json")),
    ))
    write(root / "approval.json", dict(
        **dict(human, sources=dict(review_gate=ref(root, "gate.json"))),
        decisions=dict(macro="accepted"),
    ))
    profile = dict(
        decision_source=ref(root, "approval.json"), acceptance=dict(macro_overlay=True),
        frozen_transform_source=ref(root, "frozen.json"), matrix=h,
        mapping_direction="target_native_to_reference_native",
        reference=ref(root, "ref.png"), target=ref(root, "target.png"),
        reference_native_to_output_crop=np.eye(3).tolist(), output_crop_size_wh=[40, 40],
        reviewed_reference_frame_polygons_xy=[[[6, 6], [30, 6], [30, 30], [6, 30]]],
    )
    write(root / "profile.json", profile)
    write(root / "material-human.json", dict(**human, decisions=[dict(
        entity_id="support", material="poly", material_identity="human_confirmed",
        coarse_location="human_confirmed",
    )]))
    material = dict(
        case_id="example", review_source=ref(root, "material-human.json"),
        sources=dict(photo=ref(root, "ref.png")),
        crop_windows_native_xywh=dict(poly=[0, 0, 40, 40]),
        regions=[dict(id="support", frame="ref", material="poly", native_source="ref.png",
                      core_polygon_xy=[[9, 9], [11, 9], [11, 13], [9, 13]],
                      envelope_polygon_xy=[[7, 7], [14, 7], [14, 15], [7, 15]])],
        unknowns=["W/L unknown"],
    )
    write(root / "candidate.json", material)
    human_material = json.loads((root / "material-human.json").read_text())
    human_material["sources"]["candidate_spec"] = ref(root, "candidate.json")
    write(root / "material-human.json", human_material)
    material["review_source"] = ref(root, "material-human.json")
    write(root / "material.json", material)
    request = dict(
        schema_version=1, document_kind="block_review_package", case=ref(root, "case.json"),
        registrations=[dict(profile=ref(root, "profile.json"), approval=dict(
            record=ref(root, "approval.json"), pointer="/decisions/macro", value="accepted"),
            frozen_matrix_pointer="/matrix")], materials=[ref(root, "material.json")],
    )
    return root, request, tmp_path / "request.json", tmp_path / "out"


def run(pack):
    root, request, path, out = pack
    write(path, request)
    return run_package(path, out, root)


def change(pack, name, update):
    root, request, _, _ = pack
    doc = json.loads((root / name).read_text())
    update(doc)
    write(root / name, doc)
    if name == "profile.json":
        request["registrations"][0]["profile"] = ref(root, name)
    elif name == "material.json":
        request["materials"][0] = ref(root, name)
    elif name == "case.json":
        request["case"] = ref(root, name)


def test_known_forward_transform_and_scoped_outputs_do_not_promote_truth(pack):
    state = run(pack)
    out = pack[3]
    aligned = np.array(Image.open(out / "registration-001-aligned.png"))
    assert aligned[12, 10].tolist() == [12, 220, 31]
    assert aligned[9, 8].tolist() == [0, 0, 0]
    scope = np.array(Image.open(out / "registration-001-reviewed-scope.png"))
    assert scope[10, 10] == 255 and scope[0, 0] == 0
    assert state["registrations"][0]["acceptance"]["macro_overlay"] is True
    assert state["materials"][0]["identity_status"] == "human_confirmed"
    assert state["materials"][0]["geometry_status"] == "candidate_not_pixel_truth"
    assert state["precise_registration_accepted"] is False
    assert state["electrical_acceptance"]["simulation_ready"] is False
    assert Image.open(out / "registration-001-overlay.png").info["bundle_id"] == state["bundle_id"]
    block = json.loads((out / "circuit/resolved-state.json").read_text())
    assert block["matrix"]["values"][0][1] == "?"
    assert block["measurements"] == []


@pytest.mark.parametrize("fault", ["hash", "actor", "approval", "matrix", "direction",
                                   "frame", "polygon", "core", "case", "crop"])
def test_invalid_bindings_or_geometry_fail_before_normal_output(pack, fault):
    root, request, _, out = pack
    if fault == "hash":
        (root / "target.png").write_bytes(b"changed")
    elif fault in {"actor", "approval"}:
        doc = json.loads((root / "approval.json").read_text())
        doc["actor"] = "reasoning_model" if fault == "actor" else "human"
        doc["decisions"]["macro"] = "rejected" if fault == "approval" else "accepted"
        write(root / "approval.json", doc)
        request["registrations"][0]["approval"]["record"] = ref(root, "approval.json")
        change(pack, "profile.json", lambda d: d.update(decision_source=ref(root, "approval.json")))
    elif fault == "matrix":
        change(pack, "profile.json", lambda d: d["matrix"][0].__setitem__(2, 8))
    elif fault == "direction":
        change(pack, "profile.json", lambda d: d.update(mapping_direction="inverse"))
    elif fault == "frame":
        change(pack, "material.json", lambda d: d["regions"][0].update(frame="target"))
    elif fault == "polygon":
        change(pack, "material.json", lambda d:
               d["regions"][0]["core_polygon_xy"][0].__setitem__(0, -1))
    elif fault == "core":
        change(pack, "material.json", lambda d:
               d["regions"][0]["core_polygon_xy"][0].__setitem__(0, 3))
    elif fault == "case":
        change(pack, "material.json", lambda d: d.update(case_id="other"))
    elif fault == "crop":
        change(pack, "profile.json", lambda d: d.update(output_crop_size_wh=[80, 40]))
    with pytest.raises(ValueError):
        run(pack)
    assert not out.exists()


def test_source_only_replay_has_same_bundle_and_output_hashes(pack, tmp_path):
    first = run(pack)
    manifest = json.loads((pack[3] / "manifest.json").read_text())
    root = tmp_path / "isolated"
    root.mkdir()
    for path in manifest["inputs"]:
        shutil.copy2(pack[0] / path, root / path)
    second = run_package(pack[2], tmp_path / "second", root)
    assert second["bundle_id"] == first["bundle_id"]
    replay = json.loads((tmp_path / "second/manifest.json").read_text())
    assert replay["outputs"] == manifest["outputs"]


def test_existing_output_and_render_failure_preserve_user_data(pack, monkeypatch):
    import silicon_eye.review_package as module

    out = pack[3]
    out.mkdir()
    (out / "keep.txt").write_text("keep")
    with pytest.raises(ValueError, match="already exists"):
        run(pack)
    assert (out / "keep.txt").read_text() == "keep"
    shutil.rmtree(out)

    def fail(*args):
        raise ValueError("render failure")

    monkeypatch.setattr(module, "render_assets", fail)
    with pytest.raises(ValueError, match="render failure"):
        run(pack)
    assert not out.exists()
    assert not list(out.parent.glob(".review-package-*"))


def test_conflict_produces_only_diagnostic_package(pack):
    def contradictory(doc):
        claim = dict(doc["claims"][0], id="absent", value=False)
        event = dict(doc["review_events"][0], id="other", claim_id="absent")
        doc["claims"].append(claim)
        doc["review_events"].append(event)
        doc["review_inventory"]["event_ids"].append("other")

    change(pack, "case.json", contradictory)
    result = run(pack)
    assert result["status"] == "conflict"
    assert (pack[3] / "bundle-state.json").is_file()
    assert not list(pack[3].rglob("*.png"))
    assert not list(pack[3].rglob("*.csv"))


def test_unreviewed_material_stays_candidate_without_changing_circuit(pack):
    def pending(doc):
        doc.pop("review_source")
        doc.update(actor="reasoning_model", status="candidate")

    change(pack, "material.json", pending)
    state = run(pack)
    assert state["materials"][0]["identity_status"] == "candidate"
    assert state["materials"][0]["geometry_status"] == "candidate_not_pixel_truth"
    assert "候选待复核" in (pack[3] / "report.md").read_text()


def test_missing_review_never_silently_falls_back_to_candidate(pack):
    change(pack, "material.json", lambda d: d.update(
        review_source=dict(path="absent.json", sha256="0" * 64),
        actor="reasoning_model", status="candidate",
    ))
    with pytest.raises(ValueError):
        run(pack)
    assert not pack[3].exists()


def test_source_path_cannot_escape_root(pack, tmp_path):
    external = tmp_path / "outside.json"
    write(external, {})
    pack[1]["materials"] = [dict(
        path="../outside.json", sha256=hashlib.sha256(external.read_bytes()).hexdigest(),
    )]
    with pytest.raises(ValueError, match="outside-root"):
        run(pack)
    assert not pack[3].exists()
