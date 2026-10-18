"""Scene extension preserves source gaps, old objects and evidence boundaries."""

import cv2
import numpy as np
import pytest
from shapely.geometry import Point, Polygon

from silicon_eye.geometry_reconstruction import object_polygon, render_mask
from silicon_eye.scene_geometry import (
    aa_proposals,
    canvas_size,
    ct_proposals,
    extract_peaks,
    orthogonal_outline,
    paint_objects,
    regularize_axis,
)

AA = dict(
    min_area=80,
    min_short_side=3,
    approximation_px=2,
    max_vertices=40,
    max_boundary_shift_px=8,
    min_area_ratio=0.8,
    max_area_ratio=1.25,
)
CT = dict(
    peak_gray=205,
    peak_residual=16,
    peak_neighborhood=11,
    max_peak_plateau_span=9,
    square_side=8,
    axis_cluster_px=2.5,
    max_regularization_shift=3,
    duplicate_radius=7,
    pitch_min=9,
    pitch_max=100,
    periodic_snap_residual=2.5,
)


def rect(identifier, bounds, hole=None):
    return dict(
        id=identifier,
        primitive="rectangle_ring" if hole else "rectangle",
        layer="AA",
        outer_xyxy=bounds,
        hole_xyxy=hole,
    )


def test_fast_roi_render_preserves_holes_islands_and_frame_clipping():
    objects = [
        rect("ring", [5, 5, 80, 80], [15, 15, 70, 70]),
        rect("island", [30, 30, 45, 45]),
        rect("edge", [-10, 90, 20, 120]),
    ]
    np.testing.assert_array_equal(
        paint_objects(objects, [100, 100]), render_mask(objects, [100, 100])
    )
    labels = paint_objects(objects, [100, 100], labels=True)
    assert labels[10, 10] == 1
    assert labels[35, 35] == 2
    assert labels[25, 25] == 0
    assert labels[95, 5] == 3


def test_full_canvas_expands_without_translating_existing_coordinates():
    base = dict(
        sources={k: dict(width=100, height=500) for k in ["aa", "poly"]}, canvas_wh=[100, 500]
    )
    a = np.array([[1.0, 0, 50], [0, 1, 30], [0, 0, 1]])
    b = np.array([[1.0, 0, 80], [0, 1, 50], [0, 0, 1]])
    original = a.copy()
    assert canvas_size(base, a, b) == [197, 567]
    np.testing.assert_array_equal(a, original)
    b[0, 2] = -80
    with pytest.raises(ValueError, match="negative coordinates"):
        canvas_size(base, a, b)


def test_concave_outline_keeps_large_step_notch():
    points = np.array(
        [[10, 10], [90, 10], [90, 30], [35, 30], [35, 80], [10, 80]], np.int32
    ).reshape(-1, 1, 2)
    fitted, shift = orthogonal_outline(points, AA)
    polygon = Polygon(fitted)
    assert polygon.contains(Point(20, 60))
    assert not polygon.contains(Point(70, 60))
    assert shift == 0
    edges = np.roll(fitted, -1, axis=0) - fitted
    assert np.all(np.count_nonzero(edges, axis=1) == 1)


def test_scene_hierarchy_keeps_ring_hole_and_preserved_inner_island():
    mask = np.zeros((160, 180), np.uint8)
    cv2.rectangle(mask, (10, 10), (160, 140), 255, -1)
    cv2.rectangle(mask, (25, 25), (145, 125), 0, -1)
    cv2.rectangle(mask, (60, 60), (90, 90), 255, -1)
    protected = rect("old-island", [60, 60, 90, 90])
    candidates, deferred = aa_proposals(mask, [protected], AA)
    assert len(candidates) == 1
    material = object_polygon(candidates[0])
    assert material.contains(Point(15, 15))
    assert not material.contains(Point(70, 70))
    assert any("old-island" in item.get("references", []) for item in deferred)
    assert protected == rect("old-island", [60, 60, 90, 90])


def test_shape_support_rejects_uniform_bright_line_but_keeps_local_contact():
    photo = np.full((120, 180, 3), 70, np.uint8)
    photo[10:20, :] = 250
    photo[60:71, 80:91] = 250
    observations = extract_peaks(photo, np.ones(photo.shape[:2], bool), CT)
    assert observations
    assert all(
        70 < o["source_native_center_xy"][0] < 100 and 50 < o["source_native_center_xy"][1] < 80
        for o in observations
    )


def test_regularization_preserves_missing_slots_and_observation_count():
    values = np.array([10.2, 23.8, 52.1, 65.9])
    result, metadata = regularize_axis(values, CT)
    assert len(result) == 4
    np.testing.assert_allclose(result, [10, 24, 52, 66], atol=0.3)
    assert not np.any(np.isclose(result, 38, atol=2))
    assert metadata["fitted_pitch"] is not None


def test_ct_source_hole_unknown_border_and_old_duplicate_stay_distinct():
    aa = [rect("ring", [10, 10, 100, 100], [30, 30, 80, 80])]
    labelmap = paint_objects(aa, [120, 120], labels=True)
    old = [dict(outer_xyxy=[14, 46, 22, 54])]
    observations = [
        dict(source_native_center_xy=p) for p in [[18, 50], [50, 50], [12, 25], [90, 90]]
    ]
    objects, unassigned, _, duplicates = ct_proposals(
        observations, aa, old, labelmap, np.eye(3), CT
    )
    assert duplicates == 1
    assert len(unassigned) == 1 and unassigned[0]["status"].endswith("not_proof_of_poly")
    assert {o["status"] for o in objects} == {
        "unknown_AA_landing",
        "observed_brightness_geometry_candidate",
    }
    assert all(o["electrical_connection"] == "unknown" for o in objects)
    assert ct_proposals([], aa, old, labelmap, np.eye(3), CT) == ([], [], [], 0)


def test_regularized_ct_squares_do_not_overlap_reserved_contact_geometry():
    aa = [rect("solid", [0, 0, 120, 120])]
    labelmap = paint_objects(aa, [120, 120], labels=True)
    old = [dict(outer_xyxy=[36, 36, 44, 44])]
    # This diagonal point is > 7 units from the old center, yet 8x8 squares overlap.
    observations = [dict(source_native_center_xy=p) for p in [[47, 47], [80, 80], [87, 87]]]
    objects, _, _, suppressed = ct_proposals(observations, aa, old, labelmap, np.eye(3), CT)
    assert suppressed == 2
    assert len(objects) == 1
    assert objects[0]["outer_xyxy"] == [76, 76, 84, 84]
