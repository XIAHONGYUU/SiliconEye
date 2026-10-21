"""Revise a full AA geometry layer from locked, scoped AI/human observations.

Run: python -m silicon_eye.aa_layer_revision --root . --spec SPEC --output NEW_DIR
Requires project OpenCV/Shapely. Reuses geometry and optional bounded image-edge
localization; no ML training, CT processing, or automatic semantic recognition.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from .aa_completion import part_polygon, pieces, polygon_record, source_polygon, validate
from .aa_semantic_revision import reconstruct
from .geometry_reconstruction import digest, object_polygon, object_rings, orthogonal_fit, project
from .joint_layers import aa_view, load_snapshot, replace_layer, write_snapshot
from .scene_geometry import load_locked, paint_objects


def canonical_layout(points, group):
    if group["explicit_affine_layout"] is not None:
        return project(points, group["explicit_affine_layout"])
    points = np.asarray(points, float)
    cx, cy = group["axis_reference_xy"]
    matrix = group["layout_axis_matrix"]
    return np.c_[
        project(np.c_[points[:, 0], np.full(len(points), cy)], matrix)[:, 0],
        project(np.c_[np.full(len(points), cx), points[:, 1]], matrix)[:, 1],
    ]


def mapped_polygon(polygon, mapper):
    result = Polygon(
        mapper(polygon.exterior.coords[:-1]), [mapper(h.coords[:-1]) for h in polygon.interiors]
    )
    if not result.is_valid or result.area <= 0:
        raise ValueError("Invalid mapped material")
    return result


def repair_local_edges(raw, locator, details, settings):
    """Retry ambiguous columns near adjacent supported traces, requiring image gradients."""
    radius = locator.get("repair_radius_px")
    if radius is None:
        return details
    result = copy.deepcopy(details)
    case = locator["case"]
    left, top, right, _ = case["native_bbox"]
    xs = np.arange(right - left) + left
    valid = np.isin(xs, details["eligible_native_x"])
    if valid.sum() < 2:
        return result
    support = {}
    scaled_x = (xs - xs.mean()) / max(float(np.ptp(xs)), 1)
    for curve in case["curves"]:
        path = np.asarray(details["paths_native_y"][curve["id"]])
        keep = valid.copy()
        for _ in range(3):
            fit = np.polyfit(scaled_x[keep], path[keep], min(2, int(keep.sum()) - 1))
            residual = np.abs(path - np.polyval(fit, scaled_x))
            limit = max(3.0, 3 * float(np.median(residual[keep])))
            selected = valid & (residual <= limit)
            if selected.sum() < 2:
                break
            keep = selected
        support[curve["id"]] = keep
    valid = np.logical_and.reduce(list(support.values()))
    target = (~valid) & (xs >= case["x_span"][0]) & (xs < case["x_span"][1])
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gradient = np.gradient(cv2.blur(gray, (settings["blur_x"], settings["blur_y"])), axis=0)
    repaired = target.copy()
    candidates = {}
    for curve in case["curves"]:
        if curve["kind"] not in {"rise", "fall"}:
            raise ValueError("Local gradient repair requires explicit rise/fall roles")
        path = np.asarray(details["paths_native_y"][curve["id"]]).copy()
        anchors = support[curve["id"]]
        predicted = np.interp(xs, xs[anchors], path[anchors])
        field = gradient if curve["kind"] == "rise" else -gradient
        for column in np.flatnonzero(target):
            lo = max(0, int(np.floor(predicted[column] - top - radius)))
            hi = min(raw.shape[0], int(np.ceil(predicted[column] - top + radius)) + 1)
            if lo >= hi:
                repaired[column] = False
                continue
            index = int(field[lo:hi, column].argmax()) + lo
            if field[index, column] < settings["min_evidence"]:
                repaired[column] = False
            path[column] = index + top
        candidates[curve["id"]] = path
    ordered = np.array(list(candidates.values()))
    repaired &= np.all(np.diff(ordered, axis=0) > 0, axis=0)
    for name, path in candidates.items():
        old = np.array(result["paths_native_y"][name])
        old[repaired] = path[repaired]
        result["paths_native_y"][name] = old.tolist()
    result["eligible_native_x"] = xs[valid | repaired].tolist()
    result["eligible_columns"] = int((valid | repaired).sum())
    result["locally_repaired_columns"] = int(repaired.sum())
    result["local_repair_scope"] = "image-supported retry near robust neighboring traces; not truth"
    return result


def edge_warp(locator, details):
    """Use valid ordered edge evidence only; unsupported columns stay explicitly reported."""
    anchors = np.asarray(locator["canonical_anchor_y"], float)
    left, _, right, _ = locator["case"]["native_bbox"]
    paths = details["paths_native_y"]
    target = np.vstack(
        [
            np.full(right - left, y) if name is None else np.asarray(paths[name])
            for y, name in zip(anchors, locator["curve_ids"], strict=True)
        ]
    )
    valid = np.zeros(right - left, bool)
    valid[np.array(details["eligible_native_x"], dtype=int) - left] = True
    valid &= np.all(np.diff(target, axis=0) > 0, axis=0)
    target[:, ~valid] = anchors[:, None]

    def points_warp(points):
        points = np.asarray(points, float)
        # Densify affected source edges, without changing layout geometry.
        dense = []
        for first, second in zip(points, np.roll(points, -1, axis=0), strict=True):
            affected = min(first[1], second[1]) <= anchors[-1]
            affected &= max(first[1], second[1]) >= anchors[0]
            count = max(1, int(np.ceil(np.linalg.norm(second - first) / 16))) if affected else 1
            dense.extend(first + (second - first) * t / count for t in range(count))
        dense = np.asarray(dense)
        for point in dense:
            if not anchors[0] <= point[1] <= anchors[-1]:
                continue
            x = np.clip(point[0] - left, 0, right - left - 1)
            column = np.array([np.interp(x, np.arange(right - left), row) for row in target])
            point[1] = np.interp(point[1], anchors, column)
        return dense

    return points_warp, int(valid.sum())


def revise_object(root, obj, base, operation, photo, settings):
    old_source = source_polygon(obj, base)
    if obj['id'] in base.get('source_footprints', {}):
        raise ValueError('Merged AA needs explicit local correspondence before image refinement')
    kind = operation["kind"]
    details = {}
    layout_parts, native_parts = [], []
    if kind in {"canonical_cut", "canonical_rebuild"}:
        group = next(g for g in base["groups"] if g["id"] == obj["structure_group"])
        matrix = np.asarray(group["canonical_to_source"])
        canonical = mapped_polygon(
            old_source, lambda v: np.round(project(v, np.linalg.inv(matrix)), 6)
        )
        if kind == "canonical_cut":
            canonical = canonical.difference(unary_union([box(*b) for b in operation["cut_boxes"]]))
        else:
            canonical = part_polygon(operation["part"])
        segments = sorted(pieces(canonical), key=lambda p: p.area, reverse=True)
        if len(segments) != operation["expected_components"]:
            raise ValueError("Unexpected component change: " + operation["id"])

        def warp(v):
            return np.asarray(v, float)

        if "edge_locator" in operation:
            locator = operation["edge_locator"]
            x, y, r, b = locator["case"]["native_bbox"]
            _, details = reconstruct(photo[y:b, x:r], locator["case"], settings["curve_settings"])
            details = repair_local_edges(
                photo[y:b, x:r], locator, details, settings["curve_settings"]
            )
            warp, valid = edge_warp(locator, details)
            details["warped_evidence_columns"] = valid
            details["unsupported_columns"] = r - x - valid
        for segment in segments:
            layout_parts.append(mapped_polygon(segment, lambda v: canonical_layout(v, group)))
            native_parts.append(mapped_polygon(segment, lambda v: project(warp(v), matrix)))
    elif kind == "approved_polygon":
        candidate = load_locked(root, operation["geometry"])
        review = load_locked(root, operation["review"])
        if review["reviewed_candidate"]["sha256"] != operation["geometry"]["sha256"]:
            raise ValueError("Approval refers to another candidate")
        old_outer, _ = object_rings(obj)
        native_outline = np.asarray(old_source.exterior.coords)[:-1]
        if len(native_outline) != len(old_outer):
            raise ValueError("No explicit corner correspondence")
        matrix, _ = cv2.findHomography(native_outline, np.asarray(old_outer, float), 0)
        if matrix is None:
            raise ValueError("Cannot map approved local outline to existing layout")
        error = np.max(np.linalg.norm(project(native_outline, matrix) - old_outer, axis=1))
        if error > settings["correspondence_residual_limit_px"]:
            raise ValueError("Existing source correspondence is not accurate enough")
        native = np.asarray(candidate["native_outline"])
        native_parts = [Polygon(native)]
        layout_parts = [Polygon(orthogonal_fit(project(native, matrix), operation["axes"]))]
        details = dict(
            source_correspondence_fit_residual_px=float(error),
            approved_native_outline_unchanged=True,
        )
    elif kind == "source_correspondence":
        native_parts = [Polygon(obj["native_corners"], [obj["native_hole_corners"]])]
        layout_parts = [object_polygon(obj)]
        details = dict(
            layout_geometry_unchanged=True,
            source_observation="existing native_corners, not global back-projection",
        )
    else:
        raise ValueError("Unknown revision kind")
    new_source = unary_union(native_parts)
    outside = (
        old_source.symmetric_difference(new_source)
        .difference(box(*operation["allowed_native_bbox"]))
        .area
    )
    if outside > settings["domain_leak_area_px2"]:
        raise ValueError(f"Revision leaves declared scope: {operation['id']} ({outside})")
    result = []
    for i, (layout, native) in enumerate(zip(layout_parts, native_parts, strict=True)):
        identifier = obj["id"] if i == 0 else obj["id"] + f"-split{i:02}"
        item = copy.deepcopy(obj)
        item.update(polygon_record(identifier, layout))
        item["source_geometry"] = dict(
            outer_xy=list(map(list, native.exterior.coords[:-1])),
            holes_xy=[list(map(list, h.coords[:-1])) for h in native.interiors],
        )
        item["working_revision"] = dict(
            id=operation["id"],
            reason=operation["reason"],
            previous_id=obj["id"],
            boundary_state="human_reviewed_relative_fit"
            if kind == "approved_polygon"
            else "AI_candidate_with_existing_semantic_decision",
            electrical_connection="unknown",
        )
        result.append(item)
    return result, dict(
        id=operation["id"],
        object_id=obj["id"],
        kind=kind,
        new_ids=[v["id"] for v in result],
        source_changed_area_px2=float(old_source.symmetric_difference(new_source).area),
        changed_outside_allowed_domain_px2=float(outside),
        details=details,
    )


def overlay(photo, model, color):
    result = photo.copy()
    for item in model["objects"]:
        p = source_polygon(item, model)
        for part in pieces(p):
            for ring in [part.exterior, *part.interiors]:
                cv2.polylines(result, [np.rint(ring.coords).astype(np.int32)], True, color, 2)
    return result


def geometry_svg(model, native=False, only_ids=None, color="#72d4ec"):
    size = (
        [model["sources"]["aa"]["width"], model["sources"]["aa"]["height"]]
        if native
        else model["canvas_wh"]
    )
    chunks = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size[0]} {size[1]}">']
    for item in model["objects"]:
        if only_ids is not None and item["id"] not in only_ids:
            continue
        p = source_polygon(item, model) if native else object_polygon(item)
        path = ""
        for part in pieces(p):
            for ring in [part.exterior, *part.interiors]:
                path += "M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in ring.coords) + " Z "
        chunks.append(
            f'<path d="{path}" fill="{color}" fill-opacity=".4" '
            f'stroke="{color}" stroke-width="1" fill-rule="evenodd"/>'
        )
    return "".join(chunks) + "</svg>"


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(Path(spec_path).read_text())
    base = load_locked(root, spec["base"])
    snapshot = None
    if spec.get('joint_snapshot'):
        ref = spec['joint_snapshot']
        load_locked(root, ref)
        snapshot = load_snapshot(root, root / ref['path'])
        if spec['base'] != snapshot['manifest']['inputs']['materials']:
            raise ValueError('AA revision must start from current joint materials')
        base = aa_view(snapshot)
    protected = load_locked(root, spec["protected"])
    for name in [
        "previous_human_review",
        "local_adoption",
        "unresolved_observations",
        "bound_conflicts",
    ]:
        load_locked(root, spec[name])
    if digest(root / spec["skill"]["path"]) != spec["skill"]["sha256"]:
        raise ValueError("Changed skill snapshot")
    if digest(root / spec["source"]["path"]) != spec["source"]["sha256"]:
        raise ValueError("Changed source photo")
    photo = cv2.imread(str(root / spec["source"]["path"]))
    operations = {v["object_id"]: v for v in spec["revisions"]}
    if len(operations) != len(spec["revisions"]):
        raise ValueError("Multiple edits to one object must be consolidated")
    old = {v["id"]: v for v in base["objects"]}
    protected_ids = {v["id"] for v in protected["objects"] if v["layer"] == "AA"}
    if protected_ids & operations.keys():
        raise ValueError("Would change protected AA")
    if not operations.keys() <= old.keys():
        raise ValueError("Unknown target object")
    result, audits = [], []
    for item in base["objects"]:
        if item["id"] in operations:
            revised, audit = revise_object(
                root, item, base, operations[item["id"]], photo, spec["settings"]
            )
            result.extend(revised)
            audits.append(audit)
        else:
            result.append(copy.deepcopy(item))
    model = copy.deepcopy(base)
    model.update(
        objects=result,
        parent=spec["base"],
        status="full_frame_scoped_AA_working_candidate",
        physical_fullframe_acceptance=False,
        revision_spec_sha256=digest(spec_path),
    )
    for item in result:
        model["object_projection_groups"].setdefault(
            item["id"], item.get("structure_group", "global")
        )
    conflicts = validate(result)
    if snapshot is not None:
        continued = replace_layer(snapshot, 'AA', result, operations.keys())
        # A split introduces new identities and needs explicit companion-reference edits;
        # this entry is for bounded same-ID refinement of the common snapshot.
        model['joint_layers'] = continued['joint_report']
    current = {v["id"]: v for v in result}
    untouched = set(old) - operations.keys()
    assert all(current[k] == old[k] for k in untouched)
    assert all(current[k] == old[k] for k in protected_ids)
    boundary_evidence = {}
    for audit in audits:
        details = audit["details"]
        if "paths_native_y" in details:
            boundary_evidence[audit["id"]] = {
                name: details.pop(name) for name in ["paths_native_y", "eligible_native_x"]
            }
            details["boundary_evidence_file"] = "boundary-evidence.json"
    report = dict(
        status="full_frame_candidate_requires_material_review",
        before_objects=len(old),
        after_objects=len(current),
        unchanged_objects=len(untouched),
        protected_AA_unchanged=len(protected_ids),
        revisions=audits,
        gates=dict(
            source="PASS",
            unchanged_objects="PASS",
            protected_AA="PASS",
            orthogonal_geometry="PASS",
            area_overlaps="FAIL" if conflicts else "PASS",
            complete_material_coverage="NOT_ACCEPTED",
            skill_fullframe_release="NOT_READY",
        ),
        layout_intersection_conflicts=conflicts,
        remaining_decisions=spec["remaining_decisions"],
        ML_training=False,
        ML_inference=False,
        CT_updated=False,
        raw_photo_unchanged=True,
        code_sha256=digest(__file__),
        spec_sha256=digest(spec_path),
    )
    output.mkdir(parents=True)
    if snapshot is not None:
        write_snapshot(root, continued, output)
        report['joint_layers'] = continued['joint_report']
    for name, value in [
        ("model.json", model),
        ("report.json", report),
        ("spec.json", spec),
        ("boundary-evidence.json", boundary_evidence),
    ]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    before = overlay(photo, base, (0, 210, 255))
    after = overlay(photo, model, (230, 170, 30))
    changed = {name for audit in audits for name in audit["new_ids"]}
    for name, svg in [
        ("native-AA.svg", geometry_svg(model, True)),
        ("layout-AA.svg", geometry_svg(model)),
        ("changed-native.svg", geometry_svg(model, True, changed)),
    ]:
        (output / name).write_text(svg)
    cv2.imwrite(str(output / "source.jpg"), photo, [cv2.IMWRITE_JPEG_QUALITY, 86])
    cv2.imwrite(str(output / "before.jpg"), before, [cv2.IMWRITE_JPEG_QUALITY, 86])
    cv2.imwrite(str(output / "after.jpg"), after, [cv2.IMWRITE_JPEG_QUALITY, 86])
    cv2.imwrite(str(output / "AA-layout.png"), paint_objects(result, model["canvas_wh"]))
    windows = [
        dict(
            id="FULL",
            bbox=[0, 0, photo.shape[1], photo.shape[0]],
            state="全幅总览：复用既有AA层与局部修订",
        )
    ]
    windows += spec["review_windows"]
    windows += spec.get("inspection_windows", [])
    windows += [
        dict(id=v["id"], bbox=v["bbox"], state=v["question"], landmarks=v.get("landmarks", []))
        for v in spec["remaining_decisions"]
    ]
    for window in windows:
        if window["id"] == "FULL":
            continue
        sub = output / window["id"]
        sub.mkdir()
        x, y, r, b = window["bbox"]
        for name, value in [("source", photo), ("before", before), ("after", after)]:
            crop = value[y:b, x:r].copy()
            for mark in window.get("landmarks", []):
                px, py = np.array(mark["native_xy"]) - [x, y]
                cv2.circle(crop, (int(px), int(py)), 5, (20, 80, 255), 2)
                cv2.putText(
                    crop,
                    mark["label"],
                    (int(px) + 12, int(py) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (20, 80, 255),
                    2,
                )
            cv2.imwrite(str(sub / f"{name}.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, 86])
    (output / "data.js").write_text(
        "const DATA=" + json.dumps(dict(windows=windows, report=report), ensure_ascii=False) + ";\n"
    )
    (output / "index.html").write_text(PAGE)
    assert digest(root / spec["source"]["path"]) == spec["source"]["sha256"]
    manifest = {
        str(p.relative_to(output)): digest(p) for p in sorted(output.rglob("*")) if p.is_file()
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return report


PAGE = """<!doctype html><meta charset="utf-8"><title>AA全幅接续与质量复核</title>
<style>body{font-family:sans-serif;
background:#19212d;
color:#eee;
margin:24px}a{color:#8edcff}
select{padding:8px}img{width:100%;
background:#111}.pair{display:grid;
grid-template-columns:1fr 1fr;
gap:12px}
@media(max-width:900px){.pair{grid-template-columns:1fr}}#note{line-height:1.6}</style>
<h1>AA全幅：接续已有几何，修订明确问题</h1>

<p>黄色为旧版，蓝色为修订后。原图叠加使用逐对象来源；规则版图单独显示重建坐标，不能直接当照片投影。</p>


<p>没有全图重训/模型推断或CT更新。既有语义不重复询问，旧问题不等于新批准。全幅材料完整性尚未验收。</p>

<select id="scope"></select>
<select id="mode"><option value="after">修订后叠加</option>
<option value="before">旧版叠加</option><option value="source">原图</option>
<option value="layout">规则AA版图（重建坐标）</option></select>
<p id="note"></p>

<div class="pair"><div>原图与上下文<img id="raw"></div>
<div id="resultlabel">所选结果<img id="result"></div>
</div>

<h2>本轮检查范围</h2><p id="stats"></p>

<p id="questions"></p>
<p>全幅AI巡检与局部变更结果另见人工/AI复核记录；不要求重新验收全部检查块。</p>


<p><a href="report.json">质量门/变更记录</a> ·
<a href="model.json">全幅AA几何</a> · <a href="spec.json">输入/假设</a></p>

<script src="data.js"></script><script>
const el=id=>document.getElementById(id);
for(const w of DATA.windows){let o=document.createElement('option');
o.value=w.id;
o.textContent=w.id+' '+w.state;
el('scope').append(o);
}
function update(){const w=DATA.windows.find(v=>v.id===el('scope').value);
const mode=el('mode').value,dir=w.id==='FULL'?'':w.id+'/';

el('raw').src=dir+'source.jpg';
el('result').src=mode==='layout'?'layout-AA.svg':dir+mode+'.jpg';

el('note').textContent=w.state+'；原生范围 '+w.bbox.join(', ')+
'；规则版图模式始终显示整层共同重建坐标。';
}
el('stats').textContent='对象 '+DATA.report.before_objects+' → '+DATA.report.after_objects+
'；未改对象 '+DATA.report.unchanged_objects+
'；保留AA '+DATA.report.protected_AA_unchanged+
'；几何面积交叠 '+DATA.report.layout_intersection_conflicts.length+
'。对象数不是覆盖率或准确率。';

el('questions').textContent=DATA.report.remaining_decisions.map(q=>q.id+'：'+q.question).join('；');
for(const name of ['scope','mode'])el(name).addEventListener('change',update);
update();

</script>"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root, args.spec, args.output)
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "before_objects",
                    "after_objects",
                    "unchanged_objects",
                    "protected_AA_unchanged",
                    "gates",
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
    )
