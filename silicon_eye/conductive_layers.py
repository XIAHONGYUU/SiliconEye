"""Adapt locked metal/via packages to one reloadable conductive-layer registry.

Run: python -m silicon_eye.conductive_layers --request REQUEST --output NEW_DIRECTORY
Requires project dependencies and scoped human-reviewed input packages. No extraction,
coordinate refitting, new physical connections, or automatic net export is performed.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
import tempfile
from pathlib import Path

from shapely.geometry import Point, Polygon, box

from .geometry_reconstruction import digest
from .review_package import Inputs

LAYERS = ("M1", "V1", "M2", "V2", "M3")
COLORS = {"M1": "#80e6b0", "V1": "#ffb04f", "M2": "#6ad8ff",
          "V2": "#fff4bd", "M3": "#d28cff"}


def geometry(polygon):
    return dict(outer_xy=list(map(list, polygon.exterior.coords)),
                holes_xy=[list(map(list, r.coords)) for r in polygon.interiors],
                status="inherited_relative_design_geometry_not_pixel_measurement")


def assemble(root, request, inputs=None):
    """Normalize existing records, rejecting identity, geometry and review drift."""
    from .metal_reconstruction import feature_polygon, geometry_audit
    from .metal_via_pilot import interface_audit, reviewed_interface

    inputs = inputs or Inputs(root)
    base = inputs.document(request["base_snapshot"])
    if "conductive_layers" in base or request["kind"] != "conductive_stack_assembly":
        raise ValueError("Assembly needs an unextended material snapshot")
    for ref in [*base["inputs"].values(), *base["source_photos"].values()]:
        inputs.read(ref)
    packages = {}
    for name, refs in request["packages"].items():
        package = {key: inputs.document(ref) for key, ref in refs.items()}
        directory = Path(refs["manifest"]["path"]).parent
        for key in ("spec", "model", "report"):
            if refs[key] != dict(path=str(directory / (key + '.json')),
                                 sha256=package["manifest"]["artifacts"][key + '.json']):
                raise ValueError("Package record is not bound to its output manifest")
        for file, sha in package["manifest"]["artifacts"].items():
            inputs.read(dict(path=str(Path(refs["manifest"]["path"]).parent / file), sha256=sha))
        if package["report"]["status"] != "SCOPED_REVIEWED_WITH_LIMITATIONS":
            raise ValueError("Assembly cannot promote an unreviewed package")
        packages[name] = package
    first, second = packages["lower"], packages["upper"]
    first_review = reviewed_interface(inputs, first["spec"])
    second_review = inputs.human(second["spec"]["adjudication"]["human_review"])
    upper_parent = inputs.document(second["spec"]["adjudication"]["parent_spec"])
    expected_spec = copy.deepcopy(upper_parent)
    expected_spec["adjudication"] = second["spec"]["adjudication"]
    expected_spec["human_questions"] = []
    if (second["spec"] != expected_spec or second["model"]["objects_by_layer"]
            != second["spec"]["features_by_layer"]):
        raise ValueError("Upper package changed frozen geometry during adjudication")
    parent_spec = inputs.document(first["spec"]["parent_M1_spec"])
    if parent_spec["snapshot"] != request["base_snapshot"]:
        raise ValueError("Metal companions belong to a different material snapshot")
    if second["model"]["parent_snapshot"] != request["base_snapshot"]:
        raise ValueError("Upper companion snapshot mismatch")
    if second["spec"]["baseline"]["model"] != request["packages"]["lower"]["model"]:
        raise ValueError("Upper pair must inherit this exact lower pair")
    if (first["model"]["M2_objects"] != second["model"]["objects_by_layer"]["M2"]
            or first["model"]["M2_objects"] != first["spec"]["M2_features"]):
        raise ValueError("Shared M2 identity or geometry mismatch")
    if (first_review is None or first["model"]["reviewed_local_connections"]
            != [first_review["local_connection"]]):
        raise ValueError("Missing lower reviewed connection")
    expected_upper = dict(**second_review["decisions"], status="human_confirmed_local_interface",
                          human_review=second["spec"]["adjudication"]["human_review"])
    if second["model"]["reviewed_local_connections"] != [expected_upper]:
        raise ValueError("Upper connection differs from the scoped human review")
    lower_connection = first_review["local_connection"]
    if (lower_connection["upper_metal_id"] != expected_upper["lower_metal_id"]
            or lower_connection["via_layer"] != "V1" or expected_upper["via_layer"] != "V2"
            or not expected_upper["connection_confirmed"]):
        raise ValueError("Reviewed interfaces do not form a continuous layer chain")
    if first["model"]["inherited_M1_objects"] != inputs.document(
            first["spec"]["parent_M1_model"])["objects"]:
        raise ValueError("Inherited M1 records changed")

    metal = {"M1": copy.deepcopy(first["model"]["inherited_M1_objects"]),
             "M2": copy.deepcopy(first["model"]["M2_objects"]),
             "M3": copy.deepcopy(second["model"]["objects_by_layer"]["M3"])}
    addition = first["model"]["proposed_M1_addition"]
    if addition != first["spec"]["candidate_M1_addition"]:
        raise ValueError("M1 continuation changed")
    if sum(o["id"] == addition["metal_id"] for o in metal["M1"]) != 1:
        raise ValueError("Missing unique M1 continuation target")
    for obj in metal["M1"]:
        if obj["id"] == addition["metal_id"]:
            obj.setdefault("local_parts", []).append(copy.deepcopy(addition["part"]))
    budgets = {"M1": parent_spec["budget"], "M2": first["spec"]["metal_budget"],
               "M3": second["spec"]["metal_budget"]}
    audits, polygons = {}, {}
    for layer, objects in metal.items():
        audits[layer], ps = geometry_audit(objects, budgets[layer], base["canvas_wh"])
        polygons[layer] = {o["id"]: p for o, p in zip(objects, ps, strict=True)}
    cuts = {"V1": first["model"]["V1_cuts"], "V2": second["model"]["V2_support_regions"]}
    if (cuts["V1"] != first["spec"]["cuts"]
            or cuts["V2"] != second["spec"]["interface_support_regions"]):
        raise ValueError("Inherited cut or support geometry changed")
    if set(lower_connection["via_group_ids"]) != {c["id"] for c in cuts["V1"]}:
        raise ValueError("Reviewed V1 members missing or reassigned")
    for c in cuts["V2"]:
        if c["via_group_id"] != expected_upper["via_group_id"]:
            raise ValueError("Reviewed V2 group reassigned")
    connections = []
    for layer, connection, package in (("V1", lower_connection, first),
                                        ("V2", expected_upper, second)):
        a, b = ("M1", "M2") if layer == "V1" else ("M2", "M3")
        for cut in cuts[layer]:
            if (cut["lower_metal_id"] != connection["lower_metal_id"]
                    or cut["upper_metal_id"] != connection["upper_metal_id"]):
                raise ValueError("Via bearing identity changed")
        audits[layer] = interface_audit(
            cuts[layer], polygons[a][connection["lower_metal_id"]],
            polygons[b][connection["upper_metal_id"]], package["spec"]["via_budget"],
            layer_stack=(a, layer, b),
        )
        # A support proxy is never counted as a measured cut.
        if layer == "V2":
            audits[layer]["support_region_count"] = audits[layer].pop("candidate_cut_count")
        review_ref = (first["spec"]["reviewed_interface"]["human_review"] if layer == "V1"
                      else second["spec"]["adjudication"]["human_review"])
        connections.append(dict(
            id=connection["id"], lower_metal_id=connection["lower_metal_id"],
            upper_metal_id=connection["upper_metal_id"], via_layer=layer,
            via_object_ids=[c["id"] for c in cuts[layer]],
            original_reviewed_record=connection, human_review=review_ref,
            status="human_confirmed_local_interface_not_complete_net",
        ))
    if any(r["status"] != "PASS" for r in audits.values()):
        raise ValueError("Inherited conductive geometry fails joint assembly checks")
    chain_ids = {c[k] for c in connections for k in ("lower_metal_id", "upper_metal_id")}
    objects = {layer: [] for layer in LAYERS}
    raw_m1 = {o["id"]: o for o in first["model"]["inherited_M1_objects"]}
    for layer, features in metal.items():
        key = "lower" if layer in {"M1", "M2"} else "upper"
        for obj in features:
            objects[layer].append(dict(
                id=obj["id"], layer=layer, kind="metal", geometry=geometry(feature_polygon(obj)),
                inherited_record=raw_m1[obj["id"]] if layer == "M1" else obj,
                input_package=request["packages"][key]["model"],
                inherited_local_addition=addition if obj["id"] == addition["metal_id"] else None,
                source_frame=obj.get("source_frame", layer.lower()),
                source_photo=base["source_photos"][layer.lower()],
                role="reviewed_chain" if obj["id"] in chain_ids else "context_only",
                geometry_status="candidate", net_id=None,
                end_states=obj["end_states"],
            ))
    for layer, features in cuts.items():
        key = "lower" if layer == "V1" else "upper"
        for cut in features:
            observation = (next(o for o in first["model"]["source_observations"]
                                if o["id"] == cut["observation_id"])
                           if layer == "V1" else second["model"]["inherited_native_V2"])
            if observation["id"] != cut["observation_id"]:
                raise ValueError("Via source observation mismatch")
            objects[layer].append(dict(
                id=cut["id"], layer=layer,
                kind="via_cut_candidate" if layer == "V1" else "via_group_support_proxy",
                geometry=geometry(box(*cut["bounds"])), inherited_record=copy.deepcopy(cut),
                input_package=request["packages"][key]["model"],
                source_frame="m1" if layer == "V1" else "m2",
                source_photo=base["source_photos"]["m1" if layer == "V1" else "m2"],
                observation_id=cut["observation_id"], role="reviewed_chain",
                source_observation=observation,
                geometry_status="candidate", physical_cut_count=None, net_id=None,
            ))
    all_ids = [o["id"] for layer in objects.values() for o in layer]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Duplicate global conductive object ID")
    model = dict(
        schema_version=1, kind="conductive_layer_registry", assembly_request=request,
        coordinate_space="shared_design_px", canvas_wh=base["canvas_wh"],
        source_photos=base["source_photos"], layer_stack=list(LAYERS), objects_by_layer=objects,
        reviewed_local_connections=connections,
        continuous_chain=dict(
            conductor_ids=[connections[0]["lower_metal_id"], connections[0]["upper_metal_id"],
                           connections[1]["upper_metal_id"]],
            interface_ids=[c["id"] for c in connections],
            via_layers=["V1", "V2"], status="assembled_from_existing_scoped_human_reviews",
            new_physical_connections=0, complete_network=False,
        ),
        geometry_audits=audits, source_to_design_transform=None,
        precise_projection_allowed=False, automatic_network_export_allowed=False, net_edges=[],
        unprocessed_is_unknown=True, physical_cut_count=None,
    )
    if request.get("reviewed_source_correction"):
        return correct_source_identity(root, model, request, inputs)
    return model


def source_identity_audit(model, policy):
    """A typed source observation cannot borrow another via layer's bright spots."""
    errors = []
    for layer in ("V1", "V2"):
        for obj in model["objects_by_layer"][layer]:
            frame = obj["source_frame"]
            observation = obj["source_observation"]
            if (policy.get(frame) != layer or observation.get("source_frame") != frame
                    or observation.get("layer") != layer
                    or obj["source_photo"] != model["source_photos"].get(frame)):
                errors.append(dict(id=obj["id"], reason="source_frame_via_identity_mismatch"))
            for other_frame, other_layer in policy.items():
                if other_layer != layer and other_frame + "_xy" in observation:
                    errors.append(dict(id=obj["id"], reason="rejected_cross_via_correspondence"))
    return dict(status="FAIL" if errors else "PASS", errors=errors,
                scope="human_adjudicated_photograph_stack_not_universal_imaging_rule")


