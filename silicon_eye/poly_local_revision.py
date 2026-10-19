"""Apply explicit object-level POLY corrections without regenerating an array.

Run: python -m silicon_eye.poly_local_revision --root . --spec SPEC --output NEW_DIR
Requires the project environment. Corrections are observations, not a detector.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon

from .geometry_reconstruction import digest, project
from .poly_full_frame import save
from .scene_geometry import load_locked


def geometry_digest(obj):
    value = {key: obj[key] for key in ("native_outline", "layout_outline")}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def apply_revisions(model, revisions):
    """Fail on stale/approved targets; retain every unaddressed object exactly."""
    result = copy.deepcopy(model)
    by_id = {obj["id"]: obj for obj in result["objects"]}
    seen = set()
    for revision in revisions:
        key = revision["object_id"]
        if key in seen or key not in by_id:
            raise ValueError("Duplicate or missing revision target")
        seen.add(key)
        obj = by_id[key]
        if "approval" in obj:
            raise ValueError("Reviewed object requires a separate reviewed revision")
        if geometry_digest(obj) != revision["expected_geometry_sha256"]:
            raise ValueError("Stale target geometry")
        if not revision.get("evidence"):
            raise ValueError("Missing local observation evidence")
        for field in ("native_outline", "layout_outline"):
            points = np.asarray(revision[field], dtype=float)
            if points.shape != (4, 2) or not np.isfinite(points).all():
                raise ValueError("Expected finite ordered quadrilateral")
            polygon = Polygon(points)
            if not polygon.is_valid or polygon.area <= 0:
                raise ValueError("Invalid local geometry")
            if field == "layout_outline":
                delta = np.roll(points, -1, axis=0) - points
                if not np.all((abs(delta[:, 0]) < 1e-8) | (abs(delta[:, 1]) < 1e-8)):
                    raise ValueError("Local layout must remain orthogonal")
        previous = {
            key: copy.deepcopy(obj[key])
            for key in (
                "native_outline",
                "layout_outline",
                "native_to_layout",
                "body_native_outline",
                "body_layout_outline",
                "terminal_extension_side",
                "terminal_shape_status",
            )
            if key in obj
        }
        for field in ("native_outline", "layout_outline"):
            obj[field] = copy.deepcopy(revision[field])
        matrix = cv2.getPerspectiveTransform(
            np.float32(obj["native_outline"]), np.float32(obj["layout_outline"])
        )
        if (
            not np.isfinite(matrix).all()
            or np.max(abs(project(obj["native_outline"], matrix) - np.array(obj["layout_outline"])))
            > 0.003
        ):
            raise ValueError("Invalid revised source correspondence")
        obj["native_to_layout"] = matrix.tolist()
        for field in ("body_native_outline", "body_layout_outline", "terminal_extension_side"):
            obj.pop(field, None)
        obj["terminal_shape_status"] = "explicit_local_extent_candidate"
        obj["terminal_routing"] = "unknown_no_CT_or_net_assignment"
        obj["status"] = "AI_local_revision_not_human_confirmed"
        obj["source_method"] = "explicit_per_object_observation_not_array_interpolation"
        obj["local_revision"] = dict(previous=previous, input=copy.deepcopy(revision))
    # A local correction may not silently collide with an unchanged neighbor.
    polygons = {key: Polygon(obj["layout_outline"]) for key, obj in by_id.items()}
    for key in seen:
        for other, polygon in polygons.items():
            if other != key and polygons[key].intersection(polygon).area > 1e-7:
                raise ValueError("Local revision overlaps a neighbor")
    return result


def annotated(image, bbox, objects, color):
    x, y, r, b = bbox
    result = image[y:b, x:r].copy()
    for obj in objects:
        object_color = (85, 225, 85) if "approval" in obj else color
        points = np.rint(np.array(obj["native_outline"]) - [x, y]).astype(np.int32)
        cv2.polylines(result, [points], True, object_color, 1, cv2.LINE_AA)
        cv2.putText(
            result,
            obj["id"].split("-")[-1],
            tuple(points[0] - [0, 4]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.34,
            object_color,
            1,
            cv2.LINE_AA,
        )
    return result


def check_alignment(objects, families):
    """Check explicit local atlas constraints, never infer gate presence from them."""
    by_id = {obj["id"]: obj for obj in objects}
    for family in families:
        bounds = np.array([Polygon(by_id[key]["layout_outline"]).bounds for key in family["ids"]])
        widths = bounds[:, 2] - bounds[:, 0]
        centers = (bounds[:, 0] + bounds[:, 2]) / 2
        if not np.allclose(widths, family["equal_width_px"]):
            raise ValueError("Local family width mismatch")
        if not np.allclose(np.diff(centers), family["equal_pitch_px"]):
            raise ValueError("Local family pitch mismatch")
        if family["common_top_and_bottom"] and not np.allclose(
            bounds[:, [1, 3]], bounds[0, [1, 3]]
        ):
            raise ValueError("Local family row alignment mismatch")


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(Path(spec_path).read_text())
    parent = load_locked(root, spec["parent_model"])
    if "human_review" in spec:
        load_locked(root, spec["human_review"])
    protected = set(parent.get("confirmed_local_extent_ids", []))
    protected.update(spec.get("protected_object_ids", []))
    if protected.intersection(r["object_id"] for r in spec["revisions"]):
        raise ValueError("Revision targets a protected reviewed object")
    if "AA_model" in spec:
        aa_model = load_locked(root, spec["AA_model"])
        aa_ids = {obj["id"] for obj in aa_model["objects"]}
        if any(r["evidence"].get("AA_target_id") not in aa_ids for r in spec["revisions"]):
            raise ValueError("Missing declared AA target")
    for source in spec["sources"].values():
        if digest(root / source["path"]) != source["sha256"]:
            raise ValueError("Changed source photograph")
    revised = apply_revisions(parent, spec["revisions"])
    revised["confirmed_local_extent_ids"] = sorted(protected)
    if "human_review" in spec:
        revised["local_human_reviews"] = [
            *parent.get("local_human_reviews", []),
            spec["human_review"],
        ]
    check_alignment(revised["objects"], spec.get("local_alignment_sets", []))
    previous = {obj["id"]: obj for obj in parent["objects"]}
    current = {obj["id"]: obj for obj in revised["objects"]}
    changed = [key for key in current if current[key] != previous[key]]
    if set(changed) != {r["object_id"] for r in spec["revisions"]}:
        raise ValueError("Unexpected revision scope")
    output.mkdir(parents=True)
    # This is a derived snapshot; parent layer records remain parent-relative.
    revised["parent_model"] = spec["parent_model"]
    revised["working_reconstruction_layers"] = {
        "inherit_from_parent": spec["parent_model"],
        "local_review": "observation_and_photo_atlas_only_not_joint_design_acceptance",
    }
    observation_by_id = {}
    for case in spec["cases"]:
        for obj in case.get("proposed_objects", []):
            if "approval" in obj:
                continue
            if obj["id"] in observation_by_id and observation_by_id[obj["id"]] != obj:
                raise ValueError("Inconsistent observation across review windows")
            observation_by_id[obj["id"]] = obj
    observations = list(observation_by_id.values())
    for obj in observations:
        points = np.asarray(obj["native_outline"], dtype=float)
        if points.shape != (4, 2) or not np.isfinite(points).all():
            raise ValueError("Invalid unmerged observation")
        polygon = Polygon(points)
        if not polygon.is_valid or polygon.area <= 0:
            raise ValueError("Invalid unmerged observation")
    revised["unmerged_local_observations"] = observations
    save(output / "model.json", revised)
    save(output / "spec.json", spec)
    images = {layer: cv2.imread(str(root / ref["path"])) for layer, ref in spec["sources"].items()}
    sections = []
    for case in spec["cases"]:
        folder = output / case["id"]
        folder.mkdir()
        x, y, r, b = case["poly_bbox"]
        ax, ay, ar, ab = case["aa_bbox"]
        ids = case["object_ids"]
        proposals = case.get("proposed_objects", [])
        edited = any(key in changed for key in ids) or bool(proposals)
        accepted = case.get("review_state") == "human_accepted_displayed_extent"
        views = {
            "poly": images["poly"][y:b, x:r],
            "aa": images["aa"][ay:ab, ax:ar],
            "before": annotated(
                images["poly"], case["poly_bbox"], [previous[key] for key in ids], (0, 190, 255)
            ),
            "after": annotated(
                images["poly"],
                case["poly_bbox"],
                proposals or [current[key] for key in ids],
                (85, 225, 85) if accepted else (255, 190, 30) if edited else (0, 190, 255),
            ),
        }
        for name, image in views.items():
            if image.size == 0:
                raise ValueError("Empty review crop")
            cv2.imwrite(str(folder / f"{name}.png"), image)
        title = html.escape(case["title"])
        for question_region in case.get("question_regions", []):
            a, c, d, e = question_region["bbox"]
            cv2.rectangle(views["after"], (a - x, c - y), (d - x, e - y), (0, 190, 255), 1)
            cv2.putText(
                views["after"],
                question_region["id"],
                (a - x, c - y - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (0, 190, 255),
                1,
            )
        if case.get("question_regions"):
            cv2.imwrite(str(folder / "after.png"), views["after"])
        note = html.escape(case["finding"])
        question = html.escape(case["question"])
        after_title = (
            "已审范围保留（绿）"
            if accepted
            else "独立观察候选（蓝，尚未替换旧对象/编号）"
            if proposals
            else "局部候选（蓝）"
            if edited
            else "旧候选保留待核（未修订）"
        )
        sections.append(
            f'<section id="{case["id"]}"><h2>{case["id"]} · {title}</h2>'
            f"<p>{note}</p><p><b>待核：</b>{question}</p>"
            f"<p>POLY 原生范围 {case['poly_bbox']}；AA 原生范围 {case['aa_bbox']}。"
            "两图仅按结构导航并列，不代表配准或可直接投影。</p>"
            f'<div class="pair"><div>POLY 原图<img src="{case["id"]}/poly.png">'
            f'</div><div>AA 原图上下文<img src="{case["id"]}/aa.png"></div></div>'
            f'<div class="pair"><div>旧候选（橙）<img src="{case["id"]}/before.png">'
            f'</div><div>{after_title}<img src="{case["id"]}/after.png"></div></div>'
            "</section>"
        )
    report = dict(
        changed_ids=changed,
        unchanged_objects=len(current) - len(changed),
        geometry_gate="PASS_for_edited_objects_only" if changed else "no_parent_geometry_changed",
        local_alignment_sets_checked=spec.get("local_alignment_sets", []),
        AA_relationship_gate="not_run_no_fine_registration_or_joint_geometry_for_new_scope",
        recognition_gate="pending_human_review_not_full_frame_accepted",
        no_array_regeneration=True,
        sources_verified=True,
        unaffected_objects_equal=True,
        cases=spec["cases"],
        parent_model=spec["parent_model"],
        scope="native_observations_and_photo_atlas; inherited_joint_design_unchanged",
        unmerged_observation_count=len(observations),
        inventory_review=spec.get("inventory_review"),
    )
    save(output / "report.json", report)
    page = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>上方小 MOS：逐对象局部修订</title><style>
body{font:16px sans-serif;background:#18202b;color:#eee;max-width:1700px;margin:auto;padding:24px}
a{color:#8cddff}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}
section{border-top:1px solid #657081;margin-top:30px;padding-top:10px}
img{width:100%;image-rendering:auto}select,button{padding:9px;margin:5px}
@media(max-width:900px){.pair{grid-template-columns:1fr}}
</style><h1>上方小 MOS：先核查真实栅范围，再局部修订</h1>
<p>蓝色只表示本轮候选，橙色为旧候选；未修改窗口的两图相同，用于诊断。
绿色为人工确认的展示范围；主体身份确认与精确边界确认分别记录。
本轮不声称上方全幅识别通过，也不从亮点推断 CT 归属或电连接。
下方已审联合图、F05 和 U10 均未修改。</p>
<p>照片轮廓与规则版图分开保存；本页仅展示原生来源范围修订，尚未批准并入联合版图。
所有范围仍为像素；AA 作为上下文，不进行未经核准的跨层叠加。</p>
<label>选择核查窗口 <select id="case"></select></label>
<label>层/结果 <select id="view"><option value="all">全部并列</option>
<option value="poly">POLY 原图</option><option value="aa">AA 原图</option>
<option value="before">旧范围</option><option value="after">局部范围</option></select></label>
<p><a href="report.json">范围与检查</a> · <a href="spec.json">持久修订输入</a> ·
<a href="model.json">局部修订模型（包含未改对象）</a></p>
"""
    if "inventory_review" in spec:
        review = spec["inventory_review"]
        page += "<h2>本轮范围与AI复核结论</h2><p>" + html.escape(review["scope"]) + "</p>"
        page += "<p>" + html.escape(review["limitations"]) + "</p>"
        page += '<table border="1" cellpadding="8"><tr><th>原观察范围</th>'
        page += "<th>旧模板槽数</th><th>本轮主体候选数</th><th>复核结论</th></tr>"
        for row in review["rows"]:
            page += "<tr>" + "".join(
                "<td>" + html.escape(str(row[key])) + "</td>"
                for key in ["id", "old_count", "candidate_count", "finding"]
            )
            page += "</tr>"
        page += "</table><h2>需人工裁决的歧义</h2>"
        for question in review["questions"]:
            page += "<p><b>" + html.escape(question["id"]) + "</b>："
            page += html.escape(question["question"]) + "</p>"
    page += "".join(sections)
    page += """<script>
const sel=document.getElementById('case'),view=document.getElementById('view');
sel.add(new Option('全部窗口','all'));
for(const s of document.querySelectorAll('section')){
sel.add(new Option(s.querySelector('h2').textContent,s.id));}
function update(){for(const s of document.querySelectorAll('section')){
s.hidden=sel.value!=='all'&&sel.value!==s.id;
for(const pair of s.querySelectorAll('.pair')){
pair.style.gridTemplateColumns=view.value==='all'?'1fr 1fr':'1fr';}
for(const img of s.querySelectorAll('img')){
const kind=img.getAttribute('src').split('/').pop().split('.')[0];
img.parentElement.hidden=view.value!=='all'&&view.value!==kind;}}}
sel.onchange=view.onchange=update;</script></html>"""
    (output / "index.html").write_text(page)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.spec, args.output), ensure_ascii=False))
