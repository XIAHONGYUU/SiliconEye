"""Source-boundary revision preserves gaps, unknowns, and internally dark AA."""

import numpy as np
import pytest

from silicon_eye.aa_semantic_revision import reconstruct, reviewed_center_metrics


def example():
    image = np.full((100, 80, 3), 80, np.uint8)
    image[30:44] = 220
    for y in range(44, 55):
        image[y] = 55 + abs(y - 49) * 4
    image[55:] = 180
    image[72:76] = 45
    case = dict(
        native_bbox=[0, 0, 80, 100],
        x_span=[10, 70],
        curves=[
            dict(id="inner", kind="rise", search_native_y=[25, 35]),
            dict(id="outer", kind="fall", search_native_y=[40, 48]),
            dict(id="gap", kind="valley", search_native_y=[46, 54]),
            dict(id="mos", kind="rise", search_native_y=[52, 60]),
        ],
        regions=[
            dict(material=0, above="inner", margin=3),
            dict(material=1, between=["inner", "outer"], margin=3),
            dict(material=0, around="gap", radius=1),
            dict(material=1, below="mos", margin=3),
        ],
    )
    settings = dict(blur_x=7, blur_y=3, curve_sigma=2, uncertainty_px=3, min_evidence=1)
    return image, case, settings


def test_internal_texture_does_not_punch_holes_and_edges_remain_unknown():
    image, case, settings = example()
    states, _ = reconstruct(image, case, settings)
    assert states[10, 40] == 0 and states[36, 40] == 1
    assert states[49, 40] == 0 and states[74, 40] == 1
    assert states[30, 40] == -1
    assert np.all(states[:, :10] == -1) and np.all(states[:, 70:] == -1)


def test_missing_edge_evidence_does_not_silently_label_background():
    image, case, settings = example()
    states, details = reconstruct(np.full_like(image, 100), case, settings)
    assert np.all(states == -1) and details["eligible_columns"] == 0


def test_unknown_center_is_reported_separately_from_correct_background():
    _, case, _ = example()
    states = np.full((100, 80), -1, np.int8)
    checks = [dict(native_xy=[40, 49], class_name="background")]
    metrics = reviewed_center_metrics(states, case, checks)
    assert metrics["unknown"] == 1 and metrics["correct"] == 0 and metrics["wrong"] == 0


def test_out_of_crop_edge_search_is_rejected():
    image, case, settings = example()
    case["curves"][0]["search_native_y"] = [-1, 35]
    with pytest.raises(ValueError, match="outside"):
        reconstruct(image, case, settings)
