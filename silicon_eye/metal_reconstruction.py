"""Build a source-bound orthogonal metal pilot, without adopting electrical connections.

Run: python -m silicon_eye.metal_reconstruction --spec SPEC --output NEW_DIRECTORY
Requires existing project dependencies; consumes AI observations, not automatic segmentation.
"""

from __future__ import annotations

import argparse
import html
import json
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Polygon, box

from .ct_transfer import apply_reviewed_record_changes
from .geometry_reconstruction import digest, object_polygon
from .joint_layers import load_snapshot
from .layer_review import model_svg, write_json
from .review_package import Inputs


def stroke(points, width):
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) < 2 or not np.isfinite(pts).all():
        raise ValueError("A metal path needs finite xy vertices")
    edges = np.diff(pts, axis=0)
    if not np.isfinite(width) or width <= 0 or np.any(np.all(edges == 0, axis=1)):
        raise ValueError("Invalid metal width or repeated vertex")
    if np.any(np.all(edges != 0, axis=1)) or not LineString(pts).is_simple:
        raise ValueError("Design path must be simple and orthogonal")
    return LineString(pts).buffer(width / 2, cap_style="square", join_style="mitre")


def feature_polygon(obj, minimum_width=0):
    """Keep one conductor ID while adding connected, source-bound local geometry."""
    p = stroke(obj["design_path"], obj["design_width"])
    seen = set()
    for part in obj.get("local_parts", []):
        if part["id"] in seen or not part.get("basis"):
            raise ValueError("Duplicate or unsupported local metal part")
        seen.add(part["id"])
        bounds = np.asarray(part["bounds"], dtype=float)
        if bounds.shape != (4,) or not np.isfinite(bounds).all():
            raise ValueError("Local part needs finite bounds")
        left, top, right, bottom = bounds
        if right <= left or bottom <= top or min(right - left, bottom - top) < minimum_width:
            raise ValueError("Local metal part is collapsed or below minimum width")
        extra = box(*bounds)
        if p.intersection(extra).area <= 1e-8:
            raise ValueError("Local part must join the existing conductor with positive area")
        p = p.union(extra)
    if p.geom_type != "Polygon" or not p.is_valid:
        raise ValueError("Local metal revision produced invalid or disconnected material")
    return p


def reviewed_features(root, inputs, spec):
    """Replay exact scoped changes, without promoting approval to unrelated geometry."""
    if not spec.get("reviewed_revision"):
        return None
    revision = spec["reviewed_revision"]
    parent = inputs.document(revision["parent_spec"])
    review = inputs.human(revision["human_review"])
    if revision.get("before_preview"):
        inputs.read(revision["before_preview"])
    for field in (
        "snapshot",
        "budget",
        "source_windows",
        "design_bounds",
        "column_correspondence",
        "pending_gate_CT_ids",
    ):
        if spec[field] != parent[field]:
            raise ValueError("Reviewed M1 revision changed fixed context: " + field)
    inherited_claims = parent["CT_support_candidates"]
    if spec["CT_support_candidates"][: len(inherited_claims)] != inherited_claims:
        raise ValueError("Reviewed M1 revision dropped or changed earlier CT support")
    expected = apply_reviewed_record_changes(
        parent["features"], revision["changes"], review["authorized_feature_ids"]
    )
    if expected != spec["features"]:
        raise ValueError("Reviewed M1 changes do not reproduce feature records")
    before = {f["id"]: f for f in parent["features"]}
    after = {f["id"]: f for f in spec["features"]}
    for key in review["preserve_exact_feature_ids"]:
        if after.get(key) != before[key]:
            raise ValueError("Reviewed M1 revision changed a protected feature")
    for key in review["authorized_feature_ids"]:
        for field in ("design_path", "design_width", "source_path", "end_states"):
            if after[key][field] != before[key][field]:
                raise ValueError("Local M1 correction changed an accepted skeleton")
    return review


def design_canvas_bounds(canvas_wh, bounds=None):
    """A signed viewport may grow left without changing design coordinates."""
    if bounds is None:
        return [0, 0, *canvas_wh]
    values = np.asarray(bounds, dtype=float)
    if (values.shape != (4,) or not np.isfinite(values).all()
            or len(canvas_wh) != 2 or values[2] - values[0] != canvas_wh[0]
            or values[3] - values[1] != canvas_wh[1]
            or min(canvas_wh) <= 0 or (values[:2] > 0).any() or (values[2:] < 0).any()):
        raise ValueError("Invalid signed design canvas bounds")
    return list(bounds)


