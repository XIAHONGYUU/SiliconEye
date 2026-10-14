"""Independent-coordinate validation and real evidence-pack behavior."""

import copy
import json

import cv2
import numpy as np
import pytest

from silicon_eye.registration_audit import (
    digest,
    evaluate_points,
    fit_image,
    full_matrix,
    run_audit,
    validate_points,
)


def test_crop_and_rounded_resize_preserve_native_transform():
    image = np.zeros((401, 607, 3), dtype=np.uint8)
    _, ref_scale = fit_image(image, [31, 47, 503, 301], 173)
    _, target_scale = fit_image(image, [25, 39, 499, 307], 173)
    expected = np.array([[1.01, 0.02, 9], [-0.01, 0.99, -6], [0.0001, 0, 1]])
    fitted = ref_scale @ expected @ np.linalg.inv(target_scale)
    actual = full_matrix(fitted, ref_scale, target_scale)
    np.testing.assert_allclose(actual, expected, atol=1e-12)
    assert ref_scale[0, 0] != ref_scale[1, 1]


def point(identifier="P-1", status="candidate", xy=(150, 200)):
    return {
        "id": identifier,
        "role": "validation",
        "status": status,
        "producer": "test",
        "description": "independent structure",
        "reference_xy": list(xy),
        "target_xy": list(xy),
        "exclusion_radius_px": 8,
        "reviewed_by": "test-reviewer",
    }


def annotation():
    return {
        "schema_version": 1,
        "reference": "aa",
        "source_sha256": {"aa": "A", "poly": "B"},
        "layers": {"poly": [point()]},
    }


def test_validation_points_are_separate_and_bound_to_sources():
    sources = {
        "aa": {"size": [256, 256], "sha256": "A"},
        "poly": {"size": [256, 256], "sha256": "B"},
    }
    document = annotation()
    validate_points(document, "aa", sources, [0, 0, 256, 128])
    for mutation in ("overlap", "hash", "duplicate", "bounds", "reviewer", "role"):
        changed = copy.deepcopy(document)
        record = changed["layers"]["poly"][0]
        if mutation == "overlap":
            record["target_xy"] = [150, 130]
        elif mutation == "hash":
            changed["source_sha256"]["poly"] = "WRONG"
        elif mutation == "duplicate":
            changed["layers"]["poly"].append(record.copy())
        elif mutation == "bounds":
            record["reference_xy"] = [256, 200]
        elif mutation == "reviewer":
            record["status"] = "confirmed"
            record.pop("reviewed_by")
        elif mutation == "role":
            record["role"] = "fitting"
        with pytest.raises(ValueError):
            validate_points(changed, "aa", sources, [0, 0, 256, 128])


def test_candidate_accuracy_does_not_establish_acceptance():
    result = evaluate_points(np.eye(3), [point()], 1.0, (256, 256))
    assert result["median_px"] == 0
    assert result["status"] == "unknown" and result["reason"] == "points_need_review"
    no_points = evaluate_points(np.eye(3), [], 1.0, (256, 256))
    assert no_points["reason"] == "no_independent_points"
    failed = evaluate_points(None, [point()], 1.0, (256, 256))
    assert failed["reason"] == "registration_failed"


def test_independent_errors_and_gates():
    locations = [(20, 20), (200, 20), (20, 200), (200, 200), (70, 80), (190, 90)]
    records = [point(f"P-{i}", "confirmed", xy) for i, xy in enumerate(locations)]
    correct = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
    wrong = np.array([[1, 0, 3], [0, 1, 4], [0, 0, 1]], dtype=float)
    result = evaluate_points(wrong, records, 4.0, (256, 256))
    assert result["status"] == "conflict"
    assert result["median_px"] == result["p95_px"] == result["max_px"] == 5
    assert result["covered_quadrants"] == 4
    assert evaluate_points(correct, records, 1.0, (256, 256))["status"] == "confirmed"
    assert evaluate_points(correct, records, None, (256, 256))["reason"] == "no_locked_error_budget"
    assert evaluate_points(correct, records[:2], 1.0, (256, 256))["reason"] == (
        "insufficient_spatial_coverage"
    )


