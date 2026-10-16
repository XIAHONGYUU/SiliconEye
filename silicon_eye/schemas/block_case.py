"""Pixel-based block review input, separate from micron-based device models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, StrictBool, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(Record):
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class Frame(Record):
    id: str
    source_ref: str
    unit: Literal["px"]
    coordinates: Literal["xy_half_open"]
    size_wh: tuple[int, int]


class Scope(Record):
    id: str
    domain: Literal["electrical_case", "physical_identity", "physical_layer_region"]
    extent: str
    frame_id: str | None = None
    xywh: tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat] | None = None


class Entity(Record):
    id: str = Field(min_length=1, max_length=100)
    kind: Literal[
        "device",
        "terminal",
        "device_group",
        "physical_region",
        "conductor_inspection_feature",
        "image_feature",
    ]
    class_label: Literal["MOS"] | None = None
    polarity: None = None
    source_drain_orientation: None = None
    device_id: str | None = None
    role: Literal["G", "A", "B", "Bulk"] | None = None
    location: None = None
    member_ids: list[str] = Field(default_factory=list)
    terminal_ids: list[str] = Field(default_factory=list)


class Geometry(Record):
    entity_id: str
    frame_id: str
    xywh: tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat]
    role: Literal["inspection_window_not_material_boundary"]
    status: Literal["candidate"]
    producer: str


class Measurement(Record):
    entity_id: str
    kind: Literal["visible_support_proxy"]
    unit: Literal["px"]
    span: FiniteFloat = Field(gt=0)
    run_median: FiniteFloat = Field(gt=0)
    window_clipped: StrictBool
    physical_wl: None = Field(default=None, alias="physical_WL")
    method: str
    evidence_refs: list[str] = Field(min_length=1)


class Claim(Record):
    id: str
    predicate: Literal[
        "device_exists",
        "shared_physical_region",
        "joined_in_region",
        "same_feature_identity",
        "terminal_maps_to_conductor",
        "same_net",
        "different_net",
    ]
    subject_ids: list[str] = Field(min_length=1)
    scope_id: str
    value: StrictBool
    intent: Literal["proposal", "question"]
    producer: str
    evidence_refs: list[str] = Field(min_length=1)


class ReviewEvent(Record):
    id: str
    claim_id: str
    verdict: Literal["confirm", "reject", "no_evidence", "defer", "withdraw"]
    actor: Literal["human", "script", "vision_model", "reasoning_model"]
    source_refs: list[str] = Field(min_length=1)
    source_statement: str = Field(min_length=1)
    supersedes_event_ids: list[str] = Field(default_factory=list)
    normalization_note: str | None = None


class Inventory(Record):
    source_refs: list[str]
    event_ids: list[str]
    registration_policy: str


class ExportRequest(Record):
    mode: Literal["current", "snapshot"]
    rendering: Literal["from_resolved_state_only"]
    unknown_electrical_relations: Literal["preserve"]
    network_labels_are: Literal["presentation_only_not_entity_identity"]


def indexed(records):
    result = {r.id: r for r in records}
    if len(result) != len(records) or any(not r.id for r in records):
        raise ValueError("Duplicate record IDs")
    return result


def inside(box, size):
    x, y, w, h = box
    if min(x, y) < 0 or min(w, h) <= 0 or x + w > size[0] or y + h > size[1]:
        raise ValueError("Geometry outside native frame")


class BlockCase(Record):
    schema_version: Literal[1]
    document_kind: Literal["block_case"]
    case_id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    source_base: Literal["repository_root"]
    sources: dict[str, Source]
    frames: list[Frame]
    scopes: list[Scope]
    entities: list[Entity] = Field(min_length=1)
    geometry_observations: list[Geometry] = Field(default_factory=list)
    measurements: list[Measurement] = Field(default_factory=list)
    claims: list[Claim]
    review_events: list[ReviewEvent]
    review_inventory: Inventory
    export_request: ExportRequest
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def references(self):
        entities, scopes = indexed(self.entities), indexed(self.scopes)
        frames, claims = indexed(self.frames), indexed(self.claims)
        events = indexed(self.review_events)
        if not any(e.kind == "device" for e in self.entities):
            raise ValueError("Block case needs at least one MOS")
        if len({m.entity_id for m in self.measurements}) != len(self.measurements):
            raise ValueError("v1 allows one support measurement per device")
        if sum(s.domain == "electrical_case" for s in self.scopes) != 1:
            raise ValueError("v1 requires exactly one electrical case scope")
        for f in self.frames:
            if f.source_ref not in self.sources or min(f.size_wh) <= 0:
                raise ValueError("Invalid frame source/size")
        for s in self.scopes:
            if s.domain == "physical_layer_region" and (s.frame_id is None or s.xywh is None):
                raise ValueError("Physical layer scope needs frame and region")
            if s.xywh is not None and s.frame_id is None:
                raise ValueError("Scoped geometry needs a frame")
            if s.frame_id is not None:
                if s.frame_id not in frames or s.xywh is None:
                    raise ValueError("Invalid scope frame/region")
                inside(s.xywh, frames[s.frame_id].size_wh)
        for e in self.entities:
            if e.kind == "device":
                terminals = [
                    t.role for t in self.entities if t.kind == "terminal" and t.device_id == e.id
                ]
                if (
                    e.class_label != "MOS"
                    or len(terminals) != 4
                    or set(terminals) != {"A", "B", "Bulk", "G"}
                ):
                    raise ValueError("MOS must have exactly G/A/B/Bulk terminals")
            if e.kind == "terminal" and (
                e.device_id not in entities
                or entities[e.device_id].kind != "device"
                or e.role is None
            ):
                raise ValueError("Invalid terminal owner/role")
            if e.kind == "device_group" and not e.member_ids:
                raise ValueError("Device group needs members")
            if any(x not in entities or entities[x].kind != "device" for x in e.member_ids):
                raise ValueError("Invalid device group member")
            if any(x not in entities or entities[x].kind != "terminal" for x in e.terminal_ids):
                raise ValueError("Invalid physical terminal reference")
        for g in self.geometry_observations:
            if g.entity_id not in entities or g.frame_id not in frames:
                raise ValueError("Invalid geometry reference")
            inside(g.xywh, frames[g.frame_id].size_wh)
        for m in self.measurements:
            if m.entity_id not in entities or not set(m.evidence_refs) <= self.sources.keys():
                raise ValueError("Invalid measurement reference")
        for c in self.claims:
            if c.scope_id not in scopes or not set(c.subject_ids) <= entities.keys():
                raise ValueError("Invalid claim reference")
            if (
                len(set(c.subject_ids)) != len(c.subject_ids)
                or not set(c.evidence_refs) <= self.sources.keys()
            ):
                raise ValueError("Invalid claim subjects/evidence")
            kinds = [entities[x].kind for x in c.subject_ids]
            domain = scopes[c.scope_id].domain
            valid = {
                "device_exists": kinds == ["device"],
                "shared_physical_region": (
                    kinds.count("physical_region") == 1
                    and kinds.count("terminal") >= 2
                    and len(kinds) == kinds.count("terminal") + 1
                    and domain == "physical_identity"
                ),
                "joined_in_region": kinds == ["physical_region"] * 2
                and domain == "physical_layer_region",
                "same_feature_identity": sorted(kinds) == ["device_group", "image_feature"]
                and domain == "physical_identity",
                "terminal_maps_to_conductor": sorted(kinds)
                == ["conductor_inspection_feature", "terminal"]
                and domain == "electrical_case",
                "same_net": kinds == ["terminal"] * len(kinds)
                and len(kinds) >= 2
                and domain == "electrical_case",
                "different_net": kinds == ["terminal"] * 2 and domain == "electrical_case",
            }[c.predicate]
            if not valid or (
                not c.value and c.predicate not in {"device_exists", "joined_in_region"}
            ):
                raise ValueError("Invalid predicate types/value/scope")
        inventory = self.review_inventory
        if (
            len(set(inventory.event_ids)) != len(inventory.event_ids)
            or set(inventory.event_ids) != events.keys()
            or len(set(inventory.source_refs)) != len(inventory.source_refs)
            or set(inventory.source_refs) != {s for e in self.review_events for s in e.source_refs}
        ):
            raise ValueError("Review inventory does not match registered events/sources")
        for e in self.review_events:
            if e.claim_id not in claims or not set(e.source_refs) <= self.sources.keys():
                raise ValueError("Invalid review reference")
            if e.verdict in {"confirm", "reject", "withdraw"} and e.actor != "human":
                raise ValueError("Physical decision requires human review")
            if len(set(e.supersedes_event_ids)) != len(e.supersedes_event_ids):
                raise ValueError("Duplicate supersession")
            if e.verdict == "withdraw" and not e.supersedes_event_ids:
                raise ValueError("Withdrawal must name a previous event")
            for parent in e.supersedes_event_ids:
                if parent not in events or events[parent].claim_id != e.claim_id:
                    raise ValueError("Supersession must reference the same claim")
        visited, visiting = set(), set()

        def visit(id):
            if id in visiting:
                raise ValueError("Supersession cycle")
            if id in visited:
                return
            visiting.add(id)
            for parent in events[id].supersedes_event_ids:
                visit(parent)
            visiting.remove(id)
            visited.add(id)

        for id in events:
            visit(id)
        return self
