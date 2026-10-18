"""Build a sparse orthogonal AA/CT geometry pilot with source backprojections.

Usage: python -m silicon_eye.geometry_reconstruction --spec SPEC --output NEW_DIR
Requires the project's OpenCV, NumPy and Shapely dependencies; never edits photographs.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon, box


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def project(points, matrix):
    a = np.asarray(points, np.float64)
    result = cv2.perspectiveTransform(a.reshape(-1, 1, 2), np.asarray(matrix, float))
    result = result.reshape(-1, 2)
    if not np.isfinite(result).all():
        raise ValueError("Nonfinite projection")
    return result


def corners(bounds):
    x, y, r, b = bounds
    return np.array([[x, y], [r, y], [r, b], [x, b]], float)


def rectangle_fit(points, step=1):
    """Fit axis-aligned sides from ordered TL/TR/BR/BL corner observations."""
    if step <= 0:
        raise ValueError("Grid step must be positive")
    p = np.asarray(points, float)
    if p.shape != (4, 2) or not np.isfinite(p).all():
        raise ValueError("Expected four finite ordered corners")
    bounds = np.array(
        [np.mean(p[[0, 3], 0]), np.mean(p[[0, 1], 1]), np.mean(p[[1, 2], 0]), np.mean(p[[2, 3], 1])]
    )
    bounds = np.round(bounds / step) * step
    if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
        raise ValueError("Collapsed orthogonal rectangle")
    return bounds.tolist()


def normalize(observations, settings, canvas_wh=(5712, 4284)):
    grid = [x for x in observations if x.get("group") == settings["group"]]
    if len(grid) < 8:
        raise ValueError("Insufficient lattice observations")
    source = np.array([np.mean(x["observed_outer_native_xy"], axis=0) for x in grid])
    origin, pitch = np.array(settings["origin_xy"]), np.array(settings["pitch_xy"])
    if (pitch <= 0).any():
        raise ValueError("Lattice pitch must be positive")
    target = np.array([origin + pitch * [x["column"], x["row"]] for x in grid])
    matrix, _ = cv2.findHomography(source, target, 0)
    if matrix is None or abs(np.linalg.det(matrix)) < 1e-8:
        raise ValueError("Degenerate normalization")
    # Reject folded/extreme extrapolation across the complete reference canvas.
    plane = project(corners([0, 0, *canvas_wh]), matrix)
    ratio = cv2.contourArea(plane.astype(np.float32), oriented=True) / (canvas_wh[0] * canvas_wh[1])
    if not 0.7 < ratio < 1.3:
        raise ValueError("Implausible normalization over full canvas")
    residual = np.linalg.norm(project(source, matrix) - target, axis=1)
    return matrix, {
        "anchor_count": len(grid),
        "median_fit_residual_px": float(np.median(residual)),
        "max_fit_residual_px": float(residual.max()),
        "independent_validation": False,
        "fullframe_distortion_eliminated": False,
    }


def object_rings(obj):
    """Material boundaries; a polygon's bbox is never its material geometry."""
    if obj.get("primitive") == "orthogonal_polygon":
        return np.asarray(obj["outer_xy"], float), [np.asarray(h, float) for h in obj["holes_xy"]]
    return corners(obj["outer_xyxy"]), (
        [] if obj.get("hole_xyxy") is None else [corners(obj["hole_xyxy"])]
    )


def object_polygon(obj):
    outer, holes = object_rings(obj)
    return Polygon(outer, holes)


def orthogonal_fit(points, edge_axes, step=1):
    """Fit declared H/V edge constraints while rejecting collapsed/reversed turns."""
    points = np.asarray(points, float)
    n = len(points)
    if (
        points.shape != (n, 2)
        or n < 4
        or len(edge_axes) != n
        or not np.isfinite(points).all()
        or step <= 0
        or any(a not in ("H", "V") for a in edge_axes)
    ):
        raise ValueError("Invalid orthogonal polygon observations or axes")
    if not Polygon(points).is_valid:
        raise ValueError("Source polygon is self-intersecting or degenerate")
    result = points.copy()
    for coordinate, axis in [(0, "V"), (1, "H")]:
        parents = list(range(n))

        def find(i, parents=parents):
            while parents[i] != i:
                parents[i] = parents[parents[i]]
                i = parents[i]
            return i

        for i, declared in enumerate(edge_axes):
            if declared == axis:
                parents[find((i + 1) % n)] = find(i)
        for group in {find(i) for i in range(n)}:
            ids = [i for i in range(n) if find(i) == group]
            result[ids, coordinate] = np.round(np.mean(points[ids, coordinate]) / step) * step
    original_edges = np.roll(points, -1, axis=0) - points
    edges = np.roll(result, -1, axis=0) - result
    for i, declared in enumerate(edge_axes):
        along, across = (0, 1) if declared == "H" else (1, 0)
        if (
            edges[i, across] != 0
            or abs(edges[i, along]) < step
            or edges[i, along] * original_edges[i, along] <= 0
        ):
            raise ValueError("Orthogonal fitting collapsed or reversed an edge")
    polygon = Polygon(result)
    if not polygon.is_valid or polygon.area <= 0:
        raise ValueError("Orthogonal fitting changed polygon topology")
    return result


