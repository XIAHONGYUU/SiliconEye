"""Schema: DeviceList — Phase 1 output (extracted devices from images)."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class DeviceType(StrEnum):
    NMOS = "nmos"
    PMOS = "pmos"
    RESISTOR = "resistor"
    MIM_CAP = "mim_cap"
    MOM_CAP = "mom_cap"
    UNKNOWN = "unknown"


class Terminal(BaseModel):
    """A device terminal with its physical location."""

    name: str = Field(description="Terminal name: gate, source, drain, plus, minus")
    layer: str = Field(description="Layer the terminal is on")
    x_um: float
    y_um: float


class ExtractedDevice(BaseModel):
    """A single device extracted from die images."""

    id: str = Field(description="Unique device ID, e.g. 'Q1', 'M5', 'R12'")
    type: DeviceType
    bbox_um: tuple[float, float, float, float] = Field(
        description="Bounding box in μm: (x, y, w, h)"
    )
    area_um2: float
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    # Geometry parameters (populated for transistors)
    w_um: float | None = Field(default=None, description="Gate width (μm)")
    l_um: float | None = Field(default=None, description="Gate length (μm)")
    fingers: int | None = Field(default=None, description="Number of gate fingers")

    # Value parameters (populated for passives)
    value: float | None = Field(default=None, description="Resistance (Ω) or capacitance (fF)")
    value_unit: str | None = Field(default=None)

    terminals: list[Terminal] = Field(default_factory=list)
    annotation_hints: list[str] = Field(
        default_factory=list,
        description="Hints from human annotations applied to this device",
    )


class Connection(BaseModel):
    """A wire or net connecting two terminals."""

    id: str
    from_ref: tuple[str, str] = Field(description="(device_id, terminal_name)")
    to_ref: tuple[str, str]
    layers: list[str] = Field(default_factory=list)
    length_um: float | None = None


class DeviceList(BaseModel):
    """Phase 1 output: all extracted devices and connections."""

    metadata: dict = Field(default_factory=dict)
    devices: list[ExtractedDevice]
    connections: list[Connection] = Field(default_factory=list)
