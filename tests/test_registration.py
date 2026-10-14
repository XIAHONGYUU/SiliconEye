"""Registration regression tests using known geometry, without real die images."""

from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from silicon_eye.phase1_image.stitcher import Stitcher


@pytest.fixture
def texture():
    cv2.setRNGSeed(0)
    rng = np.random.default_rng(17)
    image = rng.integers(10, 60, (384, 384), dtype=np.uint8)
    for _ in range(160):
        center = tuple(int(v) for v in rng.integers(20, 364, 2))
        cv2.circle(image, center, int(rng.integers(2, 9)), int(rng.integers(90, 250)), -1)
    return cv2.GaussianBlur(image, (3, 3), 0.6)


def homogeneous(matrix):
    return matrix if matrix.shape == (3, 3) else np.vstack([matrix, [0, 0, 1]])


def verify_alignment(reference, target, result, forward):
    assert result["success"], result["reason"]
    assert result["matrix_direction"] == "target_to_reference"
    assert result["warped"].shape == reference.shape
    assert result["warped"].dtype == target.dtype
    assert result["valid_mask"].dtype == bool
    assert result["valid_mask"].shape == reference.shape[:2]
    # These grid points are independent of the ORB fit's keypoints.
    points = np.float32([[80, 80], [300, 80], [80, 300], [300, 300], [190, 190]])
    target_points = cv2.perspectiveTransform(points[None], homogeneous(forward))
    recovered = cv2.perspectiveTransform(target_points, homogeneous(result["matrix"]))
    error = np.linalg.norm(recovered[0] - points, axis=1)
    assert error.max() <= 1.0, error

    def gray(image):
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image

    interior = np.zeros(reference.shape[:2], dtype=bool)
    interior[32:-32, 32:-32] = True
    mask = interior & result["valid_mask"]
    assert mask.sum() > 0.6 * interior.sum()
    expected = gray(reference).astype(float)
    before = np.sqrt(np.mean((gray(target).astype(float)[mask] - expected[mask]) ** 2))
    after = np.sqrt(np.mean((gray(result["warped"]).astype(float)[mask] - expected[mask]) ** 2))
    assert after < before * 0.5, (before, after)


@pytest.mark.parametrize("dx,dy", [(4, -3), (-4, 3), (2.5, -1.25)])
@pytest.mark.parametrize("color", [False, True])
def test_ecc_translation_direction_and_image(texture, dx, dy, color):
    reference = cv2.cvtColor(texture, cv2.COLOR_GRAY2BGR) if color else texture
    if color:
        reference[:, :, 1] //= 2
    forward = np.float32([[1, 0, dx], [0, 1, dy]])
    target = cv2.warpAffine(reference, forward, (384, 384))
    originals = reference.copy(), target.copy()
    result = Stitcher().register_layers(reference, target, method="ecc")
    verify_alignment(reference, target, result, forward)
    assert result["method"] == "ecc"
    assert result["rmse"] is None
    assert result["inlier_ratio"] is None
    assert result["correlation"] > 0.9
    assert not result["valid_mask"].all()
    np.testing.assert_array_equal(reference, originals[0])
    np.testing.assert_array_equal(target, originals[1])


@pytest.mark.parametrize("transform_type", ["similarity", "affine", "homography"])
@pytest.mark.parametrize("color", [False, True])
def test_orb_recovers_known_transform(texture, transform_type, color):
    if transform_type == "similarity":
        forward = cv2.getRotationMatrix2D((192, 192), 2.0, 1.01)
        forward[:, 2] += [4, -3]
    elif transform_type == "affine":
        forward = np.float64([[1.01, 0.012, 3], [-0.018, 0.99, 4]])
    else:
        forward = np.float64([[1.005, 0.01, 3], [-0.01, 1.002, 4], [0.00004, -0.00006, 1]])
    reference = cv2.cvtColor(texture, cv2.COLOR_GRAY2BGR) if color else texture
    if color:
        reference[:, :, 2] //= 2
    warp = cv2.warpPerspective if transform_type == "homography" else cv2.warpAffine
    target = warp(reference, forward, (384, 384))
    originals = reference.copy(), target.copy()
    result = Stitcher().register_layers(
        reference, target, method="orb", transform_type=transform_type
    )
    verify_alignment(reference, target, result, forward)
    assert result["matrix"].shape == ((3, 3) if transform_type == "homography" else (2, 3))
    assert result["num_matches"] >= 4
    assert 0 < result["inlier_ratio"] <= 1
    assert 0 <= result["rmse"] < 2
    assert result["correlation"] is None
    np.testing.assert_array_equal(reference, originals[0])
    np.testing.assert_array_equal(target, originals[1])


@pytest.mark.parametrize("method", ["ecc", "orb", "auto"])
def test_blank_images_fail_honestly(method):
    reference = np.zeros((128, 128), dtype=np.uint8)
    target = np.zeros((128, 128, 3), dtype=np.uint8)
    result = Stitcher().register_layers(reference, target, method=method)
    assert not result["success"]
    assert result["reason"] in {"constant_image", "insufficient_features"}
    assert result["rmse"] is None and result["correlation"] is None
    assert not result["valid_mask"].any()
    np.testing.assert_array_equal(result["warped"], target)
    assert not np.shares_memory(result["warped"], target)
    if method == "auto":
        assert [a["method"] for a in result["attempts"]] == ["ecc", "orb"]


def test_auto_falls_back_after_ecc_error(texture, monkeypatch):
    def fail(*args, **kwargs):
        raise cv2.error("test nonconvergence")

    monkeypatch.setattr(cv2, "findTransformECC", fail)
    result = Stitcher().register_layers(texture, texture, method="auto")
    assert result["success"] and result["method"] == "orb"
    assert result["attempts"][0]["reason"] == "ecc_not_converged"
    assert result["attempts"][1]["success"]