def build_aa_polygons(observations, matrix, step):
    objects = []
    for item in observations:
        observed = np.asarray(item["observed_outline_native_xy"], float)
        fitted = orthogonal_fit(project(observed, matrix), item["edge_axes"], step)
        holes = []
        for hole in item.get("observed_holes", []):
            holes.append(
                orthogonal_fit(project(hole["native_xy"], matrix), hole["edge_axes"], step)
            )
        polygon = Polygon(fitted, holes)
        if not polygon.is_valid or polygon.area <= 0:
            raise ValueError("Invalid reconstructed polygon material")
        residuals = np.linalg.norm(project(fitted, np.linalg.inv(matrix)) - observed, axis=1)
        obj = dict(
            item,
            layer="AA",
            primitive="orthogonal_polygon",
            status="candidate",
            revision_role="added_polygon_aa",
            outer_xy=fitted.tolist(),
            holes_xy=[h.tolist() for h in holes],
            outer_xyxy=list(polygon.bounds),
            hole_xyxy=None,
            max_corner_backprojection_shift_px=float(max(residuals)),
            corner_backprojection_shift_px=residuals.tolist(),
            dimension_status="relative_candidate_not_measured_process_dimension",
            electrical_connection="unknown",
        )
        obj["continuation_ports"] = [
            dict(layout_xy=project([p["native_xy"]], matrix)[0].tolist(), **p)
            for p in item.get("continuation_ports", [])
        ]
        objects.append(obj)
    return objects


def check_aa_separation(objects):
    for i, left in enumerate(objects):
        for right in objects[i + 1 :]:
            if object_polygon(left).intersects(object_polygon(right)):
                raise ValueError(f"Unapproved AA touching/overlap: {left['id']} / {right['id']}")


def build_aa(observations, matrix, settings):
    result = []
    for observation in observations:
        obj = dict(observation)
        points = project(obj["observed_outer_native_xy"], matrix)
        outer = rectangle_fit(points, settings["grid_step"])
        if obj.get("group") == settings["group"]:
            center = np.array(settings["origin_xy"]) + np.array(settings["pitch_xy"]) * [
                obj["column"],
                obj["row"],
            ]
            size = np.array(settings["equal_dummy_size_xy"])
            outer = [*(center - size / 2), *(center + size / 2)]
            outer = list(map(float, outer))
        hole = None
        if obj["observed_hole_native_xy"]:
            hole = rectangle_fit(
                project(obj["observed_hole_native_xy"], matrix), settings["grid_step"]
            )
            if not box(*outer).contains(box(*hole)):
                raise ValueError("Ring hole escapes outer boundary: " + obj["id"])
        polygon = Polygon(corners(outer), [] if hole is None else [corners(hole)])
        if not polygon.is_valid or polygon.area <= 0:
            raise ValueError("Invalid AA geometry")
        obj.update(
            primitive="rectangle_ring" if hole else "rectangle",
            outer_xyxy=outer,
            hole_xyxy=hole,
            max_corner_backprojection_shift_px=float(
                np.max(
                    np.linalg.norm(
                        project(corners(outer), np.linalg.inv(matrix))
                        - np.array(obj["observed_outer_native_xy"]),
                        axis=1,
                    )
                )
            ),
            dimension_status="relative_candidate_not_measured_process_dimension",
        )
        result.append(obj)
    # Do not make new joins while regularizing independent observed objects.
    check_aa_separation(result)
    return result


def fit_lattice(points, origin, pitch, shape, limit):
    """Fit two orthogonal equal-pitch axes without inventing missing contact observations."""
    points = np.asarray(points, float).reshape(-1, 2)
    origin, pitch, shape = np.array(origin, float), np.array(pitch, float), np.array(shape)
    if (pitch <= 0).any() or (shape < 2).any():
        raise ValueError("Invalid contact lattice")
    ij = np.rint((points - origin) / pitch).astype(int)
    residual = np.max(np.abs(points - (origin + ij * pitch)), axis=1)
    keep = (ij >= 0).all(axis=1) & (ij < shape).all(axis=1) & (residual <= limit)
    if keep.sum() < 6:
        raise ValueError("Too few independent single-support lattice points")
    for axis in range(2):
        if len(np.unique(ij[keep, axis])) < 2:
            raise ValueError("Lattice axis is unconstrained")
        design = np.c_[np.ones(keep.sum()), ij[keep, axis]]
        origin[axis], pitch[axis] = np.linalg.lstsq(design, points[keep, axis], rcond=None)[0]
    if (pitch <= 0).any():
        raise ValueError("Fitted lattice pitch is invalid")
    return origin, pitch, int(keep.sum())


