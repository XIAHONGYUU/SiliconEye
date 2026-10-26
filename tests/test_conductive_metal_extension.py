"""Explicit inventory-backed additions preserve all reviewed geometry and interfaces."""

import copy
import json
import tempfile
from pathlib import Path

import pytest

from silicon_eye.conductive_workflow import prepare, run
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/conductive-corridor-geometry-v1"


def read(path):
    return json.loads(path.read_text())


def ref(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


def test_additions_preserve_all_old_objects_via_centers_and_human_scope():
    model, report, sample, *_ = prepare(ROOT, read(BASE / "request.json"))
    old = read(ROOT / "docs/assets/metal-representative-transfer-reviewed-v2/reviewed/model.json")
    index = {o["id"]: o for objects in model["objects_by_layer"].values() for o in objects}
    assert all(index[o["id"]] == o for objects in old["objects_by_layer"].values() for o in objects)
    assert model["reviewed_local_connections"] == old["reviewed_local_connections"]
    assert model["candidate_interfaces"] == old["candidate_interfaces"]
    assert report["object_counts"]["M2"] == 8 and report["object_counts"]["M3"] == 22
    assert len(report["added_metal_ids"]) == 22 and report["changed_object_ids"] == []
    mapping = report["quality"]["visible_inventory_geometry"]
    assert mapping["mapped_geometry_count"] == 30 and mapping["unmapped_observation_ids"] == []
    assert mapping["actual_photo_coverage_fraction"] is None
    assert mapping["unresolved_observation_ids"] == ["C-U1", "C-U2", "C-U3", "C-U4", "C-U5"]
    assert not mapping["complete_source_extent_geometry"]
    assert all(r["human_cut_count"] is None for r in report["quality"]["interface_geometry"])
    assert len(sample["interfaces"]) == 4 and not model["pending_interface_ids"]
    assert (
        not model["net_edges"] and not model["geometry_adopted"] and not model["complete_network"]
    )


@pytest.mark.parametrize(
    "mutation, message",
    [
        ("undeclared_add", "silently add or retire"),
        ("old_width", "preserve every existing"),
        ("source_shift", "moved away from inventory"),
        ("missing_mapping", "mapping incomplete"),
        ("overlap", "Metal geometry gate failed"),
        ("reverse_row_order", "Additional source order gate failed"),
        ("bad_proposal", "evidence does not bind"),
        ("no_parent", "requires a parent"),
    ],
)
def test_extension_rejects_unscoped_changes_or_quality_regressions(mutation, message):
    request = copy.deepcopy(read(BASE / "request.json"))
    sample = read(ROOT / request["sample"]["path"])
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temporary:
        folder = Path(temporary)
        if mutation == "undeclared_add":
            request["added_metal_ids"].pop()
        elif mutation == "old_width":
            sample["features_by_layer"]["M2"][0]["design_width"] = 24
        elif mutation == "source_shift":
            feature = next(f for f in sample["features_by_layer"]["M2"] if f["id"] == "C-M2-08")
            feature["native_path"] = [[x + 1, y] for x, y in feature["native_path"]]
        elif mutation == "missing_mapping":
            sample["inventory_geometry_mapping"].pop()
        elif mutation in ("overlap", "reverse_row_order"):
            features = {f["id"]: f for f in sample["features_by_layer"]["M3"]}
            if mutation == "overlap":
                features["C-M3-T01"]["design_path"] = features["C-M3-T02"]["design_path"]
            else:
                a, b = features["C-M3-T01"], features["C-M3-T02"]
                a["design_path"], b["design_path"] = b["design_path"], a["design_path"]
        elif mutation == "bad_proposal":
            proposal = read(ROOT / request["extension_evidence"]["path"])
            proposal["added_metal_ids"] = []
            path = folder / "proposal.json"
            path.write_text(json.dumps(proposal))
            request["extension_evidence"] = ref(path)
        else:
            request.pop("parent")
        path = folder / "sample.json"
        path.write_text(json.dumps(sample))
        request["sample"] = ref(path)
        with pytest.raises(ValueError, match=message):
            prepare(ROOT, request)


def test_extended_model_can_resume_exactly_without_declaring_additions_again():
    request = read(BASE / "request.json")
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temporary:
        folder = Path(temporary)
        output = folder / "extended"
        before, _ = run(ROOT, BASE / "request.json", output)
        request["parent"] = ref(output / "manifest.json")
        request.pop("added_metal_ids")
        request.pop("extension_evidence")
        after, report, *_ = prepare(ROOT, request)
        assert after == before
        assert report["added_metal_ids"] == []
        assert report["changed_object_ids"] == []


def test_source_length_revision_only_changes_the_two_new_boundary_fragments():
    model, report, sample, *_ = prepare(ROOT, read(BASE / "request-v2.json"))
    initial = read(ROOT / "docs/assets/conductive-corridor-geometry-v1/work/model.json")
    before = {o["id"]: o for objects in initial["objects_by_layer"].values() for o in objects}
    after = {o["id"]: o for objects in model["objects_by_layer"].values() for o in objects}
    assert sorted(k for k in before if before[k] != after[k]) == ["C-M3-E1", "C-M3-E2"]
    assert report["changed_object_ids"] == ["C-M3-E1", "C-M3-E2"]
    assert model["reviewed_local_connections"] == initial["reviewed_local_connections"]
    features = {f["id"]: f for f in sample["features_by_layer"]["M3"]}
    for key in ("C-M3-E1", "C-M3-E2"):
        feature = features[key]
        native_length = feature["native_path"][-1][0] - feature["native_path"][0][0]
        design_length = feature["design_path"][-1][0] - feature["design_path"][0][0]
        assert design_length == pytest.approx(native_length * 610 / 730, rel=0.02)
