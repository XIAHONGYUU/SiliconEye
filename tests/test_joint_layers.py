"""Joint continuation must protect material relations, evidence and scoped history."""

import copy
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from silicon_eye.aa_completion import source_polygon
from silicon_eye.ct_joint_reconstruction import audit_contacts
from silicon_eye.joint_layers import (
    aa_view,
    audit_joint,
    load_snapshot,
    material_aliases,
    replace_layer,
    resolved_material,
    source_conflicts,
    write_snapshot,
)
from silicon_eye.poly_closeout import audit

ROOT = Path(__file__).resolve().parents[1]
BUDGET = dict(square_side=5, min_gap_px=3, enclosure_px=1, channel_clearance_px=1)


def rect(left, top, right, bottom):
    return [[left, top], [right, top], [right, bottom], [left, bottom]]


def cut(key, target, center, source):
    x, y = center
    return dict(
        id=key,
        family=key,
        column=0,
        row=0,
        AA_target=target,
        layout_outline=rect(x - 2.5, y - 2.5, x + 2.5, y + 2.5),
        source_frame="poly",
        source_evidence=dict(native_center=source, supported=True),
    )


def fixture():
    material = dict(
        objects=[
            dict(id="G", kind="MOS_gate_body", AA_target="A", layout_outline=rect(40, -10, 50, 110))
        ],
        AA_objects=[dict(id="A", outer_xyxy=[0, 0, 100, 100])],
        guard_AA_ids=[],
        canvas_wh=[150, 150],
        relative_budget=dict(gate_extension_px=8),
    )
    contacts = [cut("SD", "A", [20, 20], [20, 20])]
    return material, contacts


def test_joint_gate_rejects_truncated_gate_even_when_ct_still_passes():
    material, contacts = fixture()
    assert audit_joint(contacts, material, BUDGET)["status"] == "PASS"
    material["objects"][0]["layout_outline"] = rect(40, -10, 50, 60)
    assert audit_contacts(contacts, material, BUDGET)["status"] == "PASS"
    joint = audit_joint(contacts, material, BUDGET)
    assert joint["status"] == "FAIL"
    assert joint["POLY"]["errors"][0]["reason"] == "explicit_target_extension_missing"


def test_joint_gate_rejects_aa_collision_even_when_ct_still_passes():
    material = dict(
        objects=[],
        AA_objects=[
            dict(id="A", outer_xyxy=[0, 0, 40, 40]),
            dict(id="B", outer_xyxy=[50, 0, 90, 40]),
        ],
    )
    contacts = [cut("SD", "A", [12, 12], [12, 12])]
    assert audit_joint(contacts, material, BUDGET)["status"] == "PASS"
    material["AA_objects"][0]["outer_xyxy"][2] = 60
    assert audit_contacts(contacts, material, BUDGET)["status"] == "PASS"
    report = audit_joint(contacts, material, BUDGET)
    assert report["status"] == "FAIL"
    assert report["AA_overlap_conflicts"][0]["intersection_area"] == 400


def test_declared_bus_must_connect_each_member_and_does_not_excuse_other_overlap():
    material = dict(
        objects=[
            dict(id="G1", layout_outline=rect(10, 0, 20, 50)),
            dict(id="G2", layout_outline=rect(30, 0, 40, 50)),
            dict(
                id="B",
                kind="shared_gate_terminal_bus",
                member_POLY_ids=["G1", "G2"],
                layout_outline=rect(10, 40, 40, 55),
            ),
        ],
        AA_objects=[],
    )
    assert audit(material)["geometry_status"] == "PASS"
    material["objects"][1]["layout_outline"] = rect(30, 0, 40, 30)
    report = audit(material)
    assert report["geometry_status"] == "FAIL"
    assert report["errors"][0]["reason"] == "shared_POLY_member_disconnected"
    material["objects"][1]["layout_outline"] = rect(15, 0, 25, 50)
    assert ["G1", "G2"] in audit(material)["positive_area_overlap_pairs"]


