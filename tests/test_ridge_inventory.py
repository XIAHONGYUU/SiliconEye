"""Check fragment inventory behavior; counts are not conductor truth."""

import numpy as np
import pytest

from silicon_eye.ridge_inventory import detect


def test_parallel_slopes_and_disconnected_gap():
    y, x = np.mgrid[:120, :401]
    g = sum(180 * np.exp(-(((y - (seed - 0.025 * x)) / 1.3) ** 2)) for seed in [30, 80])
    fragments, _ = detect(g, threshold=10, minimum_span=100)
    assert len(fragments) == 2
    for f, seed in zip(fragments, [30, 80], strict=True):
        assert not f["branch_or_parallel_overlap"]
        assert max(abs(py - (seed - 0.025 * px)) for px, py in f["points"]) <= 1
    g[:, 180:220] = 0
    parts, _ = detect(g, threshold=10, minimum_span=100)
    assert len(parts) == 4
    assert all(not (f["bounds"][0] < 180 and f["bounds"][2] > 220) for f in parts)


def test_blank_and_short_features_do_not_become_lines():
    g = np.zeros((80, 300), dtype=np.uint8)
    assert detect(g)[0] == []
    g[30:33, 40:75] = 255
    assert detect(g)[0] == []
    with pytest.raises(ValueError):
        detect(g, threshold=-1)