def ct_positive(obj):
    return obj["status"] in {
        "observed_brightness_geometry_candidate",
        "human_confirmed_contact_candidate_geometry",
    }


def aa_contains(aa_object, bounds):
    return object_polygon(aa_object).contains(box(*bounds))


def apply_human_review(objects, record, record_sha):
    """Apply explicit scoped identity/structure reviews; never alter coordinates or infer nets."""
    by_id = {o["id"]: o for o in objects}
    for decision in record["decisions"]:
        for identifier in decision["object_ids"]:
            if identifier not in by_id:
                raise ValueError("Human review refers to missing object: " + identifier)
            obj = by_id[identifier]
            obj["human_review"] = dict(
                scope=decision["scope"],
                state="confirmed",
                record_sha256=record_sha,
                exact_dimensions="not_accepted",
                electrical_connection="unknown",
            )
            if decision["scope"] == "CT_presence_and_approximate_placement":
                if obj["layer"] != "CT":
                    raise ValueError("CT review cannot promote a different material")
                obj["algorithm_status_before_human_review"] = obj["status"]
                obj["status"] = "human_confirmed_contact_candidate_geometry"
    return objects


def sample_ring_profile(gray, inverse, axis, normal, lo, hi, pitch, max_offset):
    """Fit phase/normal offset at a predeclared pitch; retain actual periodic contrast."""
    ts = np.arange(lo, hi, 0.5)
    if len(ts) < 12 or hi - lo < pitch * 2:
        raise ValueError("Ring side too short to constrain a contact run")
    best = None
    for offset in np.arange(-max_offset, max_offset + 0.01, 1):
        xy = np.zeros((len(ts), 2))
        xy[:, axis], xy[:, 1 - axis] = ts, normal + offset
        native = project(xy, inverse)
        profile = cv2.remap(
            gray,
            native[:, 0].astype(np.float32)[None, :],
            native[:, 1].astype(np.float32)[None, :],
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
        )[0].astype(float)
        profile = (
            np.convolve(np.pad(profile, (2, 2), mode="edge"), [1, 2, 3, 2, 1], mode="valid") / 9
        )
        for phase in np.arange(0, pitch, 0.5):
            positions = np.arange(lo + phase, hi - pitch / 2, pitch)
            contrast = np.interp(positions, ts, profile) - np.interp(
                positions + pitch / 2, ts, profile
            )
            score = float(np.median(contrast))
            if best is None or score > best["median_contrast_gray"]:
                best = dict(
                    positions=positions,
                    normal=normal + offset,
                    offset=float(offset),
                    median_contrast_gray=score,
                    local_contrast=contrast,
                )
    return best


