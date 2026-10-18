"""Extend a reviewed geometry scene with full-frame AA/CT proposals and coverage records.

Run: python -m silicon_eye.scene_geometry --root . --spec SPEC --output NEW_DIR
Uses existing OpenCV/Shapely dependencies. Source segmentation initializes observations;
all exported material geometry is orthogonal. No photographs or reviewed objects are changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from .full_frame_materials import native_valid, segment_aa
from .geometry_reconstruction import (
    REVIEW_HTML,
    corners,
    ct_positive,
    digest,
    object_polygon,
    object_rings,
    project,
    rectangle_fit,
    svg,
    svg_continuations,
)
from .guided_materials import ct_support


def load_locked(root, reference):
    path = (root / reference["path"]).resolve()
    if not path.is_relative_to(root) or digest(path) != reference["sha256"]:
        raise ValueError("Changed or external evidence: " + reference["path"])
    return json.loads(path.read_text())


def canvas_size(base, matrix, poly_matrix, aa_top=185):
    """Expand the origin-zero layout canvas without moving any existing coordinates."""
    all_points = []
    for frame, transform, top in [("aa", matrix, aa_top), ("poly", poly_matrix, 0)]:
        s = base["sources"][frame]
        all_points.extend(project(corners([0, top, s["width"], s["height"]]), transform))
    points = np.asarray(all_points)
    if points.min() < -1:
        raise ValueError("Valid source extends to negative coordinates; explicit origin needed")
    return np.maximum(base["canvas_wh"], np.ceil(points.max(axis=0) + 17)).astype(int).tolist()


def paint_objects(objects, size, labels=False):
    """Rasterize bounded object ROIs; holes never erase another object's material."""
    result = np.zeros((size[1], size[0]), np.int32 if labels else np.uint8)
    for index, obj in enumerate(objects, 1):
        outer, holes = object_rings(obj)
        lo = np.maximum(0, np.floor(outer.min(axis=0)).astype(int) - 1)
        hi = np.minimum(size, np.ceil(outer.max(axis=0)).astype(int) + 2)
        if (hi <= lo).any():
            continue
        local = np.zeros((hi[1] - lo[1], hi[0] - lo[0]), np.uint8)
        cv2.fillPoly(local, [np.rint(outer - lo).astype(np.int32)], 1)
        for hole in holes:
            cv2.fillPoly(local, [np.rint(hole - lo).astype(np.int32)], 0)
        roi = result[lo[1] : hi[1], lo[0] : hi[0]]
        roi[local > 0] = index if labels else 255
    return result


def orthogonal_outline(contour, settings):
    """Fit cyclic horizontal/vertical line runs, retaining genuine concavities."""
    raw = contour.reshape(-1, 2).astype(float)
    reference = Polygon(raw)
    if reference.area < settings["min_area"]:
        raise ValueError("small_source_outline")
    rectangle = box(*reference.bounds)
    if reference.boundary.hausdorff_distance(rectangle.boundary) <= 5:
        vertices = corners(rectangle.bounds)
    else:
        if not reference.is_valid:
            raise ValueError("self_touching_source_requires_review")
        points = cv2.approxPolyDP(contour, settings["approximation_px"], True).reshape(-1, 2)
        edges = np.roll(points, -1, axis=0) - points
        axes = (np.abs(edges[:, 1]) > np.abs(edges[:, 0])).astype(int)
        starts = [i for i in range(len(points)) if axes[i] != axes[i - 1]]
        if len(starts) < 4 or len(starts) > settings["max_vertices"]:
            raise ValueError("complex_or_unconstrained_outline")
        lines = []
        for j, start in enumerate(starts):
            end, ids, current = starts[(j + 1) % len(starts)], [], start
            while True:
                ids.append(current)
                current = (current + 1) % len(points)
                if current == end:
                    break
            ids.append(end)
            axis = axes[start]
            lines.append((axis, float(np.rint(np.median(points[ids, 1 - axis])))))
        vertices = []
        for j, (axis, value) in enumerate(lines):
            previous = lines[j - 1][1]
            vertices.append([previous, value] if axis == 0 else [value, previous])
        vertices = np.asarray(vertices)
    fitted = Polygon(vertices)
    if not fitted.is_valid or fitted.area <= 0:
        raise ValueError("invalid_fitted_outline")
    distance = reference.boundary.hausdorff_distance(fitted.boundary)
    ratio = fitted.area / reference.area
    lengths = np.linalg.norm(np.roll(vertices, -1, axis=0) - vertices, axis=1)
    if (
        distance > settings["max_boundary_shift_px"]
        or not settings["min_area_ratio"] <= ratio <= settings["max_area_ratio"]
        or min(lengths) < settings["min_short_side"]
    ):
        raise ValueError("shape_fit_exceeds_working_limits")
    return vertices.tolist(), float(distance)


