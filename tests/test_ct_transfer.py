"""Transfer must preserve reviewed state and only regularize observed evidence."""

import copy
import json
from pathlib import Path

import pytest

from silicon_eye.ct_transfer import check_protected, fit_observed_row

ROOT = Path(__file__).resolve().parents[1]


def observation(key, x, y=20):
    return dict(
        id=key,
        evidence_tier="compact_shape",
        source_observation=dict(source_native_center_xy=[x, y], peak_gray=230, local_residual=30),
    )


def row_spec(axis=0):
    return dict(
        id="T",
        axis=axis,
        source_roi=[0, 0, 50, 50],
        source_origin=10,
        source_pitch=10,
        source_fit_tolerance=2,
        layout_origin=[10, 20],
        layout_pitch=10,
        material="AA",
        target="A",
        min_gray=205,
        min_residual=16,
    )


def test_missing_observation_is_not_filled_by_grid_rule():
    prior = dict(objects=[observation("s0", 10), observation("s2", 30)])
    original = copy.deepcopy(prior)
    proposed, report = fit_observed_row(prior, row_spec(), dict(square_side=5))
    assert len(proposed) == 2 and report["unobserved_slots"] == [1]
    assert [o["column"] for o in proposed] == [0, 2]
    assert prior == original


def test_duplicate_peak_and_off_lattice_observation_stay_in_exclusion_ledger():
    prior = dict(
        objects=[
            observation("best", 10),
            observation("alternate", 10.8),
            observation("off", 15),
            observation("next", 20),
        ]
    )
    proposed, report = fit_observed_row(prior, row_spec(), dict(square_side=5))
    assert len(proposed) == 2
    assert {x["source_id"] for x in report["exclusions_not_deleted_evidence"]} == {
        "alternate",
        "off",
    }
    assert len(prior["objects"]) == 4


def test_vertical_rows_preserve_column_and_row_semantics():
    prior = dict(objects=[observation("s0", 20, 10), observation("s1", 20, 20)])
    proposed, _ = fit_observed_row(prior, row_spec(1), dict(square_side=5))
    assert [o["column"] for o in proposed] == [0, 0]
    assert [o["row"] for o in proposed] == [0, 1]
    assert [o["layout_center"][0] for o in proposed] == [10, 10]


def test_no_supported_observations_fail_instead_of_empty_success():
    with pytest.raises(ValueError, match="No source-supported"):
        fit_observed_row(dict(objects=[]), row_spec(), dict(square_side=5))


def test_real_53_reviewed_records_are_protected_from_renewed_candidate_work():
    contacts = json.loads((ROOT / "benchmarks/ct-right6-reviewed-v5/model-v1.json").read_text())[
        "objects"
    ]
    materials = json.loads(
        (ROOT / "benchmarks/ct-right6-reviewed-v5/material-model-v1.json").read_text()
    )
    working = copy.deepcopy(contacts) + [{"id": "new-candidate"}]
    check_protected(working, materials, contacts, materials)
    assert len(contacts) == 53
    working[0]["layout_center"][0] += 1
    with pytest.raises(ValueError, match="contact records"):
        check_protected(working, materials, contacts, materials)
    changed = copy.deepcopy(materials)
    changed["objects"][0]["layout_outline"][0][0] += 1
    with pytest.raises(ValueError, match="material records"):
        check_protected(contacts, changed, contacts, materials)


def test_profile_detector_requires_actual_peaks_and_preserves_missing_sites():
    import numpy as np

    from silicon_eye.ct_transfer import profile_observations

    row = row_spec()
    row.update(source_roi=[0, 0, 70, 12], sigma=1, min_gray=120, min_residual=10)
    image = np.full((12, 70), 150, dtype=np.uint8)
    assert profile_observations(image, row)["objects"] == []
    image[:, 9:12] = 240
    image[:, 29:32] = 240
    measured = profile_observations(image, row)
    proposed, fit = fit_observed_row(measured, row, dict(square_side=5))
    assert len(proposed) == 2
    assert fit["unobserved_slots"] == [1]
    assert [o["source_evidence"]["native_center"][0] for o in proposed] == [10, 30]