def build_ring_ct(spec, aa, matrix, poly_to_aa, base_arrays, photo):
    """One-dimensional side runs: no CT implied in holes or unobserved corners."""
    inverse = np.linalg.inv(matrix @ poly_to_aa)
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    objects, arrays = [], []
    for proposal in spec.get("ct_ring_runs", []):
        obj_aa = next(o for o in aa if o["id"] == proposal["aa_object_id"])
        if obj_aa["hole_xyxy"] is None:
            raise ValueError("Ring CT proposal requires an AA object with a hole")
        left, top, right, bottom = obj_aa["outer_xyxy"]
        il, it, ir, ib = obj_aa["hole_xyxy"]
        side = proposal["side"]
        side_data = dict(
            top=(0, (top + it) / 2, il, ir),
            bottom=(0, (bottom + ib) / 2, il, ir),
            left=(1, (left + il) / 2, it, ib),
            right=(1, (right + ir) / 2, it, ib),
        )
        if side not in side_data:
            raise ValueError("Invalid ring side")
        axis, normal, lo, hi = side_data[side]
        pitch_ref = next(a for a in base_arrays if a["id"] == proposal["pitch_reference_array"])
        pitch = pitch_ref["fitted_pitch_xy"][axis]
        fit = sample_ring_profile(
            gray, inverse, axis, normal, lo, hi, pitch, proposal["max_normal_offset"]
        )
        slot_ids = []
        for index, (position, contrast) in enumerate(
            zip(fit["positions"], fit["local_contrast"], strict=True)
        ):
            center = np.zeros(2)
            center[axis], center[1 - axis] = position, fit["normal"]
            native = project([center], inverse)[0]
            x, y = np.rint(native).astype(int)
            peak, prominence = 0.0, 0.0
            if 12 <= x < gray.shape[1] - 12 and 12 <= y < gray.shape[0] - 12:
                peak = float(np.percentile(gray[y - 3 : y + 4, x - 3 : x + 4], 80))
                area = gray[y - 11 : y + 12, x - 11 : x + 12].copy().astype(float)
                area[7:16, 7:16] = np.nan
                prominence = peak - float(np.nanmedian(area))
            supported = (
                fit["median_contrast_gray"] >= proposal["min_periodic_contrast_gray"]
                and contrast >= proposal["min_periodic_contrast_gray"]
                and peak >= spec["support"]["min_peak_gray"]
                and prominence >= spec["support"]["min_local_prominence"]
            )
            half = proposal["square_side"] / 2
            bounds = [*(center - half), *(center + half)]
            landed = aa_contains(obj_aa, bounds)
            status = (
                "observed_brightness_geometry_candidate"
                if supported and landed
                else "unknown_AA_landing"
                if supported
                else "unknown_missing_or_occluded"
            )
            identifier = f"{proposal['id']}-p{index + 1:03}"
            objects.append(
                dict(
                    id=identifier,
                    layer="CT",
                    primitive="square",
                    outer_xyxy=list(map(float, bounds)),
                    hole_xyxy=None,
                    status=status,
                    revision_role="added_ring_ct",
                    array_id=proposal["id"],
                    source_frame="poly",
                    source_native_center_xy=native.tolist(),
                    peak_gray=peak,
                    local_prominence=prominence,
                    periodic_contrast_gray=float(contrast),
                    aa_object_id=obj_aa["id"],
                    electrical_connection="unknown",
                    dimension_status="assumed_square_side",
                )
            )
            slot_ids.append(identifier)
        arrays.append(
            dict(
                proposal,
                pitch=float(pitch),
                fitted_normal=fit["normal"],
                fitted_offset=fit["offset"],
                median_periodic_contrast_gray=fit["median_contrast_gray"],
                slot_ids=slot_ids,
                corner_coverage="not_modeled",
                completeness="unknown",
            )
        )
    return objects, arrays


def build_ct(spec, aa, matrix, poly_to_aa, records, photo):
    single = [
        r
        for r in records
        if max(r["poly_native_bbox_xywh"][2:])
        <= spec["support"]["max_single_component_native_size"]
    ]
    centers = project([r["aa_reference_center_xy"] for r in single], matrix)
    inverse = np.linalg.inv(matrix @ poly_to_aa)
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    objects, arrays = [], []
    for proposal in spec["ct_arrays"]:
        aa_obj = next(x for x in aa if x["id"] == proposal["aa_object_id"])
        # A structural hypothesis proposes a grid, but each slot requires raw evidence.
        seed = project([proposal["origin_aa_native_xy"]], matrix)[0]
        axis_points = project(
            [
                np.array(proposal["origin_aa_native_xy"]) + [proposal["pitch_seed_xy"][0], 0],
                np.array(proposal["origin_aa_native_xy"]) + [0, proposal["pitch_seed_xy"][1]],
            ],
            matrix,
        )
        pitch_seed = [axis_points[0, 0] - seed[0], axis_points[1, 1] - seed[1]]
        shape = [proposal["columns"], proposal["rows"]]
        origin, pitch, fit_count = fit_lattice(
            centers, seed, pitch_seed, shape, spec["support"]["grid_fit_residual_limit"]
        )
        slots = []
        for row in range(shape[1]):
            for col in range(shape[0]):
                center = origin + pitch * [col, row]
                native = project([center], inverse)[0]
                x, y = np.rint(native).astype(int)
                peak, prominence = 0.0, 0.0
                if 12 <= x < gray.shape[1] - 12 and 12 <= y < gray.shape[0] - 12:
                    core = gray[y - 3 : y + 4, x - 3 : x + 4]
                    around = gray[y - 11 : y + 12, x - 11 : x + 12].copy().astype(float)
                    around[7:16, 7:16] = np.nan
                    peak = float(np.percentile(core, 80))
                    prominence = peak - float(np.nanmedian(around))
                supported = (
                    peak >= spec["support"]["min_peak_gray"]
                    and prominence >= spec["support"]["min_local_prominence"]
                )
                side = proposal["square_side"]
                bounds = [*(center - side / 2), *(center + side / 2)]
                # AA ownership remains a separate candidate, even where brightness exists.
                landed = aa_contains(aa_obj, bounds)
                status = (
                    "observed_brightness_geometry_candidate"
                    if supported and landed
                    else "unknown_AA_landing"
                    if supported
                    else "unknown_missing_or_occluded"
                )
                identifier = f"{proposal['id']}-r{row + 1:02}-c{col + 1:02}"
                obj = dict(
                    id=identifier,
                    layer="CT",
                    primitive="square",
                    outer_xyxy=bounds,
                    hole_xyxy=None,
                    status=status,
                    array_id=proposal["id"],
                    row=row,
                    column=col,
                    source_frame="poly",
                    source_native_center_xy=native.tolist(),
                    peak_gray=peak,
                    local_prominence=prominence,
                    aa_object_id=aa_obj["id"],
                    electrical_connection="unknown",
                    dimension_status="assumed_square_side",
                )
                objects.append(obj)
                slots.append(identifier)
        arrays.append(
            dict(
                proposal,
                fitted_origin_xy=origin.tolist(),
                fitted_pitch_xy=pitch.tolist(),
                single_support_fit_count=fit_count,
                slot_ids=slots,
                completeness="unknown_not_physical_contact_count",
            )
        )
    return objects, arrays


