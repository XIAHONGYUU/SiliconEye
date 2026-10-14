"""Source-pixel ROI drafts; deliberately separate from micron/device schemas."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

Status = Literal["candidate", "confirmed", "conflict", "unknown"]


class StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HumanReview(StrictRecord):
    reviewer: str = Field(min_length=1)
    actor: Literal["human"]
    decision: Literal["confirm"]
    evidence: str = Field(min_length=1)


class PixelSource(StrictRecord):
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_wh: tuple[int, int]
    registration_side: Literal["reference", "target"]
    scope_xywh: tuple[int, int, int, int]
    layer_label: str
    layer_status: Status
    layer_review: HumanReview | None = None

    @model_validator(mode="after")
    def check_source(self):
        width, height = self.size_wh
        x, y, w, h = self.scope_xywh
        if min(width, height, w, h) <= 0 or min(x, y) < 0 or x + w > width or y + h > height:
            raise ValueError("invalid source size/scope")
        if self.layer_status == "confirmed" and self.layer_review is None:
            raise ValueError("confirmed layer requires human review")
        return self


class PixelObject(StrictRecord):
    id: str = Field(pattern=r"^[A-Za-z0-9-]+$")
    source_id: str
    bbox_xywh: tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat]
    role: Literal["registration_control", "region_candidate"]
    usage: Literal["fitting", "diagnostic", "annotation_draft", "holdout"]
    label: str = Field(min_length=1)
    boundary_definition: Literal["visual_roi_not_material_mask"]
    producer: Literal["vision_model", "reasoning_model", "human"]
    status: Status
    review: HumanReview | None = None
    uncertainty: str = Field(min_length=1)
    device_type: Literal["unknown"] = "unknown"
    terminals: list[str] = Field(default_factory=list, max_length=0)

    @model_validator(mode="after")
    def check_role(self):
        if self.status == "confirmed" and self.review is None:
            raise ValueError("confirmed geometry requires human review")
        if self.role == "registration_control" and self.usage not in {"fitting", "diagnostic"}:
            raise ValueError("registration controls cannot become independent holdouts")
        return self


class PixelCorrespondence(StrictRecord):
    id: str = Field(pattern=r"^[A-Za-z0-9-]+$")
    object_ids: tuple[str, str]
    status: Status
    producer: Literal["vision_model", "reasoning_model", "human"]
    review: HumanReview | None = None
    uncertainty: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_confirmation(self):
        if self.status == "confirmed" and self.review is None:
            raise ValueError("confirmed cross-layer identity requires human review")
        return self


class PixelAnnotationSet(StrictRecord):
    schema_version: Literal[1]
    case_id: str
    coordinate_frame: Literal["native_source_pixel_xy_half_open"]
    physical_scale_status: Literal["unknown"]
    physical_scale_px_per_um: None = None
    registration_manifest: str
    registration_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    previous_input_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    correspondences: list[PixelCorrespondence] = Field(default_factory=list)
    sources: dict[str, PixelSource]
    objects: list[PixelObject] = Field(min_length=1)

    @model_validator(mode="after")
    def check_objects(self):
        if any(not re.fullmatch(r"[A-Za-z0-9-]+", name) for name in self.sources):
            raise ValueError("source IDs must be safe filename tokens")
        sides = [source.registration_side for source in self.sources.values()]
        if len(sides) != len(set(sides)):
            raise ValueError("duplicate registration source side")
        used = set()
        for obj in self.objects:
            if obj.id in used or obj.source_id not in self.sources:
                raise ValueError("duplicate object ID or unknown source")
            used.add(obj.id)
            x, y, w, h = obj.bbox_xywh
            sx, sy, sw, sh = self.sources[obj.source_id].scope_xywh
            if min(w, h) <= 0 or x < sx or y < sy or x + w > sx + sw or y + h > sy + sh:
                raise ValueError("object outside declared local source scope")
        objects = {obj.id: obj for obj in self.objects}
        pair_ids = set()
        for pair in self.correspondences:
            if pair.id in pair_ids or any(name not in objects for name in pair.object_ids):
                raise ValueError("duplicate correspondence ID or unknown object")
            pair_ids.add(pair.id)
            first, second = (objects[name] for name in pair.object_ids)
            if first.source_id == second.source_id:
                raise ValueError("cross-layer pair must reference different source images")
        return self
