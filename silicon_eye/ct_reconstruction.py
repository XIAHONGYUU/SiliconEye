"""Evidence-first CT pilot on a locked AA/POLY baseline.

Run: python -m silicon_eye.ct_reconstruction --spec SPEC --output NEW_DIR
Requires the project environment. Rules check proposals; they never create missing holes.
"""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

from .geometry_reconstruction import object_polygon, project
from .poly_closeout import svg
from .scene_geometry import extract_peaks, load_locked, regularize_axis

COLORS = {"AA_candidate": "#4de1c1", "POLY_candidate": "#65baff", "unknown": "#ffc56b"}


def landing(footprint, aa, poly, enclosure=1):
    """Check complete cut, not just its center; ambiguous/channel cuts remain unknown."""
    if footprint.intersection(aa).area > 0 and footprint.intersection(poly).area > 0:
        return "unknown", "mixed_or_channel_overlap"
    if aa.buffer(-enclosure).covers(footprint):
        return "AA_candidate", "AA_enclosure_candidate"
    if poly.buffer(-enclosure).covers(footprint):
        return "POLY_candidate", "POLY_enclosure_candidate"
    return "unknown", "no_unique_enclosed_landing"


def regularize(points, settings):
    """Constrain only observed centers; return a reversible limited adjustment."""
    points = np.asarray(points, float).reshape(-1, 2)
    result = points.copy()
    for axis in range(2):
        result[:, axis], _ = regularize_axis(points[:, axis], settings)
    shift = np.linalg.norm(result - points, axis=1)
    result[shift > settings["max_regularization_shift"]] = points[
        shift > settings["max_regularization_shift"]
    ]
    return result


def supplement_peaks(crop, observations, origin, settings):
    """Keep real bright peaks missed by compact-shape filtering near supported rows.

    Two nearby compact observations must support the row/column. These supplementary
    observations stay unknown: row support does not establish contact identity.
    """
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray, (5, 5), 1)
    residual = smooth.astype(float) - cv2.GaussianBlur(smooth, (0, 0), 4)
    maxima = (
        (smooth == cv2.dilate(smooth, np.ones((settings["neighborhood"],) * 2, np.uint8)))
        & (smooth >= settings["peak_gray"])
        & (residual >= settings["peak_residual"])
    ).astype(np.uint8)
    border = settings["crop_border_px"]
    maxima[:border] = maxima[-border:] = 0
    maxima[:, :border] = maxima[:, -border:] = 0
    count, _, stats, centers = cv2.connectedComponentsWithStats(maxima)
    strict = np.array([o["source_native_center_xy"] for o in observations]).reshape(-1, 2)
    result = list(observations)
    if not len(strict):
        return result
    for i in range(1, count):
        if max(stats[i, 2:4]) > settings["max_peak_plateau_span"]:
            continue
        native = centers[i] + np.asarray(origin)
        delta = np.abs(strict - native)
        if np.min(np.linalg.norm(delta, axis=1)) < settings["duplicate_radius"]:
            continue
        row = (delta[:, 0] < settings["neighbor_radius"]) & (
            delta[:, 1] < settings["axis_tolerance"]
        )
        col = (delta[:, 1] < settings["neighbor_radius"]) & (
            delta[:, 0] < settings["axis_tolerance"]
        )
        if max(int(row.sum()), int(col.sum())) < settings["min_neighbors"]:
            continue
        if any(
            np.linalg.norm(native - o["source_native_center_xy"]) < settings["duplicate_radius"]
            for o in result
        ):
            continue
        x, y = np.rint(centers[i]).astype(int)
        result.append(
            dict(
                source_native_center_xy=native.tolist(),
                peak_gray=int(smooth[y, x]),
                local_residual=float(residual[y, x]),
                detector="relaxed_shape_observed_peak_two_neighbor_axis_support",
            )
        )
    return result