def test_alias_resolution_is_copy_only_and_rejects_cycles_wrong_layers_and_resurrection():
    material, _ = fixture()
    material["AA_objects"][0]["material_aliases"] = ["OLD-A"]
    material["guard_AA_ids"] = ["OLD-A"]
    before = copy.deepcopy(material)
    assert resolved_material(material)["guard_AA_ids"] == ["A"]
    assert material == before
    material["local_material_revision"] = dict(alias_map={"X": "Y", "Y": "X"})
    with pytest.raises(ValueError, match="Cyclic"):
        material_aliases(material)
    material["local_material_revision"] = dict(alias_map={"A": "G"})
    with pytest.raises(ValueError, match="resurrected"):
        material_aliases(material)
    material.pop("local_material_revision")
    material["guard_AA_ids"] = ["G"]
    with pytest.raises(ValueError, match="wrong-layer"):
        resolved_material(material)


def test_sources_are_frame_scoped_order_independent_and_old_conflicts_stay_open():
    material = dict(
        objects=[],
        AA_objects=[
            dict(id="A", outer_xyxy=[0, 0, 40, 40]),
            dict(id="B", outer_xyxy=[50, 0, 90, 40]),
        ],
    )
    contacts = [cut("CA", "A", [20, 20], [20, 20]), cut("CB", "B", [70, 20], [21, 20])]
    assert len(source_conflicts(contacts)) == 1
    assert source_conflicts(contacts[::-1]) == source_conflicts(contacts)
    report = audit_joint(contacts, material, BUDGET, contacts)
    assert report["status"] == "REVIEW_REQUIRED"
    assert not report["automatic_network_export_allowed"]
    changed = copy.deepcopy(contacts)
    changed[1]["source_evidence"]["native_center"] = [22, 20]
    assert audit_joint(changed, material, BUDGET, contacts)["status"] == "FAIL"
    changed[1]["source_frame"] = "aa"
    assert not source_conflicts(changed)
    assert audit_joint(contacts, material, BUDGET, contacts[:1])["status"] == "FAIL"


@pytest.fixture(scope="module")
def real_snapshot():
    return load_snapshot(ROOT, ROOT / "configs/joint-work-layer-v1.json")


def test_current_snapshot_keeps_geometry_and_all_source_questions(real_snapshot):
    material, contacts = real_snapshot["materials"], real_snapshot["contacts"]
    before = copy.deepcopy(material)
    r = audit_joint(contacts, material, BUDGET, contacts)
    assert r["geometry_status"] == "PASS"
    assert r["status"] == "REVIEW_REQUIRED"
    assert len(r["source_gate"]["inherited_unresolved"]) == 16
    assert not r["source_gate"]["new_conflicts"]
    assert len(r["POLY"]["declared_connected_overlap_pairs"]) == 2
    assert not r["POLY"]["errors"]
    assert material == before
    assert len(real_snapshot["values"]["use_contract"]["restrictions"]) == 5


def test_aa_adapter_uses_latest_objects_and_complete_merged_observations(real_snapshot):
    view = aa_view(real_snapshot)
    assert view["objects"] == real_snapshot["materials"]["AA_objects"]
    assert len(view["objects"]) == 334
    obj = next(a for a in view["objects"] if a["id"] == "AA2-UPPER-INNER-B-AA-0")
    old = Polygon(obj["source_geometry"]["outer_xy"], obj["source_geometry"]["holes_xy"])
    assert source_polygon(obj, view).area > old.area
    assert len(view["source_footprints"]["AA-LEFT-STAIR-SHARED-56"]) == 2


def test_bounded_layer_revision_protects_companions_and_rejects_stale_scope(real_snapshot):
    records = copy.deepcopy(real_snapshot["materials"]["objects"])
    gate = next(o for o in records if o["id"] == "G26-P01")
    gate["layout_outline"][2][1] += 1
    gate["layout_outline"][3][1] += 1
    result = replace_layer(real_snapshot, "POLY", records, [gate["id"]])
    assert result["materials"]["AA_objects"] == real_snapshot["materials"]["AA_objects"]
    assert result["contacts"] == real_snapshot["contacts"]
    assert result["values"]["unknown"] == real_snapshot["values"]["unknown"]
    with pytest.raises(ValueError, match="outside scope"):
        replace_layer(real_snapshot, "POLY", records, [])
    gate["layout_outline"] = rect(904, 1542, 934, 1600)
    with pytest.raises(ValueError, match="Joint layer"):
        replace_layer(real_snapshot, "POLY", records, [gate["id"]])


