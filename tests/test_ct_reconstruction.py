"""CT structural checks must preserve unknowns and must not manufacture evidence."""

import copy

import cv2
import numpy as np
import pytest
from shapely.geometry import Polygon, box

from silicon_eye.ct_reconstruction import build_candidates, landing, regularize, supplement_peaks


def settings():
    return dict(
        square_side=4,
        enclosure_px=1,
        min_gap_px=2,
        axis_cluster_px=2.5,
        max_regularization_shift=3,
        pitch_min=9,
        pitch_max=100,
        periodic_snap_residual=2.5,
    )


@pytest.mark.parametrize(
    ("cut", "expected"),
    [
        (box(2, 2, 6, 6), "AA_candidate"),
        (box(32, 2, 36, 6), "POLY_candidate"),
        (box(18, 2, 22, 6), "unknown"),
        (box(50, 2, 54, 6), "unknown"),
        (box(39, 2, 43, 6), "unknown"),
    ],
)
def test_channel_field_and_edge_never_become_valid_landing(cut, expected):
    aa, poly = box(0, 0, 25, 20), box(18, 0, 40, 20)
    assert landing(cut, aa, poly)[0] == expected


def test_ring_hole_is_not_material():
    ring = Polygon(box(0, 0, 40, 40).exterior.coords, [list(box(8, 8, 32, 32).exterior.coords)])
    assert landing(box(15, 15, 19, 19), ring, Polygon())[0] == "unknown"
    assert landing(box(2, 15, 6, 19), ring, Polygon())[0] == "AA_candidate"


def test_regularization_keeps_observed_count_without_filling_missing_slot():
    points = np.array([[1.0, 1.0], [1.2, 13.0], [1.1, 37.0]])
    result = regularize(points, settings())
    assert len(result) == 3
    assert np.max(np.linalg.norm(result - points, axis=1)) <= 3
    assert not np.any(np.isclose(result[:, 1], 25))


def test_conflicting_cut_evidence_is_retained_and_baseline_unchanged():
    model = {
        "AA_objects": [dict(id="A", outer_xyxy=[0, 0, 40, 40])],
        "objects": [dict(id="P", layout_outline=[[60, 0], [70, 0], [70, 40], [60, 40]])],
    }
    original = copy.deepcopy(model)
    observations = [
        dict(source_native_center_xy=[10.0, 10.0], peak_gray=220),
        dict(source_native_center_xy=[12.0, 10.0], peak_gray=200, detector="relaxed_shape"),
    ]
    records, conflicts = build_candidates(observations, model, np.eye(3), settings(), "T")
    assert model == original
    assert len(records) == 2 and len(conflicts) == 1
    assert records[0]["net_id"] is None
    assert records[1]["evidence_tier"] == "relaxed_shape"
    assert records[1]["landing_hypothesis"] == "unknown"
    assert all(r["assignment_status"].startswith("unknown") for r in records)
    assert all(Polygon(r["layout_outline"]).area == 16 for r in records)


def test_unreviewed_family_cannot_enable_array_snap():
    model = {
        "AA_objects": [dict(id="A", outer_xyxy=[0, 0, 40, 40])],
        "objects": [dict(id="P", layout_outline=[[60, 0], [70, 0], [70, 40], [60, 40]])],
    }
    config = settings() | {"allow_regularization": True}
    with pytest.raises(ValueError, match="Local family review"):
        build_candidates([], model, np.eye(3), config, "T")


def test_row_prior_cannot_create_a_hole_without_an_observed_peak():
    config = dict(
        neighborhood=11,
        peak_gray=205,
        peak_residual=16,
        crop_border_px=8,
        max_peak_plateau_span=9,
        duplicate_radius=6,
        neighbor_radius=45,
        axis_tolerance=4,
        min_neighbors=2,
    )
    image = np.full((70, 90, 3), 40, np.uint8)
    for x in [20, 60]:
        cv2.circle(image, (x, 30), 4, (255, 255, 255), -1)
    compact = [
        dict(source_native_center_xy=[20.0, 30.0], peak_gray=240),
        dict(source_native_center_xy=[60.0, 30.0], peak_gray=240),
    ]
    assert len(supplement_peaks(image, compact, [0, 0], config)) == 2
    cv2.circle(image, (40, 30), 4, (255, 255, 255), -1)
    expanded = supplement_peaks(image, compact, [0, 0], config)
    assert len(expanded) == 3
    assert expanded[-1]["detector"].startswith("relaxed_shape")
    assert expanded[-1]["source_native_center_xy"] == [40.0, 30.0]
