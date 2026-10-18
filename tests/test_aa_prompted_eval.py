"""Prompted evaluation keeps the human center contract and excludes prompts from scoring."""

import copy

import numpy as np
import pytest

from silicon_eye.aa_prompted_eval import check_labels, local_masks


def sample_case():
    return dict(
        native_bbox=[0, 0, 80, 60],
        prompts=[
            dict(class_name="AA", native_xy=[10, 10], radius=3),
            dict(class_name="AA", native_xy=[10, 40], radius=3),
            dict(class_name="background", native_xy=[10, 25], radius=1),
        ],
        checks=[
            dict(class_name="AA", native_xy=[50, 10]),
            dict(class_name="background", native_xy=[50, 25]),
        ],
    )


def test_only_nonprompt_center_pixels_are_scored():
    labels = check_labels(sample_case())
    assert np.count_nonzero(labels >= 0) == 2
    assert labels[10, 50] == 1 and labels[25, 50] == 0
    assert labels[10, 10] == -1 and labels[10, 49] == -1


def test_prompt_neighborhood_overlap_is_rejected():
    case = sample_case()
    case["checks"][0]["native_xy"] = [13, 13]
    with pytest.raises(ValueError, match="overlaps prompt"):
        check_labels(case)


def test_check_labels_do_not_affect_predictions_and_local_contrast_is_recovered():
    pytest.importorskip("sklearn")
    rng = np.random.default_rng(3)
    raw = np.full((60, 80, 3), 40, np.int16)
    raw[5:20] = 180
    raw[35:50] = 180
    raw = np.clip(raw + rng.integers(-12, 13, raw.shape), 0, 255).astype(np.uint8)
    settings = dict(
        seed=2,
        feature_sigmas=[1, 2],
        forest_trees=20,
        forest_max_depth=8,
        grabcut_iterations=3,
        refine_from_fixed=True,
    )
    case = sample_case()
    first, _ = local_masks(raw, case, settings)
    changed = copy.deepcopy(case)
    changed["checks"] = []
    second, _ = local_masks(raw, changed, settings)
    for method in first:
        assert np.array_equal(first[method], second[method])
    assert first["local_rf"][10, 50] and not first["local_rf"][25, 50]
