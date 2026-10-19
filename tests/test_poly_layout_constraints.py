"""Forward-layout repairs must satisfy AA relations without rewriting observations."""

import copy

import pytest
from shapely.geometry import Polygon, box

from silicon_eye.poly_layout_constraints import (
    audit_relative,
    fit_gate_rectangle,
    reconstruct_relative,
)


def case():
    guard = Polygon(
        [[-10, -10], [130, -10], [130, 110], [-10, 110]], [[[0, 0], [120, 0], [120, 100], [0, 100]]]
    )
    records = [
        dict(id="guard", polygon=guard, is_guard=True),
        dict(id="AA1", polygon=box(10, 20, 110, 40), is_guard=False),
        dict(id="AA2", polygon=box(10, 60, 110, 80), is_guard=False),
    ]
    settings = dict(
        families=[dict(groups=["U", "L"], gate_width_px=10)],
        row_AA_targets={"U": "AA1", "L": "AA2"},
        lateral_margin_px=8,
        min_intergate_gap_px=8,
        min_poly_extension_px=8,
        guard_clearance_px=3,
    )
    derived = []
    for gid, yy in [("U", -5), ("L", 50)]:
        for i in range(3):
            derived.append(
                dict(
                    group_id=gid,
                    group_index=i,
                    source_poly_id=f"{gid}{i}",
                    aa_native_outline=[[i, yy]],
                    joint_layout_outline=[
                        [20 + i * 40, yy],
                        [30 + i * 40, yy],
                        [30 + i * 40, yy + 20],
                        [20 + i * 40, yy + 20],
                    ],
                    aa_body_assignment_within_budget=False,
                )
            )
    return records, settings, derived


def test_reconstruction_repairs_missed_active_and_ring_intrusion_without_moving_aa():
    records, settings, original = case()
    before = copy.deepcopy(original)
    record_wkb = [r["polygon"].wkb for r in records]
    assert audit_relative(original, records, settings)["status"] == "FAIL"
    result = reconstruct_relative(original, records, settings)
    assert audit_relative(result, records, settings)["status"] == "PASS"
    assert original == before
    assert [r["polygon"].wkb for r in records] == record_wkb
    for upper, lower in zip(result[:3], result[3:], strict=True):
        assert [p[0] for p in upper["joint_layout_outline"]] == [
            p[0] for p in lower["joint_layout_outline"]
        ]
        assert upper["aa_native_outline"] == before[upper["group_index"]]["aa_native_outline"]


def test_impossible_clearance_does_not_pass_by_shortening_gate_or_editing_active():
    with pytest.raises(ValueError, match="Insufficient free space"):
        fit_gate_rectangle(box(10, 20, 30, 40), box(0, 15, 50, 45), 20, 10, 8, 3)


def test_overcrowded_count_is_rejected_instead_of_squeezing_gate_width():
    records, settings, derived = case()
    settings["families"][0]["gate_width_px"] = 40
    with pytest.raises(ValueError, match="cannot fit count"):
        reconstruct_relative(derived, records, settings)