def revision_fixture():
    root = ROOT / "benchmarks"
    before = json.loads((root / "ct-transfer-v1/model-v1.json").read_text())["objects"]
    material = json.loads((root / "ct-right6-reviewed-v5/material-model-v1.json").read_text())
    after = []
    for old in before:
        if old["family"] in ["RING-TOP", "RING-LEFT"]:
            continue
        obj = copy.deepcopy(old)
        if obj["family"] == "RIGHT6-GATE":
            obj["layout_center"][1] -= 5
            obj["layout_outline"] = [[x, y - 5] for x, y in obj["layout_outline"]]
        after.append(obj)
    return before, after, material


def test_scoped_revision_blocks_source_or_previously_approved_contact_changes():
    from silicon_eye.ct_transfer import check_scoped_revision

    before, after, material = revision_fixture()
    for index, field in [(0, "layout_center"), (42, "source_evidence")]:
        changed = copy.deepcopy(after)
        if field == "layout_center":
            changed[index][field][0] += 1
        else:
            changed[index][field]["native_center"][0] += 1
        with pytest.raises(ValueError, match="Unauthorized contact"):
            check_scoped_revision(
                before,
                changed,
                material,
                material,
                {"RIGHT6-GATE": [0, -5]},
                ["RING-TOP", "RING-LEFT"],
            )


def test_review_revision_preserves_baseline_and_rejects_unrelated_material_change():
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union

    from silicon_eye.ct_transfer import check_scoped_revision

    before, after, material = revision_fixture()
    original = copy.deepcopy(material)
    changed = copy.deepcopy(material)
    common = next(o for o in changed["objects"] if o["id"] == "POLY-RIGHT6-COMMON")
    merged = unary_union(
        [Polygon(o["layout_outline"]) for o in common["gate_fingers"]]
        + [box(1407, 1500, 1560, 1507)]
    )
    common["layout_outline"] = [list(xy) for xy in list(merged.exterior.coords)[:-1]]
    assert (
        check_scoped_revision(
            before, after, material, changed, {"RIGHT6-GATE": [0, -5]}, ["RING-TOP", "RING-LEFT"]
        )
        == 72
    )
    assert material == original
    changed["AA_objects"][0]["id"] += "-unauthorized"
    with pytest.raises(ValueError, match="Unauthorized material"):
        check_scoped_revision(
            before, after, material, changed, {"RIGHT6-GATE": [0, -5]}, ["RING-TOP", "RING-LEFT"]
        )


def test_local_spacing_tracking_handles_slow_drift_without_filling_missing_peak():
    row = row_spec()
    row.update(
        track_local_spacing=True,
        source_roi=[0, 0, 100, 50],
        inspection_slot_range=[0, 6],
        source_fit_tolerance=4,
    )
    prior = dict(objects=[observation(str(i), x) for i, x in enumerate([10, 21, 33, 57, 69])])
    proposed, report = fit_observed_row(prior, row, dict(square_side=5))
    assert [o["column"] for o in proposed] == [0, 1, 2, 4, 5]
    assert report["unobserved_slots"] == [3, 6]
    assert report["source_assignment_mode"] == "local_observed_spacing"


def test_profile_path_follows_sloped_band_and_retains_native_peak_positions():
    import cv2
    import numpy as np

    from silicon_eye.ct_transfer import profile_observations

    im = np.full((90, 90), 80, np.uint8)
    for x in [20, 40, 60]:
        cv2.circle(im, (x, x), 3, 240, -1)
    row = row_spec()
    row.update(
        source_roi=[5, 5, 80, 80],
        source_path=[[10, 10], [75, 75]],
        band_half_width=4,
        sigma=1,
        min_gray=100,
        min_residual=10,
    )
    peaks = profile_observations(im, row)["objects"]
    assert len(peaks) == 3
    for obj, x in zip(peaks, [20, 40, 60], strict=True):
        xy = obj["source_observation"]["source_native_center_xy"]
        assert abs(xy[0] - x) <= 1 and abs(xy[1] - x) <= 3
    row["source_path"] = [[10, 10], [95, 95]]
    with pytest.raises(ValueError, match="leaves source image"):
        profile_observations(im, row)


