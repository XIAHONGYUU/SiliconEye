"""Build a continuous local metal-stack candidate from source-bound observations.

Run: python -m silicon_eye.conductive_medium --request REQUEST --output NEW_DIRECTORY
Requires project dependencies. Reuses geometry/source renderers; does not detect cuts,
register photographs, adopt candidate geometry, or export an electrical netlist.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
from pathlib import Path

import numpy as np
from shapely.geometry import box

from .conductive_layers import LAYERS, geometry, source_identity_audit, svg_layers
from .geometry_reconstruction import digest
from .metal_reconstruction import geometry_audit
from .metal_via_pilot import interface_audit, source_panels
from .review_package import Inputs


def source_order_audit(features_by_layer, checks):
    """Check declared same-frame order without claiming a photograph transform."""
    features = {f["id"]: f for group in features_by_layer.values() for f in group}
    results = []
    for check in checks:
        axis = {"x": 0, "y": 1}[check["axis"]]
        operands = [features[check[key]["id"]] for key in ("first", "second")]
        if operands[0]["source_frame"] != operands[1]["source_frame"]:
            raise ValueError("Source order requires the same native frame")
        values = {}
        for space in ("native_path", "design_path"):
            values[space] = [
                {"min": min, "max": max}[check[key]["extreme"]](
                    point[axis] for point in feature[space]
                ) for key, feature in zip(("first", "second"), operands, strict=True)
            ]
        if values["native_path"][0] >= values["native_path"][1]:
            raise ValueError("Declared source order is not supported by native paths")
        results.append(dict(id=check["id"], values=values,
                            passed=values["design_path"][0] < values["design_path"][1]))
    return dict(status="PASS" if all(r["passed"] for r in results) else "FAIL",
                checks=results, scope="declared_same_frame_order_not_registration")


def prepare(root, request):
    """Keep reviewed interfaces, accepted structural groups and geometry separate."""
    root, inputs = Path(root), Inputs(root)
    if request["kind"] != "continuous_conductive_medium":
        raise ValueError("Expected continuous conductive medium")
    if (request.get("net_edges") or request.get("automatic_network_export_allowed")
            or request.get("source_to_design_transform") is not None):
        raise ValueError("Medium candidates cannot authorize projection or net export")
    snapshot = inputs.document(request["snapshot"])
    baseline = inputs.document(snapshot["conductive_layers"])
    policy = baseline["source_identity_policy"]
    if source_identity_audit(baseline, policy)["status"] != "PASS":
        raise ValueError("Invalid inherited via source identity")
    for ref in snapshot["source_photos"].values():
        inputs.read(ref)
    order_audit = None
    if request.get("source_order_checks"):
        order_audit = source_order_audit(request["features_by_layer"],
                                         request["source_order_checks"])
        if order_audit["status"] != "PASS":
            raise ValueError("Source relative order gate failed")
    inventory = {}
    for ref in request["interface_inventories"]:
        document = inputs.document(ref)
        for record in document["reviewed_local_connections"]:
            if record["id"] in inventory and record != inventory[record["id"]]:
                raise ValueError("Conflicting interface inventory")
            inputs.human(record["human_review"])
            inventory[record["id"]] = record

    objects = {layer: [] for layer in LAYERS}
    records, polygons, audits = {}, {}, {}
    for layer in ("M1", "M2", "M3"):
        features = request["features_by_layer"][layer]
        audits[layer], shapes = geometry_audit(
            features, request["metal_budget"], request["canvas_wh"]
        )
        if audits[layer]["status"] != "PASS":
            raise ValueError("Metal geometry gate failed: " + layer)
        for feature, shape in zip(features, shapes, strict=True):
            key = feature["id"]
            native = np.asarray(feature["native_path"], dtype=float)
            if (key in records or feature["source_frame"] != layer.lower()
                    or native.ndim != 2 or native.shape[1] != 2 or len(native) < 2
                    or not np.isfinite(native).all() or (native < 0).any()
                    or (native >= np.asarray(snapshot["source_wh"])).any()):
                raise ValueError("Invalid metal source or duplicate ID")
            records[key], polygons[key] = feature, shape
            objects[layer].append(dict(
                id=key, layer=layer, kind="metal", geometry=dict(
                    geometry(shape), status="AI_local_regular_candidate_not_registered"
                ),
                geometry_status="AI_local_regular_candidate_not_registered",
                source_frame=feature["source_frame"], native_path=feature["native_path"],
                role=feature.get("role", "context_only"),
                end_states=feature["end_states"], net_id=None,
            ))

    interfaces, seen, used_reviews = [], set(records), set()
    for claim in request["interfaces"]:
        edge = inventory[claim["reviewed_id"]]
        a, b, via = (edge[k] for k in ("lower_metal_id", "upper_metal_id", "via_layer"))
        pair = (records[a]["layer"], via, records[b]["layer"])
        if pair not in {("M1", "V1", "M2"), ("M2", "V2", "M3")}:
            raise ValueError("Wrong interface layer pair")
        if policy.get(claim["source_frame"]) != via:
            raise ValueError("Via source frame mismatch")
        cut = dict(id=claim["id"], layer=via, layer_pair=[pair[0], pair[2]],
                   observation_id=edge["id"], bounds=claim["support_bounds"])
        if cut["id"] in seen or edge["id"] in used_reviews:
            raise ValueError("Duplicate support or reviewed interface")
        seen.add(cut["id"])
        used_reviews.add(edge["id"])
        audit = interface_audit(
            [cut], polygons[a], polygons[b], request["via_budget"], layer_stack=pair
        )
        if audit["status"] != "PASS":
            raise ValueError("Via support enclosure gate failed")
        objects[via].append(dict(
            id=cut["id"], layer=via, kind="via_group_support_proxy",
            geometry=dict(geometry(box(*cut["bounds"])),
                          status="candidate_group_support_not_measured_cut"),
            role="reviewed_chain",
            geometry_status="candidate_group_support_not_measured_cut",
            physical_cut_count=None, source_frame=claim["source_frame"],
            source_photo=snapshot["source_photos"][claim["source_frame"]],
            human_review=edge["human_review"], net_id=None,
        ))
        interfaces.append(dict(
            id=edge["id"], lower_metal_id=a, upper_metal_id=b, via_layer=via,
            support_id=cut["id"], human_review=edge["human_review"],
            status="inherited_scoped_connection_geometry_candidate",
        ))
    for layer in ("V1", "V2"):
        supports = [box(*next(claim["support_bounds"] for claim in request["interfaces"]
                             if claim["id"] == obj["id"])) for obj in objects[layer]]
        for index, first in enumerate(supports):
            for second in supports[index + 1:]:
                if first.intersects(second) or first.distance(second) < request[
                    "via_budget"]["minimum_cut_gap_px"]:
                    raise ValueError("Via support overlap or gap failed")

    groups = inputs.document(request["structural_groups"])
    for group in groups["grouping_decisions"]:
        review = inputs.human(group["human_review"])
        if review.get("correction", {}).get("group_id") == group["group_id"]:
            accepted = review["correction"]
            members = accepted["current_M1_members"]
        else:
            accepted = next((item for item in review.get("decisions", [])
                             if item.get("group_id") == group["group_id"]), None)
            if accepted is None:
                raise ValueError("Structural group has no matching human decision")
            members = accepted["M1_members"]
        if (members != group["M1_members"] or not accepted["grouping_accepted"]
                or accepted["M2_anchor"] != group["M2_anchor"]
                or accepted["routing_layers_reported"] != group["routing_layers_reported"]):
            raise ValueError("Structural group contradicts human decision")
        if not group["grouping_accepted"]:
            raise ValueError("Unaccepted structural group")
        if any(key not in records for key in [*group["M1_members"], group["M2_anchor"]]):
            raise ValueError("Structural group member missing from geometry")
    # A source hypothesis may be displayed but cannot be converted into an interface.
    for hypothesis in request["path_hypotheses"]:
        if hypothesis["status"] != "candidate" or hypothesis.get("connection_confirmed"):
            raise ValueError("Unreviewed path cannot be promoted")
        if any(key not in records for key in hypothesis["metal_ids"]):
            raise ValueError("Hypothesis references unknown metal")

    negative = inputs.document(request["non_junctions"])
    for fact in negative["reviewed_non_junctions"]:
        inputs.human(fact["human_review"])
        a, b = fact["feature_id"], fact["other_metal_id"]
        if a in polygons and b in polygons and polygons[a].intersects(polygons[b]):
            raise ValueError("Human-reviewed local isolation violated")

    by_id = {edge["id"]: edge for edge in interfaces}
    route = request["branch"]["metal_route"]
    if len(route) < 3 or len(route) % 2 != 1 or any(key not in records for key in route[::2]):
        raise ValueError("Branch must alternate metal and reviewed interface")
    for a, edge_id, b in zip(route[::2], route[1::2], route[2::2], strict=False):
        if edge_id not in by_id:
            raise ValueError("Branch uses an unreviewed interface")
        edge = by_id[edge_id]
        if {a, b} != {edge["lower_metal_id"], edge["upper_metal_id"]}:
            raise ValueError("Branch continuity mismatch")
    terminal = request["branch"]["terminal_candidate"]
    if terminal["status"] != "candidate" or terminal.get("connection_confirmed"):
        raise ValueError("Terminal requires separate evidence before adoption")
    if terminal["from_metal_id"] != route[-1]:
        raise ValueError("Terminal does not continue the reviewed metal route")
    model = dict(
        schema_version=1, kind="continuous_local_conductive_candidate",
        coordinate_space="local_regular_design_px_not_photo_projection",
        canvas_wh=request["canvas_wh"], source_photos=snapshot["source_photos"],
        objects_by_layer=objects, reviewed_local_connections=interfaces,
        accepted_structural_groups=copy.deepcopy(groups["grouping_decisions"]),
        path_hypotheses=copy.deepcopy(request["path_hypotheses"]),
        branch=dict(metal_route=route, reviewed_metal_route_continuous=True,
                    terminal_candidate=terminal, terminal_closed=False),
        source_to_design_transform=None, common_canvas_placement=None,
        precise_projection_allowed=False, automatic_network_export_allowed=False,
        net_edges=[], complete_network=False,
    )
    report = dict(
        status="CANDIDATE_GEOMETRY_PASS_TERMINAL_REVIEW_REQUIRED",
        geometry_audits=audits, object_counts={k: len(v) for k, v in objects.items()},
        input_interface_union_count=len(inventory),
        interfaces_represented=len(interfaces),
        interface_inventory_coverage="selected_region_not_whole_net",
        baseline_geometry_adoption=False, new_physical_connections=0,
        structural_group_count=len(groups["grouping_decisions"]),
        support_boxes_are_cut_counts=False, terminal_closed=False,
        complete_network=False, verified_input_count=len(inputs.files),
    )
    if order_audit is not None:
        report["source_order_audit"] = order_audit
    if request.get("reviewed_terminal_state"):
        state = inputs.document(request["reviewed_terminal_state"])
        review = inputs.human(state["human_review"])
        decision = review["decisions"]
        approved = state["approved_terminal_connections"]
        if (len(approved) != 1 or not decision["connection_confirmed"]
                or not approved[0]["connection_confirmed"]
                or state["branch"]["metal_route"] != route
                or decision["from_metal_id"] != terminal["from_metal_id"]
                or decision["source_regions"] != terminal["source_regions"]
                or any(approved[0][key] != decision[key] for key in
                       ("id", "from_metal_id", "source_regions", "target_material",
                        "target_structure", "via_layer"))):
            raise ValueError("Terminal continuation contradicts scoped human decision")
        if (approved[0]["physical_cut_count"] is not None
                or approved[0]["body_terminal_assignment"] is not None
                or approved[0]["canonical_CT_object_ids"] is not None
                or approved[0]["canonical_AA_object_ids"] is not None
                or approved[0]["human_review"] != state["human_review"]
                or approved[0]["geometry_adopted"]):
            raise ValueError("Terminal continuation exceeds reviewed scope")
        model["branch"].update(terminal_closed=True,
                               reviewed_terminal_connection=copy.deepcopy(approved[0]),
                               all_along_route_interfaces_checked=False)
        report.update(status="CANDIDATE_GEOMETRY_PASS_SCOPED_TERMINAL_REVIEWED",
                      terminal_closed=True, verified_input_count=len(inputs.files))
    return model, report, snapshot, inputs.files


def review_page(model, report, request):
    content = request["review"]
    w, h = model["canvas_wh"]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">'
           + svg_layers(model, [0, 0, w, h]))
    for objects in model["objects_by_layer"].values():
        for obj in objects:
            if obj["role"] == "structural_hypothesis":
                marker = f'data-object="{html.escape(obj["id"])}"'
                svg = svg.replace(marker, marker + ' stroke-dasharray="12 7"')
    for layer in ("M1", "M2", "M3"):
        svg += f'<g data-layer="{layer}" fill="white" font-size="26">'
        for obj in request["features_by_layer"][layer]:
            x, y = obj["label_xy"]
            svg += (f'<text x="{x}" y="{y}" stroke="#101a27" stroke-width="5" '
                    f'paint-order="stroke">{html.escape(obj["label"])}</text>')
        svg += '</g>'
    svg += '</svg>'
    counts = '；'.join(f'{layer}：{count}处孔组支持' if layer.startswith('V')
                      else f'{layer}：{count}条导体'
                      for layer, count in report["object_counts"].items())
    buttons = ''.join(
        f'<label><input type="checkbox" data-toggle="{layer}" checked>{layer}</label>'
        for layer in LAYERS
    )
    source_buttons = ''.join(f'<button data-frame="{layer}">{layer.upper()}原图</button>'
                             for layer in ("m1", "m2", "m3", "poly", "aa"))
    sources = ''.join(
        f'<section data-frame-panel="{layer}" '+('' if layer == 'm1' else 'hidden')+'>'
        f'<h2>{layer.upper()}原生照片</h2><a href="{layer}-wide-raw.png">打开原尺寸</a>'
        f'<img src="{layer}-wide-raw.png" alt="{layer}连续上下文"></section>'
        for layer in ("m1", "m2", "m3", "poly", "aa")
    )
    page = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(content['title'])}</title><style>
body{{font:20px/1.65 system-ui;background:#101a27;color:#edf3fa;max-width:1700px;
margin:auto;padding:24px}}a{{color:#8bd4ff}}button,label{{font-size:20px;margin:8px}}
.note{{padding:18px;border-left:5px solid #6ad8ff;background:#233246}}
.drawing{{overflow:auto}}svg{{width:100%;min-width:1400px}}img{{width:100%}}
table{{border-collapse:collapse}}td,th{{border:1px solid #62768c;padding:10px}}
[hidden]{{display:none}}.controls{{position:sticky;top:0;background:#101a27;z-index:2}}
</style><h1>{html.escape(content['title'])}</h1>
<div class="note">规则几何是一个连续局部画布上的AI候选，不是原图精确投影，
也没有替换共同快照。实线金属为候选几何；方框是已审接口的设计支持区，
不是实测单孔。虚线边框表示结构路径候选，仍不构成新接口。</div>
<p>{html.escape(content['scope_summary'])}</p>
<h2>一、五层连续规则几何</h2><div class="controls">{buttons}</div>
<p>{counts}。只覆盖指定导体，其他可见导体仍属未建模上下文。</p>
<div class="drawing">{svg}</div>
<h2>二、主网支路的当前终点</h2>
<p><b>{html.escape(content['branch_summary'])}</b>：所列金属接口已审。
器件端子接入仍是候选，未宣布支路到器件端子完成。</p>
<div class="note">{html.escape(content['terminal_question'])}</div>
<p><a href="terminal/index.html">打开端子宽上下文复核</a> ·
<a href="closeout-report.md">四项收口报告与skill判断</a></p>
<h2>三、来源照片（与规则模型分开）</h2>{source_buttons}{sources}
<p><a href="model.json">候选模型</a> · <a href="report.json">几何／来源检查</a> ·
<a href="request.json">复跑输入</a></p>
<script>
document.querySelectorAll('[data-toggle]').forEach(e=>e.onchange=()=>{{
document.querySelectorAll('[data-layer="'+e.dataset.toggle+'"]').forEach(g=>
g.style.display=e.checked?'':'none')}});
document.querySelectorAll('[data-frame]').forEach(e=>e.onclick=()=>{{
document.querySelectorAll('[data-frame-panel]').forEach(p=>
p.hidden=p.dataset.framePanel!==e.dataset.frame)}});
</script></html>'''
    if model["branch"]["terminal_closed"]:
        page = page.replace("器件端子接入仍是候选，未宣布支路到器件端子完成。",
                            "U3经CT接AA环已获批准；只闭合该端子路径，其他分支未完成。")
        page = page.replace(html.escape(content['terminal_question']),
                            "U3端子已审，沿用原裁决，不重复审批；体端身份及孔数仍未知。")
    return page


def terminal_page(request, *, reviewed=False):
    """Show independently located source regions, never an unqualified projection."""
    content, spec = request["review"], request["terminal_source_panels"]
    panels = ''
    for frame in spec["source_windows"]:
        panels += f'<h2>{frame.upper()}宽上下文</h2>'
        for mode in ("wide", "detail"):
            panels += (f'<p><a href="{frame}-{mode}-raw.png">原图</a> · '
                       f'<a href="{frame}-{mode}-marked.png">大字标记</a></p>'
                       f'<img src="{frame}-{mode}-marked.png" '
                       f'alt="{frame} {mode} terminal context">')
    page = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>器件端子接入复核</title><style>body{{font:20px/1.6 system-ui;background:#101a27;
color:#edf3fa;max-width:1600px;margin:auto;padding:24px}}a{{color:#8bd4ff}}
img{{display:block;width:100%;margin-bottom:24px}}.note{{padding:18px;background:#233246}}
</style><h1>当前唯一新增端子问题</h1><div class="note">
{html.escape(content['terminal_question'])}</div><p>{html.escape(content['terminal_scope'])}</p>
<p>下列分别在各层原生照片定位；并未按相同像素坐标投影或宣称精确对齐。
标框是候选范围，不是单孔边界；可打开原图及完整放大图。</p>
<p><a href="../index.html">返回联合中样</a></p>{panels}</html>'''
    if reviewed:
        page = page.replace("当前唯一新增端子问题", "U3端子接入已审：不重复审批")
        page = page.replace(html.escape(content['terminal_question']),
                            "用户已确认U3宽M1经所圈CT行接入对应AA环。")
        page = page.replace(html.escape(content['terminal_scope']),
                            "复用原送审定位；接入已审，体端身份、孔数和精确投影未确认。")
    return page


def deliver(root, request_path, output):
    root, output = Path(root), Path(output)
    if output.exists():
        raise ValueError("Output must be a new directory")
    request = json.loads(Path(request_path).read_text())
    model, report, snapshot, files = prepare(root, request)
    # Fail all semantic checks before creating a deliverable directory.
    output.mkdir(parents=True)
    for name, value in (("model", model), ("report", report), ("request", request)):
        (output / (name + '.json')).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        )
    source_panels(root, snapshot, request["source_panels"], output,
                  frames=("m1", "m2", "m3", "poly", "aa"))
    # The overview links only raw wide views; retain detailed terminal views below.
    for frame in request["source_panels"]["source_windows"]:
        for suffix in ("wide-marked", "detail-raw", "detail-marked"):
            (output / f'{frame}-{suffix}.png').unlink()
    (output / 'index.html').write_text(review_page(model, report, request))
    terminal = output / 'terminal'
    terminal.mkdir()
    source_panels(root, snapshot, request["terminal_source_panels"], terminal,
                  frames=tuple(request["terminal_source_panels"]["source_windows"]))
    (terminal / 'index.html').write_text(terminal_page(
        request, reviewed=model["branch"]["terminal_closed"]
    ))
    (output / 'closeout-report.md').write_text(request["review"]["closeout_markdown"])
    manifest = dict(inputs=files, artifacts={str(p.relative_to(output)): digest(p)
                                          for p in output.rglob('*') if p.is_file()})
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return model, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    deliver(Path.cwd(), args.request, args.output)


if __name__ == '__main__':
    main()
