"""Geometry reconstruction must preserve separations and unsupported slots."""

import cv2
import numpy as np
import pytest

from silicon_eye.geometry_reconstruction import (
    build_aa,
    build_ct,
    corners,
    fit_lattice,
    normalize,
    project,
    rectangle_fit,
    render_mask,
)


def observation(identifier, bounds, hole=None):
    return dict(
        id=identifier,
        layer="AA",
        observed_outer_native_xy=corners(bounds).tolist(),
        observed_hole_native_xy=None if hole is None else corners(hole).tolist(),
        status="candidate",
    )


def test_orthogonal_fit_uses_opposite_sides_and_grid():
    p = [[10.2, 20.1], [90.6, 18.8], [89.9, 70.3], [9.4, 71.1]]
    bounds = rectangle_fit(p)
    assert bounds == [10, 19, 90, 71]
    edges = np.diff(np.vstack([corners(bounds), corners(bounds)[0]]), axis=0)
    assert np.all(np.count_nonzero(edges, axis=1) == 1)
    with pytest.raises(ValueError, match="positive"):
        rectangle_fit(p, 0)
    with pytest.raises(ValueError, match="Collapsed"):
        rectangle_fit(corners([1, 2, 1, 3]))


def test_hole_and_independent_island_survive_vector_and_raster_build():
    obs = [
        observation("ring", [10, 10, 110, 100], [20, 20, 100, 90]),
        observation("island", [40, 40, 80, 70]),
    ]
    settings = dict(group="unused", grid_step=1)
    aa = build_aa(obs, np.eye(3), settings)
    mask = render_mask(aa, [130, 120])
    assert mask[15, 15] and mask[50, 50]
    assert not mask[30, 30]
    count, labels = cv2.connectedComponents(mask)
    assert count == 3
    assert labels[15, 15] != labels[50, 50]
    # Rendering order must not allow the ring's hole to erase the independent island.
    np.testing.assert_array_equal(mask, render_mask(list(reversed(aa)), [130, 120]))


def test_regularization_that_creates_a_touch_is_rejected():
    obs = [observation("a", [10, 10, 20.4, 30]), observation("b", [20.49, 10, 40, 30])]
    with pytest.raises(ValueError, match="Unapproved AA touching"):
        build_aa(obs, np.eye(3), dict(group="unused", grid_step=1))


def test_known_projective_lattice_is_rectified_without_claiming_physical_truth():
    transform = np.array([[1.01, 0.015, 3.0], [-0.01, 0.99, 4.0], [1e-5, -1e-5, 1.0]])
    observations = []
    expected = []
    for row in range(3):
        for col in range(4):
            center = np.array([100 + 40 * col, 100 + 50 * row])
            native = project(corners([*(center - 5), *(center + 5)]), np.linalg.inv(transform))
            observations.append(
                dict(group="grid", row=row, column=col, observed_outer_native_xy=native.tolist())
            )
            expected.append(center)
    matrix, report = normalize(
        observations, dict(group="grid", origin_xy=[100, 100], pitch_xy=[40, 50]), [400, 300]
    )
    centers = [np.mean(o["observed_outer_native_xy"], axis=0) for o in observations]
    np.testing.assert_allclose(project(centers, matrix), expected, atol=0.003)
    assert report["independent_validation"] is False
    assert report["fullframe_distortion_eliminated"] is False


def test_equal_pitch_fit_tolerates_missing_observations_without_filling_them():
    ij = np.array([[0, 0], [1, 0], [2, 0], [0, 1], [1, 2], [2, 2], [0, 3]])
    points = [20, 30] + ij * [12, 16]
    points = np.vstack([points, [300, 400]])
    origin, pitch, count = fit_lattice(points, [20, 30], [12, 16], [3, 4], 0.5)
    np.testing.assert_allclose(origin, [20, 30])
    np.testing.assert_allclose(pitch, [12, 16])
    assert count == 7
    with pytest.raises(ValueError, match="Too few"):
        fit_lattice(points[:3], origin, pitch, [3, 4], 0.5)


