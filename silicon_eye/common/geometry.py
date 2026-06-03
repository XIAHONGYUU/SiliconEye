"""Geometry utilities: rectangle operations, connectivity, spatial queries."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .types import Um


@dataclass(slots=True)
class BBox:
    """Axis-aligned bounding box in micrometers (physical coordinates)."""

    x: Um
    y: Um
    w: Um
    h: Um

    @property
    def area(self) -> Um:
        return self.w * self.h

    @property
    def center(self) -> tuple[Um, Um]:
        return (self.x + self.w / 2, self.y + self.h / 2)

    @property
    def x2(self) -> Um:
        return self.x + self.w

    @property
    def y2(self) -> Um:
        return self.y + self.h

    def intersects(self, other: BBox) -> bool:
        return not (
            self.x2 <= other.x
            or other.x2 <= self.x
            or self.y2 <= other.y
            or other.y2 <= self.y
        )

    def intersection_area(self, other: BBox) -> Um:
        if not self.intersects(other):
            return 0.0
        x_overlap = min(self.x2, other.x2) - max(self.x, other.x)
        y_overlap = min(self.y2, other.y2) - max(self.y, other.y)
        return max(0.0, x_overlap * y_overlap)

    def iou(self, other: BBox) -> float:
        inter = self.intersection_area(other)
        if inter == 0:
            return 0.0
        return inter / (self.area + other.area - inter)

    def contains_point(self, x: Um, y: Um) -> bool:
        return self.x <= x <= self.x2 and self.y <= y <= self.y2

    def distance_to(self, other: BBox) -> Um:
        """Minimum Euclidean distance between two bounding boxes."""
        dx = max(0.0, max(self.x - other.x2, other.x - self.x2))
        dy = max(0.0, max(self.y - other.y2, other.y - self.y2))
        return math.sqrt(dx * dx + dy * dy)

    def expand(self, margin: Um) -> BBox:
        return BBox(
            self.x - margin,
            self.y - margin,
            self.w + 2 * margin,
            self.h + 2 * margin,
        )

    def to_tuple(self) -> tuple[Um, Um, Um, Um]:
        return (self.x, self.y, self.w, self.h)

    @classmethod
    def from_center(cls, cx: Um, cy: Um, w: Um, h: Um) -> BBox:
        return cls(cx - w / 2, cy - h / 2, w, h)


def bbox_union(a: BBox, b: BBox) -> BBox:
    """Smallest bounding box containing both a and b."""
    x = min(a.x, b.x)
    y = min(a.y, b.y)
    x2 = max(a.x2, b.x2)
    y2 = max(a.y2, b.y2)
    return BBox(x, y, x2 - x, y2 - y)
