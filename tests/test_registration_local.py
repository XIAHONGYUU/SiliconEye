import json

import cv2
import numpy as np
import pytest

from silicon_eye.registration_audit import digest
from silicon_eye.registration_local import ring_translation, run_local


def make_spec(tmp_path, check_shift=0):
    fit = [300, 180, 180, 100]
    check = [100, 150, 70, 220]
    reference = np.zeros((600, 700, 3), np.uint8)
    target = reference.copy()
    for image, dx, dy, extra in ((reference, 0, 0, 0), (target, -14, -18, check_shift)):
        for index, (x, y, width, height) in enumerate((fit, check)):
            x += dx + (extra if index else 0)
            y += dy
            cv2.rectangle(image, (x, y), (x + width, y + height), (220, 220, 220), 6)
    spec = {
        "schema_version": 1,
        "scope": "local_only",
        "fitting": {"model": "translation_only", "edge_search_band_px": 15},
        "validation": {
            "edge_search_band_px": 15,
            "minimum_structure_gap_px": 50,
            "correlation_note": "one check structure",
        },
        "budget": {"locked_before_registration": True, "p95_px": 8, "max_px": 12},
    }
    for side, image, origin, dx, dy in (
        ("reference", reference, [50, 80], 0, 0),
        ("target", target, [40, 60], -14, -18),
    ):
        path = tmp_path / f"{side}.png"
        cv2.imwrite(str(path), image)
        spec[side] = {
            "path": str(path),
            "sha256": digest(path),
            "crop_xywh": [*origin, 500, 400],
            "fit_box_xywh": [fit[0] + dx, fit[1] + dy, *fit[2:]],
            "check_box_xywh": [
                check[0] + dx + (check_shift if dx else 0),
                check[1] + dy,
                *check[2:],
            ],
        }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    return path


@pytest.mark.parametrize("check_shift,passes", [(0, True), (25, False)])
def test_local_direction_and_checks_cannot_change_fit(tmp_path, check_shift, passes):
    spec_path = make_spec(tmp_path, check_shift)
    result = run_local(str(spec_path), str(tmp_path / "out"))
    np.testing.assert_allclose(np.array(result["matrix_native"])[:2, 2], [14, 18], atol=0.01)
    # Native translation and crop translation differ; test both coordinate frames.
    np.testing.assert_allclose(np.array(result["matrix_crop"])[:2, 2], [4, -2], atol=0.01)
    assert result["numeric_budget_met"] is passes
    assert result["acceptance"] == "unknown"
    assert result["validation_metrics"]["max_px"] == pytest.approx(check_shift, abs=0.01)
    assert cv2.imread(str(tmp_path / "out/after-overlay-candidate.jpg")).shape == (400, 500, 3)
    assert (tmp_path / "out/source-snapshot/registration_local.py").exists()
    with pytest.raises(ValueError, match="new directory"):
        run_local(str(spec_path), str(tmp_path / "out"))


@pytest.mark.parametrize("defect", ["hash", "overlap", "budget"])
def test_invalid_local_input_rejected_before_outputs(tmp_path, defect):
    path = make_spec(tmp_path)
    spec = json.loads(path.read_text())
    if defect == "hash":
        spec["target"]["sha256"] = "wrong"
    elif defect == "overlap":
        spec["target"]["check_box_xywh"] = spec["target"]["fit_box_xywh"]
    else:
        spec["budget"]["locked_before_registration"] = False
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError):
        run_local(str(path), str(tmp_path / "out"))
    assert not (tmp_path / "out").exists()


def test_bad_ring_measurement_cannot_fit():
    good = {"xy": [1, 2], "measurement_quality": {"valid": True}}
    with pytest.raises(ValueError, match="quality"):
        ring_translation(good, {"xy": [1, 2]})


def test_similarity_recovers_known_rotation_scale_and_direction():
    from silicon_eye.registration_local import ring_similarity

    src = np.array([[100, 200], [700, 200], [700, 500], [100, 500]], dtype=float)
    angle = np.deg2rad(3)
    linear = 1.04 * np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    translation = np.array([14, -23])
    dst = src @ linear.T + translation
    quality = {"measurement_quality": {"valid": True}}
    limits = {
        "min_scale": 0.9,
        "max_scale": 1.1,
        "max_rotation_deg": 5,
        "max_corner_residual_px": 10,
    }
    matrix, result = ring_similarity(
        {**quality, "corners_native": dst.tolist()},
        {**quality, "corners_native": src.tolist()},
        limits,
    )
    np.testing.assert_allclose(matrix[:2, :2], linear, atol=1e-10)
    np.testing.assert_allclose(matrix[:2, 2], translation, atol=1e-10)
    assert result["rotation_deg"] == pytest.approx(3)
    assert result["scale"] == pytest.approx(1.04)
    with pytest.raises(ValueError, match="constraint"):
        ring_similarity(
            {**quality, "corners_native": (src * [1.15, 0.9]).tolist()},
            {**quality, "corners_native": src.tolist()},
            limits,
        )


