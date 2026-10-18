"""Behavioral checks for structural rules, missing evidence and held-out image mismatches."""

import copy

import numpy as np
import pytest
from shapely.geometry import Point

from silicon_eye.geometry_reconstruction import object_polygon
from silicon_eye.group_constraints import (
    array_geometry,
    audit,
    evidence_result,
    fault_trials,
    fit_photo,
    rect,
)


def array(kind="rectangle_array"):
    return dict(
        id="fixture",
        kind=kind,
        rows=3,
        cols=4,
        origin_xy=[20.0, 20.0],
        pitch_xy=[30.0, 30.0],
        size_wh=[8.0, 8.0],
        AA_material=rect("AA", [0.0, 0.0, 150.0, 150.0]),
        landing_margin=2.0,
        channel_zones=None,
        upper_metal=None,
    )


def states(results):
    return {r["rule"]: r["state"] for r in results}


def test_array_gate_accepts_regular_group_and_rejects_shift_size_missing_duplicate():
    group = array()
    objects = array_geometry(group)
    assert all(v == "pass" for v in states(audit(group, objects)).values())
    trials = fault_trials(group, objects)
    assert len(trials) == 4 and all(t["detected"] for t in trials)
    # Independent fixture: a whole row shifted coherently must fail even with equal pitches in it.
    changed = copy.deepcopy(objects)
    for o in changed:
        if o["row"] == 1:
            o["outer_xyxy"][0] += 3
            o["outer_xyxy"][2] += 3
    assert states(audit(group, changed))["shared_baselines_pitch_and_shape"] == "fail"


def test_valid_hv_and_equal_area_do_not_replace_template_shape_check():
    group = array()
    objects = array_geometry(group)
    objects[0].update(
        primitive="orthogonal_polygon",
        outer_xy=[
            [20.0, 20.0],
            [28.0, 20.0],
            [28.0, 24.0],
            [24.0, 24.0],
            [24.0, 32.0],
            [20.0, 32.0],
        ],
        holes_xy=[],
    )
    assert object_polygon(objects[0]).area == 64
    result = states(audit(group, objects))
    assert result["HV_edges"] == "pass"
    assert result["shared_baselines_pitch_and_shape"] == "fail"


def test_contact_legality_checks_real_polygons_and_explicit_dependencies():
    group = array("contact_array")
    objects = array_geometry(group)
    result = states(audit(group, objects))
    assert result["AA_landing_enclosure"] == "pass"
    assert result["channel_exclusion"] == result["upper_metal_enclosure"] == "unknown"
    assert result["target_process_numeric_DRC"] == "unknown"
    group["AA_material"] = dict(
        rect("ring", [0.0, 0.0, 150.0, 150.0]),
        primitive="rectangle_ring",
        hole_xyxy=[10.0, 10.0, 60.0, 60.0],
    )
    assert states(audit(group, objects))["AA_landing_enclosure"] == "fail"
    group["AA_material"] = None
    assert states(audit(group, objects))["AA_landing_enclosure"] == "unknown"


def test_channel_and_upper_layer_faults_are_detected_without_fake_real_layer_claims():
    group = array("contact_array")
    objects = array_geometry(group)
    trials = fault_trials(group, objects)
    assert len(trials) == 7 and all(t["detected"] for t in trials)
    group["channel_zones"] = []
    group["upper_metal"] = [[0.0, 0.0, 150.0, 150.0]]
    result = states(audit(group, objects))
    assert result["channel_exclusion"] == result["upper_metal_enclosure"] == "pass"
    assert result["target_process_numeric_DRC"] == "unknown"
    assert states(audit(group, []))["valid_nonempty_geometry"] == "fail"


def test_ring_gate_preserves_hole_and_detects_gap_filled_hole_and_width_variation():
    group = dict(
        id="ring",
        kind="closed_ring",
        outer_xyxy=[0.0, 0.0, 80.0, 60.0],
        hole_xyxy=[10.0, 10.0, 70.0, 50.0],
    )
    ring = dict(
        rect("r", group["outer_xyxy"]), primitive="rectangle_ring", hole_xyxy=group["hole_xyxy"]
    )
    assert all(v == "pass" for v in states(audit(group, [ring])).values())
    assert not object_polygon(ring).contains(Point(40.0, 30.0))
    assert fault_trials(group, [ring])[0]["detected"]
    for hole in [None, [11.0, 10.0, 70.0, 50.0]]:
        bad = dict(ring, hole_xyxy=hole)
        assert states(audit(group, [bad]))["continuous_constant_width_ring"] == "fail"


