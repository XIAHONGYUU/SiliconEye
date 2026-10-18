"""Whole-scene expansion must retain anchors, exclude holes and preserve uncertainty."""

import copy

import numpy as np
from shapely.geometry import Point

from silicon_eye.geometry_reconstruction import object_polygon
from silicon_eye.group_constraints import rect
from silicon_eye.regular_scene import (
    axis_levels,
    contact_candidates,
    display_role,
    regularize_aa,
    source_assignments,
)

AA = dict(
    size_relative_tolerance=0.09,
    baseline_tolerance=9.0,
    max_shift=8.0,
    pitch_relative_tolerance=0.08,
    min_group_size=3,
)
CT = dict(
    square_side=8.0,
    axis_cluster=3.5,
    max_axis_shift=6.0,
    min_pitch=10.0,
    max_slots_per_AA=6000,
    max_inferred_fraction=0.2,
    min_grid_support=0.55,
    AA_margin=2.0,
    duplicate_radius=6.0,
)
MATRICES = {"global": {"aa": np.eye(3), "poly": np.eye(3)}}


def observations(points):
    return [dict(id=f"p{i}", native_center_xy=list(p)) for i, p in enumerate(points)]


def test_row_shares_baseline_size_and_pitch_without_moving_locked_geometry():
    objects = [
        rect("a", [0, 0, 10, 10]),
        rect("b", [20, 1, 30, 11]),
        rect("c", [40, 2, 50, 12]),
        rect("locked", [80, 3, 90, 13]),
    ]
    before = copy.deepcopy(objects)
    result, groups = regularize_aa(objects, {"locked"}, AA)
    assert result[-1] == before[-1] and objects == before
    assert len(groups) == 1 and groups[0]["state"] == "applied_candidate"
    assert [o["outer_xyxy"][1] for o in result[:3]] == [1, 1, 1]
    np.testing.assert_allclose([o["outer_xyxy"][0] for o in result[:3]], [0, 20, 40], atol=1e-10)


def test_row_collision_defers_entire_group_without_partial_changes():
    objects = [
        rect("a", [0, 0, 10, 10]),
        rect("b", [20, 2, 30, 12]),
        rect("c", [40, 4, 50, 14]),
        rect("obstacle", [1, 10.5, 3, 11.5]),
    ]
    result, groups = regularize_aa(objects, {"obstacle"}, AA)
    assert result == objects
    assert groups[0]["state"] == "deferred_collision_or_shift"


def test_axis_fits_existing_levels_without_inventing_unknown_columns():
    levels, indices, pitch = axis_levels([12.2, 12.8, 26.1, 26.4, 40.4, 40.8], CT)
    assert pitch is not None
    np.testing.assert_array_equal(indices, [0, 0, 1, 1, 2, 2])
    np.testing.assert_allclose(np.diff(levels), [pitch, pitch], atol=1e-8)
    levels, _, pitch = axis_levels([10, 40], CT)
    assert len(levels) == 2 and pitch is None


def test_source_assignment_respects_holes_and_per_group_projection():
    ring = dict(rect("r", [0, 0, 100, 100]), hole_xyxy=[30, 30, 70, 70])
    shift = np.array([[1.0, 0, 150.0], [0, 1, 0], [0, 0, 1]])
    matrices = dict(MATRICES, local={"aa": shift, "poly": shift})
    assigned = source_assignments(
        observations([[170, 20], [200, 50], [20, 20]]), [ring], {"r": "local"}, matrices
    )
    assert assigned == {0: [0]}


def test_full_scope_contacts_preserve_reserved_geometry_and_unclassified_sources():
    aa = [rect("a", [0, 0, 100, 100])]
    obs = observations([[x, y] for x in [20, 50, 80] for y in [20, 50, 80]] + [[150, 150]])
    retained = [
        dict(
            rect("keep", [16, 16, 24, 24], "CT"),
            status="photo_peak_support",
            source_observation_ids=["p0"],
        )
    ]
    snapshot = copy.deepcopy(retained)
    new, pending, dispositions, groups = contact_candidates(obs, aa, retained, {}, MATRICES, CT)
    assert retained == snapshot
    assert len(new) == 8 and len(pending) == 1
    assert len(dispositions) == len(obs)
    assert all(not object_polygon(o).intersects(object_polygon(retained[0])) for o in new)
    assert all(display_role(o) == "CT" for o in new)
    assert pending[0]["reason"] == "AA_assignment_unknown_not_proof_of_poly"
    assert groups[0]["repeat_supported"]


def test_template_never_infers_material_contact_into_ring_hole():
    ring = dict(rect("r", [0, 0, 100, 100]), hole_xyxy=[30, 30, 70, 70])
    pts = [[x, y] for x in [20, 50, 80] for y in [20, 50, 80]]
    new, pending, dispositions, _ = contact_candidates(
        observations(pts), [ring], [], {}, MATRICES, CT
    )
    assert len(new) == 8 and len(pending) == 1 and len(dispositions) == 9
    assert all(not object_polygon(o).contains(Point(50, 50)) for o in new)
    assert all(o["electrical_connection"] == "unknown" for o in new)
    inferred = dict(rect("i", [0, 0, 8, 8], "CT"), status="inferred_candidate")
    assert display_role(inferred) == "inferred"


def test_periodic_axis_handles_split_peak_levels_without_creating_missing_rows():
    values = [13 * r + d for r in [0, 1, 2, 4, 5, 6, 7] for d in [-4, 0, 0, 0, 0, 0, 0, 0, 0, 4]]
    levels, assignment, pitch = axis_levels(values, CT)
    assert pitch is not None
    assert len(levels) == 7 and len(assignment) == len(values)
    np.testing.assert_allclose(levels, [0, 13, 26, 52, 65, 78, 91], atol=0.01)
    assert not any(abs(levels - 39) < 0.01)


def test_boundary_fragment_uses_retained_lattice_without_moving_anchor():
    from silicon_eye.regular_scene import align_boundary_neighbors

    anchor = dict(rect("keep", [0.0, 0.0, 10.0, 10.0]), template_id="D01")
    fragment = rect("edge", [-4.0, 0.0, 2.0, 10.0])
    group = dict(
        id="D01",
        kind="rectangle_array",
        rows=1,
        cols=1,
        origin_xy=[0.0, 0.0],
        size_wh=[10.0, 10.0],
        pitch_xy=[20.0, 20.0],
        source_frame="aa",
        layout_to_native=[[1.0, 0.0, 20.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    )
    seed = dict(objects=[anchor], groups=[group])
    result, mapping, extensions, deferred = align_boundary_neighbors(
        [anchor, fragment], seed, dict(aa_native_to_layout=np.eye(3).tolist())
    )
    assert result[0] == anchor
    np.testing.assert_allclose(result[1]["outer_xyxy"], [-20, 0, -10, 10])
    assert mapping == {"edge": "D01"} and len(extensions) == 1 and not deferred
    assert not object_polygon(result[0]).intersects(object_polygon(result[1]))


def test_unresolved_boundary_collision_preserves_evidence_outside_active_layer():
    from silicon_eye.regular_scene import align_boundary_neighbors

    anchor = dict(rect("keep", [0.0, 0.0, 10.0, 10.0]), template_id="other")
    fragment = rect("edge", [-4.0, 0.0, 2.0, 10.0])
    seed = dict(objects=[anchor], groups=[])
    result, _, _, deferred = align_boundary_neighbors([anchor, fragment], seed, {})
    assert result == [anchor]
    assert deferred[0]["object"] == fragment
    assert deferred[0]["reason"] == "retained_boundary_frame_conflict"
