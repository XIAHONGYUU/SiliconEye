"""Passive Merger: merge same-value resistors and capacitors.

When multiple identical resistors or capacitors appear in the device list
(e.g., poly resistors in series, parallel MIM caps), merge them into
single devices with combined values.
"""

from __future__ import annotations

import logging

from ..schemas.annotation import Annotations
from ..schemas.devices import DeviceList, DeviceType, ExtractedDevice
from ..schemas.netlist import MergedPassive

logger = logging.getLogger(__name__)


class PassiveMerger:
    """Merges identical passive components (R, C) for cleaner netlists."""

    def __init__(self, value_tolerance_pct: float = 5.0):
        self.value_tol = value_tolerance_pct / 100.0

    def merge(
        self,
        device_list: DeviceList,
        annotations: Annotations,
    ) -> list[MergedPassive]:
        """Merge identical passives in the device list.

        Does NOT modify the original DeviceList.
        """
        merged: list[MergedPassive] = []

        # Group passives by type
        resistors = [
            d for d in device_list.devices if d.type == DeviceType.RESISTOR
        ]
        capacitors = [
            d
            for d in device_list.devices
            if d.type in (DeviceType.MIM_CAP, DeviceType.MOM_CAP)
        ]

        merged.extend(self._merge_passives(resistors, "resistor"))
        merged.extend(self._merge_passives(capacitors, "capacitor"))

        logger.info("Passive merger created %d merged groups", len(merged))
        return merged

    def _merge_passives(
        self, devices: list[ExtractedDevice], passive_type: str
    ) -> list[MergedPassive]:
        """Merge devices of the same passive type by value similarity."""
        groups: list[list[ExtractedDevice]] = []
        remaining = list(devices)

        while remaining:
            ref = remaining.pop(0)
            if ref.value is None:
                continue
            group = [ref]

            i = 0
            while i < len(remaining):
                d = remaining[i]
                if d.value is not None:
                    if (
                        abs(d.value - ref.value) / max(ref.value, 1e-6)
                        <= self.value_tol
                    ):
                        group.append(remaining.pop(i))
                        continue
                i += 1

            if len(group) > 1:
                groups.append(group)

        merged: list[MergedPassive] = []
        for group in groups:
            avg_value = sum(d.value for d in group if d.value is not None) / len(
                group
            )
            unit = group[0].value_unit or ("ohm" if passive_type == "resistor" else "fF")
            merged.append(
                MergedPassive(
                    original_ids=[d.id for d in group],
                    merged_value=round(avg_value, 3),
                    merged_unit=unit,
                    type=passive_type,
                )
            )

        return merged
