"""Scope extensions keep native anchors, full via arrays and human decisions separate."""

import json
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from silicon_eye.conductive_workflow import prepare, run
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/conductive-corridor-batch-review-v1"


def read(path):
    return json.loads(path.read_text())


def ref(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


def test_extent_candidates_preserve_anchors_via_sites_and_scoped_reviews():
    model, report, sample, *_ = prepare(ROOT, read(BASE / "request.json"))
    old = read(ROOT / "docs/assets/conductive-corridor-geometry-v1/revised/model.json")
    old_objects = {o["id"]: o for rows in old["objects_by_layer"].values() for o in rows}
    objects = {o["id"]: o for rows in model["objects_by_layer"].values() for o in rows}
    assert set(objects) == set(old_objects)
    for key, obj in objects.items():
        if "native_path" in obj:
            assert obj["native_path"] == old_objects[key]["native_path"]
    assert model["objects_by_layer"]["V2"] == old["objects_by_layer"]["V2"]
    assert model["reviewed_local_connections"] == old["reviewed_local_connections"]
    assert model["candidate_interfaces"] == old["candidate_interfaces"]
    assert model["source_extent_candidates"]["metal_count"] == 8
    assert model["source_extent_candidates"]["source_boundary_endpoints"] == 13
    assert not model["source_extent_candidates"]["geometry_human_approved"]
    assert not model["source_extent_candidates"]["precise_extent_geometry_qualified"]
    assert not model["geometry_adopted"] and not model["complete_network"]
    assert len(report["changed_object_ids"]) == 18
    for row in read(BASE / "source-extent-evidence.json")["metals"]:
        if row["preserve_old_footprint"]:
            a, b = (objects[row["metal_id"]], old_objects[row["metal_id"]])
            assert Polygon(a["geometry"]["outer_xy"]).covers(Polygon(b["geometry"]["outer_xy"]))
    f = {o["id"]: o for rows in sample["features_by_layer"].values() for o in rows}
    assert f["RT-M2-NARROW"]["design_path"][0][1] > 590 + 80 / 2
    assert f["C-M3-EDGE"]["design_path"][0][1] < f["RT-M2-R01"]["design_path"][-1][1]
    assert [f[f"C-M3-M{i:02}"]["design_path"][0][1] for i in range(1, 7)] == list(
        range(450, 526, 15)
    )


@pytest.mark.parametrize(
    "mutation, message",
    [
        ("native_anchor", "source/path/endpoint binding mismatch"),
        ("source_extent", "source/path/endpoint binding mismatch"),
        ("missing_metal", "omits or duplicates"),
        ("shrink", "removed or failed to extend"),
        ("false_approval", "must remain an AI candidate"),
        ("no_reposition_reason", "requires a separate source reason"),
    ],
)
def test_extent_gate_rejects_unbound_or_promoted_evidence(mutation, message):
    request = read(BASE / "request.json")
    sample = read(ROOT / request["sample"]["path"])
    evidence = read(ROOT / sample["source_extent_evidence"]["path"])
    f = sample["features_by_layer"]["M2"][0]
    if mutation == "native_anchor":
        f["native_path"][-1][1] += 1
    elif mutation == "source_extent":
        evidence["metals"][0]["visible_native_path"][-1][1] -= 1
    elif mutation == "missing_metal":
        evidence["metals"].pop()
    elif mutation == "shrink":
        f["design_path"][-1][1] = 1099
        evidence["metals"][0]["design_path"] = f["design_path"]
    elif mutation == "false_approval":
        evidence["geometry_human_approved"] = True
    else:
        evidence["metals"][2]["reposition_reason"] = ""
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temporary:
        folder = Path(temporary)
        ep = folder / "extents.json"
        ep.write_text(json.dumps(evidence))
        sample["source_extent_evidence"] = ref(ep)
        path = folder / "sample.json"
        path.write_text(json.dumps(sample))
        request["sample"] = ref(path)
        with pytest.raises(ValueError, match=message):
            prepare(ROOT, request)


def test_extent_metadata_replays_exactly_and_cannot_disappear():
    request = read(BASE / "request.json")
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temporary:
        output = Path(temporary) / "package"
        before, _ = run(ROOT, BASE / "request.json", output)
        request["parent"] = ref(output / "manifest.json")
        request["allowed_changed_ids"] = []
        request.pop("revision_evidence")
        after, *_ = prepare(ROOT, request)
        assert after == before
        sample = read(ROOT / request["sample"]["path"])
        sample.pop("source_extent_evidence")
        path = Path(temporary) / "without-extents.json"
        path.write_text(json.dumps(sample))
        request["sample"] = ref(path)
        with pytest.raises(ValueError, match="inventory/order binding"):
            prepare(ROOT, request)


def test_explicit_later_point_adjustment_can_rebind_extent_evidence():
    request = read(BASE / "request.json")
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temporary:
        folder = Path(temporary)
        output = folder / "package"
        before, _ = run(ROOT, BASE / "request.json", output)
        sample = read(ROOT / request["sample"]["path"])
        sample["features_by_layer"]["M2"][0]["design_path"][-1][1] = 1118
        extent = read(ROOT / sample["source_extent_evidence"]["path"])
        extent["basis_parent"] = ref(output / "manifest.json")
        extent["metals"][0]["design_path"] = sample["features_by_layer"]["M2"][0]["design_path"]
        ep = folder / "new-extent.json"
        ep.write_text(json.dumps(extent))
        sample["source_extent_evidence"] = ref(ep)
        sp = folder / "sample.json"
        sp.write_text(json.dumps(sample))
        proposal = folder / "proposal.json"
        proposal.write_text(
            json.dumps(
                dict(
                    actor="AI",
                    reason="Test a small endpoint adjustment",
                    sources=dict(extent=ref(ep)),
                )
            )
        )
        request.update(
            parent=ref(output / "manifest.json"),
            sample=ref(sp),
            allowed_changed_ids=["RT-M2-R01"],
            revision_evidence=ref(proposal),
        )
        after, report, *_ = prepare(ROOT, request)
        assert report["changed_object_ids"] == ["RT-M2-R01"]
        assert after["reviewed_local_connections"] == before["reviewed_local_connections"]
        assert after["objects_by_layer"]["V2"] == before["objects_by_layer"]["V2"]
