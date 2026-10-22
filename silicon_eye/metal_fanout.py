"""Validate reviewed metal fanout with source-bound local relative geometry.

Run: python -m silicon_eye.metal_fanout --request REQUEST --output NEW_DIRECTORY
Requires project dependencies. Replays scoped human edges, not fresh recognition;
local geometry is deliberately separate from the common material coordinate space.
"""

from __future__ import annotations

import argparse
import html
import json
import tempfile
from pathlib import Path

from shapely.geometry import Point, Polygon, box

from .conductive_layers import COLORS, geometry, svg_layers
from .geometry_reconstruction import digest
from .joint_layers import load_snapshot
from .layer_review import write_json
from .metal_reconstruction import geometry_audit
from .metal_via_pilot import interface_audit, preview, source_panels
from .review_package import Inputs, pointer


def fanout_inventory(branches):
    """Several via groups to one lower segment still count as one lower conductor."""
    inventory = {}
    for branch in branches:
        key = branch["lower_metal_id"]
        inventory.setdefault(key, set()).add(branch["via_group_id"])
    return [
        {"lower_metal_id": key, "via_group_ids": sorted(groups)}
        for key, groups in sorted(inventory.items())
    ]


def validate(root, request, inputs=None):
    """Count distinct lower conductors, not via markers or projected intersections."""
    inputs = inputs or Inputs(root)
    if request["kind"] != "reviewed_metal_fanout_validation":
        raise ValueError("Expected a reviewed fanout request")
    inputs.read(request["parent_snapshot"])
    parent = load_snapshot(root, Path(root) / request["parent_snapshot"]["path"])
    if not parent.get("conductors", {}).get("source_identity_gate", {}).get("status") == "PASS":
        raise ValueError("Fanout must continue a source-corrected conductive baseline")
    inputs.read(parent["manifest"]["conductive_layers"])
    for frame in request["layer_stack"][::2]:
        inputs.read(parent["manifest"]["source_photos"][frame.lower()])
    evidence = {}
    for key, ref in request["evidence"].items():
        document = inputs.document(ref)
        inputs.evidence(document)
        evidence[key] = document
    reviews = {k: inputs.human(ref) for k, ref in request["human_reviews"].items()}

    def reviewed(binding):
        return pointer(reviews[binding["review"]], binding["pointer"])

    lower, via, upper = request["layer_stack"]
    if (lower, via, upper) not in {("M1", "V1", "M2"), ("M2", "V2", "M3")}:
        raise ValueError("Unsupported layer pair")
    policy = parent["conductors"]["source_identity_policy"]
    if policy.get(lower.lower()) != via:
        raise ValueError("Via evidence frame identity mismatch")
    features = request["features_by_layer"]
    if set(features) != {lower, upper}:
        raise ValueError("Fanout metal layer inventory mismatch")
    objects = {k: [] for k in COLORS}
    polygons, records, audits = {}, {}, {}
    for layer, rows in features.items():
        audits[layer], ps = geometry_audit(rows, request["metal_budget"], request["canvas_wh"])
        for record, poly in zip(rows, ps, strict=True):
            if record["id"] in records or record["source_frame"] != layer.lower():
                raise ValueError("Duplicate object or wrong metal source frame")
            records[record["id"]], polygons[record["id"]] = record, poly
            objects[layer].append(
                dict(
                    id=record["id"],
                    layer=layer,
                    kind="metal",
                    geometry=dict(geometry(poly), status="local_candidate_not_registered"),
                    role=record["role"],
                    input_package=request["parent_snapshot"],
                    geometry_status="local_candidate_not_common_canvas_registration",
                )
            )
    target = request["upper_metal_id"]
    if target not in {r["id"] for r in features[upper]}:
        raise ValueError("Missing selected upper metal")
    branches, seen, used_lower = [], set(records), set()
    for claim in request["branches"]:
        edge = reviewed(claim["review_binding"])
        if edge.get("status") != "confirmed" or edge["upper_conductor"] != target:
            raise ValueError("Unreviewed or reassigned fanout destination")
        a, v = edge["lower_conductor"], edge["via_id"]
        if a not in {r["id"] for r in features[lower]} or v in seen:
            raise ValueError("Missing lower conductor or duplicate via ID")
        seen.add(v)
        source = pointer(
            evidence[claim["evidence_binding"]["source"]], claim["evidence_binding"]["pointer"]
        )
        if (
            source[lower + "_id"] != a
            or source[via + "_id"] != v
            or claim["source_frame"] != lower.lower()
            or claim["source_xy"] != source[lower.lower() + "_native_xy"]
        ):
            raise ValueError("Via source/owner mismatch")
        document = evidence[claim["evidence_binding"]["source"]]
        if (
            document[upper + "_id"] != target
            or document["sources"][lower.lower()]
            != parent["manifest"]["source_photos"][lower.lower()]
            or document["sources"]["human_review"]
            != request["human_reviews"][claim["review_binding"]["review"]]
        ):
            raise ValueError("Fanout inventory belongs to another photo, carrier or review")
        if not box(*claim["source_bounds"]).covers(Point(claim["source_xy"])):
            raise ValueError("Source support omits via reference point")
        # A single support box is not a measured single cut or a complete hole array.
        cut = dict(
            id=v,
            layer=via,
            layer_pair=[lower, upper],
            lower_metal_id=a,
            upper_metal_id=target,
            observation_id=source["id"],
            bounds=claim["design_support_bounds"],
        )
        check = interface_audit(
            [cut],
            polygons[a],
            polygons[target],
            request["via_budget"],
            layer_stack=(lower, via, upper),
        )
        if check["status"] != "PASS":
            raise ValueError("Fanout support fails double metal enclosure")
        objects[via].append(
            dict(
                id=v,
                layer=via,
                kind="via_group_support_proxy",
                geometry=dict(
                    geometry(box(*cut["bounds"])), status="local_support_not_measured_cut"
                ),
                role="reviewed_chain",
                input_package=request["evidence"][claim["evidence_binding"]["source"]],
                source_frame=lower.lower(),
                source_photo=parent["manifest"]["source_photos"][lower.lower()],
                source_xy=claim["source_xy"],
                physical_cut_count=None,
            )
        )
        used_lower.add(a)
        branches.append(
            dict(
                id=edge["id"],
                lower_metal_id=a,
                upper_metal_id=target,
                via_group_id=v,
                human_review=claim["review_binding"],
                status="inherited_human_confirmed_local_interface",
            )
        )
    if len(used_lower) < 2:
        raise ValueError("Fanout needs at least two distinct reviewed lower conductors")
    active = {target, *used_lower}
    if {
        r["id"] for rows in features.values() for r in rows if r["role"] == "reviewed_chain"
    } != active:
        raise ValueError("Context cannot silently join the reviewed fanout")
    excluded = []
    for claim in request["excluded_attachments"]:
        a = claim["lower_metal_id"]
        if (
            reviewed(claim["review_binding"]) != "excluded"
            or a in used_lower
            or a not in {r["id"] for r in features[lower]}
            or records[a]["role"] != "context_only"
            or claim["upper_metal_id"] != target
        ):
            raise ValueError("Excluded attachment contradicts the reviewed fanout")
        excluded.append(
            dict(
                lower_metal_id=a,
                upper_metal_id=target,
                projected_overlap=polygons[a].intersects(polygons[target]),
                direct_attachment="human_excluded_in_reviewed_span",
                global_same_net_status="unknown",
            )
        )
    sweep = request["interior_sweep"]
    if (
        sweep["upper_metal_id"] != target
        or reviewed(sweep["review_binding"]) != "absent_in_reviewed_conductor_span"
    ):
        raise ValueError("Missing scoped middle-span review")
    # Across all support groups also reject overlaps; array pitch is local to each group.
    supports = objects[via]
    for i, a in enumerate(supports):
        for b in supports[i + 1 :]:
            p, q = (Polygon(o["geometry"]["outer_xy"]) for o in (a, b))
            if p.intersects(q) or p.distance(q) < request["via_budget"]["minimum_cut_gap_px"]:
                raise ValueError("Overlapping or insufficiently separated via supports")
    if any(a["status"] != "PASS" for a in audits.values()):
        raise ValueError("Metal continuity or same-layer isolation failed")
    model = dict(
        schema_version=1,
        kind="reviewed_local_fanout_validation",
        parent_snapshot=request["parent_snapshot"],
        coordinate_space="local_relative_design_px",
        canvas_wh=request["canvas_wh"],
        objects_by_layer=objects,
        reviewed_branches=branches,
        excluded_attachments=excluded,
        source_to_design_transform=None,
        common_canvas_placement=None,
        automatic_network_export_allowed=False,
        net_edges=[],
        physical_cut_count=None,
        fanout_inventory=fanout_inventory(branches),
    )
    report = dict(
        status="KNOWN_REVIEWED_FANOUT_REPLAY_PASS",
        geometry_audits=audits,
        reviewed_attachment_count=len(branches),
        distinct_lower_metal_count=len(fanout_inventory(branches)),
        via_support_group_count=len(supports),
        physical_cut_count=None,
        middle_span="human_reviewed_no_additional_lower_attachment",
        excluded_attachments=excluded,
        complete_network=False,
        new_physical_connections=0,
        human_statements={key: r["statement"] for key, r in reviews.items()},
        fresh_blind_recognition=False,
        source_correspondence_status="NOT_QUALIFIED",
        automatic_network_export_allowed=False,
        physical_PDK_DRC=False,
        parent_conductive_objects_preserved=sum(
            len(v) for v in parent["conductors"]["objects_by_layer"].values()
        ),
        parent_snapshot_unchanged=True,
        human_questions=[],
        requires_user_action_now=False,
        unresolved=request["limits"],
    )
    return model, report, parent


