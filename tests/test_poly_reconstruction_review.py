"""POLY refinement must measure width on either orientation and preserve occlusion."""

import numpy as np
import pytest

from silicon_eye.poly_reconstruction_review import refine_strip, visible_states

SETTINGS = dict(
    trim_tangent_fraction=0.1,
    normal_search_fraction=0.8,
    minimum_supported_fraction=0.4,
    max_normal_shift_fraction=0.6,
)


@pytest.mark.parametrize("vertical", [False, True])
def test_normal_width_is_refined_without_changing_tangent_extent(vertical):
    mask = np.zeros((100, 100), bool)
    if vertical:
        mask[10:90, 20:30] = True
        points = np.array([[22, 10], [28, 10], [28, 90], [22, 90]], float)
    else:
        mask[20:30, 10:90] = True
        points = np.array([[10, 22], [90, 22], [90, 28], [10, 28]], float)
    unknown = np.zeros_like(mask)
    if vertical:
        unknown[40:50] = True
    else:
        unknown[:, 40:50] = True
    result, info = refine_strip(points, mask, unknown, np.array([0, 0]), SETTINGS)
    assert result is not None
    widths = np.ptp(result, axis=0)
    assert widths[0 if vertical else 1] == pytest.approx(10)
    assert widths[1 if vertical else 0] == pytest.approx(80)
    assert info["quality_improvement"].startswith("NOT_ESTABLISHED")
    assert info["mean_corner_change_px"] == pytest.approx(2)
    states = visible_states(mask, unknown)
    assert np.all(states[unknown] == -1)
    assert np.all(states[~mask] == -1)


def test_no_visible_evidence_cannot_create_new_poly():
    empty = np.zeros((50, 100), bool)
    points = np.array([[10, 20], [90, 20], [90, 30], [10, 30]])
    result, info = refine_strip(points, empty, empty, np.array([0, 0]), SETTINGS)
    assert result is None
    assert info["status"] == "insufficient_visible_support"


def test_foreground_only_under_occlusion_does_not_count_as_evidence():
    mask = np.ones((50, 100), bool)
    points = np.array([[10, 20], [90, 20], [90, 30], [10, 30]])
    result, _ = refine_strip(points, mask, mask, np.array([0, 0]), SETTINGS)
    assert result is None