def geometry_audit(features, budget, canvas_wh, canvas_bounds=None):
    errors, polygons = [], []
    viewport = box(*design_canvas_bounds(canvas_wh, canvas_bounds))
    ids = [o["id"] for o in features]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate metal ID")
    for obj in features:
        p = feature_polygon(obj, budget["minimum_width_px"])
        polygons.append(p)
        if obj["design_width"] < budget["minimum_width_px"]:
            errors.append(dict(id=obj["id"], reason="minimum_width_failed"))
        if not viewport.covers(p):
            errors.append(dict(id=obj["id"], reason="outside_canvas"))
        if not p.is_valid or p.geom_type != "Polygon":
            errors.append(dict(id=obj["id"], reason="invalid_or_disconnected"))
    gaps = []
    for i, a in enumerate(polygons):
        for j, b in enumerate(polygons[i + 1 :], i + 1):
            gap = a.distance(b)
            gaps.append(dict(ids=[ids[i], ids[j]], gap_px=gap))
            if a.intersects(b) or gap < budget["minimum_gap_px"] - 1e-6:
                errors.append(dict(ids=[ids[i], ids[j]], reason="unexpected_join_or_gap_failed"))
    return dict(
        status="FAIL" if errors else "PASS",
        errors=errors,
        pair_gaps=gaps,
        minimum_gap_px=min((g["gap_px"] for g in gaps), default=None),
    ), polygons


def column_correspondence(check):
    """Only qualify the declared x-column relation; never infer a 2-D transform."""
    fit, hold = check["fit"], check["holdout"]
    if len(fit) < 2 or not hold:
        raise ValueError("Need separate fit and holdout column observations")
    if {p["id"] for p in fit} & {p["id"] for p in hold}:
        raise ValueError("Holdout column was used to fit")
    a, b = np.polyfit([p["m1_x"] for p in fit], [p["poly_x"] for p in fit], 1)
    if not np.isfinite([a, b]).all() or a <= 0:
        raise ValueError("Invalid local column ordering")
    rows = [
        dict(**p, predicted_poly_x=a * p["m1_x"] + b, error_px=abs(a * p["m1_x"] + b - p["poly_x"]))
        for p in hold
    ]
    ok = max(p["error_px"] for p in rows) <= check["tolerance_native_px"] + 1e-6
    return dict(
        x_status="PASS" if ok else "FAIL",
        affine_x=[a, b],
        holdout=rows,
        scope=check["scope"],
        source="AI_column_observations_not_human_mapping",
        y_status="NOT_QUALIFIED",
        precise_CT_projection_allowed=False,
    )


def contact_audit(features, polygons, contacts, claims, enclosure):
    by_ct = {o["id"]: o for o in contacts}
    by_metal = {o["id"]: p for o, p in zip(features, polygons, strict=True)}
    rows = []
    seen = set()
    for claim in claims:
        p = by_metal[claim["metal_id"]]
        ids = claim["contact_ids"]
        if not ids or len(set(ids)) != len(ids) or seen & set(ids):
            raise ValueError("Empty or duplicate CT support claim")
        seen.update(ids)
        failed = [
            key
            for key in ids
            if not p.covers(
                Polygon(by_ct[key]["layout_outline"]).buffer(enclosure, join_style="mitre")
            )
        ]
        rows.append(
            dict(
                metal_id=claim["metal_id"],
                CT_count=len(ids),
                geometry_status="FAIL" if failed else "PASS",
                failed_ids=failed,
                identity_status="AI_candidate_not_M1_human_approved",
                electrical_connection_confirmed=False,
            )
        )
    return rows