def correct_source_identity(root, model, request, inputs):
    """Apply a scoped human correction without rewriting historical evidence."""
    from .metal_via_pilot import interface_audit

    binding = request["reviewed_source_correction"]
    parent = inputs.document(binding["parent_request"])
    old = inputs.document(binding["parent_registry"])
    review = inputs.human(binding["human_review"])
    revision = inputs.document(binding["revision"])
    expected = copy.deepcopy(parent)
    expected["reviewed_source_correction"] = binding
    expected["source_regions"]["m2"] = revision["M2_source_regions"]
    expected["limits"] = revision["active_limits"]
    if request != expected:
        raise ValueError("Source correction cannot move metals or revise unrelated evidence")
    before = copy.deepcopy(model)
    before["assembly_request"] = parent
    if before != old:
        raise ValueError("Source correction must continue the exact previous registry")
    if review["decisions"] != dict(
        evidence_frame="m2", visible_via_layer="V2", V1_visible_here=False,
        array_rows=3, array_columns=4, local_group_cut_count=12,
    ):
        raise ValueError("M2 array identity or 3x4 human count contradicted")
    if (review["sources"]["parent_registry"] != binding["parent_registry"]
            or review["sources"]["parent_request"] != binding["parent_request"]):
        raise ValueError("Human correction is not bound to this parent")
    policy = revision["source_identity_policy"]
    if policy != {"m1": "V1", "m2": "V2"}:
        raise ValueError("Correction policy applies only to the adjudicated photographs")
    if (len(revision["M2_source_regions"]) != 1
            or revision["M2_source_regions"][0]["feature_layer"] != "V2"
            or "V1" in revision["M2_source_regions"][0]["label"]):
        raise ValueError("M2 review must show the V2 group without a V1 region")
    for obj in model["objects_by_layer"]["V1"]:
        prior = obj["source_observation"]
        obj["source_observation"] = dict(
            id=prior["id"], source_frame="m1", layer="V1", m1_xy=prior["m1_xy"],
            status="M1_evidence_retained_M2_correspondence_rejected",
            m2_correspondence_status="REJECTED_DIFFERENT_VIA_LAYER",
        )
    array = revision["V2_array"]
    if (array["rows"], array["columns"], array["count"]) != (3, 4, 12):
        raise ValueError("V2 local count must remain the human-confirmed 3x4")
    native_x, native_y = array["native_x"], array["native_y"]
    design_x, design_y = array["design_x"], array["design_y"]
    if len(native_x) != 4 or len(design_x) != 4 or len(native_y) != 3 or len(design_y) != 3:
        raise ValueError("V2 array has missing rows or columns")
    import numpy as np

    coordinates = np.asarray(native_x + native_y + design_x + design_y, dtype=float)
    if not np.isfinite(coordinates).all() or any(
        not all(b > a for a, b in zip(values, values[1:], strict=False))
        for values in (native_x, native_y, design_x, design_y)
    ):
        raise ValueError("Invalid or unordered array coordinates")
    if array["source_bounds"] != revision["M2_source_regions"][0]["bounds"]:
        raise ValueError("Visible V2 group window mismatch")
    support = model["objects_by_layer"]["V2"]
    if len(support) != 1 or support[0]["id"] != "V2-J-EDGE-SUPPORT":
        raise ValueError("Only the original single group-support proxy may be superseded")
    connection = model["reviewed_local_connections"][1]
    if connection["upper_metal_id"] != "M3-J-B1" or connection["lower_metal_id"] != "M2-J01":
        raise ValueError("Count correction cannot change the reviewed B1 carrier")
    cuts, objects = [], []
    size = revision["via_budget"]["cut_size_px"]
    for row, (sy, dy) in enumerate(zip(native_y, design_y, strict=True), 1):
        for column, (sx, dx) in enumerate(zip(native_x, design_x, strict=True), 1):
            if not box(*array["source_bounds"]).covers(Point(sx, sy)):
                raise ValueError("Native V2 center outside its observed group")
            key = f"V2-J-R{row:02}-C{column:02}"
            observation = dict(id=key + "-source", source_frame="m2", layer="V2",
                               native_center=[sx, sy], status="AI_center_not_measured_boundary")
            cut = dict(id=key, layer="V2", layer_pair=["M2", "M3"],
                       observation_id=observation["id"], via_group_id="J-M2-EDGE-V2",
                       lower_metal_id="M2-J01", upper_metal_id="M3-J-B1",
                       bounds=[dx-size/2, dy-size/2, dx+size/2, dy+size/2],
                       electrical_connection_confirmed=False, status="geometry_candidate")
            cuts.append(cut)
            objects.append(dict(
                id=key, layer="V2", kind="via_cut_candidate",
                geometry=geometry(box(*cut["bounds"])),
                inherited_record=cut, input_package=binding["revision"],
                source_frame="m2", source_photo=model["source_photos"]["m2"],
                observation_id=observation["id"], source_observation=observation,
                role="reviewed_chain", geometry_status="candidate", physical_cut_count=1,
                physical_group_id="J-M2-EDGE-V2", human_identity_review=binding["human_review"],
                net_id=None,
            ))
    metal = {o["id"]: Polygon(o["geometry"]["outer_xy"], o["geometry"]["holes_xy"])
             for layer in ("M2", "M3") for o in model["objects_by_layer"][layer]}
    audit = interface_audit(cuts, metal["M2-J01"], metal["M3-J-B1"],
                            revision["via_budget"], layer_stack=("M2", "V2", "M3"))
    if audit["status"] != "PASS":
        raise ValueError("Corrected V2 array violates spacing or named metal enclosure")
    audit.update(human_confirmed_local_group_cut_count=12, scope="this_array_not_full_frame")
    model["objects_by_layer"]["V2"] = objects
    model["geometry_audits"]["V2"] = audit
    connection["via_object_ids"] = [c["id"] for c in cuts]
    connection["source_correction_review"] = binding["human_review"]
    model["retired_object_ids"] = ["V2-J-EDGE-SUPPORT"]
    model["confirmed_local_via_groups"] = [dict(
        id="J-M2-EDGE-V2", layer="V2", source_frame="m2", rows=3, columns=4, cut_count=12,
        member_ids=[c["id"] for c in cuts], human_review=binding["human_review"],
        former_scope="left_column_only", current_scope="complete_local_3x4_array",
        precise_boundaries_measured=False,
    )]
    model["evidence_correction"] = dict(
        human_review=binding["human_review"], retired_support="V2-J-EDGE-SUPPORT",
        human_statement=review["statement"],
        invalidated_correspondence_ids=[o["source_observation"]["id"]
                                       for o in model["objects_by_layer"]["V1"]],
        prior_M1_M2_array_fit_status="REJECTED_DIFFERENT_VIA_LAYER",
        prior_4_52px_holdout_is_valid_registration_evidence=False,
        new_physical_connections=0,
    )
    model["source_identity_policy"] = policy
    model["source_identity_gate"] = source_identity_audit(model, policy)
    if model["source_identity_gate"]["status"] != "PASS":
        raise ValueError("Via observation identity gate failed")
    return model


