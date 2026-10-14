"""Behavioral tests for structural priors and independent error-budget checks."""

import copy

import cv2
import numpy as np
import pytest

from silicon_eye.registration_constraints import (
    rectangle_center,
    solve_similarity,
    validate_constraints,
)


@pytest.fixture
def limits():
    return {
        "min_scale": 0.9,
        "max_scale": 1.1,
        "max_rotation_deg": 5,
        "max_translation_px": 400,
        "max_anchor_residual_px": 10,
        "min_anchor_hull_area_px2": 100000,
    }


def anchor_set(matrix):
    src = np.array([[500, 500], [2000, 500], [1500, 1500]], dtype=float)
    dst = src @ matrix[:2, :2].T + matrix[:2, 2]
    return [
        {
            "id": f"FIT-{i}",
            "role": "fitting",
            "description": "unique structure",
            "target_xy": s.tolist(),
            "reference_xy": d.tolist(),
        }
        for i, (s, d) in enumerate(zip(src, dst, strict=True))
    ]


def test_recovers_similarity_from_only_fit_anchors(limits):
    angle = np.radians(2)
    a, b = 1.01 * np.cos(angle), 1.01 * np.sin(angle)
    expected = np.array([[a, -b, 80], [b, a, 120], [0, 0, 1]])
    result = solve_similarity(anchor_set(expected), limits)
    assert result["success"]
    np.testing.assert_allclose(result["matrix"], expected, atol=1e-10)
    assert max(result["anchor_residuals_px"]) < 1e-8


@pytest.mark.parametrize(
    "matrix,check",
    [
        (np.array([[0.4, 0, 0], [0, 0.4, 0], [0, 0, 1]]), "scale"),
        (np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]]), "rotation"),
        (np.array([[1, 0, 500], [0, 1, 0], [0, 0, 1]]), "translation"),
    ],
)
def test_rejects_implausible_exact_fits(limits, matrix, check):
    result = solve_similarity(anchor_set(matrix), limits)
    assert not result["success"]
    assert result["reason"] == "structural_constraint_violation"
    assert not result["checks"][check]
    # A low fit residual cannot override a structural prior.
    assert max(result["anchor_residuals_px"]) < 1e-8


def test_insufficient_degenerate_and_inconsistent_anchors(limits):
    records = anchor_set(np.eye(3))
    assert solve_similarity(records[:2], limits)["reason"] == "insufficient_structural_anchors"
    bad = copy.deepcopy(records)
    for p in bad:
        p["target_xy"][1] = 500
    assert solve_similarity(bad, limits)["reason"] == "degenerate_structural_anchors"
    records[2]["reference_xy"][0] += 100
    result = solve_similarity(records, limits)
    assert not result["success"] and not result["checks"]["anchor_residual"]


def test_rectangle_edge_centroid_and_input_integrity():
    image = np.zeros((320, 420, 3), dtype=np.uint8)
    cv2.rectangle(image, (90, 80), (290, 220), (220, 220, 220), 5)
    original = image.copy()
    result = rectangle_center(image, [90, 80, 200, 140], band=15)
    np.testing.assert_allclose(result["xy"], [190, 150], atol=1)
    assert min(result["edge_contrast"]) > 100
    assert result["measurement_quality"]["valid"]
    np.testing.assert_array_equal(image, original)
    with pytest.raises(ValueError, match="no measurable"):
        rectangle_center(np.zeros_like(image), [90, 80, 200, 140], band=15)


@pytest.mark.parametrize("kind", ["weak", "clipped"])
def test_unreliable_edges_are_not_fit_anchors(limits, kind):
    image = np.zeros((320, 420, 3), dtype=np.uint8)
    if kind == "weak":
        cv2.rectangle(image, (90, 80), (290, 220), (4, 4, 4), 5)
    else:
        cv2.rectangle(image, (70, 80), (290, 220), (220, 220, 220), 5)
    result = rectangle_center(image, [90, 80, 200, 140], band=25)
    assert not result["measurement_quality"]["valid"]
    checks = result["measurement_quality"]["edge_checks_lrtb"]
    if kind == "weak":
        assert not checks[0]["contrast_sufficient"]
    else:
        assert not checks[0]["support_inside_search_band"]
    anchors = anchor_set(np.eye(3))
    anchors[0]["target_measurement"] = result
    solved = solve_similarity(anchors, limits)
    assert not solved["success"] and solved["reason"] == "unreliable_structural_measurement"
    assert solved["quality_failures"][0]["side"] == "target_measurement"


def test_legacy_script_measurement_cannot_bypass_quality(limits):
    anchors = anchor_set(np.eye(3))
    anchors[0]["target_measurement"] = {"xy": anchors[0]["target_xy"]}
    assert solve_similarity(anchors, limits)["reason"] == "unreliable_structural_measurement"


def test_brighter_internal_stripe_does_not_replace_declared_boundary():
    image = np.zeros((340, 440, 3), dtype=np.uint8)
    cv2.rectangle(image, (100, 90), (300, 230), (180, 180, 180), 5)
    cv2.line(image, (125, 100), (125, 220), (255, 255, 255), 7)
    result = rectangle_center(image, [100, 90, 200, 140], band=40)
    assert result["measurement_quality"]["valid"]
    np.testing.assert_allclose(result["edge_positions_lrtb"][0], 100, atol=1)
    np.testing.assert_allclose(result["xy"], [200, 160], atol=1)


def test_constraints_validate_provenance_budget_and_separation(limits):
    sources = {"aa": {"sha256": "A"}, "poly": {"sha256": "B"}}
    document = {
        "schema_version": 1,
        "reference": "aa",
        "source_sha256": {"aa": "A", "poly": "B"},
        "limits": limits,
        "budget": {
            "p95_px": 8,
            "max_px": 12,
            "basis": "allocation",
            "locked_before_registration": True,
        },
        "layers": {"poly": anchor_set(np.eye(3))},
    }
    points = {
        "layers": {
            "poly": [
                {
                    "reference_xy": [1200, 3000],
                    "target_xy": [1200, 3000],
                    "exclusion_radius_px": 128,
                }
            ]
        }
    }
    roi = [100, 200, 2500, 2000]
    validate_constraints(document, "aa", sources, points, roi)
    overlap = copy.deepcopy(points)
    overlap["layers"]["poly"][0]["target_xy"] = [500, 500]
    with pytest.raises(ValueError, match="overlaps"):
        validate_constraints(document, "aa", sources, overlap, roi)
    for kind in ["hash", "lock", "budget", "duplicate"]:
        bad = copy.deepcopy(document)
        if kind == "hash":
            bad["source_sha256"]["poly"] = "wrong"
        elif kind == "lock":
            bad["budget"]["locked_before_registration"] = False
        elif kind == "budget":
            bad["budget"]["p95_px"] = 13
        else:
            bad["layers"]["poly"].append(bad["layers"]["poly"][0].copy())
        with pytest.raises(ValueError):
            validate_constraints(bad, "aa", sources, points, roi)