def build_candidates(observations, model, layout_to_native, settings, scope):
    aa = unary_union([object_polygon(o) for o in model["AA_objects"]])
    poly_geometries = [Polygon(o["layout_outline"]) for o in model["objects"]]
    poly = unary_union(poly_geometries)
    aa_geometries = [object_polygon(o) for o in model["AA_objects"]]
    aa_tree, poly_tree = STRtree(aa_geometries), STRtree(poly_geometries)
    # Global transform remains provisional. No local warp is inferred from bright points.
    matrix = np.linalg.inv(np.asarray(layout_to_native, float))
    native = np.array([o["source_native_center_xy"] for o in observations]).reshape(-1, 2)
    projected = project(native, matrix) if len(native) else native
    if settings.get("allow_regularization") and not settings.get("local_family_reviewed"):
        raise ValueError("Local family review required before CT pitch regularization")
    adjusted = (
        regularize(projected, settings)
        if settings.get("allow_regularization")
        else projected.copy()
    )
    records = []
    for i, (observation, before, center) in enumerate(
        zip(observations, projected, adjusted, strict=True), 1
    ):
        side = settings["square_side"]
        footprint = box(
            center[0] - side / 2, center[1] - side / 2, center[0] + side / 2, center[1] + side / 2
        )
        kind, reason = landing(footprint, aa, poly, settings["enclosure_px"])
        tier = "relaxed_shape" if observation.get("detector") else "compact_shape"
        if tier == "relaxed_shape":
            kind, reason = "unknown", "observed_peak_but_compact_shape_unverified"
        records.append(
            dict(
                id=f"CT-{scope}-{i:04}",
                layer="CT",
                status="AI_candidate_not_human_reviewed",
                source_frame="poly",
                source_observation=observation,
                evidence_tier=tier,
                observed_layout_center=before.tolist(),
                layout_center=center.tolist(),
                layout_outline=list(map(list, footprint.exterior.coords[:-1])),
                regularization_shift_px=float(np.linalg.norm(center - before)),
                landing_hypothesis=kind,
                rule_finding=reason,
                AA_candidates=[
                    model["AA_objects"][j]["id"]
                    for j in aa_tree.query(footprint)
                    if aa_geometries[j].intersection(footprint).area > 0
                ],
                POLY_candidates=[
                    model["objects"][j]["id"]
                    for j in poly_tree.query(footprint)
                    if poly_geometries[j].intersection(footprint).area > 0
                ],
                assignment_status="unknown_pending_local_registration_and_material_review",
                projection_status="inherited_global_provisional_not_new_registration",
                upper_M1_enclosure="unknown_not_tested",
                net_id=None,
            )
        )
    # Never move/resize cuts to make this check pass; preserve conflict for review.
    shapes = [Polygon(o["layout_outline"]) for o in records]
    tree = STRtree(shapes)
    conflicts = []
    for i, shape in enumerate(shapes):
        for j in tree.query(shape.buffer(settings["min_gap_px"])):
            if j > i and shape.distance(shapes[j]) < settings["min_gap_px"]:
                conflicts.append([records[i]["id"], records[j]["id"]])
    return records, conflicts


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output)
    if output.exists():
        raise ValueError("Output must be new; preserve previous evidence")
    spec = json.loads(Path(spec_path).read_text())
    model = load_locked(root, spec["inputs"]["baseline"])
    aa_source = load_locked(root, spec["inputs"]["AA_projection"])
    acceptance = load_locked(root, spec["inputs"]["baseline_acceptance"])
    if acceptance["locked_files"]["model-v1.json"] != spec["inputs"]["baseline"]["sha256"]:
        raise ValueError("Baseline differs from accepted stage lock")
    # Verify source bytes without interpreting the photograph as JSON.
    from .geometry_reconstruction import digest

    source = spec["inputs"]["photo"]
    if digest(root / source["path"]) != source["sha256"]:
        raise ValueError("Changed source photograph")
    image = cv2.imread(str(root / source["path"]))
    if image is None:
        raise ValueError("Missing source photograph")
    output.mkdir(parents=True)
    matrix = aa_source["projection_matrices"]["global"]["poly"]
    all_records, report_scopes, cards = [], [], []
    for scope in spec["scopes"]:
        key = scope["id"]
        left, top, right, bottom = scope["native_bbox"]
        valid = np.zeros(image.shape[:2], bool)
        valid[top:bottom, left:right] = True
        # Reuse existing, previously reviewed detector profile; no whole-layer rerun.
        compact = extract_peaks(image, valid, spec["detector"])
        observed = supplement_peaks(
            image[top:bottom, left:right], compact, [left, top], spec["supplement"]
        )
        records, conflicts = build_candidates(observed, model, matrix, spec["geometry"], key)
        all_records.extend(records)
        raw = Image.fromarray(cv2.cvtColor(image[top:bottom, left:right], cv2.COLOR_BGR2RGB))
        raw.save(output / f"{key}-raw.png")
        layers = []
        for kind, color in COLORS.items():
            rects = []
            for record in records:
                if record["landing_hypothesis"] != kind:
                    continue
                x, y = record["source_observation"]["source_native_center_xy"]
                rects.append(
                    f'<rect x="{x - left - 5}" y="{y - top - 5}" width="10" '
                    f'height="10"><title>{record["id"]}</title></rect>'
                )
            layers.append(
                f'<g data-layer="{kind}" fill="none" stroke="{color}" '
                f'stroke-width="1.5">' + "".join(rects) + "</g>"
            )
        source_svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {right - left} {bottom - top}">'
            f'<image href="{key}-raw.png" width="{right - left}" '
            f'height="{bottom - top}"/>' + "".join(layers) + "</svg>"
        )
        (output / f"{key}-source.svg").write_text(source_svg)
        strict_rects = []
        for record in records:
            if record["evidence_tier"] != "compact_shape":
                continue
            x, y = record["source_observation"]["source_native_center_xy"]
            strict_rects.append(
                f'<rect x="{x - left - 5}" y="{y - top - 5}" width="10" '
                f'height="10" fill="none" stroke="#ffc56b"/>'
            )
        strict_svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {right - left} {bottom - top}">'
            f'<image href="{key}-raw.png" width="{right - left}" '
            f'height="{bottom - top}"/>' + "".join(strict_rects) + "</svg>"
        )
        (output / f"{key}-strict.svg").write_text(strict_svg)
        corners = np.array([[left, top], [right, top], [right, bottom], [left, bottom]], float)
        projected = project(corners, np.linalg.inv(matrix))
        bounds = [*projected.min(axis=0), *projected.max(axis=0)]
        design = svg(model, bounds)
        cuts = "".join(
            '<polygon points="'
            + " ".join(f"{x},{y}" for x, y in r["layout_outline"])
            + f'" fill="none" stroke="{COLORS[r["landing_hypothesis"]]}" '
            + f'stroke-width="1.5"><title>{r["id"]}</title></polygon>'
            for r in records
        )
        (output / f"{key}-layout.svg").write_text(design.replace("</svg>", cuts + "</svg>"))
        counts = dict(Counter(r["landing_hypothesis"] for r in records))
        evidence_counts = dict(Counter(r["evidence_tier"] for r in records))
        report_scopes.append(
            dict(
                id=key,
                observations=len(observed),
                hypotheses=counts,
                evidence_tiers=evidence_counts,
                spacing_conflicts=conflicts,
            )
        )
        cards.append(
            f"<section><h2>{key} {html.escape(scope['title'])}</h2>"
            f"<p>{html.escape(scope['review_focus'])}；观察点{len(records)}。"
            "颜色仅为投影假设，所有归属待核。</p>"
            f"<select onchange=\"document.getElementById('{key}').src=this.value\">"
            + "".join(
                f'<option value="{key}-{mode}.{ext}">{label}</option>'
                for mode, ext, label in [
                    ("source", "svg", "原图＋孔候选"),
                    ("strict", "svg", "原紧凑形状检测（对照）"),
                    ("raw", "png", "纯原图"),
                    ("layout", "svg", "规则AA/POLY＋孔投影（待配准）"),
                ]
            )
            + f'</select><img id="{key}" src="{key}-source.svg"></section>'
        )
    page = "".join(cards)
    (output / "index.html").write_text(
        """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>CT规则约束试验 v1</title><style>body{background:#111c28;color:#eee;font:16px sans-serif;
max-width:1500px;margin:24px auto}section{padding:16px;border:1px solid #567;margin:20px 0}
img{display:block;width:100%;image-rendering:auto}select{padding:8px}a{color:#65baff}</style>
<h1>历史算法观察诊断：不是CT重建验收稿</h1>
<p>整体几何质量未通过，亮点框不得用作重建孔层。</p>
<p>青绿＝AA落点假设；蓝＝POLY落点假设；橙＝无包围/沟道交叠/归属未知。
框为亮点定位，不代表实际孔边界。设计视图为继承全局投影，未获局部落点验收，不可据此判定连接。</p>
<p>仅四类小样本；不自动补齐孔，不以阵列先验代替观察，不修改已审AA/POLY。
所有CT归属和M1包围仍未知。尚未确认局部对应和同组孔列，因此不执行全区等间距吸附。
<a href="report.json">检查报告</a></p>"""
        + page
        + "</html>"
    )
    if digest(root / spec["inputs"]["baseline"]["path"]) != spec["inputs"]["baseline"]["sha256"]:
        raise ValueError("Baseline changed during CT run")
    report = dict(
        implementation_sha256=digest(Path(__file__)),
        stage="local_CT_pilot_not_fullframe_release",
        scopes=report_scopes,
        observed_candidates=len(all_records),
        baseline_unchanged=True,
        new_holes_from_rules=0,
        primitive_status="PASS_square_primitives",
        geometry_status="FAIL_spacing"
        if any(s["spacing_conflicts"] for s in report_scopes)
        else "HOLD_landing",
        reconstruction_export_allowed=False,
        spacing_status="HOLD_conflicts_not_automatically_deleted"
        if any(s["spacing_conflicts"] for s in report_scopes)
        else "PASS_relative_budget_only",
        release_status="HOLD_local_projection_and_landing_review",
        real_PDK_DRC="not_run_process_and_scale_unknown",
        M1_enclosure="not_checked",
        fullframe_coverage=False,
        counts_are_physical_contacts=False,
        baseline_ref=spec["inputs"]["baseline"],
    )
    for name, value in [
        ("model", dict(schema_version=1, objects=all_records)),
        ("report", report),
        ("spec", spec),
    ]:
        (output / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
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
