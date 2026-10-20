"""Failed geometry or unsupported observations must never reach CT reconstruction export."""

import copy
import json
from pathlib import Path

import pytest

from silicon_eye.ct_joint_reconstruction import audit_contacts, require_exportable

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    model = dict(
        AA_objects=[dict(id="A", outer_xyxy=[0, 0, 100, 100])],
        objects=[dict(id="P", layout_outline=[[45, 0], [55, 0], [55, 100], [45, 100]])],
    )
    objects = []
    for row, y in enumerate([15, 30, 45]):
        objects.append(
            dict(
                id=f"C{row}",
                family="F",
                column=0,
                row=row,
                AA_target="A",
                layout_center=[20, y],
                layout_outline=[[17.5, y - 2.5], [22.5, y - 2.5], [22.5, y + 2.5], [17.5, y + 2.5]],
                source_evidence=dict(supported=True, native_center=[20, y]),
            )
        )
    budget = dict(square_side=5, min_gap_px=3, enclosure_px=1, channel_clearance_px=1)
    return model, objects, budget


def move(obj, dx=0, dy=0):
    obj["layout_outline"] = [[x + dx, y + dy] for x, y in obj["layout_outline"]]


def test_joint_gate_accepts_straight_supported_family_without_changing_baseline():
    model, objects, budget = fixture()
    old = copy.deepcopy(model)
    report = require_exportable(objects, model, budget)
    assert report["status"] == "PASS" and report["minimum_edge_gap_px"] == 10
    assert model == old


@pytest.mark.parametrize("offset", [0, 7, 12, 15])
def test_indexed_minimum_gap_matches_all_pairs_including_duplicate_shapes(offset):
    from shapely.geometry import Polygon

    model, objects, budget = fixture()
    move(objects[0], dy=offset)
    shapes = [Polygon(o["layout_outline"]) for o in objects]
    expected = min(a.distance(b) for i, a in enumerate(shapes) for b in shapes[i + 1 :])
    assert audit_contacts(objects, model, budget)["minimum_edge_gap_px"] == expected


def test_single_contact_has_no_neighbour_gap():
    model, objects, budget = fixture()
    assert audit_contacts(objects[:1], model, budget)["minimum_edge_gap_px"] is None


@pytest.mark.parametrize("offset", [12, 8])
def test_overlap_and_insufficient_gap_both_block_export(offset):
    model, objects, budget = fixture()
    move(objects[0], dy=offset)
    with pytest.raises(ValueError, match="export blocked"):
        require_exportable(objects, model, budget)
    assert audit_contacts(objects, model, budget)["min_gap_violations"]


def test_nonuniform_spacing_blocks_even_without_overlap():
    model, objects, budget = fixture()
    move(objects[-1], dy=2)
    report = audit_contacts(objects, model, budget)
    assert not report["positive_area_overlap_pairs"]
    assert any(e["reason"] == "row_pitch_not_uniform" for e in report["errors"])


def test_wandering_column_blocks_even_if_center_metadata_was_not_updated():
    model, objects, budget = fixture()
    move(objects[1], dx=2)
    assert any(
        e["reason"] == "row_or_column_not_straight"
        for e in audit_contacts(objects, model, budget)["errors"]
    )


@pytest.mark.parametrize(
    ("dx", "reason"), [(29, "channel_overlap_or_clearance_failed"), (-20, "AA_enclosure_failed")]
)
def test_material_landing_blocks_invalid_reconstruction(dx, reason):
    model, objects, budget = fixture()
    for o in objects:
        move(o, dx=dx)
    assert any(e["reason"] == reason for e in audit_contacts(objects, model, budget)["errors"])
    with pytest.raises(ValueError):
        require_exportable(objects, model, budget)


def test_unsupported_expected_slot_cannot_be_exported():
    model, objects, budget = fixture()
    objects[1]["source_evidence"]["supported"] = False
    with pytest.raises(ValueError, match="no_observed_source_support"):
        require_exportable(objects, model, budget)


def test_one_source_peak_cannot_be_used_as_two_contacts():
    model, objects, budget = fixture()
    objects[1]["source_evidence"]["native_center"] = objects[0]["source_evidence"]["native_center"]
    with pytest.raises(ValueError, match="source_peak_reused"):
        require_exportable(objects, model, budget)


def test_real_prior_observations_are_not_a_geometry_acceptance_baseline():
    from shapely.geometry import Polygon
    from shapely.strtree import STRtree

    old = json.loads((ROOT / "benchmarks/ct-reconstruction-v1/model-v1.json").read_text())
    shapes = [Polygon(o["layout_outline"]) for o in old["objects"]]
    tree = STRtree(shapes)
    overlap = sum(
        shapes[i].intersection(shapes[j]).area > 0
        for i, p in enumerate(shapes)
        for j in tree.query(p)
        if j > i
    )
    assert overlap == 21


