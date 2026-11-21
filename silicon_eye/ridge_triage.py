"""Source-only triage of reviewed ridge inventories; never adopts conductor/net identities.

Run: python -m silicon_eye.ridge_triage --output runs/NEW_DIR
Requires the project's metal-batch dependencies and reviewed full-frame inputs.
"""

import argparse
import time
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from .metal_extent_batch import put, read, ref, require
from .review_package import Inputs
from .review_sheet import check
from .ridge_inventory import detect


def support(points, candidates, tolerance=2):
    """Union of sampled path support, preserving gaps and rejecting extrapolation."""
    points = np.asarray(points, dtype=float)
    covered = np.zeros(len(points), dtype=bool)
    for candidate in candidates:
        xy = np.asarray(candidate["points"], dtype=float)
        inside = (points[:, 0] >= xy[0, 0]) & (points[:, 0] <= xy[-1, 0])
        indices = np.flatnonzero(inside)
        if len(indices):
            close = (
                abs(points[indices, 1] - np.interp(points[indices, 0], xy[:, 0], xy[:, 1]))
                <= tolerance
            )
            covered[indices[close]] = True
    return covered


def classify(fragment, stability, matches):
    if fragment["peripheral_edge_risk"]:
        return "peripheral_edge_hold"
    if fragment["branch_or_parallel_overlap"]:
        return "branch_topology_hold"
    strong = [m for m in matches if m["fraction"] >= 0.9]
    if len(strong) > 1:
        return "identity_conflict_hold"
    if len(strong) == 1:
        return "known_path_context"
    if matches:
        return "partial_known_path_hold"
    if min(stability.values()) < 0.9:
        return "threshold_unstable_hold"
    return "stable_new_source_candidate"


def run(root, output):
    start = time.perf_counter()
    root = Path(root).resolve()
    output = Path(output).resolve()
    require(not output.exists() and output.is_relative_to(root / "runs"), "Use new runs directory")
    inventory_path = root / "runs/m3-wide-inventory-20261109/final/inventory.json"
    review = inventory_path.parent / "review"
    verdict = check(root, review, review / "review-decision.json")
    require(verdict["verdicts"] == {"accepted": 8}, "Requires accepted source inventory")
    inputs = Inputs(root)
    inventory = read(inventory_path)
    inputs.read(inventory["photo"])
    previous = read(inventory_path.parent / "spec.json")["previous_traces"]
    by_id = {}
    for source in previous:
        for track in inputs.document(source)["tracks"]:
            by_id.setdefault(track["id"], []).append(track)
    output.mkdir(parents=True)
    with Image.open(root / inventory["photo"]["path"]) as image:
        gray = np.asarray(image.convert("L"))
    variants = {}
    for threshold in [8.0, 12.0]:
        fragments, filtered = detect(gray, threshold=threshold, minimum_span=120)
        variants[str(threshold)] = fragments
        put(
            output / f"threshold-{threshold}.json",
            dict(threshold=threshold, fragments=fragments, filtered=filtered),
        )
    rows = []
    for f in inventory["fragments"]:
        stability = {}
        for key, fragments in variants.items():
            # Restrict by bounding-box overlap before comparing sampled paths.
            candidates = [
                g
                for g in fragments
                if g["bounds"][2] >= f["bounds"][0]
                and g["bounds"][0] <= f["bounds"][2]
                and g["bounds"][3] >= f["bounds"][1] - 2
                and g["bounds"][1] <= f["bounds"][3] + 2
            ]
            stability[key] = float(support(f["points"], candidates).mean())
        matches = []
        for identity, tracks in by_id.items():
            fraction = float(support(f["points"], tracks, tolerance=4).mean())
            if fraction >= 0.1:
                matches.append(dict(id=identity, fraction=fraction))
        matches.sort(key=lambda m: -m["fraction"])
        rows.append(
            dict(
                fragment_id=f["id"],
                bounds=f["bounds"],
                points=f["points"],
                category=classify(f, stability, matches),
                threshold_support=stability,
                old_path_matches=matches,
                source_identity="unassigned",
                electrical_identity="unknown",
                physical_endpoints="unknown",
            )
        )
    stable = [r for r in rows if r["category"] == "stable_new_source_candidate"]
    # Candidate-only continuity proposals; no union/physical identity assignment across gaps.
    links = []
    for a in stable:
        ax, ay = a["points"][-1]
        for b in stable:
            bx, by = b["points"][0]
            gap = bx - ax
            if 0 < gap <= 40 and abs(by - ay) <= 4:
                links.append(
                    dict(
                        left=a["fragment_id"],
                        right=b["fragment_id"],
                        gap_px=gap,
                        dy_px=by - ay,
                        status="unknown_do_not_merge",
                    )
                )
    for i, row in enumerate(stable, 1):
        row["candidate_object_id"] = f"SRC-M3-{i:04}"
    result = dict(
        kind="source_candidate_triage",
        actor="AI_program",
        sources=dict(
            inventory=ref(root, inventory_path),
            decision=ref(root, review / "review-decision.json"),
            photo=inventory["photo"],
            algorithm=ref(root, Path(__file__)),
        ),
        parameters=dict(
            thresholds=[8, 10, 12],
            stable_fraction=0.9,
            tolerance_px=2,
            identity_tolerance_px=4,
            identity_min_fraction=0.9,
        ),
        categories=dict(Counter(r["category"] for r in rows)),
        rows=rows,
        continuity_proposals=links,
        no_geometry_or_network_mutation=True,
    )
    put(output / "triage.json", result)
    put(
        output / "source-candidates.json",
        dict(
            kind="unadopted_source_objects",
            objects=stable,
            note="Source candidates, not metal IDs. No design geometry or connectivity inferred.",
        ),
    )
    put(
        output / "timing.json",
        dict(
            total_seconds=time.perf_counter() - start,
            fragments=len(rows),
            stable_candidates=len(stable),
            continuity_proposals=len(links),
        ),
    )
    print(result["categories"])
    print(read(output / "timing.json"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(Path.cwd(), args.output)
