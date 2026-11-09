"""Check coordinate and sparse-evidence semantics, independently of SAM inference."""

import numpy as np
import pytest

from silicon_eye.metal_algorithm_pilot import crop, diagnostics, local_points, seeded_components


def test_native_crop_coordinates_and_reject_outside():
    image = np.arange(120).reshape(10, 12)
    np.testing.assert_array_equal(crop(image, [4, 3, 7, 5]), image[3:5, 4:7])
    np.testing.assert_array_equal(local_points([[5, 4]], [4, 3, 7, 5]), [[1, 1]])
    with pytest.raises(ValueError):
        crop(image, [-1, 0, 5, 5])
    with pytest.raises(ValueError):
        local_points([[7, 4]], [4, 3, 7, 5])


def test_seed_does_not_snap_across_gap_or_keep_other_component():
    mask = np.zeros((8, 12), bool)
    mask[1:7, 2:4] = True
    mask[1:7, 7:9] = True
    selected = seeded_components(mask, np.array([[2, 3], [5, 3]]))
    assert selected.sum() == 12
    assert not selected[:, 7:9].any()
    assert not seeded_components(mask, np.array([[5, 3]])).any()


def test_sparse_checks_distinguish_misses_and_false_hits_and_breaks():
    mask = np.zeros((10, 10), bool)
    mask[2, 2] = mask[6, 6] = mask[8, 8] = True
    case = {'bounds': [100, 200, 110, 210],
            'probes': [[102, 202, 1], [106, 206, 1], [104, 204, 1], [108, 208, 0]]}
    result = diagnostics(mask, case)
    assert result['missed_positive_probes'] == 1
    assert result['hit_negative_probes'] == 1
    assert result['positive_probes_one_component'] is False
