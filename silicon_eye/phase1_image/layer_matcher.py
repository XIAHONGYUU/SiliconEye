"""Layer Matcher: cross-layer association.

Connects features across layers:
  - poly ∩ p_diffusion → NMOS gate
  - poly ∩ n_diffusion → PMOS gate
  - metal1 → via → metal2 → wire tracing
"""

from __future__ import annotations

import logging

from ..common.geometry import BBox
from ..schemas.devices import Connection

logger = logging.getLogger(__name__)


class LayerMatcher:
    """Matches features across imaging layers to identify devices and connections."""

    def __init__(self, alignment_tolerance_um: float = 0.5):
        self.tolerance = alignment_tolerance_um

    def find_transistor_regions(
        self,
        poly_regions: list[BBox],
        p_diff_regions: list[BBox],
        n_diff_regions: list[BBox],
        n_well_regions: list[BBox] | None = None,
    ) -> tuple[list[dict], list[dict]]:
        """Find NMOS and PMOS transistor regions via layer intersection.

        NMOS: poly ∩ p_diffusion (and NOT in n-well)
        PMOS: poly ∩ n_diffusion (and in n-well, if n-well layer available)

        Returns:
            (nmos_results, pmos_results) — each a list of {bbox, poly_bbox, diff_bbox}
        """
        nmos: list[dict] = []
        pmos: list[dict] = []

        for poly in poly_regions:
            for diff in p_diff_regions:
                if poly.intersects(diff):
                    if n_well_regions is None or not any(
                        poly.intersects(nw) for nw in n_well_regions
                    ):
                        nmos.append(
                            {
                                "bbox": BBox(
                                    max(poly.x, diff.x),
                                    max(poly.y, diff.y),
                                    min(poly.x2, diff.x2) - max(poly.x, diff.x),
                                    min(poly.y2, diff.y2) - max(poly.y, diff.y),
                                ),
                                "poly_bbox": poly,
                                "diff_bbox": diff,
                            }
                        )

            for diff in n_diff_regions:
                if poly.intersects(diff):
                    pmos.append(
                        {
                            "bbox": BBox(
                                max(poly.x, diff.x),
                                max(poly.y, diff.y),
                                min(poly.x2, diff.x2) - max(poly.x, diff.x),
                                min(poly.y2, diff.y2) - max(poly.y, diff.y),
                            ),
                            "poly_bbox": poly,
                            "diff_bbox": diff,
                        }
                    )

        logger.info(
            "Layer matcher found %d NMOS, %d PMOS transistor regions",
            len(nmos),
            len(pmos),
        )
        return nmos, pmos

    def trace_wires(
        self,
        metal_layers: dict[str, list[BBox]],
        via_layers: dict[str, list[BBox]],
    ) -> list[Connection]:
        """Trace interconnections through metal and via layers.

        Args:
            metal_layers: {layer_name: [metal_bboxes]}
            via_layers: {layer_name: [via_bboxes]}

        Returns:
            List of Connection objects.
        """
        connections: list[Connection] = []
        # TODO: implement wire tracing through metal/via stack
        logger.warning("Wire tracing not yet implemented")
        return connections
