import numpy as np

from silicon_eye.ridge_risk_diagnostics import intervals, sample_support


def test_intervals_conserve_separate_columns_and_edges():
    assert intervals([True, True, False, True, False, True]) == [(0, 2), (3, 4), (5, 6)]
    assert intervals([]) == []
    assert intervals([False, False]) == []


def test_raw_support_does_not_extend_beyond_radius():
    mask = np.zeros((8, 10), dtype=bool)
    mask[0, 2] = True
    mask[7, 8] = True
    assert sample_support(mask, [[2, 0], [2, 2], [2, 3], [8, 7], [8, 5], [8, 4]]).tolist() == [
        True,
        True,
        False,
        True,
        True,
        False,
    ]
