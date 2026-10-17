"""Minimal model observations and frozen local-task packets, in native pixels."""
from __future__ import annotations

from typing import Literal

from pydantic import Field, FiniteFloat, StrictBool, model_validator

from .block_case import Frame, Record, Scope, Source, indexed, inside


class Region(Record):
    id: str
    frame_id: str
    xywh: tuple[int, int, int, int]
    role: Literal["inspection_window_not_material_boundary"]


class PhotoTask(Record):
    schema_version: Literal[1]
    document_kind: Literal["local_photo_task"]
    task_id: str
    case_id: str
    same_chip_same_location: Literal["human_reviewed_local_identity"]
    sources: dict[str, Source]
    frames: list[Frame]
    regions: list[Region]
    subject_ids: list[str]
    scopes: list[Scope]
    instructions: str

    @model_validator(mode="after")
    def references(self):
        frames = indexed(self.frames)
        indexed(self.regions)
        indexed(self.scopes)
        if len(set(self.subject_ids)) != len(self.subject_ids):
            raise ValueError("Duplicate task subjects")
        for frame in self.frames:
            if frame.source_ref not in self.sources or min(frame.size_wh) <= 0:
                raise ValueError("Invalid task frame")
        for region in self.regions:
            if region.frame_id not in frames:
                raise ValueError("Unknown task frame")
            inside(region.xywh, frames[region.frame_id].size_wh)
        for scope in self.scopes:
            if scope.frame_id is not None:
                if scope.frame_id not in frames or scope.xywh is None:
                    raise ValueError("Invalid task scope")
                inside(scope.xywh, frames[scope.frame_id].size_wh)
        return self


class Observation(Record):
    id: str
    predicate: Literal[
        "device_exists", "material_identity", "same_net", "different_net", "joined_in_region",
        "terminal_maps_to_conductor",
    ]
    subject_ids: list[str] = Field(min_length=1)
    scope_id: str
    status: Literal["candidate", "unknown"]
    value: StrictBool | Literal["aa", "poly", "ct"] | None
    evidence_refs: list[str]
    rationale: str = Field(min_length=1)
    boundary_status: Literal["unknown", "candidate"] = "unknown"
    location: Region | None = None
    boundary_polygon_xy: list[tuple[FiniteFloat, FiniteFloat]] | None = None

    @model_validator(mode="after")
    def semantics(self):
        n = len(self.subject_ids)
        if len(set(self.subject_ids)) != n:
            raise ValueError("Duplicate observation subjects")
        if self.boundary_status == "candidate" and self.boundary_polygon_xy is None:
            raise ValueError("Candidate boundary needs explicit polygon geometry")
        if self.boundary_polygon_xy is not None:
            if self.location is None or self.boundary_status != "candidate":
                raise ValueError("Boundary polygon needs a native location and candidate status")
            if len(self.boundary_polygon_xy) < 3:
                raise ValueError("Boundary polygon needs at least three vertices")
            points = self.boundary_polygon_xy
            area = sum(a[0] * b[1] - a[1] * b[0]
                       for a, b in zip(points, points[1:] + points[:1], strict=True))
            if area == 0:
                raise ValueError("Degenerate boundary polygon")
        if n != (1 if self.predicate in {"device_exists", "material_identity"} else 2):
            raise ValueError("Observation needs one object or one explicit relation pair")
        if self.status == "unknown":
            if self.value is not None:
                raise ValueError("Unknown observation must have null value")
        else:
            if self.value is None or not self.evidence_refs:
                raise ValueError("Candidate judgment needs a value and source evidence")
            if self.predicate == "material_identity":
                if self.value not in {"aa", "poly", "ct"}:
                    raise ValueError("Invalid material identity")
            elif not isinstance(self.value, bool):
                raise ValueError("Relation/device observation must have boolean value")
            if self.predicate in {"same_net", "different_net"} and self.value is not True:
                raise ValueError("Express known separation as different_net, not false same_net")
        return self


class AgentObservations(Record):
    schema_version: Literal[1]
    document_kind: Literal["agent_observations"]
    task_id: str
    input_packet: Source
    run_id: str
    purpose: Literal["live_observation", "historical_reexpression", "synthetic_fixture"] = (
        "live_observation"
    )
    producer: Literal["vision_model", "reasoning_model"]
    model_id: str | None
    prompt_version: str | None
    observations: list[Observation]
    human_corrections: None = None

    def check_task(self, task: PhotoTask):
        if self.task_id != task.task_id:
            raise ValueError("Observations belong to another task")
        indexed(self.observations)
        keys = set()
        scopes = {s.id: s for s in task.scopes}
        frames = {f.id: f for f in task.frames}
        for obs in self.observations:
            if obs.location is not None:
                if obs.location.frame_id not in frames:
                    raise ValueError("Unknown observation location frame")
                size = frames[obs.location.frame_id].size_wh
                inside(obs.location.xywh, size)
                if obs.boundary_polygon_xy is not None:
                    points = obs.boundary_polygon_xy
                    if any(x < 0 or y < 0 or x >= size[0] or y >= size[1] for x, y in points):
                        raise ValueError("Boundary polygon outside native frame")
            if not set(obs.subject_ids) <= set(task.subject_ids):
                raise ValueError("Observation refers to unknown task subjects")
            if obs.scope_id not in {s.id for s in task.scopes}:
                raise ValueError("Observation refers to unknown task scope")
            domain = scopes[obs.scope_id].domain
            if (
                obs.predicate in {"same_net", "different_net", "terminal_maps_to_conductor"}
                and domain != "electrical_case"
            ):
                raise ValueError("Electrical relation needs electrical scope")
            if obs.predicate == "joined_in_region" and domain != "physical_layer_region":
                raise ValueError("Physical joining needs local layer scope")
            if obs.predicate == "material_identity" and domain != "physical_identity":
                raise ValueError("Material identity needs physical identity scope")
            if not set(obs.evidence_refs) <= task.sources.keys():
                raise ValueError("Observation refers to unknown source")
            key = (obs.predicate, obs.scope_id, tuple(sorted(obs.subject_ids)))
            if key in keys:
                raise ValueError("Duplicate or conflicting observation proposition")
            keys.add(key)
