"""Resolve typed block claims from registered, explicitly superseded review events.

Used by `silicon-eye annotate block`. No image recognition or case-specific rules.
"""

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path

from PIL import Image

from .schemas.block_case import BlockCase


def canonical(value, key=""):
    if isinstance(value, dict):
        return {k: canonical(v, k) for k, v in sorted(value.items())}
    if isinstance(value, list):
        values = [canonical(v) for v in value]
        if all(isinstance(v, dict) for v in values) or key in {
            "subject_ids",
            "source_refs",
            "evidence_refs",
            "event_ids",
            "supersedes_event_ids",
            "member_ids",
            "terminal_ids",
        }:
            values.sort(key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False))
        return values
    return value


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(
            canonical(value),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def verify_sources(case: BlockCase, root: Path) -> None:
    root = root.resolve()
    documents = {}
    for id, source in case.sources.items():
        relative = Path(source.path)
        path = (root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"Missing/outside-root source: {id}")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != source.sha256:
            raise ValueError(f"Source hash changed: {id}")
        if path.suffix == ".json":
            documents[id] = json.loads(content)
        for frame in case.frames:
            if frame.source_ref == id:
                with Image.open(BytesIO(content)) as image:
                    if image.size != frame.size_wh:
                        raise ValueError(f"Frame size differs from source: {frame.id}")
    for event in case.review_events:
        records = [documents[s] for s in event.source_refs if s in documents]
        if not any(event.source_statement in json.dumps(d, ensure_ascii=False) for d in records):
            raise ValueError(f"Review excerpt missing from bound record: {event.id}")
        if event.actor == "human" and not any(
            isinstance(d, dict)
            and d.get("actor") == "human"
            and event.source_statement in json.dumps(d, ensure_ascii=False)
            for d in records
        ):
            raise ValueError(f"Review has no bound human source: {event.id}")


def resolve_block(case: BlockCase, evidence_checked: bool = False) -> dict:
    """Recompute all electrical components; identity/geometry never trigger union."""
    claims = {c.id: c for c in case.claims}
    superseded = {p for e in case.review_events for p in e.supersedes_event_ids}
    statuses, conflicts = [], []
    for id, claim in sorted(claims.items()):
        heads = sorted(
            [e for e in case.review_events if e.claim_id == id and e.id not in superseded],
            key=lambda e: e.id,
        )
        effects = {
            "confirmed"
            if e.verdict == "confirm"
            else "rejected"
            if e.verdict == "reject"
            else "unknown"
            for e in heads
        }
        status = (
            "conflict"
            if len(effects) > 1
            else next(iter(effects))
            if effects
            else "candidate"
            if claim.intent == "proposal"
            else "unknown"
        )
        if status == "conflict":
            conflicts.append(
                dict(kind="parallel_decisions", claim_ids=[id], event_ids=[e.id for e in heads])
            )
        statuses.append(
            dict(
                **canonical(claim.model_dump(mode="json", by_alias=True)),
                status=status,
                active_event_ids=[e.id for e in heads],
                reasons=sorted({e.verdict for e in heads}),
            )
        )
    # Two separately recorded opposite values of the same scoped fact also conflict.
    propositions = {}
    for c in statuses:
        if c["status"] == "confirmed":
            key = (c["predicate"], c["scope_id"], tuple(sorted(c["subject_ids"])))
            propositions.setdefault(key, []).append(c)
    for group in propositions.values():
        if len({c["value"] for c in group}) > 1:
            conflicts.append(
                dict(kind="contradictory_values", claim_ids=sorted(c["id"] for c in group))
            )
    terminals = sorted([e for e in case.entities if e.kind == "terminal"], key=lambda e: e.id)
    parent = {t.id: t.id for t in terminals}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    accepted = [c for c in statuses if c["status"] == "confirmed"]
    for c in accepted:
        if c["predicate"] == "same_net":
            for t in c["subject_ids"][1:]:
                a, b = find(c["subject_ids"][0]), find(t)
                parent[max(a, b)] = min(a, b)
    groups = {}
    for t in terminals:
        groups.setdefault(find(t.id), []).append(t.id)
    components = [
        dict(id=f"C{i + 1:03}", terminals=members)
        for i, members in enumerate(sorted(g for g in groups.values() if len(g) > 1))
    ]
    distinct = []
    for c in accepted:
        if c["predicate"] == "different_net":
            a, b = c["subject_ids"]
            if find(a) == find(b):
                conflicts.append(
                    dict(kind="same_net_vs_different_net", claim_ids=[c["id"]], terminal_ids=[a, b])
                )
            distinct.append((find(a), find(b)))
    existence = {
        c["subject_ids"][0]: c["value"] for c in accepted if c["predicate"] == "device_exists"
    }
    for c in accepted:
        if c["predicate"] in {"same_net", "terminal_maps_to_conductor"}:
            for id in c["subject_ids"]:
                terminal = next((t for t in terminals if t.id == id), None)
                if terminal is not None and existence.get(terminal.device_id) is False:
                    conflicts.append(
                        dict(
                            kind="connection_to_absent_device",
                            claim_ids=[c["id"]],
                            terminal_ids=[id],
                        )
                    )
    rows = []
    for i, t in enumerate(terminals):
        group = next((g for g in components if t.id in g["terminals"]), None)
        mappings = [
            c
            for c in accepted
            if c["predicate"] == "terminal_maps_to_conductor" and t.id in c["subject_ids"]
        ]
        rows.append(
            dict(
                id=t.id,
                device_id=t.device_id,
                role=t.role,
                confirmed_net_id=None if group is None else group["id"],
                display_label=f"T{i + 1:03}" if group is None else group["id"],
                mapping_status="confirmed" if mappings else "unknown",
                conductor_ids=sorted({s for c in mappings for s in c["subject_ids"] if s != t.id}),
                render_status="confirmed" if group or mappings else "unknown",
            )
        )
    matrix = [
        [
            "self"
            if a.id == b.id
            else "K"
            if find(a.id) == find(b.id)
            else "D"
            if (find(a.id), find(b.id)) in distinct or (find(b.id), find(a.id)) in distinct
            else "?"
            for b in terminals
        ]
        for a in terminals
    ]
    state = dict(
        schema_version=1,
        case_id=case.case_id,
        case_revision=case.revision,
        sources={k: v.model_dump(mode="json") for k, v in sorted(case.sources.items())},
        frames=canonical([f.model_dump(mode="json") for f in case.frames]),
        scopes=canonical([s.model_dump(mode="json") for s in case.scopes]),
        geometry_observations=canonical(
            [g.model_dump(mode="json") for g in case.geometry_observations]
        ),
        review_events=canonical([e.model_dump(mode="json") for e in case.review_events]),
        mode=case.export_request.mode,
        status="conflict" if conflicts else "review_state_ready",
        input_digest=fingerprint(case.model_dump(mode="json", by_alias=True)),
        inventory_digest=fingerprint(case.review_inventory.model_dump(mode="json", by_alias=True)),
        devices=[
            dict(**e.model_dump(mode="json", by_alias=True), existence=existence.get(e.id))
            for e in sorted(case.entities, key=lambda e: e.id)
            if e.kind == "device"
        ],
        terminals=rows,
        confirmed_components=components,
        claims=statuses,
        active_event_ids=sorted({e for c in statuses for e in c["active_event_ids"]}),
        superseded_event_ids=sorted(superseded),
        conflicts=conflicts,
        matrix=dict(terminals=[t.id for t in terminals], values=matrix),
        measurements=canonical(
            [m.model_dump(mode="json", by_alias=True) for m in case.measurements]
        ),
        boundary_ports=[],
        acceptance=dict(
            structure_draft_ready=not conflicts,
            local_topology_accepted=False,
            four_terminal_complete=False,
            simulation_ready=False,
        ),
        evidence_integrity="sources_checked" if evidence_checked else "sources_not_checked",
        limitations=[
            "Distinct component labels do not prove isolation.",
            "Confirmed mappings/identities do not imply new electrical joins.",
            "Human source/excerpt binding checks provenance, not physical truth.",
            "Only the registered case revision is resolved; no discovery of other files.",
        ],
    )
    # Conflict matrices/components are diagnostic, never an accepted graph.
    state["state_id"] = fingerprint(
        dict(case=case.model_dump(mode="json", by_alias=True), state=state)
    )
    return state
