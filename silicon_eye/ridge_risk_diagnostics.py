"""Localize source ridge risks without inferring conductor topology.

Run: python -m silicon_eye.ridge_risk_diagnostics --output runs/NEW_DIR
Requires existing OpenCV/Pillow/NumPy and accepted full-frame source inventory.
"""

import argparse
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .metal_extent_batch import put, read, ref, require
from .review_package import Inputs
from .ridge_triage import support


def intervals(mask):
    """Return half-open integer intervals; never fill missing columns."""
    edges = np.diff(np.r_[False, np.asarray(mask, dtype=bool), False].astype(int))
    return list(
        zip(np.flatnonzero(edges == 1).tolist(), np.flatnonzero(edges == -1).tolist(), strict=True)
    )


def sample_support(mask, points, radius=2):
    result = []
    for x, y in points:
        x, y = int(round(x)), int(round(y))
        result.append(bool(mask[max(0, y - radius) : min(mask.shape[0], y + radius + 1), x].any()))
    return np.asarray(result)


def run(root, output):
    start = time.perf_counter()
    root = Path(root).resolve()
    output = Path(output).resolve()
    require(not output.exists() and output.is_relative_to(root / "runs"), "Use new runs directory")
    base = root / "runs/m3-wide-inventory-20261109/final"
    inventory = read(base / "inventory.json")
    triage = read(root / "runs/m3-triage-20261111/verified/triage.json")
    rows = {r["fragment_id"]: r for r in triage["rows"]}
    inputs = Inputs(root)
    inputs.read(inventory["photo"])
    with Image.open(root / inventory["photo"]["path"]) as image:
        gray = np.asarray(image.convert("L"))
    smooth = cv2.GaussianBlur(gray.astype(np.float32), (0, 0), sigmaX=3, sigmaY=1)
    ridge = smooth - cv2.GaussianBlur(smooth, (0, 0), sigmaX=0.01, sigmaY=6)
    localmax = cv2.dilate(ridge, np.ones((5, 1), np.uint8))
    peak = ridge >= localmax - 1e-5
    unstable = [
        f for f in inventory["fragments"] if rows[f["id"]]["category"] == "threshold_unstable_hold"
    ]
    threshold_rows = {f["id"]: {} for f in unstable}
    branch_rows = []
    sections = []
    for threshold in [8, 10, 12]:
        raw = (peak & (ridge >= threshold)).astype(np.uint8)
        _, labels, stats, _ = cv2.connectedComponentsWithStats(
            cv2.dilate(raw, np.ones((3, 1), np.uint8)), connectivity=8
        )
        long_ids = (stats[:, cv2.CC_STAT_WIDTH] >= 120) & (
            stats[:, cv2.CC_STAT_WIDTH] >= 4 * stats[:, cv2.CC_STAT_HEIGHT]
        )
        long_ids[0] = False
        kept = raw & long_ids[labels]
        for f in unstable:
            a = sample_support(raw, f["points"])
            b = sample_support(kept, f["points"])
            threshold_rows[f["id"]][str(threshold)] = dict(
                raw_peak_fraction=float(a.mean()),
                kept_component_fraction=float(b.mean()),
                short_component_only_samples=int((a & ~b).sum()),
                unsupported_sample_runs=intervals(~a),
            )
        if threshold != 10:
            continue
        lookup = {tuple(map(int, s[:4])): i for i, s in enumerate(stats) if i}
        for f in inventory["fragments"]:
            if rows[f["id"]]["category"] != "branch_topology_hold":
                continue
            x, y, x1, y1 = f["bounds"]
            component = lookup[(x, y, x1 - x, y1 - y)]
            mask = (labels[y:y1, x:x1] == component) & raw[y:y1, x:x1].astype(bool)
            good = np.zeros(x1 - x, dtype=bool)
            bad = np.zeros(x1 - x, dtype=bool)
            center = np.zeros(x1 - x)
            for col in range(x1 - x):
                yy = np.flatnonzero(mask[:, col])
                if not len(yy):
                    continue
                bad[col] = yy[-1] - yy[0] > 3
                good[col] = not bad[col]
                center[col] = y + yy[(len(yy) - 1) // 2]
            require(
                int(bad.sum()) == f["ambiguous_columns"], "Source component reproduction mismatch"
            )
            # Guard 8 pixels around ambiguous columns; never bridge them.
            guard = cv2.dilate(bad.astype(np.uint8)[None, :], np.ones((1, 17), np.uint8))[0].astype(
                bool
            )
            safe = good & ~guard
            ranges = intervals(safe)
            kept_ranges = [(a, b) for a, b in ranges if b - a >= 120]
            for i, (a, b) in enumerate(kept_ranges, 1):
                xx = list(range(a, b, 8))
                if xx[-1] != b - 1:
                    xx.append(b - 1)
                sections.append(
                    dict(
                        id=f"{f['id']}-SECTION-{i:02}",
                        parent_fragment=f["id"],
                        native_x=[x + a, x + b - 1],
                        points=[[x + k, float(center[k])] for k in xx],
                        status="source_section_only",
                        physical_identity="unknown",
                        connections=[],
                    )
                )
            branch_rows.append(
                dict(
                    id=f["id"],
                    bounds=f["bounds"],
                    ambiguous_columns=int(bad.sum()),
                    ambiguous_x_intervals=[[x + a, x + b] for a, b in intervals(bad)],
                    guarded_x_intervals=[[x + a, x + b] for a, b in intervals(guard)],
                    unambiguous_sections=[[x + a, x + b] for a, b in kept_ranges],
                    retained_x_columns=sum(b - a for a, b in kept_ranges),
                    total_x_columns=x1 - x,
                    topology="unknown",
                )
            )
    unstable_rows = []
    for f in unstable:
        values = threshold_rows[f["id"]]
        minimum = min(v["raw_peak_fraction"] for v in values.values())
        cause = (
            "length_filter_or_sample_representation"
            if minimum >= 0.9
            else "raw_photometric_support_unstable"
        )
        unstable_rows.append(
            dict(id=f["id"], cause=cause, measurements=values, original_hold_preserved=True)
        )
    # Include old-ID overlaps hidden by the higher-priority branch-risk category.
    references = {}
    for source in read(base / "spec.json")["previous_traces"]:
        for track in inputs.document(source)["tracks"]:
            references.setdefault(track["id"], []).append(track)
    overlap = []
    for f in inventory["fragments"]:
        row = rows[f["id"]]
        if (
            row["category"] not in ["partial_known_path_hold", "branch_topology_hold"]
            or not row["old_path_matches"]
        ):
            continue
        matches = []
        for m in row["old_path_matches"]:
            covered = support(f["points"], references[m["id"]], tolerance=4)
            matches.append(
                dict(
                    old_id=m["id"],
                    matched_sample_intervals=intervals(covered),
                    unmatched_sample_intervals=intervals(~covered),
                    fraction=float(covered.mean()),
                    status="reference_only_no_identity_inheritance",
                )
            )
        overlap.append(dict(id=f["id"], source_points=f["points"], matches=matches))
    peripheral = []
    for f in inventory["fragments"]:
        if rows[f["id"]]["category"] == "peripheral_edge_hold":
            x, y, x1, y1 = f["bounds"]
            peripheral.append(
                dict(
                    id=f["id"],
                    bounds=f["bounds"],
                    touches_photo_boundary=(
                        x == 0 or y == 0 or x1 == gray.shape[1] or y1 == gray.shape[0]
                    ),
                    classification="spatial_risk_not_material_identity",
                )
            )
    output.mkdir(parents=True)
    for name, value in [
        ("branch-localization", branch_rows),
        ("unambiguous-source-sections", sections),
        ("threshold-causes", unstable_rows),
        ("old-id-overlap-intervals", overlap),
        ("peripheral-boundaries", peripheral),
    ]:
        put(output / (name + ".json"), value)
    summary = dict(
        branch_parents=len(branch_rows),
        source_sections=len(sections),
        retained_columns=sum(x["retained_x_columns"] for x in branch_rows),
        original_branch_columns=sum(x["total_x_columns"] for x in branch_rows),
        threshold_causes=dict(Counter(x["cause"] for x in unstable_rows)),
        old_id_overlap_records=len(overlap),
        peripheral_records=len(peripheral),
        photo_clipped=sum(x["touches_photo_boundary"] for x in peripheral),
        seconds=time.perf_counter() - start,
        no_topology_or_geometry_mutation=True,
        sources=dict(
            inventory=ref(root, base / "inventory.json"),
            triage=ref(root, root / "runs/m3-triage-20261111/verified/triage.json"),
            photo=inventory["photo"],
            algorithm=ref(root, Path(__file__)),
        ),
    )
    put(output / "summary.json", summary)
    print(summary)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    run(Path.cwd(), args.output)