def test_fractional_border_coverage_is_excluded(texture, monkeypatch):
    inverse = np.float32([[1, 0, 2.5], [0, 1, -1.25]])
    monkeypatch.setattr(cv2, "findTransformECC", lambda *args, **kwargs: (0.9, inverse))
    result = Stitcher().register_layers(texture, texture, method="ecc")
    assert result["success"]
    expected = np.zeros(texture.shape, dtype=bool)
    expected[2:, :-3] = True
    np.testing.assert_array_equal(result["valid_mask"], expected)


def test_no_overlap_is_a_failure(texture, monkeypatch):
    inverse = np.float32([[1, 0, 1000], [0, 1, 0]])
    monkeypatch.setattr(cv2, "findTransformECC", lambda *args, **kwargs: (0.9, inverse))
    result = Stitcher().register_layers(texture, texture, method="ecc")
    assert not result["success"] and result["reason"] == "no_overlap"
    assert not result["valid_mask"].any()
    np.testing.assert_array_equal(result["warped"], texture)


def test_orb_and_auto_support_different_sizes(texture):
    target = texture[10:-10, 15:-15]
    for method in ("orb", "auto"):
        result = Stitcher().register_layers(texture, target, method=method)
        assert result["success"], result["reason"]
        assert result["warped"].shape == texture.shape
        np.testing.assert_allclose(result["matrix"][:, 2], [15, 10], atol=1)
        assert not result["valid_mask"].all()
        if method == "auto":
            assert result["attempts"][0]["reason"] == "size_mismatch"
    with pytest.raises(ValueError, match="equal spatial sizes"):
        Stitcher().register_layers(texture, target, method="ecc")


@pytest.mark.parametrize(
    "options",
    [
        {"method": "typo"},
        {"transform_type": "projective"},
        {"max_features": 3},
        {"max_features": 5.5},
        {"match_ratio": 0},
        {"match_ratio": 1},
        {"match_ratio": float("nan")},
    ],
)
def test_invalid_options(texture, options):
    with pytest.raises(ValueError):
        Stitcher().register_layers(texture, texture, **options)


@pytest.mark.parametrize(
    "image",
    [
        None,
        np.zeros((0, 8), dtype=np.uint8),
        np.zeros((7, 8), dtype=np.uint8),
        np.zeros((8, 8, 4), dtype=np.uint8),
        np.zeros((8, 8), dtype=np.float32),
        np.zeros((8,), dtype=np.uint8),
    ],
)
def test_invalid_images(image, texture):
    with pytest.raises(ValueError):
        Stitcher().register_layers(image, texture)


def test_short_neighbor_lists_are_skipped(texture, monkeypatch):
    matcher = SimpleNamespace(knnMatch=lambda *args, **kwargs: [[], [cv2.DMatch(0, 0, 1)]])
    monkeypatch.setattr(cv2, "BFMatcher", lambda *args, **kwargs: matcher)
    result = Stitcher().register_layers(texture, texture, method="orb")
    assert not result["success"] and result["reason"] == "insufficient_matches"
    assert result["num_matches"] == 0


@pytest.mark.parametrize("failure", ["none", "singular", "few_inliers", "nonfinite"])
def test_bad_estimates_fail(texture, monkeypatch, failure):
    def estimate(src, dst, **kwargs):
        matrix = np.eye(2, 3)
        inliers = np.ones((len(src), 1), dtype=np.uint8)
        if failure == "none":
            return None, None
        if failure == "singular":
            matrix[:] = 0
        if failure == "nonfinite":
            matrix[0, 0] = np.nan
        if failure == "few_inliers":
            inliers[3:] = 0
        return matrix, inliers

    monkeypatch.setattr(cv2, "estimateAffinePartial2D", estimate)
    result = Stitcher().register_layers(texture, texture, method="orb")
    assert not result["success"]
    assert result["reason"] in {"estimation_failed", "invalid_transform", "insufficient_inliers"}
    assert result["rmse"] is None


def test_perspective_rmse_is_root_mean_square_on_inliers(monkeypatch):
    matrix = np.float64([[1, 0, 3], [0, 1, 2], [0.001, 0.0005, 1]])
    src = np.float32([[20, 20], [80, 20], [20, 80], [80, 80], [50, 50]])
    dst = cv2.perspectiveTransform(src[None], matrix)[0]
    dst[:, 0] += [0, 1, 2, 3, 50]
    descriptors = np.zeros((5, 32), dtype=np.uint8)
    detections = iter(
        [
            ([cv2.KeyPoint(float(x), float(y), 1) for x, y in dst], descriptors),
            ([cv2.KeyPoint(float(x), float(y), 1) for x, y in src], descriptors),
        ]
    )
    detector = SimpleNamespace(detectAndCompute=lambda *args: next(detections))
    pairs = [[cv2.DMatch(i, i, 1), cv2.DMatch(i, (i + 1) % 5, 10)] for i in range(5)]
    matcher = SimpleNamespace(knnMatch=lambda *args, **kwargs: pairs)
    monkeypatch.setattr(cv2, "ORB_create", lambda **kwargs: detector)
    monkeypatch.setattr(cv2, "BFMatcher", lambda *args, **kwargs: matcher)
    monkeypatch.setattr(
        cv2, "findHomography", lambda *args: (matrix, np.uint8([[1], [1], [1], [1], [0]]))
    )
    blank = np.zeros((128, 128), dtype=np.uint8)
    result = Stitcher().register_layers(blank, blank, method="orb", transform_type="homography")
    assert result["success"]
    assert result["rmse"] == pytest.approx(np.sqrt(3.5), abs=1e-5)
    assert result["inlier_ratio"] == 0.8
