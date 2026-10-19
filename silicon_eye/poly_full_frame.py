"""Expand AI-declared full-frame POLY observations without replacing reviewed objects.

Run: python -m silicon_eye.poly_full_frame --root . --spec SPEC --output NEW_DIR
Requires the project OpenCV/NumPy/Shapely environment. This renderer is not a
material detector: counts, full-body observations and unresolved scope are inputs.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon, box
from shapely.strtree import STRtree

from .geometry_reconstruction import digest, project
from .scene_geometry import load_locked


def build_geometry(spec, accepted, parent=None):
    """Retain adopted geometry and fit regular array candidates in a common atlas."""
    objects = copy.deepcopy(accepted["objects"])
    approved = {o["id"]: o for o in objects}
    if len(approved) != len(objects):
        raise ValueError("Duplicate accepted IDs")
    used_slots = set()
    for group in spec["groups"]:
        count = group["count"]
        if count < 1:
            raise ValueError("Empty observation group")
        first = np.array(group["first_native_outline"], float)
        last = np.array(group["last_native_outline"], float)
        if first.shape != (4, 2) or last.shape != (4, 2):
            raise ValueError("Expected ordered source quadrilaterals")
        widths = [np.mean(q[[1, 2], 0]) - np.mean(q[[0, 3], 0]) for q in [first, last]]
        width = round(float(np.mean(widths)))
        centers = [float(q[:, 0].mean()) for q in [first, last]]
        top, bottom = group["layout_y"]
        if width <= 0 or bottom <= top:
            raise ValueError("Collapsed group body")
        if count > 1 and (centers[1] - centers[0]) / (count - 1) <= width:
            raise ValueError("Group pitch would merge adjacent bodies")
        for index in range(count):
            slot = str(index)
            if slot in group["approved_slots"]:
                obj_id = group["approved_slots"][slot]
                if obj_id not in approved or obj_id in used_slots:
                    raise ValueError("Missing or reused approved object")
                used_slots.add(obj_id)
                continue
            fraction = 0 if count == 1 else index / (count - 1)
            native = first * (1 - fraction) + last * fraction
            # Half pixels allow one exact common pitch without accumulating roundoff.
            center = centers[0] * (1 - fraction) + centers[1] * fraction
            layout = np.array(
                [
                    [center - width / 2, top],
                    [center + width / 2, top],
                    [center + width / 2, bottom],
                    [center - width / 2, bottom],
                ]
            )
            if not Polygon(native).is_valid or Polygon(native).area <= 0:
                raise ValueError("Invalid source body")
            matrix = cv2.getPerspectiveTransform(
                native.astype(np.float32), layout.astype(np.float32)
            )
            if np.max(np.abs(project(native, matrix) - layout)) > 0.003:
                raise ValueError("Invalid source-to-layout correspondence")
            objects.append(
                dict(
                    id=f"{group.get('id_prefix', group['id'])}-P{index + 1:02}",
                    group_id=group["id"],
                    group_index=index,
                    kind=group["kind"],
                    material="poly",
                    status="AI_candidate_not_human_confirmed",
                    native_outline=native.tolist(),
                    layout_outline=layout.tolist(),
                    native_to_layout=matrix.tolist(),
                    source_method=group["method"],
                    extent=group["body_scope"],
                    terminal_routing="unknown_not_completed_by_repetition",
                )
            )
    apply_layout_constraints(objects, spec, parent)
    ids = [o["id"] for o in objects]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate output IDs")
    polygons = [Polygon(o["layout_outline"]) for o in objects]
    tree = STRtree(polygons)
    overlaps = []
    for i, polygon in enumerate(polygons):
        if not polygon.is_valid or polygon.area <= 0:
            raise ValueError("Invalid layout polygon")
        edges = np.roll(np.array(objects[i]["layout_outline"]), -1, axis=0) - np.array(
            objects[i]["layout_outline"]
        )
        if not np.all((np.abs(edges[:, 0]) < 1e-8) | (np.abs(edges[:, 1]) < 1e-8)):
            raise ValueError("Nonorthogonal output")
        for j in tree.query(polygon):
            if j < i and polygon.intersection(polygons[j]).area > 1e-7:
                overlaps.append([objects[i]["id"], objects[j]["id"]])
    return objects, overlaps


def apply_layout_constraints(objects, spec, parent=None):
    """Tie matching rows in layout while leaving original photo coordinates intact."""
    by_id = {o["id"]: o for o in objects}
    groups = {g["id"]: g for g in spec["groups"]}
    old_by_id = {} if parent is None else {o["id"]: o for o in parent["objects"]}

    def member(group, index):
        obj_id = group["approved_slots"].get(
            str(index), f"{group.get('id_prefix', group['id'])}-P{index + 1:02}"
        )
        return by_id[obj_id]

    for group in groups.values():
        if group.get("freeze_geometry_from_parent"):
            for index in range(group["count"]):
                obj = member(group, index)
                if obj["id"] not in old_by_id:
                    raise ValueError("Missing parent for reviewed scoped geometry")
                frozen = copy.deepcopy(old_by_id[obj["id"]])
                obj.clear()
                obj.update(frozen)
                obj["approval"] = "human_accepted_displayed_scope_not_pixel_truth"
                obj["approval_source"] = group["approval_ref"]
                obj["status"] = "human_accepted_displayed_geometry"
        if group.get("layout_lock_from_parent"):
            for index in range(group["count"]):
                obj = member(group, index)
                if obj["id"] not in old_by_id:
                    raise ValueError("Missing parent for locked layout")
                obj["layout_outline"] = copy.deepcopy(old_by_id[obj["id"]]["layout_outline"])
                obj["layout_status"] = "parent_reviewed_material_body_retained"
                obj["material_body_review"] = "human_confirmed_v1_body_and_count"
                obj["source_projection_review"] = "new_candidate_not_accepted"
    for relation in spec.get("cross_row_alignment_sets", []):
        reference = groups[relation["reference"]]
        for gid in relation["groups"]:
            group = groups[gid]
            if group["count"] != reference["count"]:
                raise ValueError("Matched rows have inconsistent slot counts")
            for index in range(group["count"]):
                target = np.asarray(member(reference, index)["layout_outline"], float)
                obj = member(group, index)
                current = np.asarray(obj["layout_outline"], float)
                if "approval" in obj:
                    if not np.allclose(current[:, 0], target[:, 0]):
                        raise ValueError("Constraint would change reviewed geometry")
                    continue
                current[:, 0] = target[:, 0]
                obj["layout_outline"] = current.tolist()
                obj["cross_row_constraint"] = relation["id"]
    for obj in objects:
        if "approval" in obj:
            continue
        native = np.asarray(obj["native_outline"], float)
        layout = np.asarray(obj["layout_outline"], float)
        matrix = cv2.getPerspectiveTransform(native.astype(np.float32), layout.astype(np.float32))
        group = groups[obj["group_id"]]
        extension = group.get("end_extension")
        if extension:
            x, y, r, b = Polygon(layout).bounds
            length = extension["length_px"]
            if (
                extension.get("shape", "rectangle") != "rectangle"
                or extension.get("width_factor", 1) != 1
            ):
                raise ValueError(
                    "Widened MOS templates withdrawn; require separately observed geometry"
                )
            side = extension["side"]
            if side == "alternating":
                side = "bottom" if obj["group_index"] % 2 == 0 else "top"
            if side not in {"top", "bottom"}:
                raise ValueError("Unsupported terminal extension side")
            if side == "bottom":
                b += length
            else:
                y -= length
            outline = np.array([[x, y], [r, y], [r, b], [x, b]])
            obj["body_layout_outline"] = layout.tolist()
            obj["body_native_outline"] = native.tolist()
            obj["layout_outline"] = outline.tolist()
            obj["native_outline"] = project(outline, np.linalg.inv(matrix)).tolist()
            obj["terminal_shape_status"] = extension["status"]
            obj["terminal_extension_side"] = side
            obj["terminal_routing"] = "material_extension_candidate_no_CT_or_net_assignment"
        obj["native_to_layout"] = matrix.tolist()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def color(obj):
    if "approval" in obj:
        return (85, 225, 85)
    if obj.get("kind") == "resistor_POLY_body_candidate":
        return (220, 120, 215)
    return (245, 175, 25)


def raster_view(source, objects, unresolved, bbox):
    x, y, right, bottom = bbox
    image = source[y:bottom, x:right].copy()
    area = box(*bbox)
    for obj in objects:
        if not Polygon(obj["native_outline"]).intersects(area):
            continue
        p = np.rint(np.array(obj["native_outline"]) - [x, y]).astype(np.int32)
        cv2.polylines(image, [p], True, color(obj), 2, cv2.LINE_AA)
    for region in unresolved:
        if not box(*region["bbox"]).intersects(area):
            continue
        left, top, r, b = region["bbox"]
        # This is a navigation box, never rasterized as a material support.
        cv2.rectangle(image, (left - x, top - y), (r - x, b - y), (10, 150, 245), 2)
        anchor = (max(4, left - x + 4), max(18, top - y + 20))
        cv2.putText(
            image,
            region["id"],
            anchor,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (10, 150, 245),
            2,
            cv2.LINE_AA,
        )
    return image


def layout_svg(objects, bbox):
    x, y, r, b = bbox
    area = box(*bbox)
    text = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{x} {y} {r - x} {b - y}">'
        f'<rect x="{x}" y="{y}" width="{r - x}" height="{b - y}" fill="#111b26"/>'
    )
    for obj in objects:
        if not Polygon(obj["layout_outline"]).intersects(area):
            continue
        pts = " ".join(f"{a},{b}" for a, b in obj["layout_outline"])
        blue, green, red = color(obj)
        text += (
            f'<polygon points="{pts}" fill="rgb({red},{green},{blue})" '
            'fill-opacity=".65" stroke="#a4dfff" stroke-width="1"/>'
        )
    return text + "</svg>"


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(Path(spec_path).read_text())
    baseline = load_locked(root, spec["baseline"])
    for item in baseline["references"].values():
        if digest(root / item["path"]) != item["sha256"]:
            raise ValueError("Changed frozen baseline: " + item["path"])
    accepted = load_locked(root, spec["accepted_local_model"])
    load_locked(root, spec["region_context"])
    for ref in [spec["source"], spec["aa_source"]]:
        if digest(root / ref["path"]) != ref["sha256"]:
            raise ValueError("Changed photograph")
    parent = load_locked(root, spec["parent_model"]) if "parent_model" in spec else None
    if "feedback" in spec:
        load_locked(root, spec["feedback"])
    objects, overlaps = build_geometry(spec, accepted, parent)
    if overlaps:
        raise ValueError("Candidate layout overlap: " + str(overlaps))
    source = cv2.imread(str(root / spec["source"]["path"]))
    aa = cv2.imread(str(root / spec["aa_source"]["path"]))
    width, height = spec["native_canvas_wh"]
    if source.shape[:2] != (height, width) or aa.shape[:2] != (height, width):
        raise ValueError("Canvas mismatch")
    output.mkdir(parents=True)
    grid = spec["review_grid"]
    frames = [dict(id="ALL", bbox=[0, 0, width, height], aa_context_bbox=[0, 0, width, height])]
    for row in range(grid["rows"]):
        for col in range(grid["columns"]):
            bbox = [
                round(width * col / grid["columns"]),
                round(height * row / grid["rows"]),
                round(width * (col + 1) / grid["columns"]),
                round(height * (row + 1) / grid["rows"]),
            ]
            # Coarse native crop navigation only; not a point transform or overlay.
            shift_x, shift_y = spec["aa_context_navigation_offset_xy"]
            ax, ay = min(width - 1, bbox[0] + shift_x), min(height - 1, bbox[1] + shift_y)
            aa_bbox = [ax, ay, min(width, bbox[2] + shift_x), min(height, bbox[3] + shift_y)]
            frames.append(
                dict(
                    id=f"F{row * grid['columns'] + col + 1:02}", bbox=bbox, aa_context_bbox=aa_bbox
                )
            )
    frames.extend(copy.deepcopy(spec.get("additional_review_windows", [])))
    for frame in frames:
        folder = output / frame["id"]
        folder.mkdir()
        x, y, r, b = frame["bbox"]
        raw = source[y:b, x:r]
        overlay = raster_view(source, objects, spec["unresolved"], frame["bbox"])
        ax, ay, ar, ab = frame["aa_context_bbox"]
        aa_crop = aa[ay:ab, ax:ar]
        scale = min(1, 1600 / (r - x))
        aa_scale = min(1, 1600 / (ar - ax))
        frame["display_scale"] = scale
        frame["aa_display_scale"] = aa_scale
        for name, im, factor in [
            ("source", raw, scale),
            ("overlay", overlay, scale),
            ("aa", aa_crop, aa_scale),
        ]:
            if factor < 1:
                im = cv2.resize(im, None, fx=factor, fy=factor, interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(folder / f"{name}.jpg"), im, [cv2.IMWRITE_JPEG_QUALITY, 94])
        (folder / "layout.svg").write_text(layout_svg(objects, frame["bbox"]))
        frame["objects"] = [
            o["id"] for o in objects if Polygon(o["native_outline"]).intersects(box(*frame["bbox"]))
        ]
        frame["unresolved"] = [
            u["id"] for u in spec["unresolved"] if box(*u["bbox"]).intersects(box(*frame["bbox"]))
        ]
    model = dict(
        schema_version=1,
        source=spec["source"],
        native_canvas_wh=[width, height],
        layout_canvas_wh=[width, height],
        objects=objects,
        groups=spec["groups"],
        unresolved=spec["unresolved"],
        outside_geometry="unknown_not_background",
        human_non_POLY_scopes=spec.get("human_non_POLY_scopes", []),
        cross_row_alignment_sets=spec.get("cross_row_alignment_sets", []),
        preserved_unknown_inputs={
            "topology_unknown": baseline["references"]["topology_unknown"],
            "CT_underlying_unknown": baseline["references"]["CT_underlying_unknown"],
            "native_origin_xy": baseline["annotation_crop_poly_xywh"][:2],
            "semantics": "retain_unknown_overrides_if_rasterized; "
            "candidate_polygons_are_not_dense_positive_material_truth",
        },
        CT_assignments=False,
        AA_to_POLY_projection=False,
        coordinate_scope="shared_native_canvas_and_regular_candidate_atlas; "
        "per_object_source_correspondence_not_fullframe_calibration",
    )
    report = dict(
        status="fullframe_first_candidates_with_unresolved_scope_require_review",
        objects=len(objects),
        accepted_retained=sum("approval" in obj for obj in objects),
        original_baseline_retained=len(accepted["objects"]),
        new_candidates=sum("approval" not in obj for obj in objects),
        groups=len(spec["groups"]),
        unresolved_regions=len(spec["unresolved"]),
        unresolved=spec["unresolved"],
        fullframe_complete=False,
        counts_are_not_devices=True,
        overlapping_layout_pairs=overlaps,
        regular_geometry="PASS",
        source=spec["source"],
        AA_unchanged=True,
        frames=frames,
        quality_improvement="not_claimed_before_review",
        count_observation="AI_declared_candidate_counts_not_human_truth",
        cross_row_alignment_sets=spec.get("cross_row_alignment_sets", []),
        human_non_POLY_scopes=spec.get("human_non_POLY_scopes", []),
        fullframe_model_training=False,
        algorithm_material_segmentation=False,
        spec_sha256=digest(spec_path),
        code_sha256=digest(__file__),
        questions=spec["human_questions"],
        AA_navigation="coarse_crop_only_no_pixel_correspondence_or_geometry_projection",
    )
    if "joint_checks" in spec:
        from .poly_aa_joint_review import joint_review

        report["joint_review"] = joint_review(root, spec, objects, output)
        if "forward_layout_constraints" in spec["joint_checks"]:
            model["working_reconstruction_layers"] = {
                "AA": spec["aa_model"],
                "POLY": {
                    "record": "joint/report.json",
                    "objects": "derived_objects[*].joint_layout_outline",
                    "frame": "existing_AA_regular_layout",
                    "scope": spec["joint_checks"]["aa_group"],
                    "status": "AA_relative_design_candidate_not_human_accepted",
                },
                "photo_atlas_role": "source_correspondence_review_not_final_joint_layout",
            }
    save(output / "model.json", model)
    save(output / "report.json", report)
    save(output / "spec.json", spec)
    (output / "data.js").write_text("const DATA=" + json.dumps(report, ensure_ascii=False) + ";\n")
    template = Path(__file__).with_name("poly_full_frame_review.html")
    (output / "index.html").write_text(template.read_text())
    save(
        output / "manifest.json",
        {str(p.relative_to(output)): digest(p) for p in sorted(output.rglob("*")) if p.is_file()},
    )
    return {k: report[k] for k in ["status", "objects", "new_candidates", "unresolved_regions"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.spec, args.output), ensure_ascii=False, indent=2))
