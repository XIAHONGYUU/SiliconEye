"""New-region transfer keeps whole arrays and rejects known interface mistakes."""

import copy
import json
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from silicon_eye.conductive_workflow import prepare
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/metal-representative-transfer-v1"


def read(path):
    return json.loads(path.read_text())


def test_new_region_uses_four_whole_arrays_without_inventing_approvals():
    model, report, sample, *_ = prepare(ROOT, read(BASE / "request-v2.json"))
    assert report["quality"]["execution_checks"] == "PASS"
    assert report["quality"]["source_path_shape"]["status"] == "PASS"
    assert len(model["pending_interface_ids"]) == 4
    assert model["reviewed_local_connections"] == [] and model["net_edges"] == []
    assert [len(o["candidate_cut_bounds"]) for o in model["objects_by_layer"]["V2"]] == [
        6, 6, 10, 10
    ]
    assert all(r["human_cut_count"] is None for r in report["quality"]["interface_geometry"])
    assert sample["via_budget"]["minimum_cut_gap_px"] == 3
    assert not model["geometry_adopted"] and not model["complete_network"]
    shapes = {o["id"]: Polygon(o["geometry"]["outer_xy"])
              for layer in ("M2", "M3") for o in model["objects_by_layer"][layer]}
    # An actual design crossing without an observed via must remain unconnected.
    assert shapes["RT-M2-NARROW"].intersects(shapes["RT-M3-MID"])
    assert not any(c["lower_metal_id"] == "RT-M2-NARROW" for c in sample["interfaces"])


@pytest.mark.parametrize("mutation", ["narrow_carrier", "reverse_bend", "missing_site"])
def test_transfer_gates_reject_misassigned_carrier_reversed_turn_and_partial_array(mutation):
    request = read(BASE / "request-v2.json")
    sample = copy.deepcopy(read(ROOT / request["sample"]["path"]))
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temporary:
        folder = Path(temporary)
        if mutation == "narrow_carrier":
            sample["interfaces"][0]["lower_metal_id"] = "RT-M2-NARROW"
            message = "Via enclosure/spacing gate failed"
        elif mutation == "reverse_bend":
            sample["features_by_layer"]["M2"][2]["design_path"][0][0] = 615
            message = "Source turn handedness mismatch"
        else:
            claim = sample["interfaces"][0]
            observation = read(ROOT / claim["array_source_evidence"]["path"])
            observation["sites"].pop()
            path = folder / "partial-array.json"
            path.write_text(json.dumps(observation))
            claim["array_source_evidence"] = dict(
                path=str(path.relative_to(ROOT)), sha256=digest(path)
            )
            message = "omits sites"
        path = folder / "sample.json"
        path.write_text(json.dumps(sample))
        request["sample"] = dict(path=str(path.relative_to(ROOT)), sha256=digest(path))
        with pytest.raises(ValueError, match=message):
            prepare(ROOT, request)
