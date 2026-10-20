"""Reconstruct evidence-supported contact families against a locked material baseline.

Run: python -m silicon_eye.ct_joint_reconstruction --spec SPEC --output NEW_DIR
Needs the project environment. Family correspondence is an explicit AI hypothesis;
all exported cuts must pass geometry and landing checks. Raw observations stay separate.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

from .geometry_reconstruction import digest, object_polygon
from .poly_closeout import svg
from .scene_geometry import load_locked


def audit_contacts(objects, model, budget):
    """Hard gate on the whole proposal, including cross-family spacing and landing."""
    aa = {o["id"]: object_polygon(o) for o in model["AA_objects"]}
    poly_by_id = {o["id"]: Polygon(o["layout_outline"]) for o in model["objects"]}
    poly = unary_union(list(poly_by_id.values()))
    all_aa = unary_union(list(aa.values()))
    errors, shapes, cells = [], [], set()
    source_points, identifiers = set(), set()
    for obj in objects:
        if obj["id"] in identifiers:
            errors.append(dict(id=obj["id"], reason="duplicate_contact_ID"))
        identifiers.add(obj["id"])
        native_key = tuple(obj["source_evidence"]["native_center"])
        if native_key in source_points:
            errors.append(dict(id=obj["id"], reason="source_peak_reused"))
        source_points.add(native_key)
        p = Polygon(obj["layout_outline"])
        shapes.append(p)
        key = (obj["family"], obj["column"], obj["row"])
        if key in cells:
            errors.append(dict(id=obj["id"], reason="duplicate_family_slot"))
        cells.add(key)
        x1, y1, x2, y2 = p.bounds
        if (
            not p.is_valid
            or not p.equals(box(*p.bounds))
            or abs((x2 - x1) - (y2 - y1)) > 1e-6
            or abs((x2 - x1) - budget["square_side"]) > 1e-6
        ):
            errors.append(dict(id=obj["id"], reason="not_uniform_square"))
        if obj.get("landing_material", "AA") == "POLY":
            target = poly_by_id[obj["POLY_target"]]
            if not target.buffer(-budget["enclosure_px"]).covers(p):
                errors.append(dict(id=obj["id"], reason="POLY_enclosure_failed"))
            if (
                p.intersection(all_aa).area > 1e-8
                or p.distance(all_aa) < budget["channel_clearance_px"] - 1e-8
            ):
                errors.append(dict(id=obj["id"], reason="POLY_CT_over_active_or_clearance_failed"))
        else:
            if not aa[obj["AA_target"]].buffer(-budget["enclosure_px"]).covers(p):
                errors.append(dict(id=obj["id"], reason="AA_enclosure_failed"))
            if (
                p.intersection(poly).area > 1e-8
                or p.distance(poly) < budget["channel_clearance_px"] - 1e-8
            ):
                errors.append(dict(id=obj["id"], reason="channel_overlap_or_clearance_failed"))
        if not obj["source_evidence"]["supported"]:
            errors.append(dict(id=obj["id"], reason="no_observed_source_support"))
    tree = STRtree(shapes)
    overlaps = []
    gaps = []
    nearest = None
    for i, p in enumerate(shapes):
        for j in tree.query(p.buffer(budget["min_gap_px"])):
            if j <= i:
                continue
            if p.intersection(shapes[j]).area > 1e-8:
                overlaps.append([objects[i]["id"], objects[j]["id"]])
            if p.distance(shapes[j]) < budget["min_gap_px"] - 1e-8:
                gaps.append([objects[i]["id"], objects[j]["id"]])
    if overlaps:
        nearest = 0.0
    elif len(shapes) > 1:
        # Exact nearest-neighbour distances avoid an all-pairs scan on full-frame CT.
        _, distances = tree.query_nearest(shapes, exclusive=True, return_distance=True)
        nearest = float(distances.min()) if len(distances) else None
    for family in {o["family"] for o in objects}:
        group = [o for o in objects if o["family"] == family]
        for axis, label in [(0, "column"), (1, "row")]:
            for level in {o[label] for o in group}:
                values = [
                    Polygon(o["layout_outline"]).centroid.coords[0][axis]
                    for o in group
                    if o[label] == level
                ]
                if np.ptp(values) > 1e-6:
                    errors.append(dict(family=family, reason="row_or_column_not_straight"))
        for fixed, varying, axis, reason in [
            ("column", "row", 1, "row_pitch_not_uniform"),
            ("row", "column", 0, "column_pitch_not_uniform"),
        ]:
            for level in {o[fixed] for o in group}:
                entries = sorted(
                    (o[varying], Polygon(o["layout_outline"]).centroid.coords[0][axis])
                    for o in group
                    if o[fixed] == level
                )
                if len(entries) > 2:
                    indices, positions = np.array(entries).T
                    if (
                        np.any(np.diff(indices) <= 0)
                        or np.ptp(np.diff(positions) / np.diff(indices)) > 1e-6
                    ):
                        errors.append(dict(family=family, reason=reason))
    return dict(
        status="PASS" if objects and not errors and not overlaps and not gaps else "FAIL",
        errors=errors,
        positive_area_overlap_pairs=overlaps,
        min_gap_violations=gaps,
        minimum_edge_gap_px=nearest,
        minimum_AA_enclosure_px=min(
            (
                aa[o["AA_target"]].boundary.distance(p)
                for o, p in zip(objects, shapes, strict=True)
                if o.get("landing_material", "AA") == "AA"
            ),
            default=None,
        ),
        minimum_POLY_clearance_px=min(
            (
                p.distance(poly)
                for o, p in zip(objects, shapes, strict=True)
                if o.get("landing_material", "AA") == "AA"
            ),
            default=None,
        ),
        minimum_POLY_enclosure_px=min(
            (
                poly_by_id[o["POLY_target"]].boundary.distance(p)
                for o, p in zip(objects, shapes, strict=True)
                if o.get("landing_material") == "POLY"
            ),
            default=None,
        ),
        contact_count=len(objects),
        physical_PDK_DRC=False,
    )


def fit_family(photo, model, family, budget):
    """Match observed columns to diffusion windows between explicitly named gates."""
    target = next(o for o in model["AA_objects"] if o["id"] == family["AA_target"])
    aa = object_polygon(target)
    if not aa.equals(box(*aa.bounds)):
        raise ValueError("This family method requires a rectangular active body")
    gates = [o for o in model["objects"] if o["id"] in family["gate_ids"]]
    if len(gates) != len(family["gate_ids"]):
        raise ValueError("Missing gate ID")
    if any(o["AA_target"] != target["id"] for o in gates):
        raise ValueError("Wrong active target")
    remaining = aa.difference(unary_union([Polygon(o["layout_outline"]) for o in gates]))
    windows = sorted(list(remaining.geoms), key=lambda p: p.bounds[0])
    seeds = family["native_columns_at_first_row"]
    if len(windows) != len(seeds):
        raise ValueError("Source and reconstructed diffusion counts differ")
    xlevels = np.linspace(windows[0].centroid.x, windows[-1].centroid.x, len(windows)).tolist()
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray, (5, 5), 1).astype(float)
    residual = smooth - cv2.GaussianBlur(smooth, (0, 0), 4)
    observations = []
    widths = []
    for col, seed in enumerate(seeds):
        for row in range(family["row_count"]):
            expected = np.array(
                [
                    seed + family["native_column_drift_per_row"] * row,
                    family["native_first_row_y"] + row * family["native_row_pitch"],
                ]
            )
            x, y = np.rint(expected).astype(int)
            rx, ry = family["search_radius_xy"]
            patch = residual[y - ry : y + ry + 1, x - rx : x + rx + 1]
            dy, dx = np.unravel_index(patch.argmax(), patch.shape)
            px, py = x - rx + int(dx), y - ry + int(dy)
            support = (
                smooth[py, px] >= family["min_gray"] and residual[py, px] >= family["min_residual"]
            )
            # Optical residual core, recorded independently of the desired geometry.
            line = residual[py, px - 8 : px + 9] >= residual[py, px] * 0.5
            lo = hi = 8
            while lo > 0 and line[lo - 1]:
                lo -= 1
            while hi < 16 and line[hi + 1]:
                hi += 1
            widths.append(hi - lo + 1)
            observations.append(
                dict(
                    column=col,
                    row=row,
                    native_center=[int(px), int(py)],
                    supported=bool(support),
                    peak_gray=float(smooth[py, px]),
                    residual=float(residual[py, px]),
                    residual_core_width_px=int(hi - lo + 1),
                    seed_distance_px=float(np.linalg.norm(np.array([px, py]) - expected)),
                )
            )
    # Fitted common row phase/pitch straightens the design, not the source photograph.
    row_idx = np.array([o["row"] for o in observations])
    design = np.c_[np.ones(len(row_idx)), row_idx]
    photo_y = np.array([o["native_center"][1] for o in observations])
    origin, pitch = np.linalg.lstsq(design, photo_y, rcond=None)[0]
    sy1, sy2 = family["native_AA_y_bounds"]
    _, ay1, _, ay2 = aa.bounds
    ys = ay1 + (origin + np.arange(family["row_count"]) * pitch - sy1) * (ay2 - ay1) / (sy2 - sy1)
    if "layout_row_origin" in family:
        ys = (
            family["layout_row_origin"]
            + np.arange(family["row_count"]) * family["layout_row_pitch"]
        )
    slope_x = []
    for col in range(len(seeds)):
        values = [o for o in observations if o["column"] == col]
        cx = np.array([o["native_center"][0] for o in values])
        fit = np.linalg.lstsq(np.c_[np.ones(len(cx)), np.arange(len(cx))], cx, rcond=None)[0]
        slope_x.append(fit.tolist())
    # Independent dark material between observed contact columns supports the gate correspondence.
    contrasts = []
    y1 = int(origin)
    y2 = int(origin + (family["row_count"] - 1) * pitch)
    for left, right in zip(seeds[:-1], seeds[1:], strict=True):
        lx, rx, center_x = round(left), round(right), round((left + right) / 2)
        contact = (gray[y1:y2, lx - 2 : lx + 3].mean() + gray[y1:y2, rx - 2 : rx + 3].mean()) / 2
        contrasts.append(float(contact - gray[y1:y2, center_x - 2 : center_x + 3].mean()))
    if min(contrasts) < family["min_gate_body_contrast"]:
        raise ValueError("Gate body correspondence lacks independent contrast support")
    objects = []
    for o in observations:
        col, row = o["column"], o["row"]
        x, y = xlevels[col], ys[row]
        half = budget["square_side"] / 2
        p = box(x - half, y - half, x + half, y + half)
        objects.append(
            dict(
                id=f"CTJ-{family['id']}-C{col + 1:02}-R{row + 1:02}",
                family=family["id"],
                column=col,
                row=row,
                layer="CT",
                AA_target=target["id"],
                POLY_context=family["gate_ids"],
                layout_center=[x, float(y)],
                layout_outline=list(map(list, p.exterior.coords[:-1])),
                source_evidence=o,
                source_frame="poly",
                fitted_native_center=[
                    float(slope_x[col][0] + slope_x[col][1] * row),
                    float(origin + pitch * row),
                ],
                status="AI_joint_reconstruction_candidate_not_human_approved",
                M1_enclosure="unknown",
                net_id=None,
            )
        )
    return objects, dict(
        id=family["id"],
        native_row_fit=[float(origin), float(pitch)],
        native_y_fit_RMS_px=float(np.sqrt(np.mean((photo_y - design @ [origin, pitch]) ** 2))),
        photo_residual_core_width_median_px=float(np.median(widths)),
        photo_residual_core_width_range_px=[min(widths), max(widths)],
        gate_body_contrasts=contrasts,
        correspondence="AI_local_family_match_not_human_accepted",
        physical_cut_size="unknown_optical_core_is_not_lithographic_boundary",
        source_observations=observations,
    )


def apply_poly_connections(model, recipes):
    """Merge authorized connected POLY parts, retaining each gate's identity as a child."""
    working = copy.deepcopy(model)
    revisions = []
    for recipe in recipes:
        ids = set(recipe["gate_ids"])
        fingers = [o for o in working["objects"] if o["id"] in ids]
        if len(fingers) != len(ids):
            raise ValueError("Missing POLY finger in authorized patch")
        bus = box(*recipe["bus_layout_bbox"])
        parts = [Polygon(o["layout_outline"]) for o in fingers]
        if any(p.intersection(bus).area <= 0 for p in parts):
            raise ValueError("Bus must overlap every named gate end")
        for o in working["objects"]:
            if (
                o["id"] not in ids
                and Polygon(o["layout_outline"]).distance(bus) < recipe["unrelated_POLY_gap_px"]
            ):
                raise ValueError("Gate bus would join or approach unrelated POLY")
        all_aa = unary_union([object_polygon(o) for o in working["AA_objects"]])
        if bus.intersects(all_aa):
            raise ValueError("Common gate bus must stay outside active")
        merged = unary_union(parts + [bus])
        if merged.geom_type != "Polygon" or not merged.is_valid or len(merged.interiors):
            raise ValueError("Common gate must be a single valid material polygon")
        new = copy.deepcopy(fingers[0])
        new.update(
            id=recipe["id"],
            layout_outline=list(map(list, merged.exterior.coords[:-1])),
            kind="connected_gate_fingers_and_bus",
            gate_finger_ids=recipe["gate_ids"],
            gate_fingers=copy.deepcopy(fingers),
            native_outline=[],
            geometry_method="human_confirmed_common_gate_local_bus_candidate_extent",
            source_record=dict(
                native_bus_bbox=recipe["native_bus_bbox"],
                extent_status="AI_candidate_not_exact_boundary",
            ),
        )
        working["objects"] = [o for o in working["objects"] if o["id"] not in ids] + [new]
        revisions.append(
            dict(
                id=recipe["id"],
                previous_finger_records=fingers,
                bus_layout_bbox=recipe["bus_layout_bbox"],
                count_of_MOS_fingers=len(fingers),
                identity_status="human_confirmed_common_POLY_gate",
                precise_extent_status="AI_candidate",
            )
        )
    working["local_POLY_connection_revisions"] = revisions
    working["POLY_material_aliases"] = {key: r["id"] for r in recipes for key in r["gate_ids"]}
    working["final_status"] = "local_common_gate_POLY_extent_candidate; human_topology_confirmed"
    return working