def aa_proposals(mask, protected, settings):
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return [], []
    hierarchy = hierarchy[0]
    candidates, deferred = [], []
    occupied = [(object_polygon(o), o["id"]) for o in protected]
    for index, contour in enumerate(contours):
        if abs(cv2.contourArea(contour)) < settings["min_area"]:
            continue
        depth, parent = 0, index
        while hierarchy[parent, 3] >= 0:
            parent = hierarchy[parent, 3]
            depth += 1
        if depth % 2:
            continue
        x, y, w, h = map(int, cv2.boundingRect(contour))
        identifier = f"AA-F{index:05}"
        record = dict(id=identifier, layout_observation_bbox_xywh=[x, y, w, h])
        try:
            outer, distance = orthogonal_outline(contour, settings)
            holes, child = [], hierarchy[index, 2]
            while child >= 0:
                if abs(cv2.contourArea(contours[child])) >= settings["min_area"]:
                    hole, d = orthogonal_outline(contours[child], settings)
                    holes.append(hole)
                    distance = max(distance, d)
                child = hierarchy[child, 0]
            polygon = Polygon(outer, holes)
            if not polygon.is_valid or polygon.area < settings["min_area"]:
                raise ValueError("invalid_material_polygon")
            collisions = [name for p, name in occupied if polygon.intersects(p)]
            if collisions:
                covered = unary_union([p for p, name in occupied if name in collisions])
                fraction = polygon.intersection(covered).area / polygon.area
                record.update(
                    reason=(
                        "covered_by_existing_geometry"
                        if fraction >= 0.9
                        else "overlaps_preserved_or_other_geometry"
                    ),
                    references=collisions,
                    represented_area_fraction=float(fraction),
                )
                deferred.append(record)
                continue
            obj = dict(
                record,
                layer="AA",
                primitive="orthogonal_polygon",
                outer_xy=outer,
                holes_xy=holes,
                outer_xyxy=list(polygon.bounds),
                hole_xyxy=None,
                status="candidate",
                revision_role="scene_AA_candidate",
                observation_method="full_frame_support_line_fit_not_material_truth",
                max_outline_fit_shift_layout_units=distance,
                connectivity="geometry_candidate_not_electrical_net",
                dimension_status="relative_layout_units_not_um",
            )
            candidates.append(obj)
            occupied.append((polygon, identifier))
        except ValueError as error:
            deferred.append(dict(record, reason=str(error)))
    return candidates, deferred


def extract_peaks(photo, valid, settings):
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray, (5, 5), 1)
    residual = smooth.astype(np.int16) - cv2.GaussianBlur(smooth, (0, 0), 4).astype(np.int16)
    k = settings["peak_neighborhood"]
    shape_support = ct_support(photo, profile="narrow_vertical")
    maxima = (
        (smooth == cv2.dilate(smooth, np.ones((k, k), np.uint8)))
        & (smooth >= settings["peak_gray"])
        & (residual >= settings["peak_residual"])
        & valid
        & shape_support
    ).astype(np.uint8)
    count, _, stats, centers = cv2.connectedComponentsWithStats(maxima)
    observations = []
    for index in range(1, count):
        if max(stats[index, 2:4]) > settings["max_peak_plateau_span"]:
            continue
        x, y = np.rint(centers[index]).astype(int)
        observations.append(
            dict(
                source_native_center_xy=centers[index].tolist(),
                peak_gray=int(smooth[y, x]),
                local_residual=int(residual[y, x]),
            )
        )
    return observations