def test_nonuniform_column_pitch_is_rejected():
    model, objects, budget = fixture()
    for col, o in enumerate(objects):
        o["row"] = 0
        o["column"] = col
        x, y = o["layout_center"]
        move(o, dx=[0, 10, 22][col], dy=15 - y)
    assert any(
        e["reason"] == "column_pitch_not_uniform"
        for e in audit_contacts(objects, model, budget)["errors"]
    )


def test_source_boundary_gate_rejects_shifted_family_with_correct_count():
    from silicon_eye.ct_joint_reconstruction import check_source_boundaries

    family = {
        "id": "F",
        "native_columns_at_first_row": [1164, 1195, 1227, 1258, 1289, 1320, 1351],
        "source_boundary_constraints": {
            "first_column_native_x_range": [1158, 1173],
            "last_column_native_x_range": [1345, 1361],
            "excluded_column_native_x_ranges": [[1135, 1152]],
        },
    }
    correct = [
        dict(family="F", column=i, source_evidence=dict(native_center=[x, 1220]))
        for i, x in enumerate(family["native_columns_at_first_row"])
    ]
    check_source_boundaries(correct, family)
    wrong = copy.deepcopy(correct)
    for obj, x in zip(wrong, [1143, 1164, 1195, 1227, 1258, 1289, 1320], strict=True):
        obj["source_evidence"]["native_center"][0] = x
    with pytest.raises(ValueError, match="Source boundary"):
        check_source_boundaries(wrong, family)


def test_correspondence_revision_preserves_all_design_slots():
    from silicon_eye.ct_joint_reconstruction import preserve_layout

    _, objects, _ = fixture()
    parent = dict(objects=copy.deepcopy(objects))
    changed = copy.deepcopy(objects)
    for o in changed:
        move(o, dy=1)
        o["source_evidence"]["native_center"][0] += 30
    result = preserve_layout(changed, parent)
    for new, old in zip(result, parent["objects"], strict=True):
        assert new["layout_outline"] == old["layout_outline"]
        assert new["layout_center"] == old["layout_center"]
        assert new["source_evidence"]["native_center"] != old["source_evidence"]["native_center"]
    with pytest.raises(ValueError, match="all contact slots"):
        preserve_layout(result[:-1], parent)


def common_gate_fixture():
    model = dict(
        AA_objects=[dict(id="A", outer_xyxy=[0, 0, 100, 100])],
        objects=[
            dict(id="P1", layout_outline=[[20, -5], [25, -5], [25, 105], [20, 105]], AA_target="A"),
            dict(id="P2", layout_outline=[[40, -5], [45, -5], [45, 105], [40, 105]], AA_target="A"),
            dict(
                id="OTHER", layout_outline=[[70, -5], [75, -5], [75, 105], [70, 105]], AA_target="A"
            ),
        ],
    )
    recipe = dict(
        id="COMMON",
        gate_ids=["P1", "P2"],
        bus_layout_bbox=[20, 101, 45, 112],
        unrelated_POLY_gap_px=3,
        native_bus_bbox=[0, 0, 1, 1],
    )
    return model, recipe


def test_common_gate_merge_preserves_finger_identity_and_unrelated_material():
    from shapely.geometry import Polygon

    from silicon_eye.ct_joint_reconstruction import apply_poly_connections

    model, recipe = common_gate_fixture()
    original = copy.deepcopy(model)
    working = apply_poly_connections(model, [recipe])
    assert model == original and working["AA_objects"] == model["AA_objects"]
    common = next(o for o in working["objects"] if o["id"] == "COMMON")
    assert len(common["gate_fingers"]) == 2
    assert working["POLY_material_aliases"] == {"P1": "COMMON", "P2": "COMMON"}
    assert next(o for o in working["objects"] if o["id"] == "OTHER") == model["objects"][-1]
    assert Polygon(common["layout_outline"]).is_valid
    assert Polygon(common["layout_outline"]).geom_type == "Polygon"


@pytest.mark.parametrize("bbox", [[20, 102, 30, 112], [20, 99, 45, 112], [20, 101, 73, 112]])
def test_invalid_bus_cannot_miss_fingers_touch_active_or_join_unrelated_poly(bbox):
    from silicon_eye.ct_joint_reconstruction import apply_poly_connections

    model, recipe = common_gate_fixture()
    recipe["bus_layout_bbox"] = bbox
    with pytest.raises(ValueError):
        apply_poly_connections(model, [recipe])


