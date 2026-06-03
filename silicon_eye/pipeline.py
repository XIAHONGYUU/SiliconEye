"""Pipeline: orchestration engine for the reverse engineering workflow.

Runs Phase 1 → Phase 2 in sequence, with checkpoint support.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from .config import ChipConfig, load_config
from .phase1_image.extractor import Extractor
from .phase1_image.layer_matcher import LayerMatcher
from .phase1_image.segmenter import Segmenter
from .phase1_image.stitcher import Stitcher
from .phase2_clean.dummy_filter import DummyFilter
from .phase2_clean.grouper import Grouper
from .phase2_clean.passive_merger import PassiveMerger
from .schemas.annotation import Annotations
from .schemas.devices import DeviceList
from .schemas.layer_image import TileSet

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the reverse engineering pipeline.

    Each phase writes its output to a checkpoint directory so that:
    - Interrupted runs can resume from the last checkpoint.
    - Phase 2 can be run independently given a hand-curated DeviceList.
    """

    def __init__(self, config: ChipConfig):
        self.config = config

        # Ensure config has necessary defaults
        if not hasattr(config, "annotations") or config.annotations is None:
            config.annotations = Annotations()

        # Create run directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = Path(f"runs/{config.chip.name}_{timestamp}")
        self.run_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Pipeline initialized for chip '%s'", config.chip.name)
        logger.info("Run directory: %s", self.run_dir)

    def run(self, stages: list[str] | None = None) -> dict:
        """Execute the pipeline.

        Args:
            stages: Which stages to run. Default: ["phase1", "phase2"].

        Returns:
            Dict with paths to output files.
        """
        if stages is None:
            stages = ["phase1", "phase2"]

        results: dict = {}

        if "phase1" in stages:
            results["phase1"] = self._run_phase1()

        if "phase2" in stages:
            # Load phase1 output (from checkpoint or provided externally)
            device_list = self._load_phase1_result()
            results["phase2"] = self._run_phase2(device_list)

        return results

    def _run_phase1(self) -> dict:
        """Run Phase 1: Image → Devices."""
        logger.info("=== Phase 1: Image → Devices ===")

        # 1. Build TileSet from config
        tile_set = self._build_tile_set()

        # 2. Stitch (if multi-tile)
        stitcher = Stitcher()
        stitched = stitcher.stitch(
            tile_set, self.run_dir / "stitched"
        )

        # 3. Segment
        segmenter = Segmenter(
            mode=self.config.phase1.segmenter.mode,
            confidence_threshold=self.config.phase1.segmenter.confidence_threshold,
        )
        regions = segmenter.segment(
            stitched,
            self.config.annotations,
            tile_set.tiles[0].pixel_per_um if tile_set.tiles else 20.0,
        )

        # 4. Extract device parameters
        extractor = Extractor(
            pixel_per_um=tile_set.tiles[0].pixel_per_um if tile_set.tiles else 20.0,
            min_device_area_um2=self.config.phase1.extractor.min_device_area_um2,
        )
        device_list = extractor.extract(regions, stitched, self.config.annotations)

        # 5. Write checkpoint
        checkpoint_path = self.run_dir / "phase1_devices.json"
        checkpoint_path.write_text(device_list.model_dump_json(indent=2))
        logger.info("Phase 1 checkpoint: %s", checkpoint_path)

        return {
            "checkpoint": str(checkpoint_path),
            "device_count": len(device_list.devices),
            "connection_count": len(device_list.connections),
        }

    def _run_phase2(self, device_list: DeviceList) -> dict:
        """Run Phase 2: Devices → Clean Netlist."""
        logger.info("=== Phase 2: Devices → Clean Netlist ===")

        # 1. Group matched devices
        grouper = Grouper(
            w_tolerance_pct=self.config.phase2.grouper.w_tolerance_pct,
            l_tolerance_pct=self.config.phase2.grouper.l_tolerance_pct,
            spatial_proximity_um=self.config.phase2.grouper.spatial_proximity_um,
        )
        matched_groups = grouper.group(device_list, self.config.annotations)

        # 2. Filter dummy devices
        dummy_filter = DummyFilter(
            auto_detect=self.config.phase2.dummy_filter.auto_detect,
        )
        dummies = dummy_filter.filter(device_list, self.config.annotations)

        # 3. Merge passives
        merger = PassiveMerger(value_tolerance_pct=5.0)
        merged = merger.merge(device_list, self.config.annotations)

        # 4. Build CleanNetlist
        from .schemas.netlist import CleanNetlist

        # Remove dummy devices for spice generation
        dummy_ids = {d.id for d in dummies}
        active_devices = [d for d in device_list.devices if d.id not in dummy_ids]

        clean_netlist = CleanNetlist(
            metadata={
                "chip": self.config.chip.name,
                "phase1_device_count": len(device_list.devices),
                "active_device_count": len(active_devices),
                "dummy_count": len(dummies),
                "matched_groups": len(matched_groups),
                "merged_passives": len(merged),
            },
            matched_groups=matched_groups,
            dummy_devices=dummies,
            merged_passives=merged,
            spice_netlist=self._generate_spice(active_devices, matched_groups),
        )

        # 5. Write checkpoint
        checkpoint_path = self.run_dir / "phase2_netlist.json"
        checkpoint_path.write_text(clean_netlist.model_dump_json(indent=2))

        # Also write SPICE file
        spice_path = self.run_dir / "netlist.spice"
        spice_path.write_text(clean_netlist.spice_netlist)

        logger.info("Phase 2 checkpoint: %s", checkpoint_path)
        logger.info("SPICE netlist: %s", spice_path)

        return {
            "checkpoint": str(checkpoint_path),
            "spice": str(spice_path),
            "active_devices": len(active_devices),
            "dummies_removed": len(dummies),
            "matched_groups": len(matched_groups),
            "merged_passives": len(merged),
        }

    def _build_tile_set(self) -> TileSet:
        """Build TileSet from config."""
        tiles = []
        for tile_config in self.config.tiles or []:
            from .schemas.layer_image import LayerImage, Tile

            images = []
            for layer in self.config.layers:
                # Try common image extensions
                img_path = None
                for ext in [".png", ".jpg", ".jpeg", ".tif", ".tiff"]:
                    candidate = f"{self.config.chip.name}/{tile_config.id}/{layer.name}{ext}"
                    if (Path(self.config.chip.name) / tile_config.id / f"{layer.name}{ext}").exists():
                        img_path = candidate
                        break
                if img_path is None:
                    # Fallback: use .png path (will error if missing)
                    img_path = f"{self.config.chip.name}/{tile_config.id}/{layer.name}.png"
                images.append(
                    LayerImage(
                        path=img_path,
                        layer_name=layer.name,
                        layer_z=layer.index,
                    )
                )

            tiles.append(
                Tile(
                    id=tile_config.id,
                    bbox_um=tile_config.bbox_um,
                    overlap_um=tile_config.overlap_um,
                    images=images,
                    pixel_per_um=tile_config.pixel_per_um,
                )
            )

        return TileSet(tiles=tiles, chip_name=self.config.chip.name)

    def _load_phase1_result(self) -> DeviceList:
        """Load Phase 1 output from checkpoint."""
        checkpoint_path = self.run_dir / "phase1_devices.json"
        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"Phase 1 checkpoint not found: {checkpoint_path}. "
                "Run phase1 first or provide an external device list."
            )
        data = json.loads(checkpoint_path.read_text())
        return DeviceList(**data)

    def _generate_spice(
        self,
        devices: list,
        matched_groups: list,
    ) -> str:
        """Generate a SPICE netlist from the clean device list."""
        lines = [
            f"* SPICE netlist for {self.config.chip.name}",
            f"* Generated by Silicon Eye v0.1.0",
            f"* Date: {datetime.now().isoformat()}",
            f"* Active devices: {len(devices)}",
            "",
        ]

        for device in devices:
            from .schemas.devices import DeviceType

            if device.type == DeviceType.NMOS:
                lines.append(
                    f"{device.id} D G S B NMOS W={device.w_um or '?'}u L={device.l_um or '?'}u"
                )
            elif device.type == DeviceType.PMOS:
                lines.append(
                    f"{device.id} D G S B PMOS W={device.w_um or '?'}u L={device.l_um or '?'}u"
                )
            elif device.type == DeviceType.RESISTOR:
                val = device.value or "?"
                lines.append(f"{device.id} A B {val}")
            elif device.type in (DeviceType.MIM_CAP, DeviceType.MOM_CAP):
                val = device.value or "?"
                lines.append(f"{device.id} A B {val}")

        lines.append("\n* Matched groups:")
        for group in matched_groups:
            ids = " ".join(group.device_ids)
            lines.append(f"* {group.group_id} ({group.type}): {ids}")

        lines.append("\n.END")
        return "\n".join(lines)
