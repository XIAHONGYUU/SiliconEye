"""Schema: human annotations injected into the pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RegionAnnotation(BaseModel):
    """A labeled rectangular region on the die (ROI)."""

    bbox_um: tuple[float, float, float, float]
    label: str = Field(description="e.g., 'differential_pair_input_stage'")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class DeviceHint(BaseModel):
    """Explicit hint about a specific device."""

    bbox_um: tuple[float, float, float, float]
    label: str = Field(
        description="e.g., 'Q1_NMOS_input', 'DUMMY_ignore', 'R_feedback'"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class PowerNet(BaseModel):
    """A labeled power/ground net trace."""

    layer: str
    path: list[tuple[float, float]] = Field(description="Polyline in μm coordinates")
    label: str = Field(description="e.g., 'VDD', 'VSS', 'VCC_1V8'")


class GlobalHint(BaseModel):
    """Free-text hint injected into segmenter prompts."""

    text: str = Field(description="Natural language hint, e.g. 'CMOS 180nm process'")


class Annotations(BaseModel):
    """All human annotations for a chip."""

    global_hints: list[GlobalHint] = Field(default_factory=list)
    regions: list[RegionAnnotation] = Field(default_factory=list)
    device_hints: list[DeviceHint] = Field(default_factory=list)
    power_nets: list[PowerNet] = Field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not any(
            [self.global_hints, self.regions, self.device_hints, self.power_nets]
        )
