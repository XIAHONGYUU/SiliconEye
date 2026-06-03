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

    def _align_by_coordinates(
        self, tiles: list[Tile]
    ) -> dict[str, np.ndarray]:
        """Align tiles using their bbox_um coordinates (preferred method)."""
        # TODO: implement coordinate-based alignment
        raise NotImplementedError

    def _align_by_features(
        self, tiles: list[Tile]
    ) -> dict[str, np.ndarray]:
        """Align tiles using ORB feature matching (fallback)."""
        # TODO: implement feature-based alignment
        raise NotImplementedError