def build_poly_contacts(prior, recipe, budget):
    by_id = {o["id"]: o for o in prior["objects"]}
    objects = []
    for index, entry in enumerate(recipe["observed_slots"]):
        old = by_id[entry["source_observation_id"]]
        x = recipe["first_layout_x"] + entry["slot"] * recipe["layout_pitch"]
        y = recipe["layout_y"]
        half = budget["square_side"] / 2
        evidence = copy.deepcopy(old["source_observation"])
        evidence.update(
            native_center=evidence["source_native_center_xy"],
            supported=evidence["peak_gray"] >= recipe["min_gray"]
            and evidence["local_residual"] >= recipe["min_residual"],
            source_observation_id=old["id"],
        )
        objects.append(
            dict(
                id=f"CTJ-{recipe['id']}-{index + 1:02}",
                family=recipe["id"],
                column=entry["slot"],
                row=0,
                layer="CT",
                landing_material="POLY",
                POLY_target=recipe["POLY_target"],
                layout_center=[x, y],
                layout_outline=list(
                    map(list, box(x - half, y - half, x + half, y + half).exterior.coords[:-1])
                ),
                source_evidence=evidence,
                source_frame="poly",
                status="observed_gate_contact_candidate_not_human_approved",
                M1_enclosure="unknown",
                net_id=None,
            )
        )
    return objects