def test_photo_gate_checks_heldout_samples_and_catches_coherent_wrong_geometry():
    xy = np.array([[x, y] for y in [0, 30, 60] for x in [0, 30, 60, 90]], float)
    photo = xy * np.array([1.1, 0.9]) + [12.0, 40.0]
    split = ["holdout" if i % 4 == 1 else "fit" for i in range(len(xy))]
    transform, metrics = fit_photo(xy, photo, split)
    assert metrics["holdout_count"] == 3
    assert evidence_result(metrics, 0.01, 0.01)["state"] == "pass"
    assert np.allclose(transform, [[1.1, 0, 12], [0, 0.9, 40], [0, 0, 1]], atol=1e-6)
    # Geometry is regular, but mismatched held-out image evidence must not be accepted.
    bad = photo.copy()
    bad[1::4] += [20.0, 0.0]
    _, metrics = fit_photo(xy, bad, split)
    assert evidence_result(metrics, 3, 5)["state"] == "fail"
    with pytest.raises(ValueError, match="disjoint"):
        fit_photo(xy, photo, ["fit"] * len(xy))


def test_gate_rejects_self_consistent_overlapping_array_and_unequal_ring_spec():
    group = array("contact_array")
    group["pitch_xy"] = [5.0, 30.0]
    assert states(audit(group, array_geometry(group)))["nonoverlapping_members"] == "fail"
    group = dict(
        id="r",
        kind="closed_ring",
        outer_xyxy=[0.0, 0.0, 80.0, 60.0],
        hole_xyxy=[8.0, 10.0, 70.0, 50.0],
    )
    obj = dict(
        rect("r", group["outer_xyxy"]), primitive="rectangle_ring", hole_xyxy=group["hole_xyxy"]
    )
    assert states(audit(group, [obj]))["continuous_constant_width_ring"] == "fail"


def test_repeated_motif_keeps_cell_pitch_distinct_from_local_contact_pitch():
    group = array("contact_array")
    group.update(
        cols=6,
        motif_cols=3,
        cell_pitch=100.0,
        AA_material=None,
        AA_materials=[rect("a", [10.0, 10.0, 90.0, 100.0]), rect("b", [110.0, 10.0, 190.0, 100.0])],
    )
    objects = array_geometry(group)
    first_row = [o["outer_xyxy"][0] for o in objects if o["row"] == 0]
    assert first_row == [20.0, 50.0, 80.0, 120.0, 150.0, 180.0]
    result = states(audit(group, objects))
    assert result["shared_baselines_pitch_and_shape"] == "pass"
    assert result["AA_landing_enclosure"] == "pass"
    assert result["channel_exclusion"] == "unknown"
    assert states(audit(group, objects[1:]))["unique_complete_slot_inventory"] == "fail"


def test_cropped_dummy_centroids_and_bottom_edges_do_not_bias_camera_fit():
    from silicon_eye.group_constraints import build_group

    group = array()
    group.update(id="D01", rows=2, cols=4, source_frame="aa", observations=[])
    parent = dict(objects=[], aa_native_to_layout=np.eye(3).tolist())
    for row in range(2):
        for col in range(4):
            x, y = 20.0 + col * 30, 20.0 + row * 30
            bottom = y + 8 if row == 0 else y + 2
            obj = rect(f"{row}-{col}", [x, y, x + 8, bottom])
            parent["objects"].append(obj)
            points = [[x, y], [x + 8, y], [x + 8, bottom], [x, bottom]]
            group["observations"].append(
                dict(
                    id=obj["id"],
                    row=row,
                    col=col,
                    native_center_xy=[x + 4, (y + bottom) / 2],
                    native_outline_xy=points,
                    clipped_source_bottom=bool(row),
                    split="holdout" if col == 1 else "fit",
                )
            )
    limits = dict(
        dummy_holdout_median_px=0.01, dummy_holdout_p95_px=0.01, normalized_geometry_tolerance=0.01
    )
    fitted, objects, _, checks = build_group(group, parent, limits)
    assert fitted["pitch_xy"][1] == pytest.approx(30)
    assert fitted["origin_xy"][1] == pytest.approx(20)
    assert np.allclose(fitted["layout_to_native"], np.eye(3), atol=1e-6)
    evidence = next(c for c in checks if c["rule"] == "heldout_photo_observations")
    assert evidence["holdout_count"] == 6
    assert evidence["state"] == "pass"
    assert next(o for o in objects if o["row"] == 1)["outer_xyxy"][3] == pytest.approx(58)
