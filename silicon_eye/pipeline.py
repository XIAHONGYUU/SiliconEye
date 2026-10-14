"""Pipeline: orchestration engine for the reverse engineering workflow.

Runs local registration evidence with explicit candidate and blocked states.
Device extraction is unavailable; legacy phase2 helpers are not an accepted workflow.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from .config import ChipConfig
from .phase2_clean.dummy_filter import DummyFilter
from .phase2_clean.grouper import Grouper
from .phase2_clean.passive_merger import PassiveMerger
from .registration_audit import digest, write_json
from .schemas.annotation import Annotations
from .schemas.devices import DeviceList
from .schemas.layer_image import TileSet

logger = logging.getLogger(__name__)


class Pipeline:
    """Orchestrates the reverse engineering pipeline.

    Registration writes a local evidence pack and a stage manifest. Device and
    netlist stages remain blocked until their implementation and prerequisites
    are available; checkpoint resume/import is not implemented by this entry.
    """

    def __init__(self, config: ChipConfig, data_root: str = "data", output_dir: str | None = None):
        self.config = config
        self.data_root = Path(data_root).resolve()

        # Ensure config has necessary defaults
        if not hasattr(config, "annotations") or config.annotations is None:
            config.annotations = Annotations()

        # Create run directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.run_dir = Path(output_dir or f"runs/{config.chip.name}_{timestamp}").resolve()
        if self.run_dir.is_relative_to(self.data_root):
            raise ValueError("run output cannot be inside the source data root")
        self.run_dir.mkdir(parents=True, exist_ok=False)

        logger.info("Pipeline initialized for chip '%s'", config.chip.name)
        logger.info("Run directory: %s", self.run_dir)

    def run(self, stages: list[str] | None = None, registration_spec: str | None = None) -> dict:
        """Run explicit stages; candidate geometry cannot authorize extraction."""
        stages = ["phase1", "phase2"] if stages is None else stages
        if (
            not stages
            or len(stages) != len(set(stages))
            or any(stage not in {"registration", "phase1", "phase2"} for stage in stages)
        ):
            raise ValueError("stages must be unique supported stage names")
        if "registration" in stages and not registration_spec:
            raise ValueError("registration stage requires a local registration spec")
        results = {}
        state = {
            "status": "running",
            "data_root": str(self.data_root),
            "requested_stages": stages,
            "stages": results,
            "code_sha256": {
                "pipeline.py": digest(Path(__file__)),
                "cli.py": digest(Path(__file__).with_name("cli.py")),
            },
        }
        state_path = self.run_dir / "pipeline_manifest.json"
        write_json(state_path, state)
        # Dependency order is fixed regardless of the argument order.
        for stage in ("registration", "phase1", "phase2"):
            if stage not in stages:
                continue
            try:
                if stage == "registration":
                    results[stage] = self._run_registration(registration_spec)
                elif stage == "phase1":
                    if (
                        "registration" in results
                        and results["registration"].get("acceptance") != "confirmed"
                    ):
                        results[stage] = {
                            "status": "blocked",
                            "reason": "registration_not_confirmed",
                        }
                    else:
                        results[stage] = self._run_phase1()
                else:
                    if results.get("phase1", {}).get("status") != "complete":
                        results[stage] = {
                            "status": "blocked",
                            "reason": "verified_device_checkpoint_unavailable",
                        }
                    else:
                        results[stage] = self._run_phase2(self._load_phase1_result())
            except NotImplementedError as error:
                results[stage] = {"status": "blocked", "reason": str(error)}
            except (ValueError, OSError, KeyError) as error:
                results[stage] = {"status": "failed", "reason": str(error)}
            write_json(state_path, state)
        statuses = {result["status"] for result in results.values()}
        state["status"] = next(
            (s for s in ("failed", "blocked", "candidate") if s in statuses), "complete"
        )
        write_json(state_path, state)
        return results

    def _run_registration(self, spec_path: str) -> dict:
        from .registration_local import run_local

        if len(self.config.tiles) != 1:
            raise ValueError("local registration requires exactly one configured tile")
        source = Path(spec_path).resolve()
        spec = json.loads(source.read_text())
        names = {Path(spec[side]["path"]).stem for side in ("reference", "target")}
        tile_set = self._build_tile_set(selected_layers=names)
        paths = {image.layer_name: image.path for image in tile_set.tiles[0].images}
        for side in ("reference", "target"):
            spec[side]["path"] = paths[Path(spec[side]["path"]).stem]
        local_input = self.run_dir / "local_registration_input.json"
        write_json(local_input, spec)
        evidence = self.run_dir / "registration"
        result = run_local(str(local_input), str(evidence))
        return {
            "status": "candidate",
            "acceptance": result["acceptance"],
            "numeric_budget_met": result["numeric_budget_met"],
            "reason": result["reason"],
            "evidence": str(evidence),
            "source_spec_sha256": digest(source),
            "loaded_layers": sorted(names),
            "validation_metrics": result["validation_metrics"],
        }

    def _run_phase1(self) -> dict:
        """Do not turn an unimplemented segmenter into an empty success checkpoint."""
        raise NotImplementedError("device_segmentation_and_verified_extraction_unavailable")

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
            "status": "complete",
            "checkpoint": str(checkpoint_path),
            "spice": str(spice_path),
            "active_devices": len(active_devices),
            "dummies_removed": len(dummies),
            "matched_groups": len(matched_groups),
            "merged_passives": len(merged),
        }

    def _build_tile_set(self, selected_layers: set[str] | None = None) -> TileSet:
        """Build TileSet from config."""
        if selected_layers is not None and not selected_layers.issubset(
            {layer.name for layer in self.config.layers}
        ):
            raise ValueError("local case contains unconfigured layer names")
        tiles = []
        for tile_config in self.config.tiles or []:
            from .schemas.layer_image import LayerImage, Tile

            images = []
            for layer in self.config.layers:
                if selected_layers is not None and layer.name not in selected_layers:
                    continue
                directory = self.data_root / self.config.chip.name / tile_config.id
                candidates = [
                    directory / f"{layer.name}{ext}"
                    for ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff")
                ]
                existing = [path for path in candidates if path.is_file()]
                if not existing:
                    raise FileNotFoundError(f"Missing source image for {layer.name}: {directory}")
                if len(existing) > 1:
                    raise ValueError(f"Ambiguous source images for {layer.name}: {directory}")
                img_path = str(existing[0].resolve())
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