def promote_confirmed_slots(objects, parent, review, review_ref, budget):
    """Human approval can resolve an unknown without inventing optical measurements."""
    if objects != parent["objects"]:
        raise ValueError("Acceptance promotion must preserve all prior contact records")
    result = copy.deepcopy(objects)
    pending = {(o["family"], o["slot"]): o for o in parent["unresolved_slots"]}
    for decision in review["confirmed_slots"]:
        key = (decision["family"], decision["slot"])
        if key not in pending:
            raise ValueError("No matching previously reviewed unknown slot")
        item = pending[key]
        x, y = item["layout_center"]
        half = budget["square_side"] / 2
        context = next(o for o in objects if o["family"] == key[0])
        new = copy.deepcopy(context)
        new.update(
            id=decision["contact_id"],
            column=key[1] if item.get("axis", 0) == 0 else context["column"],
            row=key[1] if item.get("axis", 0) == 1 else context["row"],
            layout_center=[x, y],
            layout_outline=list(
                map(list, box(x - half, y - half, x + half, y + half).exterior.coords[:-1])
            ),
            source_evidence=dict(
                native_center=item["estimated_native_center"],
                supported=True,
                evidence_type="human_confirmation",
                algorithm_detected=False,
                native_locator_status="estimated_from_prior_review_grid_not_exact_pixel_confirmation",
                human_review=review_ref,
            ),
            status="human_confirmed_displayed_contact",
        )
        result.append(new)
    return result


