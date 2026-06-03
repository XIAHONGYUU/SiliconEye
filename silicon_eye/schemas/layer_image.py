"""Schema: layer image description (input to Phase 1)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LayerImage(BaseModel):
    """A single layer image for a tile."""

    path: str = Field(description="Path to the image file (relative to config dir)")
    layer_name: str = Field(
        description="Layer name: poly, p_diffusion, n_diffusion, n_well, contact, "
        "metal1, metal2, via1, mim_top, mim_bottom, ..."
    )
    layer_z: int = Field(
        default=0,
        description="Stack order for alignment (lower = deeper in chip)",
    )


class Tile(BaseModel):
    """A rectangular region of the die, with one image per layer."""

    id: str = Field(description="Unique tile identifier, e.g. 'tile_001'")
    bbox_um: tuple[float, float, float, float] = Field(
        description="(x, y, width, height) in micrometers"
    )
    overlap_um: float = Field(
        default=10.0,
        description="Overlap with adjacent tiles for stitching",
    )
    images: list[LayerImage] = Field(
        default_factory=list,
        description="One image per layer, named by layer_name",
    )
    pixel_per_um: float = Field(
        description="Image resolution: pixels per micrometer (e.g., 20.0 for 50nm/px)"
    )

    @property
    def image_bbox_px(self) -> tuple[int, int, int, int]:
        """Bounding box in pixels (x, y, w, h)."""
        ppm = self.pixel_per_um
        x, y, w, h = self.bbox_um
        return (int(x * ppm), int(y * ppm), int(w * ppm), int(h * ppm))


class TileSet(BaseModel):
    """Collection of tiles covering a die — may be a single tile for large images."""

    tiles: list[Tile] = Field(min_length=1)
    chip_name: str = Field(default="unknown")


class LayerDef(BaseModel):
    """Layer definition in the chip config."""

    name: str
    index: int = Field(description="Stack order (0 = deepest)")
    description: str = ""
    is_metal: bool = False
    is_via: bool = False