def svg(objects, size, matrix=None, labels=False):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" '
        f'height="{size[1]}" viewBox="0 0 {size[0]} {size[1]}">'
    ]
    for obj in objects:
        outer, holes = object_rings(obj)
        if matrix is not None:
            outer = project(outer, matrix)
            holes = [project(hole, matrix) for hole in holes]
        if labels:
            if obj["layer"] == "CT":
                continue
            x, y = outer[0]
            parts.append(
                f'<text x="{x}" y="{y - 8}" fill="#ffe898" font-size="18">'
                f"{html.escape(obj['id'])}</text>"
            )
            continue
        color = "#60d99a" if obj["layer"] == "AA" else "#54dafa"
        unknown = obj["layer"] == "CT" and not ct_positive(obj)
        if obj.get("revision_role") == "added_ring_ct":
            color = "#cba4ff"
        if obj.get("revision_role") == "added_polygon_aa":
            color = "#ff80b5"
        if unknown:
            color = "#ffb85c"
        path = "M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in outer) + " Z"
        for hole in holes:
            path += " M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in hole) + " Z"
        parts.append(
            f'<path d="{path}" fill="{"none" if unknown else color}" '
            f'fill-opacity="0.64" fill-rule="evenodd" stroke="{color}" '
            f'stroke-width="{1.5 if unknown else 0.7}"/>'
        )
    return "\n".join([*parts, "</svg>"])


def svg_continuations(objects, size, matrix):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size[0]}" '
        f'height="{size[1]}" viewBox="0 0 {size[0]} {size[1]}">'
    ]
    for obj in objects:
        outer, _ = object_rings(obj)
        for port in obj.get("continuation_ports", []):
            index = port["edge_index"]
            segment = project([outer[index], outer[(index + 1) % len(outer)]], matrix)
            (x, y), (r, b) = segment
            parts.append(
                f'<path d="M{x},{y} L{r},{b}" stroke="#ffd16f" '
                'stroke-width="4" stroke-dasharray="4 3"/>'
            )
            cx, cy = segment.mean(axis=0)
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="6" fill="none" stroke="#ffd16f" stroke-width="2"/>'
            )
    return "\n".join([*parts, "</svg>"])


def render_mask(objects, size):
    result = np.zeros((size[1], size[0]), np.uint8)
    for obj in objects:
        # Use a separate canvas so one object's hole cannot erase another object.
        layer = np.zeros_like(result)
        outer, holes = object_rings(obj)
        cv2.fillPoly(layer, [np.rint(outer).astype(np.int32)], 255)
        for hole in holes:
            cv2.fillPoly(layer, [np.rint(hole).astype(np.int32)], 0)
        result |= layer
    return result


