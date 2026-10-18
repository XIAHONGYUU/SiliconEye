"""Full-frame spatial contracts, uncertainty and nested AA separation."""

import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from silicon_eye.full_frame_materials import associate_ct, native_valid, run, segment_aa

SETTINGS = json.loads(
    (Path(__file__).parents[1] / "benchmarks/full-frame-aa-ct-v1/spec-v1.json").read_text()
)["aa"]


def test_nested_ring_does_not_become_solid_or_join_inner_aa():
    raw = np.zeros((260, 320, 3), np.uint8)
    cv2.rectangle(raw, (25, 25), (285, 235), (240, 240, 240), 6)
    cv2.rectangle(raw, (90, 90), (220, 170), (240, 240, 240), 6)
    result = segment_aa(raw, np.ones(raw.shape[:2], bool), SETTINGS)
    assert result["mask"][120, 140]  # Interior of independent inner AA.
    assert not result["mask"][60, 60]  # Field between inner AA and outer ring.
    _, labels = cv2.connectedComponents(result["mask"].astype(np.uint8))
    assert labels[25, 100] > 0
    assert labels[25, 100] != labels[120, 140]
    assert result["inferred"][120, 140]
    assert not result["observed"][120, 140]


def test_validity_exclusion_survives_aa_completion_and_source_is_immutable():
    raw = np.zeros((150, 220, 3), np.uint8)
    cv2.rectangle(raw, (30, 30), (180, 120), (240, 240, 240), 7)
    original = raw.copy()
    valid = native_valid(raw.shape[:2], [[95, 65, 105, 75]])
    result = segment_aa(raw, valid, SETTINGS)
    assert result["mask"][60, 90]
    assert not result["mask"][70, 100]
    assert not result["unknown"][70, 100]
    np.testing.assert_array_equal(raw, original)
    assert result["mask"].shape == raw.shape[:2]


@pytest.mark.parametrize("box", [[-1, 0, 5, 5], [0, 0, 21, 5], [0.0, 0, 5, 5]])
def test_invalid_native_exclusion_is_rejected(box):
    with pytest.raises(ValueError):
        native_valid((20, 20), [box])


def ct_fixture():
    aa = np.zeros((160, 200), bool)
    aa[30:130, 30:140] = True
    ct = np.zeros_like(aa)
    for x, y in [(70, 70), (30, 70), (180, 70), (90, 90)]:
        ct[y - 2 : y + 3, x - 2 : x + 3] = True
    valid = np.ones_like(aa)
    valid[85:96, 85:96] = False
    anchors = [[10, 10], [190, 10], [190, 150], [10, 150]]
    settings = dict(base_px=5, max_px=15, outside_anchor_hull_growth_px_per_px=0.01)
    return aa, ct, valid, anchors, settings


def test_ct_association_keeps_boundary_invalid_and_exterior_distinct():
    aa, ct, valid, anchors, settings = ct_fixture()
    result = associate_ct(aa, ct, np.eye(3), anchors, settings, valid)
    assert result["selected"][70, 70]
    assert result["unknown"][70, 30]
    assert not result["selected"][70, 180]
    assert not result["unknown"][70, 180]
    assert result["unknown"][90, 90]
    assert {x["status"] for x in result["records"]} == {
        "AA_interior_candidate",
        "AA_boundary_or_registration_unknown",
        "invalid_reference_coverage",
        "not_assigned_to_AA_not_proof_of_poly",
    }
    assert all(x["physical_contact_count"] is None for x in result["records"])


def test_ct_transform_direction_is_source_to_reference():
    aa, ct, valid, anchors, settings = ct_fixture()
    matrix = np.array([[1.0, 0, 100], [0, 1, 0], [0, 0, 1]])
    result = associate_ct(aa, ct, matrix, anchors, settings, valid)
    assert not result["selected"][70, 70]  # Source x70 lands at AA x170, outside.
    assert result["unknown"][70, 180]  # Projects outside the reference canvas.
    record = next(x for x in result["records"] if x["poly_native_center_xy"] == [70.0, 70.0])
    assert record["aa_reference_center_xy"] == [170.0, 70.0]


@pytest.mark.parametrize("matrix", [np.zeros((3, 3)), np.diag([0.01, 0.01, 1])])
def test_degenerate_full_frame_registration_rejected(matrix):
    aa, ct, valid, anchors, settings = ct_fixture()
    with pytest.raises(ValueError, match="Degenerate"):
        associate_ct(aa, ct, matrix, anchors, settings, valid)


def test_output_cannot_overwrite_originals_or_existing_run(tmp_path):
    raw = tmp_path / "data"
    raw.mkdir()
    with pytest.raises(ValueError, match="outside raw"):
        run(tmp_path, tmp_path / "missing.json", raw / "new")
    with pytest.raises(ValueError, match="new"):
        run(tmp_path, tmp_path / "missing.json", raw)
