"""Fanout replay must preserve evidence, distinct conductors and scoped exclusions."""

import copy
import json
import tempfile
from pathlib import Path
from xml.etree import ElementTree

import numpy as np
import pytest
from PIL import Image

from silicon_eye.geometry_reconstruction import digest
from silicon_eye.metal_fanout import deliver, fanout_inventory, validate

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "benchmarks/metal-fanout-validation-v1/request-v1.json"


@pytest.fixture(scope="module")
def spec():
    return json.loads(REQUEST.read_text())


@pytest.fixture(scope="module")
def validated(spec):
    return validate(ROOT, spec)


def test_two_confirmed_lower_segments_and_overlap_is_not_a_third_edge(validated):
    model, report, parent = validated
    assert report["distinct_lower_metal_count"] == 2
    assert report["reviewed_attachment_count"] == 2
    assert report["via_support_group_count"] == 2 and report["physical_cut_count"] is None
    excluded = report["excluded_attachments"][0]
    assert excluded["projected_overlap"]
    assert excluded["direct_attachment"] == "human_excluded_in_reviewed_span"
    assert excluded["global_same_net_status"] == "unknown"
    assert model["net_edges"] == [] and not report["complete_network"]
    assert not report["fresh_blind_recognition"] and report["new_physical_connections"] == 0
    assert model["source_to_design_transform"] is None and model["common_canvas_placement"] is None
    baseline = json.loads((ROOT / "docs/assets/conductive-stack-v2/model.json").read_text())
    assert parent["conductors"] == baseline
    assert report["parent_conductive_objects_preserved"] == 33
    assert model["coordinate_space"] == "local_relative_design_px"
    assert all(
        o["source_frame"] == "m2" and o["physical_cut_count"] is None
        for o in model["objects_by_layer"]["V2"]
    )


def test_several_via_groups_to_same_lower_segment_are_not_extra_branches():
    inventory = fanout_inventory(
        [
            dict(lower_metal_id="A", via_group_id="VA1"),
            dict(lower_metal_id="A", via_group_id="VA2"),
            dict(lower_metal_id="C", via_group_id="VC"),
            dict(lower_metal_id="A", via_group_id="VA1"),
        ]
    )
    assert inventory == [
        dict(lower_metal_id="A", via_group_ids=["VA1", "VA2"]),
        dict(lower_metal_id="C", via_group_ids=["VC"]),
    ]


@pytest.mark.parametrize(
    "change,reason",
    [
        ("source_frame", "source/owner mismatch"),
        ("source_xy", "source/owner mismatch"),
        ("support_outside", "double metal enclosure"),
        ("duplicate_via", "duplicate via ID"),
        ("same_layer_join", "same-layer isolation"),
        ("promote_context", "Context cannot silently join"),
        ("bad_span_review", "Missing scoped middle-span"),
        ("bad_exclusion", "Excluded attachment contradicts"),
        ("diagonal", "orthogonal"),
    ],
)
def test_quality_gates_reject_regression(spec, change, reason):
    request = copy.deepcopy(spec)
    if change == "source_frame":
        request["branches"][0]["source_frame"] = "m1"
    elif change == "source_xy":
        request["branches"][0]["source_xy"][0] += 40
    elif change == "support_outside":
        request["branches"][0]["design_support_bounds"][1] -= 20
        request["branches"][0]["design_support_bounds"][3] -= 20
    elif change == "duplicate_via":
        request["branches"].append(copy.deepcopy(request["branches"][0]))
    elif change == "same_layer_join":
        request["features_by_layer"]["M2"][2]["design_path"] = [[150, 280], [150, 530]]
    elif change == "promote_context":
        request["features_by_layer"]["M2"][2]["role"] = "reviewed_chain"
    elif change == "bad_span_review":
        request["interior_sweep"]["review_binding"]["pointer"] = (
            "/decisions/B_global_same_net_status"
        )
    elif change == "bad_exclusion":
        request["excluded_attachments"][0]["lower_metal_id"] = "R2_M2_gate_segment_01"
    else:
        request["features_by_layer"]["M3"][0]["design_path"][1][1] += 3
    with pytest.raises(ValueError, match=reason):
        validate(ROOT, request)


def test_delivered_source_crops_are_native_and_hash_locks_replay(spec):
    before = digest(ROOT / "configs/joint-work-layer-v5.json")
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temp:
        out = Path(temp) / "delivery"
        report = deliver(ROOT, REQUEST, out)
        assert report["status"] == "KNOWN_REVIEWED_FANOUT_REPLAY_PASS"
        for frame in ("m2", "m3"):
            with Image.open(ROOT / f"data/test_chip/tile_full/{frame}.jpg") as raw:
                for mode in ("wide", "detail"):
                    expected = raw.crop(spec["source_windows"][frame][mode]).convert("RGB")
                    if mode == "detail":
                        expected = expected.resize((expected.width * 4, expected.height * 4))
                    with Image.open(out / f"{frame}-{mode}-raw.png") as crop:
                        assert np.array_equal(np.asarray(crop), np.asarray(expected))
        ElementTree.parse(out / "local-design.svg")
        page = (out / "index.html").read_text()
        assert 'data-toggle="V2"' in page and 'data-context="true"' in page
        assert "已知案例" in page and "没有放入共同" in page
        manifest = json.loads((out / "manifest.json").read_text())
        assert all(digest(out / name) == sha for name, sha in manifest["artifacts"].items())
        with pytest.raises(ValueError, match="Output must be new"):
            deliver(ROOT, REQUEST, out)
    assert digest(ROOT / "configs/joint-work-layer-v5.json") == before
