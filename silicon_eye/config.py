"""Config system: typed configuration with YAML loading and inheritance.

Supports:
  - YAML-based chip configs
  - Inheritance via `extends` key (e.g., extends: defaults/cmos.yaml)
  - Typed Python dataclasses with validation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from .schemas.annotation import Annotations


# ── Phase 1 config ──────────────────────────────────────────


@dataclass
class SegmenterConfig:
    mode: Literal["sam3", "rule_based", "none"] = "rule_based"
    confidence_threshold: float = 0.7
    prompt_mode: str = "text"


@dataclass
class ExtractorConfig:
    min_device_area_um2: float = 5.0


@dataclass
class Phase1Config:
    stitcher: dict = field(default_factory=lambda: {"enabled": False})
    segmenter: SegmenterConfig = field(default_factory=SegmenterConfig)
    extractor: ExtractorConfig = field(default_factory=ExtractorConfig)


# ── Phase 2 config ──────────────────────────────────────────


@dataclass
class GrouperConfig:
    w_tolerance_pct: float = 5.0
    l_tolerance_pct: float = 5.0
    spatial_proximity_um: float = 50.0


@dataclass
class DummyFilterConfig:
    auto_detect: bool = True


@dataclass
class Phase2Config:
    grouper: GrouperConfig = field(default_factory=GrouperConfig)
    dummy_filter: DummyFilterConfig = field(default_factory=DummyFilterConfig)


# ── Chip / Tile / Layer config ──────────────────────────────


@dataclass
class LayerDef:
    name: str
    index: int
    description: str = ""
    is_metal: bool = False
    is_via: bool = False


@dataclass
class TileConfig:
    id: str
    bbox_um: tuple[float, float, float, float] = (0, 0, 0, 0)
    overlap_um: float = 10.0
    pixel_per_um: float = 20.0


@dataclass
class ChipDef:
    name: str = "unknown"
    process: str = "cmos"
    die_size_um: list[float] = field(default_factory=lambda: [0, 0, 0, 0])


# ── Top-level config ────────────────────────────────────────


@dataclass
class ChipConfig:
    chip: ChipDef = field(default_factory=ChipDef)
    layers: list[LayerDef] = field(default_factory=list)
    tiles: list[TileConfig] = field(default_factory=list)
    phase1: Phase1Config = field(default_factory=Phase1Config)
    phase2: Phase2Config = field(default_factory=Phase2Config)
    annotations: Annotations = field(default_factory=Annotations)
    extends: str | None = None


# ── Loader ──────────────────────────────────────────────────


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: str | Path) -> ChipConfig:
    """Load a chip config YAML file, resolving inheritance.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Typed ChipConfig instance.
    """
    config_path = Path(config_path)
    raw = yaml.safe_load(config_path.read_text())

    # Resolve inheritance
    if "extends" in raw:
        base_path = config_path.parent / raw["extends"]
        if base_path.exists():
            base_raw = yaml.safe_load(base_path.read_text())
            raw = _deep_merge(base_raw, raw)
            del raw["extends"]

    # Build ChipConfig from raw dict
    return _dict_to_config(raw)


def _dict_to_config(raw: dict) -> ChipConfig:
    """Convert raw dict to typed ChipConfig."""
    chip = ChipDef(**raw.get("chip", {}))

    layers = [LayerDef(**l) for l in raw.get("layers", [])]

    tiles = []
    for t in raw.get("tiles", []):
        tiles.append(
            TileConfig(
                id=t["id"],
                bbox_um=tuple(t.get("bbox_um", (0, 0, 0, 0))),
                overlap_um=t.get("overlap_um", 10.0),
                pixel_per_um=t.get("pixel_per_um", 20.0),
            )
        )

    # Phase 1
    p1_raw = raw.get("phase1", {})
    seg_raw = p1_raw.get("segmenter", {})
    ext_raw = p1_raw.get("extractor", {})
    phase1 = Phase1Config(
        stitcher=p1_raw.get("stitcher", {"enabled": False}),
        segmenter=SegmenterConfig(
            mode=seg_raw.get("mode", "rule_based"),
            confidence_threshold=seg_raw.get("confidence_threshold", 0.7),
        ),
        extractor=ExtractorConfig(
            min_device_area_um2=ext_raw.get("min_device_area_um2", 5.0),
        ),
    )

    # Phase 2
    p2_raw = raw.get("phase2", {})
    g_raw = p2_raw.get("grouper", {})
    d_raw = p2_raw.get("dummy_filter", {})
    phase2 = Phase2Config(
        grouper=GrouperConfig(
            w_tolerance_pct=g_raw.get("w_tolerance_pct", 5.0),
            l_tolerance_pct=g_raw.get("l_tolerance_pct", 5.0),
            spatial_proximity_um=g_raw.get("spatial_proximity_um", 50.0),
        ),
        dummy_filter=DummyFilterConfig(
            auto_detect=d_raw.get("auto_detect", True),
        ),
    )

    # Annotations
    ann_raw = raw.get("annotations", {})
    annotations = Annotations(**ann_raw) if ann_raw else Annotations()

    return ChipConfig(
        chip=chip,
        layers=layers,
        tiles=tiles,
        phase1=phase1,
        phase2=phase2,
        annotations=annotations,
    )