def source_view(photo, bounds, features, output):
    raw = photo.crop(bounds).convert("RGB")
    overlay = raw.copy()
    d = ImageDraw.Draw(overlay)
    for obj in features:
        points = [(x - bounds[0], y - bounds[1]) for x, y in obj["source_path"]]
        d.line(points, fill=obj["color"], width=2)
        for x, y in points:
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=obj["color"])
        x, y = points[len(points) // 2]
        d.text((x + 4, y + 4), obj["label"], fill=obj["color"], stroke_width=1)
    raw.save(output / "m1-raw.png")
    overlay.save(output / "m1-observations.png")
    overview = photo.convert("RGB")
    overview.thumbnail((1100, 900))
    sx, sy = overview.width / photo.width, overview.height / photo.height
    ImageDraw.Draw(overview).rectangle(
        (bounds[0] * sx, bounds[1] * sy, bounds[2] * sx, bounds[3] * sy),
        outline="#ff5577",
        width=3,
    )
    overview.save(output / "m1-location.png")


def design_preview(snapshot, features, polygons, bounds, output):
    """Raster companion for direct inspection; use the exact vector polygons."""
    left, top, right, bottom = bounds
    scale = 2
    size = (int((right - left) * scale), int((bottom - top) * scale))
    canvas = Image.new("RGBA", size, "#111f2d")
    viewport = box(*bounds)

    def paint(p, color, alpha=155):
        if not p.intersects(viewport):
            return
        mask = Image.new("L", size)
        draw = ImageDraw.Draw(mask)
        draw.polygon(
            [((x - left) * scale, (y - top) * scale) for x, y in p.exterior.coords], fill=alpha
        )
        for ring in p.interiors:
            draw.polygon([((x - left) * scale, (y - top) * scale) for x, y in ring.coords], fill=0)
        canvas.paste(color, (0, 0), mask)

    for obj in snapshot["materials"]["AA_objects"]:
        paint(object_polygon(obj), "#5ab987")
    for obj in snapshot["materials"]["objects"]:
        paint(Polygon(obj["layout_outline"]), "#e9ac58")
    for obj in snapshot["contacts"]:
        paint(Polygon(obj["layout_outline"]), "#ffffff", 255)
    for obj, p in zip(features, polygons, strict=True):
        paint(p, obj["color"], 110)
        d = ImageDraw.Draw(canvas)
        for ring in [p.exterior, *p.interiors]:
            d.line(
                [((x - left) * scale, (y - top) * scale) for x, y in ring.coords],
                fill=obj["color"],
                width=2,
            )
        x, y = p.representative_point().coords[0]
        d.text(((x - left) * scale + 6, (y - top) * scale), obj["label"], fill="white")
    canvas.convert("RGB").save(output / "joint-design.png")


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or not output.is_relative_to(root):
        raise ValueError("Output must be new and inside project")
    spec = json.loads(Path(spec_path).read_text())
    if spec["kind"] != "metal_geometry_pilot" or spec["layer"] != "M1":
        raise ValueError("Pilot currently supports declared M1 only")
    inputs = Inputs(root)
    inputs.read(spec["snapshot"])
    snapshot = load_snapshot(root, root / spec["snapshot"]["path"])
    for ref in snapshot["manifest"]["inputs"].values():
        inputs.read(ref)
    for ref in snapshot["manifest"]["source_photos"].values():
        inputs.read(ref)
    for ref in spec["evidence"].values():
        inputs.read(ref)
    human_review = reviewed_features(root, inputs, spec)
    features = spec["features"]
    geometry, polygons = geometry_audit(features, spec["budget"], snapshot["manifest"]["canvas_wh"])
    correspondence = column_correspondence(spec["column_correspondence"])
    landings = contact_audit(
        features,
        polygons,
        snapshot["contacts"],
        spec["CT_support_candidates"],
        spec["budget"]["CT_enclosure_px"],
    )
    pending = spec["pending_gate_CT_ids"]
    active_ct = {c["id"] for c in snapshot["contacts"]}
    if not set(pending) <= active_ct:
        raise ValueError("Unknown pending gate CT")
    for frame, bounds in spec["source_windows"].items():
        if frame not in snapshot["manifest"]["source_photos"]:
            raise ValueError("Unknown photo frame")
        path = root / snapshot["manifest"]["source_photos"][frame]["path"]
        with Image.open(path) as im:
            if not (
                0 <= bounds[0] < bounds[2] <= im.width and 0 <= bounds[1] < bounds[3] <= im.height
            ):
                raise ValueError("Native review window outside source")
            if frame == "m1":
                viewport = box(*bounds)
                if any(not viewport.covers(LineString(o["source_path"])) for o in features):
                    raise ValueError("M1 window omits observed path")
    geom_fail = (
        correspondence["x_status"] == "FAIL"
        or geometry["status"] == "FAIL"
        or any(r["geometry_status"] == "FAIL" for r in landings)
    )
    report = dict(
        status="FAIL"
        if geom_fail
        else ("SCOPED_REVIEWED_WITH_LIMITATIONS" if human_review else "REVIEW_REQUIRED"),
        geometry=geometry,
        column_correspondence=correspondence,
        CT_support_candidates=landings,
        pending_gate_CT_ids=pending,
        human_questions=spec["human_questions"],
        precise_CT_projection_allowed=False,
        source_to_design_transform=None,
        topology_status="AI_photo_observation_candidates_not_electrical_confirmation",
        automatic_network_export_allowed=False,
        whole_frame_complete=False,
        physical_PDK_DRC=False,
        parent_snapshot_unchanged=True,
        scoped_human_review=human_review,
        requires_user_action_now=bool(spec["human_questions"]),
    )
    model = dict(
        kind="metal_geometry_companion_candidate",
        layer="M1",
        canvas_wh=snapshot["manifest"]["canvas_wh"],
        parent_snapshot=spec["snapshot"],
        coordinate_space="shared_design_px",
        processed_scope=spec["design_bounds"],
        object_count=len(features),
        objects=[
            dict(
                **o,
                layer="M1",
                outer_xy=list(p.exterior.coords),
                holes_xy=[list(r.coords) for r in p.interiors],
                status=(
                    "scoped_structure_human_reviewed_geometry_candidate"
                    if human_review
                    else "AI_candidate_not_human_approved"
                ),
                reviewed_structure_scope=(human_review or {})
                .get("feature_scopes", {})
                .get(o["id"]),
                net_id=None,
            )
            for o, p in zip(features, polygons, strict=True)
        ],
        unprocessed_is_unknown=True,
        adopted_into_joint_snapshot=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".metal-pilot-", dir=output.parent) as tmp:
        stage = Path(tmp) / "delivery"
        stage.mkdir()
        write_json(stage / "spec.json", spec)
        write_json(stage / "model.json", model)
        write_json(stage / "report.json", report)
        write_json(
            stage / "continuation-context.json",
            dict(
                snapshot_id=snapshot["manifest"]["id"],
                budget=snapshot["manifest"]["budget"],
                inherited_documents={
                    k: v
                    for k, v in snapshot["values"].items()
                    if k not in {"materials", "contacts", "AA_context"}
                },
                adoption_status="not_adopted",
                automatic_network_export_allowed=False,
                M1_scoped_review=human_review,
            ),
        )
        for frame, bounds in spec["source_windows"].items():
            with Image.open(root / snapshot["manifest"]["source_photos"][frame]["path"]) as im:
                if frame == "m1":
                    source_view(im, bounds, features, stage)
                else:
                    im.crop(bounds).save(stage / (frame + "-raw.png"))
        svg = model_svg(snapshot, spec["design_bounds"]).replace("</svg>", "")
        svg += '<g data-layer="M1" fill-opacity=".35" stroke-width="1.4">'
        for obj, p in zip(features, polygons, strict=True):
            path = " ".join(
                "M" + " L".join(f"{x},{y}" for x, y in ring.coords) + " Z"
                for ring in [p.exterior, *p.interiors]
            )
            svg += f'<path d="{path}" fill="{obj["color"]}" stroke="{obj["color"]}" '
            svg += f'fill-rule="evenodd"><title>{html.escape(obj["id"])}</title></path>'
            x, y = p.representative_point().coords[0]
            svg += f'<text x="{x + 4}" y="{y}" fill="white" font-size="9">{obj["label"]}</text>'
        svg += "</g></svg>"
        (stage / "joint-design.svg").write_text(svg)
        design_preview(snapshot, features, polygons, spec["design_bounds"], stage)
        before_preview = spec.get("reviewed_revision", {}).get("before_preview")
        if before_preview:
            (stage / "before-design.png").write_bytes(inputs.read(before_preview))
        question_list = "".join(
            f"<li><b>{html.escape(q['id'])}</b>：{html.escape(q['question'])}</li>"
            for q in spec["human_questions"]
        )
        page = """<!doctype html><html lang="zh"><meta charset="utf-8"><title>M1规则几何小样</title>
<style>body{background:#14202d;color:#eee;font:16px sans-serif;margin:22px}a{color:#81cfff}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(390px,1fr));gap:20px}
img,svg{width:100%;height:auto;background:#0c1825}label,button{margin:8px}button{padding:8px}
.card{border:1px solid #536272;padding:12px}p,li{line-height:1.6}</style>
<h1>M1规则几何小样：Q2上左阶梯组</h1>
<p>沿用当前AA／POLY／CT。人工结构批准与新边界候选分开保存，未确认整网。窗口用于检查，右侧延伸保持未知。</p>
<p>局部仅检查了x线列对应；y与精确孔位投影未放行。因此原图与设计图并列，不作CT到M1照片的伪精确叠图。</p>
"""
        page += f"<p>金属几何：{geometry['status']}；CT模型包围："
        page += f"{sum(r['CT_count'] for r in landings)}孔；总体：{report['status']}。</p>"
        if human_review:
            statements = "".join(
                "<li>" + html.escape(s) + "</li>" for s in human_review["verbatim_feedback"]
            )
            page += '<div class="card"><h2>已记录本轮裁决</h2><ul>' + statements + "</ul>"
            page += "<p>已补外U两端短横段，内U原横段仅细化CT包围；P08只加宽左竖段。"
            page += "具体补条尺寸／左竖宽度为AI实施值，不扩大人工批准。</p>"
            page += "<p>无新增审批问题；精确照片投影仍待定。</p></div>"
        if question_list:
            page += (
                '<div class="card"><h2>本轮一次核对清单</h2><ol>' + question_list + "</ol></div>"
            )
        if before_preview:
            page += "<details><summary>查看修订前设计图（原始待审版）</summary>"
            page += '<img src="before-design.png"></details>'
        for layer in ("AA", "POLY", "CT", "M1", "unknown"):
            page += f'<label><input type="checkbox" checked data-toggle="{layer}">{layer}</label>'
        page += '<details><summary>查看M1全图定位</summary><img src="m1-location.png"></details>'
        page += '<div class="grid"><div><h2>共同设计坐标：规则几何候选</h2>' + svg + "</div>"
        page += "<div><h2>M1源图：宽上下文／可切观察线</h2>"
        page += '<button id="raw">原图</button><button id="observations">AI观察线</button>'
        page += '<img id="m1" src="m1-raw.png"><p>观察线只记录走向，不是精确金属边界。</p></div>'
        page += '<div><h2>POLY源图：已审CT所在结构</h2><img src="poly-raw.png"></div>'
        page += '<div><h2>AA源图：独立背景参考</h2><img src="aa-raw.png"></div></div>'
        page += '<p><a href="model.json">M1候选数据</a> · <a href="report.json">质量门与未决</a> · '
        page += '<a href="continuation-context.json">原裁决与六处未知</a></p>'
        page += """<script>
document.querySelectorAll('[data-toggle]').forEach(e=>e.onchange=()=>{
 document.querySelectorAll('[data-layer="'+e.dataset.toggle+'"]').forEach(g=>
 g.style.display=e.checked?'':'none');});
document.getElementById('raw').onclick=()=>document.getElementById('m1').src='m1-raw.png';
document.getElementById('observations').onclick=()=>
 document.getElementById('m1').src='m1-observations.png';</script></html>"""
        (stage / "index.html").write_text(page)
        write_json(
            stage / "manifest.json",
            dict(
                parent_snapshot=spec["snapshot"],
                verified_inputs=inputs.files,
                spec_sha256=digest(spec_path),
                code_sha256=digest(__file__),
                artifacts={p.name: digest(p) for p in stage.iterdir()},
                no_parent_model_change=True,
                status=report["status"],
            ),
        )
        stage.rename(output)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.root, args.spec, args.output)
    print(json.dumps(dict(status=result["status"], geometry_status=result["geometry"]["status"])))
    if result["status"] == "FAIL":
        raise SystemExit(2)