def test_new_extension_cannot_move_any_of_130_accepted_contacts_or_materials():
    accepted = json.loads((ROOT / "benchmarks/ct-transfer-revision-v2/model-v1.json").read_text())
    materials = json.loads(
        (ROOT / "benchmarks/ct-transfer-revision-v2/material-model-v1.json").read_text()
    )
    working = copy.deepcopy(accepted["objects"])
    assert len(working) == 130
    check_protected(working, materials, accepted["objects"], materials)
    working[-1]["layout_outline"][0][1] += 1
    with pytest.raises(ValueError, match="contact records"):
        check_protected(working, materials, accepted["objects"], materials)


def test_working_parent_is_retained_without_promoting_its_geometry_approval(tmp_path):
    from silicon_eye.ct_transfer import run

    spec = json.loads((ROOT / "benchmarks/ct-middle-mos-v1/spec-v1.json").read_text())
    spec.update(families=[], rows=[], profile_rows=[], cases=[])
    for key, ref in spec["inputs"].items():
        source = ROOT / ref["path"]
        if key == "photo":
            ref["path"] = str(source)
        else:
            destination = tmp_path / f"{key}.json"
            destination.write_bytes(source.read_bytes())
            ref["path"] = destination.name
    request = tmp_path / "spec.json"
    request.write_text(json.dumps(spec))
    report = run(tmp_path, request, tmp_path / "valid")
    retained = json.loads((tmp_path / spec["inputs"]["retained_contacts"]["path"]).read_text())
    exported = json.loads((tmp_path / "valid/model.json").read_text())
    assert exported["objects"] == retained["objects"]
    assert report["previously_accepted_contact_count"] == 130
    assert report["retained_working_geometry_count"] == 661
    assert report["new_contact_count"] == 0

    retained["objects"][0]["layout_center"][0] += 1
    bad_parent = tmp_path / "bad-parent.json"
    bad_parent.write_text(json.dumps(retained))
    from silicon_eye.geometry_reconstruction import digest

    spec["inputs"]["retained_contacts"] = dict(path=str(bad_parent), sha256=digest(bad_parent))
    request.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="Protected reviewed contact records changed"):
        run(tmp_path, request, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_review_unknown_grid_is_explicitly_not_contact_evidence():
    from silicon_eye.ct_transfer import review_unknown_sites

    spec = row_spec()
    sites = review_unknown_sites([spec], [dict(id="T", unobserved_slots=[1])], dict(square_side=5))
    assert len(sites) == 1
    assert sites[0]["status"] == "inspection_slot_unknown_not_a_contact"
    assert "source_evidence" not in sites[0]
    assert "layer" not in sites[0]
    assert sites[0]["layout_outline"] == [[17.5, 17.5], [22.5, 17.5], [22.5, 22.5], [17.5, 22.5]]


def test_human_confirmation_preserves_vertical_slot_semantics_and_optical_unknowns():
    from silicon_eye.ct_joint_reconstruction import promote_confirmed_slots

    original = dict(
        id="old",
        family="vertical",
        column=0,
        row=0,
        AA_target="A",
        landing_material="AA",
        layer="CT",
        source_evidence=dict(native_center=[10, 10], supported=True),
    )
    parent = dict(
        objects=[original],
        unresolved_slots=[
            dict(
                family="vertical",
                slot=3,
                axis=1,
                layout_center=[20, 50],
                estimated_native_center=[10, 40],
            )
        ],
    )
    review = dict(confirmed_slots=[dict(family="vertical", slot=3, contact_id="human3")])
    result = promote_confirmed_slots(
        parent["objects"],
        parent,
        review,
        dict(path="review.json", sha256="locked-review"),
        dict(square_side=5),
    )
    assert result[0] == original
    added = result[-1]
    assert (added["column"], added["row"]) == (0, 3)
    assert added["AA_target"] == "A" and added["landing_material"] == "AA"
    assert added["source_evidence"]["evidence_type"] == "human_confirmation"
    assert added["source_evidence"]["algorithm_detected"] is False
    assert "peak_gray" not in added["source_evidence"]
    assert "residual" not in added["source_evidence"]


def test_reviewed_translation_preserves_source_and_unrelated_records():
    from silicon_eye.ct_transfer import translate_reviewed_geometry

    contacts = [
        dict(
            id="C",
            layout_center=[4, 8],
            layout_outline=[[2, 6], [6, 10]],
            source_evidence=dict(native_center=[130, 170], supported=True),
        ),
        dict(id="KEEP", layout_center=[30, 40]),
    ]
    material = dict(
        AA_objects=[
            dict(
                id="A",
                outer_xy=[[0, 10], [10, 20]],
                outer_xyxy=[0, 10, 10, 20],
                holes_xy=[],
                hole_xyxy=None,
                layout_observation_bbox_xywh=[0, 10, 10, 10],
            )
        ],
        objects=[
            dict(id="P", layout_outline=[[2, 3], [6, 25]], source_native_bbox=[30, 40, 50, 60])
        ],
    )
    original = copy.deepcopy((contacts, material))
    changes = [
        dict(layer=layer, id=key, delta_xy=[0, 7])
        for layer, key in [("AA", "A"), ("POLY", "P"), ("CT", "C")]
    ]
    after, revised, ledger = translate_reviewed_geometry(
        contacts, material, changes, dict(local_translations=changes)
    )
    assert (contacts, material) == original  # Immutable parent input.
    assert after[0]["layout_center"] == [4, 15]
    assert after[0]["source_evidence"] == contacts[0]["source_evidence"]
    assert after[1] == contacts[1]
    assert revised["AA_objects"][0]["outer_xyxy"] == [0, 17, 10, 27]
    assert revised["AA_objects"][0]["layout_observation_bbox_xywh"] == [0, 10, 10, 10]
    assert revised["objects"][0]["source_native_bbox"] == [30, 40, 50, 60]
    assert ledger[2]["before"] == contacts[0] and ledger[2]["after"] == after[0]


@pytest.mark.parametrize(
    "changes,review",
    [
        ([dict(layer="CT", id="C", delta_xy=[0, 7])], {}),
        ([dict(layer="CT", id="MISSING", delta_xy=[0, 7])], None),
        ([dict(layer="CT", id="C", delta_xy=[0, float("nan")])], None),
    ],
)
def test_reviewed_translation_rejects_unapproved_missing_or_invalid_target(changes, review):
    from silicon_eye.ct_transfer import translate_reviewed_geometry

    if review is None:
        review = dict(local_translations=changes)
    with pytest.raises(ValueError):
        translate_reviewed_geometry(
            [dict(id="C")], dict(AA_objects=[], objects=[]), changes, review
        )


def test_local_spacing_ignores_other_photo_regions():
    row = row_spec()
    row.update(track_local_spacing=True, source_pitch=10, source_fit_tolerance=2)
    local = [observation("a", 10), observation("b", 20), observation("c", 40)]
    expected, fit = fit_observed_row(dict(objects=local), row, dict(square_side=5))
    # Other rows interleave in x; none may reset this row's phase or occupy its missing slot.
    unrelated = [observation("outside", 14, y=90), observation("outside2", 29, y=90)]
    actual, actual_fit = fit_observed_row(dict(objects=local + unrelated), row, dict(square_side=5))
    assert actual == expected
    assert actual_fit["occupied_slots"] == fit["occupied_slots"] == [0, 1, 3]
    assert actual_fit["unobserved_slots"] == [2]


def test_scoped_record_revision_preserves_unrelated_records_and_original_evidence():
    from silicon_eye.ct_transfer import apply_reviewed_record_changes

    parent = [
        dict(id="C1", layout_center=[10, 20], source_evidence=dict(native_center=[3, 4])),
        dict(id="C2", layout_center=[40, 50]),
    ]
    after = copy.deepcopy(parent[0])
    after["layout_center"] = [13, 20]
    changes = [dict(id="C1", before=parent[0], after=after)]
    output = apply_reviewed_record_changes(parent, changes, ["C1"], ["source_evidence"])
    assert output[0] == after and output[1] == parent[1]
    assert parent[0]["layout_center"] == [10, 20]
    # Human permission to adjust the design must not rewrite the photographed location.
    after["source_evidence"]["native_center"][0] = 9
    with pytest.raises(ValueError, match="source evidence"):
        apply_reviewed_record_changes(parent, changes, ["C1"], ["source_evidence"])


def test_scoped_record_revision_rejects_stale_parent_or_other_target():
    from silicon_eye.ct_transfer import apply_reviewed_record_changes

    parent = [dict(id="A", outer_xyxy=[0, 0, 20, 20])]
    changes = [dict(id="A", before=parent[0], after=dict(id="A", outer_xyxy=[0, 0, 26, 20]))]
    with pytest.raises(ValueError, match="outside human review"):
        apply_reviewed_record_changes(parent, changes, ["B"])
    stale = copy.deepcopy(parent)
    stale[0]["outer_xyxy"][2] = 21
    with pytest.raises(ValueError, match="Stale"):
        apply_reviewed_record_changes(stale, changes, ["A"])


def test_later_local_revision_preserves_existing_material_aliases(tmp_path):
    """An unrelated POLY patch must not lose a previously merged AA identity."""
    import hashlib

    from PIL import Image

    from silicon_eye.ct_transfer import run_local_review_revision

    budget = dict(square_side=5, min_gap_px=3, enclosure_px=1, channel_clearance_px=1)
    active = dict(id="A", outer_xyxy=[0, 0, 100, 100], material_aliases=["OLD-A"])
    poly = dict(id="P", layout_outline=[[60, 60], [70, 60], [70, 70], [60, 70]])
    added_poly = dict(id="P2", layout_outline=[[80, 80], [90, 80], [90, 90], [80, 90]])
    contact = dict(
        id="C", family="F", column=0, row=0, AA_target="A",
        layout_outline=[[10, 10], [15, 10], [15, 15], [10, 15]],
        source_evidence=dict(native_center=[12, 12], supported=True),
    )
    inputs = {}
    values = dict(
        materials=dict(objects=[poly], AA_objects=[active]),
        contacts=dict(objects=[contact]),
        human_review=dict(authorized_material_ids=["P2"], authorized_contact_ids=[],
                          authorized_new_contact_ids=[]),
        new_contacts=dict(objects=[]), unknown_sites=dict(sites=[]),
        parent_spec=dict(budget=budget),
    )
    for key, value in values.items():
        path = tmp_path / (key + ".json")
        path.write_text(json.dumps(value))
        inputs[key] = dict(path=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    photo = tmp_path / "photo.png"
    Image.new("RGB", (100, 100)).save(photo)
    inputs["photo"] = dict(path=photo.name, sha256=hashlib.sha256(photo.read_bytes()).hexdigest())
    spec = dict(
        inputs=inputs, budget=budget,
        material_changes=dict(objects=[dict(id="P2", before=None, after=added_poly)]),
        contact_changes=[], cases=[], review_title="Local revision", review_notes="Scoped patch",
    )
    output = tmp_path / "output"
    run_local_review_revision(tmp_path, spec, output)
    result = json.loads((output / "material-model.json").read_text())
    assert result["AA_objects"] == [active]
    assert result["local_material_revision"]["alias_map"] == {"OLD-A": "A"}
    assert json.loads((output / "model.json").read_text())["objects"] == [contact]


def test_source_correction_preserves_design_and_appends_original_observation():
    from silicon_eye.ct_transfer import apply_source_correspondence_corrections

    parent = [
        dict(
            id="C",
            POLY_target="P",
            layout_center=[10, 20],
            source_frame="poly",
            source_evidence=dict(native_center=[30, 40], supported=True),
        ),
        dict(id="KEEP", source_evidence=dict(native_center=[50, 60], supported=True)),
    ]
    original = copy.deepcopy(parent)
    change = dict(
        id="C",
        before_source_evidence=copy.deepcopy(parent[0]["source_evidence"]),
        after_source_evidence=dict(
            native_center=[30, 70], supported=True, source_roi=[25, 65, 35, 75]
        ),
        reason="human terminal-side decision followed by independent optical reinspection",
    )
    ref = dict(path="review.json", sha256="review-hash")
    result = apply_source_correspondence_corrections(parent, [change], ["C"], ref)
    assert parent == original and result[1] == parent[1]
    assert result[0]["layout_center"] == [10, 20] and result[0]["POLY_target"] == "P"
    assert result[0]["source_frame"] == "poly"
    assert result[0]["source_evidence"]["native_center"] == [30, 70]
    assert result[0]["source_correspondence_history"] == [
        dict(
            before=parent[0]["source_evidence"],
            after=change["after_source_evidence"],
            reason=change["reason"],
            review_ref=ref,
        )
    ]
    second = dict(
        change,
        before_source_evidence=copy.deepcopy(result[0]["source_evidence"]),
        after_source_evidence=dict(native_center=[31, 70], supported=True),
    )
    final = apply_source_correspondence_corrections(result, [second], ["C"], ref)
    assert len(final[0]["source_correspondence_history"]) == 2
    assert (
        final[0]["source_correspondence_history"][0]
        == result[0]["source_correspondence_history"][0]
    )


@pytest.mark.parametrize(
    "failure", ["scope", "stale", "duplicate", "unsupported", "nonfinite", "source_alias"]
)
def test_source_correction_rejects_unscoped_stale_or_unsupported_evidence(failure):
    from silicon_eye.ct_transfer import apply_source_correspondence_corrections

    parent = [dict(id="C", source_evidence=dict(native_center=[10, 20], supported=True))]
    change = dict(
        id="C",
        before_source_evidence=copy.deepcopy(parent[0]["source_evidence"]),
        after_source_evidence=dict(native_center=[10, 30], supported=True),
        reason="observed",
    )
    allowed, changes = ["C"], [change]
    if failure == "scope":
        allowed = []
    elif failure == "stale":
        change["before_source_evidence"]["native_center"] = [0, 0]
    elif failure == "duplicate":
        changes.append(change)
    elif failure == "unsupported":
        change["after_source_evidence"]["supported"] = False
    elif failure == "source_alias":
        change["after_source_evidence"]["source_native_center_xy"] = [10, 20]
    else:
        change["after_source_evidence"]["native_center"] = [float("nan"), 30]
    with pytest.raises(ValueError):
        apply_source_correspondence_corrections(parent, changes, allowed, {})


def test_access_inventory_keeps_internal_diffusion_without_inventing_contacts():
    from silicon_eye.ct_transfer import audit_terminal_access

    material = dict(
        AA_objects=[dict(id="A", primitive="rectangle", outer_xyxy=[0, 0, 60, 40])],
        objects=[
            dict(id="P1", AA_target="A", layout_outline=[[15, -8], [20, -8], [20, 45], [15, 45]]),
            dict(id="P2", AA_target="A", layout_outline=[[40, -8], [45, -8], [45, 45], [40, 45]]),
        ],
    )
    contacts = [dict(id="C", AA_target="A", layout_outline=[[3, 10], [8, 10], [8, 15], [3, 15]])]
    original = copy.deepcopy((material, contacts))
    report = audit_terminal_access(contacts, material)
    assert report["diffusion_region_count"] == 3
    assert report["diffusion_regions_without_direct_CT"] == 2
    assert report["diffusion_regions"][1]["status"] == "no_direct_CT_evidence"
    assert report["status"] == "access_inventory_not_physical_completion_gate"
    assert (material, contacts) == original


def test_shared_poly_access_requires_the_declared_bridge_to_reach_the_finger():
    from silicon_eye.ct_transfer import audit_terminal_access

    material = dict(
        AA_objects=[],
        objects=[
            dict(id="P1", layout_outline=[[10, -8], [15, -8], [15, 40], [10, 40]]),
            dict(id="P2", layout_outline=[[30, -8], [35, -8], [35, 40], [30, 40]]),
            dict(id="P3", layout_outline=[[80, -8], [85, -8], [85, 40], [80, 40]]),
            dict(
                id="BUS",
                member_POLY_ids=["P1", "P2", "P3"],
                layout_outline=[[10, -12], [35, -12], [35, -6], [10, -6]],
            ),
        ],
    )
    report = audit_terminal_access([dict(id="C", POLY_target="BUS")], material)
    by_id = {o["material_id"]: o for o in report["POLY_materials"]}
    assert by_id["P1"]["contact_ids"] == ["C"]
    assert by_id["P2"]["contact_ids"] == ["C"]
    assert not by_id["P3"]["contact_ids"]


def test_access_inventory_does_not_borrow_a_contact_from_another_active_id():
    from silicon_eye.ct_transfer import audit_terminal_access

    material = dict(
        AA_objects=[dict(id="A", primitive="rectangle", outer_xyxy=[0, 0, 40, 40])],
        objects=[
            dict(id="P", AA_target="A", layout_outline=[[15, -8], [20, -8], [20, 45], [15, 45]])
        ],
    )
    contact = dict(id="OTHER", AA_target="B", layout_outline=[[3, 10], [8, 10], [8, 15], [3, 15]])
    report = audit_terminal_access([contact], material)
    assert report["diffusion_regions_without_direct_CT"] == 2