def review_page(svg, request, model, report):
    template = Path(__file__).with_name("metal_via_pilot.html").read_text()
    style = template[template.index("<style>") : template.index("</style>") + 8]
    script = template[template.index("<script>") : template.index("</script>") + 9]
    esc = html.escape
    page = '<!doctype html><html lang="zh"><meta charset="utf-8">'
    page += '<meta name="viewport" content="width=device-width,initial-scale=1">'
    page += "<title>高层金属分支复核</title>" + style
    lower, _, upper = request["layer_stack"]
    count = report["distinct_lower_metal_count"]
    page += f"<h1>一根 {upper} → {count} 根 {lower}：已审分支回放</h1>"
    page += '<div class="card"><p>沿用历史人工裁决，无需重复审批：</p>'
    for statement in report["human_statements"].values():
        page += "<blockquote>" + esc(statement) + "</blockquote>"
    page += "<p>这是已知案例的工具验证，不计作新发现。"
    page += f"当前五层基准{report['parent_conductive_objects_preserved']}条记录完整保留。</p></div>"
    page += '<p class="notice">下图是独立局部规则几何候选，没有放入共同 AA／POLY 画布。'
    page += "孔方块是组支持区，不能解读为各只有一个孔；孔数、精确边界、出窗走线和更高层仍未知。"
    page += "原生照片分开显示，不执行未经核准的投影。遮挡处连续性来自人工裁决。</p>"
    page += '<div class="legend">'
    for layer in request["layer_stack"]:
        page += f'<label><input type="checkbox" checked data-toggle="{layer}">{layer}</label>'
    page += '<label><input type="checkbox" id="context" checked>淡色隔离上下文</label></div>'
    page += svg + "<p>各层按颜色区分。上下层几何交叠不自动产生连接；淡色为隔离上下文。</p>"
    page += "<table><tr><th>接口</th><th>下层</th><th>Via组</th><th>上层</th></tr>"
    for row in model["reviewed_branches"]:
        page += (
            "<tr>"
            + "".join(
                "<td>" + esc(str(row[k])) + "</td>"
                for k in ("id", "lower_metal_id", "via_group_id", "upper_metal_id")
            )
            + "</tr>"
        )
    page += '</table><h2>证据原图及宽局部</h2><button id="raw">原图</button>'
    page += '<button id="marked">观察标记</button><div class="grid">'
    for mode in ("wide", "detail"):
        for frame in request["source_windows"]:
            key = frame + "-" + mode
            page += (
                f"<div><h2>{frame.upper()} {mode} · {request['source_windows'][frame][mode]}</h2>"
            )
            page += f'<a data-image="{key}" href="{key}-marked.png"><img data-source="{key}" '
            page += f'src="{key}-marked.png"></a></div>'
    page += "</div><h2>仍保留的范围限制</h2><ul>"
    page += "".join("<li>" + esc(s) + "</li>" for s in request["limits"]) + "</ul>"
    page += '<p><a href="model.json">局部分支数据</a> · <a href="report.json">质量检查</a> · '
    page += '<a href="manifest.json">来源锁与产物</a> · '
    page += '<a href="../conductive-stack-v2/index.html">保持不变的五层基准</a></p>'
    return (
        page
        + script
        + """<script>
document.getElementById('context').onchange=e=>document.querySelectorAll('[data-context]')
.forEach(p=>p.style.display=e.target.checked?'':'none');
</script></html>"""
    )


