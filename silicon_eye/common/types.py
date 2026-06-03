"""Common type aliases for silicon_eye."""

from typing import TypeAlias

# Physical coordinates in micrometers (μm)
Um: TypeAlias = float
Pt: TypeAlias = tuple[Um, Um]  # (x, y) point

# Pixel coordinates (image space)
Px: TypeAlias = int
PxPt: TypeAlias = tuple[Px, Px]

# Unique identifiers
DeviceId: TypeAlias = str
ConnectionId: TypeAlias = str
GroupId: TypeAlias = str
TileId: TypeAlias = str
