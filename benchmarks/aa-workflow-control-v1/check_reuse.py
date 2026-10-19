"""Verify frozen local-to-native reuse without segmentation.

Run from repo: .venv/bin/python benchmarks/aa-workflow-control-v1/check_reuse.py
Requires existing native-canvas evidence (restore archives if missing), numpy and OpenCV.
"""

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

r = Path(__file__).resolve().parents[2]


def lock(p):
    p = Path(p)
    return {"path": str(p.relative_to(r)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}


specpath = r / "benchmarks/aa-native-canvas-v1/spec-v1.json"
s = json.loads(specpath.read_text())
out = r / "benchmarks/aa-workflow-control-v1"
out.mkdir(exist_ok=True)
assert lock(r / s["source"]["path"]) == s["source"], "Changed source"
a = np.load(r / "runs/aa-native-canvas-v1a/states.npy", mmap_mode="r")
g = np.load(r / "runs/aa-native-canvas-v1a/global-model-states.npy", mmap_mode="r")
rows = []
for c in s["local_candidates"]:
    refs = {}
    for k in ("states", "domain", "human_review"):
        ref = c[k]
        actual = lock(r / ref["path"])
        assert actual == ref, (c["id"], k)
        refs[k] = actual
    x, y, b, d = c["native_bbox"]
    old = np.load(r / c["states"]["path"])
    domain = cv2.imread(str(r / c["domain"]["path"]), 0) > 0
    for left, t, rr, bb in s["excluded_native_boxes"]:
        xx, yy, rx, by = max(left, x), max(t, y), min(rr, b), min(bb, d)
        if xx < rx and yy < by:
            domain[yy - y : by - y, xx - x : rx - x] = False
    current = a[y:d, x:b]
    original = g[y:d, x:b]
    change = {
        f"{i}_to_{j}": int(np.sum(domain & (old == i) & (current == j)))
        for i in (-1, 0, 1)
        for j in (-1, 0, 1)
        if i != j
    }
    assert not sum(change.values()), c["id"]
    rows.append(
        dict(
            id=c["id"],
            native_bbox=c["native_bbox"],
            references=refs,
            scope=c["scope"],
            compared_pixels=int(domain.sum()),
            changes=change,
            global_to_local_changed_pixels=int(np.sum(domain & (original != current))),
            decision="reuse_existing_local_no_recompute",
            material_reacceptance="not_performed_or_required_for_unchanged_scope",
        )
    )
report = dict(
    schema_version=1,
    mode="read_existing_arrays_only_no_training_or_inference",
    source=lock(r / s["source"]["path"]),
    spec=lock(specpath),
    canvas=lock(r / "runs/aa-native-canvas-v1a/states.npy"),
    baseline=lock(r / "benchmarks/aa-skill-baseline-v2.json"),
    local_comparisons=rows,
    scope=(
        "Assembly preservation only; neither a dense accuracy benchmark "
        "nor a semantic or speed improvement claim."
    ),
    gates={
        "local_assembly_preservation": "PASS",
        "whole_frame_material": "FAIL_known_semantic_errors",
        "full_frame_algorithm_nonregression": "NOT_CHECKED_no_matched_full_frame_before_after",
        "efficiency_improvement": "NOT_MEASURED",
        "formal_geometry": "NOT_APPLICABLE_photo_candidate",
    },
    decision=(
        "Do not adopt global RF as default; retain five locals and earlier "
        "full-frame candidates with existing defect lists. No N01-N12 restart."
    ),
    recompute={
        "now": [],
        "conditional": [
            (
                "Locate unresolved resistor-interior false-positive boundaries "
                "from existing photos; "
                "repair only evidenced region, protect outer rings."
            ),
            (
                "For other prior F01-F12 defects, check current existing candidates first; "
                "do not retrain unchanged accepted scopes."
            ),
        ],
    },
    known_failure_reference=lock(r / "benchmarks/aa-native-canvas-v1/ai-review-v1.json"),
    earlier_full_frame_review=lock(r / "benchmarks/aa-completion-v1/human-review-v2.json"),
)
(out / "reuse-comparison-v1.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n"
)
print(
    json.dumps(
        {
            "cases": [
                {
                    k: v
                    for k, v in t.items()
                    if k in ["id", "compared_pixels", "changes", "decision"]
                }
                for t in rows
            ],
            "gates": report["gates"],
        },
        ensure_ascii=False,
    )
)
