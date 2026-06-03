"""Dummy Filter: identify and mark non-functional / dummy devices."""

from __future__ import annotations

import logging

from ..schemas.annotation import Annotations
from ..schemas.devices import DeviceList, ExtractedDevice
from ..schemas.netlist import DummyDevice

logger = logging.getLogger(__name__)


class DummyFilter:
    """Identifies dummy devices that should be excluded from the functional netlist.

    Heuristics:
      - All terminals shorted together (gate = source = drain)
      - Minimum-size transistor with no external connections
      - Explicitly marked as DUMMY in manual annotations
      - Repeating pattern at edge of active area (guard ring fillers)
      - Floating gate with source/drain tied to supply
    """

    def __init__(self, auto_detect: bool = True):
        self.auto_detect = auto_detect

    def filter(
        self,
        device_list: DeviceList,
        annotations: Annotations,
    ) -> list[DummyDevice]:
        """Identify dummy devices in the device list.

        Returns list of DummyDevice, does NOT modify the original DeviceList.
        """
        dummies: list[DummyDevice] = []

        for device in device_list.devices:
            # Check manual annotations first (highest priority)
            if self._is_manually_marked(device, annotations):
                dummies.append(
                    DummyDevice(id=device.id, reason="manual_annotation")
                )
                continue

            if not self.auto_detect:
                continue

            # Auto-detection heuristics
            if self._all_terminals_shorted(device):
                dummies.append(
                    DummyDevice(id=device.id, reason="all_terminals_shorted")
                )
            elif self._min_size_no_connection(device, device_list):
                dummies.append(
                    DummyDevice(id=device.id, reason="min_size_no_connection")
                )

        logger.info("Dummy filter identified %d dummy devices", len(dummies))
        return dummies

    def _is_manually_marked(
        self, device: ExtractedDevice, annotations: Annotations
    ) -> bool:
        """Check if device was explicitly marked as DUMMY in annotations."""
        for hint in device.annotation_hints:
            if "DUMMY" in hint.upper():
                return True
        return False

    def _all_terminals_shorted(self, device: ExtractedDevice) -> bool:
        """Check if all terminals are shorted together (gate = source = drain)."""
        if len(device.terminals) < 2:
            return False
        # TODO: check terminal connectivity
        return False

    def _min_size_no_connection(
        self, device: ExtractedDevice, device_list: DeviceList
    ) -> bool:
        """Check if device is minimum size and has no external connections."""
        # TODO: detect minimum-size devices in the process
        # TODO: check if no other device connects to its terminals
        return False