def preserve_layout(objects, parent):
    """Revise evidence correspondence without perturbing the existing design proposal."""
    previous = {o["id"]: o for o in parent["objects"]}
    if set(previous) != {o["id"] for o in objects}:
        raise ValueError("Correspondence-only revision must preserve all contact slots")
    for obj in objects:
        old = previous[obj["id"]]
        if (obj["AA_target"], obj["column"], obj["row"]) != (
            old["AA_target"],
            old["column"],
            old["row"],
        ):
            raise ValueError("Correspondence-only revision cannot change material or slot")
        obj["layout_outline"] = copy.deepcopy(old["layout_outline"])
        obj["layout_center"] = copy.deepcopy(old["layout_center"])
        obj["previous_source_evidence"] = copy.deepcopy(old["source_evidence"])
    return objects


def retain_accepted_records(observed, parent):
    """Keep accepted contact records byte-for-byte equivalent after support revalidation."""
    by_id = {o["id"]: o for o in observed}
    if set(by_id) != {o["id"] for o in parent["objects"]}:
        raise ValueError("Accepted contact scope changed")
    if any(by_id[o["id"]]["source_evidence"] != o["source_evidence"] for o in parent["objects"]):
        raise ValueError("Accepted source evidence changed")
    return copy.deepcopy(parent["objects"])


