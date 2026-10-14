"""Stitcher: align and merge overlapping tile images.

Handles multi-tile alignment and single-tile pass-through.
"""

from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np

from ..schemas.layer_image import LayerImage, TileSet

logger = logging.getLogger(__name__)


class Stitcher:
    """Aligns and merges overlapping tile images into a unified per-layer image.

    When all tiles have bbox_um defined, alignment uses physical coordinates.
    When tiles lack bbox info, falls back to ORB feature matching.
    """

    def __init__(self, feature_threshold: float = 0.7):
        self.feature_threshold = feature_threshold

    def stitch(self, tile_set: TileSet, output_dir: Path) -> list[LayerImage]:
        """Stitch all tiles into unified per-layer images.

        Args:
            tile_set: Input tiles with per-layer images.
            output_dir: Directory for stitched output images.

        Returns:
            Single unified LayerImage per layer.
        """
        if len(tile_set.tiles) == 1:
            logger.info("Single tile — skipping stitch, passing through")
            return tile_set.tiles[0].images

        # TODO: multi-tile stitching via coordinate alignment or feature matching
        logger.warning("Multi-tile stitching not yet implemented; using first tile only")
        return tile_set.tiles[0].images

    def register_layers(
        self,
        reference: np.ndarray,
        target: np.ndarray,
        method: str = "auto",
        max_features: int = 5000,
        match_ratio: float = 0.75,
        transform_type: str = "similarity",
    ) -> dict:
        """Align uint8 grayscale/BGR target to reference without changing inputs.

        All returned matrices map target pixel coordinates to reference pixels.
        ECC estimates translation; transform_type applies only to ORB. Successful
        warped images retain target channels and have reference spatial size.
        valid_mask excludes border fill. ECC correlation is not geometric error;
        rmse/inlier_ratio are None when not measured. ORB rmse is inlier
        reprojection RMS distance in pixels, not independent validation error.

        Expected algorithm failures return success=False, a reason, an identity
        placeholder and an unchanged target copy. Invalid inputs raise ValueError.
        auto records attempts and falls back from ECC to ORB. Different spatial
        sizes are supported by ORB only; auto skips ECC for these inputs.
        """
        ref_gray = self._gray(reference)
        tgt_gray = self._gray(target)
        if method not in {"auto", "ecc", "orb"}:
            raise ValueError("method must be auto, ecc or orb")
        if transform_type not in {"similarity", "affine", "homography"}:
            raise ValueError("transform_type must be similarity, affine or homography")
        if not isinstance(max_features, int) or isinstance(max_features, bool) or max_features < 4:
            raise ValueError("max_features must be an integer >= 4")
        if not isinstance(match_ratio, (int, float)) or not 0 < match_ratio < 1:
            raise ValueError("match_ratio must be between 0 and 1")
        if method == "ecc" and ref_gray.shape != tgt_gray.shape:
            raise ValueError("ECC requires equal spatial sizes")

        attempts = []
        if method in {"auto", "ecc"}:
            if ref_gray.shape == tgt_gray.shape:
                result = self._register_ecc(ref_gray, tgt_gray, target)
                attempts.append(
                    {"method": "ecc", "success": result["success"], "reason": result["reason"]}
                )
                if result["success"] or method == "ecc":
                    result["attempts"] = attempts
                    return result
            else:
                attempts.append({"method": "ecc", "success": False, "reason": "size_mismatch"})

        result = self._register_orb(
            ref_gray, tgt_gray, target, max_features, match_ratio, transform_type
        )
        attempts.append({"method": "orb", "success": result["success"], "reason": result["reason"]})
        result["attempts"] = attempts
        return result

    @staticmethod
    def _gray(image: np.ndarray) -> np.ndarray:
        if not isinstance(image, np.ndarray) or image.dtype != np.uint8:
            raise ValueError("images must be uint8 numpy arrays")
        if image.ndim not in {2, 3} or min(image.shape[:2], default=0) < 8:
            raise ValueError("images must have spatial size at least 8 x 8")
        if image.ndim == 3:
            if image.shape[2] != 3:
                raise ValueError("color images must have three BGR channels")
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return np.ascontiguousarray(image)

    @staticmethod
    def _failure(
        target: np.ndarray,
        ref_shape: tuple[int, int],
        method: str,
        reason: str,
        num_matches: int = 0,
        homography: bool = False,
    ) -> dict:
        logger.debug("%s registration failed: %s", method, reason)
        return {
            "warped": target.copy(),
            "matrix": np.eye(3, dtype=np.float64) if homography else np.eye(2, 3),
            "matrix_direction": "target_to_reference",
            "method": method,
            "success": False,
            "reason": reason,
            "num_matches": num_matches,
            "inlier_ratio": None,
            "rmse": None,
            "correlation": None,
            "valid_mask": np.zeros(ref_shape, dtype=bool),
        }

    @staticmethod
    def _warp(
        target: np.ndarray, matrix: np.ndarray, ref_shape: tuple[int, int]
    ) -> tuple[np.ndarray, np.ndarray]:
        height, width = ref_shape
        warp = cv2.warpPerspective if matrix.shape == (3, 3) else cv2.warpAffine
        warped = warp(
            target, matrix, (width, height), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT
        )
        coverage = warp(
            np.ones(target.shape[:2], dtype=np.float32),
            matrix,
            (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
        )
        return warped, coverage >= 1.0 - 1e-6

    def _register_ecc(self, ref_gray: np.ndarray, tgt_gray: np.ndarray, target: np.ndarray) -> dict:
        if ref_gray.std() == 0 or tgt_gray.std() == 0:
            return self._failure(target, ref_gray.shape, "ecc", "constant_image")
        try:
            correlation, inverse_matrix = cv2.findTransformECC(
                ref_gray,
                tgt_gray,
                np.eye(2, 3, dtype=np.float32),
                cv2.MOTION_TRANSLATION,
                (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 1000, 1e-6),
                inputMask=None,
                gaussFiltSize=5,
            )
            if not np.isfinite(correlation) or not np.isfinite(inverse_matrix).all():
                return self._failure(target, ref_gray.shape, "ecc", "nonfinite_estimate")
            # ECC estimates reference -> target, unlike ORB's target -> reference.
            matrix = cv2.invertAffineTransform(inverse_matrix)
            warped, valid_mask = self._warp(target, matrix, ref_gray.shape)
        except cv2.error:
            return self._failure(target, ref_gray.shape, "ecc", "ecc_not_converged")
        if not valid_mask.any():
            return self._failure(target, ref_gray.shape, "ecc", "no_overlap")
        return {
            "warped": warped,
            "matrix": matrix,
            "matrix_direction": "target_to_reference",
            "method": "ecc",
            "success": True,
            "reason": None,
            "num_matches": 0,
            "inlier_ratio": None,
            "rmse": None,
            "correlation": float(correlation),
            "valid_mask": valid_mask,
        }

    def _register_orb(
        self,
        ref_gray: np.ndarray,
        tgt_gray: np.ndarray,
        target: np.ndarray,
        max_features: int,
        match_ratio: float,
        transform_type: str,
    ) -> dict:
        homography = transform_type == "homography"
        num_matches = 0
        try:
            orb = cv2.ORB_create(nfeatures=max_features)
            kp_ref, des_ref = orb.detectAndCompute(ref_gray, None)
            kp_tgt, des_tgt = orb.detectAndCompute(tgt_gray, None)
            if des_ref is None or des_tgt is None or min(len(des_ref), len(des_tgt)) < 4:
                return self._failure(
                    target, ref_gray.shape, "orb", "insufficient_features", homography=homography
                )
            matches = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(des_ref, des_tgt, k=2)
            good = [
                pair[0]
                for pair in matches
                if len(pair) == 2 and pair[0].distance < match_ratio * pair[1].distance
            ]
            num_matches = len(good)
            if num_matches < 4:
                return self._failure(
                    target, ref_gray.shape, "orb", "insufficient_matches", num_matches, homography
                )
            src_pts = np.float32([kp_tgt[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp_ref[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            if homography:
                matrix, inliers = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 3.0)
            else:
                estimate = (
                    cv2.estimateAffinePartial2D
                    if transform_type == "similarity"
                    else cv2.estimateAffine2D
                )
                matrix, inliers = estimate(
                    src_pts,
                    dst_pts,
                    method=cv2.RANSAC,
                    ransacReprojThreshold=3.0,
                    maxIters=2000,
                    confidence=0.99,
                )
            if matrix is None or inliers is None:
                return self._failure(
                    target, ref_gray.shape, "orb", "estimation_failed", num_matches, homography
                )
            full_matrix = matrix if homography else np.vstack([matrix, [0, 0, 1]])
            if not np.isfinite(matrix).all() or abs(np.linalg.det(full_matrix)) < 1e-12:
                return self._failure(
                    target, ref_gray.shape, "orb", "invalid_transform", num_matches, homography
                )
            inlier_mask = inliers.ravel().astype(bool)
            num_inliers = int(inlier_mask.sum())
            if num_inliers < 4:
                return self._failure(
                    target, ref_gray.shape, "orb", "insufficient_inliers", num_matches, homography
                )
            projected = cv2.perspectiveTransform(src_pts[inlier_mask], full_matrix)
            distances_squared = np.sum((projected - dst_pts[inlier_mask]) ** 2, axis=2)
            rmse = float(np.sqrt(np.mean(distances_squared)))
            if not np.isfinite(rmse):
                return self._failure(
                    target, ref_gray.shape, "orb", "nonfinite_error", num_matches, homography
                )
            warped, valid_mask = self._warp(target, matrix, ref_gray.shape)
        except cv2.error:
            return self._failure(
                target, ref_gray.shape, "orb", "opencv_error", num_matches, homography
            )
        if not valid_mask.any():
            return self._failure(
                target, ref_gray.shape, "orb", "no_overlap", num_matches, homography
            )
        return {
            "warped": warped,
            "matrix": matrix,
            "matrix_direction": "target_to_reference",
            "method": "orb",
            "success": True,
            "reason": None,
            "num_matches": num_matches,
            "inlier_ratio": num_inliers / num_matches,
            "rmse": rmse,
            "correlation": None,
            "valid_mask": valid_mask,
        }