def line_settings():
    return {
        "sample_count": 48,
        "central_fraction": 0.7,
        "min_valid_fraction": 0.75,
        "min_contrast": 10,
        "max_line_p95_px": 4,
        "trim_residual_px": 4,
    }


def test_line_measurement_recovers_tilted_corners_and_rejects_blank():
    from silicon_eye.registration_local import ring_edge_lines

    image = np.zeros((500, 700, 3), np.uint8)
    vertices = np.array([[200, 170], [500, 170], [500, 320], [200, 320]], dtype=float)
    angle = np.deg2rad(2)
    linear = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    tilted = (vertices - [350, 245]) @ linear.T + [350, 245]
    cv2.polylines(image, [np.round(tilted).astype(np.int32)], True, (220, 220, 220), 6)
    measurement = ring_edge_lines(image, [1000, 2000], [1200, 2170, 300, 150], 30, line_settings())
    np.testing.assert_allclose(measurement["corners_native"], tilted + [1000, 2000], atol=1.5)
    assert all(e["p95_residual_px"] < 1 for e in measurement["edge_line_evidence_lrtb"])
    with pytest.raises(ValueError):
        ring_edge_lines(
            np.zeros_like(image), [1000, 2000], [1200, 2170, 300, 150], 30, line_settings()
        )


@pytest.mark.parametrize("check_shift,passes", [(0, True), (25, False)])
def test_similarity_local_checks_remain_outside_fitting(tmp_path, check_shift, passes):
    path = make_spec(tmp_path, check_shift)
    spec = json.loads(path.read_text())
    spec["fitting"].update(
        {
            "model": "ring_similarity",
            "line_sampling": line_settings(),
            "limits": {
                "min_scale": 0.9,
                "max_scale": 1.1,
                "max_rotation_deg": 5,
                "max_corner_residual_px": 10,
            },
        }
    )
    path.write_text(json.dumps(spec))
    result = run_local(str(path), str(tmp_path / "out"))
    np.testing.assert_allclose(np.array(result["matrix_native"])[:2, 2], [14, 18], atol=0.01)
    assert result["numeric_budget_met"] is passes
    assert result["acceptance"] == "unknown"
    assert result["unestimated"] == ["perspective"]


def make_frozen_spec(tmp_path):
    path = make_spec(tmp_path)
    spec = json.loads(path.read_text())
    baseline_path = tmp_path / "baseline"
    run_local(str(path), str(baseline_path))
    baseline = json.loads((baseline_path / "manifest.json").read_text())
    spec["frozen_transform"] = {
        "baseline_manifest": str(baseline_path / "manifest.json"),
        "baseline_sha256": digest(baseline_path / "manifest.json"),
        "matrix_native": baseline["matrix_native"],
    }
    return path, spec, baseline


def test_frozen_check_uses_exact_matrix_without_solver(tmp_path, monkeypatch):
    import silicon_eye.registration_local as local

    path, spec, baseline = make_frozen_spec(tmp_path)
    spec["target"]["crop_xywh"][0] -= 10
    path.write_text(json.dumps(spec))

    def forbidden(*args, **kwargs):
        pytest.fail("frozen validation called a fitting algorithm")

    monkeypatch.setattr(local, "ring_translation", forbidden)
    monkeypatch.setattr(local, "ring_similarity", forbidden)
    monkeypatch.setattr(local, "ring_edge_lines", forbidden)
    result = run_local(str(path), str(tmp_path / "validation"))
    assert result["matrix_native"] == baseline["matrix_native"]
    assert result["numeric_budget_met"] is True
    assert result["acceptance"] == "unknown"


@pytest.mark.parametrize("defect", ["matrix", "budget", "fit", "source", "baseline_hash"])
def test_frozen_protocol_drift_is_rejected(tmp_path, defect):
    path, spec, _ = make_frozen_spec(tmp_path)
    if defect == "matrix":
        spec["frozen_transform"]["matrix_native"][0][2] += 1
    elif defect == "budget":
        spec["budget"]["max_px"] = 100
    elif defect == "fit":
        spec["reference"]["fit_box_xywh"][0] += 1
    elif defect == "source":
        spec["target"]["sha256"] = "changed"
    else:
        spec["frozen_transform"]["baseline_sha256"] = "changed"
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="frozen"):
        run_local(str(path), str(tmp_path / "validation"))
    assert not (tmp_path / "validation").exists()