def check_source_boundaries(objects, family):
    """A matching count is insufficient; named source boundaries must also match."""
    limits = family.get("source_boundary_constraints")
    if not limits:
        return
    group = [o for o in objects if o["family"] == family["id"]]
    for label, col in [("first", 0), ("last", len(family["native_columns_at_first_row"]) - 1)]:
        observed = np.median(
            [o["source_evidence"]["native_center"][0] for o in group if o["column"] == col]
        )
        low, high = limits[label + "_column_native_x_range"]
        if not low <= observed <= high:
            raise ValueError("Source boundary correspondence failed: " + label)
    for obj in group:
        x = obj["source_evidence"]["native_center"][0]
        if any(low <= x <= high for low, high in limits["excluded_column_native_x_ranges"]):
            raise ValueError("Wrong neighboring device contact column selected")


def require_exportable(objects, model, budget):
    report = audit_contacts(objects, model, budget)
    if report["status"] != "PASS":
        raise ValueError("CT reconstruction export blocked: " + json.dumps(report))
    return report


def run(root, spec_path, output):
    root = Path(root).resolve()
    output = Path(output)
    if output.exists():
        raise ValueError("Output must be new")
    spec = json.loads(Path(spec_path).read_text())
    model = load_locked(root, spec["inputs"]["baseline"])
    prior = load_locked(root, spec["inputs"]["prior_observations"])
    acceptance = load_locked(root, spec["inputs"]["baseline_acceptance"])
    if acceptance["locked_files"]["model-v1.json"] != spec["inputs"]["baseline"]["sha256"]:
        raise ValueError("Not the accepted stage baseline")
    photo_ref = spec["inputs"]["photo"]
    if digest(root / photo_ref["path"]) != photo_ref["sha256"]:
        raise ValueError("Changed source photograph")
    photo = cv2.imread(str(root / photo_ref["path"]))
    objects = []
    fits = []
    for family in spec["families"]:
        additions, fit = fit_family(photo, model, family, spec["budget"])
        objects.extend(additions)
        fits.append(fit)
    if "geometry_parent" in spec["inputs"]:
        contact_parent = load_locked(root, spec["inputs"]["geometry_parent"])
        objects = (
            retain_accepted_records(objects, contact_parent)
            if spec.get("retain_accepted_contact_records")
            else preserve_layout(objects, contact_parent)
        )
    for family in spec["families"]:
        check_source_boundaries(objects, family)
    original_material_model = model
    if spec.get("poly_connections"):
        review = load_locked(root, spec["inputs"]["gate_review"])
        if set(review["approved_SD_ids"]) != {o["id"] for o in objects}:
            raise ValueError("Gate patch must retain exactly the accepted source/drain contacts")
        if any(
            set(r["gate_ids"]) != set(review["shared_gate_finger_ids"])
            for r in spec["poly_connections"]
        ):
            raise ValueError("POLY connection patch exceeds human-confirmed group")
        model = apply_poly_connections(model, spec["poly_connections"])
        model["POLY_revision_parent_ref"] = spec["inputs"]["baseline"]
        for recipe in spec["poly_contact_rows"]:
            objects.extend(build_poly_contacts(prior, recipe, spec["budget"]))
    if "acceptance_review" in spec["inputs"]:
        review = load_locked(root, spec["inputs"]["acceptance_review"])
        accepted_parent = load_locked(root, spec["inputs"]["acceptance_parent"])
        objects = promote_confirmed_slots(
            objects, accepted_parent, review, spec["inputs"]["acceptance_review"], spec["budget"]
        )
    report = require_exportable(objects, model, spec["budget"])
    report.update(
        scope="explicit_family_subset_not_full_CT_layer",
        baseline_ref=spec["inputs"]["baseline"],
        correspondence_status="AI_candidate_after_human_boundary_correction"
        if "geometry_parent" in spec["inputs"]
        else "AI_candidate",
        layout_preserved="geometry_parent" in spec["inputs"],
        approved_SD_contact_count=42 if spec.get("poly_connections") else None,
        added_POLY_contact_count=sum(o.get("landing_material") == "POLY" for o in objects),
        POLY_local_revision=bool(spec.get("poly_connections")),
        M1_enclosure="unknown",
        net_inference=False,
        implementation_sha256=digest(Path(__file__)),
        retained_prior_observations=len(prior["objects"]),
        phase="geometry_and_material_landing_PASS; material_truth_not_human_accepted",
    )
    if digest(root / spec["inputs"]["baseline"]["path"]) != spec["inputs"]["baseline"]["sha256"]:
        raise ValueError("Baseline modified")
    output.mkdir(parents=True)
    design = svg(model, spec["layout_bbox"])
    cuts = "".join(
        '<polygon points="'
        + " ".join(f"{x},{y}" for x, y in o["layout_outline"])
        + f'" fill="{("#ed8eff" if o.get("landing_material") == "POLY" else "#65baff")}" '
        + f'stroke="#c3e5ff" stroke-width="0.4"><title>{o["id"]}</title></polygon>'
        for o in objects
    )
    unknown_slots = []
    for row in spec.get("poly_contact_rows", []):
        row_objects = [o for o in objects if o["family"] == row["id"]]
        indices = np.array([o["column"] for o in row_objects])
        source_x = np.array([o["source_evidence"]["native_center"][0] for o in row_objects])
        phase, pitch = np.linalg.lstsq(np.c_[np.ones(len(indices)), indices], source_x, rcond=None)[
            0
        ]
        source_y = float(np.median([o["source_evidence"]["native_center"][1] for o in row_objects]))
        for slot in row["unobserved_slot_indices"]:
            x = row["first_layout_x"] + slot * row["layout_pitch"]
            y = row["layout_y"]
            unknown_slots.append(
                dict(
                    family=row["id"],
                    slot=slot,
                    layout_center=[x, y],
                    estimated_native_center=[float(phase + slot * pitch), source_y],
                    status="unknown_not_exported_contact",
                )
            )
    annotations = "".join(
        f'<rect x="{q["layout_center"][0] - 2.5}" y="{q["layout_center"][1] - 2.5}" '
        'width="5" height="5" fill="none" stroke="#ffb34d" '
        'stroke-width="0.6" stroke-dasharray="1 1"><title>UNKNOWN - not a CT object</title></rect>'
        for q in unknown_slots
    )
    design = design.replace(
        "</svg>",
        '<g data-layer="CT">' + cuts + '</g><g data-layer="UNKNOWN">' + annotations + "</g></svg>",
    )
    (output / "layout.svg").write_text(design)
    left, top, right, bottom = spec["native_bbox"]
    raw = Image.fromarray(cv2.cvtColor(photo[top:bottom, left:right], cv2.COLOR_BGR2RGB))
    raw.save(output / "raw.png")
    marked = raw.copy()
    draw = ImageDraw.Draw(marked)
    for o in objects:
        x, y = o["source_evidence"]["native_center"]
        x -= left
        y -= top
        color = "#ed8eff" if o.get("landing_material") == "POLY" else "#65baff"
        if o["source_evidence"].get("evidence_type") == "human_confirmation":
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), outline=color, width=1)
            draw.text((x - 3, y + 5), "H", fill=color, stroke_width=1, stroke_fill="black")
            continue
        draw.line((x - 3, y, x + 3, y), fill=color, width=1)
        draw.line((x, y - 3, x, y + 3), fill=color, width=1)
    if "geometry_parent" in spec["inputs"]:
        for family in spec["families"]:
            limits = family["source_boundary_constraints"]
            for low, high in limits["excluded_column_native_x_ranges"]:
                draw.rectangle(
                    (
                        low - left,
                        family["native_AA_y_bounds"][0] - top,
                        high - left,
                        family["native_AA_y_bounds"][1] - top,
                    ),
                    outline="#ff6868",
                    width=1,
                )
            for col in range(len(family["native_columns_at_first_row"])):
                first = next(
                    o
                    for o in objects
                    if o["family"] == family["id"] and o["column"] == col and o["row"] == 0
                )
                x, y = first["source_evidence"]["native_center"]
                draw.text(
                    (x - left - 7, y - top - 18),
                    f"C{col + 1}",
                    fill="#65baff",
                    stroke_width=1,
                    stroke_fill="black",
                )
        previous_image = spec["inputs"]["previous_source_image"]
        if digest(root / previous_image["path"]) != previous_image["sha256"]:
            raise ValueError("Changed prior source review image")
        Image.open(root / previous_image["path"]).save(output / "source-before.png")
    for entry in unknown_slots:
        x, y = entry["estimated_native_center"]
        x -= left
        y -= top
        draw.rectangle((x - 4, y - 4, x + 4, y + 4), outline="#ffb34d", width=1)
        draw.text((x - 3, y + 5), "?", fill="#ffb34d", stroke_width=1, stroke_fill="black")
    marked.save(output / "source.png")
    for name, value in [
        ("model", dict(objects=objects, unresolved_slots=unknown_slots, scope=report["scope"])),
        ("report", report),
        ("fit", fits),
        ("spec", spec),
        ("material-model", model),
    ]:
        (output / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    (output / "index.html").write_text("""<!doctype html><html lang="zh"><meta charset="utf-8">
<title>CT联合规则重建 v2</title><style>body{max-width:1400px;margin:24px auto;background:#111c28;
color:#eee;font:16px sans-serif}img{width:100%}select{padding:8px}a{color:#65baff}
section{padding:16px;border:1px solid #567;margin:20px 0}</style>
<h1>CT联合重建：先通过自检，再交人工验收</h1>
<p>本页只重建右侧已确认六条MOS区域的扩散CT，未宣告整个窗口完成。
绿色AA、黄色POLY、蓝色CT。已审AA/POLY不变。孔与孔不重叠，同列竖直、同行水平，纵向等间距；
CT完整落在AA且避开POLY沟道。所有孔都有实际亮峰支持。</p>
<p>局部列对应仍为AI候选；相对像素检查不是目标工艺DRC，M1包围与电连接未知。
左侧宽MOS、下端栅连接亮点和其他窗口尚未导出为合格CT几何，旧473个观察完整保留。</p>
<section><h2>联合设计图</h2><p>只检查右侧六MOS的CT子集，不把未处理处解释成没有孔。</p>
<select onchange="document.getElementById('design').src=this.value">
<option value="layout.svg">AA＋POLY＋CT</option>
<option value="base.svg">既有AA＋POLY（未改动）</option>
</select><img id="design" src="layout.svg"></section>
<section><h2>同一位置原图与观察支持（十字为实际亮点）</h2>
<select onchange="document.getElementById('source').src=this.value">
<option value="source.png">原图＋实际亮点</option><option value="raw.png">纯原图</option>
</select><img id="source" src="source.png"></section>
<p><a href="report.json">硬性质量门</a> ·
<a href="fit.json">局部匹配与光学尺寸观察</a></p></html>""")
    if "geometry_parent" in spec["inputs"]:
        page = (output / "index.html").read_text().replace("CT联合规则重建 v2", "CT源图对应修订 v3")
        page = page.replace(
            "<h1>",
            "<p>本轮只修正源图对应，42个CT的设计坐标及AA/POLY保持不变。红框为排除的宽MOS孔列；蓝色C1–C7为当前七列，最右C7现已纳入。边界坐标由AI据用户定性反馈定位，仍待复核。</p><h1>",
            1,
        )
        page = page.replace(
            '<option value="raw.png">纯原图</option>',
            '<option value="source-before.png">修订前标注（对照）</option>'
            '<option value="raw.png">纯原图</option>',
        )
        (output / "index.html").write_text(page)
    if spec.get("poly_connections"):
        page = (output / "index.html").read_text()
        start = page.index("<h1>")
        end = page.index("<section>", start)
        page = (
            page[:start]
            + """<h1>源漏CT已确认：补充共栅POLY和栅接触</h1>
<p>蓝色源漏CT原有42孔保持不变。用户确认六MOS的栅在POLY上相连；
本次将六栅指及下端横带合并为同一POLY实体，六个栅指编号继续保留。</p>
<p>另加入10个有明确照片亮点支持的栅极CT候选，均被共栅POLY完整包围且位于AA之外。
行列位置仍按规则几何重建；一处可能漏检的槽位保留未知，未凭预期补孔。
原图紫色十字为新增栅极接触、蓝色为已审源漏接触；橙框问号仅是待核位置，不是CT对象。横带精确边界及新增CT仍待复核，M1归属未知。</p>
"""
            + page[end:]
        )
        page = page.replace(
            "本轮只修正源图对应，42个CT的设计坐标及AA/POLY保持不变。",
            "本轮局部增加共栅横带；已审源漏CT与AA保持不变。",
        )
        page = page.replace(
            "只检查右侧六MOS的CT子集，不把未处理处解释成没有孔。",
            "检查六栅共用横带及其接触；其他区域未覆盖。",
        )
        page = page.replace("既有AA＋POLY（未改动）", "含共栅带的AA＋POLY")
        page = page.replace(
            '<option value="layout.svg">AA＋POLY＋CT</option>',
            '<option value="layout.svg">AA＋POLY＋全部CT</option>'
            '<option value="before.svg">修订前：六独立栅指＋已审源漏CT</option>',
        )
        (output / "index.html").write_text(page)
        before = svg(original_material_model, spec["layout_bbox"])
        before_cuts = "".join(
            '<polygon points="'
            + " ".join(f"{x},{y}" for x, y in o["layout_outline"])
            + '" fill="#65baff"/>'
            for o in objects
            if o.get("landing_material", "AA") == "AA"
        )
        (output / "before.svg").write_text(before.replace("</svg>", before_cuts + "</svg>"))
    if "acceptance_review" in spec["inputs"]:
        page = (output / "index.html").read_text()
        start = page.index("<h1>")
        end = page.index("<section>", start)
        page = (
            page[:start]
            + """<h1>右侧六MOS局部复核通过</h1>
<p>42个源漏CT与共栅POLY横带已确认。栅CT共11个：保留此前10个，并将用户确认的橙色位置纳入。
所有原有52个CT记录不变。紫色为栅CT，蓝色为源漏CT。</p>
<p>原图H表示人工确认的原待核位置，其图上落点仍是原孔列推算定位；没有伪造算法检出的亮峰。
局部几何通过不代表真实工艺DRC或M1连接已确认。其他区域未覆盖。</p>
"""
            + page[end:]
        )
        page = page.replace("CT联合规则重建 v2", "右侧六MOS局部已审 v5")
        (output / "index.html").write_text(page)
    (output / "base.svg").write_text(svg(model, spec["layout_bbox"]))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.spec, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
