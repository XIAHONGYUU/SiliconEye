"""Native canvas preserves coordinates, peer conflicts, unknowns and inference seams."""

import numpy as np
import pytest

from silicon_eye.aa_native_canvas import (
    place_local,
    probabilities_to_states,
    review_grid,
    run,
    strip_probabilities,
)
from silicon_eye.aa_segmentation_eval import image_features


def test_uncalibrated_middle_scores_and_nan_remain_unknown():
    p = np.array([[0, 0.2, 0.5, 0.8, 1, np.nan]], np.float32)
    np.testing.assert_array_equal(probabilities_to_states(p, 0.2, 0.8), [[0, 0, -1, 1, 1, -1]])


def test_local_placement_is_translation_and_preserves_its_unknown_band():
    canvas = np.zeros((9, 12), np.int8)
    seen = np.zeros(canvas.shape, bool)
    flags = seen.copy()
    contributors = np.zeros(canvas.shape, np.uint16)
    local = np.array([[1, -1], [0, 1]], np.int8)
    place_local(
        canvas, seen, flags, contributors, local, np.ones(local.shape, bool), [4, 3, 6, 5], 1
    )
    np.testing.assert_array_equal(canvas[3:5, 4:6], local)
    assert not seen[:3].any() and seen.sum() == 4
    assert np.all(contributors[3:5, 4:6] == 1)


def test_equal_rank_contradictions_stay_unknown_without_majority_voting():
    canvas = np.zeros((4, 4), np.int8)
    seen = np.zeros(canvas.shape, bool)
    flags = seen.copy()
    contributors = np.zeros(canvas.shape, np.uint16)
    bbox = [1, 1, 3, 3]
    domain = np.ones((2, 2), bool)
    place_local(canvas, seen, flags, contributors, np.ones((2, 2), np.int8), domain, bbox, 1)
    place_local(canvas, seen, flags, contributors, np.zeros((2, 2), np.int8), domain, bbox, 2)
    place_local(canvas, seen, flags, contributors, np.ones((2, 2), np.int8), domain, bbox, 4)
    assert np.all(canvas[1:3, 1:3] == -1) and flags[1:3, 1:3].all()
    assert np.all(contributors[1:3, 1:3] == 7)


def test_review_grid_covers_native_roi_exactly_without_gaps_or_overlap():
    counts = np.zeros((100, 120), np.uint8)
    tiles = review_grid([7, 11, 110, 90], 4, 3, "N")
    for tile in tiles:
        x, y, r, b = tile["native_bbox"]
        counts[y:b, x:r] += 1
    assert len(tiles) == 12 and np.all(counts[11:90, 7:110] == 1)
    assert counts.sum() == 103 * 79 and counts.max() == 1


def test_strip_halo_has_no_inference_boundary_discontinuity():
    rng = np.random.default_rng(7)
    image = rng.integers(0, 256, (173, 190, 3), dtype=np.uint8)
    sigmas = [1, 2, 4, 8]

    class ProbeModel:
        def predict_proba(self, features):
            p = np.clip(features[:, [0, 3, 5, 8, 11, 14]].mean(axis=1), 0, 1)
            return np.stack([1 - p, p], axis=1)

    model = ProbeModel()
    features = image_features(image, sigmas)
    expected = model.predict_proba(features.reshape(-1, features.shape[-1]))[:, 1].reshape(173, 190)
    actual = strip_probabilities(
        image, model, dict(halo=48, strip_height=41, feature_sigmas=sigmas)
    )
    np.testing.assert_allclose(actual, expected, atol=1e-6)


def test_coordinate_request_cannot_trigger_training_or_create_output(tmp_path):
    output = tmp_path / "result"
    with pytest.raises(ValueError, match="not coordinate assembly"):
        run(tmp_path, tmp_path / "missing-spec.json", output)
    assert not output.exists()