def test_snapshot_roundtrip_and_tamper_detection(real_snapshot, tmp_path):
    # The output must be within its project root; use a copied mini-project of locked refs.
    root = tmp_path
    for ref in real_snapshot["manifest"]["inputs"].values():
        path = root / ref["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / ref["path"]).read_bytes())
    snapshot = copy.deepcopy(real_snapshot)
    snapshot["manifest"]["source_photos"] = {}
    path = write_snapshot(root, snapshot, root / "next")
    reloaded = load_snapshot(root, path)
    assert reloaded["materials"] == snapshot["materials"]
    assert reloaded["contacts"] == snapshot["contacts"]
    assert reloaded["values"]["use_contract"] == snapshot["values"]["use_contract"]
    assert reloaded["manifest"]["adoption_status"] == "candidate_not_new_human_approval"
    target = root / reloaded["manifest"]["inputs"]["materials"]["path"]
    target.write_text("{}")
    with pytest.raises(ValueError, match="Changed"):
        load_snapshot(root, path)


@pytest.mark.parametrize("failure", ["truncated_gate", "aa_overlap"])
def test_ct_revision_entry_blocks_material_regressions_before_writing(tmp_path, failure):
    import hashlib
    import json

    from PIL import Image

    from silicon_eye.ct_transfer import run_local_review_revision

    material, contacts = fixture()
    if failure == "truncated_gate":
        before = material["objects"][0]
        after = copy.deepcopy(before)
        after["layout_outline"] = rect(40, -10, 50, 60)
        changes = dict(objects=[dict(id="G", before=before, after=after)])
        authorized = ["G"]
    else:
        material["objects"] = []
        material["AA_objects"] = [
            dict(id="A", outer_xyxy=[0, 0, 40, 40]),
            dict(id="B", outer_xyxy=[50, 0, 90, 40]),
        ]
        before = material["AA_objects"][0]
        after = dict(id="A", outer_xyxy=[0, 0, 60, 40])
        changes = dict(AA_objects=[dict(id="A", before=before, after=after)])
        authorized = ["A"]
    values = dict(
        materials=material,
        contacts=dict(objects=contacts),
        human_review=dict(
            authorized_material_ids=authorized,
            authorized_contact_ids=[],
            authorized_new_contact_ids=[],
        ),
        new_contacts=dict(objects=[]),
        unknown_sites=dict(sites=[]),
        parent_spec=dict(budget=BUDGET),
    )
    inputs = {}
    for key, value in values.items():
        path = tmp_path / (key + ".json")
        path.write_text(json.dumps(value))
        inputs[key] = dict(path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    photo = tmp_path / "photo.png"
    Image.new("RGB", (150, 150)).save(photo)
    inputs["photo"] = dict(path=photo.name, sha256=hashlib.sha256(photo.read_bytes()).hexdigest())
    spec = dict(
        inputs=inputs, budget=BUDGET, material_changes=changes, contact_changes=[], cases=[]
    )
    with pytest.raises(ValueError, match="Joint layer continuation blocked"):
        run_local_review_revision(tmp_path, spec, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_retired_id_cannot_return_even_in_authorized_scope(real_snapshot):
    records = copy.deepcopy(real_snapshot["materials"]["objects"])
    records.append(dict(id="G06-P06", layout_outline=rect(0, 0, 1, 1)))
    with pytest.raises(ValueError, match="Retired"):
        replace_layer(real_snapshot, "POLY", records, ["G06-P06"])


def test_snapshot_writer_preflights_existing_files_before_any_write(tmp_path):
    material, contacts = fixture()
    snapshot = dict(
        materials=material,
        contacts=contacts,
        manifest=dict(id="fixture", budget=BUDGET, inputs={}),
        values=dict(contacts=dict(objects=contacts)),
    )
    output = tmp_path / "next"
    output.mkdir()
    existing = output / "joint-contacts.json"
    existing.write_text("preserve me")
    with pytest.raises(ValueError, match="already exists"):
        write_snapshot(tmp_path, snapshot, output)
    assert existing.read_text() == "preserve me"
    assert not (output / "joint-materials.json").exists()