def test_poly_contacts_require_poly_enclosure_and_active_exclusion():
    from silicon_eye.ct_joint_reconstruction import apply_poly_connections

    model, recipe = common_gate_fixture()
    working = apply_poly_connections(model, [recipe])
    _, objects, budget = fixture()
    contact = objects[0]
    contact.update(landing_material="POLY", POLY_target="COMMON")
    move(contact, dx=10, dy=93)  # center (30,108), on the bus outside active
    assert audit_contacts([contact], working, budget)["status"] == "PASS"
    invalid = copy.deepcopy(contact)
    move(invalid, dx=22.5)
    assert any(
        e["reason"] == "POLY_enclosure_failed"
        for e in audit_contacts([invalid], working, budget)["errors"]
    )
    invalid = copy.deepcopy(contact)
    move(invalid, dx=-7.5, dy=-58)
    assert any(
        e["reason"] == "POLY_CT_over_active_or_clearance_failed"
        for e in audit_contacts([invalid], working, budget)["errors"]
    )


def test_real_gate_bus_addition_preserves_accepted_sd_contacts_and_unknown_slot():
    from silicon_eye.ct_joint_reconstruction import apply_poly_connections, build_poly_contacts

    spec = json.loads((ROOT / "benchmarks/ct-gate-bus-v4/spec-v1.json").read_text())
    model = json.loads((ROOT / spec["inputs"]["baseline"]["path"]).read_text())
    parent = json.loads((ROOT / spec["inputs"]["geometry_parent"]["path"]).read_text())
    prior = json.loads((ROOT / spec["inputs"]["prior_observations"]["path"]).read_text())
    original = copy.deepcopy(parent)
    working = apply_poly_connections(model, spec["poly_connections"])
    new = build_poly_contacts(prior, spec["poly_contact_rows"][0], spec["budget"])
    assert len(new) == 10 and not any(o["column"] == 1 for o in new)
    assert parent == original
    assert require_exportable(parent["objects"] + new, working, spec["budget"])["status"] == "PASS"
    assert (
        len(next(o for o in working["objects"] if o["id"] == "POLY-RIGHT6-COMMON")["gate_fingers"])
        == 6
    )


def test_accepted_contacts_are_retained_exactly_and_changed_sources_blocked():
    from silicon_eye.ct_joint_reconstruction import retain_accepted_records

    _, objects, _ = fixture()
    parent = dict(objects=copy.deepcopy(objects))
    regenerated = copy.deepcopy(objects)
    move(regenerated[0], dy=1)
    retained = retain_accepted_records(regenerated, parent)
    assert retained == parent["objects"]
    regenerated[0]["source_evidence"]["native_center"][0] += 1
    with pytest.raises(ValueError, match="Accepted source evidence changed"):
        retain_accepted_records(regenerated, parent)


def test_human_confirmation_promotes_only_the_reviewed_slot_without_faking_optical_support():
    from silicon_eye.ct_joint_reconstruction import promote_confirmed_slots

    _, objects, budget = fixture()
    parent = dict(
        objects=copy.deepcopy(objects),
        unresolved_slots=[
            dict(family="F", slot=3, layout_center=[20, 60], estimated_native_center=[20.2, 60.1])
        ],
    )
    review = dict(confirmed_slots=[dict(family="F", slot=3, contact_id="C-H01")])
    result = promote_confirmed_slots(objects, parent, review, {"path": "human-review.json"}, budget)
    assert result[:3] == objects and len(result) == 4
    support = result[-1]["source_evidence"]
    assert (
        support["evidence_type"] == "human_confirmation" and support["algorithm_detected"] is False
    )
    assert "peak_gray" not in support and "residual" not in support
    assert parent["objects"] == objects
    review["confirmed_slots"][0]["slot"] = 4
    with pytest.raises(ValueError, match="matching previously reviewed unknown"):
        promote_confirmed_slots(objects, parent, review, {}, budget)


def test_human_acceptance_cannot_rewrite_prior_contacts():
    from silicon_eye.ct_joint_reconstruction import promote_confirmed_slots

    _, objects, budget = fixture()
    parent = dict(objects=copy.deepcopy(objects), unresolved_slots=[])
    changed = copy.deepcopy(objects)
    move(changed[0], dx=1)
    with pytest.raises(ValueError, match="preserve all prior contact records"):
        promote_confirmed_slots(changed, parent, dict(confirmed_slots=[]), {}, budget)
