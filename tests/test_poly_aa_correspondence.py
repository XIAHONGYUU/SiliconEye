"""Explicit AA ownership, partial coverage and source-preserving working revisions."""

import copy

import pytest

from silicon_eye.aa_completion import source_polygon
from silicon_eye.geometry_reconstruction import object_polygon
from silicon_eye.poly_aa_correspondence import build_correspondences, propose_aa_row_alignment


def active(key, bounds):
    x, y, r, b = bounds
    return dict(
        id=key,
        primitive="rectangle",
        outer_xyxy=bounds,
        hole_xyxy=None,
        source_geometry=dict(outer_xy=[[x, y], [r, y], [r, b], [x, b]], holes_xy=[]),
    )


def sample():
    inventory = dict(
        objects=[
            dict(id=k, native_outline=[[1, 1], [3, 1], [3, 9], [1, 9]], status="candidate")
            for k in ["p0", "p1", "wide"]
        ]
    )
    aa = dict(objects=[active("A", [10, 20, 70, 40])])
    settings = dict(
        relative_budgets=dict(
            gate_width_px=4, poly_extension_px=3, lateral_margin_px=4, min_intergate_gap_px=2
        ),
        relations=[
            dict(
                id="cell",
                scope="row",
                AA_object_id="A",
                poly_observation_ids=["p0", "p1"],
                slot_count=5,
                slot_indices=[2, 4],
                association_status="candidate",
            )
        ],
        unresolved=[dict(poly_observation_id="wide", AA_object_id=None)],
    )
    return inventory, aa, settings


def test_unseen_slots_do_not_invent_poly_and_all_sources_are_accounted_for():
    inventory, aa, settings = sample()
    before = copy.deepcopy((inventory, aa, settings))
    result = build_correspondences(inventory, aa, settings)
    assert (inventory, aa, settings) == before
    assert result["assigned_candidates"] == 2
    assert result["unobserved_slots"] == 3
    assert [o["source_poly_id"] for o in result["objects"]] == ["p0", "p1"]
    assert result["geometry_counts"] == dict(PASS=2, CONFLICT=0, BLOCKED=0)
    assert result["unresolved"][0]["AA_object_id"] is None


def test_guard_conflict_keeps_the_explicit_identity_and_target():
    inventory, aa, settings = sample()
    aa["objects"].append(active("guard", [0, 15, 160, 18]))
    result = build_correspondences(inventory, aa, settings)
    assert result["geometry_counts"]["CONFLICT"] == 2
    assert all(o["AA_object_id"] == "A" for o in result["objects"])
    assert all(
        o["geometry_check"]["non_target_AA_intersections"][0]["AA_object_id"] == "guard"
        for o in result["objects"]
    )


def test_missing_duplicate_and_outside_slot_accounting_fail():
    inventory, aa, settings = sample()
    settings["unresolved"] = []
    with pytest.raises(ValueError, match="Unaccounted"):
        build_correspondences(inventory, aa, settings)
    inventory, aa, settings = sample()
    settings["relations"] *= 2
    with pytest.raises(ValueError, match="multiply assigned"):
        build_correspondences(inventory, aa, settings)
    inventory, aa, settings = sample()
    settings["relations"][0]["slot_indices"] = [2, 5]
    with pytest.raises(ValueError, match="slot accounting"):
        build_correspondences(inventory, aa, settings)


def test_aa_working_row_revision_keeps_native_evidence_and_reference_exact():
    aa = dict(objects=[active("A", [10, 20, 70, 40]), active("B", [80, 15, 140, 35])])
    before = copy.deepcopy(aa)
    revised, changes = propose_aa_row_alignment(
        aa,
        [
            dict(
                reference_AA_id="A",
                AA_object_ids=["A", "B"],
                evidence="same row independent of gate conflict",
            )
        ],
    )
    assert aa == before and revised["objects"][0] == aa["objects"][0]
    assert len(changes) == 1 and changes[0]["AA_object_id"] == "B"
    assert object_polygon(revised["objects"][1]).bounds == (80, 20, 140, 40)
    assert source_polygon(revised["objects"][1], revised).equals_exact(
        source_polygon(aa["objects"][1], aa), 1e-8
    )