def run(root, spec_path, output):
    root, spec_path, output = (
        Path(root).resolve(),
        Path(spec_path).resolve(),
        Path(output).resolve(),
    )
    if output.exists() or output.is_relative_to(root / "data"):
        raise ValueError("Output must be new and outside data/")
    spec = json.loads(spec_path.read_text())
    photos = {}
    for key, source in spec["sources"].items():
        path = (root / source["path"]).resolve()
        if not path.is_relative_to(root) or digest(path) != source["sha256"]:
            raise ValueError("Changed source or path outside root")
        photos[key] = cv2.imread(str(path))
        if photos[key] is None or photos[key].shape[:2] != (source["height"], source["width"]):
            raise ValueError("Invalid source dimensions")
    reg_path = root / spec["registration"]["path"]
    record_path = root / spec["support"]["record_path"]
    if (
        digest(reg_path) != spec["registration"]["sha256"]
        or digest(record_path) != spec["support"]["record_sha256"]
    ):
        raise ValueError("Registration or observation evidence changed")
    poly_to_aa = np.array(json.loads(reg_path.read_text())["matrix"])
    review_reference = None
    if "parent_model" in spec:
        reference = spec["parent_model"]
        base_path = (root / reference["path"]).resolve()
        if not base_path.is_relative_to(root) or digest(base_path) != reference["sha256"]:
            raise ValueError("Parent geometry model changed")
        base = json.loads(base_path.read_text())
        if base["sources"] != spec["sources"] or base["canvas_wh"] != spec["canvas_wh"]:
            raise ValueError("Parent geometry source or canvas mismatch")
        matrix = np.asarray(base["aa_native_to_layout"], float)
        if not np.allclose(matrix @ poly_to_aa, base["poly_native_to_layout"]):
            raise ValueError("Parent geometry registration mismatch")
        fit = base["normalization_fit"]
        aa = [o for o in base["objects"] if o["layer"] == "AA"]
        ct = [o for o in base["objects"] if o["layer"] == "CT"]
        arrays = base["arrays"]
        review_reference = spec.get("human_review", base.get("human_review"))
        if "human_review" in spec:
            review_path = (root / review_reference["path"]).resolve()
            if (
                not review_path.is_relative_to(root)
                or digest(review_path) != review_reference["sha256"]
            ):
                raise ValueError("Human review record changed")
            review = json.loads(review_path.read_text())
            if review["reviewed_model_sha256"] != reference["sha256"]:
                raise ValueError("Human review does not match parent model")
            apply_human_review(aa + ct, review, review_reference["sha256"])
        ring_ct, ring_arrays = build_ring_ct(spec, aa, matrix, poly_to_aa, arrays, photos["poly"])
        ct += ring_ct
        arrays = arrays + ring_arrays
    else:
        matrix, fit = normalize(spec["aa_observations"], spec["normalization"], spec["canvas_wh"])
        aa = build_aa(spec["aa_observations"], matrix, spec["normalization"])
        ct, arrays = build_ct(
            spec, aa, matrix, poly_to_aa, json.loads(record_path.read_text()), photos["poly"]
        )
    new_polygons = build_aa_polygons(
        spec.get("aa_polygon_observations", []), matrix, spec["normalization"]["grid_step"]
    )
    aa += new_polygons
    check_aa_separation(aa)
    if len({o["id"] for o in aa + ct}) != len(aa) + len(ct):
        raise ValueError("Duplicate geometry identifier")
    accepted_ct = [o for o in ct if ct_positive(o)]
    unknown_ct = [o for o in ct if not ct_positive(o)]
    model = dict(
        schema_version=1,
        status=(
            "partially_reviewed_geometry_with_new_candidates"
            if review_reference
            else "sparse_geometry_candidate"
        ),
        canvas_wh=spec["canvas_wh"],
        unit=spec["unit"],
        spec_sha256=digest(spec_path),
        sources=spec["sources"],
        aa_native_to_layout=matrix.tolist(),
        poly_native_to_layout=(matrix @ poly_to_aa).tolist(),
        normalization_fit=fit,
        objects=aa + ct,
        arrays=arrays,
        unmodeled_area="unknown_not_empty_material",
        electrical_net_extraction=False,
        code_sha256=digest(__file__),
        parent_model=spec.get("parent_model"),
        human_review=review_reference,
        inherited_review_history=base.get("review_history", []) if "parent_model" in spec else [],
        inherited_acceptance_scope=base.get("acceptance_scope") if "parent_model" in spec else None,
    )
    report = dict(
        AA_geometries=len(aa),
        AA_added_polygons=len(new_polygons),
        review_focus=spec.get("review_focus", "AA_CT_arrays"),
        CT_proposed_slots=len(ct),
        CT_positive_geometry_count=len(accepted_ct),
        CT_human_confirmed_count=sum(
            o["status"] == "human_confirmed_contact_candidate_geometry" for o in ct
        ),
        CT_new_ring_positions=sum(o.get("revision_role") == "added_ring_ct" for o in ct),
        CT_new_ring_positive_candidates=sum(
            o.get("revision_role") == "added_ring_ct" and ct_positive(o) for o in ct
        ),
        CT_unknown_slots=len(unknown_ct),
        fullframe_coverage=False,
        independent_physical_acceptance=False,
        full_distortion_correction=False,
        max_AA_backprojection_corner_shift_px=max(
            o["max_corner_backprojection_shift_px"] for o in aa
        ),
        normalization_fit=fit,
    )
    size = spec["canvas_wh"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".geometry-", dir=output.parent) as temp:
        stage = Path(temp)
        for name, data in [("model.json", model), ("report.json", report), ("spec.json", spec)]:
            (stage / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        frames = dict(
            layout=np.eye(3), aa=np.linalg.inv(matrix), poly=np.linalg.inv(matrix @ poly_to_aa)
        )
        for frame, transform in frames.items():
            for name, group in [
                ("AA", [o for o in aa if o.get("revision_role") != "added_polygon_aa"]),
                ("polygon", new_polygons),
                ("CT", [o for o in accepted_ct if o.get("revision_role") != "added_ring_ct"]),
                ("ring", [o for o in accepted_ct if o.get("revision_role") == "added_ring_ct"]),
                ("unknown", unknown_ct),
            ]:
                (stage / f"{frame}-{name}.svg").write_text(svg(group, size, transform))
            (stage / f"{frame}-labels.svg").write_text(svg(aa, size, transform, labels=True))
            (stage / f"{frame}-continuations.svg").write_text(
                svg_continuations(new_polygons, size, transform)
            )
        for name, group in [("AA", aa), ("CT", accepted_ct)]:
            if not cv2.imwrite(str(stage / f"layout-{name}.png"), render_mask(group, size)):
                raise OSError("Mask write failed")
        (stage / "layout.svg").write_text(svg(aa + ct, size))
        preview = np.full((size[1], size[0], 3), (32, 23, 15), np.uint8)
        preview[render_mask(aa, size) > 0] = (140, 202, 83)
        preview[render_mask(new_polygons, size) > 0] = (181, 128, 255)
        preview[render_mask(accepted_ct, size) > 0] = (245, 214, 70)
        added = [o for o in accepted_ct if o.get("revision_role") == "added_ring_ct"]
        preview[render_mask(added, size) > 0] = (255, 164, 203)
        for obj in unknown_ct:
            pts = np.rint(corners(obj["outer_xyxy"])).astype(np.int32)
            cv2.polylines(preview, [pts], True, (92, 184, 255), 1)
        if not cv2.imwrite(str(stage / "layout-preview.png"), preview):
            raise OSError("Preview write failed")
        paths = {k: os.path.relpath(root / v["path"], output) for k, v in spec["sources"].items()}
        windows = []
        for w in spec["review_windows"]:
            native = corners(w["aa_native_xyxy"])
            views = {}
            for frame, points in [
                ("aa", native),
                ("poly", project(native, np.linalg.inv(poly_to_aa))),
                ("layout", project(native, matrix)),
            ]:
                lo, hi = points.min(axis=0), points.max(axis=0)
                views[frame] = [*lo, *(hi - lo)]
            windows.append(dict(id=w["id"], label=w["label"], views=views))
        data = dict(paths=paths, windows=windows, report=report, size=size)
        (stage / "review-data.js").write_text(
            "const DATA=" + json.dumps(data, ensure_ascii=False) + ";\n"
        )
        (stage / "index.html").write_text(REVIEW_HTML)
        for key, source in spec["sources"].items():
            if digest(root / source["path"]) != source["sha256"]:
                raise ValueError("Original changed during generation: " + key)
        hashes = {p.name: digest(p) for p in stage.iterdir()}
        (stage / "manifest.json").write_text(json.dumps(hashes, indent=2) + "\n")
        if output.exists():
            raise ValueError("Output appeared during generation")
        stage.rename(output)
    return report


REVIEW_HTML = """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>AA＋CT 规则几何样稿</title><style>
body{background:#14212b;color:#e2edf6;font:17px/1.6 sans-serif;margin:22px}
a{color:#68dbff}select,label{font:inherit;margin:8px}select{max-width:100%}
#view{width:100%;height:70vh;background:#0c1720;border:1px solid #527087}
.note{color:#ffd48a}button{font:inherit}code{color:#b4e4d3}
</style><h1>AA＋CT 规则几何样稿 · 候选</h1>
<p id="intro">同一全幅版图坐标中的稀疏样稿，未建模区域为未知。
绿色 AA；蓝色为既有 CT，含已审位置；紫色为新增环上 CT 候选；
橙色空框为待核阵列位置。编号指几何对象，不代表器件或网络。没有恢复真实工艺尺度或完成 GDS。</p>
<select id="frame"><option value="layout">规则版图：正交矢量几何</option>
<option value="aa">AA 原图＋回投</option>
<option value="poly">CT 所在 poly 原图＋回投</option></select>
<select id="window"></select><br>
<label><input id="aa" type="checkbox" checked>既有 AA</label>
<label><input id="polygon" type="checkbox" checked>新 AA 多边形</label>
<label><input id="continuations" type="checkbox" checked>延续截口提示</label>
<label><input id="ct" type="checkbox" checked>既有 CT</label>
<label><input id="ring" type="checkbox" checked>环上 CT</label>
<label><input id="unknown" type="checkbox" checked>待核 CT 位置</label>
<label><input id="labels" type="checkbox">AA 编号</label>
<label>叠加透明度 <input id="opacity" type="range" min="0" max="1" step="0.05" value="0.8"></label>
<svg id="view" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
<image id="photo"/><image id="aaLayer"/><image id="polygonLayer"/>
<image id="ctLayer"/>
<image id="ringLayer"/><image id="unknownLayer"/>
<image id="labelLayer"/><image id="continuationsLayer"/></svg>
<p id="reviewSummary"></p>
<p id="summary"></p>
<p class="note" id="reviewNote">重点核对：AA 环内空洞与独立岛是否保留；
CT 行列数量、落点与未知位置是否合理。
正交、等距与等尺寸是待验收的重建约束，不证明全图畸变已消除。看原图时可将透明度降为 0。</p>
<p><a href="layout.svg">打开完整矢量版图</a> · <a href="model.json">几何及来源记录</a> ·
<a href="report.json">拟合与限制</a> · <a href="layout-AA.png">由几何渲染的 AA 像素图</a> ·
<a href="layout-CT.png">由几何渲染的 CT 像素图</a></p>
<script src="review-data.js"></script><script>
const el=id=>document.getElementById(id);
for(const w of DATA.windows){const o=document.createElement('option');o.value=w.id;
o.textContent=w.label;el('window').append(o);}
const full=document.createElement('option');full.value='full';
full.textContent='完整画布（空白处未重建）';
el('window').append(full);
function change(){const f=el('frame').value,w=DATA.windows.find(w=>w.id===el('window').value);
el('view').setAttribute('viewBox',(w?w.views[f]:[0,0,...DATA.size]).join(' '));
for(const id of ['photo','aaLayer','polygonLayer','ctLayer','ringLayer',
'unknownLayer','labelLayer','continuationsLayer']){
el(id).setAttribute('width',DATA.size[0]);el(id).setAttribute('height',DATA.size[1]);}
el('photo').setAttribute('href',DATA.paths[f]||'');el('photo').style.display=f==='layout'?'none':'';
for(const [key,kind,id] of [['aa','AA','aaLayer'],['ct','CT','ctLayer'],
['polygon','polygon','polygonLayer'],['continuations','continuations','continuationsLayer'],
['ring','ring','ringLayer'],['unknown','unknown','unknownLayer'],['labels','labels','labelLayer']]){
el(id).setAttribute('href',f+'-'+kind+'.svg');el(id).style.display=el(key).checked?'':'none';
el(id).style.opacity=el('opacity').value;}}
const r=DATA.report;
if(r.AA_added_polygons>0){
 document.title='阶梯与折线 AA 多边形复核';
 document.querySelector('h1').textContent='阶梯／折线 AA：正交多边形候选';
 el('labels').checked=true;
 el('intro').textContent='粉色是本次新 AA 多边形；绿色是既有 AA。'
 +'橙色截口表示向外延续未建模，不能当作 AA 真实断点。所有对象保留在同一全幅坐标中。';
 el('reviewSummary').textContent='此前已审对象与人审状态保留；本轮只核对 P01–P06。';
 el('summary').textContent=`本次新增 ${r.AA_added_polygons} 个候选：四个台阶与两个折线局部段。`
 +'未抽取新 CT，不新增电气连接或器件判定。';
 el('reviewNote').textContent='核对台阶方向、凹角、缺口、折线宽度与间隙是否合理。'
 +'P05/P06 的橙色截口继续向外延伸，并非独立 AA 岛。可切换 AA 原图并调低透明度。';
}else{
 el('reviewSummary').textContent=r.CT_human_confirmed_count>0
 ?'已录入 AA 结构、dummy 排列及既有横向 CT／原橙色 CT 的确认。'
 +'此次只需核对新增环上 CT；橙色空框均为新增待核位置。':'';
 el('summary').textContent=`${r.AA_geometries} 个 AA 几何；`
 +`${r.CT_proposed_slots} 个 CT 阵列位置中，`
 +`${r.CT_positive_geometry_count} 个为已审或候选几何，${r.CT_unknown_slots} 个待核。`
 +`新增环上 CT 位置 ${r.CT_new_ring_positions} 个，仍需复核。`
 +'这不是全图器件或通孔计数。';
}
document.querySelectorAll('select,input').forEach(x=>x.addEventListener('input',change));change();
</script></html>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        report = run(args.root, args.spec, args.output)
    except (ValueError, OSError, KeyError, cv2.error) as error:
        parser.exit(1, f"Geometry pilot failed: {error}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
