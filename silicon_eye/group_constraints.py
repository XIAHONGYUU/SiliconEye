"""Fit shared layout templates and audit geometry, photo evidence and injected faults.

Run: python -m silicon_eye.group_constraints --root . --spec SPEC --output NEW_DIR
Requires the existing OpenCV/Shapely environment. No raw or reviewed model is overwritten.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import tempfile
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union

from .geometry_reconstruction import corners, digest, object_polygon, object_rings, project


def rect(identifier, bounds, layer="AA", **fields):
    return dict(
        id=identifier,
        layer=layer,
        primitive="rectangle",
        outer_xyxy=list(bounds),
        hole_xyxy=None,
        **fields,
    )


def array_geometry(group):
    objects = []
    for row in range(group["rows"]):
        for col in range(group["cols"]):
            x, y = np.array(group["origin_xy"]) + np.array([col, row]) * group["pitch_xy"]
            if group.get("motif_cols"):
                cell, local_col = divmod(col, group["motif_cols"])
                x = (
                    group["origin_xy"][0]
                    + cell * group["cell_pitch"]
                    + local_col * group["pitch_xy"][0]
                )
            w, h = group["size_wh"]
            objects.append(
                rect(
                    f"{group['id']}-{row:02}-{col:02}",
                    [x, y, x + w, y + h],
                    "CT" if group["kind"] == "contact_array" else "AA",
                    row=row,
                    col=col,
                    template_id=group["id"],
                    status="inferred_candidate",
                    electrical_connection="unknown",
                )
            )
    return objects


def rule(name, state, **detail):
    return dict(rule=name, state=state, **detail)


def audit(group, objects, tolerance=0.01):
    """Check actual geometry independently of the renderer; absent evidence stays unknown."""
    results = []
    polygons = []
    hv = valid = True
    for obj in objects:
        p = object_polygon(obj)
        valid &= p.is_valid and p.area > 0
        polygons.append(p)
        outer, holes = object_rings(obj)
        for ring in [outer, *holes]:
            edges = np.roll(ring, -1, axis=0) - ring
            hv &= bool(np.all((abs(edges[:, 0]) < tolerance) | (abs(edges[:, 1]) < tolerance)))
    results += [
        rule("valid_nonempty_geometry", "pass" if valid and objects else "fail"),
        rule("HV_edges", "pass" if hv and objects else "fail"),
    ]
    if group["kind"] == "closed_ring":
        expected = box(*group["outer_xyxy"]).difference(box(*group["hole_xyxy"]))
        actual = unary_union(polygons)
        complete = actual.geom_type == "Polygon" and len(actual.interiors) == 1
        complete &= actual.symmetric_difference(expected).area <= tolerance
        outer, hole = group["outer_xyxy"], group["hole_xyxy"]
        widths = [hole[0] - outer[0], hole[1] - outer[1], outer[2] - hole[2], outer[3] - hole[3]]
        complete &= min(widths) > 0 and max(widths) - min(widths) <= tolerance
        results.append(rule("continuous_constant_width_ring", "pass" if complete else "fail"))
    else:
        expected = array_geometry(group)
        slots = [(o.get("row"), o.get("col")) for o in objects]
        keys = {(o["row"], o["col"]): o for o in expected}
        count_ok = Counter(slots) == Counter(keys.keys())
        results.append(rule("unique_complete_slot_inventory", "pass" if count_ok else "fail"))
        shape_ok = placement_ok = True
        for obj in objects:
            key = (obj.get("row"), obj.get("col"))
            if key not in keys:
                shape_ok = placement_ok = False
                continue
            a, b = object_polygon(obj), object_polygon(keys[key])
            shape_ok &= abs(a.area - b.area) < tolerance and abs(a.length - b.length) < tolerance
            # Comparing complete polygons also catches skew or irregular equal-area shapes.
            placement_ok &= a.symmetric_difference(b).area <= tolerance
        results += [
            rule("shared_size", "pass" if shape_ok and objects else "fail"),
            rule(
                "shared_baselines_pitch_and_shape", "pass" if placement_ok and objects else "fail"
            ),
        ]
        separated = all(not p.intersects(q) for i, p in enumerate(polygons) for q in polygons[:i])
        results.append(rule("nonoverlapping_members", "pass" if objects and separated else "fail"))
    if group["kind"] == "contact_array":
        landing = group.get("AA_materials")
        if landing is None and group.get("AA_material") is not None:
            landing = [group["AA_material"]]
        if landing is None:
            results.append(rule("AA_landing_enclosure", "unknown", missing="AA_material"))
        else:
            material = unary_union([object_polygon(o) for o in landing]).buffer(
                -group["landing_margin"]
            )
            results.append(
                rule(
                    "AA_landing_enclosure",
                    "pass" if objects and all(material.contains(p) for p in polygons) else "fail",
                )
            )
        for field, name in [
            ("channel_zones", "channel_exclusion"),
            ("upper_metal", "upper_metal_enclosure"),
        ]:
            zones = group.get(field)
            if zones is None:
                results.append(rule(name, "unknown", missing=field))
            elif name == "channel_exclusion":
                passed = all(not p.intersects(box(*z)) for p in polygons for z in zones)
                results.append(rule(name, "pass" if objects and passed else "fail"))
            else:
                upper = unary_union([box(*z) for z in zones])
                passed = all(upper.contains(p) for p in polygons)
                results.append(rule(name, "pass" if objects and passed else "fail"))
        results.append(
            rule(
                "target_process_numeric_DRC",
                "unknown",
                missing="target process, calibrated scale and complete layer stack",
            )
        )
    return results


def fit_photo(template_xy, native_xy, split):
    template_xy, native_xy = np.asarray(template_xy, float), np.asarray(native_xy, float)
    training = np.array([s == "fit" for s in split])
    if training.sum() < 4 or (~training).sum() < 1:
        raise ValueError("Need disjoint fitting and held-out observations")
    transform, _ = cv2.findHomography(template_xy[training], native_xy[training], 0)
    if transform is None or not np.isfinite(transform).all() or np.linalg.det(transform) == 0:
        raise ValueError("Degenerate photo fit")
    errors = np.linalg.norm(project(template_xy, transform) - native_xy, axis=1)
    metrics = dict(
        fit_count=int(training.sum()),
        holdout_count=int((~training).sum()),
        fit_median_px=float(np.median(errors[training])),
        holdout_median_px=float(np.median(errors[~training])),
        holdout_p95_px=float(np.percentile(errors[~training], 95)),
        holdout_max_px=float(errors[~training].max()),
    )
    return transform, metrics


def evidence_result(metrics, median_limit, p95_limit):
    passed = metrics["holdout_median_px"] <= median_limit and metrics["holdout_p95_px"] <= p95_limit
    return rule(
        "heldout_photo_observations",
        "pass" if passed else "fail",
        **metrics,
        median_limit_px=median_limit,
        p95_limit_px=p95_limit,
        truth_scope="same_chip_derived_observations_not_independent_human_ground_truth",
    )


def build_group(description, parent, limits):
    group = copy.deepcopy(description)
    old = {o["id"]: o for o in parent["objects"]}
    native_to_layout = np.array(parent[group["source_frame"] + "_native_to_layout"])
    if group["kind"] == "rectangle_array":
        obs = group["observations"]
        original = [dict(copy.deepcopy(old[o["id"]]), row=o["row"], col=o["col"]) for o in obs]
        centers = np.array([np.mean(corners(o["outer_xyxy"]), axis=0) for o in original])
        # Fit group parameters on fitting cells only. Cropped row sizes do not set the prototype.
        fit = np.array([o["split"] == "fit" for o in obs])
        rc = np.array([[o["col"], o["row"]] for o in obs])
        x_design = np.c_[np.ones(fit.sum()), rc[fit, 0]]
        x0, dx = np.linalg.lstsq(x_design, centers[fit, 0], rcond=None)[0]
        y_design = np.c_[np.ones(fit.sum()), rc[fit, 1]]
        # A photo-edge-clipped square has a biased centroid; its visible top edge is usable.
        tops = np.array([o["outer_xyxy"][1] for o in original])
        y0, dy = np.linalg.lstsq(y_design, tops[fit], rcond=None)[0]
        widths = [
            np.diff(np.array(old[o["id"]]["outer_xyxy"]).reshape(2, 2), axis=0)[0]
            for o in obs
            if o["split"] == "fit" and o["row"] == 0
        ]
        side = float(np.rint(np.median(widths)))
        group.update(
            size_wh=[side, side],
            pitch_xy=[float(dx), float(dy)],
            origin_xy=[float(x0 - side / 2), float(y0)],
        )
        objects = array_geometry(group)
        for obj, o in zip(objects, obs, strict=True):
            obj.update(
                previous_object_id=o["id"],
                status="candidate_shared_parameter_revision",
                observation_role="partial_photo_support"
                if o["clipped_source_bottom"]
                else "photo_outline_support",
            )
        template, native_points, splits = [], [], []
        for obj, observation in zip(objects, obs, strict=True):
            clipped = observation["clipped_source_bottom"]
            if clipped and observation["split"] == "fit":
                # Its top edge already influenced pitch fitting; do not call it held out.
                continue
            indices = [0, 1] if clipped else [0, 1, 2, 3]
            for i in indices:
                template.append(corners(obj["outer_xyxy"])[i])
                native_points.append(observation["native_outline_xy"][i])
                splits.append(observation["split"])
        homography, metrics = fit_photo(template, native_points, splits)
        proof = evidence_result(
            metrics, limits["dummy_holdout_median_px"], limits["dummy_holdout_p95_px"]
        )
        group["photo_protocol"] = (
            "fit full-cell corners; hold out other full-cell corners and visible cropped-cell top "
            "corners; clipped centroids/bottom edges excluded; "
            "parameter-fit-only edges not held out"
        )
        group["cropped_observation_count"] = sum(o["clipped_source_bottom"] for o in obs)
    elif group["kind"] == "closed_ring":
        base = old[group["object_id"]]
        x1, y1, x2, y2 = base["outer_xyxy"]
        h1, v1, h2, v2 = base["hole_xyxy"]
        width = float(np.median([h1 - x1, v1 - y1, x2 - h2, y2 - v2]))
        hole = [x1 + width, y1 + width, x2 - width, y2 - width]
        group.update(outer_xyxy=[x1, y1, x2, y2], hole_xyxy=hole, shared_width=width)
        obj = rect(
            "R01-ring",
            [x1, y1, x2, y2],
            previous_object_id=base["id"],
            template_id=group["id"],
            status="candidate_equal_width_revision",
        )
        obj.update(primitive="rectangle_ring", hole_xyxy=hole)
        objects, original = [obj], [copy.deepcopy(base)]
        template = np.vstack([corners(group["outer_xyxy"]), corners(hole)])
        points = base["observed_outer_native_xy"] + base["observed_hole_native_xy"]
        homography, metrics = fit_photo(template, points, ["fit"] * 4 + ["holdout"] * 4)
        proof = evidence_result(metrics, limits["ring_corner_p95_px"], limits["ring_corner_p95_px"])
        group["photo_protocol"] = (
            "fit outer four corners; hold out existing inner four observations"
        )
    else:
        obs = group["observations"]
        baseline = old[group["aa_object_id"]]
        x1, y1, x2, y2 = baseline["outer_xyxy"]
        by_slot = {}
        unmatched = []
        for o in obs:
            if not (0 <= o["row"] < group["rows"] and 0 <= o["col"] < group["cols"]):
                unmatched.append(o)
                continue
            by_slot.setdefault((o["row"], o["col"]), []).append(o)
        usable = [o[0] for o in by_slot.values() if len(o) == 1]
        fit = [o for o in usable if o["split"] == "fit"]
        mapped = project([o["native_center_xy"] for o in fit], native_to_layout)
        cols = np.array([o["col"] for o in fit])
        x0, dx = np.linalg.lstsq(np.c_[np.ones(len(cols)), cols], mapped[:, 0], rcond=None)[0]
        # Symmetric margins are explicit design hypotheses, not lithographic measurements.
        y0, yend = y1 + 12, y2 - 12
        group.update(
            size_wh=[8.0, 8.0],
            pitch_xy=[float(dx), (yend - y0) / (group["rows"] - 1)],
            origin_xy=[float(x0 - 4), float(y0 - 4)],
            AA_material=copy.deepcopy(baseline),
            landing_margin=limits["CT_landing_margin"],
        )
        if group.get("motif_cols"):
            group.update(
                pitch_xy=group["motif_pitch_xy"],
                origin_xy=(np.array(group["origin_center_xy"]) - 4).tolist(),
            )
        group["unmatched_source_observations"] = unmatched
        objects = array_geometry(group)
        for obj in objects:
            sources = by_slot.get((obj["row"], obj["col"]), [])
            obj["source_observation_ids"] = [s["id"] for s in sources]
            obj["status"] = (
                "source_slot_ambiguous"
                if len(sources) > 1
                else "photo_peak_support"
                if sources
                else "inferred_candidate"
            )
        lookup = {(o["row"], o["col"]): o for o in objects}
        template = [
            np.mean(corners(lookup[o["row"], o["col"]]["outer_xyxy"]), axis=0) for o in usable
        ]
        homography, metrics = fit_photo(
            template, [o["native_center_xy"] for o in usable], [o["split"] for o in usable]
        )
        proof = evidence_result(
            metrics, limits["CT_holdout_median_px"], limits["CT_holdout_p95_px"]
        )
        group["photo_protocol"] = "row indices frozen before fit; every fourth row held out"
        group["ambiguous_observation_slots"] = [list(k) for k, v in by_slot.items() if len(v) > 1]
        original = [dict(copy.deepcopy(old[o["id"]]), row=o["row"], col=o["col"]) for o in obs]
    group["layout_to_native"] = homography.tolist()
    group["old_layout_to_native"] = np.linalg.inv(native_to_layout).tolist()
    group["cross_frame_registration"] = "local_group_hypothesis_not_globally_stitched"
    checks = audit(group, objects, limits["normalized_geometry_tolerance"]) + [proof]
    if group.get("ambiguous_observation_slots"):
        checks.append(
            rule("source_slot_ambiguity", "unknown", slots=group["ambiguous_observation_slots"])
        )
    if group.get("unmatched_source_observations"):
        checks.append(
            rule(
                "unmatched_photo_observations",
                "unknown",
                ids=[o["id"] for o in group["unmatched_source_observations"]],
            )
        )
    return group, objects, original, checks


def fault_trials(group, objects):
    """Controlled mutations, with expected failing rule registered independently of audit."""
    mutations = []
    if group["kind"] == "closed_ring":
        changed = copy.deepcopy(objects)
        x1, y1, x2, y2 = group["outer_xyxy"]
        gap = box((x1 + x2) / 2 - 3, y1 - 1, (x1 + x2) / 2 + 3, group["hole_xyxy"][1] + 1)
        p = object_polygon(changed[0]).difference(gap)
        changed[0].update(
            primitive="orthogonal_polygon",
            outer_xy=list(p.exterior.coords)[:-1],
            holes_xy=[list(r.coords)[:-1] for r in p.interiors],
        )
        mutations.append(("ring_gap", changed, "continuous_constant_width_ring", group))
    else:
        changed = copy.deepcopy(objects)
        b = changed[0]["outer_xyxy"]
        changed[0]["outer_xyxy"] = [b[0], b[1] + 5, b[2], b[3] + 5]
        mutations.append(("row_shift", changed, "shared_baselines_pitch_and_shape", group))
        changed = copy.deepcopy(objects)
        changed[0]["outer_xyxy"][2] += 5
        mutations.append(("wrong_size", changed, "shared_size", group))
        mutations += [
            ("missing_slot", copy.deepcopy(objects[1:]), "unique_complete_slot_inventory", group),
            (
                "extra_slot",
                copy.deepcopy(objects) + [copy.deepcopy(objects[0])],
                "unique_complete_slot_inventory",
                group,
            ),
        ]
    if group["kind"] == "contact_array":
        changed = copy.deepcopy(objects)
        b = changed[0]["outer_xyxy"]
        changed[0]["outer_xyxy"] = [0.0, 0.0, 8.0, 8.0]
        mutations.append(("outside_AA", changed, "AA_landing_enclosure", group))
        # Synthetic known channel fixture; no real channel boundary is invented.
        fixture = copy.deepcopy(group)
        fixture["channel_zones"] = [list(objects[0]["outer_xyxy"])]
        mutations.append(
            (
                "synthetic_known_channel_contact",
                copy.deepcopy(objects),
                "channel_exclusion",
                fixture,
            )
        )
        fixture = copy.deepcopy(group)
        fixture["upper_metal"] = [[0, 0, 10, 10]]
        mutations.append(
            (
                "synthetic_missing_upper_coverage",
                copy.deepcopy(objects),
                "upper_metal_enclosure",
                fixture,
            )
        )
    trials = []
    for name, changed, expected, fixture in mutations:
        results = audit(fixture, changed)
        detected = any(c["rule"] == expected and c["state"] == "fail" for c in results)
        trials.append(
            dict(
                group_id=group["id"],
                mutation=name,
                expected_rule=expected,
                detected=detected,
                synthetic_fault=True,
                checks=results,
            )
        )
    return trials


def svg_geometry(objects, transform, frame_size, opacity=0.55):
    pieces = []
    for o in objects:
        outer, holes = object_rings(o)
        paths = []
        for ring in [outer, *holes]:
            points = project(ring, transform)
            paths.append("M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in points) + " Z")
        status = o.get("status", "candidate")
        color = (
            "#ffb84c"
            if status == "inferred_candidate"
            else (
                "#ff6666"
                if status == "source_slot_ambiguous"
                else "#d3adff"
                if o["layer"] == "CT"
                else "#50cbd5"
            )
        )
        fill = "none" if status == "inferred_candidate" else color
        pieces.append(
            f'<path d="{" ".join(paths)}" fill="{fill}" fill-rule="evenodd" '
            f'stroke="{color}" stroke-width="1.6" opacity="{opacity}"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{frame_size[0]}" '
        f'height="{frame_size[1]}">' + "".join(pieces) + "</svg>"
    )


def run(root, spec_path, output):
    root, spec_path, output = (
        Path(root).resolve(),
        Path(spec_path).resolve(),
        Path(output).resolve(),
    )
    if output.exists() or output.is_relative_to(root / "data"):
        raise ValueError("Output must be new and outside data")
    spec = json.loads(spec_path.read_text())
    ref = spec["parent_model"]
    path = (root / ref["path"]).resolve()
    if not path.is_relative_to(root) or digest(path) != ref["sha256"]:
        raise ValueError("Parent evidence changed")
    policy = spec["recognition"]
    if digest(root / policy["policy_document"]) != policy["policy_sha256"]:
        raise ValueError("Frozen policy changed")
    for key in ["extends_prior_spec", "semantic_reference"]:
        if key in spec:
            locked = spec[key]
            if digest(root / locked["path"]) != locked["sha256"]:
                raise ValueError("Changed " + key)
    parent = json.loads(path.read_text())
    for source in parent["sources"].values():
        if digest(root / source["path"]) != source["sha256"]:
            raise ValueError("Source photograph changed")
    groups, objects, results, trials, viewdata = [], [], [], [], []
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".group-", dir=output.parent) as temp:
        stage = Path(temp)
        for description in spec["groups"]:
            group, new, old, checks = build_group(description, parent, spec["limits"])
            groups.append(group)
            objects.extend(new)
            results.append(
                dict(
                    group_id=group["id"],
                    checks=checks,
                    old_checks=audit(group, old),
                    human_review="pending",
                    machine_state=(
                        "fail"
                        if any(c["state"] == "fail" for c in checks)
                        else "unknown"
                        if any(c["state"] == "unknown" for c in checks)
                        else "pass"
                    ),
                )
            )
            trials.extend(fault_trials(group, new))
            context_new = group.get(
                "AA_materials", [group["AA_material"]] if group.get("AA_material") else []
            )
            for obj in group.get("AA_materials", []):
                obj["template_id"] = group["id"] + "-AA"
                objects.append(obj)
            context_old = [
                next(
                    o for o in parent["objects"] if o["id"] == c.get("previous_object_id", c["id"])
                )
                for c in context_new
            ]
            displayed_new, displayed_old = context_new + new, context_old + old
            native = group["source_frame"]
            homography = np.array(group["layout_to_native"])
            old_h = np.array(group["old_layout_to_native"])
            views = {}
            for frame in ["layout", "aa", "poly"]:
                if frame == "layout":
                    transform = old_transform = np.eye(3)
                    bounds = unary_union(
                        [object_polygon(o) for o in displayed_new + displayed_old]
                    ).bounds
                    x1, y1, x2, y2 = bounds
                    views[frame] = [x1 - 25, y1 - 25, x2 - x1 + 50, y2 - y1 + 50]
                    size = parent["canvas_wh"]
                else:
                    cross = np.linalg.inv(parent[frame + "_native_to_layout"]) @ np.array(
                        parent[native + "_native_to_layout"]
                    )
                    transform, old_transform = cross @ homography, cross @ old_h
                    points = project(corners(group["native_window"]), cross)
                    lo, hi = points.min(0), points.max(0)
                    views[frame] = [*lo, *(hi - lo)]
                    size = [parent["sources"][frame]["width"], parent["sources"][frame]["height"]]
                for mode, arr, drawing_transform in [
                    ("before", displayed_old, old_transform),
                    ("after", displayed_new, transform),
                ]:
                    (stage / f"{group['id']}-{frame}-{mode}.svg").write_text(
                        svg_geometry(arr, drawing_transform, size)
                    )
            viewdata.append(
                dict(
                    id=group["id"],
                    label={
                        "D01": "底部 dummy 阵列",
                        "R01": "连续等宽 AA 环",
                        "T01": "U01 宽 MOS 的四列 CT",
                        "T02": "M03 三个 AA 单元的重复接触模式",
                    }.get(group["id"], group["interpretation"]),
                    views=views,
                    native=native,
                    checks=checks,
                )
            )
            # Wide native-source pairs and geometry pairs are deterministic review artifacts.
            for frame in [native, "layout"]:
                images = []
                window = views[frame]
                x, y, w, h = window
                pixel_scale = min(1100 / w, 900 / h)
                target_w = max(1, round(w * pixel_scale))
                target_h = max(1, round(h * pixel_scale))
                scale = np.array(
                    [
                        [target_w / w, 0, -x * target_w / w],
                        [0, target_h / h, -y * target_h / h],
                        [0, 0, 1],
                    ]
                )
                for _mode, arr, transform in [
                    ("before", displayed_old, old_h),
                    ("after", displayed_new, homography),
                ]:
                    if frame == "layout":
                        photo = np.full((target_h, target_w, 3), (35, 24, 16), np.uint8)
                        transform = np.eye(3)
                    else:
                        photo = cv2.imread(str(root / parent["sources"][native]["path"]))
                        photo = cv2.warpPerspective(photo, scale, (target_w, target_h))
                    for o in arr:
                        outer, holes = object_rings(o)
                        for ring in [outer, *holes]:
                            points = np.rint(project(ring, scale @ transform)).astype(np.int32)
                            color = (
                                (60, 180, 255)
                                if o.get("status") == "inferred_candidate"
                                else ((255, 170, 210) if o["layer"] == "CT" else (215, 205, 55))
                            )
                            cv2.polylines(photo, [points], True, color, 1, cv2.LINE_AA)
                    images.append(photo)
                cv2.imwrite(
                    str(stage / f"{group['id']}-{frame}-comparison.png"),
                    np.concatenate(images, axis=1),
                )
        # Gate anti-cheating probe: coherent template translation still breaks fixed photo evidence.
        g = next(g for g in groups if g["kind"] == "contact_array")
        observations = [o for o in g["observations"] if o["split"] == "holdout"]
        homography = np.array(g["layout_to_native"])
        lookup = {(o["row"], o["col"]): o for o in objects if o.get("template_id") == g["id"]}
        pts = [
            np.mean(corners(lookup[o["row"], o["col"]]["outer_xyxy"]), axis=0) for o in observations
        ]
        error = np.linalg.norm(
            project(np.array(pts) + [40, 0], homography)
            - np.array([o["native_center_xy"] for o in observations]),
            axis=1,
        )
        trials.append(
            dict(
                group_id=g["id"],
                mutation="coherent_template_photo_mismatch",
                expected_rule="heldout_photo_observations",
                synthetic_fault=True,
                detected=bool(np.percentile(error, 95) > spec["limits"]["CT_holdout_p95_px"]),
                holdout_p95_px=float(np.percentile(error, 95)),
            )
        )
        model = dict(
            schema_version=1,
            parent_model=ref,
            source_native_sizes=[5712, 4284],
            canvas_wh=parent["canvas_wh"],
            sources=parent["sources"],
            groups=groups,
            objects=objects,
            status="three_structure_families_development_validation_not_full_scene",
            code_sha256=digest(__file__),
            spec_sha256=digest(spec_path),
            physical_fullframe_acceptance=False,
            net_extraction=False,
            previous_parent_objects_changed=False,
        )
        report = dict(
            results=results,
            fault_trials=trials,
            injected_faults_detected=sum(t["detected"] for t in trials),
            injected_faults_total=len(trials),
            same_chip_development_run_not_blind_AI_eval=True,
            automatic_prompt_recognition_benchmark=False,
            physical_legality="pending missing channel/upper-layer evidence and process",
            frozen_policy_and_observations=policy,
            physical_acceptance="pending_human_review_and_missing_material_evidence",
            full_scene_expansion_ready=False,
            failed_photo_groups=[
                r["group_id"]
                for r in results
                if any(
                    c["rule"] == "heldout_photo_observations" and c["state"] == "fail"
                    for c in r["checks"]
                )
            ],
        )
        for name, value in [("model.json", model), ("report.json", report), ("spec.json", spec)]:
            (stage / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        paths = {k: os.path.relpath(root / v["path"], output) for k, v in parent["sources"].items()}
        sizes = {
            "layout": parent["canvas_wh"],
            **{k: [s["width"], s["height"]] for k, s in parent["sources"].items()},
        }
        (stage / "data.js").write_text(
            "const DATA="
            + json.dumps(dict(groups=viewdata, paths=paths, sizes=sizes), ensure_ascii=False)
            + ";"
        )
        (stage / "index.html").write_text(PAGE)
        if digest(path) != ref["sha256"]:
            raise ValueError("Evidence changed during generation")
        for source in parent["sources"].values():
            if digest(root / source["path"]) != source["sha256"]:
                raise ValueError("Photo changed during generation")
        (stage / "manifest.json").write_text(
            json.dumps({p.name: digest(p) for p in stage.iterdir()}, indent=2) + "\n"
        )
        stage.rename(output)
    return report


PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>v5 三类结构约束验证</title>
<style>body{background:#14212b;color:#e2edf6;font:17px/1.6 sans-serif;margin:20px}a{color:#70dfff}
select,input{font:inherit;margin:8px}.pair{display:flex;gap:12px}.panel{width:50%}
svg{width:100%;height:52vh;background:#101923}td,th{border:1px solid #647585;padding:6px}
.orange{color:#ffb84c}</style><h1>v5：结构组、原图回投与质量门验证</h1>
<p>左：旧候选；右：共享参数重建。青色 AA，紫色 CT，橙色空框为模板推断孔，红色为来源槽位歧义。
未批准新几何，未完成工艺 DRC；局部照片模型尚未拼成全幅变形场。</p>
<select id="group"></select><select id="frame"><option value="layout">规则版图</option>
<option value="aa">AA 原图</option><option value="poly">poly/CT 原图</option></select>
<label>叠加透明度<input id="opacity" type="range" min="0" max="1" step="0.05" value="0.6"></label>
<p id="note"></p><div class="pair"><div class="panel">旧候选<svg id="before"><image id="bphoto"/>
<image id="bgeom"/></svg></div><div class="panel">结构组候选<svg id="after"><image id="aphoto"/>
<image id="ageom"/></svg></div></div><table id="checks"></table>
<p><a href="model.json">模型与参数</a> · <a href="report.json">真实样本结果与反例检查</a> ·
<a href="spec.json">冻结输入/阈值</a></p><script src="data.js"></script><script>
const el=id=>document.getElementById(id);
for(const g of DATA.groups){const op=document.createElement('option');op.value=g.id;
op.textContent=g.id+' '+g.label;el('group').append(op);}
function update(){const g=DATA.groups.find(g=>g.id===el('group').value),f=el('frame').value;
for(const [mode,p] of [['before','b'],['after','a']]){const svg=el(mode);
svg.setAttribute('viewBox',g.views[f].join(' '));
for(const name of ['photo','geom']){el(p+name).setAttribute('width',DATA.sizes[f][0]);
el(p+name).setAttribute('height',DATA.sizes[f][1]);}
el(p+'photo').setAttribute('href',DATA.paths[f]||'');
el(p+'geom').setAttribute('href',g.id+'-'+f+'-'+mode+'.svg');
el(p+'geom').style.opacity=el('opacity').value;}
el('note').textContent='原生证据帧：'+g.native+'。'+(f!=='layout'&&f!==g.native?
'当前跨层视图沿用旧候选关系，不能作为精确配准验收。':'此帧可对照拟合与留出观察；规则吻合不等于物理结论通过。');
const names={valid_nonempty_geometry:'多边形有效且非空',HV_edges:'水平/竖直边',
unique_complete_slot_inventory:'模板槽位数量与唯一性',shared_size:'同组尺寸',
shared_baselines_pitch_and_shape:'基线、节距与形状',nonoverlapping_members:'成员分离',
continuous_constant_width_ring:'等宽闭环连续',AA_landing_enclosure:'AA 几何落点与留边',
channel_exclusion:'沟道禁区',upper_metal_enclosure:'上覆金属包围',
target_process_numeric_DRC:'目标工艺数值 DRC',heldout_photo_observations:'留出照片观察回投',
source_slot_ambiguity:'来源槽位歧义',unmatched_photo_observations:'模板外来源亮点'};
el('checks').replaceChildren();for(const c of g.checks){const tr=document.createElement('tr');
const detail=c.holdout_p95_px!==undefined?'中位 '+c.holdout_median_px.toFixed(2)+
' px / P95 '+c.holdout_p95_px.toFixed(2)+' px':c.missing||'';
for(const text of [names[c.rule]||c.rule,{pass:'通过',fail:'失败',unknown:'待定'}[c.state],detail]){
const td=document.createElement('td');
td.textContent=text;tr.append(td);}el('checks').append(tr);}}
document.querySelectorAll('select,input').forEach(x=>x.addEventListener('input',update));update();
</script></html>"""


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--spec", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    report = run(args.root, args.spec, args.output)
    print(
        json.dumps(
            {
                "injected_faults_detected": report["injected_faults_detected"],
                "injected_faults_total": report["injected_faults_total"],
                "groups": report["results"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
