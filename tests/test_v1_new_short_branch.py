"""A new V1 source/carrying hypothesis stays pending and keeps unresolved count."""

import copy
import json
import tempfile
from pathlib import Path

import pytest

from silicon_eye.conductive_workflow import prepare
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/v1-new-short-branch-v1"


def read(path):
    return json.loads(path.read_text())


def test_new_interface_does_not_inherit_old_approval_or_claim_measured_array():
    model, report, sample, *_ = prepare(ROOT, read(BASE / "request.json"))
    assert report["quality"]["execution_checks"] == "PASS"
    assert report["quality"]["source_path_shape"]["status"] == "PASS"
    assert model["reviewed_local_connections"] == []
    assert model["pending_interface_ids"] == ["V1-S1-GROUP"]
    via = model["objects_by_layer"]["V1"][0]
    assert via["source_frame"] == "m1"
    assert via["physical_cut_count"] is None and "candidate_cut_bounds" not in via
    row = report["quality"]["interface_geometry"][0]
    assert row["human_cut_count"] is None
    assert row["full_group_design_enclosure"] == "NOT_EVALUATED"
    assert report["quality"]["proxy_interface_ids"] == ["V1-S1-GROUP"]
    assert not model["geometry_adopted"] and not model["net_edges"]
    assert sample["interfaces"][0]["upper_metal_id"] == "S1-M2-A"


@pytest.mark.parametrize("mutation", ["neighbor_carrier", "wrong_source", "reverse_turn"])
def test_new_v1_gates_reject_neighbor_m2_source_borrowing_and_mirrored_bend(mutation):
    request = read(BASE / "request.json")
    sample = copy.deepcopy(read(ROOT / request["sample"]["path"]))
    if mutation == "neighbor_carrier":
        sample["interfaces"][0]["upper_metal_id"] = "S1-M2-B"
        message = "Via enclosure/spacing gate failed"
    elif mutation == "wrong_source":
        sample["interfaces"][0]["source_frame"] = "m2"
        message = "Source identity/order gate failed"
    else:
        sample["features_by_layer"]["M2"][0]["design_path"][0][0] = 300
        message = "Source turn handedness mismatch"
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temporary:
        path = Path(temporary) / "sample.json"
        path.write_text(json.dumps(sample))
        request["sample"] = dict(path=str(path.relative_to(ROOT)), sha256=digest(path))
        with pytest.raises(ValueError, match=message):
            prepare(ROOT, request)
