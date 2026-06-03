"""Segmenter: device segmentation on layer images.

Uses SAM 3 (optional) or rule-based methods to identify device regions.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import cv2
import numpy as np

from ..common.geometry import BBox
from ..common.types import Um
from ..schemas.annotation import Annotations
from ..schemas.devices import DeviceType
from ..schemas.layer_image import LayerImage

logger = logging.getLogger(__name__)

SegmenterMode = Literal["sam3", "rule_based", "none"]


class Segmenter:
    """Device segmentation using SAM 3 or rule-based heuristics."""

    def __init__(
        self,
        mode: SegmenterMode = "rule_based",
        confidence_threshold: float = 0.7,
    ):
        self.mode = mode
        self.confidence_threshold = confidence_threshold
        self._sam_predictor = None

    def segment(
        self,
        images: list[LayerImage],
        annotations: Annotations,
        pixel_per_um: float,
    ) -> list[SegmentedRegion]:
        """Segment devices from layer images.

        Returns list of SegmentedRegion with type, bbox, confidence.
        """
        if self.mode == "none":
            logger.info("Segmenter disabled — relying on manual annotations only")
            return []

        if self.mode == "sam3":
            return self._segment_sam3(images, annotations, pixel_per_um)

        return self._segment_rule_based(images, annotations, pixel_per_um)

    def _segment_rule_based(
        self,
        images: list[LayerImage],
        annotations: Annotations,
        pixel_per_um: float,
    ) -> list[SegmentedRegion]:
        """Rule-based segmentation using color filtering and contour detection.

        This is the fallback when SAM 3 is not available. Works well on
        color-annotated images and clean die photographs.
        """
        regions: list[SegmentedRegion] = []
        # TODO: implement rule-based segmentation
        # - Load each layer image
        # - Find poly layer
        # - Find diffusion layers
        # - Intersect poly ∩ p_diffusion → NMOS candidates
        # - Intersect poly ∩ n_diffusion → PMOS candidates
        # - Detect long narrow strips → resistor candidates
        # - Detect parallel plate pairs → MIM candidate
        # - Detect interdigitated fingers → MOM candidates
        logger.warning("Rule-based segmentation not yet implemented")
        return regions

    def _segment_sam3(
        self,
        images: list[LayerImage],
        annotations: Annotations,
        pixel_per_um: float,
    ) -> list[SegmentedRegion]:
        """SAM 3-based segmentation with text prompts from annotations.

        Requires: pip install git+https://github.com/facebookresearch/sam3.git
        """
        try:
            # Lazy import — SAM 3 is optional
            pass  # TODO: implement SAM 3 integration
        except ImportError:
            logger.warning("SAM 3 not installed; falling back to rule_based")
            return self._segment_rule_based(images, annotations, pixel_per_um)

        regions: list[SegmentedRegion] = []
        # TODO:
        # - Build text prompts from global_hints
        # - Pass per-layer images to SAM 3
        # - Parse masks into SegmentedRegion list
        logger.warning("SAM 3 integration not yet implemented")
        return regions


class SegmentedRegion:
    """A candidate device region from segmentation."""

    __slots__ = ("device_type", "bbox_um", "confidence")

    def __init__(
        self,
        device_type: DeviceType,
        bbox_um: tuple[Um, Um, Um, Um],
        confidence: float,
    ):
        self.device_type = device_type
        self.bbox_um = bbox_um
        self.confidence = confidence
