"""Schema: CleanNetlist — Phase 2 output."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MatchedGroup(BaseModel):
    """A group of matched devices (current mirror, diff pair, etc.)."""

    group_id: str
    type: str = Field(description="e.g., 'current_mirror', 'diff_pair', 'common_centroid'")
    device_ids: list[str]
    ratio: str | None = Field(default=None, description="e.g., '1:4', '2:1'")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class DummyDevice(BaseModel):
    """A device identified as dummy / non-functional."""

    id: str
    reason: str = Field(
        description="Why classified as dummy: 'all_terminals_shorted', "
        "'min_size_no_connection', 'manual_annotation'"
    )


class MergedPassive(BaseModel):
    """Merged resistors or capacitors of same value/type."""

    original_ids: list[str]
    merged_value: float
    merged_unit: str
    type: str = Field(default="unknown", description="resistor | capacitor")


class CleanNetlist(BaseModel):
    """Phase 2 output: cleaned and structured netlist."""

    metadata: dict = Field(default_factory=dict)
    matched_groups: list[MatchedGroup] = Field(default_factory=list)
    dummy_devices: list[DummyDevice] = Field(default_factory=list)
    merged_passives: list[MergedPassive] = Field(default_factory=list)
    spice_netlist: str = Field(default="", description="SPICE netlist string")
