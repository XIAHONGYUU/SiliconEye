"""New source-approved interfaces cannot alter old geometry or acquire count approval."""

import copy
import json
import tempfile
from pathlib import Path

import pytest

from silicon_eye.conductive_workflow import prepare, run
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/n1-v2-local-reconstruction-v1"


def read(path):
    return json.loads(path.read_text())


def ref(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


def test_n1_keeps_carrier_approval_separate_from_candidate_count_and_geometry():
    model, report, sample, *_ = prepare(ROOT, read(BASE / "request.json"))
    parent = read(ROOT / "docs/assets/n1-v2-local-reconstruction-v1/metal-revised/model.json")
    for layer in ("M1", "M2", "M3"):
        assert model["objects_by_layer"][layer] == parent["objects_by_layer"][layer]
    assert model["objects_by_layer"]["V2"][:-1] == parent["objects_by_layer"]["V2"]
    assert model["candidate_interfaces"][:-1] == parent["candidate_interfaces"]
    assert model["reviewed_local_connections"][:-1] == parent["reviewed_local_connections"]
    new = model["reviewed_local_connections"][-1]
    assert new["id"] == "N1-V2" and new["upper_metal_id"] == "C-M3-L01"
    assert new["connection_confirmed"] is True and new["physical_cut_count"] is None
    assert report["added_interface_ids"] == ["N1-V2"]
    assert report["changed_object_ids"] == []
    quality = next(r for r in report["quality"]["interface_geometry"] if r["id"] == "N1-V2")
    assert quality["design_cut_count"] == 2 and quality["human_cut_count"] is None
    assert quality["full_group_design_enclosure"] == "CHECKED"
    assert quality["source_array_geometry"] == "NOT_QUALIFIED"
    assert not model["net_edges"] and not model["geometry_adopted"]
    assert not model["complete_network"] and sample["source_to_design_transform"] is None


def test_local_head_alignment_changes_only_n1_and_preserves_native_anchor():
    _, report, sample, *_ = prepare(ROOT, read(BASE / "metal-request.json"))
    previous = read(ROOT / "benchmarks/conductive-corridor-batch-review-v1/observations.json")
    before = {f["id"]: f for group in previous["features_by_layer"].values() for f in group}
    after = {f["id"]: f for group in sample["features_by_layer"].values() for f in group}
    assert report["changed_object_ids"] == ["RT-M2-NARROW"]
    assert sorted(k for k in before if before[k] != after[k]) == ["RT-M2-NARROW"]
    assert before["RT-M2-NARROW"]["native_path"] == after["RT-M2-NARROW"]["native_path"]
    assert after["RT-M2-NARROW"]["design_path"] == [[565, 682], [590, 682], [590, 1115]]


@pytest.mark.parametrize(
    "mutation,message",
    [
        ("undeclared", "silently add or retire"),
        ("old_role", "preserve every existing record"),
        ("wrong_carrier_review", "Review carrier contradicts candidate"),
        ("invent_count_approval", "exceeds the submitted source scope"),
        ("geometry_in_verdict", "Review exceeds interface scope"),
        ("no_parent", "requires a parent"),
        ("missing_array_observation", "does not bind parent/IDs"),
        ("unfixed_head", "Via enclosure/spacing gate failed"),
        ("source_window_omits_n1", "Source review omits the observed via group"),
    ],
)
def test_extension_rejects_scope_and_enclosure_regressions(mutation, message):
    request = copy.deepcopy(read(BASE / "request.json"))
    sample = read(ROOT / request["sample"]["path"])
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temporary:
        folder = Path(temporary)
        if mutation == "undeclared":
            request.pop("added_interface_ids")
            request.pop("interface_extension_evidence")
        elif mutation == "old_role":
            sample["features_by_layer"]["M2"][0]["role"] = "unscoped_changed_role"
        elif mutation in ("wrong_carrier_review", "invent_count_approval", "geometry_in_verdict"):
            review = read(ROOT / request["reviews"][0]["path"])
            if mutation == "wrong_carrier_review":
                review["decisions"]["upper_metal_id"] = "RT-M3-THIN1"
            elif mutation == "invent_count_approval":
                review["observed_cut_count"] = 2
            else:
                review["decisions"]["design_bounds"] = [565, 679, 589, 685]
            path = folder / "review.json"
            path.write_text(json.dumps(review))
            request["reviews"] = [ref(path)]
        elif mutation == "no_parent":
            request.pop("parent")
        elif mutation == "missing_array_observation":
            evidence = read(ROOT / request["interface_extension_evidence"]["path"])
            evidence["interface_observations"] = {}
            path = folder / "extension.json"
            path.write_text(json.dumps(evidence))
            request["interface_extension_evidence"] = ref(path)
        elif mutation == "unfixed_head":
            feature = next(f for f in sample["features_by_layer"]["M2"]
                           if f["id"] == "RT-M2-NARROW")
            feature["design_path"] = [[565, 675], [590, 675], [590, 1115]]
        else:
            sample["source_panels"]["source_windows"]["m2"] = dict(
                wide=[2940, 1730, 3450, 3000], detail=[3020, 1820, 3420, 2100])
        path = folder / "sample.json"
        path.write_text(json.dumps(sample))
        request["sample"] = ref(path)
        with pytest.raises(ValueError, match=message):
            prepare(ROOT, request)


def test_extension_resumes_exactly_and_hard_failure_only_leaves_diagnostic():
    before = read(ROOT / "docs/assets/n1-v2-local-reconstruction-v1/work/model.json")
    after, report, *_ = prepare(ROOT, read(BASE / "next-request.json"))
    assert after == before and report["changed_object_ids"] == []
    request = read(BASE / "request.json")
    request.pop("added_interface_ids")
    request.pop("interface_extension_evidence")
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temporary:
        folder = Path(temporary)
        path = folder / "bad-request.json"
        path.write_text(json.dumps(request))
        with pytest.raises(ValueError, match="silently add or retire"):
            run(ROOT, path, folder / "rejected")
        assert [p.name for p in (folder / "rejected").iterdir()] == ["diagnostic.json"]
