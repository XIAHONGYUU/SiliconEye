"""Adapt source-bound AI observations into existing case proposals and review cards.

Run: python -m silicon_eye.observation_adapter --package package.json
     --observations observations.json --root . --output runs/new-adaptation
Uses existing package rendering; no model invocation or human decisions are generated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image

from .block_export import write_json
from .block_review import resolve_block
from .review_package import Inputs, PackageRequest, prepare, run_package
from .schemas.agent_observation import AgentObservations, PhotoTask
from .schemas.block_case import BlockCase, Source


def reference(path, root):
    path = Path(path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Adapter input/output must stay inside repository root")
    return Source(path=str(path.relative_to(root)),
                  sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def comparison(obs, state, materials):
    """Compare to existing decisions without promoting a model observation."""
    result = dict(status="not_previously_confirmed", claim_ids=[], event_ids=[],
                  material_review_sources=[])
    if obs.predicate == "material_identity":
        matches = [(r, m["observations"]["review_source"])
                   for m in materials if m["identity_status"] == "human_confirmed"
                   for r in m["observations"]["regions"] if r["id"] == obs.subject_ids[0]]
        values = {r["material"] for r, _ in matches}
        result["material_review_sources"] = [ref for _, ref in matches]
    else:
        matches = [c for c in state["claims"]
                   if c["predicate"] == obs.predicate and c["scope_id"] == obs.scope_id
                   and set(c["subject_ids"]) == set(obs.subject_ids)
                   and c["status"] in {"confirmed", "rejected"}]
        result["claim_ids"] = [c["id"] for c in matches]
        result["event_ids"] = sorted({e for c in matches for e in c["active_event_ids"]})
        values = {c["value"] for c in matches if c["status"] == "confirmed"}
        # A rejection does not assert the inverse physical fact.
        if obs.status == "candidate" and any(
            c["status"] == "rejected" and c["value"] == obs.value for c in matches
        ):
            result["status"] = "differs_from_human_review"
            return result
        if obs.predicate in {"same_net", "different_net"}:
            ids, matrix = state["matrix"]["terminals"], state["matrix"]["values"]
            a, b = (ids.index(s) for s in obs.subject_ids)
            known = matrix[a][b]
            if known in {"K", "D"}:
                values.add((known == "K") == (obs.predicate == "same_net"))
    if values:
        result["status"] = ("model_unknown_existing_decision_retained" if obs.status == "unknown"
                            else "matches_human_review" if values == {obs.value}
                            else "differs_from_human_review")
    return result


def build(inputs, package_ref, batch_ref):
    request = PackageRequest.model_validate(inputs.document(package_ref))
    if request.observation_adaptations:
        raise ValueError("v1 adapts an original package, not a chained adaptation")
    case, _, materials = prepare(request, inputs)
    base_state = resolve_block(case, evidence_checked=True)
    if base_state["conflicts"]:
        raise ValueError("Resolve existing human decision conflicts before adaptation")
    batch = AgentObservations.model_validate(inputs.document(batch_ref))
    task = PhotoTask.model_validate(inputs.document(batch.input_packet))
    batch.check_task(task)
    if task.case_id != case.case_id:
        raise ValueError("Task belongs to a different case")
    frames = {f.id: f for f in case.frames}
    scopes = {s.id: s for s in case.scopes}
    entities = {e.id: e for e in case.entities}
    result = case.model_dump(mode="json", by_alias=True)
    for frame in task.frames:
        source = task.sources[frame.source_ref]
        with Image.open(BytesIO(inputs.read(source))) as image:
            if image.size != frame.size_wh:
                raise ValueError("Task frame size differs from photo")
        if frame.id in frames and (
            frame.size_wh != frames[frame.id].size_wh
            or source != case.sources[frames[frame.id].source_ref]
        ):
            raise ValueError("Task native frame/source differs from existing case")
        if frame.id not in frames:
            # The task explicitly declares this extra evidence frame; no alignment is inferred.
            if (frame.source_ref in result["sources"]
                    and result["sources"][frame.source_ref] != source.model_dump()):
                raise ValueError("New task frame source ID collides with existing case")
            result["sources"][frame.source_ref] = source.model_dump()
            result["frames"].append(frame.model_dump(mode="json"))
    for source in task.sources.values():
        inputs.read(source)
    prefix = "agent_" + batch_ref.sha256[:16]
    for name, ref in [(prefix + "_batch", batch_ref), (prefix + "_task", batch.input_packet)]:
        if name in result["sources"]:
            raise ValueError("Adapter provenance ID collision")
        result["sources"][name] = ref.model_dump()
    result["revision"] += "+" + prefix
    cards = []
    for obs in batch.observations:
        if not set(obs.subject_ids) <= entities.keys():
            raise ValueError("Adapter requires existing explicitly typed case entities")
        if obs.predicate == "material_identity":
            if entities[obs.subject_ids[0]].kind not in {"physical_region", "image_feature"}:
                raise ValueError("Material identity requires a material/image entity")
        elif obs.scope_id not in scopes or scopes[obs.scope_id] != next(
            s for s in task.scopes if s.id == obs.scope_id
        ):
            raise ValueError("Case scope differs from task; explicit scope mapping required")
        if obs.predicate != "material_identity":
            # Check predicate entity types even for unknowns; this temporary value is never saved.
            BlockCase.model_validate(dict(result, claims=result["claims"] + [dict(
                id=prefix + "_typecheck", predicate=obs.predicate,
                subject_ids=obs.subject_ids, scope_id=obs.scope_id,
                value=True, intent="proposal", producer=batch.producer,
                evidence_refs=[prefix + "_batch"],
            )]))
        if obs.location is not None:
            loc = obs.location
            frame = next(f for f in task.frames if f.id == loc.frame_id)
            if obs.status == "candidate" and frame.source_ref not in obs.evidence_refs:
                raise ValueError("Location photo must be declared observation evidence")
            x, y, w, h = loc.xywh
            if not any(r.frame_id == loc.frame_id and x >= r.xywh[0] and y >= r.xywh[1]
                       and x+w <= r.xywh[0]+r.xywh[2] and y+h <= r.xywh[1]+r.xywh[3]
                       for r in task.regions):
                raise ValueError("Location outside declared task inspection windows")
            scope = next(s for s in task.scopes if s.id == obs.scope_id)
            if scope.frame_id is not None and scope.frame_id != loc.frame_id:
                raise ValueError("Location frame differs from physical scope")
            if obs.boundary_polygon_xy is not None and any(
                not (x <= px < x+w and y <= py < y+h) for px, py in obs.boundary_polygon_xy
            ):
                raise ValueError("Candidate boundary outside its inspection window")
        if obs.boundary_polygon_xy is not None and obs.predicate != "material_identity":
            raise ValueError("v1 boundary display is supported only for material cards")
        card = obs.model_dump(mode="json")
        card["existing_review"] = comparison(obs, base_state, materials)
        card["case_claim_id"] = None
        if obs.predicate == "material_identity":
            card["route"] = "material_card"
        elif obs.status == "unknown":
            # BlockCase claims require boolean values; never invent one for unknown.
            card["route"] = "unknown_card_no_case_assertion"
        else:
            claim_id = prefix + "_" + obs.id
            if any(c["id"] == claim_id for c in result["claims"]):
                raise ValueError("Adapter claim ID collision")
            evidence = [prefix + "_batch"]
            for source_id in obs.evidence_refs:
                source = task.sources[source_id]
                candidates = [k for k, v in result["sources"].items() if v == source.model_dump()]
                if not candidates:
                    raise ValueError("Observation evidence needs explicit existing case source")
                evidence.append(sorted(candidates)[0])
            result["claims"].append(dict(
                id=claim_id, predicate=obs.predicate, subject_ids=obs.subject_ids,
                scope_id=obs.scope_id, value=obs.value, intent="proposal",
                producer=batch.producer, evidence_refs=sorted(set(evidence)),
            ))
            card.update(route="case_proposal", case_claim_id=claim_id)
        cards.append(card)
    adapted = BlockCase.model_validate(result)
    state = resolve_block(adapted, evidence_checked=True)
    for field in ["matrix", "confirmed_components", "terminals", "review_events", "devices"]:
        if state[field] != base_state[field]:
            raise ValueError("Adaptation unexpectedly changed accepted physical/electrical state")
    data = dict(
        schema_version=1, document_kind="agent_observation_adaptation",
        base_package=package_ref.model_dump(), observations=batch_ref.model_dump(),
        task=batch.input_packet.model_dump(), case_id=case.case_id, run_id=batch.run_id,
        observation_purpose=batch.purpose, cards=cards,
        source_frames=[f.model_dump(mode="json") for f in task.frames],
        task_regions=[r.model_dump(mode="json") for r in task.regions],
        task_sources={k: v.model_dump() for k, v in task.sources.items()},
        human_decisions_changed=False, new_model_invocation=False,
    )
    return adapted, data, request


def validate_adaptation(inputs, entry, case):
    doc = inputs.document(entry)
    adapted, expected, _ = build(inputs, Source(**doc["base_package"]),
                                 Source(**doc["observations"]))
    if doc != expected or adapted != case:
        raise ValueError("Adaptation cards/case differ from bound observation inputs")
    return doc


def run_adapter(package_path, observations_path, output, root="."):
    inputs = Inputs(root)
    out = Path(output).resolve()
    if not out.is_relative_to(inputs.root) or out.exists():
        raise ValueError("Adapter output must be a new directory inside root")
    case, data, request = build(inputs, reference(package_path, inputs.root),
                                reference(observations_path, inputs.root))
    out.parent.mkdir(parents=True, exist_ok=True)

    def future_ref(name, content):
        return Source(path=str((out / name).relative_to(inputs.root)),
                      sha256=hashlib.sha256(content).hexdigest())

    case_bytes = encode(case.model_dump(mode="json", by_alias=True))
    data_bytes = encode(data)
    new_request = request.model_copy(update={
        "case": future_ref("case.json", case_bytes),
        "observation_adaptations": [future_ref("adaptation.json", data_bytes)],
    })
    for path, sha in list(inputs.files.items()):
        inputs.read(Source(path=path, sha256=sha))
    with tempfile.TemporaryDirectory(prefix=".observation-adapter-", dir=out.parent) as tmp:
        stage = Path(tmp) / "adaptation"
        stage.mkdir()
        (stage / "case.json").write_bytes(case_bytes)
        (stage / "adaptation.json").write_bytes(data_bytes)
        write_json(stage / "package-request.json", new_request.model_dump(mode="json"))
        stage.rename(out)
    # Validated inputs remain available for diagnosis if rendering fails; never overwrite a run.
    return run_package(out / "package-request.json", out / "review", inputs.root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True)
    parser.add_argument("--observations", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = run_adapter(args.package, args.observations, args.output, args.root)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"Observation adaptation failed: {error}\n")
    print("Review: " + str(Path(args.output) / "review/report.md"))
    if result["status"] == "conflict":
        parser.exit(2)


if __name__ == "__main__":
    main()
