"""Direction descriptors must distinguish oriented evidence without inventing geometry."""

import numpy as np

from silicon_eye.aa_texture_eval import feature_groups

SETTINGS = dict(feature_sigmas=[1, 2, 4, 8], tensor_sigmas=[3, 9], directional_widths=[15, 31, 63])


def test_uniform_field_has_no_direction_or_texture_energy():
    groups = feature_groups(np.full((80, 90, 3), 100, np.uint8), SETTINGS)
    assert all(np.isfinite(v).all() for v in groups.values())
    structural = groups["structure"][..., 3:]
    assert np.max(np.abs(structural[..., :8])) < 1e-5
    for i in [10, 13, 16]:
        assert np.max(np.abs(structural[..., i])) < 1e-5


def test_transposition_preserves_energy_and_reverses_axis_preference():
    raw = np.zeros((81, 81, 3), np.uint8)
    raw[:, 34:47] = 200
    a = feature_groups(raw, SETTINGS)["structure"][..., 3:]
    b = feature_groups(raw.transpose(1, 0, 2).copy(), SETTINGS)["structure"][..., 3:]
    b = b.transpose(1, 0, 2)
    for offset in [0, 4]:
        np.testing.assert_allclose(a[..., offset], b[..., offset], atol=1e-5)
        np.testing.assert_allclose(a[..., offset + 2], -b[..., offset + 2], atol=1e-5)
    assert a[40, 34, 2] > 0.9
    for offset in [8, 11, 14]:
        np.testing.assert_allclose(a[..., offset], b[..., offset + 1], atol=1e-5)
        np.testing.assert_allclose(a[..., offset + 2], -b[..., offset + 2], atol=1e-5)
