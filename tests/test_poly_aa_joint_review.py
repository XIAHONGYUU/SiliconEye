"""Failed independent local correspondence checks must suppress the overlay."""

import hashlib
import json

from silicon_eye.poly_aa_joint_review import joint_review


def test_bad_independent_correspondence_never_produces_a_plausible_overlay(tmp_path):
    model = tmp_path / "aa.json"
    model.write_text(json.dumps({"groups": [{"id": "local", "members": []}], "objects": []}))
    points = [[0, 0], [10, 0], [10, 10], [0, 10]]
    spec = {
        "aa_model": {"path": "aa.json", "sha256": hashlib.sha256(model.read_bytes()).hexdigest()},
        "joint_checks": {
            "aa_group": "local",
            "poly_fit_points": points,
            "aa_fit_points": points,
            "poly_check_points": [[5, 5]],
            "aa_check_points": [[50, 50]],
            "max_check_error_px": 2,
            "scope": "local_candidate",
        },
    }
    report = joint_review(tmp_path, spec, [], tmp_path)
    assert not report["geometric_check_pass"]
    assert report["status"] == "registration_check_failed_overlay_not_drawn"
    assert not (tmp_path / "joint/source-overlay.jpg").exists()
    assert not (tmp_path / "joint/joint-layout.svg").exists()


def test_bad_photo_fit_does_not_block_explicit_aa_relative_design(tmp_path):
    guard = dict(
        id="GUARD",
        primitive="orthogonal_polygon",
        outer_xy=[[-10, -10], [130, -10], [130, 110], [-10, 110]],
        holes_xy=[[[0, 0], [120, 0], [120, 100], [0, 100]]],
    )
    active = dict(
        id="AA1",
        primitive="orthogonal_polygon",
        outer_xy=[[10, 20], [110, 20], [110, 40], [10, 40]],
        holes_xy=[],
    )
    model = tmp_path / "aa.json"
    model.write_text(
        json.dumps(
            dict(groups=[dict(id="local", members=["GUARD", "AA1"])], objects=[guard, active])
        )
    )
    points = [[0, 0], [10, 0], [10, 10], [0, 10]]
    rules = dict(
        families=[dict(groups=["G"], gate_width_px=10)],
        row_AA_targets={"G": "AA1"},
        lateral_margin_px=8,
        min_intergate_gap_px=8,
        min_poly_extension_px=8,
        guard_clearance_px=3,
    )
    spec = dict(
        aa_model=dict(path="aa.json", sha256=hashlib.sha256(model.read_bytes()).hexdigest()),
        groups=[dict(id="G", count=1, approved_slots={})],
        joint_checks=dict(
            aa_group="local",
            poly_fit_points=points,
            aa_fit_points=points,
            poly_check_points=[[5, 5]],
            aa_check_points=[[50, 50]],
            max_check_error_px=2,
            scope="design_scope",
            poly_group_ids=["G"],
            forward_layout_constraints=rules,
        ),
    )
    report = joint_review(tmp_path, spec, [dict(id="G-P01")], tmp_path)
    assert not report["geometric_check_pass"]
    assert report["reconstructed_relation_audit"]["status"] == "PASS"
    assert report["derived_objects"][0]["photo_projected_layout_outline"] is None
    assert not (tmp_path / "joint/source-overlay.jpg").exists()
    assert (tmp_path / "joint/joint-layout.svg").is_file()
