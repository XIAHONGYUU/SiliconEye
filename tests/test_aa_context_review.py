"""Review agreement is strict unanimity, never majority-based segmentation."""

import numpy as np

from silicon_eye.aa_context_review import disagreements


def test_unanimity_distinguishes_conflict_from_foreground_and_background():
    a = np.array([[0, 1, 1, 0]], bool)
    b = np.array([[0, 1, 0, 1]], bool)
    c = np.array([[0, 1, 1, 0]], bool)
    np.testing.assert_array_equal(disagreements([a, b, c]), [[0, 1, 2, 2]])


def test_duplicating_correlated_masks_cannot_turn_conflict_into_agreement():
    a = np.array([[0, 1, 1]], bool)
    b = np.array([[0, 1, 0]], bool)
    expected = disagreements([a, b])
    np.testing.assert_array_equal(disagreements([a] * 10 + [b]), expected)
