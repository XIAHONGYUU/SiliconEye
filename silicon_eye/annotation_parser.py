"""Annotation Parser: extract labels from color-block annotated images.

Parses an annotated copy of a die image where the user has painted
colored rectangles directly on the photo:

  🔴 #FF0000 → NMOS
  🔵 #0000FF → PMOS
  🟢 #00FF00 → Resistor
  🟡 #FFFF00 → MIM capacitor
  🟣 #800080 → MOM capacitor
  ⚫ #808080 → DUMMY (ignore)

Usage:
    silicon-eye annotate parse -i chip_annotated.png -o chip_config.yaml

Or via API:
    from silicon_eye.annotation_parser import parse_color_annotations
    devices, regions = parse_color_annotations("chip_annotated.png", pixel_per_um=20.0)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import yaml

from .common.geometry import BBox

logger = logging.getLogger(__name__)

# Color → Device type mapping (BGR order for OpenCV)
COLOR_MAP: dict[tuple[int, int, int], str] = {
    (0, 0, 255): "nmos",       # Red → NMOS
    (255, 0, 0): "pmos",       # Blue → PMOS
    (0, 255, 0): "resistor",   # Green → Resistor
    (0, 255, 255): "mim_cap",  # Yellow → MIM capacitor
    (128, 0, 128): "mom_cap",  # Purple → MOM capacitor
    (128, 128, 128): "dummy",  # Gray → DUMMY
}

COLOR_TOLERANCE = 30  # RGB tolerance for color matching


@dataclass
class ParsedAnnotation:
    """A single parsed annotation from a color block."""

    label: str
    bbox_px: tuple[int, int, int, int]  # (x, y, w, h) in pixels
    color_bgr: tuple[int, int, int]
    confidence: float = 1.0


def _color_match(
    pixel: np.ndarray, target: tuple[int, int, int], tolerance: int = COLOR_TOLERANCE
) -> bool:
    """Check if a pixel color matches a target color within tolerance."""
    return bool(np.all(np.abs(pixel.astype(int) - np.array(target)) <= tolerance))


def _find_contiguous_rect(
    mask: np.ndarray, start_y: int, start_x: int
) -> tuple[int, int, int, int] | None:
    """Find the bounding rectangle of a contiguous colored region using flood fill.

    Returns (x, y, w, h) in pixels, or None if region too small.
    """
    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    stack = [(start_y, start_x)]
    visited[start_y, start_x] = True

    min_y, max_y = start_y, start_y
    min_x, max_x = start_x, start_x

    while stack:
        y, x = stack.pop()
        min_y = min(min_y, y)
        max_y = max(max_y, y)
        min_x = min(min_x, x)
        max_x = max(max_x, x)

        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not visited[ny, nx]:
                visited[ny, nx] = True
                stack.append((ny, nx))

    region_w = max_x - min_x + 1
    region_h = max_y - min_y + 1

    # Filter noise: require at least 10x10 pixels
    if region_w < 10 or region_h < 10:
        return None

    return (min_x, min_y, region_w, region_h)


def parse_color_annotations(
    image_path: str | Path,
    pixel_per_um: float,
    min_area_px: int = 100,
) -> tuple[list[ParsedAnnotation], dict]:
    """Parse color-block annotations from an image.

    Args:
        image_path: Path to the annotated image.
        pixel_per_um: Image scale (pixels per micrometer).
        min_area_px: Minimum region area in pixels to consider.

    Returns:
        (annotations_list, config_dict) — parsed annotations and YAML-ready config.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    h, w = img.shape[:2]
    logger.info("Parsing annotations from %s (%dx%d)", image_path, w, h)

    annotations: list[ParsedAnnotation] = []

    for color_bgr, label in COLOR_MAP.items():
        # Create mask for this color
        mask = np.zeros((h, w), dtype=bool)
        for y in range(h):
            for x in range(w):
                if _color_match(img[y, x], color_bgr):
                    mask[y, x] = True

        # Find contiguous regions
        visited_global = np.zeros((h, w), dtype=bool)
        for y in range(h):
            for x in range(w):
                if mask[y, x] and not visited_global[y, x]:
                    rect = _find_contiguous_rect(mask, y, x)
                    if rect is None:
                        continue

                    rx, ry, rw, rh = rect
                    if rw * rh < min_area_px:
                        continue

                    # Mark region as visited
                    visited_global[ry : ry + rh, rx : rx + rw] = True

                    annotations.append(
                        ParsedAnnotation(
                            label=label,
                            bbox_px=rect,
                            color_bgr=color_bgr,
                        )
                    )

    logger.info("Found %d annotated regions", len(annotations))

    # Convert to YAML-ready config
    config = _annotations_to_config(annotations, pixel_per_um, w, h)

    return annotations, config


def _annotations_to_config(
    annotations: list[ParsedAnnotation],
    pixel_per_um: float,
    img_w: int,
    img_h: int,
) -> dict:
    """Convert parsed annotations to a chip config dictionary."""
    device_hints = []
    regions = []
    global_hints = []

    img_w_um = img_w / pixel_per_um
    img_h_um = img_h / pixel_per_um

    for ann in annotations:
        x_px, y_px, w_px, h_px = ann.bbox_px
        bbox_um = (
            round(x_px / pixel_per_um, 1),
            round(y_px / pixel_per_um, 1),
            round(w_px / pixel_per_um, 1),
            round(h_px / pixel_per_um, 1),
        )

        if ann.label == "dummy":
            device_hints.append(
                {
                    "bbox_um": list(bbox_um),
                    "label": "DUMMY_ignore",
                    "confidence": 1.0,
                }
            )
        else:
            device_hints.append(
                {
                    "bbox_um": list(bbox_um),
                    "label": f"auto_{ann.label}",
                    "confidence": 0.9,
                }
            )

    return {
        "chip": {
            "name": "annotated_chip",
            "process": "cmos",
            "die_size_um": [0, 0, round(img_w_um, 1), round(img_h_um, 1)],
        },
        "annotations": {
            "global_hints": global_hints,
            "regions": regions,
            "device_hints": device_hints,
            "power_nets": [],
        },
    }


# CLI entry point
def parse_command(
    image_path: str,
    output_path: str,
    pixel_per_um: float = 20.0,
) -> None:
    """CLI: parse annotations and write YAML config.

    Usage: silicon-eye annotate parse -i annotated.png -o config.yaml
    """
    _, config = parse_color_annotations(image_path, pixel_per_um)

    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Parsed annotations written to {output_path}")
    print(f"  Device hints: {len(config['annotations']['device_hints'])}")
