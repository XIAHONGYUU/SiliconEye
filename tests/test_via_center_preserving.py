"""Size corrections retain every site and the existing physical-support gates."""

import copy
import json
from pathlib import Path

import pytest

from silicon_eye.conductive_snapshot import focus_metrics
from silicon_eye.conductive_workflow import prepare, preserve_via_centers

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/via-center-preserving-v1"


def read(path):
    return json.loads(path.read_text())


def test_size_revision_keeps_centers_counts_metals_and_approvals():
    model, report, sample, *_ = prepare(ROOT, read(BASE / "revision-request.json"))
    parent = read(ROOT / "docs/assets/conductive-work-baseline-v1/independent/model.json")
    for layer in ("M1", "M2", "M3", "V1"):
        assert model["objects_by_layer"][layer] == parent["objects_by_layer"][layer]
    assert model["reviewed_local_connections"] == parent["reviewed_local_connections"]
    via = model["objects_by_layer"]["V2"][0]
    assert len(via["candidate_cut_bounds"]) == 6
    assert all(c-a == d-b == 6 for a, b, c, d in via["candidate_cut_bounds"])
    assert report["changed_object_ids"] == ["IT1-V2-B"]
    assert report["quality"]["execution_checks"] == "PASS"
    assert report["audits"]["preserved_via_centers"]["IT1-V2-B"]["status"] == "PASS"
    assert sample["via_budget"] == read(ROOT / parent["sample"]["path"])["via_budget"]
    assert not model["geometry_adopted"] and not model["complete_network"]


@pytest.mark.parametrize("mutation", ["translate", "reorder", "drop"])
def test_size_gate_rejects_shifted_reordered_or_missing_sites(mutation):
    parent = read(ROOT / "docs/assets/conductive-work-baseline-v1/independent/model.json")
    model = copy.deepcopy(parent)
    cuts = model["objects_by_layer"]["V2"][0]["candidate_cut_bounds"]
    if mutation == "translate":
        cuts[0][0] += 1
        cuts[0][2] += 1
    elif mutation == "reorder":
        cuts.reverse()
    else:
        cuts.pop()
    with pytest.raises(ValueError, match="Via center preservation failed"):
        preserve_via_centers(parent, model, ["IT1-V2-B"])


def test_group_overlap_does_not_require_inflated_individual_cuts():
    model = read(ROOT / "docs/assets/conductive-work-baseline-v1/independent/model.json")
    # Interleaved sites have overlapping group footprints without overlapping cuts.
    model["objects_by_layer"]["V1"][0]["candidate_cut_bounds"] = [
        [0, 0, 6, 6], [20, 0, 26, 6]
    ]
    model["objects_by_layer"]["V2"][0]["candidate_cut_bounds"] = [[10, 0, 16, 6]]
    metrics = focus_metrics(model, dict(v1_id="IT1-V1-A", v2_id="IT1-V2-B"))
    assert metrics["V1_V2_overlap_area"] == 0
    assert metrics["V1_V2_group_overlap_area"] == 36
