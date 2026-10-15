import cv2
import numpy as np
import pytest

from silicon_eye.guided_materials import ct_support
from silicon_eye.material_review import extend_aa


def test_aa_full_scan_preserves_known_gap_and_finds_unmarked_candidate():
    raw = np.full((100, 160, 3), 40, np.uint8)
    cv2.rectangle(raw, (10, 10), (90, 80), (210, 210, 210), 4)
    raw[30:60, 30:70] = 210
    raw[20:40, 120:145] = 210
    prompt = np.zeros((100, 160), np.uint8)
    cv2.rectangle(prompt, (10, 10), (90, 80), 255, 3)
    prompt[32:58, 32:68] = 255
    refined = prompt > 0
    domain = cv2.dilate(prompt, np.ones((5, 5), np.uint8)) > 0
    result, _, info = extend_aa(raw, refined, domain, prompt)
    np.testing.assert_array_equal(result[domain], refined[domain])
    assert result[30, 130]
    assert info["unreviewed_added_pixels"] > 0
    _, labels = cv2.connectedComponents(result.astype(np.uint8), connectivity=8)
    assert labels[45, 50] > 0 and labels[10, 50] > 0
    assert labels[45, 50] != labels[10, 50]


def test_full_ct_scan_is_not_restricted_to_a_poly_prompt():
    raw = np.full((100, 160, 3), 60, np.uint8)
    raw[20:32, 20:32] = 250
    raw[60:72, 120:132] = 250
    mask = ct_support(raw)
    assert mask[26, 26]
    assert mask[66, 126]
    assert not mask[45, 80]


def test_inconsistent_material_shapes_are_rejected():
    with pytest.raises(ValueError, match="shapes"):
        extend_aa(
            np.zeros((50, 50, 3), np.uint8),
            np.zeros((20, 20), bool),
            np.zeros((50, 50), bool),
            np.zeros((50, 50), np.uint8),
        )
