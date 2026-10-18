"""Extend retained geometry to a whole-frame regular AA/CT candidate scene.

Run: python -m silicon_eye.regular_scene --root . --spec SPEC --output NEW_DIR
Uses existing OpenCV/Shapely. Frozen inputs/raw images are immutable; no net is extracted.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
import os
import tempfile
from collections import Counter
from itertools import product
from pathlib import Path

import cv2
import numpy as np
import shapely
from shapely.geometry import Polygon, box
from shapely.strtree import STRtree

from .geometry_reconstruction import (
    corners,
    ct_positive,
    digest,
    object_polygon,
    object_rings,
    project,
)
from .scene_geometry import load_locked, paint_objects


def rect_copy(obj, bounds):
    new = copy.deepcopy(obj)
    new.update(
        primitive="rectangle",
        outer_xyxy=list(map(float, bounds)),
        hole_xyxy=None,
        geometry_revision="shared_parameter_candidate",
        previous_geometry_bounds=obj["outer_xyxy"],
    )
    new.pop("outer_xy", None)
    new.pop("holes_xy", None)
    return new


def align_boundary_neighbors(objects, seed, base):
    """Resolve old-frame fragments at retained array boundaries without moving anchors."""
    result = copy.deepcopy(objects)
    locked = {o["id"] for o in seed["objects"] if o["layer"] == "AA"}
    arrays = {g["id"]: g for g in seed["groups"] if g["kind"] == "rectangle_array"}
    notes = []
    mapping = {}
    deferred = []
    for i, obj in enumerate(result):
        if obj["id"] in locked:
            continue
        hits = [
            a
            for a in result
            if a["id"] in locked and object_polygon(obj).intersects(object_polygon(a))
        ]
        if not hits:
            continue
        owners = {a.get("template_id") for a in hits}
        proposal = None
        if len(owners) == 1 and next(iter(owners)) in arrays:
            group = arrays[next(iter(owners))]
            transform = np.linalg.inv(group["layout_to_native"]) @ np.linalg.inv(
                base[group["source_frame"] + "_native_to_layout"]
            )
            center = project([object_polygon(obj).centroid.coords[0]], transform)[0]
            origin = np.array(group["origin_xy"])
            wh = np.array(group["size_wh"])
            col, row = np.rint((center - origin - wh / 2) / group["pitch_xy"]).astype(int)
            outside = not (0 <= col < group["cols"] and 0 <= row < group["rows"])
            if outside and -1 <= col <= group["cols"] and -1 <= row <= group["rows"]:
                lo = origin + np.array([col, row]) * group["pitch_xy"]
                proposal = rect_copy(obj, [*lo, *(lo + wh)])
                proposal.update(
                    geometry_revision="array_boundary_extension_candidate",
                    extension_row=int(row),
                    extension_col=int(col),
                    support="neighbor_observation_not_complete_source_or_human_truth",
                )
                safe = all(
                    not object_polygon(proposal).intersects(object_polygon(a))
                    for a in result
                    if a["id"] != obj["id"]
                )
                if safe:
                    result[i] = proposal
                    mapping[obj["id"]] = group["id"]
                    notes.append(
                        dict(
                            id=obj["id"],
                            template_id=group["id"],
                            row=int(row),
                            col=int(col),
                            state="neighbor_extension_candidate",
                        )
                    )
                    continue
        deferred.append(
            dict(
                object=copy.deepcopy(obj),
                reason="retained_boundary_frame_conflict",
                references=[a["id"] for a in hits],
            )
        )
    rejected = {d["object"]["id"] for d in deferred}
    return [o for o in result if o["id"] not in rejected], mapping, notes, deferred


def rectangle_objects(objects, excluded):
    selected = []
    for o in objects:
        p = object_polygon(o)
        if o["id"] in excluded or o.get("human_review", {}).get("state") == "confirmed":
            continue
        if len(p.interiors) == 0 and abs(p.area - box(*p.bounds).area) < 0.01:
            selected.append(o)
    return selected


def regularize_aa(objects, retained_ids, settings):
    """Propose shared rows; collision-check the complete group before changing any member."""
    result = copy.deepcopy(objects)
    lookup = {o["id"]: i for i, o in enumerate(result)}
    available = rectangle_objects(result, retained_ids)
    groups = []
    used = set()
    for initial in sorted(available, key=lambda o: o["id"]):
        if initial["id"] in used:
            continue
        a = np.array(initial["outer_xyxy"])
        size = a[2:] - a[:2]
        center = (a[:2] + a[2:]) / 2
        candidates = []
        for o in available:
            if o["id"] in used:
                continue
            b = np.array(o["outer_xyxy"])
            s = b[2:] - b[:2]
            c = (b[:2] + b[2:]) / 2
            if (
                np.abs(s - size) <= np.maximum(3, size * settings["size_relative_tolerance"])
            ).all() and abs(c[1] - center[1]) <= settings["baseline_tolerance"]:
                candidates.append(o)
        if len(candidates) < settings["min_group_size"]:
            continue
        candidates.sort(key=lambda o: (o["outer_xyxy"][0] + o["outer_xyxy"][2]) / 2)
        # A large gap divides unrelated rows rather than inventing an array across it.
        centers = np.array([np.array(o["outer_xyxy"]).reshape(2, 2).mean(0) for o in candidates])
        gaps = np.diff(centers[:, 0])
        pitch = float(np.median(gaps))
        if pitch <= 0 or np.max(abs(gaps - pitch)) > max(
            4, pitch * settings["pitch_relative_tolerance"]
        ):
            continue
        sizes = np.array(
            [np.diff(np.array(o["outer_xyxy"]).reshape(2, 2), axis=0)[0] for o in candidates]
        )
        wh = np.median(sizes, axis=0)
        y = float(np.median(centers[:, 1]))
        indices = np.arange(len(candidates))
        x0, dx = np.linalg.lstsq(np.c_[np.ones(len(indices)), indices], centers[:, 0], rcond=None)[
            0
        ]
        proposed = []
        for i, o in enumerate(candidates):
            c = np.array([x0 + i * dx, y])
            proposed.append(rect_copy(o, [*(c - wh / 2), *(c + wh / 2)]))
        ids = {o["id"] for o in candidates}
        shift = max(
            np.max(abs(np.array(a["outer_xyxy"]) - b["outer_xyxy"]))
            for a, b in zip(proposed, candidates, strict=True)
        )
        safe = shift <= settings["max_shift"] and all(
            not object_polygon(p).intersects(object_polygon(q))
            for p in proposed
            for q in result
            if q["id"] not in ids
        )
        safe &= all(
            not object_polygon(p).intersects(object_polygon(q))
            for i, p in enumerate(proposed)
            for q in proposed[:i]
        )
        group = dict(
            id="AA-ROW-" + min(ids),
            member_ids=sorted(ids),
            shared_size_wh=wh.tolist(),
            pitch=float(dx),
            baseline=y,
            max_change=float(shift),
            state="applied_candidate" if safe else "deferred_collision_or_shift",
            scope="whole_scene_group_not_crop",
        )
        groups.append(group)
        used.update(ids)
        if safe:
            for o in proposed:
                result[lookup[o["id"]]] = o
    # Unreviewed rings can share a wall width; preserve all reviewed/retained geometry.
    for i, o in enumerate(result):
        if (
            o["id"] in retained_ids
            or o.get("human_review", {}).get("state") == "confirmed"
            or not o.get("hole_xyxy")
        ):
            continue
        b = np.array(o["outer_xyxy"])
        h = np.array(o["hole_xyxy"])
        w = float(np.median([h[0] - b[0], h[1] - b[1], b[2] - h[2], b[3] - h[3]]))
        proposal = copy.deepcopy(o)
        proposal["hole_xyxy"] = [b[0] + w, b[1] + w, b[2] - w, b[3] - w]
        if not object_polygon(proposal).is_valid:
            continue
        if all(
            not object_polygon(proposal).intersects(object_polygon(q))
            for q in result
            if q["id"] != o["id"]
        ):
            result[i] = proposal
            groups.append(
                dict(
                    id="AA-RING-" + o["id"],
                    member_ids=[o["id"]],
                    shared_width=w,
                    state="applied_candidate",
                )
            )
    return result, groups


def axis_levels(values, settings):
    """Shared coordinate levels; equal pitch is fitted only when its observed indices support it."""
    values = np.asarray(values, float)
    clusters = []
    for i in np.argsort(values):
        if not clusters or values[i] - np.mean(values[clusters[-1]]) > settings["axis_cluster"]:
            clusters.append([int(i)])
        else:
            clusters[-1].append(int(i))
    levels = np.array([np.median(values[c]) for c in clusters])
    target = levels.copy()
    pitch = None
    if len(levels) >= 3:
        diffs = np.diff(levels)
        possible = diffs[diffs >= settings["min_pitch"]]
        if len(possible) >= 2:
            p = float(np.median(possible))
            ix = np.rint((levels - levels[0]) / p)
            if len(np.unique(ix)) == len(ix):
                origin, step = np.linalg.lstsq(np.c_[np.ones(len(ix)), ix], levels, rcond=None)[0]
                fit = origin + step * ix
                if (
                    step >= settings["min_pitch"]
                    and np.max(abs(fit - levels)) <= settings["max_axis_shift"]
                ):
                    target = fit
                    pitch = float(step)
    assignment = np.empty(len(values), int)
    for j, c in enumerate(clusters):
        assignment[c] = j
    if pitch is None and len(values) >= 8 and len(levels) >= 3:
        # A common row can be split by local peak drift. Fit a periodic phase rather than
        # treating each small brightness displacement as a new row or column.
        shifted = values - values.min()
        candidates = list(
            np.arange(
                settings["min_pitch"],
                settings.get("dense_pitch_max", 24.0) + 0.01,
                settings.get("dense_pitch_step", 0.15),
            )
        )
        differences = np.diff(levels)
        large = differences[differences >= settings["min_pitch"]]
        if len(large):
            candidates.extend(np.quantile(large, [0.25, 0.5, 0.75]))
        best = None
        for step in candidates:
            phase = np.mean(np.exp(2j * np.pi * shifted / step))
            coherence = abs(phase)
            if coherence < settings.get("periodic_min_coherence", 0.6):
                continue
            origin = np.angle(phase) * step / (2 * np.pi)
            indices = np.rint((shifted - origin) / step)
            offset, fitted = np.linalg.lstsq(
                np.c_[np.ones(len(indices)), indices], shifted, rcond=None
            )[0]
            predicted = offset + fitted * indices
            residual = abs(predicted - shifted)
            if (
                fitted < settings["min_pitch"]
                or np.max(residual) > settings["max_axis_shift"]
                or np.median(residual) > settings.get("periodic_max_median_shift", 2.5)
            ):
                continue
            if best is None or coherence > best[0]:
                best = (coherence, indices, offset, fitted)
        if best is not None:
            _, indices, offset, pitch = best
            unique, assignment = np.unique(indices, return_inverse=True)
            target = values.min() + offset + pitch * unique
    return target, assignment, pitch


def centered_observations(peaks, photo, radius):
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY).astype(float)
    records = []
    for i, o in enumerate(peaks):
        x, y = np.rint(o["source_native_center_xy"]).astype(int)
        x0, y0 = max(0, x - radius), max(0, y - radius)
        patch = gray[
            y0 : min(gray.shape[0], y + radius + 1), x0 : min(gray.shape[1], x + radius + 1)
        ]
        yy, xx = np.indices(patch.shape)
        weight = np.maximum(patch - np.percentile(patch, 25), 0)
        point = (
            np.array(
                [
                    float((xx * weight).sum() / weight.sum() + x0),
                    float((yy * weight).sum() / weight.sum() + y0),
                ]
            )
            if weight.sum() > 0
            else np.array([x, y], float)
        )
        records.append(
            dict(
                id=f"CT-F{i:05}",
                original_peak_xy=o["source_native_center_xy"],
                native_center_xy=point.tolist(),
                center_shift=float(np.linalg.norm(point - o["source_native_center_xy"])),
                definition="local_weighted_brightness_center_not_independent_truth",
            )
        )
    return records


def projection_matrices(base, seed):
    matrices = {"global": {f: np.linalg.inv(base[f + "_native_to_layout"]) for f in ["aa", "poly"]}}
    for g in seed["groups"]:
        native = g["source_frame"]
        h = np.array(g["layout_to_native"])
        matrices[g["id"]] = {
            f: np.linalg.inv(base[f + "_native_to_layout"])
            @ np.array(base[native + "_native_to_layout"])
            @ h
            for f in ["aa", "poly"]
        }
    return matrices


def source_assignments(observations, aa, mapping, matrices):
    polygons = []
    for o in aa:
        h = matrices[mapping.get(o["id"], "global")]["poly"]
        outer, holes = object_rings(o)
        polygons.append(Polygon(project(outer, h), [project(v, h) for v in holes]))
    points = shapely.points(np.array([o["native_center_xy"] for o in observations]))
    pairs = STRtree(polygons).query(points, predicate="within")
    matches = {}
    for pi, ai in pairs.T:
        matches.setdefault(int(pi), []).append(int(ai))
    return matches


def reserve(bounds, occupied, settings):
    if len(occupied):
        a = np.asarray(occupied)
        b = np.asarray(bounds)
        overlap = (a[:, 0] <= b[2]) & (a[:, 2] >= b[0]) & (a[:, 1] <= b[3]) & (a[:, 3] >= b[1])
        if np.any(overlap):
            return False
        centers = (a[:, :2] + a[:, 2:]) / 2
        if (
            np.min(np.linalg.norm(centers - (b[:2] + b[2:]) / 2, axis=1))
            < settings["duplicate_radius"]
        ):
            return False
    occupied.append(list(map(float, bounds)))
    return True


def contact_candidates(observations, aa, retained, mapping, matrices, settings):
    matches = source_assignments(observations, aa, mapping, matrices)
    occupied = [o["outer_xyxy"] for o in retained]
    locked_sources = {s for o in retained for s in o.get("source_observation_ids", [])}
    assigned = {}
    pending = []
    dispositions = []
    groups = []
    for i, o in enumerate(observations):
        if o["id"] in locked_sources:
            dispositions.append(dict(source_id=o["id"], state="retained_geometry_source"))
            continue
        owners = matches.get(i, [])
        if len(owners) != 1:
            pending.append(
                dict(
                    o,
                    reason="overlapping_source_projections"
                    if owners
                    else "AA_assignment_unknown_not_proof_of_poly",
                    layout_center_xy=project(
                        [o["native_center_xy"]], np.linalg.inv(matrices["global"]["poly"])
                    )[0].tolist(),
                )
            )
            dispositions.append(dict(source_id=o["id"], state="material_assignment_unknown"))
            continue
        index = owners[0]
        owner = aa[index]
        h = matrices[mapping.get(owner["id"], "global")]["poly"]
        point = project([o["native_center_xy"]], np.linalg.inv(h))[0]
        bounds = [*(point - 4), *(point + 4)]
        if not reserve(bounds, occupied, settings):
            dispositions.append(dict(source_id=o["id"], state="near_retained_or_prior_observation"))
            continue
        # Release provisional footprint; reserve final regularized candidates later.
        occupied.pop()
        assigned.setdefault(index, []).append(dict(o, layout_center_xy=point.tolist()))
    created = []
    for index, records in assigned.items():
        owner = aa[index]
        material = object_polygon(owner)
        points = np.array([o["layout_center_xy"] for o in records])
        xs, xc, xpitch = axis_levels(points[:, 0], settings)
        ys, yc, ypitch = axis_levels(points[:, 1], settings)
        slots = {}
        for j, o in enumerate(records):
            slots.setdefault((int(xc[j]), int(yc[j])), []).append(o)
        capacity = len(xs) * len(ys)
        repeat = (
            len(slots) >= 4
            and (xpitch is not None or ypitch is not None)
            and capacity <= settings["max_slots_per_AA"]
        )
        repeat &= len(slots) / max(1, capacity) >= settings["min_grid_support"]
        # A lattice hypothesis doesn't by itself identify a material contact or a legal channel.
        missing_budget = int(len(slots) * settings["max_inferred_fraction"])
        inferred = 0
        emitted = []
        slot_indices = product(range(len(xs)), range(len(ys))) if repeat else iter(slots)
        for xi, yi in slot_indices:
            x, y = xs[xi], ys[yi]
            source = slots.get((xi, yi), [])
            if not source and (not repeat or inferred >= missing_budget):
                continue
            bounds = [x - 4, y - 4, x + 4, y + 4]
            p = box(*bounds)
            landed = material.buffer(-settings["AA_margin"]).contains(p)
            if not source and not landed:
                continue
            shift = (
                max(np.linalg.norm(np.array(v["layout_center_xy"]) - [x, y]) for v in source)
                if source
                else 0
            )
            if source and shift > settings["max_axis_shift"]:
                for v in source:
                    pending.append(dict(v, reason="template_shift_exceeds_working_limit"))
                    dispositions.append(dict(source_id=v["id"], state="template_position_unknown"))
                continue
            if not reserve(bounds, occupied, settings):
                for v in source:
                    dispositions.append(
                        dict(source_id=v["id"], state="geometry_proximity_suppressed")
                    )
                continue
            if not source:
                state = "inferred_CT_geometry_candidate"
                inferred += 1
            elif landed and repeat and len(source) == 1:
                state = "observed_CT_template_candidate"
            else:
                state = "unknown_CT_landing_or_template"
            identifier = f"CT-R-{owner['id']}-{xi:03}-{yi:03}"
            obj = dict(
                id=identifier,
                layer="CT",
                primitive="square",
                outer_xyxy=list(map(float, bounds)),
                hole_xyxy=None,
                status=state,
                aa_object_id=owner["id"],
                template_id="CT-G-" + owner["id"],
                source_observation_ids=[v["id"] for v in source],
                row=yi,
                col=xi,
                center_definition="local_weighted_brightness_center_candidate",
                electrical_connection="unknown",
                channel_and_upper_metal_check="unknown",
                dimension_status="assumed_8_relative_units_not_process_dimension",
            )
            created.append(obj)
            mapping[identifier] = mapping.get(owner["id"], "global")
            emitted.append(identifier)
            for v in source:
                dispositions.append(dict(source_id=v["id"], state=state, object_id=identifier))
        groups.append(
            dict(
                id="CT-G-" + owner["id"],
                AA_id=owner["id"],
                member_ids=emitted,
                x_levels=xs.tolist(),
                y_levels=ys.tolist(),
                x_pitch=xpitch,
                y_pitch=ypitch,
                repeat_supported=bool(repeat),
                source_observations=len(records),
                inferred_slots=inferred,
                status="candidate_not_full_contact_legality",
            )
        )
    return created, pending, dispositions, groups


def display_role(o):
    if o["layer"] == "AA":
        return "AA"
    state = o.get("status")
    if ct_positive(o) or state in {"photo_peak_support", "observed_CT_template_candidate"}:
        return "CT"
    if state in {"inferred_candidate", "inferred_CT_geometry_candidate"}:
        return "inferred"
    return "unknown" if state == "unknown_material_landing" else "pending"


def scene_svg(objects, size, frame, mapping, matrices, labels=False):
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" '
        f'height="{size[1]}" viewBox="0 0 {size[0]} {size[1]}">'
    ]
    for o in objects:
        outer, holes = object_rings(o)
        h = np.eye(3) if frame == "layout" else matrices[mapping.get(o["id"], "global")][frame]
        outer = project(outer, h)
        holes = [project(v, h) for v in holes]
        if labels:
            chunks.append(
                f'<text x="{outer[0, 0]:.2f}" y="{outer[0, 1] - 5:.2f}" '
                f'font-size="16" fill="#fff2b8">{html.escape(o["id"])}</text>'
            )
            continue
        role = display_role(o)
        color = {
            "AA": "#50cbd5",
            "CT": "#d3adff",
            "inferred": "#ffbd54",
            "pending": "#f6dc80",
            "unknown": "#ff7770",
        }[role]
        path = "M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in outer) + " Z"
        for v in holes:
            path += " M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in v) + " Z"
        chunks.append(
            f'<path d="{path}" fill="{color if role in {"AA", "CT"} else "none"}" '
            f'fill-opacity="0.58" stroke="{color}" stroke-width="1.2" fill-rule="evenodd"/>'
        )
    return "\n".join([*chunks, "</svg>"])


def run(root, spec_path, output):
    root, spec_path, output = (
        Path(root).resolve(),
        Path(spec_path).resolve(),
        Path(output).resolve(),
    )
    if output.exists() or output.is_relative_to(root / "data"):
        raise ValueError("New output outside data/ required")
    spec = json.loads(spec_path.read_text())
    data = {k: load_locked(root, v) for k, v in spec["inputs"].items()}
    base, seed, old = data["base_scene"], data["retained_geometry"], data["retained_parent"]
    for s in base["sources"].values():
        if digest(root / s["path"]) != s["sha256"]:
            raise ValueError("Changed source photograph")
    retained_ids = {o["id"] for o in seed["objects"]}
    replaced = {
        o["previous_object_id"]
        for o in seed["objects"]
        if o.get("previous_object_id") and o["layer"] == "AA"
    }
    aa = [copy.deepcopy(o) for o in seed["objects"] if o["layer"] == "AA"] + [
        copy.deepcopy(o) for o in base["objects"] if o["layer"] == "AA" and o["id"] not in replaced
    ]
    aa, boundary_mapping, boundary_extensions, boundary_conflicts = align_boundary_neighbors(
        aa, seed, base
    )
    aa, aa_groups = regularize_aa(aa, retained_ids | set(boundary_mapping), spec["AA"])
    if any(
        object_polygon(a).intersects(object_polygon(b)) for i, a in enumerate(aa) for b in aa[:i]
    ):
        raise ValueError("AA collision must remain a deferred conflict, not merged material")
    retained_ct = [copy.deepcopy(o) for o in seed["objects"] if o["layer"] == "CT"] + [
        copy.deepcopy(o) for o in old["objects"] if o["layer"] == "CT"
    ]
    matrices = projection_matrices(base, seed)
    mapping = dict(boundary_mapping)
    for o in seed["objects"]:
        mapping[o["id"]] = o["template_id"].removesuffix("-AA")
    # T01's unchanged surrounding AA uses the same local mapping as its retained contacts.
    for g in seed["groups"]:
        if g.get("AA_material") and not g.get("AA_materials"):
            mapping[g["AA_material"]["id"]] = g["id"]
    photo = cv2.imread(str(root / base["sources"]["poly"]["path"]))
    observations = centered_observations(
        data["source_peaks"], photo, spec["CT"]["weighted_center_radius"]
    )
    newct, pending, dispositions, ct_groups = contact_candidates(
        observations, aa, retained_ct, mapping, matrices, spec["CT"]
    )
    # Pending non-AA observations are displayed separately; no AA or poly identity is invented.
    pending_objects = []
    occupied = [o["outer_xyxy"] for o in retained_ct + newct]
    for i, o in enumerate(pending):
        p = (
            np.array(o["layout_center_xy"])
            if "layout_center_xy" in o
            else project([o["native_center_xy"]], base["poly_native_to_layout"])[0]
        )
        bounds = [*(p - 4), *(p + 4)]
        if not reserve(bounds, occupied, spec["CT"]):
            continue
        pending_objects.append(
            dict(
                id=f"CT-U-{i:05}",
                layer="CT",
                primitive="square",
                outer_xyxy=list(map(float, bounds)),
                hole_xyxy=None,
                status="unknown_material_landing",
                source_observation_ids=[o["id"]],
                electrical_connection="unknown",
                uncertainty_reason=o["reason"],
            )
        )
    objects = aa + retained_ct + newct + pending_objects
    lookup = {o["id"]: o for o in objects}
    if len(lookup) != len(objects):
        raise ValueError("Duplicate object IDs")
    if not all(lookup[o["id"]] == o for o in seed["objects"]):
        raise ValueError("Retained geometry or state changed")
    unresolved = [v for v in data["deferred_AA"] if v["reason"] != "covered_by_existing_geometry"]
    report = dict(
        AA_records=len(aa),
        retained_objects_unchanged=len(seed["objects"]),
        retained_CT_records=len(retained_ct),
        new_CT_records=len(newct),
        unclassified_CT_geometry_records=len(pending_objects),
        CT_source_observations=len(observations),
        CT_disposition_counts=dict(Counter(o["state"] for o in dispositions)),
        AA_row_and_ring_groups=len(aa_groups),
        AA_groups_applied=sum(g["state"] == "applied_candidate" for g in aa_groups),
        AA_groups_deferred=sum(g["state"] != "applied_candidate" for g in aa_groups),
        AA_boundary_extensions=len(boundary_extensions),
        AA_boundary_conflicts=len(boundary_conflicts),
        CT_groups=len(ct_groups),
        AA_unresolved_observations=len(unresolved),
        display_counts=dict(Counter(display_role(o) for o in objects)),
        full_photo_scope_processed=True,
        physical_full_frame_completeness=False,
        full_contact_legality="unknown_missing_channel_upper_material_and_process",
        photo_peak_residual_scope="diagnostic_only_not_automatic_geometry_veto",
        global_deformation_field="not_stitched_local_group_hypotheses",
        new_human_review="pending",
    )
    model = dict(
        schema_version=1,
        status="whole_frame_regular_geometry_candidates",
        canvas_wh=base["canvas_wh"],
        sources=base["sources"],
        objects=objects,
        AA_groups=aa_groups,
        AA_boundary_extensions=boundary_extensions,
        AA_boundary_conflicts=boundary_conflicts,
        CT_groups=ct_groups,
        object_projection_groups=mapping,
        projection_matrices={k: {f: h.tolist() for f, h in v.items()} for k, v in matrices.items()},
        retained_geometry=spec["inputs"]["retained_geometry"],
        inputs=spec["inputs"],
        code_sha256=digest(__file__),
        spec_sha256=digest(spec_path),
        units="relative_layout_units_not_um",
        electrical_net_extraction=False,
        physical_fullframe_acceptance=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".regular-scene-", dir=output.parent) as temp:
        stage = Path(temp)
        for name, value in [
            ("model.json", model),
            ("report.json", report),
            ("spec.json", spec),
            ("source-observations.json", observations),
            ("source-dispositions.json", dispositions),
            ("unclassified-CT-observations.json", pending),
            ("unresolved-AA.json", unresolved),
            ("boundary-AA-conflicts.json", boundary_conflicts),
        ]:
            (stage / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        sizes = {
            "layout": base["canvas_wh"],
            **{f: [s["width"], s["height"]] for f, s in base["sources"].items()},
        }
        for frame in sizes:
            for role in ["AA", "CT", "inferred", "pending", "unknown"]:
                (stage / f"{frame}-{role}.svg").write_text(
                    scene_svg(
                        [o for o in objects if display_role(o) == role],
                        sizes[frame],
                        frame,
                        mapping,
                        matrices,
                    )
                )
            (stage / f"{frame}-labels.svg").write_text(
                scene_svg(aa, sizes[frame], frame, mapping, matrices, labels=True)
            )
            (stage / f"{frame}-retained.svg").write_text(
                scene_svg(seed["objects"], sizes[frame], frame, mapping, matrices)
            )
            (stage / f"{frame}-before.svg").write_text(
                scene_svg(base["objects"], sizes[frame], frame, {}, matrices)
            )
            (stage / f"{frame}-conflicts.svg").write_text(
                scene_svg(
                    [d["object"] for d in boundary_conflicts], sizes[frame], frame, {}, matrices
                )
                .replace("#50cbd5", "#ff7770")
                .replace('fill-opacity="0.58"', 'fill-opacity="0.1"')
            )
        size = base["canvas_wh"]
        image = np.full((size[1], size[0], 3), (32, 23, 15), np.uint8)
        for role, color in [
            ("AA", (213, 203, 80)),
            ("CT", (255, 173, 211)),
            ("inferred", (60, 180, 255)),
            ("pending", (128, 220, 246)),
        ]:
            mask = paint_objects([o for o in objects if display_role(o) == role], size)
            image[mask > 0] = color
            if not cv2.imwrite(str(stage / f"{role}-layout.png"), mask):
                raise OSError("Image write failed")
        cv2.imwrite(
            str(stage / "CT-all-candidates-layout.png"),
            paint_objects(
                [o for o in objects if o["layer"] == "CT" and display_role(o) != "unknown"], size
            ),
        )
        cv2.imwrite(
            str(stage / "overview.png"), cv2.resize(image, (1600, round(size[1] * 1600 / size[0])))
        )
        windows = [
            dict(id="full", label="全幅规则几何", views={f: [0, 0, *s] for f, s in sizes.items()})
        ]
        coverage = []
        for row in range(3):
            for col in range(4):
                identifier = f"F{row * 4 + col + 1:02}"
                bounds = [
                    1428 * col,
                    185 + 4099 * row / 3,
                    1428 * (col + 1),
                    185 + 4099 * (row + 1) / 3,
                ]
                views = {}
                for f in sizes:
                    h = (
                        base["aa_native_to_layout"]
                        if f == "layout"
                        else np.eye(3)
                        if f == "aa"
                        else np.linalg.inv(base["poly_native_to_layout"])
                        @ np.array(base["aa_native_to_layout"])
                    )
                    pts = project(corners(bounds), h)
                    lo, hi = pts.min(0), pts.max(0)
                    views[f] = [*lo, *(hi - lo)]
                windows.append(
                    dict(
                        id=identifier, label=f"{identifier} 第{row + 1}行第{col + 1}列", views=views
                    )
                )
                coverage.append(
                    dict(
                        id=identifier,
                        AA_native_bbox=bounds,
                        display_window_only=True,
                        material_completeness="not_accepted",
                    )
                )
        for g in seed["groups"]:
            views = {}
            for f in sizes:
                if f == "layout":
                    selected = [
                        o
                        for o in seed["objects"]
                        if o.get("template_id", "").removesuffix("-AA") == g["id"]
                    ]
                    bounds = shapely.union_all([object_polygon(o) for o in selected]).bounds
                    lo = np.array(bounds[:2]) - 20
                    hi = np.array(bounds[2:]) + 20
                else:
                    h = np.linalg.inv(base[f + "_native_to_layout"]) @ np.array(
                        base[g["source_frame"] + "_native_to_layout"]
                    )
                    pts = project(corners(g["native_window"]), h)
                    lo, hi = pts.min(0), pts.max(0)
                views[f] = [*lo, *(hi - lo)]
            windows.append(dict(id=g["id"], label=g["id"] + " 已保留样稿", views=views))
        (stage / "coverage.json").write_text(
            json.dumps(coverage, ensure_ascii=False, indent=2) + "\n"
        )
        paths = {f: os.path.relpath(root / s["path"], output) for f, s in base["sources"].items()}
        (stage / "data.js").write_text(
            "const DATA="
            + json.dumps(
                dict(sizes=sizes, paths=paths, windows=windows, report=report), ensure_ascii=False
            )
            + ";"
        )
        (stage / "index.html").write_text(PAGE)
        for s in base["sources"].values():
            if digest(root / s["path"]) != s["sha256"]:
                raise ValueError("Source changed during generation")
        (stage / "manifest.json").write_text(
            json.dumps({p.name: digest(p) for p in stage.iterdir()}, indent=2) + "\n"
        )
        stage.rename(output)
    return report


PAGE = """<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<title>全幅规则 AA＋CT</title>
<style>body{font:17px/1.6 sans-serif;
background:#14212b;
color:#e2edf6;
margin:20px}a{color:#70dfff}
select,label{font:inherit;
margin:8px}svg{width:100%;
height:72vh;
background:#101923}table{border-collapse:collapse}td{padding:5px;
border:1px solid #647585}</style>
<h1>保留几何，扩展全幅 AA＋CT</h1>
<p>青色 AA、紫色来源支持的 CT 候选、橙框推断孔、浅黄框 AA 范围待核孔、红框材料归属未知。
195 个保留对象不动。照片峰值偏差只作诊断，不据此自动否决结构；完整孔合法性仍待定。</p>
<select id="frame">
<option value="layout">规则版图</option>
<option value="aa">AA 原图回投</option>
<option value="poly">poly / CT 原图回投</option>
</select>
<select id="window">
</select>
<label>
<input id="before" type="checkbox">对照旧全幅候选</label>
<br>
<label>
<input id="AA" type="checkbox" checked>AA</label>
<label>
<input id="CT" type="checkbox" checked>CT 候选</label>
<label>
<input id="inferred" type="checkbox" checked>推断 CT</label>
<label>
<input id="pending" type="checkbox" checked>AA 范围待核 CT</label>
<label>
<input id="unknown" type="checkbox">材料归属未知亮点</label>
<label>
<input id="retained" type="checkbox">突出保留几何</label>
<label>
<input id="labels" type="checkbox">AA 编号</label>
<label>
<input id="conflicts" type="checkbox" checked>AA 边界冲突</label>
<label>透明度<input id="opacity" type="range" min="0" max="1" step="0.05" value="0.75">
</label>
<svg id="view">
<image id="photo"/>
<image id="AAimg"/>
<image id="CTimg"/>
<image id="inferredimg"/>
<image id="pendingimg"/>
<image id="unknownimg"/>
<image id="retainedimg"/>
<image id="labelsimg"/>
<image id="conflictsimg"/>
<image id="beforeimg"/>
</svg>
<p id="summary">
</p>
<p>F01–F12 是显示窗口，不裁割材料或网络。局部照片变换尚未拼成全幅一致变形场；
回投用于复核，不能直接并网。
空白/未分类不等于无材料；照片外与遮挡处未知。</p>
<p>
<a href="model.json">几何与来源</a> ·
<a href="report.json">统计及限制</a> ·
<a href="unresolved-AA.json">待解决 AA 观察</a> ·
<a href="unclassified-CT-observations.json">待分类亮点</a> ·
<a href="AA-layout.png">AA 像素图</a> ·
<a href="CT-all-candidates-layout.png">全部 AA 关联 CT 候选像素图</a> ·
<a href="CT-layout.png">规律支持 CT 像素图</a>
</p>
<script src="data.js">
</script>
<script>
const el=id=>document.getElementById(id);
const roles=['AA','CT','inferred','pending','unknown','retained','labels','conflicts','before'];

for(const w of DATA.windows){const o=document.createElement('option');
o.value=w.id;
o.textContent=w.label;
el('window').append(o);
}
function update(){const f=el('frame').value,w=DATA.windows.find(w=>w.id===el('window').value);

el('view').setAttribute('viewBox',w.views[f].join(' '));

for(const id of ['photo',...roles.map(r=>r+'img')]){el(id).setAttribute('width',DATA.sizes[f][0]);
el(id).setAttribute('height',DATA.sizes[f][1]);
}
el('photo').setAttribute('href',DATA.paths[f]||'');

for(const r of roles){const img=el(r+'img');
img.setAttribute('href',f+'-'+r+'.svg');

img.style.opacity=el('opacity').value;
img.style.display=(r==='before'?el('before').checked:!el('before').checked&&el(r).checked)?'':'none';
}}
const r=DATA.report;
el('summary').textContent=`全幅 AA ${r.AA_records} 条；`
+`CT 显示记录：${r.display_counts.CT||0} 候选、`
+`${r.display_counts.inferred||0} 推断、${r.display_counts.pending||0} AA 范围待核；`
+`${r.display_counts.unknown||0} 材料归属未知亮点（可选显示）。`
+`另有 ${r.AA_unresolved_observations} 条 AA 观察未解决，`
+`${r.AA_boundary_conflicts} 处边界冲突。以上不是物理孔/器件总数。`;

document.querySelectorAll('select,input').forEach(x=>x.addEventListener('input',update));
update();

</script>
</html>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    a = parser.parse_args()
    print(json.dumps(run(a.root, a.spec, a.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
