"""Segmentation evaluation must keep unmarked pixels unknown and holdouts out of fitting."""

import copy

import numpy as np
import pytest

from silicon_eye.aa_segmentation_eval import (
    annotation_mask,
    image_features,
    sparse_metrics,
    threshold_masks,
    training_rows,
)


def case(identifier, split):
    return dict(
        id=identifier,
        split=split,
        native_bbox=[0, 0, 32, 32],
        annotations=[
            dict(class_name="AA", native_xy=[8, 8], radius=3),
            dict(class_name="background", native_xy=[24, 24], radius=3),
        ],
    )


def test_unmarked_pixels_are_unknown_and_conflicting_seeds_rejected():
    sample = case("a", "train")
    labels = annotation_mask(sample)
    assert labels[0, 0] == -1 and labels[8, 8] == 1 and labels[24, 24] == 0
    sample["annotations"].append(dict(class_name="background", native_xy=[8, 8], radius=1))
    with pytest.raises(ValueError, match="Conflicting"):
        annotation_mask(sample)


def test_holdout_annotations_and_pixels_cannot_enter_training_rows():
    samples = [case("train", "train"), case("test", "holdout")]
    photos = {
        "train": np.full((32, 32, 3), 90, np.uint8),
        "test": np.full((32, 32, 3), 240, np.uint8),
    }
    settings = dict(seed=1, feature_sigmas=[1, 2], max_training_pixels_per_class=40)
    before = training_rows(samples, photos, settings)
    changed = copy.deepcopy(samples)
    changed[1]["annotations"][0]["class_name"] = "background"
    photos["test"][:] = 0
    after = training_rows(changed, photos, settings)
    for a, b in zip(before, after, strict=True):
        assert np.array_equal(a, b)


def test_sparse_metrics_do_not_score_unknown_background_as_correct():
    labels = np.array([[1, 0], [-1, -1]], np.int8)
    score = sparse_metrics(np.ones((2, 2), bool), labels)
    assert score["balanced_accuracy"] == 0.5 and score["fp"] == 1
    assert score["tn"] == 0 and score["tp"] == 1
    assert sparse_metrics(np.zeros((2, 2), bool), np.full((2, 2), -1))["balanced_accuracy"] is None


def test_thresholds_are_native_sized_binary_observations_without_rectangle_fill():
    raw = np.full((120, 160, 3), 50, np.uint8)
    raw[30:90, 30:65] = 200
    raw[30:90, 90:125] = 200
    settings = dict(blur_sigma=1.2, adaptive_block=51, adaptive_c=-5, illumination_sigma=40)
    masks = threshold_masks(raw, settings)
    for mask in masks.values():
        assert mask.shape == raw.shape[:2] and mask.dtype == bool
    assert not masks["otsu"][60, 78] and masks["otsu"][60, 45]
    features = image_features(raw, [1, 2])
    assert features.shape[:2] == raw.shape[:2] and np.isfinite(features).all()
