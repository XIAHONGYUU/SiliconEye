"""Stitcher: align and merge overlapping tile images.

Handles multi-tile alignment and single-tile pass-through.
"""

from __future__ import annotations

import logging
from pathlib import Path

import cv2
import numpy as np

from ..schemas.layer_image import LayerImage, Tile, TileSet

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
        logger.warning(
            "Multi-tile stitching not yet implemented; using first tile only"
        )
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
        """Register (align) a target image to a reference image.

        Supports two methods:
        - 'ecc': Enhanced Correlation Coefficient — intensity-based, best for
          cross-layer die images where patterns differ but geometry correlates.
          Fast, works well for small offsets (<50px).
        - 'orb': ORB feature detection + RANSAC — works for same-layer tile
          stitching where feature patterns are similar.
        - 'auto': tries ECC first, falls back to ORB.

        Args:
            reference: The reference (base) image to align TO.
            target: The target image to warp/align.
            method: 'ecc', 'orb', or 'auto'.
            max_features: Max ORB features (ORB method only).
            match_ratio: Lowe's ratio test threshold (ORB method only).
            transform_type: 'similarity', 'affine', or 'homography' (ORB only).

        Returns:
            Dict with warped, matrix, num_matches, inlier_ratio, rmse, success.
        """
        # Convert to grayscale if needed
        if len(reference.shape) == 3:
            ref_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
        else:
            ref_gray = reference
        if len(target.shape) == 3:
            tgt_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
        else:
            tgt_gray = target

        # Method dispatch
        if method in ("ecc", "auto"):
            result = self._register_ecc(ref_gray, tgt_gray)
            if result["success"] or method == "ecc":
                return result

        return self._register_orb(
            ref_gray, tgt_gray, max_features, match_ratio, transform_type
        )

    def _register_ecc(
        self, ref_gray: np.ndarray, tgt_gray: np.ndarray
    ) -> dict:
        """ECC-based registration for small-offset cross-layer alignment."""
        warp_matrix = np.eye(2, 3, dtype=np.float32)
        criteria = (
            cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 5000, 1e-10
        )

        try:
            cc, warp_matrix = cv2.findTransformECC(
                ref_gray, tgt_gray, warp_matrix,
                cv2.MOTION_TRANSLATION, criteria, gaussFiltSize=5,
            )
            h, w = ref_gray.shape
            warped = cv2.warpAffine(
                tgt_gray if len(tgt_gray.shape) == 2 else
                cv2.cvtColor(tgt_gray, cv2.COLOR_GRAY2BGR),
                warp_matrix, (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
            )
            ox, oy = warp_matrix[0, 2], warp_matrix[1, 2]
            logger.info(
                "ECC registration: offset=(%.1f, %.1f) px, correlation=%.4f",
                ox, oy, cc,
            )
            return {
                "warped": warped,
                "matrix": warp_matrix,
                "num_matches": 0,
                "inlier_ratio": 1.0,
                "rmse": 0.0,
                "success": True,
            }
        except Exception as e:
            logger.debug("ECC registration failed: %s", e)
            return {
                "warped": tgt_gray,
                "matrix": np.eye(2, 3, dtype=np.float32),
                "num_matches": 0,
                "inlier_ratio": 0.0,
                "rmse": float("inf"),
                "success": False,
            }

    def _register_orb(
        self,
        ref_gray: np.ndarray,
        tgt_gray: np.ndarray,
        max_features: int,
        match_ratio: float,
        transform_type: str,
    ) -> dict:
        """ORB feature-based registration for same-layer tile stitching."""

        # 1. Detect ORB features
        orb = cv2.ORB_create(nfeatures=max_features)
        kp_ref, des_ref = orb.detectAndCompute(ref_gray, None)
        kp_tgt, des_tgt = orb.detectAndCompute(tgt_gray, None)

        if des_ref is None or des_tgt is None or len(des_ref) < 4 or len(des_tgt) < 4:
            logger.warning(
                "Insufficient features: ref=%d, tgt=%d",
                len(des_ref) if des_ref is not None else 0,
                len(des_tgt) if des_tgt is not None else 0,
            )
            return {
                "warped": target,
                "matrix": np.eye(2, 3, dtype=np.float32),
                "num_matches": 0,
                "inlier_ratio": 0.0,
                "rmse": float("inf"),
                "success": False,
            }

        # 2. Match features with ratio test
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(des_ref, des_tgt, k=2)

        good_matches = []
        for m, n in matches:
            if m.distance < match_ratio * n.distance:
                good_matches.append(m)

        if len(good_matches) < 4:
            logger.warning("Too few good matches: %d", len(good_matches))
            return {
                "warped": target,
                "matrix": np.eye(2, 3, dtype=np.float32),
                "num_matches": len(good_matches),
                "inlier_ratio": 0.0,
                "rmse": float("inf"),
                "success": False,
            }

        # 3. Extract matched point coordinates
        src_pts = np.float32([
            kp_tgt[m.trainIdx].pt for m in good_matches
        ]).reshape(-1, 1, 2)
        dst_pts = np.float32([
            kp_ref[m.queryIdx].pt for m in good_matches
        ]).reshape(-1, 1, 2)

        # 4. Estimate transform
        if transform_type == "similarity":
            matrix, inliers = cv2.estimateAffinePartial2D(
                src_pts, dst_pts, method=cv2.RANSAC,
                ransacReprojThreshold=3.0, maxIters=2000, confidence=0.99,
            )
        elif transform_type == "affine":
            matrix, inliers = cv2.estimateAffine2D(
                src_pts, dst_pts, method=cv2.RANSAC,
                ransacReprojThreshold=3.0, maxIters=2000, confidence=0.99,
            )
        else:  # homography
            matrix, inliers = cv2.findHomography(
                src_pts, dst_pts, cv2.RANSAC, ransacReprojThreshold=3.0,
            )

        if matrix is None:
            logger.warning("Transform estimation failed")
            return {
                "warped": target,
                "matrix": np.eye(2, 3, dtype=np.float32),
                "num_matches": len(good_matches),
                "inlier_ratio": 0.0,
                "rmse": float("inf"),
                "success": False,
            }

        # 5. Warp target image
        h, w = reference.shape[:2]
        warped = cv2.warpAffine(
            target, matrix, (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
        )

        # 6. Compute quality metrics
        num_inliers = int(inliers.sum()) if inliers is not None else 0
        inlier_ratio = num_inliers / len(good_matches) if good_matches else 0

        # RMSE on inliers
        if num_inliers > 0 and transform_type != "homography":
            inlier_mask = inliers.ravel().astype(bool)
            src_in = src_pts[inlier_mask].reshape(-1, 2)
            dst_in = dst_pts[inlier_mask].reshape(-1, 2)
            src_h = np.hstack([src_in, np.ones((src_in.shape[0], 1))])
            projected = (matrix @ src_h.T).T
            errors = np.sqrt(np.sum((projected[:, :2] - dst_in) ** 2, axis=1))
            rmse = float(np.mean(errors))
        else:
            rmse = float("inf")

        logger.info(
            "Registration: %d matches, %d inliers (%.1f%%), RMSE=%.2f px",
            len(good_matches), num_inliers,
            100 * inlier_ratio, rmse,
        )

        return {
            "warped": warped,
            "matrix": matrix,
            "num_matches": len(good_matches),
            "inlier_ratio": inlier_ratio,
            "rmse": rmse,
            "success": num_inliers >= 4,
        }