def regularize_axis(values, settings):
    """Snap observed points to supported row/column levels; never create new slots."""
    values = np.asarray(values, float)
    order = np.argsort(values)
    groups = []
    for index in order:
        if not groups or values[index] - np.mean(values[groups[-1]]) > settings["axis_cluster_px"]:
            groups.append([int(index)])
        else:
            groups[-1].append(int(index))
    levels = np.array([np.median(values[g]) for g in groups])
    target = levels.copy()
    diffs = np.diff(levels)
    possible = diffs[(diffs >= settings["pitch_min"]) & (diffs <= settings["pitch_max"])]
    pitch = None
    if len(possible) >= 3:
        pitch = float(np.median(possible))
        ij = np.rint((levels - levels[0]) / pitch)
        design = np.c_[np.ones(len(ij)), ij]
        origin, fitted_pitch = np.linalg.lstsq(design, levels, rcond=None)[0]
        predicted = origin + ij * fitted_pitch
        if (
            fitted_pitch > 0
            and np.max(np.abs(predicted - levels)) <= settings["periodic_snap_residual"]
        ):
            target = predicted
            pitch = float(fitted_pitch)
        else:
            pitch = None
    result = values.copy()
    for group, level in zip(groups, target, strict=True):
        for index in group:
            if abs(values[index] - level) <= settings["max_regularization_shift"]:
                result[index] = level
    return result, dict(level_count=len(levels), fitted_pitch=pitch)


def ct_proposals(observations, aa, parent_ct, labelmap, matrix, settings):
    if not observations:
        return [], [], [], 0
    points = project([o["source_native_center_xy"] for o in observations], matrix)
    old = np.array([np.mean(corners(o["outer_xyxy"]), axis=0) for o in parent_ct])
    groups, unassigned, skipped = {}, [], 0
    for i, point in enumerate(points):
        if len(old) and np.min(np.linalg.norm(old - point, axis=1)) < settings["duplicate_radius"]:
            skipped += 1
            continue
        x, y = np.rint(point).astype(int)
        label = (
            int(labelmap[y, x]) if 0 <= y < labelmap.shape[0] and 0 <= x < labelmap.shape[1] else 0
        )
        if label == 0:
            unassigned.append(
                dict(
                    observations[i],
                    layout_center_xy=point.tolist(),
                    status="AA_assignment_unknown_not_proof_of_poly",
                )
            )
        else:
            groups.setdefault(label - 1, []).append(i)
    objects, metadata = [], []
    reserved = [o["outer_xyxy"] for o in parent_ct]
    for ai, indices in groups.items():
        actual = points[indices]
        xs, xmeta = regularize_axis(actual[:, 0], settings)
        ys, ymeta = regularize_axis(actual[:, 1], settings)
        aa_object = aa[ai]
        material = object_polygon(aa_object)
        emitted = []
        for local_index, source_index in enumerate(indices):
            center = np.array([xs[local_index], ys[local_index]])
            if np.linalg.norm(center - actual[local_index]) > settings["max_regularization_shift"]:
                center = actual[local_index].copy()
            if any(np.linalg.norm(center - p) < settings["duplicate_radius"] for p in emitted):
                skipped += 1
                continue
            half = settings["square_side"] / 2
            bounds = [*(center - half), *(center + half)]
            if reserved:
                occupied = np.asarray(reserved)
                overlap = (
                    (occupied[:, 0] <= bounds[2])
                    & (occupied[:, 2] >= bounds[0])
                    & (occupied[:, 1] <= bounds[3])
                    & (occupied[:, 3] >= bounds[1])
                )
                if np.any(overlap):
                    skipped += 1
                    continue
            emitted.append(center)
            reserved.append(bounds)
            manual_shift = aa_object.get("max_manual_corner_shift_px", 0)
            landed = material.contains(box(*bounds))
            if manual_shift > settings.get("max_manual_AA_shift_for_landing", 8):
                # Working boundary guard, not uncertainty everywhere in the material interior.
                landed = landed and material.boundary.distance(box(*bounds)) > manual_shift
            obj = dict(
                observations[source_index],
                id=f"CT-F{source_index:05}",
                layer="CT",
                primitive="square",
                outer_xyxy=list(map(float, bounds)),
                hole_xyxy=None,
                status="observed_brightness_geometry_candidate" if landed else "unknown_AA_landing",
                revision_role="scene_CT_candidate",
                aa_object_id=aa_object["id"],
                original_layout_center_xy=actual[local_index].tolist(),
                regularization_shift_layout_units=float(
                    np.linalg.norm(center - actual[local_index])
                ),
                dimension_status="assumed_8_unit_square_not_measured",
                electrical_connection="unknown",
            )
            objects.append(obj)
        metadata.append(
            dict(
                aa_object_id=aa_object["id"],
                x_axis=xmeta,
                y_axis=ymeta,
                source_peak_count=len(indices),
                emitted_count=len(emitted),
                missing_slots="not_generated",
            )
        )
    return objects, unassigned, metadata, skipped