def load_registry(root, ref, manifest):
    """Reload through the common snapshot, verifying the adapter output against parents."""
    inputs = Inputs(root)
    model = inputs.document(ref)
    expected = assemble(root, model["assembly_request"], inputs)
    if model != expected:
        raise ValueError("Conductive registry drifted from frozen sources or reviewed interfaces")
    if (model["canvas_wh"] != manifest["canvas_wh"]
            or model["source_photos"] != manifest["source_photos"]):
        raise ValueError("Conductive registry uses different coordinates or photographs")
    return model


def svg_layers(model, bounds):
    viewport = box(*bounds)
    parts = []
    for layer in ("M1", "M2", "M3", "V1", "V2"):
        parts.append(f'<g data-layer="{layer}" fill="{COLORS[layer]}" stroke="{COLORS[layer]}">')
        for o in model["objects_by_layer"][layer]:
            p = Polygon(o["geometry"]["outer_xy"], o["geometry"]["holes_xy"])
            if not viewport.intersects(p):
                continue
            path = " ".join("M" + " L".join(f"{x},{y}" for x, y in ring.coords) + " Z"
                            for ring in [p.exterior, *p.interiors])
            context = ' data-context="true"' if o["role"] == "context_only" else ""
            opacity = ".18" if context else (".48" if o["kind"] == "metal" else "1")
            parts.append(f'<path data-object="{html.escape(o["id"])}"{context} d="{path}" '
                         f'fill-rule="evenodd" fill-opacity="{opacity}" stroke-width="1">'
                         f'<title>{html.escape(o["id"])} | {o["kind"]}</title></path>')
        parts.append('</g>')
    return ''.join(parts)


