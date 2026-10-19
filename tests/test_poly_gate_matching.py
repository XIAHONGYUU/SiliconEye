"""Evidence proposals must not force a count or merge distinct neighboring peaks."""

import numpy as np
import pytest

from silicon_eye.poly_gate_matching import match_region


def test_two_nearby_observations_and_blank_field():
    rng = np.random.default_rng(5)
    patch = rng.integers(0, 255, (18, 16), dtype=np.uint8)
    image = np.zeros((60, 100), np.uint8)
    image[20:38, 12:28] = patch
    image[20:38, 48:64] = patch
    templates = [dict(id="seed", image=patch, body_offset_xywh=[0, 0, 16, 18])]
    result = match_region(image, [0, 0, 100, 60], templates, 0.95, 24)
    assert [p["bbox"] for p in result] == [[12, 20, 28, 38], [48, 20, 64, 38]]
    assert match_region(np.zeros_like(image), [0, 0, 100, 60], templates, 0.95, 24) == []


def test_invalid_evidence_and_region_fail_explicitly():
    image = np.zeros((30, 30), np.uint8)
    templates = [
        dict(id="constant", image=np.ones((8, 8), np.uint8), body_offset_xywh=[0, 0, 8, 8])
    ]
    with pytest.raises(ValueError, match="constant template"):
        match_region(image, [0, 0, 30, 30], templates, 0.5, 24)
    with pytest.raises(ValueError, match="outside source"):
        match_region(image, [-1, 0, 30, 30], templates, 0.5, 24)
