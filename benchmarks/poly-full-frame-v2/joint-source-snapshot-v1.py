"""Build a scoped AA/POLY comparison from declared photo correspondences.

Called by poly_full_frame when joint_checks is supplied. Uses existing AA source
geometry and regular layout; new cross-layer mapping remains an AI candidate.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Point, Polygon, box

from .aa_completion import source_polygon
from .aa_layer_revision import canonical_layout
from .geometry_reconstruction import digest, object_polygon, orthogonal_fit, project
from .scene_geometry import load_locked


def joint_review(root, spec, objects, output):
    """Require independent check points before drawing the provisional local overlay."""
    settings = spec["joint_checks"]
    aa_model = load_locked(root, spec["aa_model"])
    group = next(g for g in aa_model["groups"] if g["id"] == settings["aa_group"])
    matrix = cv2.getPerspectiveTransform(
        np.float32(settings["poly_fit_points"]), np.float32(settings["aa_fit_points"])
    )
    errors = np.linalg.norm(
        project(settings["poly_check_points"], matrix) - np.array(settings["aa_check_points"]),
        axis=1,
    )
    folder = Path(output) / "joint"
    folder.mkdir()
    report = dict(
        status="AI_local_registration_candidate_requires_review",
        poly_to_aa_native=matrix.tolist(),
        check_errors_px=errors.tolist(),
        budget_px=settings["max_check_error_px"],
        control_points=settings,
        geometric_check_pass=bool(errors.max() <= settings["max_check_error_px"]),
        human_accepted=False,
        source_scope=settings["scope"],
        photos_not_warped_into_material_truth=True,
    )
    if not report["geometric_check_pass"]:
        report["status"] = "registration_check_failed_overlay_not_drawn"
        (folder / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        return report
    members = [o for o in aa_model["objects"] if o["id"] in group["members"]]
    aa_bodies = [o for o in members if "GUARD" not in o["id"]]
    raw_polygons = {o["id"]: source_polygon(o, aa_model) for o in members}
    slots = {}
    for g in spec["groups"]:
        for index in range(g["count"]):
            slots[
                g["approved_slots"].get(
                    str(index), f"{g.get('id_prefix', g['id'])}-P{index + 1:02}"
                )
            ] = (
                g["id"],
                index,
            )
    derived = []
    for obj in objects:
        native = np.array(obj["native_outline"])
        if not Polygon(native).intersects(box(*settings["joint_plot_bbox_poly"])):
            continue
        if obj["id"] not in slots or slots[obj["id"]][0] not in settings["poly_group_ids"]:
            continue
        aa_native = project(native, matrix)
        center = Point(aa_native.mean(0))
        member = min(aa_bodies, key=lambda o: raw_polygons[o["id"]].distance(center))
        distance = raw_polygons[member["id"]].distance(center)
        within_body_budget = distance <= settings["max_body_assignment_distance_px"]
        src = np.array(raw_polygons[member["id"]].exterior.coords[:-1])
        target = np.array(object_polygon(member).exterior.coords[:-1])
        if within_body_budget and len(src) == 4 and len(target) == 4:
            correspondence = cv2.getPerspectiveTransform(
                src.astype(np.float32), target.astype(np.float32)
            )
            polygon = project(aa_native, correspondence)
            method = "per_AA_body_recorded_corner_correspondence"
        else:
            canonical = project(aa_native, np.linalg.inv(np.array(group["canonical_to_source"])))
            polygon = canonical_layout(canonical, group)
            method = "recorded_AA_group_source_homography_plus_separable_layout_axes"
        edges = np.roll(polygon, -1, axis=0) - polygon
        axes = ["H" if abs(d[0]) > abs(d[1]) else "V" for d in edges]
        regular = orthogonal_fit(polygon, axes)
        derived.append(
            dict(
                source_poly_id=obj["id"],
                group_id=slots[obj["id"]][0],
                group_index=slots[obj["id"]][1],
                aa_object_id=member["id"] if within_body_budget else None,
                aa_assignment_distance_px=float(distance),
                aa_body_assignment_within_budget=within_body_budget,
                aa_native_outline=aa_native.tolist(),
                joint_layout_outline=regular.tolist(),
                original_source_geometry_unchanged=True,
                source_to_joint_method=method,
                status="derived_joint_geometry_candidate_not_adopted",
            )
        )
    # Column constraints are explicit design relations, not inferred from image slant.
    for relation in spec.get("cross_row_alignment_sets", []):
        reference = {d["group_index"]: d for d in derived if d["group_id"] == relation["reference"]}
        for obj in derived:
            if obj["group_id"] not in relation["groups"] or obj["group_index"] not in reference:
                continue
            p = np.array(obj["joint_layout_outline"])
            q = np.array(reference[obj["group_index"]]["joint_layout_outline"])
            if p.shape == q.shape:
                p[:, 0] = q[:, 0]
                obj["joint_layout_outline"] = p.tolist()
    report["derived_objects"] = derived
    report["AA_relation_warnings"] = [
        d["source_poly_id"] for d in derived if not d["aa_body_assignment_within_budget"]
    ]
    report["derived_scope"] = (
        "LOWER-MOS-GRID; AA layout stays unchanged; original reviewed POLY unchanged"
    )
    report["composed_by"] = (
        "POLY native -> candidate AA native -> per-AA-body recorded layout correspondence"
    )
    poly = cv2.imread(str(Path(root) / spec["source"]["path"]))
    aa = cv2.imread(str(Path(root) / spec["aa_source"]["path"]))
    x, y, r, b = settings["joint_plot_bbox_poly"]
    poly_crop = poly[y:b, x:r].copy()
    overlay = poly_crop.copy()
    inverse = np.linalg.inv(matrix)
    for obj in members:
        polygon = raw_polygons[obj["id"]]
        for ring in [polygon.exterior, *polygon.interiors]:
            points = np.rint(project(np.array(ring.coords), inverse) - [x, y]).astype(np.int32)
            cv2.polylines(overlay, [points], True, (65, 225, 65), 2, cv2.LINE_AA)
    for obj in objects:
        if not Polygon(obj["native_outline"]).intersects(box(x, y, r, b)):
            continue
        points = np.rint(np.array(obj["native_outline"]) - [x, y]).astype(np.int32)
        cv2.polylines(overlay, [points], True, (245, 175, 25), 2, cv2.LINE_AA)
    aa_bounds = project([[x, y], [r, y], [r, b], [x, b]], matrix)
    ax, ay = np.maximum(0, np.floor(aa_bounds.min(0)).astype(int))
    ar, ab = np.minimum([aa.shape[1], aa.shape[0]], np.ceil(aa_bounds.max(0)).astype(int))
    for name, im in [
        ("poly-source", poly_crop),
        ("aa-source", aa[ay:ab, ax:ar]),
        ("source-overlay", overlay),
    ]:
        cv2.imwrite(str(folder / (name + ".jpg")), im, [cv2.IMWRITE_JPEG_QUALITY, 95])
    report["raw_crop_boxes"] = dict(poly=[x, y, r, b], aa=[int(ax), int(ay), int(ar), int(ab)])
    # Show unwarped control-point images with corresponding IDs for human verification.
    for name, im, origin, fit, checks in [
        (
            "poly-anchors",
            poly_crop,
            [x, y],
            settings["poly_fit_points"],
            settings["poly_check_points"],
        ),
        (
            "aa-anchors",
            aa[ay:ab, ax:ar],
            [ax, ay],
            settings["aa_fit_points"],
            settings["aa_check_points"],
        ),
    ]:
        marked = im.copy()
        for prefix, points in [("A", fit), ("C", checks)]:
            for index, point in enumerate(points):
                px, py = np.rint(np.array(point) - origin).astype(int)
                cv2.circle(marked, (px, py), 8, (20, 200, 255), 2)
                cv2.putText(
                    marked,
                    f"{prefix}{index + 1}",
                    (px + 9, py + 12),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (20, 200, 255),
                    2,
                )
        cv2.imwrite(str(folder / (name + ".jpg")), marked, [cv2.IMWRITE_JPEG_QUALITY, 95])
    all_bounds = np.array([object_polygon(o).bounds for o in members])
    left, top = all_bounds[:, :2].min(0) - 20
    right, bottom = all_bounds[:, 2:].max(0) + 20
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{left} {top} {right - left} {bottom - top}">'
        f'<rect x="{left}" y="{top}" width="{right - left}" '
        f'height="{bottom - top}" fill="#14202c"/>'
    )
    for obj in members:
        polygon = object_polygon(obj)
        path = ""
        for ring in [polygon.exterior, *polygon.interiors]:
            pts = list(ring.coords)
            path += "M" + " L".join(f"{a},{b}" for a, b in pts) + " Z "
        svg += (
            f'<path d="{path}" fill="#56b76a" fill-opacity=".4" '
            'fill-rule="evenodd" stroke="#78dc80"/>'
        )
    for obj in derived:
        pts = " ".join(f"{a},{b}" for a, b in obj["joint_layout_outline"])
        style = (
            'fill="#51bffa" fill-opacity=".65" stroke="#a0e4ff"'
            if obj["aa_body_assignment_within_budget"]
            else 'fill="#f1a33f" fill-opacity=".5" stroke="#ffd191" stroke-dasharray="5 3"'
        )
        svg += f'<polygon points="{pts}" {style}/' + ">"
    (folder / "joint-layout.svg").write_text(svg + "</svg>")
    report["aa_model_sha256"] = digest(Path(root) / spec["aa_model"]["path"])
    (folder / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report
