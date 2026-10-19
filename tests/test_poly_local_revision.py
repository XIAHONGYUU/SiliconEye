"""Local corrections must persist without changing adjacent or accepted geometry."""

import copy
import json

import cv2
import numpy as np
import pytest

from silicon_eye.geometry_reconstruction import digest
from silicon_eye.poly_full_frame import build_geometry
from silicon_eye.poly_local_revision import apply_revisions, check_alignment, geometry_digest, run


def sample():
    group = dict(
        id="G",
        count=2,
        first_native_outline=[[10, 10], [14, 10], [14, 30], [10, 30]],
        last_native_outline=[[30, 10], [34, 10], [34, 30], [30, 30]],
        layout_y=[10, 30],
        approved_slots={},
        kind="MOS_gate_body",
        method="AI_candidate",
        body_scope="candidate",
        end_extension=dict(length_px=3, side="top", status="candidate"),
    )
    objects, _ = build_geometry({"groups": [group]}, {"objects": []})
    model = dict(objects=objects)
    patch = dict(
        object_id="G-P01",
        expected_geometry_sha256=geometry_digest(objects[0]),
        native_outline=[[10, 8], [14, 8], [14, 33], [10, 33]],
        layout_outline=[[10, 8], [14, 8], [14, 33], [10, 33]],
        evidence="Independent full-extent observation",
    )
    return model, patch


def test_local_end_correction_leaves_neighbor_and_input_unchanged():
    model, patch = sample()
    before = copy.deepcopy(model)
    revised = apply_revisions(model, [patch])
    assert model == before
    assert revised["objects"][1] == before["objects"][1]
    changed = revised["objects"][0]
    assert changed["native_outline"] == patch["native_outline"]
    assert "body_native_outline" not in changed
    assert "terminal_extension_side" not in changed
    assert (
        changed["local_revision"]["previous"]["native_outline"]
        == (before["objects"][0]["native_outline"])
    )
    with pytest.raises(ValueError, match="Stale"):
        apply_revisions(revised, [patch])


def test_reviewed_and_duplicate_targets_cannot_be_silently_rewritten():
    model, patch = sample()
    with pytest.raises(ValueError, match="Duplicate"):
        apply_revisions(model, [patch, patch])
    model["objects"][0]["approval"] = "human_accepted"
    with pytest.raises(ValueError, match="Reviewed"):
        apply_revisions(model, [patch])


def test_diagonal_layout_and_neighbor_collision_are_rejected():
    model, patch = sample()
    patch["layout_outline"][0][0] += 1
    with pytest.raises(ValueError, match="orthogonal"):
        apply_revisions(model, [patch])
    model, patch = sample()
    patch["layout_outline"] = [[10, 8], [32, 8], [32, 33], [10, 33]]
    with pytest.raises(ValueError, match="overlaps"):
        apply_revisions(model, [patch])


def test_regular_rectangles_do_not_hide_family_pitch_drift():
    model, _ = sample()
    family = dict(
        ids=["G-P01", "G-P02"], equal_width_px=4, equal_pitch_px=20, common_top_and_bottom=True
    )
    check_alignment(model["objects"], [family])
    for point in model["objects"][1]["layout_outline"]:
        point[0] += 1
    with pytest.raises(ValueError, match="pitch"):
        check_alignment(model["objects"], [family])


def test_overlapping_review_windows_do_not_double_count_or_unconfirm_reviewed_objects(tmp_path):
    model, patch = sample()
    model["objects"][1]["approval"] = "human_accepted_displayed_extent"
    parent = tmp_path / "parent.json"
    parent.write_text(json.dumps(model))
    photo = tmp_path / "photo.png"
    cv2.imwrite(str(photo), np.zeros((90, 100, 3), np.uint8))
    observation = dict(id="new-observation", native_outline=patch["native_outline"])
    case = dict(
        id="A",
        title="window",
        poly_bbox=[0, 0, 80, 70],
        aa_bbox=[0, 0, 80, 70],
        object_ids=[],
        proposed_objects=[observation, copy.deepcopy(model["objects"][1])],
        finding="test",
        question="pending",
    )
    second = copy.deepcopy(case)
    second["id"] = "B"
    spec = dict(
        parent_model=dict(path="parent.json", sha256=digest(parent)),
        sources={k: dict(path="photo.png", sha256=digest(photo)) for k in ["poly", "aa"]},
        revisions=[],
        cases=[case, second],
    )
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    report = run(tmp_path, path, tmp_path / "out")
    result = json.loads((tmp_path / "out/model.json").read_text())
    assert report["unmerged_observation_count"] == 1
    assert result["objects"] == model["objects"]
    assert report["geometry_gate"] == "no_parent_geometry_changed"
    second["proposed_objects"][0]["native_outline"][0][0] += 1
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="Inconsistent observation"):
        run(tmp_path, path, tmp_path / "conflict")
