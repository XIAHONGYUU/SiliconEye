"""Geometry checks deliberately avoid treating intersections as device truth."""

import numpy as np

from silicon_eye.local_mos_review import crop_transform, geometry


def test_native_inverse_and_crop_offsets():
    native = np.array([[1, 0, 20], [0, 1, -5], [0, 0, 1]], dtype=float)
    matrix = crop_transform(native, [100, 200], [70, 210])
    assert np.allclose(matrix @ [3, 4, 1], [13, -1, 1])


def test_shift_coverage_and_ct_do_not_create_hidden_channel():
    aa = np.zeros((30, 30), bool)
    aa[5:25, 5:20] = True
    poly = np.zeros_like(aa)
    poly[4:26, 12:15] = True
    ct = np.zeros_like(aa)
    ct[12:16, 12:15] = True
    matrix = np.array([[1, 0, 3], [0, 1, 0], [0, 0, 1]], dtype=float)
    result = geometry(aa, poly, ct, matrix, 2)
    assert result['aa_aligned'][5, 8]
    assert not result['aa_aligned'][5, 5]
    assert not result['valid'][:, :3].any()
    assert result['ct_occluded'].sum() == 12
    assert not (result['visible_overlap'] & ct).any()
    assert np.all(result['sensitivity_core'] <= result['visible_overlap'])
    assert result['sensitivity_band'].any()


def test_aa_and_ct_without_poly_have_no_channel_support():
    aa = np.ones((20, 20), bool)
    result = geometry(aa, np.zeros_like(aa), aa, np.eye(3), 2)
    assert not result['overlap'].any()
    assert not result['sensitivity_core'].any()