def write_image(path, array):
    if not cv2.imwrite(str(path), array):
        raise OSError("Failed writing " + str(path))


def run(root, spec_path, output):
    root, spec_path, output = (
        Path(root).resolve(),
        Path(spec_path).resolve(),
        Path(output).resolve(),
    )
    if output.exists() or output.is_relative_to(root / "data"):
        raise ValueError("Output must be new and outside data/")
    spec = json.loads(spec_path.read_text())
    base = load_locked(root, spec["parent_model"])
    initializer = load_locked(root, spec["initializer"])
    cv2.setNumThreads(2)
    photos, valid = {}, {}
    for name, source in base["sources"].items():
        path = root / source["path"]
        if digest(path) != source["sha256"]:
            raise ValueError("Changed photograph")
        photos[name] = cv2.imread(str(path))
        if photos[name] is None or photos[name].shape[:2] != (source["height"], source["width"]):
            raise ValueError("Source dimensions changed")
        valid[name] = native_valid(
            photos[name].shape[:2],
            initializer["excluded_native_boxes"][name]
            + spec.get("additional_excluded_native_boxes", {}).get(name, []),
        )
    matrix = np.array(base["aa_native_to_layout"])
    poly_matrix = np.array(base["poly_native_to_layout"])
    aa_top = int(np.flatnonzero(np.any(valid["aa"], axis=1))[0])
    size = canvas_size(base, matrix, poly_matrix, aa_top)
    aa = [copy.deepcopy(o) for o in base["objects"] if o["layer"] == "AA"]
    old_ct = [copy.deepcopy(o) for o in base["objects"] if o["layer"] == "CT"]
    manual = []
    for observed in spec["manual_AA_observations"]:
        bounds = rectangle_fit(project(observed["native_corners"], matrix))
        hole = (
            rectangle_fit(project(observed["native_hole_corners"], matrix))
            if observed.get("native_hole_corners")
            else None
        )
        shift = float(
            np.max(
                np.linalg.norm(
                    project(corners(bounds), np.linalg.inv(matrix)) - observed["native_corners"],
                    axis=1,
                )
            )
        )
        obj = dict(
            observed,
            layer="AA",
            primitive="rectangle_ring" if hole else "rectangle",
            outer_xyxy=bounds,
            hole_xyxy=hole,
            max_manual_corner_shift_px=shift,
            status="candidate",
            revision_role="scene_AA_candidate",
            scope=(
                "visible_fragment_photo_edge_not_physical_endpoint"
                if observed.get("visible_photo_edge")
                else "visible_geometry_candidate"
            ),
            dimension_status="relative_layout_units_not_um",
        )
        if any(object_polygon(obj).intersects(object_polygon(p)) for p in aa + manual):
            raise ValueError("Manual source hypothesis intersects preserved geometry")
        manual.append(obj)
    initial = segment_aa(photos["aa"], valid["aa"], initializer["aa"])
    support = cv2.warpPerspective(
        initial["mask"].astype(np.uint8) * 255, matrix, tuple(size), flags=cv2.INTER_NEAREST
    )
    del initial
    new_aa, deferred = aa_proposals(support, aa + manual, spec["aa"])
    new_aa = manual + new_aa
    aa += new_aa
    labelmap = paint_objects(aa, size, labels=True)
    observations = extract_peaks(photos["poly"], valid["poly"], spec["ct"])
    new_ct, unassigned, groups, skipped = ct_proposals(
        observations, aa, old_ct, labelmap, poly_matrix, spec["ct"]
    )
    geometry_mask = (labelmap > 0).astype(np.uint8)
    outside = cv2.distanceTransform(1 - geometry_mask, cv2.DIST_L2, 5)
    residual = ((support > 0) & (outside > spec["aa"]["working_residual_band_px"])).astype(
        np.uint8
    ) * 255
    aa_valid = cv2.warpPerspective(
        valid["aa"].astype(np.uint8) * 255, matrix, tuple(size), flags=cv2.INTER_NEAREST
    )
    ct_valid = cv2.warpPerspective(
        valid["poly"].astype(np.uint8) * 255, poly_matrix, tuple(size), flags=cv2.INTER_NEAREST
    )
    del labelmap, outside, support
    model = copy.deepcopy(base)
    model.update(
        status="full_frame_geometry_candidates_partial_physical_coverage",
        canvas_wh=size,
        previous_canvas_wh=base["canvas_wh"],
        source_native_sizes={k: [v["width"], v["height"]] for k, v in base["sources"].items()},
        objects=aa + old_ct + new_ct,
        scene_CT_groups=groups,
        parent_model=spec["parent_model"],
        derived_from_model=spec["parent_model"],
        spec_sha256=digest(spec_path),
        code_sha256=digest(__file__),
        geometry_code_sha256=digest(Path(__file__).with_name("geometry_reconstruction.py")),
        fullframe_physical_coverage="not_accepted",
        electrical_net_extraction=False,
    )
    positive = [o for o in new_ct if ct_positive(o)]
    unknown = [o for o in new_ct if not ct_positive(o)]
    report = dict(
        AA_geometries=len(aa),
        AA_added_polygons=len(new_aa),
        AA_preserved=len(aa) - len(new_aa),
        CT_proposed_slots=len(old_ct) + len(new_ct),
        CT_positive_geometry_count=sum(ct_positive(o) for o in old_ct) + len(positive),
        CT_unknown_slots=sum(not ct_positive(o) for o in old_ct) + len(unknown),
        CT_preserved_unknown_slots=sum(not ct_positive(o) for o in old_ct),
        AA_deferred_proposals=len(deferred),
        AA_already_represented_observations=sum(
            d["reason"] == "covered_by_existing_geometry" for d in deferred
        ),
        AA_unresolved_proposals=sum(
            d["reason"] != "covered_by_existing_geometry" for d in deferred
        ),
        new_CT_positive=len(positive),
        new_CT_boundary_unknown=len(unknown),
        CT_unassigned_source_peaks=len(unassigned),
        source_CT_peak_observations=len(observations),
        CT_duplicates_suppressed=skipped,
        CT_suppression_meaning="geometry_overlap_or_proximity_not_physical_duplicate_proof",
        CT_human_confirmed_count=120,
        canvas_wh=size,
        raw_canvas_wh=base["canvas_wh"],
        parent_objects_unchanged=True,
        fullframe_physical_acceptance=False,
        residual_initializer_support_pixels=int(np.count_nonzero(residual)),
        coverage_metric_meaning="support_residual_not_ground_truth_missing_AA",
        new_geometry_human_review="pending",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".scene-", dir=output.parent) as temp:
        stage = Path(temp)
        windows, rows = [], []
        s = base["sources"]["aa"]
        xs, ys = (
            np.linspace(0, s["width"], 5).astype(int),
            np.linspace(185, s["height"], 4).astype(int),
        )
        full = dict(id="overview", label="全幅总览（空白不代表无材料）", views={})
        for name, transform in [
            ("layout", matrix),
            ("aa", np.eye(3)),
            ("poly", np.linalg.inv(poly_matrix) @ matrix),
        ]:
            ps = project(corners([0, 185, s["width"], s["height"]]), transform)
            lo, hi = ps.min(0), ps.max(0)
            full["views"][name] = [*lo, *(hi - lo)]
        windows.append(full)
        for row in range(3):
            for col in range(4):
                name = f"F{row * 4 + col + 1:02}"
                native = corners([xs[col], ys[row], xs[col + 1], ys[row + 1]])
                views = {}
                for frame, transform in [
                    ("layout", matrix),
                    ("aa", np.eye(3)),
                    ("poly", np.linalg.inv(poly_matrix) @ matrix),
                ]:
                    ps = project(native, transform)
                    lo, hi = ps.min(0), ps.max(0)
                    views[frame] = [*lo, *(hi - lo)]
                windows.append(
                    dict(id=name, label=f"{name}：第{row + 1}行第{col + 1}列", views=views)
                )
                poly = Polygon(project(native, matrix))
                ids = [o["id"] for o in new_aa if poly.intersects(object_polygon(o))]
                rows.append(
                    dict(
                        id=name,
                        native_xyxy=[
                            int(xs[col]),
                            int(ys[row]),
                            int(xs[col + 1]),
                            int(ys[row + 1]),
                        ],
                        new_AA_intersecting_ids=ids,
                        unresolved_AA_observation_ids=[
                            d["id"]
                            for d in deferred
                            if d["reason"] != "covered_by_existing_geometry"
                            and poly.intersects(
                                box(
                                    d["layout_observation_bbox_xywh"][0],
                                    d["layout_observation_bbox_xywh"][1],
                                    d["layout_observation_bbox_xywh"][0]
                                    + d["layout_observation_bbox_xywh"][2],
                                    d["layout_observation_bbox_xywh"][1]
                                    + d["layout_observation_bbox_xywh"][3],
                                )
                            )
                        ],
                        display_window_only=True,
                        coverage_status="candidate_or_unmodeled_not_accepted_complete",
                    )
                )
        for name, data in [
            ("model.json", model),
            ("report.json", report),
            ("spec.json", spec),
            ("deferred-AA.json", deferred),
            ("unassigned-CT.json", unassigned),
            ("source-CT-peaks.json", observations),
            ("coverage.json", rows),
        ]:
            (stage / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        frames = {
            "layout": np.eye(3),
            "aa": np.linalg.inv(matrix),
            "poly": np.linalg.inv(poly_matrix),
        }
        sizes = {"layout": size, **model["source_native_sizes"]}
        for frame, transform in frames.items():
            for name, objects in [
                ("AA", aa[: -len(new_aa)] if new_aa else aa),
                ("polygon", new_aa),
                ("CT", old_ct),
                ("ring", positive),
                ("unknown", unknown),
            ]:
                text = svg(objects, sizes[frame], transform)
                if name == "polygon":
                    text = text.replace("#60d99a", "#50cbd5")
                if name == "ring":
                    text = text.replace("#54dafa", "#d3adff")
                (stage / f"{frame}-{name}.svg").write_text(text)
            (stage / f"{frame}-labels.svg").write_text(
                svg(aa, sizes[frame], transform, labels=True)
            )
            (stage / f"{frame}-continuations.svg").write_text(
                svg_continuations(aa, sizes[frame], transform)
            )
        rgba = np.zeros((size[1], size[0], 4), np.uint8)
        rgba[residual > 0] = [0, 170, 255, 180]
        write_image(stage / "layout-coverage.png", rgba)
        for frame, transform in [
            ("aa", np.linalg.inv(matrix)),
            ("poly", np.linalg.inv(poly_matrix)),
        ]:
            write_image(
                stage / f"{frame}-coverage.png",
                cv2.warpPerspective(rgba, transform, tuple(sizes[frame]), flags=cv2.INTER_NEAREST),
            )
        write_image(stage / "AA-layout.png", geometry_mask * 255)
        write_image(
            stage / "CT-layout.png",
            paint_objects([o for o in old_ct + new_ct if ct_positive(o)], size),
        )
        write_image(stage / "AA-valid-layout.png", aa_valid)
        write_image(stage / "CT-source-valid-layout.png", ct_valid)
        (stage / "layout.svg").write_text(svg(aa + old_ct + new_ct, size))
        paths = {k: os.path.relpath(root / v["path"], output) for k, v in base["sources"].items()}
        data = dict(
            scene=True,
            paths=paths,
            windows=windows,
            coverage=rows,
            report=report,
            size=size,
            frame_sizes=sizes,
        )
        (stage / "review-data.js").write_text(
            "const DATA=" + json.dumps(data, ensure_ascii=False) + ";\n"
        )
        (stage / "index.html").write_text(scene_page())
        preview = np.full((size[1], size[0], 3), (32, 23, 15), np.uint8)
        preview[paint_objects(aa[: -len(new_aa)] if new_aa else aa, size) > 0] = (140, 202, 83)
        preview[paint_objects(new_aa, size) > 0] = (213, 203, 80)
        preview[paint_objects(positive, size) > 0] = (255, 173, 211)
        preview[paint_objects([o for o in old_ct if ct_positive(o)], size) > 0] = (245, 214, 70)
        write_image(
            stage / "overview.png", cv2.resize(preview, (1600, round(size[1] * 1600 / size[0])))
        )
        for source in base["sources"].values():
            if digest(root / source["path"]) != source["sha256"]:
                raise ValueError("Source changed during run")
        manifest = {p.name: digest(p) for p in stage.iterdir()}
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        if output.exists():
            raise ValueError("Output appeared during generation")
        stage.rename(output)
    return report


def scene_page():
    page = (
        REVIEW_HTML.replace("新增环上 CT", "新增 CT")
        .replace("环上 CT", "新增 CT")
        .replace("新 AA 多边形", "新增 AA")
    )
    page = page.replace(
        "el(id).setAttribute('width',DATA.size[0]);",
        "el(id).setAttribute('width',(DATA.frame_sizes?.[f]||DATA.size)[0]);",
    )
    page = page.replace(
        "el(id).setAttribute('height',DATA.size[1]);",
        "el(id).setAttribute('height',(DATA.frame_sizes?.[f]||DATA.size)[1]);",
    )
    page = page.replace(
        '<image id="labelLayer"/>', '<image id="coverageLayer"/><image id="labelLayer"/>'
    )
    page = page.replace(
        "'unknownLayer','labelLayer','continuationsLayer'",
        "'unknownLayer','labelLayer','continuationsLayer','coverageLayer'",
    )
    page = page.replace(
        '<select id="window"></select><br>',
        '<select id="window"></select><br>'
        '<label><input id="coverage" type="checkbox">残余证据提示</label>',
    )
    page = page.replace(
        "el('photo').setAttribute('href',DATA.paths[f]||'');",
        """el('coverageLayer').setAttribute('href',f+'-coverage.png');
el('coverageLayer').style.display=el('coverage').checked?'':'none';
el('coverageLayer').style.opacity=el('opacity').value;
el('photo').setAttribute('href',DATA.paths[f]||'');""",
    )
    page = page.replace(
        '<p id="summary"></p>',
        '<p id="summary"></p>'
        '<table id="coverageTable" border="1" cellpadding="6"></table>'
        '<p><a href="coverage.json">覆盖清单</a> · '
        '<a href="deferred-AA.json">重复观察及未解决几何</a> · '
        '<a href="unassigned-CT.json">尚未分配的来源亮点</a></p>',
    )
    a = page.index("if(r.AA_added_polygons>0){")
    end = page.index("document.querySelectorAll('select,input')", a)
    page = (
        page[:a]
        + """document.title='全幅 AA＋CT 规则几何扩展';
document.querySelector('h1').textContent='全幅 AA＋CT：规则几何候选与覆盖';
el('intro').textContent='青色：新增 AA；紫色：新增 CT 候选；橙色空框：新增落点待核。'
+'已审对象保留。空白为未建模/未分类，不能当成无材料。残余证据提示不是全部未知的边界。';
el('reviewSummary').textContent='已审样本不重问；先看全幅，再按 F01–F12 检查覆盖、误连及明显遗漏。';
el('summary').textContent=`新增 AA ${r.AA_added_polygons} 个几何，CT ${r.new_CT_positive} 个候选，`
+`${r.new_CT_boundary_unknown} 个落点待核；${r.CT_unassigned_source_peaks} 个亮点尚未分配给 AA。`
+'这些不是物理器件/通孔总数，全幅完整性尚未验收。';
el('reviewNote').textContent='F01–F12 只作显示窗口，不裁割材料或网络。'
+'照片边缘不是物理终点；局部畸变和复杂轮廓冲突仍保留。可切到原图并降低透明度。';
el('unknown').checked=false;
const header=document.createElement('tr');
for(const text of ['位置','新增 AA 涉及对象','待解决观察','原生 AA 范围']){
 const cell=document.createElement('th');cell.textContent=text;header.append(cell);}
el('coverageTable').append(header);
for(const row of DATA.coverage){
 const tr=document.createElement('tr'),td=document.createElement('td');
 const button=document.createElement('button');button.textContent=row.id;
 button.onclick=()=>{el('window').value=row.id;change();window.scrollTo({top:0});};
 td.append(button);tr.append(td);
 for(const value of [row.new_AA_intersecting_ids.length,
 row.unresolved_AA_observation_ids.length,row.native_xyxy.join(', ')]){
  const cell=document.createElement('td');cell.textContent=value;tr.append(cell);}
 el('coverageTable').append(tr);
}

"""
        + page[end:]
    )
    return (
        page.replace("layout-AA.png", "AA-layout.png")
        .replace("layout-CT.png", "CT-layout.png")
        .replace("[0,0,...DATA.size]", "[0,0,...(DATA.frame_sizes?.[f]||DATA.size)]")
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--spec", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        result = run(args.root, args.spec, args.output)
    except (ValueError, OSError, KeyError, cv2.error) as e:
        p.exit(1, f"Scene extension failed: {e}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