def test_unsupported_grid_slots_stay_unknown_even_when_fit_exists():
    records = []
    for row in range(3):
        for col in range(3):
            records.append(
                dict(
                    aa_reference_center_xy=[40 + 20 * col, 40 + 20 * row],
                    poly_native_bbox_xywh=[0, 0, 8, 8],
                )
            )
    spec = dict(
        support=dict(
            max_single_component_native_size=22,
            grid_fit_residual_limit=3,
            min_peak_gray=195,
            min_local_prominence=12,
        ),
        ct_arrays=[
            dict(
                id="ct-grid",
                aa_object_id="aa",
                origin_aa_native_xy=[40, 40],
                pitch_seed_xy=[20, 20],
                rows=3,
                columns=3,
                square_side=8,
            )
        ],
    )
    aa = [dict(id="aa", outer_xyxy=[20, 20, 100, 100])]
    objects, arrays = build_ct(
        spec, aa, np.eye(3), np.eye(3), records, np.zeros((120, 120, 3), np.uint8)
    )
    assert len(objects) == 9
    assert all(o["status"] == "unknown_missing_or_occluded" for o in objects)
    assert all(o["electrical_connection"] == "unknown" for o in objects)
    assert arrays[0]["completeness"] == "unknown_not_physical_contact_count"


def test_contact_landing_excludes_ring_hole():
    from silicon_eye.geometry_reconstruction import aa_contains

    aa = dict(outer_xyxy=[10, 10, 100, 100], hole_xyxy=[25, 25, 85, 85])
    assert aa_contains(aa, [13, 30, 21, 38])
    assert not aa_contains(aa, [40, 40, 48, 48])
    assert not aa_contains(aa, [20, 30, 28, 38])


def test_scoped_human_review_preserves_geometry_and_unreviewed_candidates():
    from copy import deepcopy

    from silicon_eye.geometry_reconstruction import apply_human_review, ct_positive

    objects = [
        dict(id="ct-orange", layer="CT", outer_xyxy=[1, 2, 9, 10], status="unknown_AA_landing"),
        dict(
            id="ct-blue",
            layer="CT",
            outer_xyxy=[20, 2, 28, 10],
            status="observed_brightness_geometry_candidate",
        ),
    ]
    before = deepcopy(objects)
    record = dict(
        decisions=[dict(scope="CT_presence_and_approximate_placement", object_ids=["ct-orange"])]
    )
    apply_human_review(objects, record, "record-sha")
    assert all(o["outer_xyxy"] == b["outer_xyxy"] for o, b in zip(objects, before, strict=True))
    assert ct_positive(objects[0])
    assert objects[0]["algorithm_status_before_human_review"] == "unknown_AA_landing"
    assert objects[0]["human_review"]["exact_dimensions"] == "not_accepted"
    assert objects[1] == before[1]
    with pytest.raises(ValueError, match="missing object"):
        apply_human_review(
            objects, dict(decisions=[dict(scope="x", object_ids=["missing"])]), "sha"
        )


def ring_ct_fixture():
    aa = [dict(id="ring", outer_xyxy=[10, 10, 130, 90], hole_xyxy=[25, 25, 115, 75])]
    spec = dict(
        support=dict(min_peak_gray=195, min_local_prominence=12),
        ct_ring_runs=[
            dict(
                id="run",
                aa_object_id="ring",
                side="top",
                pitch_reference_array="grid",
                max_normal_offset=3,
                square_side=8,
                min_periodic_contrast_gray=12,
            )
        ],
    )
    return aa, spec, [dict(id="grid", fitted_pitch_xy=[12, 12])]


def test_periodic_ring_run_recovers_slots_but_not_missing_contact():
    from silicon_eye.geometry_reconstruction import build_ring_ct, ct_positive

    aa, spec, arrays = ring_ct_fixture()
    photo = np.zeros((140, 160, 3), np.uint8)
    for x in [26, 38, 50, 74, 86, 98]:
        cv2.rectangle(photo, (x - 3, 15), (x + 3, 21), (255, 255, 255), -1)
    objects, runs = build_ring_ct(spec, aa, np.eye(3), np.eye(3), arrays, photo)
    assert runs[0]["median_periodic_contrast_gray"] > 100
    assert sum(ct_positive(o) for o in objects) >= 5
    missing = min(objects, key=lambda o: abs(o["source_native_center_xy"][0] - 62))
    # A flat-topped 7 px synthetic spot permits a 1 px phase tie.
    assert abs(missing["source_native_center_xy"][0] - 62) <= 1
    assert missing["status"] == "unknown_missing_or_occluded"
    assert all(o["electrical_connection"] == "unknown" for o in objects)


def test_uniform_bright_ring_edge_does_not_become_confirmed_contact_array():
    from silicon_eye.geometry_reconstruction import build_ring_ct, ct_positive

    aa, spec, arrays = ring_ct_fixture()
    photo = np.zeros((140, 160, 3), np.uint8)
    photo[12:24, :] = 255
    objects, runs = build_ring_ct(spec, aa, np.eye(3), np.eye(3), arrays, photo)
    assert abs(runs[0]["median_periodic_contrast_gray"]) < 0.01
    assert not any(ct_positive(o) for o in objects)


