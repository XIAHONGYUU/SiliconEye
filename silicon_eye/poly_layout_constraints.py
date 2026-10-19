"""Propose AA-relative MOS geometry and check generic forward-layout relationships.

No photo calibration or material inference is performed here. Inputs are explicit
row-to-AA hypotheses, gate counts and relative layout budgets, not foundry rules.
"""

from __future__ import annotations

import copy

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union


def fit_gate_rectangle(active, free_region, center_x, width, extension, clearance):
    """Cover assigned active vertically, extend both ends, and avoid the guard."""
    left, top, right, bottom = active.bounds
    if not left < center_x < right or width <= 0 or extension <= 0 or clearance < 0:
        raise ValueError("Invalid gate placement or budgets")
    candidate = box(center_x - width / 2, top - extension, center_x + width / 2, bottom + extension)
    if candidate.intersection(active).area <= 0:
        raise ValueError("Gate misses assigned active")
    if not free_region.buffer(-clearance).covers(candidate):
        raise ValueError("Insufficient free space for required extension/guard clearance")
    return candidate


def reconstruct_relative(derived, aa_records, settings):
    """Build a separate design candidate; do not rewrite AA or photo evidence."""
    result = copy.deepcopy(derived)
    active = {o["id"]: o["polygon"] for o in aa_records if not o["is_guard"]}
    guards = [o["polygon"] for o in aa_records if o["is_guard"]]
    guard = unary_union(guards)
    free_regions = [Polygon(ring) for p in guards for ring in p.interiors]
    by_group = {}
    for obj in result:
        by_group.setdefault(obj["group_id"], []).append(obj)
    for family in settings["families"]:
        groups = [by_group[g] for g in family["groups"]]
        counts = {len(g) for g in groups}
        if len(counts) != 1:
            raise ValueError("Matched MOS rows have different candidate counts")
        count = counts.pop()
        targets = [active[settings["row_AA_targets"][g]] for g in family["groups"]]
        width = family["gate_width_px"]
        lower = max(p.bounds[0] for p in targets) + settings["lateral_margin_px"] + width / 2
        upper = min(p.bounds[2] for p in targets) - settings["lateral_margin_px"] - width / 2
        if upper < lower or (
            count > 1 and (upper - lower) / (count - 1) < width + settings["min_intergate_gap_px"]
        ):
            raise ValueError(
                "Assigned AA cannot fit count/width/spacing without changing assumptions"
            )
        centers = np.linspace(lower, upper, count) if count > 1 else [(lower + upper) / 2]
        for gid in family["groups"]:
            target_id = settings["row_AA_targets"][gid]
            target = active[target_id]
            free = [p for p in free_regions if p.covers(target)]
            if not free:
                raise ValueError("Assigned AA lacks a containing guard-free region")
            free = min(free, key=lambda p: p.area)
            for obj in by_group[gid]:
                before = obj.get("joint_layout_outline")
                candidate = fit_gate_rectangle(
                    target,
                    free,
                    centers[obj["group_index"]],
                    width,
                    settings["min_poly_extension_px"],
                    settings["guard_clearance_px"],
                )
                x, y, r, b = candidate.bounds
                outline = [[x, y], [r, y], [r, b], [x, b]]
                overlap = candidate.intersection(target).area
                guard_overlap = candidate.intersection(guard).area
                top_extension = target.bounds[1] - y
                bottom_extension = b - target.bounds[3]
                other_overlap = [
                    key
                    for key, p in active.items()
                    if key != target_id and candidate.intersection(p).area > 1e-7
                ]
                obj["photo_projected_layout_outline"] = copy.deepcopy(before)
                obj["joint_layout_outline"] = outline
                obj["aa_object_id"] = target_id
                obj["previous_photo_AA_assignment_within_budget"] = obj.get(
                    "aa_body_assignment_within_budget"
                )
                obj["aa_body_assignment_within_budget"] = True
                obj["reconstruction_mode"] = "explicit_AA_relation_not_photo_superposition"
                obj["relation_checks"] = dict(
                    target_AA_overlap_area=float(overlap),
                    top_extension_px=float(top_extension),
                    bottom_extension_px=float(bottom_extension),
                    guard_overlap_area=float(guard_overlap),
                    guard_distance_px=float(candidate.distance(guard)),
                    non_target_AA_intersections=other_overlap,
                    rectangular=True,
                    status="PASS"
                    if overlap > 0 and guard_overlap == 0 and not other_overlap
                    else "FAIL",
                )
                if obj["relation_checks"]["status"] != "PASS":
                    raise ValueError("Forward relation conflict; not adopting repaired geometry")
    polygons = [Polygon(o["joint_layout_outline"]) for o in result]
    for i, p in enumerate(polygons):
        for q in polygons[:i]:
            if p.intersection(q).area > 1e-7:
                raise ValueError("Reconstructed POLY bodies overlap")
    return result


def audit_relative(derived, aa_records, settings):
    """Report structural checks against explicit AA targets; not material accuracy."""
    active = {o["id"]: o["polygon"] for o in aa_records if not o["is_guard"]}
    guard = unary_union([o["polygon"] for o in aa_records if o["is_guard"]])
    failures = {
        "no_target_AA_overlap": [],
        "guard_intrusion": [],
        "insufficient_top_extension": [],
        "insufficient_bottom_extension": [],
        "non_target_AA_overlap": [],
        "non_rectangular": [],
    }
    for obj in derived:
        target_id = settings["row_AA_targets"][obj["group_id"]]
        aa = active[target_id]
        p = Polygon(obj["joint_layout_outline"])
        obj_id = obj["source_poly_id"]
        if p.intersection(aa).area <= 1e-7:
            failures["no_target_AA_overlap"].append(obj_id)
        if p.intersection(guard).area > 1e-7:
            failures["guard_intrusion"].append(obj_id)
        if aa.bounds[1] - p.bounds[1] < settings["min_poly_extension_px"] - 1e-6:
            failures["insufficient_top_extension"].append(obj_id)
        if p.bounds[3] - aa.bounds[3] < settings["min_poly_extension_px"] - 1e-6:
            failures["insufficient_bottom_extension"].append(obj_id)
        if any(
            p.intersection(other).area > 1e-7 for key, other in active.items() if key != target_id
        ):
            failures["non_target_AA_overlap"].append(obj_id)
        if not p.equals(box(*p.bounds)):
            failures["non_rectangular"].append(obj_id)
    return dict(
        objects=len(derived),
        failure_counts={k: len(v) for k, v in failures.items()},
        failure_objects=failures,
        status="PASS" if not any(failures.values()) else "FAIL",
        scope="generic_geometric_relationships_not_foundry_DRC_or_material_truth",
    )
