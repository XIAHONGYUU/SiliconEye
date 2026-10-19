"""Audit explicit POLY-to-AA hypotheses and render a separate joint candidate.

Run: python -m silicon_eye.poly_aa_correspondence --root . --spec SPEC --output NEW_DIR
Requires the project environment. No nearest-AA inference or source edits occur.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon, box
from shapely.strtree import STRtree

from .aa_completion import source_polygon
from .geometry_reconstruction import digest, object_polygon
from .poly_full_frame import save
from .scene_geometry import load_locked


def propose_aa_row_alignment(aa_model, alignments):
    """Create a working variant; retain native AA outlines and untouched objects."""
    result = copy.deepcopy(aa_model)
    by_id = {o["id"]: o for o in result["objects"]}
    previous = {o["id"]: o for o in aa_model["objects"]}
    changes = []
    for alignment in alignments:
        reference = object_polygon(previous[alignment["reference_AA_id"]])
        _, top, _, bottom = reference.bounds
        for key in alignment["AA_object_ids"]:
            obj = by_id[key]
            polygon = object_polygon(obj)
            if not polygon.equals(box(*polygon.bounds)):
                raise ValueError("Row alignment requires explicitly rectangular active")
            left, old_top, right, old_bottom = polygon.bounds
            if abs(old_top - top) < 1e-6 and abs(old_bottom - bottom) < 1e-6:
                continue
            native = source_polygon(previous[key], aa_model)
            obj["source_geometry"] = dict(
                outer_xy=list(map(list, native.exterior.coords))[:-1],
                holes_xy=[list(map(list, ring.coords))[:-1] for ring in native.interiors],
            )
            obj["primitive"] = "orthogonal_polygon"
            obj["outer_xy"] = [[left, top], [right, top], [right, bottom], [left, bottom]]
            obj["outer_xyxy"] = [left, top, right, bottom]
            obj["holes_xy"] = []
            obj["hole_xyxy"] = None
            obj["status"] = "AI_joint_row_alignment_proposal_not_human_accepted"
            obj["joint_revision"] = dict(
                before_layout_bounds=list(polygon.bounds),
                reason=alignment["evidence"],
                reference_AA_id=alignment["reference_AA_id"],
            )
            if not source_polygon(obj, result).equals_exact(native, 1e-8):
                raise ValueError("Working AA revision changed source evidence")
            changes.append(
                dict(
                    AA_object_id=key,
                    before=list(polygon.bounds),
                    after=list(object_polygon(obj).bounds),
                )
            )
    return result, changes


def build_correspondences(inventory, aa_model, settings):
    """Validate total accounting; keep identity and geometry checks independent."""
    sources = {o["id"]: o for o in inventory["objects"]}
    if len(sources) != len(inventory["objects"]):
        raise ValueError("Duplicate source observation IDs")
    aa_objects = {o["id"]: o for o in aa_model["objects"]}
    aa_ids = list(aa_objects)
    polygons = [object_polygon(aa_objects[key]) for key in aa_ids]
    if any(not p.is_valid for p in polygons):
        raise ValueError("Invalid parent AA geometry; do not repair it silently")
    aa_geometry = dict(zip(aa_ids, polygons, strict=True))
    tree = STRtree(polygons)
    budgets = settings["relative_budgets"]
    width = budgets["gate_width_px"]
    extension = budgets["poly_extension_px"]
    margin = budgets["lateral_margin_px"]
    gap = budgets["min_intergate_gap_px"]
    if width <= 0 or extension <= 0 or margin < 0 or gap < 0:
        raise ValueError("Invalid relative geometry budgets")
    seen, result, groups = set(), [], []
    for relation in settings["relations"]:
        key = relation["AA_object_id"]
        if key not in aa_geometry:
            raise ValueError("Missing explicit AA target")
        slots = relation["slot_count"]
        indices = relation["slot_indices"]
        ids = relation["poly_observation_ids"]
        if (
            not isinstance(slots, int)
            or slots < 1
            or len(indices) != len(ids)
            or len(set(indices)) != len(indices)
            or any(not isinstance(i, int) or i < 0 or i >= slots for i in indices)
        ):
            raise ValueError("Invalid explicit slot accounting")
        if any(k not in sources or k in seen for k in ids):
            raise ValueError("Missing or multiply assigned POLY observation")
        seen.update(ids)
        active = aa_geometry[key]
        left, top, right, bottom = active.bounds
        available = right - left - 2 * margin - width
        infeasible = available < 0 or (slots > 1 and available / (slots - 1) < width + gap)
        centers = np.linspace(left + margin + width / 2, right - margin - width / 2, slots)
        if slots == 1:
            centers = [(left + right) / 2]
        group = copy.deepcopy(relation)
        group["unobserved_slot_indices"] = sorted(set(range(slots)) - set(indices))
        group["objects"] = []
        for source_id, index in zip(ids, indices, strict=True):
            entry = dict(
                source_poly_id=source_id,
                AA_object_id=key,
                relation_id=relation["id"],
                scope=relation["scope"],
                slot_index=index,
                association_status=relation["association_status"],
                source_native_outline=copy.deepcopy(sources[source_id]["native_outline"]),
                joint_layout_outline=None,
                source_review=sources[source_id].get("approval", sources[source_id]["status"]),
            )
            if infeasible:
                entry["geometry_check"] = dict(status="BLOCKED", reasons=["count_width_gap_budget"])
            else:
                cx = float(centers[index])
                candidate = box(cx - width / 2, top - extension, cx + width / 2, bottom + extension)
                neighbors = [
                    dict(
                        AA_object_id=aa_ids[i],
                        overlap_area=float(candidate.intersection(polygons[i]).area),
                    )
                    for i in tree.query(candidate)
                    if aa_ids[i] != key and candidate.intersection(polygons[i]).area > 1e-6
                ]
                support = candidate.intersection(active).area
                reasons = []
                if abs(support - width * (bottom - top)) > 1e-5:
                    reasons.append("AA_not_full_rectangular_crossing")
                if neighbors:
                    reasons.append("non_target_AA_overlap")
                x, y, r, b = candidate.bounds
                entry["joint_layout_outline"] = [[x, y], [r, y], [r, b], [x, b]]
                entry["geometry_check"] = dict(
                    status="CONFLICT" if reasons else "PASS",
                    reasons=reasons,
                    target_overlap_area=float(support),
                    non_target_AA_intersections=neighbors,
                    top_extension_px=extension,
                    bottom_extension_px=extension,
                    rectangular=True,
                    scope="relative_structure_not_foundry_DRC_or_material_truth",
                )
            group["objects"].append(source_id)
            result.append(entry)
        groups.append(group)
    unresolved = copy.deepcopy(settings["unresolved"])
    pending = [item["poly_observation_id"] for item in unresolved]
    if len(pending) != len(set(pending)) or seen.intersection(pending):
        raise ValueError("Duplicate or already assigned unresolved observation")
    if seen.union(pending) != set(sources):
        raise ValueError("Unaccounted source observations")
    # Cross-group conflicts remain visible; do not move targets to obtain PASS.
    for i, obj in enumerate(result):
        if obj["joint_layout_outline"] is None:
            continue
        p = Polygon(obj["joint_layout_outline"])
        for other in result[:i]:
            if other["joint_layout_outline"] is None:
                continue
            if p.intersection(Polygon(other["joint_layout_outline"])).area > 1e-6:
                for record, neighbor in [(obj, other), (other, obj)]:
                    check = record["geometry_check"]
                    check["status"] = "CONFLICT"
                    if "POLY_overlap" not in check["reasons"]:
                        check["reasons"].append("POLY_overlap")
                    check.setdefault("POLY_neighbors", []).append(neighbor["source_poly_id"])
    counts = {
        state: sum(o["geometry_check"]["status"] == state for o in result)
        for state in ["PASS", "CONFLICT", "BLOCKED"]
    }
    return dict(
        source_observations=len(sources),
        assigned_candidates=len(result),
        unresolved=unresolved,
        groups=groups,
        objects=result,
        geometry_counts=counts,
        unobserved_slots=sum(len(g["unobserved_slot_indices"]) for g in groups),
        material_and_source_geometries_unchanged=True,
        acceptance="AI_correspondence_and_geometry_candidates_not_human_confirmed",
    )


def joint_svg(objects, aa_model, target_ids, aliases):
    polygons = {o["id"]: object_polygon(o) for o in aa_model["objects"]}
    bounds = np.array([polygons[key].bounds for key in target_ids])
    left, top = bounds[:, :2].min(0) - 25
    right, bottom = bounds[:, 2:].max(0) + 35
    frame = box(left, top, right, bottom)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{left} {top} '
        f'{right - left} {bottom - top}"><rect x="{left}" y="{top}" width="{right - left}" '
        f'height="{bottom - top}" fill="#15212c"/>'
    )
    for key, polygon in polygons.items():
        if not frame.intersects(polygon):
            continue
        path = ""
        for ring in [polygon.exterior, *polygon.interiors]:
            path += "M" + " L".join(f"{x},{y}" for x, y in ring.coords) + " Z "
        color = "#5fcd77" if key in target_ids else "#789188"
        svg += f'<path d="{path}" fill="{color}" fill-opacity=".35" fill-rule="evenodd"/>'
        if key in target_ids:
            x, y, _, _ = polygon.bounds
            svg += f'<text x="{x}" y="{y - 15}" fill="#a8edb4" font-size="12">{aliases[key]}</text>'
    for obj in objects:
        if obj["joint_layout_outline"] is None:
            continue
        color = "#45baff" if obj["geometry_check"]["status"] == "PASS" else "#ff7869"
        points = " ".join(f"{x},{y}" for x, y in obj["joint_layout_outline"])
        svg += f'<polygon points="{points}" fill="{color}" fill-opacity=".65" stroke="{color}"/>'
    return svg + "</svg>"


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(Path(spec_path).read_text())
    inventory = load_locked(root, spec["inventory"])
    aa_model = load_locked(root, spec["AA_model"])
    parent = load_locked(root, spec["parent_model"])
    photos = {}
    for layer, ref in spec["sources"].items():
        if digest(root / ref["path"]) != ref["sha256"]:
            raise ValueError("Changed photograph")
        photos[layer] = cv2.imread(str(root / ref["path"]))
    report = build_correspondences(inventory, aa_model, spec)
    baseline = report
    working_aa, changes = propose_aa_row_alignment(aa_model, spec.get("AA_row_alignments", []))
    if changes:
        report = build_correspondences(inventory, working_aa, spec)
    report["baseline_geometry_counts"] = baseline["geometry_counts"]
    report["AA_working_changes"] = changes
    output.mkdir(parents=True)
    save(output / "spec.json", spec)
    save(output / "report.json", report)
    save(output / "baseline-report.json", baseline)
    save(output / "AA-working-model.json", working_aa)
    model = dict(
        parent_model=spec["parent_model"],
        parent_objects_unchanged=parent["objects"],
        source_inventory=spec["inventory"],
        AA_model=spec["AA_model"],
        AA_working_candidate="AA-working-model.json",
        joint_candidate=report,
        units="AA_working_layout_relative_pixels",
    )
    save(output / "model.json", model)
    sections = []
    source_objects = {o["id"]: o for o in inventory["objects"]}
    aa_by_id = {o["id"]: o for o in aa_model["objects"]}
    for row in inventory["rows"]:
        rid = row["id"]
        folder = output / rid
        folder.mkdir()
        groups = [g for g in report["groups"] if g["scope"] == rid]
        objects = [o for o in report["objects"] if o["scope"] == rid]
        aliases = {g["AA_object_id"]: f"A{i:02}" for i, g in enumerate(groups, 1)}
        for layer, bbox in [("poly", row["bbox"]), ("aa", row["AA_navigation_bbox"])]:
            x, y, r, b = bbox
            raw = photos[layer][y:b, x:r].copy()
            overlay = raw.copy()
            if layer == "poly":
                for i, key in enumerate(row["object_ids"], 1):
                    points = np.array(source_objects[key]["native_outline"]) - [x, y]
                    color = (85, 225, 85) if "approval" in source_objects[key] else (255, 190, 30)
                    cv2.polylines(overlay, [np.rint(points).astype("int32")], True, color, 1)
                    cv2.putText(
                        overlay,
                        f"P{i:03}",
                        tuple(np.rint(points[0] - [0, 3]).astype(int)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.3,
                        color,
                        1,
                    )
            else:
                for key, alias in aliases.items():
                    polygon = source_polygon(aa_by_id[key], aa_model)
                    points = np.array(polygon.exterior.coords) - [x, y]
                    cv2.polylines(
                        overlay, [np.rint(points).astype("int32")], True, (85, 225, 85), 1
                    )
                    cv2.putText(
                        overlay,
                        alias,
                        tuple(np.rint(points[0] - [0, 3]).astype(int)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.35,
                        (85, 225, 85),
                        1,
                    )
            cv2.imwrite(str(folder / f"{layer}-raw.png"), raw)
            cv2.imwrite(str(folder / f"{layer}.png"), overlay)
        (folder / "joint.svg").write_text(joint_svg(objects, working_aa, set(aliases), aliases))
        (folder / "joint-before.svg").write_text(
            joint_svg(
                [o for o in baseline["objects"] if o["scope"] == rid],
                aa_model,
                set(aliases),
                aliases,
            )
        )
        section = (
            f'<section data-scope="{rid}" id="{rid}"><h2>{rid}：'
            f"{len(objects)} 条对应候选</h2><p>照片各保留原始坐标；两图标签表示结构关联，"
            "不表示已像素配准。联合图另用AA设计坐标。蓝色=结构检查通过的候选，红色=约束冲突；"
            "结构PASS不等于人工确认或真实工艺DRC。</p>"
        )
        for mode, title, file in [
            ("poly", "POLY来源及P编号", "poly.png"),
            ("aa", "AA来源及A编号", "aa.png"),
            ("joint", "共同AA设计坐标候选", "joint.svg"),
            ("joint-before", "原AA工作几何的联合检查", "joint-before.svg"),
            ("poly-raw", "POLY原图", "poly-raw.png"),
            ("aa-raw", "AA原图", "aa-raw.png"),
        ]:
            section += (
                f'<div data-mode="{mode}"><h3>{title}</h3><div class="scroll">'
                f'<img src="{rid}/{file}" alt="{title}"></div></div>'
            )
        section += (
            "<table><tr><th>A编号 / AA对象</th><th>POLY来源编号</th>"
            "<th>观察/槽位</th><th>几何检查</th></tr>"
        )
        for group in groups:
            members = [o for o in objects if o["relation_id"] == group["id"]]
            ids = ", ".join(
                f"P{row['object_ids'].index(key) + 1:03} ({key})"
                for key in group["poly_observation_ids"]
            )
            states = ", ".join(
                f"{o['source_poly_id']}: {o['geometry_check']['status']}" for o in members
            )
            section += (
                f"<tr><td>{aliases[group['AA_object_id']]} / {group['AA_object_id']}</td>"
                f"<td>{html.escape(ids)}</td><td>{len(members)}/{group['slot_count']}"
                f"；未观察槽位{group['unobserved_slot_indices']}</td><td>{states}</td></tr>"
            )
        sections.append(section + "</table></section>")
    pending = spec["unresolved"][0]
    for layer in ["poly", "aa"]:
        x, y, r, b = pending[f"{layer}_bbox"]
        cv2.imwrite(str(output / f"wide-{layer}.png"), photos[layer][y:b, x:r])
    page = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>复杂小栅与AA对应复核</title>
<style>body{font:16px sans-serif;max-width:1700px;margin:auto;padding:24px;
background:#18202b;color:#eee}
a{color:#8cddff}select{padding:8px;margin:8px}section{border-top:1px solid #697581;margin-top:30px}
.scroll{overflow:auto}img{height:210px;width:auto;max-width:none}table{border-collapse:collapse;width:100%}
td,th{border:1px solid #637382;padding:7px;text-align:left;overflow-wrap:anywhere}
h3{font-size:16px}</style>
<h1>复杂小栅与AA：显式对应及联合几何候选</h1>"""
    page += (
        f"<p>来源{report['source_observations']}条；已建立AA对应候选{report['assigned_candidates']}条；"
        f"未解决{len(report['unresolved'])}条。几何检查：{report['geometry_counts']}。"
        f"另有{report['unobserved_slots']}个未完整观察槽位，不补画POLY。</p>"
    )
    page += (
        f"<p>原AA工作几何检查：{baseline['geometry_counts']}；"
        f"另存{len(changes)}条AA整排对齐提议。AA原始来源不变，提议未人审。</p>"
    )
    page += """<p>所有来源、原AA与已审联合版图均保留。新关系及设计图未人审；
红色冲突不得自动撤销材料身份或移动AA掩盖。
相对像素预算不是真实PDK规则。</p><p><a href="report.json">完整对应与冲突记录</a> ·
<a href="spec.json">对应依据与参数</a> · <a href="model.json">分离的联合候选模型</a></p>
<select id="scope"><option value="all">全部范围</option>
<option value="wide">宽POLY：AA对应未清楚</option>"""
    for row in inventory["rows"]:
        page += f'<option value="{row["id"]}">{row["id"]}</option>'
    page += """</select><select id="mode"><option value="all">全部视图</option>
<option value="poly">POLY与编号</option>
<option value="aa">AA与编号</option><option value="joint">规则联合候选</option>
<option value="joint-before">调整前AA的联合检查</option>
<option value="poly-raw">POLY原图</option><option value="aa-raw">AA原图</option></select>
<section id="wide" data-scope="wide"><h2>宽POLY身份保持，AA对应暂未建立</h2>
<p>宽POLY身份已确认，但当前AA/POLY的点位对应尚未验证。
必须先核对独立结构标记和实际对应位置，不能据当前选取的AA视窗推断没有AA或判为场区POLY。</p>
<h3>POLY原图上下文</h3><div class="scroll"><img src="wide-poly.png"></div>
<h3>AA原图上下文（未投影）</h3><div class="scroll"><img src="wide-aa.png"></div></section>"""
    page += "".join(sections)
    page += """<script>function update(){const scope=document.getElementById('scope').value;
const mode=document.getElementById('mode').value;
for(const s of document.querySelectorAll('section')){
s.hidden=scope!=='all'&&s.dataset.scope!==scope;
for(const p of s.querySelectorAll('[data-mode]'))p.hidden=mode!=='all'&&p.dataset.mode!==mode;}}
document.getElementById('scope').onchange=update;document.getElementById('mode').onchange=update;
</script></html>"""
    (output / "index.html").write_text(page)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.root, args.spec, args.output)
    print(
        json.dumps(
            {
                key: report[key]
                for key in ["assigned_candidates", "geometry_counts", "unobserved_slots"]
            }
        )
    )
