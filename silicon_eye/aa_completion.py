"""Apply evidence-linked AA-only structural revisions and render full-scene review.

Run: python -m silicon_eye.aa_completion --root . --spec SPEC --output NEW_DIR
Requires project OpenCV/Shapely/Pillow. AI observations are explicit input data;
no CT detection, photograph mutation, implicit electrical merging, or remote calls.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from .geometry_reconstruction import (
    corners,
    digest,
    object_polygon,
    object_rings,
    project,
    rectangle_fit,
)
from .regular_scene import scene_svg
from .scene_geometry import load_locked, paint_objects


def part_polygon(part):
    """Construct material, including open crop-edge frames, without filling its fields."""
    kind = part["kind"]
    if kind == "union":
        result = unary_union([part_polygon(p) for p in part["parts"]])
    elif kind == "compound_enclosure":
        result = unary_union([box(*b) for b in part["outer_boxes"]]).difference(
            unary_union([box(*b) for b in part["inner_boxes"]])
        )
    elif kind == "polygon":
        result = Polygon(part["outer"]).difference(
            unary_union([Polygon(h) for h in part.get("holes", [])])
        )
    else:
        result = box(*part["bounds"])
        if kind == "frame":
            x, y, r, b = part["bounds"]
            w = part["width"]
            if w <= 0 or min(r - x, b - y) <= 2 * w:
                raise ValueError("Invalid ring width")
            result = result.difference(box(x + w, y + w, r - w, b - w))
        elif kind == "difference":
            result = result.difference(unary_union([box(*h) for h in part["holes"]]))
        elif kind != "rectangle":
            raise ValueError("Unknown AA primitive")
    if result.is_empty or not result.is_valid or result.area <= 0:
        raise ValueError("Invalid AA material observation")
    return result


def pieces(geometry):
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type == "MultiPolygon":
        return list(geometry.geoms)
    raise ValueError("Expected polygonal material")


def polygon_record(identifier, polygon):
    return dict(
        id=identifier,
        layer="AA",
        primitive="orthogonal_polygon",
        outer_xy=list(map(list, polygon.exterior.coords[:-1])),
        holes_xy=[list(map(list, h.coords[:-1])) for h in polygon.interiors],
        outer_xyxy=list(polygon.bounds),
        hole_xyxy=None,
        status="candidate",
        dimension_status="relative_layout_units_not_um",
        electrical_connection="unknown",
    )


def source_polygon(obj, base):
    if obj['id'] in base.get('source_footprints', {}):
        return unary_union([
            Polygon(p['outer_xy'], p['holes_xy']) for p in base['source_footprints'][obj['id']]
        ])
    if "source_geometry" in obj:
        value = obj["source_geometry"]
        return Polygon(value["outer_xy"], value["holes_xy"])
    mapping = base["object_projection_groups"].get(obj["id"], "global")
    h = base["projection_matrices"][mapping]["aa"]
    outer, holes = object_rings(obj)
    return Polygon(project(outer, h), [project(p, h) for p in holes])


def revise(base, retained, spec):
    """Revisions supersede explicit source-box observations; protected objects stay identical."""
    old = [copy.deepcopy(o) for o in base["objects"] if o["layer"] == "AA"]
    locked = {o["id"] for o in retained["objects"] if o["layer"] == "AA"}
    sources = {o["id"]: source_polygon(o, base) for o in old}
    matrices = copy.deepcopy(base["projection_matrices"])
    mapping = copy.deepcopy(base["object_projection_groups"])
    global_h = np.linalg.inv(np.array(matrices["global"]["aa"]))
    added, source_materials, groups = [], {}, []
    for group in spec["groups"]:
        native_box = group["native_box"]
        target = group.get("layout_box") or rectangle_fit(project(group["source_quad"], global_h))
        x, y, native_right, native_bottom = native_box
        a, b, layout_right, layout_bottom = target
        canonical_to_layout = np.array(
            [
                [
                    (layout_right - a) / (native_right - x),
                    0,
                    a - x * (layout_right - a) / (native_right - x),
                ],
                [
                    0,
                    (layout_bottom - b) / (native_bottom - y),
                    b - y * (layout_bottom - b) / (native_bottom - y),
                ],
                [0, 0, 1.0],
            ]
        )
        canonical_to_source, _ = cv2.findHomography(
            corners(native_box), np.array(group["source_quad"], float), 0
        )
        gid = group["id"]

        # A compound structure needs more than one fitted bounding-box homography.
        # Preserve its source boundaries and explicit separable axis parameterization.
        def forward(
            points,
            group=group,
            canonical_to_layout=canonical_to_layout,
            x=x,
            y=y,
            native_right=native_right,
            native_bottom=native_bottom,
        ):
            points = np.array(points, float)
            if group.get("layout_box"):
                return project(points, canonical_to_layout)
            result = points.copy()
            px = np.c_[points[:, 0], np.full(len(points), (y + native_bottom) / 2)]
            py = np.c_[np.full(len(points), (x + native_right) / 2), points[:, 1]]
            result[:, 0] = project(px, global_h)[:, 0]
            result[:, 1] = project(py, global_h)[:, 1]
            return result

        record = dict(
            id=gid,
            source_quad=group["source_quad"],
            native_box=native_box,
            layout_box=target,
            evidence=group["reason"],
            state="AI_candidate",
            exact_boundary="not_human_accepted",
            members=[],
            projection_model="source_homography_plus_separable_layout_axes",
            canonical_to_source=canonical_to_source.tolist(),
            layout_axis_matrix=global_h.tolist(),
            axis_reference_xy=[(x + native_right) / 2, (y + native_bottom) / 2],
            explicit_affine_layout=canonical_to_layout.tolist()
            if group.get("layout_box")
            else None,
        )
        for part in group["parts"]:
            for i, p in enumerate(pieces(part_polygon(part))):
                q = Polygon(
                    forward(p.exterior.coords[:-1]), [forward(h.coords[:-1]) for h in p.interiors]
                )
                # Keep exact horizontal/vertical sides while recording source mapping separately.
                q = Polygon(
                    np.round(q.exterior.coords, 4), [np.round(h.coords, 4) for h in q.interiors]
                )
                identifier = f"AA2-{gid}-{part['id']}-{i}"
                obj = polygon_record(identifier, q)
                obj.update(
                    structure_group=gid,
                    revision_role="AA_only_structural_completion",
                    source_observation=part,
                    source_photo=base["sources"]["aa"],
                    evidence=group["reason"],
                    physical_continuation="unknown_outside_photo",
                    source_state="AI_observation_not_human_confirmed",
                )
                added.append(obj)
                source_materials[identifier] = Polygon(
                    project(p.exterior.coords[:-1], canonical_to_source),
                    [project(h.coords[:-1], canonical_to_source) for h in p.interiors],
                )
                if part.get("observed_source"):
                    observed_parts = pieces(part_polygon(part["observed_source"]))
                    if len(observed_parts) != len(pieces(part_polygon(part))):
                        raise ValueError("Source/layout boundary correspondence mismatch")
                    source_materials[identifier] = observed_parts[i]
                    obj["projection_model"] = "explicit_boundary_correspondence_at_photo_cut"
                src = source_materials[identifier]
                obj["source_geometry"] = dict(
                    outer_xy=list(map(list, src.exterior.coords[:-1])),
                    holes_xy=[list(map(list, h.coords[:-1])) for h in src.interiors],
                )
                mapping[identifier] = gid
                record["members"].append(identifier)
        groups.append(record)
    superseded, kept = [], []
    for row in spec.get("row_regularization", []):
        for i, o in enumerate(old):
            if o["id"] not in row["object_ids"]:
                continue
            if o["id"] in locked:
                raise ValueError("Row revision would move retained geometry")
            p = object_polygon(o)
            if p.interiors or abs(p.area - box(*p.bounds).area) > 0.01:
                raise ValueError("Row normalization requires observed rectangles")
            b = list(p.bounds)
            b[1] = row["top"]
            b[3] = b[1] + row["height"]
            n = polygon_record(o["id"], box(*b))
            original_source = sources[o["id"]]
            n.update(
                status="candidate",
                revision_role="shared_row_revision",
                parent_object=copy.deepcopy(o),
                structure_group=row["id"],
                evidence=row["reason"],
                source_geometry=dict(
                    outer_xy=list(map(list, original_source.exterior.coords[:-1])), holes_xy=[]
                ),
            )
            old[i] = n

    for o in old:
        p = sources[o["id"]]
        reason, ids = None, []
        explicit = {v["id"]: v for v in spec.get("supersede_ids", [])}
        if o["id"] in explicit and o["id"] not in locked:
            v = explicit[o["id"]]
            superseded.append(
                dict(object=copy.deepcopy(o), reason=v["reason"], replacements=v["replacements"])
            )
            continue
        rejected = {v["id"]: v["reason"] for v in spec.get("reject_ids", [])}
        if o["id"] in rejected and o["id"] not in locked:
            reason = rejected[o["id"]]
        if reason:
            superseded.append(
                dict(
                    object=copy.deepcopy(o),
                    reason=reason,
                    replacements=[],
                    disposition="unresolved_source_not_material",
                )
            )
            continue
        if o["id"] not in locked:
            for g in spec["groups"]:
                bounds = g.get("replace_box")
                if bounds and p.intersection(box(*bounds)).area / p.area > 0.85:
                    reason = "explicit_source_structure_revision"
                    ids = [n["id"] for n in added if n["structure_group"] == g["id"]]
                    break
            if reason is None:
                ids = [
                    identifier
                    for identifier, q in source_materials.items()
                    if p.intersection(q).area / p.area > 0.65
                ]
                if ids:
                    reason = "same_source_material_represented_by_complete_structure"
        if reason:
            superseded.append(
                dict(
                    object=copy.deepcopy(o),
                    reason=reason,
                    replacements=ids,
                    human_review_inheritance="prior_scope_only_not_new_boundary",
                )
            )
        else:
            kept.append(o)
    result = kept + added
    assert all(o in result for o in old if o["id"] in locked)
    return result, mapping, matrices, superseded, groups


def validate(objects):
    problems = []
    if len({o["id"] for o in objects}) != len(objects):
        raise ValueError("Duplicate AA object identity")
    for o in objects:
        p = object_polygon(o)
        if not p.is_valid or p.area <= 0:
            raise ValueError("Invalid material: " + o["id"])
        for ring in [p.exterior, *p.interiors]:
            d = np.diff(np.array(ring.coords), axis=0)
            if np.any((abs(d[:, 0]) > 1e-5) & (abs(d[:, 1]) > 1e-5)):
                raise ValueError("Nonorthogonal material: " + o["id"])
    for i, a in enumerate(objects):
        p = object_polygon(a)
        for b in objects[:i]:
            q = object_polygon(b)
            area = p.intersection(q).area
            if area > 0.05:
                problems.append(
                    dict(
                        a=a["id"],
                        b=b["id"],
                        intersection_area=area,
                        state="requires_localization_not_automatic_union",
                    )
                )
    return problems


def run(root, spec_path, output):
    root, spec_path, output = (
        Path(root).resolve(),
        Path(spec_path).resolve(),
        Path(output).resolve(),
    )
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(spec_path.read_text())
    base, retained = load_locked(root, spec["base"]), load_locked(root, spec["retained"])
    review = load_locked(root, spec["human_review"])
    unresolved = load_locked(root, spec["unresolved_AA"])
    load_locked(root, spec["boundary_conflicts"])
    if digest(root / base["sources"]["aa"]["path"]) != base["sources"]["aa"]["sha256"]:
        raise ValueError("Changed source AA photograph")
    objects, mapping, matrices, superseded, groups = revise(base, retained, spec)
    conflicts = validate(objects)
    model = dict(
        schema_version=1,
        status="AA_only_full_scene_candidates",
        canvas_wh=base["canvas_wh"],
        sources={"aa": base["sources"]["aa"]},
        objects=objects,
        object_projection_groups=mapping,
        projection_matrices=matrices,
        groups=groups,
        parent=spec["base"],
        code_sha256=digest(__file__),
        spec_sha256=digest(spec_path),
        source_projection_contract=(
            "source_geometry is the explicit native boundary correspondence when present; "
            "otherwise use projection_matrices via object_projection_groups. "
            "A structure-group ID does not imply a single 3x3 projection matrix."
        ),
        superseded=superseded,
        CT="not_recomputed; historical parent only",
        physical_fullframe_acceptance=False,
        units="relative_layout_units_not_um",
    )
    report = dict(
        AA_objects=len(objects),
        new_structural_objects=sum(len(g["members"]) for g in groups),
        groups=len(groups),
        superseded=len(superseded),
        active_intersection_conflicts=conflicts,
        geometry_gate="pass",
        isolation_gate="fail" if conflicts else "no_area_overlaps",
        coverage_gate="pending_independent_human_review",
        evidence_gate="pending_independent_boundary_review",
        CT_processed=False,
        geometry_gate_scope="valid_positive_orthogonal_objects_only",
        isolation_gate_scope="no_active_area_overlap_not_electrical_isolation_acceptance",
        parent_unresolved_AA_observations=len(unresolved),
        unresolved_AA_reference=spec["unresolved_AA"],
        parent_boundary_conflict_reference=spec["boundary_conflicts"],
        physical_completeness=False,
        retained_AA_unchanged=sum(o["layer"] == "AA" for o in retained["objects"]),
    )
    output.mkdir(parents=True)
    for name, value in [
        ("model.json", model),
        ("report.json", report),
        ("spec.json", spec),
        ("superseded.json", superseded),
    ]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    aa = cv2.imread(str(root / base["sources"]["aa"]["path"]))
    sizes = {"layout": base["canvas_wh"], "aa": [aa.shape[1], aa.shape[0]]}
    native_objects = []
    for o in objects:
        native_objects.append(
            polygon_record(
                o["id"],
                source_polygon(
                    o, dict(object_projection_groups=mapping, projection_matrices=matrices)
                ),
            )
        )
    for frame, size in sizes.items():
        (output / f"{frame}-AA.svg").write_text(
            scene_svg(native_objects if frame == "aa" else objects, size, "layout", {}, matrices)
        )
        (output / f"{frame}-labels.svg").write_text(
            scene_svg(
                native_objects if frame == "aa" else objects,
                size,
                "layout",
                {},
                matrices,
                labels=True,
            )
        )
        before = [o for o in base["objects"] if o["layer"] == "AA"]
        (output / f"{frame}-before.svg").write_text(
            scene_svg(
                before, size, frame, base["object_projection_groups"], base["projection_matrices"]
            )
        )
        (output / f"{frame}-new.svg").write_text(
            scene_svg(
                [
                    o
                    for o in (native_objects if frame == "aa" else objects)
                    if o["id"].startswith("AA2-")
                ],
                size,
                "layout",
                {},
                matrices,
            )
        )
    mask = paint_objects(objects, base["canvas_wh"])
    cv2.imwrite(str(output / "AA-layout.png"), mask)
    # Source overlay uses each object's own recorded mapping, never a blind global projection.
    painted = aa.copy()
    for o in objects:
        src = source_polygon(
            o, dict(object_projection_groups=mapping, projection_matrices=matrices)
        )
        cv2.polylines(
            painted, [np.rint(src.exterior.coords).astype(np.int32)], True, (80, 230, 255), 2
        )
        for hole in src.interiors:
            cv2.polylines(painted, [np.rint(hole.coords).astype(np.int32)], True, (80, 230, 255), 2)
    cv2.imwrite(str(output / "aa-outlines.jpg"), painted)
    windows = [
        dict(id=v["id"], AA_native_bbox=v["AA_native_bbox"], display_window_only=True)
        for v in review["frames"]
    ]
    data = dict(
        sizes=sizes,
        source=str((root / base["sources"]["aa"]["path"]).relative_to(root)),
        windows=windows,
        human_feedback={v["id"]: v["verbatim_feedback"] for v in review["frames"]},
        report=report,
        photo_relative=os.path.relpath(root / base["sources"]["aa"]["path"], output),
        layout_windows={
            w["id"]: [
                *project(
                    corners(w["AA_native_bbox"]),
                    np.linalg.inv(np.array(base["projection_matrices"]["global"]["aa"])),
                ).min(0),
                *np.ptp(
                    project(
                        corners(w["AA_native_bbox"]),
                        np.linalg.inv(np.array(base["projection_matrices"]["global"]["aa"])),
                    ),
                    axis=0,
                ),
            ]
            for w in windows
        },
    )
    (output / "data.js").write_text("const DATA=" + json.dumps(data, ensure_ascii=False) + ";\n")
    (output / "index.html").write_text(PAGE)
    return report


PAGE = """<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>AA 全幅结构补全</title>
<style>
body{background:#14212b;color:#edf5fa;font:17px/1.6 sans-serif;margin:20px}
a{color:#70dfff}select,label{font:inherit;margin:8px}
svg{width:100%;height:76vh;background:#101923}
</style>
<h1>全幅 AA：补环、补器件、恢复隔离</h1>
<p>本版只处理 AA。全幅标注候选尚待独立复核，不表示每条边界均已确认。</p>
<p>原图视图使用各结构的来源边界/映射；规则版图使用相应参数化几何。
局部参数化尚不构成已验收的全幅畸变场，不能据此追线。</p>
<select id="frame"><option value="aa">AA 原图与边界</option>
<option value="layout">正交规则版图</option></select>
<select id="window"><option value="full">全幅</option></select>
<label><input type="checkbox" id="before">旧版 AA</label>
<label><input type="checkbox" id="onlynew">只看新增结构</label>
<label><input type="checkbox" id="labels">编号</label>
<label>透明度<input id="opacity" type="range" min="0" max="1" step=".05" value=".6"></label>
<svg id="view"><image id="photo"/><image id="layer"/><image id="text"/></svg>
<p id="summary"></p><p id="feedback"></p>
<p><a href="model.json">AA 模型与来源</a> · <a href="report.json">检查结果</a> ·
<a href="superseded.json">旧对象修订记录</a> ·
<a href="aa-outlines.jpg">原尺寸边界图</a> · <a href="AA-layout.png">AA 像素图</a></p>
<script src="data.js"></script><script>
const el=id=>document.getElementById(id);
for(const w of DATA.windows){
const o=document.createElement('option');o.value=w.id;o.textContent=w.id;
el('window').append(o);}
function update(){
const f=el('frame').value,s=DATA.sizes[f],id=el('window').value;
let v=[0,0,...s];
if(id!=='full'){
const w=DATA.windows.find(w=>w.id===id);
if(f==='aa'){const [x,y,X,Y]=w.AA_native_bbox;v=[x,y,X-x,Y-y];}
else{v=DATA.layout_windows[id];}}
el('view').setAttribute('viewBox',v.join(' '));
for(const n of ['photo','layer','text']){
el(n).setAttribute('width',s[0]);el(n).setAttribute('height',s[1]);}
el('photo').setAttribute('href',f==='aa'?DATA.photo_relative:'');
const role=el('before').checked?'before':el('onlynew').checked?'new':'AA';
el('layer').setAttribute('href',f+'-'+role+'.svg');
el('layer').style.opacity=el('opacity').value;
el('text').setAttribute('href',el('labels').checked&&!el('before').checked?f+'-labels.svg':'');
el('feedback').textContent=id==='full'?'F01–F12 只是显示窗口，不裁割 AA。'
: '上一轮复核：'+DATA.human_feedback[id];}
for(const e of document.querySelectorAll('select,input'))e.addEventListener('input',update);
el('summary').textContent=`AA ${DATA.report.AA_objects} 条；`
+`补建结构 ${DATA.report.new_structural_objects} 条；`
+`几何交叠 ${DATA.report.active_intersection_conflicts.length} 处。覆盖与精确边界尚待复核。`;
update();
</script></html>"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.root, args.spec, args.output)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "active_intersection_conflicts"},
            ensure_ascii=False,
        )
    )
    print("intersection conflicts:", len(result["active_intersection_conflicts"]))
