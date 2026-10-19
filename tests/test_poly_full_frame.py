"""Check reviewed geometry retention and failure paths of candidate array assembly."""

import copy

import pytest

from silicon_eye.poly_full_frame import build_geometry


def group(gid="G", count=3):
    return dict(
        id=gid,
        count=count,
        first_native_outline=[[10, 10], [14, 10], [16, 30], [12, 30]],
        last_native_outline=[[30, 8], [34, 8], [36, 28], [32, 28]],
        layout_y=[9, 30],
        approved_slots={},
        kind="MOS_gate_body",
        body_scope="full_body_candidate",
        method="AI_observation",
    )


def test_reviewed_shape_survives_array_expansion_without_shrinking_to_core():
    g = group()
    g["approved_slots"] = {"1": "already_reviewed"}
    reviewed = dict(
        id="already_reviewed",
        approval="human",
        custom_unknown="preserved",
        native_outline=[[21, 10], [24, 10], [26, 29], [23, 29]],
        layout_outline=[[22, 9], [25, 9], [25, 30], [22, 30]],
    )
    before = copy.deepcopy(reviewed)
    result, overlaps = build_geometry({"groups": [g]}, {"objects": [reviewed]})
    assert result[0] == before
    assert reviewed == before
    assert len(result) == 3
    assert overlaps == []
    new = [o for o in result if o["id"] != "already_reviewed"]
    assert [o["native_outline"] for o in new] == [
        g["first_native_outline"],
        g["last_native_outline"],
    ]
    assert all(o["status"] == "AI_candidate_not_human_confirmed" for o in new)


def test_overlapping_groups_are_reported_instead_of_silently_merged():
    result, overlaps = build_geometry({"groups": [group("A"), group("B")]}, {"objects": []})
    assert len(result) == 6
    assert len(overlaps) == 3


def test_invalid_repetition_or_unavailable_approved_object_is_rejected():
    g = group(count=10)
    with pytest.raises(ValueError, match="merge adjacent"):
        build_geometry({"groups": [g]}, {"objects": []})
    g = group()
    g["approved_slots"] = {"1": "missing"}
    with pytest.raises(ValueError, match="Missing"):
        build_geometry({"groups": [g]}, {"objects": []})


def test_matching_rows_share_layout_columns_without_rewriting_photo_offsets():
    upper, lower = group("U"), group("L")
    for key in ["first_native_outline", "last_native_outline"]:
        lower[key] = [[x + 4, y + 40] for x, y in lower[key]]
    lower["layout_y"] = [49, 70]
    spec = dict(
        groups=[upper, lower],
        cross_row_alignment_sets=[dict(id="MATCH", groups=["U", "L"], reference="U")],
    )
    objects, overlaps = build_geometry(spec, {"objects": []})
    assert overlaps == []
    for upper_obj, lower_obj in zip(objects[:3], objects[3:], strict=True):
        assert [p[0] for p in upper_obj["layout_outline"]] == [
            p[0] for p in lower_obj["layout_outline"]
        ]
        assert lower_obj["native_outline"][0][0] - upper_obj["native_outline"][0][0] == 4


def test_terminal_extension_is_kept_as_geometry_hypothesis_without_ct_assignment():
    g = group(count=2)
    g["end_extension"] = dict(length_px=3, width_factor=1, side="top", status="candidate")
    objects, overlaps = build_geometry({"groups": [g]}, {"objects": []})
    assert overlaps == []
    for obj in objects:
        assert len(obj["layout_outline"]) == 4
        assert min(p[1] for p in obj["layout_outline"]) < min(
            p[1] for p in obj["body_layout_outline"]
        )
        assert obj["terminal_shape_status"] == "candidate"
        assert obj["terminal_routing"] == "material_extension_candidate_no_CT_or_net_assignment"


def test_source_projection_repair_does_not_change_parent_locked_material_shape():
    g = group()
    old, _ = build_geometry({"groups": [g]}, {"objects": []})
    changed = copy.deepcopy(g)
    changed["layout_lock_from_parent"] = True
    for key in ["first_native_outline", "last_native_outline"]:
        for p in changed[key]:
            p[0] += 2
    new, _ = build_geometry({"groups": [changed]}, {"objects": []}, parent={"objects": old})
    for before, after in zip(old, new, strict=True):
        assert before["layout_outline"] == after["layout_outline"]
        assert before["native_outline"] != after["native_outline"]


def test_unreviewed_widened_templates_are_rejected_and_reviewed_scoped_geometry_is_frozen():
    g = group(count=2)
    g["end_extension"] = dict(length_px=3, width_factor=1.5, side="top", status="candidate")
    with pytest.raises(ValueError, match="Widened MOS templates withdrawn"):
        build_geometry({"groups": [g]}, {"objects": []})
    clean = group(count=2)
    parent, _ = build_geometry({"groups": [clean]}, {"objects": []})
    changed = copy.deepcopy(clean)
    changed["freeze_geometry_from_parent"] = True
    changed["approval_ref"] = {"path": "review.json", "sha256": "review_digest"}
    for point in changed["first_native_outline"]:
        point[0] += 3
    result, _ = build_geometry({"groups": [changed]}, {"objects": []}, parent={"objects": parent})
    for old, new in zip(parent, result, strict=True):
        assert old["native_outline"] == new["native_outline"]
        assert old["layout_outline"] == new["layout_outline"]
        assert "approval" in new