def l_polygon():
    return dict(
        id="new-L",
        primitive="orthogonal_polygon",
        layer="AA",
        outer_xy=[[10, 10], [40, 10], [40, 20], [20, 20], [20, 40], [10, 40]],
        holes_xy=[],
        outer_xyxy=[10, 10, 40, 40],
        hole_xyxy=None,
    )


def test_polygon_material_does_not_fill_its_concave_bbox():
    from silicon_eye.geometry_reconstruction import aa_contains, check_aa_separation, svg

    obj = l_polygon()
    mask = render_mask([obj], [60, 60])
    assert mask[15, 30] and mask[30, 15]
    assert not mask[30, 30]
    assert aa_contains(obj, [12, 25, 18, 35])
    assert not aa_contains(obj, [25, 25, 35, 35])
    island = dict(primitive="rectangle", id="separate", outer_xyxy=[28, 28, 35, 35], hole_xyxy=None)
    check_aa_separation([obj, island])  # Overlapping bboxes are not material overlap.
    text = svg([obj], [60, 60])
    assert text.count(" L") == 5  # Complete six-vertex outline, not a four-corner bbox.
    island["outer_xyxy"] = [20, 28, 35, 35]
    with pytest.raises(ValueError, match="Unapproved AA touching"):
        check_aa_separation([obj, island])


def test_orthogonal_fitting_preserves_reentrant_corner_and_step_direction():
    from silicon_eye.geometry_reconstruction import orthogonal_fit

    source = np.array(
        [[10.2, 10], [40.3, 10.4], [40, 20.1], [20.4, 20.3], [20.1, 40.4], [10, 40.2]]
    )
    fitted = orthogonal_fit(source, ["H", "V"] * 3)
    np.testing.assert_allclose(fitted, l_polygon()["outer_xy"])
    assert len(fitted) == 6
    obj = l_polygon()
    obj["outer_xy"] = fitted.tolist()
    assert not render_mask([obj], [60, 60])[30, 30]


def test_invalid_polygon_constraints_and_collapsed_features_fail():
    from silicon_eye.geometry_reconstruction import orthogonal_fit

    with pytest.raises(ValueError, match="Invalid orthogonal"):
        orthogonal_fit(l_polygon()["outer_xy"], ["H"] * 5)
    with pytest.raises(ValueError, match="self-intersecting"):
        orthogonal_fit([[0, 0], [10, 10], [0, 10], [10, 0]], ["H", "V"] * 2)
    narrow = [[0, 0], [10, 0], [10, 0.2], [1, 0.2], [1, 10], [0, 10]]
    with pytest.raises(ValueError, match="collapsed or reversed"):
        orthogonal_fit(narrow, ["H", "V"] * 3)


def test_fold_fragments_keep_gap_and_explicit_unmodeled_continuation():
    from silicon_eye.geometry_reconstruction import (
        build_aa_polygons,
        check_aa_separation,
        svg_continuations,
    )

    top = dict(
        id="fold-up",
        observed_outline_native_xy=[[10, 10], [14, 10], [14, 30], [35, 30], [35, 34], [10, 34]],
        edge_axes=["H", "V"] * 3,
        scope="material_fragment_not_complete_component",
        continuation_ports=[
            dict(native_xy=[12, 10], edge_index=0, meaning="continues_into_unmodeled_AA")
        ],
    )
    bottom = dict(
        id="fold-down",
        observed_outline_native_xy=[[10, 38], [35, 38], [35, 42], [14, 42], [14, 60], [10, 60]],
        edge_axes=["H", "V"] * 3,
        scope="material_fragment_not_complete_component",
        continuation_ports=[
            dict(native_xy=[12, 60], edge_index=4, meaning="continues_into_unmodeled_AA")
        ],
    )
    aa = build_aa_polygons([top, bottom], np.eye(3), 1)
    check_aa_separation(aa)
    mask = render_mask(aa, [80, 80])
    assert not mask[36].any()
    count, _ = cv2.connectedComponents(mask)
    assert count == 3
    assert all(o["electrical_connection"] == "unknown" for o in aa)
    assert all(o["scope"] == "material_fragment_not_complete_component" for o in aa)
    text = svg_continuations(aa, [80, 80], np.eye(3))
    assert text.count("stroke-dasharray") == 2