def audit_summary(model):
    """Summarize a verified registry without adding physical approval or net edges."""
    result = dict(
        geometry_status="PASS", layer_stack=model["layer_stack"],
        object_counts={k: len(v) for k, v in model["objects_by_layer"].items()},
        reviewed_interface_count=len(model["reviewed_local_connections"]),
        continuous_chain=model["continuous_chain"],
        precise_projection_allowed=False, automatic_network_export_allowed=False,
    )
    if model.get("evidence_correction"):
        result.update(
            source_identity_gate=model["source_identity_gate"],
            prior_array_fit_status=model["evidence_correction"]["prior_M1_M2_array_fit_status"],
            confirmed_local_via_groups=model["confirmed_local_via_groups"],
        )
    return result


def deliver(root, request_path, output):
    """Emit a common-snapshot adapter and a five-layer review without new inference."""
    from .joint_layers import load_snapshot
    from .layer_review import model_svg, write_json
    from .metal_via_pilot import preview, source_panels

    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or not output.is_relative_to(root):
        raise ValueError("Output must be new and inside project")
    inputs = Inputs(root)
    request_ref = dict(path=str(Path(request_path).resolve().relative_to(root)),
                       sha256=digest(request_path))
    request = inputs.document(request_ref)
    model = assemble(root, request, inputs)
    snapshot = load_snapshot(root, root / request["base_snapshot"]["path"])
    objects = model["objects_by_layer"]
    report = dict(
        status="SCOPED_REVIEWED_CHAIN_ASSEMBLED", geometry_status="PASS",
        object_counts={layer: len(v) for layer, v in objects.items()},
        reviewed_interface_count=len(model["reviewed_local_connections"]),
        new_physical_connections=0, chain=model["continuous_chain"],
        geometry_audits=model["geometry_audits"],
        retained_unknown_scopes=snapshot["values"]["unknown"],
        unprocessed_is_unknown=True, automatic_network_export_allowed=False,
        precise_projection_allowed=False, physical_PDK_DRC=False, physical_cut_count=None,
        source_correspondence_status="NOT_QUALIFIED", human_questions=[],
        requires_user_action_now=False,
    )
    if model.get("evidence_correction"):
        report.update(
            status="SCOPED_REVIEWED_CHAIN_SOURCE_CORRECTED",
            evidence_correction=model["evidence_correction"],
            confirmed_local_via_groups=model["confirmed_local_via_groups"],
            source_identity_gate=model["source_identity_gate"],
            source_correspondence_status="PRIOR_ARRAY_FIT_REJECTED_DIFFERENT_VIA_LAYER",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".conductive-stack-", dir=output.parent) as tmp:
        stage = Path(tmp) / 'delivery'
        stage.mkdir()
        write_json(stage / 'model.json', model)
        write_json(stage / 'report.json', report)
        write_json(stage / 'request.json', request)
        combined = copy.deepcopy(snapshot["manifest"])
        combined["id"] += (':conductive-stack-v2-source-corrected'
                           if model.get("evidence_correction") else ':conductive-stack-v1')
        combined["conductive_layers"] = dict(path=str((output/'model.json').relative_to(root)),
                                            sha256=digest(stage/'model.json'))
        write_json(stage/'joint-snapshot.json', combined)
        display = dict(snapshot, conductors=model)
        svg = model_svg(display, request["design_bounds"])
        (stage/'joint-design.svg').write_text(svg)
        groups = []
        for layer in ("M1", "M2", "M3", "V1", "V2"):
            ps = [(o["id"], Polygon(o["geometry"]["outer_xy"], o["geometry"]["holes_xy"]))
                  for o in objects[layer] if o["role"] == "reviewed_chain"]
            groups.append((ps, COLORS[layer], 110 if layer in {"M1", "M2", "M3"} else 255))
        preview(groups, request["design_bounds"], stage/'chain-design.png')
        source_panels(root, snapshot["manifest"], request, stage, frames=('m1', 'm2', 'm3'))
        (stage/'index.html').write_text(review_page(svg, model, request))
        write_json(stage/'manifest.json', dict(
            verified_inputs=inputs.files, request=request_ref, status=report["status"],
            template_sha256=digest(Path(__file__).with_name('metal_via_pilot.html')),
            code={name: digest(Path(__file__).with_name(name)) for name in (
                'conductive_layers.py', 'joint_layers.py', 'layer_review.py',
                'metal_via_pilot.py', 'metal_reconstruction.py', 'review_package.py')},
            artifacts={p.name: digest(p) for p in stage.iterdir()},
        ))
        stage.rename(output)
    return report