def test_end_to_end_evidence_and_failed_layer(tmp_path):
    data = tmp_path / "data" / "sample" / "tile"
    data.mkdir(parents=True)
    rng = np.random.default_rng(42)
    texture = rng.integers(0, 255, (256, 256, 3), dtype=np.uint8)
    for name, image in [("aa", texture), ("poly", texture), ("blank", np.zeros_like(texture))]:
        assert cv2.imwrite(str(data / f"{name}.png"), image)
    config = tmp_path / "sample.yaml"
    config.write_text(
        "chip:\n  name: sample\nlayers:\n"
        "  - {name: aa, index: 0}\n  - {name: poly, index: 1}\n"
        "  - {name: blank, index: 2}\ntiles:\n  - {id: tile}\n"
    )
    original_hashes = {p.name: digest(p) for p in data.glob("*.png")}
    out = tmp_path / "evidence"
    result = run_audit(
        str(config), str(tmp_path / "data"), "aa", str(out), [0, 0, 256, 128], max_dimension=256
    )
    assert result["status"] == "complete"
    assert set(result["layers"]) == {"aa", "poly", "blank"}
    assert result["layers"]["poly"]["success"]
    assert result["layers"]["poly"]["evaluation"]["status"] == "unknown"
    assert result["layers"]["poly"]["metric_units"]["rmse"] == "resized_fit_pixels"
    failed = result["layers"]["blank"]
    assert not failed["success"] and failed["matrix_target_to_reference_native"] is None
    assert not (out / "blank" / "after_overlay.jpg").exists()
    for name in result["layers"]:
        assert (out / name / "transform.json").exists()
        assert (out / name / "before_overlay.jpg").exists()
        assert len(list((out / name).glob("local-*.jpg"))) == 3
    assert json.loads((out / "manifest.json").read_text())["status"] == "complete"
    assert (out / "report.md").exists()
    for relative, expected in result["code"]["sha256"].items():
        assert digest(out / "source-snapshot" / relative) == expected
    assert {p.name: digest(p) for p in data.glob("*.png")} == original_hashes
    sources = result["inputs"]
    doc = {
        "schema_version": 1,
        "reference": "aa",
        "source_sha256": {n: s["sha256"] for n, s in sources.items()},
        "layers": {"poly": [point()]},
    }
    annotations_path = tmp_path / "points.json"
    annotations_path.write_text(json.dumps(doc))
    coords = [[50, 40], [190, 40], [128, 110]]
    constraint_doc = {
        "schema_version": 1,
        "reference": "aa",
        "source_sha256": doc["source_sha256"],
        "budget": {
            "scope": "pilot",
            "p95_px": 8,
            "max_px": 12,
            "basis": "test allocation",
            "locked_before_registration": True,
        },
        "limits": {
            "min_scale": 0.9,
            "max_scale": 1.1,
            "max_rotation_deg": 5,
            "max_translation_px": 30,
            "max_anchor_residual_px": 1,
            "min_anchor_hull_area_px2": 1000,
        },
        "layers": {
            "poly": [
                {
                    "id": f"FIT-{i}",
                    "role": "fitting",
                    "description": "structure",
                    "reference_xy": xy,
                    "target_xy": xy,
                }
                for i, xy in enumerate(coords)
            ]
        },
    }
    constraint_path = tmp_path / "constraints.json"
    constraint_path.write_text(json.dumps(constraint_doc))
    constrained = run_audit(
        str(config),
        str(tmp_path / "data"),
        "aa",
        str(tmp_path / "structural"),
        [0, 0, 256, 128],
        points_path=str(annotations_path),
        constraints_path=str(constraint_path),
        max_dimension=256,
    )
    row = constrained["layers"]["poly"]
    assert row["success"] and row["method"] == "structural_similarity"
    assert row["evaluation"]["budget_check"]["numeric_met"]
    assert row["evaluation"]["status"] == "unknown"  # numeric accuracy is not human truth
    assert row["matrix_fit"] is None  # all anchor fitting used native coordinates
    assert constrained["layers"]["blank"]["reason"] == "insufficient_structural_anchors"
    assert not (tmp_path / "structural" / "blank" / "after_overlay.jpg").exists()
    with pytest.raises(FileExistsError):
        run_audit(str(config), str(tmp_path / "data"), "aa", str(out), [0, 0, 256, 128])
    with pytest.raises(ValueError, match="original input"):
        run_audit(str(config), str(tmp_path / "data"), "aa", str(data / "unsafe"), [0, 0, 256, 128])


def test_invalid_roi():
    image = np.zeros((64, 64, 3), dtype=np.uint8)
    for roi in [[-1, 0, 32, 32], [0, 0, 65, 32], [0, 0, 4, 32]]:
        with pytest.raises(ValueError):
            fit_image(image, roi, 64)