def deliver(root, request_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or not output.is_relative_to(root):
        raise ValueError("Output must be new and inside project")
    inputs = Inputs(root)
    ref = dict(
        path=str(Path(request_path).resolve().relative_to(root)), sha256=digest(request_path)
    )
    request = inputs.document(ref)
    model, report, parent = validate(root, request, inputs)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".metal-fanout-", dir=output.parent) as tmp:
        stage = Path(tmp) / "delivery"
        stage.mkdir()
        for name, value in (("request", request), ("model", model), ("report", report)):
            write_json(stage / (name + ".json"), value)
        b = request["design_bounds"]
        viewbox = f"{b[0]} {b[1]} {b[2] - b[0]} {b[3] - b[1]}"
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}">'
        svg += '<rect width="100%" height="100%" fill="#0b1724"/>' + svg_layers(model, b)
        branch_labels = {r["lower_metal_id"]: r["id"] for r in model["reviewed_branches"]}
        for layer, rows in model["objects_by_layer"].items():
            for row in rows:
                if row["kind"] != "metal":
                    continue
                p = Polygon(row["geometry"]["outer_xy"])
                context = ' data-context="true"' if row["role"] == "context_only" else ""
                if layer == request["layer_stack"][2]:
                    label, x, y = layer + " shared", p.centroid.x, p.bounds[1] - 8
                else:
                    label = branch_labels.get(row["id"], "context")
                    x, y = p.bounds[0], p.bounds[3] + 20
                svg += f'<text data-layer="{layer}"{context} x="{x}" y="{y}" '
                svg += f'fill="{COLORS[layer]}" font-size="14">{html.escape(label)}</text>'
        svg += "</svg>"
        (stage / "local-design.svg").write_text(svg)
        groups = []
        for layer in (
            request["layer_stack"][0],
            request["layer_stack"][2],
            request["layer_stack"][1],
        ):
            for role in ("context_only", "reviewed_chain"):
                ps = [
                    (o["id"], Polygon(o["geometry"]["outer_xy"]))
                    for o in model["objects_by_layer"][layer]
                    if o["role"] == role
                ]
                alpha = 30 if role == "context_only" else (255 if "V" in layer else 120)
                groups.append((ps, COLORS[layer], alpha))
        preview(groups, b, stage / "local-design.png")
        source_panels(
            root, parent["manifest"], request, stage, frames=tuple(request["source_windows"])
        )
        (stage / "index.html").write_text(review_page(svg, request, model, report))
        write_json(
            stage / "manifest.json",
            dict(
                request=ref,
                verified_inputs=inputs.files,
                code={
                    name: digest(Path(__file__).with_name(name))
                    for name in (
                        "metal_fanout.py",
                        "conductive_layers.py",
                        "metal_via_pilot.py",
                        "metal_reconstruction.py",
                        "review_package.py",
                    )
                },
                artifacts={p.name: digest(p) for p in stage.iterdir()},
            ),
        )
        stage.rename(output)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = deliver(args.root, args.request, args.output)
    print(json.dumps(result))
