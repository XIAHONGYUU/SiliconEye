"""Extractor: parameter extraction from segmented device regions.

Measures device dimensions (W, L for transistors; values for passives)
from the segmented regions on layer images.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..common.geometry import BBox
from ..schemas.annotation import Annotations
from ..schemas.devices import DeviceList, DeviceType, ExtractedDevice, Terminal
from ..schemas.layer_image import LayerImage
from .segmenter import SegmentedRegion

logger = logging.getLogger(__name__)


class Extractor:
    """Extracts device parameters from segmented regions."""

    def __init__(
        self,
        pixel_per_um: float,
        min_device_area_um2: float = 1.0,
        wl_confidence_threshold: float = 0.6,
    ):
        self.pixel_per_um = pixel_per_um
        self.min_area = min_device_area_um2
        self.wl_threshold = wl_confidence_threshold

    def extract(
        self,
        regions: list[SegmentedRegion],
        images: list[LayerImage],
        annotations: Annotations,
    ) -> DeviceList:
        """Extract device parameters from segmented regions.

        Args:
            regions: Output from Segmenter.
            images: Layer images (for pixel-level measurement).
            annotations: Human annotations for hints and overrides.

        Returns:
            DeviceList with extracted devices.
        """
        devices: list[ExtractedDevice] = []
        device_counter: dict[DeviceType, int] = {}

        for region in regions:
            if region.confidence < self.wl_threshold:
                continue

            # Check against manual device_hints
            for hint in annotations.device_hints:
                hint_bbox = BBox(*hint.bbox_um)
                region_bbox = BBox(*region.bbox_um)
                if region_bbox.iou(hint_bbox) > 0.5:
                    if "DUMMY" in hint.label.upper():
                        continue  # Skip dummy
                    region.confidence = max(region.confidence, hint.confidence)

            # Measure W, L from images
            w_um, l_um = self._measure_transistor(region, images)

            # Generate device ID
            prefix = self._type_prefix(region.device_type)
            device_counter[region.device_type] = (
                device_counter.get(region.device_type, 0) + 1
            )
            device_id = f"{prefix}{device_counter[region.device_type]}"

            devices.append(
                ExtractedDevice(
                    id=device_id,
                    type=region.device_type,
                    bbox_um=region.bbox_um,
                    area_um2=BBox(*region.bbox_um).area,
                    confidence=region.confidence,
                    w_um=w_um,
                    l_um=l_um,
                    fingers=None,  # TODO: detect multi-finger
                    terminals=self._find_terminals(region),
                )
            )

        return DeviceList(
            metadata={"extraction_method": "rule_based"},
            devices=devices,
        )

    def _type_prefix(self, device_type: DeviceType) -> str:
        prefixes = {
            DeviceType.NMOS: "M",
            DeviceType.PMOS: "M",
            DeviceType.RESISTOR: "R",
            DeviceType.MIM_CAP: "C",
            DeviceType.MOM_CAP: "C",
            DeviceType.UNKNOWN: "X",
        }
        return prefixes.get(device_type, "X")

    def _measure_transistor(
        self, region: SegmentedRegion, images: list[LayerImage]
    ) -> tuple[float | None, float | None]:
        """Measure W and L of a transistor from layer images."""
        # TODO: implement actual W/L measurement from pixel data
        # W = diffusion width perpendicular to gate
        # L = poly width (gate length)
        return None, None

    def _find_terminals(self, region: SegmentedRegion) -> list[Terminal]:
        """Locate device terminals (gate, source, drain for transistors)."""
        # TODO: implement terminal localization
        return []
