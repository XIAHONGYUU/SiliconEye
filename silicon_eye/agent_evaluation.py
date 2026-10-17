"""Compare explicit AI assertions to a partial reviewed reference, not physical truth.

Run: python -m silicon_eye.agent_evaluation --reference ref.json --observations ai.json
     --root . --output new-result.json
No model is called; human effort remains unmeasured until independently recorded.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from .review_package import Inputs
from .schemas.agent_observation import AgentObservations, Observation, PhotoTask


def key(item):
    return item["predicate"], item["scope_id"], tuple(sorted(item["subject_ids"]))


def evaluate(reference_path, observations_path, root="."):
    inputs = Inputs(root)
    reference = json.loads(Path(reference_path).read_text())
    if reference.get("schema_version") != 1 or reference.get("kind") != "partial_task_reference":
        raise ValueError("Unsupported partial reference")
    task = PhotoTask.model_validate(inputs.document(reference["input_packet"]))
    for source in task.sources.values():
        inputs.read(source)
    for frame in task.frames:
        with Image.open(inputs.root / task.sources[frame.source_ref].path) as image:
            if image.size != frame.size_wh:
                raise ValueError("Task frame size differs from photo")
    for source in reference["review_sources"].values():
        record = inputs.document(source)
        if record.get("actor") != "human" or not record.get("statement"):
            raise ValueError("Reference needs human review provenance")
    batch = AgentObservations.model_validate_json(Path(observations_path).read_text())
    if batch.input_packet.model_dump() != reference["input_packet"]:
        raise ValueError("Agent and reference use different photo packets")
    batch.check_task(task)
    predictions = {key(o.model_dump()): o.model_dump() for o in batch.observations}
    if not reference.get("labels"):
        raise ValueError("Reference must contain explicit assertions")
    rows, seen = [], set()
    for label in reference["labels"]:
        k = key(label)
        if k in seen:
            raise ValueError("Duplicate reference propositions")
        seen.add(k)
        if not set(label["review_refs"]) <= reference["review_sources"].keys():
            raise ValueError("Reference label has unknown human evidence")
        if not label["review_refs"]:
            raise ValueError("Reference label needs review provenance")
        prediction = predictions.get(k)
        known = label["reference_status"] == "known"
        if label["reference_status"] not in {"known", "unresolved"}:
            raise ValueError("Invalid partial-reference status")
        if known == (label["value"] is None):
            raise ValueError("Reference value/status inconsistent")
        normalized = Observation(
            id=label["id"], predicate=label["predicate"], subject_ids=label["subject_ids"],
            scope_id=label["scope_id"], status="candidate" if known else "unknown",
            value=label["value"], evidence_refs=[next(iter(task.sources))],
            rationale="Reference format validation only; provenance checked separately.",
        )
        batch.model_copy(update={"observations": [normalized]}).check_task(task)
        asserted = prediction is not None and prediction["status"] == "candidate"
        if known:
            outcome = "missed_known" if not asserted else (
                "correct" if prediction["value"] == label["value"] else "wrong"
            )
            if not asserted and label["predicate"] in {"same_net", "different_net"}:
                other = "different_net" if label["predicate"] == "same_net" else "same_net"
                opposite = predictions.get((other, k[1], k[2]))
                if opposite and opposite["status"] == "candidate":
                    outcome = "wrong"
        else:
            outcome = "unsupported_certainty" if asserted else (
                "kept_unknown" if prediction else "missing_unresolved"
            )
        rows.append(dict(id=label["id"], outcome=outcome))
    unreferenced = [o["id"] for k, o in predictions.items() if k not in seen]
    counts = {name: sum(r["outcome"] == name for r in rows) for name in [
        "correct", "wrong", "missed_known", "unsupported_certainty", "kept_unknown",
        "missing_unresolved",
    ]}
    return dict(
        schema_version=1, task_id=task.task_id, run_id=batch.run_id,
        model_id=batch.model_id, prompt_version=batch.prompt_version,
        run_metadata_complete=bool(batch.model_id and batch.prompt_version),
        evaluation_kind="partial_historical_development_reference_not_blind_accuracy",
        counts=counts, outcomes=rows, unreferenced_observations=unreferenced,
        reference_assertion_gate_pass=not (
            counts["wrong"] or counts["missed_known"] or counts["unsupported_certainty"]
            or counts["missing_unresolved"] or unreferenced
        ),
        human_correction_count=None, human_time_seconds=None,
        note="Gate checks only explicit reference assertions. Unknown is not isolation. "
             "Unreferenced assertions need review, not automatic wrong labels; "
             "localization, device discovery and physical truth are not scored.",
        verified_inputs=inputs.files,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--observations", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        out = Path(args.output)
        if out.exists():
            raise ValueError("Evaluation output already exists")
        result = evaluate(args.reference, args.observations, args.root)
        with out.open("x") as stream:
            stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"Agent evaluation failed: {error}\n")
    print(json.dumps(result["counts"], ensure_ascii=False))
    if not result["reference_assertion_gate_pass"]:
        parser.exit(2)


if __name__ == "__main__":
    main()
