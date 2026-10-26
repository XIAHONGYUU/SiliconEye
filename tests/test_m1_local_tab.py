"""A source-supported M1 tab holds the lower two vias without moving their sites."""

import copy
import json
from pathlib import Path

import pytest
from shapely.geometry import box

from silicon_eye.conductive_workflow import candidate_model, prepare
from silicon_eye.metal_reconstruction import feature_polygon, stroke

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "benchmarks/m1-local-tab-v1"


def read(path):
    return json.loads(path.read_text())


def test_m1_tab_covers_lower_two_holes_with_sites_and_connections_preserved():
    model, report, sample, *_ = prepare(ROOT, read(BASE / "revision-request.json"))
    old = read(ROOT / "docs/assets/via-center-preserving-v1/independent/model.json")
    for layer in ("V1", "V2", "M2", "M3"):
        assert model["objects_by_layer"][layer] == old["objects_by_layer"][layer]
    assert model["reviewed_local_connections"] == old["reviewed_local_connections"]
    before = read(ROOT / old["sample"]["path"])["features_by_layer"]["M1"][0]
    metal = sample["features_by_layer"]["M1"][0]
    assert metal["native_path"] == before["native_path"]
    assert metal["source_frame"] == before["source_frame"]
    body = stroke(metal["design_path"], metal["design_width"])
    polygon = feature_polygon(metal, sample["metal_budget"]["minimum_width_px"])
    assert polygon.bounds == feature_polygon(before).bounds
    cuts = [box(*bb) for bb in model["objects_by_layer"]["V1"][0]["candidate_cut_bounds"]]
    assert [body.covers(c) for c in cuts] == [True, True, True, True, False, False]
    assert all(polygon.covers(c.buffer(1, join_style="mitre")) for c in cuts)
    assert polygon.geom_type == "Polygon" and polygon.is_valid
    assert report["changed_object_ids"] == ["IT1-M1-RING"]
    assert report["quality"]["execution_checks"] == "PASS"


def test_missing_local_tab_fails_full_via_enclosure():
    sample = copy.deepcopy(read(BASE / "independent-observations.json"))
    sample["features_by_layer"]["M1"][0].pop("local_parts")
    with pytest.raises(ValueError, match="Via enclosure/spacing gate failed"):
        candidate_model(sample, read(ROOT / sample["snapshot"]["path"]))