def review_page(svg, model, request):
    template = Path(__file__).with_name('metal_via_pilot.html').read_text()
    style = template[template.index('<style>'):template.index('</style>')+8]
    script = template[template.index('<script>'):template.index('</script>')+9]
    page = '<!doctype html><html lang="zh"><meta charset="utf-8">'
    page += '<meta name="viewport" content="width=device-width,initial-scale=1">'
    page += '<title>五层连续联合中样</title>' + style
    page += '<h1>M1／V1／M2／V2／M3 连续联合中样</h1>'
    page += '<div class="card"><h2>两处已审接口，接成一条局部链</h2><p>'
    page += 'M1-P08 → V1孔组 → M2-J01 → J-M2-EDGE-V2 → M3-J-B1</p>'
    page += '<p>连接沿用J1／J2及K1人工裁决，没有新增接入判断，也不重复要求批准。'
    page += '其余M1、M3以淡色作为隔离上下文，不因投影交叠并入这条链。</p></div>'
    page += '<p class="notice">这是已审局部链，不是整网点亮。边界仍为候选；V2米白小方块'
    page += '是孔组最小支持区，不代表仅有一个孔。独立精确投影尚未核准，原图分开显示。'
    page += 'AA／POLY／CT及既有未知保持，M2／M3出窗延伸未知。</p>'
    page += '<div class="legend">'
    for layer in (*LAYERS, 'AA', 'POLY', 'CT', 'unknown'):
        checked = 'checked' if layer in LAYERS else ''
        page += f'<label><input type="checkbox" {checked} data-toggle="{layer}">{layer}</label>'
    page += '<label><input id="context" type="checkbox" checked>淡色上下文</label></div>'
    page += svg + '<p>绿色M1；橙色V1；蓝色M2；米白V2支持区；紫色M3。'
    page += '点击下方编号可突出对应对象；所有层使用同一设计坐标，照片保留原生坐标。</p>'
    page += '<p>原图橙框为已审V1孔组，米白框为已审V2组，红框为原已审无V1部位；'
    page += '标框是观察范围，不是孔的精确边界。</p>'
    page += '<details><summary>全部对象编号、来源与角色</summary><table><tr>'
    page += '<th>编号</th><th>图层</th><th>角色</th><th>原记录</th></tr>'
    for layer in LAYERS:
        for o in model['objects_by_layer'][layer]:
            role = '已审链上的候选几何' if o['role'] == 'reviewed_chain' else '隔离上下文'
            page += f'<tr><td><button data-select="{html.escape(o["id"])}">'
            page += html.escape(o['id']) + f'</button></td><td>{layer}</td><td>{role}</td>'
            page += '<td>' + html.escape(o['input_package']['path']) + '</td></tr>'
    page += '</table></details><h2>三层原图：宽上下文及4倍局部</h2>'
    page += '<button id="raw">原图</button><button id="marked">原观察标记</button>'
    page += '<div class="grid">'
    for mode in ('wide', 'detail'):
        for frame in ('m1', 'm2', 'm3'):
            key = frame + '-' + mode
            bounds = request['source_windows'][frame][mode]
            page += f'<div><h2>{frame.upper()} {mode} · {bounds}</h2><a data-image="{key}" '
            page += f'href="{key}-marked.png"><img data-source="{key}" '
            page += f'src="{key}-marked.png"></a></div>'
    page += '</div><p><a href="model.json">统一五层数据</a> · '
    page += '<a href="joint-snapshot.json">可接续共同快照</a> · '
    page += '<a href="report.json">联合质量门与未知</a> · '
    page += '<a href="manifest.json">来源与哈希</a></p>'
    extra = '''<script>
document.getElementById('context').onchange=e=>document.querySelectorAll('[data-context]')
.forEach(p=>p.style.display=e.target.checked?'':'none');
document.querySelectorAll('[data-select]').forEach(b=>b.onclick=()=>{
document.querySelectorAll('[data-object]').forEach(p=>{
const active=p.dataset.object===b.dataset.select;
p.style.strokeWidth=active?'4':'';p.style.stroke=active?'#ff64bc':'';});});
</script>'''
    if model.get("evidence_correction"):
        correction = model["evidence_correction"]
        card = '<div class="card"><h2>纠错：M2上的孔是3行×4列V2，共12个</h2><p>'
        card += html.escape(correction["human_statement"]) + '</p><p>撤销M2上的V1标记；'
        card += '旧9对M1/V1与M2/V2孔点不是同一孔的跨照片对应，原拟合及4.52像素留出'
        card += '不能作为配准证据。M1上的V1及原已审局部连接保留。</p></div>'
        marker = '<div class="card"><h2>两处已审接口'
        page = page.replace(marker, card + marker)
        page = page.replace('V2米白小方块是孔组最小支持区，不代表仅有一个孔。',
                            '米白色为本处已确认的3×4共12个V2，孔边界和尺寸仍为候选。')
        page = page.replace('原图橙框为已审V1孔组，米白框为已审V2组',
                            'M1原图橙框为V1组；M2原图整组米白框为V2（3×4）')
        page = page.replace('米白V2支持区', '米白V2阵列（12孔）')
        buttons = '<button data-isolate="V1">只看 M1／V1／M2</button>'
        buttons += '<button data-isolate="V2">只看 M2／V2／M3</button>'
        page = page.replace('<div class="legend">', buttons + '<div class="legend">')
        extra += '''<script>
document.querySelectorAll('[data-isolate]').forEach(b=>b.onclick=()=>{
const layers=b.dataset.isolate==='V1'?['M1','V1','M2']:['M2','V2','M3'];
document.querySelectorAll('[data-toggle]').forEach(e=>{
e.checked=layers.includes(e.dataset.toggle);e.onchange();});});
</script>'''
    return page + script + extra + '</html>'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--request', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = deliver(args.root, args.request, args.output)
    print(json.dumps(dict(status=result['status'], counts=result['object_counts'])))
