"""Grouper: identify matched device groups.

Detects current mirrors, differential pairs, common-centroid layouts, etc.
"""

from __future__ import annotations

import logging

from ..schemas.annotation import Annotations
from ..schemas.devices import DeviceList, DeviceType, ExtractedDevice
from ..schemas.netlist import MatchedGroup

logger = logging.getLogger(__name__)


class Grouper:
    """Groups matched devices by geometric and electrical similarity."""

    def __init__(
        self,
        w_tolerance_pct: float = 5.0,
        l_tolerance_pct: float = 5.0,
        spatial_proximity_um: float = 50.0,
    ):
        self.w_tol = w_tolerance_pct / 100.0
        self.l_tol = l_tolerance_pct / 100.0
        self.proximity = spatial_proximity_um

    def group(
        self,
        device_list: DeviceList,
        annotations: Annotations,
    ) -> list[MatchedGroup]:
        """Find matched device groups in the device list.

        Strategy:
        1. Group transistors by W/L similarity (within tolerance)
        2. Check spatial proximity
        3. Classify group type (current_mirror, diff_pair, etc.)
        """
        groups: list[MatchedGroup] = []
        transistors = [
            d
            for d in device_list.devices
            if d.type in (DeviceType.NMOS, DeviceType.PMOS)
        ]

        # Cluster by W/L similarity
        clustered = self._cluster_by_size(transistors)

        group_counter = 1
        for cluster in clustered:
            if len(cluster) < 2:
                continue

            group_type = self._classify_group_type(cluster)
            ratio = self._compute_ratio(cluster)
            groups.append(
                MatchedGroup(
                    group_id=f"GRP{group_counter}",
                    type=group_type,
                    device_ids=[d.id for d in cluster],
                    ratio=ratio,
                    confidence=self._confidence(cluster),
                )
            )
            group_counter += 1

        logger.info("Grouper found %d matched groups", len(groups))
        return groups

    def _cluster_by_size(
        self, devices: list[ExtractedDevice]
    ) -> list[list[ExtractedDevice]]:
        """Cluster devices with similar W and L values."""
        clusters: list[list[ExtractedDevice]] = []
        remaining = list(devices)

        while remaining:
            ref = remaining.pop(0)
            cluster = [ref]

            i = 0
            while i < len(remaining):
                d = remaining[i]
                if (
                    ref.w_um is not None
                    and d.w_um is not None
                    and ref.l_um is not None
                    and d.l_um is not None
                ):
                    w_match = (
                        abs(d.w_um - ref.w_um) / max(ref.w_um, 1e-6) <= self.w_tol
                    )
                    l_match = (
                        abs(d.l_um - ref.l_um) / max(ref.l_um, 1e-6) <= self.l_tol
                    )
                    if w_match and l_match:
                        cluster.append(remaining.pop(i))
                        continue
                i += 1

            clusters.append(cluster)

        return clusters

    def _classify_group_type(
        self, devices: list[ExtractedDevice]
    ) -> str:
        """Classify the group type based on device arrangement."""
        if len(devices) == 2:
            return "diff_pair"  # Simplest heuristic — TODO: improve
        return "current_mirror"

    def _compute_ratio(self, devices: list[ExtractedDevice]) -> str:
        """Compute the W/L ratio string for the group."""
        if not devices or devices[0].w_um is None:
            return "unknown"
        ref_w = devices[0].w_um
        widths = []
        for d in devices:
            if d.w_um is not None:
                widths.append(str(round(d.w_um / max(ref_w, 1e-6))))
        return ":".join(widths)

    def _confidence(self, devices: list[ExtractedDevice]) -> float:
        """Compute group confidence score."""
        # Higher when: same type, close W/L, nearby location
        same_type = len({d.type for d in devices}) == 1
        confidences = [d.confidence for d in devices]
        base = sum(confidences) / len(confidences) if confidences else 0.5
        if not same_type:
            base *= 0.5
        return round(base, 2)
