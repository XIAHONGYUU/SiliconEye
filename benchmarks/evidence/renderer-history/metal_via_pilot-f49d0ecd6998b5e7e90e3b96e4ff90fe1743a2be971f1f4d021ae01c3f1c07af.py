"""Review evidence-bound metal/via pilots without adopting electrical edges.

Run: python -m silicon_eye.metal_via_pilot --spec SPEC --output NEW_DIRECTORY
Requires the project dependencies and a locked, reviewed M1 companion.
AI supplies observations; geometry and evidence checks remain deterministic.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import MultiPoint, Polygon, box

from .geometry_reconstruction import digest
from .joint_layers import load_snapshot
from .layer_review import model_svg, write_json
from .metal_reconstruction import feature_polygon, geometry_audit, reviewed_features
from .review_package import Inputs, pointer


def reviewed_interface(inputs, spec):
    """Bind scoped interface decisions without changing accepted input geometry."""
    revision = spec.get("reviewed_interface")
    if not revision:
        return None
    parent = inputs.document(revision["parent_spec"])
    review = inputs.human(revision["human_review"])
    expected = copy.deepcopy(parent)
    expected["reviewed_interface"] = revision
    expected["human_questions"] = []
    expected["unknown_edge_column"] = review["resolved_edge_column"]
    expected["limits"] = review["active_limits"]
    if spec != expected:
        raise ValueError("Interface adjudication cannot change baseline geometry or context")
    decisions = review["decisions"]
    if decisions != dict(
        via_layer="V1", local_connection_confirmed=True,
        M1_box_V1_present=False, M2_box_via_layer="V2", M1_right_edge_V1_present=False,
    ):
        raise ValueError("Reviewed V1/V2 identity or exclusion was contradicted")
    edge = spec["unknown_edge_column"]
    for field in ("id", "m1_bounds", "m2_bounds"):
        if edge[field] != parent["unknown_edge_column"][field]:
            raise ValueError("Reviewed source exclusion window was moved")
    if edge["status"] != "human_adjudicated" or edge["cut_count"] is not None:
        raise ValueError("Human interface review is not an exact cut count")
    if edge["M1_box_V1_present"] is not False or edge["M2_box_via_layer"] != "V2":
        raise ValueError("Resolved edge must separate M1 no-V1 from M2 V2")
    width = review["width_and_edge_constraints"]
    if width["M1_right_edge_V1_present"] is not False or width["new_cut_creation_authorized"]:
        raise ValueError("Width agreement cannot authorize extra V1 cuts")
    connection = review["local_connection"]
    if (connection["lower_metal_id"] != spec["candidate_M1_addition"]["metal_id"]
            or connection["upper_metal_id"] != spec["M2_features"][0]["id"]
            or connection["via_layer"] != "V1"
            or set(connection["via_group_ids"]) != {c["id"] for c in spec["cuts"]}):
        raise ValueError("Reviewed interface identity mismatch")
    for o in spec["observations"]:
        for frame in ("m1", "m2"):
            if box(*edge[frame + "_bounds"]).covers(MultiPoint([o[frame + "_xy"]])):
                raise ValueError("No-V1 or V2-only observation cannot enter the V1 correspondence")
    return review


def local_correspondence(observations, fit_ids, tolerance):
    """Same-array holdouts cannot certify an independent-structure alignment."""
    for observation in observations:
        identities = observation.get("via_layer_by_frame")
        if identities and identities["m1"] != identities["m2"]:
            raise ValueError("Different via layers cannot form a same-hole correspondence")
    by_id = {o["id"]: o for o in observations}
    if len(by_id) != len(observations) or len(set(fit_ids)) != 3:
        raise ValueError("Need unique observations and three distinct affine fit points")
    fit = [by_id[k] for k in fit_ids]
    hold = [o for o in observations if o["id"] not in fit_ids]
    src = np.array([o["m1_xy"] for o in fit], dtype=np.float32)
    dst = np.array([o["m2_xy"] for o in fit], dtype=np.float32)
    if not np.isfinite(src).all() or not np.isfinite(dst).all():
        raise ValueError("Nonfinite source correspondence")
    if MultiPoint(src).convex_hull.area < 1 or MultiPoint(dst).convex_hull.area < 1:
        raise ValueError("Collinear or degenerate correspondence")
    if not hold or not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("Missing holdout or invalid tolerance")
    matrix = cv2.getAffineTransform(src, dst)
    if np.linalg.det(matrix[:, :2]) <= 0:
        raise ValueError("Reversed correspondence orientation")
    rows = []
    for o in hold:
        xy = np.asarray([*o["m1_xy"], 1.0])
        actual = np.asarray(o["m2_xy"], dtype=float)
        if not np.isfinite(xy).all() or not np.isfinite(actual).all():
            raise ValueError("Nonfinite holdout")
        predicted = matrix @ xy
        rows.append(dict(id=o["id"], error_px=float(np.linalg.norm(predicted - actual))))
    maximum = max(r["error_px"] for r in rows)
    return dict(
        direction="m1_native_to_m2_native",
        matrix=[*matrix.tolist(), [0, 0, 1]],
        fit_ids=fit_ids,
        holdout=rows,
        same_array_holdout_status="PASS" if maximum <= tolerance else "FAIL",
        maximum_holdout_error_px=maximum,
        tolerance_native_px=tolerance,
        independent_structure_status="NOT_QUALIFIED",
        precise_projection_allowed=False,
        extrapolation_allowed=False,
        electrical_connection_confirmed=False,
        scope="Observed array only; fit and holdouts share one physical structure",
    )


def interface_audit(cuts, lower, upper, budget, layer_stack=("M1", "V1", "M2")):
    """Enclosure is necessary, never sufficient to prove a physical via."""
    if tuple(layer_stack) not in {("M1", "V1", "M2"), ("M2", "V2", "M3")}:
        raise ValueError("Unsupported metal/via stack")
    lower_layer, via_layer, upper_layer = layer_stack
    if not cuts:
        raise ValueError("Missing observed vias; metal overlap alone cannot create an interface")
    numeric = np.asarray([budget[k] for k in (
        "minimum_cut_width_px", "minimum_cut_gap_px", "enclosure_px", "cut_size_px"
    )] + budget["pitch_xy"], dtype=float)
    if not np.isfinite(numeric).all() or (numeric <= 0).any():
        raise ValueError("Invalid relative via budget")
    errors, polygons, centers = [], [], []
    seen = set()
    for cut in cuts:
        if cut["id"] in seen:
            raise ValueError("Duplicate via ID")
        seen.add(cut["id"])
        if cut["layer_pair"] != [lower_layer, upper_layer] or cut["layer"] != via_layer:
            raise ValueError("Wrong via layer pair")
        if not cut.get("observation_id"):
            raise ValueError("Via requires source evidence; overlap alone is not a via")
        bounds = np.asarray(cut["bounds"], dtype=float)
        if bounds.shape != (4,) or not np.isfinite(bounds).all():
            raise ValueError("Invalid via rectangle")
        w, h = bounds[2:] - bounds[:2]
        if min(w, h) <= 0:
            raise ValueError("Collapsed via")
        p = box(*bounds)
        polygons.append(p)
        centers.append([(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2])
        if min(w, h) < budget["minimum_cut_width_px"] or abs(w - h) > 1e-6:
            errors.append(dict(id=cut["id"], reason="non_square_or_small_cut"))
        if abs(w - budget["cut_size_px"]) > 1e-6:
            errors.append(dict(id=cut["id"], reason="inconsistent_array_cut_size"))
        bearing = p.buffer(budget["enclosure_px"], join_style="mitre")
        if not lower.covers(bearing) or not upper.covers(bearing):
            errors.append(dict(id=cut["id"], reason="missing_lower_or_upper_enclosure"))
    for i, a in enumerate(polygons):
        for j, b in enumerate(polygons[i + 1 :], i + 1):
            if a.intersects(b) or a.distance(b) < budget["minimum_cut_gap_px"]:
                errors.append(dict(ids=[cuts[i]["id"], cuts[j]["id"]], reason="cut_gap_failed"))
    centers = np.asarray(centers)
    lattice = (centers - centers.min(axis=0)) / np.asarray(budget["pitch_xy"])
    if not np.allclose(lattice, np.round(lattice), atol=1e-6):
        errors.append(dict(reason="irregular_array_pitch"))
    return dict(
        status="FAIL" if errors else "PASS",
        errors=errors,
        candidate_cut_count=len(cuts),
        count_complete=False,
        electrical_connection_confirmed=False,
        unit="relative_design_px_not_PDK",
    )


def source_panels(root, manifest, spec, output, frames=("m1", "m2")):
    for frame in frames:
        with Image.open(root / manifest["source_photos"][frame]["path"]) as photo:
            for mode in ("wide", "detail"):
                b = spec["source_windows"][frame][mode]
                if not (0 <= b[0] < b[2] <= photo.width and 0 <= b[1] < b[3] <= photo.height):
                    raise ValueError("Source review window outside photo")
                raw = photo.crop(b).convert("RGB")
                marked = raw.copy()
                d = ImageDraw.Draw(marked)
                style = spec.get("source_label_style")

                def label(xy, text, color, target=None, *, style=style, d=d, marked=marked):
                    if not style:
                        d.text(xy, text, fill=color)
                        return
                    font = ImageFont.load_default(size=style.get("font_size_px", 28))
                    padding = style.get("padding_px", 5)
                    bounds = font.getbbox(text)
                    w = bounds[2] - bounds[0] + padding * 2
                    h = bounds[3] - bounds[1] + padding * 2
                    x = max(0, min(xy[0], marked.width - w))
                    y = max(0, min(xy[1], marked.height - h))
                    if target is not None:
                        d.line((x + w / 2, y + h / 2, *target), fill=color, width=2)
                    d.rectangle((x, y, x + w, y + h), fill="#101a27", outline=color, width=2)
                    d.text((x + padding - bounds[0], y + padding - bounds[1]), text,
                           fill=color, font=font)

                for region in spec.get("source_regions", {}).get(frame, []):
                    a, t, r, z = region["bounds"]
                    if not (0 <= a < r <= photo.width and 0 <= t < z <= photo.height):
                        raise ValueError("Source region outside photo")
                    d.rectangle((a-b[0], t-b[1], r-b[0], z-b[1]),
                                outline=region["color"], width=2)
                    lx, ly = region.get("label_xy", (a, t-14))
                    if not style or (r >= b[0] and a <= b[2] and z >= b[1] and t <= b[3]):
                        label((lx-b[0], ly-b[1]), region["label"], region["color"],
                              ((a+r)/2-b[0], (t+z)/2-b[1]) if style else None)
                for trace in spec.get("native_traces", {}).get(frame, []):
                    xy = [(x - b[0], y - b[1]) for x, y in trace["points"]]
                    d.line(xy, fill=trace["color"], width=2)
                    if style:
                        lx, ly = trace.get("label_xy", trace["points"][0])
                        label((lx-b[0], ly-b[1]), trace["label"], trace["color"], xy[0])
                    else:
                        d.text(xy[0], trace["label"], fill=trace["color"])
                for o in spec["observations"]:
                    x, y = o[frame + "_xy"]
                    if not box(*b).covers(MultiPoint([(x, y)])):
                        raise ValueError("Source window omits observed via")
                    x, y = x - b[0], y - b[1]
                    d.ellipse((x - 5, y - 5, x + 5, y + 5), outline="#ffb04f", width=1)
                if spec.get("unknown_edge_column"):
                    u = spec["unknown_edge_column"][frame + "_bounds"]
                    resolved = bool(spec.get("reviewed_interface"))
                    color = ("#ff7086" if frame == "m1" else "#58edab") if resolved else "#ffe36b"
                    d.rectangle((u[0] - b[0], u[1] - b[1], u[2] - b[0], u[3] - b[1]),
                                outline=color, width=1)
                    if resolved:
                        d.text((u[0] - b[0], u[1] - b[1] - 12),
                               "NO V1" if frame == "m1" else "V2", fill=color)
                if mode == "detail":
                    raw = raw.resize((raw.width * 4, raw.height * 4))
                    marked = marked.resize((marked.width * 4, marked.height * 4))
                raw.save(output / f"{frame}-{mode}-raw.png")
                marked.save(output / f"{frame}-{mode}-marked.png")
            overview = photo.convert("RGB")
            overview.thumbnail((1200, 900))
            sx, sy = overview.width / photo.width, overview.height / photo.height
            b = spec["source_windows"][frame]["wide"]
            ImageDraw.Draw(overview).rectangle(
                (b[0] * sx, b[1] * sy, b[2] * sx, b[3] * sy), outline="#ffb04f", width=3
            )
            overview.save(output / f"{frame}-location.png")


def svg_group(polygons, color, name, opacity):
    result = f'<g data-layer="{name}" fill="{color}" stroke="{color}" '
    result += f'fill-opacity="{opacity}" stroke-width="1">'
    for key, p in polygons:
        path = " ".join(
            "M" + " L".join(f"{x},{y}" for x, y in ring.coords) + " Z"
            for ring in [p.exterior, *p.interiors]
        )
        result += f'<path d="{path}" fill-rule="evenodd"><title>{html.escape(key)}</title></path>'
    return result + "</g>"


def preview(groups, bounds, path):
    """Raster inspection of the same design polygons, not a modified source photograph."""
    left, top, right, bottom = bounds
    size = (int(2 * (right - left)), int(2 * (bottom - top)))
    canvas = Image.new("RGB", size, "#0b1724")
    for polygons, color, alpha in groups:
        for _, poly in polygons:
            mask = Image.new("L", size)
            d = ImageDraw.Draw(mask)
            rings = [poly.exterior, *poly.interiors]
            for i, ring in enumerate(rings):
                xy = [((x - left) * 2, (y - top) * 2) for x, y in ring.coords]
                d.polygon(xy, fill=alpha if i == 0 else 0)
            canvas.paste(color, (0, 0), mask)
            for ring in rings:
                ImageDraw.Draw(canvas).line(
                    [((x - left) * 2, (y - top) * 2) for x, y in ring.coords],
                    fill=color, width=2,
                )
    canvas.save(path)


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or not output.is_relative_to(root):
        raise ValueError("Output must be new and inside project")
    spec = json.loads(Path(spec_path).read_text())
    if spec["kind"] == "metal_via_layer_pair_pilot":
        return run_layer_pair(root, spec_path, output)
    if spec["kind"] in {"metal_via_transfer_pilot", "metal_via_candidate_pilot"}:
        return run_transfer(root, spec_path, output)
    if spec["kind"] != "M1_V1_M2_joint_pilot":
        raise ValueError("Unsupported pilot")
    inputs = Inputs(root)
    interface_review = reviewed_interface(inputs, spec)
    parent = inputs.document(spec["parent_M1_spec"])
    parent_model = inputs.document(spec["parent_M1_model"])
    parent_report = inputs.document(spec["parent_M1_report"])
    if parent_report["status"] != "SCOPED_REVIEWED_WITH_LIMITATIONS":
        raise ValueError("Missing scoped reviewed M1 baseline")
    reviewed_features(root, inputs, parent)
    inputs.read(parent["snapshot"])
    snapshot = load_snapshot(root, root / parent["snapshot"]["path"])
    for ref in [*snapshot["manifest"]["inputs"].values(),
                *snapshot["manifest"]["source_photos"].values()]:
        inputs.read(ref)
    if [o["id"] for o in parent_model["objects"]] != [o["id"] for o in parent["features"]]:
        raise ValueError("M1 parent object mismatch")
    for record, obj in zip(parent["features"], parent_model["objects"], strict=True):
        if not feature_polygon(record).equals(Polygon(obj["outer_xy"], obj["holes_xy"])):
            raise ValueError("M1 parent geometry mismatch")
    proposed = copy.deepcopy(parent["features"])
    addition = spec["candidate_M1_addition"]
    matches = [o for o in proposed if o["id"] == addition["metal_id"]]
    if len(matches) != 1:
        raise ValueError("Unknown M1 continuation identity")
    matches[0].setdefault("local_parts", []).append(addition["part"])
    geometry, m1_polys = geometry_audit(proposed, parent["budget"], parent_model["canvas_wh"])
    lower = m1_polys[[o["id"] for o in proposed].index(addition["metal_id"])]
    m2_geometry, m2_polys = geometry_audit(
        spec["M2_features"], spec["metal_budget"], parent_model["canvas_wh"]
    )
    if len(m2_polys) != 1 or spec["M2_features"][0]["layer"] != "M2":
        raise ValueError("This bounded pilot expects one declared upper bearing conductor")
    observation_ids = {o["id"] for o in spec["observations"]}
    if any(c["observation_id"] not in observation_ids for c in spec["cuts"]):
        raise ValueError("Unobserved via cannot be created from overlap")
    if len({c["observation_id"] for c in spec["cuts"]}) != len(spec["cuts"]):
        raise ValueError("One observation cannot create duplicate vias")
    if any(c["lower_metal_id"] != addition["metal_id"] or
           c["upper_metal_id"] != spec["M2_features"][0]["id"] for c in spec["cuts"]):
        raise ValueError("Via bearing identity mismatch")
    interface = interface_audit(spec["cuts"], lower, m2_polys[0], spec["via_budget"])
    correspondence = local_correspondence(
        spec["observations"], spec["fit_ids"], spec["same_array_tolerance_native_px"]
    )
    correspondence["macro_interface_identity_status"] = (
        "human_confirmed" if interface_review else "AI_candidate"
    )
    failed = any(r["status"] == "FAIL" for r in [geometry, m2_geometry, interface])
    failed |= correspondence["same_array_holdout_status"] == "FAIL"
    report = dict(
        status="FAIL" if failed else (
            "SCOPED_REVIEWED_WITH_LIMITATIONS" if interface_review else "REVIEW_REQUIRED"
        ),
        M1_geometry=geometry, M2_geometry=m2_geometry, via_geometry=interface,
        source_correspondence=correspondence,
        human_questions=spec["human_questions"],
        parent_M1_records_preserved=True,
        inherited_CT_model_enclosure_count=sum(
            r["CT_count"] for r in parent_report["CT_support_candidates"]
        ),
        parent_snapshot_unchanged=True, inherited_unknown_scopes=snapshot["values"]["unknown"],
        precise_projection_allowed=False,
        electrical_connection_confirmed=bool(interface_review) and not failed,
        electrical_connection_scope=(interface_review or {}).get("local_connection"),
        automatic_network_export_allowed=False, whole_frame_complete=False,
        physical_PDK_DRC=False, skill_generalization_validated=False,
        unknown_edge_column=spec["unknown_edge_column"],
        scoped_interface_review=interface_review,
        requires_user_action_now=bool(spec["human_questions"]),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".metal-via-", dir=output.parent) as tmp:
        stage = Path(tmp) / "delivery"
        stage.mkdir()
        write_json(stage / "report.json", report)
        write_json(stage / "spec.json", spec)
        # A failure keeps diagnostics only; never emit a plausible rejected candidate.
        if not failed:
            model = dict(
                kind="M1_V1_M2_companion_candidate", coordinate_space="shared_design_px",
                canvas_wh=parent_model["canvas_wh"], parent_M1=spec["parent_M1_model"],
                inherited_M1_objects=parent_model["objects"],
                proposed_M1_addition=addition, M2_objects=spec["M2_features"], V1_cuts=spec["cuts"],
                source_observations=spec["observations"],
                source_photos=snapshot["manifest"]["source_photos"],
                source_to_design_transform=None,
                new_geometry_status="AI_candidate_not_human_approved", net_edges=[],
                reviewed_local_connections=[interface_review["local_connection"]]
                if interface_review else [],
                native_only_V2_observations=[dict(
                    id="J-M2-EDGE-V2", layer="V2", layer_pair=["M2", "M3"],
                    source_frame="m2", source_bounds=spec["unknown_edge_column"]["m2_bounds"],
                    identity_status="human_confirmed", design_bounds=None, cut_count=None,
                    upper_metal_id=None, M3_connection_confirmed=False,
                )] if interface_review else [],
                width_and_edge_constraints=(interface_review or {}).get(
                    "width_and_edge_constraints"
                ),
                adopted_into_joint_snapshot=False, unprocessed_is_unknown=True,
            )
            write_json(stage / "model.json", model)
            source_panels(root, snapshot["manifest"], spec, stage)
            preview([
                ([(o["id"], feature_polygon(o)) for o in parent["features"]], "#6ad8ff", 70),
                ([("addition", box(*addition["part"]["bounds"]))], "#ffb04f", 90),
                ([("upper", m2_polys[0])], "#d28cff", 55),
                ([(c["id"], box(*c["bounds"])) for c in spec["cuts"]], "#fff4bd", 255),
            ], spec["design_bounds"], stage / "joint-design.png")
            svg = model_svg(snapshot, spec["design_bounds"]).replace("</svg>", "")
            svg += svg_group([(o["id"], feature_polygon(o)) for o in parent["features"]],
                             "#6ad8ff", "M1", .25)
            svg += svg_group([("M1 continuation candidate", box(*addition["part"]["bounds"]))],
                             "#ffb04f", "M1-addition", .35)
            svg += svg_group([(spec["M2_features"][0]["id"], m2_polys[0])],
                             "#d28cff", "M2", .22)
            svg += svg_group([(c["id"], box(*c["bounds"])) for c in spec["cuts"]],
                             "#fff4bd", "V1", 1)
            svg += "</svg>"
            (stage / "joint-design.svg").write_text(svg)
            questions = "".join(f'<li><b>{q["id"]}</b>：{html.escape(q["question"])}</li>'
                                for q in spec["human_questions"])
            page = (Path(__file__).with_suffix(".html").read_text()
                    .replace("{{SVG}}", svg).replace("{{QUESTIONS}}", questions)
                    .replace("{{ERROR}}", f'{correspondence["maximum_holdout_error_px"]:.2f}'))
            if interface_review:
                statements = "".join("<li>" + html.escape(s) + "</li>"
                                     for s in interface_review["verbatim_feedback"])
                panel = '<div class="card"><h2>J1／J2 已裁决</h2><ul>' + statements + "</ul>"
                panel += "<p>本处 M1→V1→M2 接口已确认，无待重复审批问题。"
                panel += "M1 红框无 V1；M2 绿框为 V2，仅记录原生观察，尚未确认接到哪根 M3。"
                panel += "粗 M1 右缘无 V1、四排孔距离作为宽度约束保留；"
                panel += "未将其解释为新增一排孔或精确像素跨度。</p></div>"
                start = page.index('<div class="card"><h2>本轮一次核对清单')
                end = page.index('<div class="card"><h2>质量门', start)
                page = page[:start] + panel + page[end:]
                page = page.replace("物理接口待审", "局部接口已审，精确投影仍未放行")
                page = page.replace("也不自动认定电气连接", "本处接入关系另有人工确认记录")
                page = page.replace("黄色框是待判的左缘窄列", "M1 红框无 V1，M2 绿框为 V2")
                page = page.replace("V1 候选", "V1（身份已审／边界候选）")
            (stage / "index.html").write_text(page)
        write_json(stage / "manifest.json", dict(
            verified_inputs=inputs.files, spec_sha256=digest(spec_path),
            code_sha256=digest(__file__),
            template_sha256=digest(Path(__file__).with_suffix(".html")),
            reused_code={name: digest(Path(__file__).with_name(name)) for name in (
                "metal_reconstruction.py", "joint_layers.py", "layer_review.py",
                "review_package.py", "geometry_reconstruction.py",
            )},
            artifacts={p.name: digest(p) for p in stage.iterdir()}, status=report["status"],
        ))
        stage.rename(output)
    return report


def run_transfer(root, spec_path, output):
    """Review an independent scene, with historical truth or a frozen AI hypothesis."""
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or not output.is_relative_to(root):
        raise ValueError("Output must be new and inside project")
    spec = json.loads(Path(spec_path).read_text())
    candidate = spec["kind"] == "metal_via_candidate_pilot"
    inputs = Inputs(root)
    adjudication = None
    if spec.get("adjudication"):
        if not candidate:
            raise ValueError("Only a frozen candidate can receive this adjudication")
        parent_spec = inputs.document(spec["adjudication"]["parent_spec"])
        adjudication = inputs.human(spec["adjudication"]["human_review"])
        expected = copy.deepcopy(parent_spec)
        expected["adjudication"] = spec["adjudication"]
        expected["human_questions"] = []
        if (expected != spec or adjudication["sources"]["parent_spec"]
                != spec["adjudication"]["parent_spec"]):
            raise ValueError(
                "Adjudication cannot revise frozen geometry, source or baseline context"
            )
        if adjudication["sources"]["initial_AI"] != spec["evidence"][
            spec["candidate_reference"]["evidence_key"]
        ]:
            raise ValueError("Adjudication must bind the original AI observation")
    baseline = {k: inputs.document(ref) for k, ref in spec["baseline"].items()}
    baseline_review = reviewed_interface(inputs, baseline["spec"])
    if (not baseline_review or baseline["report"]["status"] != "SCOPED_REVIEWED_WITH_LIMITATIONS"
            or baseline["model"]["reviewed_local_connections"]
            != [baseline_review["local_connection"]]):
        raise ValueError("Missing intact reviewed baseline")
    directory = root / Path(spec["baseline"]["manifest"]["path"]).parent
    for name, sha in baseline["manifest"]["artifacts"].items():
        inputs.read(dict(path=str((directory / name).relative_to(root)), sha256=sha))
    parent = inputs.document(baseline["spec"]["parent_M1_spec"])
    inputs.read(parent["snapshot"])
    snapshot = load_snapshot(root, root / parent["snapshot"]["path"])
    for ref in [*snapshot["manifest"]["inputs"].values(),
                *snapshot["manifest"]["source_photos"].values()]:
        inputs.read(ref)
    evidence = {key: inputs.document(ref) for key, ref in spec["evidence"].items()}
    if not evidence:
        raise ValueError("Missing source geometry observations")
    released_model = None
    if candidate:
        release = spec["released_design"]
        approval = inputs.human(release["approval"])
        if not approval["decisions"]["displayed_design_released"]:
            raise ValueError("The preceding design is not released")
        for key in ("model", "spec", "report"):
            if release[key] != approval["sources"][key]:
                raise ValueError("Released design reference changed")
        released_model = inputs.document(release["model"])
        released_manifest = inputs.document(release["manifest"])
        directory = root / Path(release["manifest"]["path"]).parent
        for name, sha in released_manifest["artifacts"].items():
            inputs.read(dict(path=str((directory / name).relative_to(root)), sha256=sha))
        initial = evidence[spec["candidate_reference"]["evidence_key"]]
        if initial["actor"] != "AI" or initial["evaluation"]["human_ground_truth"] is not None:
            raise ValueError("Candidate must retain its unreviewed AI origin")
        for frame in ("m1", "m2"):
            if initial["source_photos"][frame] != snapshot["manifest"]["source_photos"][frame]:
                raise ValueError("Candidate evidence frame does not match current raw photos")
        hypothesis = initial["hypothesis"]
        decision = dict(
            from_metal=hypothesis["upper_metal_id"], to_metal=hypothesis["lower_metal_id"],
            via_id=hypothesis["via_group_id"], via_kind=hypothesis["via_layer"],
            status="AI_candidate_not_human_reviewed",
        )
        statement = "新候选，尚无人工接入裁决"
        if decision["via_kind"] != "V1" or (not adjudication and not spec["human_questions"]):
            raise ValueError("Unreviewed V1 candidate must retain an explicit review question")
        if adjudication:
            accepted = dict(
                lower_metal_id=hypothesis["lower_metal_id"], via_layer=hypothesis["via_layer"],
                via_group_id=hypothesis["via_group_id"],
                upper_metal_id=hypothesis["upper_metal_id"],
                identity_confirmed=True, connection_confirmed=True,
            )
            if adjudication["decisions"] != accepted:
                raise ValueError("Reviewed candidate identity or destination was changed")
            decision["status"] = "human_confirmed_local_interface"
    else:
        history = spec["historical_interface"]
        record = inputs.document(history["record"])
        inputs.evidence(record)
        statement, decision = pointer(record, history["statement_pointer"]), pointer(
            record, history["decision_pointer"]
        )
        if (record.get("record_type") != "human_cross_layer_connection_review"
                or not statement or decision["status"] != history["required_status"]
                or decision["from_layer"] != "m2" or decision["to_layer"] != "m1"
                or decision["via_kind"] != "V1"):
            raise ValueError("Invalid historical interface review")
    for binding in spec["native_trace_bindings"]:
        trace = spec["native_traces"][binding["frame"]][binding["trace_index"]]
        if trace["points"] != pointer(evidence[binding["evidence_key"]], binding["pointer"]):
            raise ValueError("Native trace changed from the bound source observation")
    anchor = spec["placement_locator"]
    contacts = {o["id"]: o for o in snapshot["contacts"]}
    if contacts[anchor["contact_id"]]["layout_center"] != anchor["frozen_layout_center"]:
        raise ValueError("Current design locator changed")
    layers, polygons, audits = spec["features_by_layer"], {}, {}
    for layer in ("M1", "M2"):
        if any(f["layer"] != layer for f in layers[layer]):
            raise ValueError("Wrong conductor layer")
        audits[layer], polys = geometry_audit(
            layers[layer], spec["metal_budget"], snapshot["manifest"]["canvas_wh"]
        )
        polygons[layer] = {o["id"]: p for o, p in zip(layers[layer], polys, strict=True)}
    if (decision["to_metal"] != spec["lower_metal_id"]
            or decision["from_metal"] != spec["upper_metal_id"]
            or decision["via_id"] != spec["via_group_id"]):
        raise ValueError("Historical connection cannot be reassigned")
    observations = {o["id"]: o for o in spec["observations"]}
    if candidate:
        binding = spec["candidate_reference"]
        reference = observations[binding["observation_id"]]
        for frame, field in binding["reference_fields"].items():
            if reference[frame + "_xy"] != pointer(initial, field):
                raise ValueError("Frozen candidate reference cannot move after initial judgment")
    else:
        reference = observations[history["reference_observation_id"]]
        for frame, field in history["reference_fields"].items():
            if reference[frame + "_xy"] != decision[field]:
                raise ValueError(
                    "Historical via endpoint cannot move to another source bright spot"
                )
    cuts = spec["interface_support_regions"]
    if (len(cuts) != len(observations) or len(observations) != len(spec["observations"])
            or {c["observation_id"] for c in cuts} != set(observations)):
        raise ValueError("Unsupported extra via region or reused source observation")
    for cut in cuts:
        if (cut["lower_metal_id"] != decision["to_metal"]
                or cut["upper_metal_id"] != decision["from_metal"]
                or cut["via_group_id"] != decision["via_id"]):
            raise ValueError("Wrong interface bearing identity")
    via = interface_audit(
        cuts, polygons["M1"][spec["lower_metal_id"]],
        polygons["M2"][spec["upper_metal_id"]], spec["via_budget"],
    )
    controls = []
    if not spec["overlap_controls"]:
        raise ValueError("Transfer requires an overlap-without-via-evidence control")
    for control in spec["overlap_controls"]:
        a, b = polygons["M1"][control["lower_metal_id"]], polygons["M2"][control["upper_metal_id"]]
        if a.intersection(b).area <= 0:
            raise ValueError("Overlap control does not exercise an actual model overlap")
        controls.append(dict(**control, overlap_area_px2=a.intersection(b).area,
                             inferred_connection=False, physical_absence_confirmed=False))
    failed = any(a["status"] == "FAIL" for a in [*audits.values(), via])
    report = dict(
        status="FAIL" if failed else (
            "REVIEW_REQUIRED" if candidate else "KNOWN_EXAMPLE_TRANSFER_VERIFIED_WITH_LIMITATIONS"
        ),
        evaluation_type="AI_pre_review_candidate_not_strict_blind_test" if candidate
        else "known_historical_example_not_blind_recognition",
        geometry=audits, via_geometry=via, overlap_controls=controls,
        historical_statement=statement, local_connection=decision,
        exact_pixel_or_cut_count_human_approved=False,
        baseline_artifacts_preserved=True, baseline_human_decisions=baseline_review["decisions"],
        baseline_unknown_scopes=snapshot["values"]["unknown"],
        source_correspondence=dict(
            status="NOT_QUALIFIED", matrix=None,
            reason="Historical destination identity is not a precise transform",
        ),
        placement_status="AI_locator_in_shared_canvas_not_exact_joint_alignment",
        precise_projection_allowed=False, automatic_network_export_allowed=False,
        new_physical_connections=0, physical_cut_count=None, physical_PDK_DRC=False,
        human_questions=spec["human_questions"],
        requires_user_action_now=bool(spec["human_questions"]),
        skill_generalization_validated=False,
    )
    if candidate:
        report["hypothesized_local_connection"] = report.pop("local_connection")
        report["AI_review_note"] = report.pop("historical_statement")
        report["initial_AI_evaluation"] = initial["evaluation"]
        report["preceding_design_approval"] = release["approval"]
        report["source_correspondence"]["reason"] = (
            "Candidate correspondence not independently qualified"
        )
        if adjudication:
            report["status"] = "FAIL" if failed else "SCOPED_REVIEWED_WITH_LIMITATIONS"
            report["local_connection"] = report.pop("hypothesized_local_connection")
            report["scoped_human_review"] = adjudication
            report["evaluation_result"] = adjudication["evaluation_result"]
            report["new_physical_connections"] = 1
            report["new_connection_basis"] = (
                "human_scoped_adjudication_only_not_automatic_net_export"
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".metal-transfer-", dir=output.parent) as tmp:
        stage = Path(tmp) / "delivery"
        stage.mkdir()
        write_json(stage / "spec.json", spec)
        write_json(stage / "report.json", report)
        if not failed:
            model = dict(
                kind="metal_via_transfer_companion", coordinate_space="shared_design_px",
                placement_status=report["placement_status"], placement_locator=anchor,
                parent_snapshot=parent["snapshot"], baseline=spec["baseline"],
                objects_by_layer=layers, V1_support_regions=cuts,
                physical_cut_count=None, reviewed_local_connections=[] if candidate else [decision],
                net_edges=[], adopted_into_joint_snapshot=False,
                source_to_design_transform=None, unprocessed_is_unknown=True,
            )
            if candidate:
                model["hypothesized_local_connections"] = [] if adjudication else [decision]
                model["released_reference_design"] = release
                model["initial_AI_evaluation"] = initial["evaluation"]
                if adjudication:
                    model["reviewed_local_connections"] = [decision]
                    model["evaluation_result"] = adjudication["evaluation_result"]
                    model["adjudication"] = spec["adjudication"]
            write_json(stage / "model.json", model)
            source_panels(root, snapshot["manifest"], spec, stage)
            groups = [(list(polygons["M1"].items()), "#6ad8ff", 85),
                      (list(polygons["M2"].items()), "#d28cff", 70),
                      ([(c["id"], box(*c["bounds"])) for c in cuts], "#fff4bd", 255)]
            preview(groups, spec["design_bounds"], stage / "joint-design.png")
            svg = model_svg(snapshot, spec["design_bounds"]).replace("</svg>", "")
            for (items, color, alpha), layer in zip(groups, ("M1", "M2", "V1"), strict=True):
                svg += svg_group(items, color, layer, alpha / 255)
            if released_model:
                references = [(f["id"], feature_polygon(f))
                              for objects in released_model["objects_by_layer"].values()
                              for f in objects]
                svg += svg_group(references, "#8997a3", "reference", .10)
            svg += "</svg>"
            (stage / "joint-design.svg").write_text(svg)
            page = transfer_page(svg, statement)
            if candidate:
                page = candidate_page(page, spec)
                if adjudication:
                    page = reviewed_candidate_page(page, adjudication)
            (stage / "index.html").write_text(page)
        write_json(stage / "manifest.json", dict(
            verified_inputs=inputs.files, spec_sha256=digest(spec_path),
            code_sha256=digest(__file__),
            template_sha256=digest(Path(__file__).with_suffix(".html")),
            reused_code={name: digest(Path(__file__).with_name(name)) for name in (
                "metal_reconstruction.py", "joint_layers.py",
                "layer_review.py", "review_package.py",
            )},
            artifacts={p.name: digest(p) for p in stage.iterdir()}, status=report["status"],
        ))
        stage.rename(output)
    return report


def run_layer_pair(root, spec_path, output):
    """Extend a frozen lower conductor to a new pair; never inherit upper identity."""
    spec = json.loads(Path(spec_path).read_text())
    if spec["layer_stack"] != ["M2", "V2", "M3"]:
        raise ValueError("This migration requires the M2/V2/M3 stack")
    inputs = Inputs(root)
    adjudication = None
    question_origin = spec
    if spec.get("adjudication"):
        binding = spec["adjudication"]
        question_origin = inputs.document(binding["parent_spec"])
        if question_origin.get("adjudication"):
            raise ValueError("Layer-pair adjudication requires the original candidate")
        expected = copy.deepcopy(question_origin)
        expected["adjudication"] = binding
        expected["human_questions"] = []
        if spec != expected:
            raise ValueError("Layer-pair approval cannot revise frozen geometry or evidence")
        adjudication = inputs.human(binding["human_review"])
        hypothesis = spec["hypothesis"]
        expected_decision = {k: hypothesis[k] for k in (
            "id", "lower_metal_id", "via_group_id", "via_layer", "upper_metal_id"
        )}
        expected_decision["connection_confirmed"] = True
        if adjudication["decisions"] != expected_decision:
            raise ValueError("Layer-pair approval changed the submitted destination")
    baseline = {k: inputs.document(v) for k, v in spec["baseline"].items()}
    review = reviewed_interface(inputs, baseline["spec"])
    if review is None or baseline["report"]["status"] != "SCOPED_REVIEWED_WITH_LIMITATIONS":
        raise ValueError("Missing reviewed lower-pair baseline")
    for name, sha in baseline["manifest"]["artifacts"].items():
        inputs.read(dict(path=str(Path(spec["baseline"]["manifest"]["path"]).parent / name),
                         sha256=sha))
    parent = inputs.document(baseline["spec"]["parent_M1_spec"])
    inputs.read(parent["snapshot"])
    snapshot = load_snapshot(root, root / parent["snapshot"]["path"])
    for ref in [*snapshot["manifest"]["inputs"].values(),
                *snapshot["manifest"]["source_photos"].values()]:
        inputs.read(ref)
    initial = inputs.document(spec["initial_observation"])
    inputs.evidence(initial)
    if (initial["actor"] != "AI" or initial["stage"] != "before_new_pair_human_review"
            or any(v is not None for v in initial["evaluation"].values())):
        raise ValueError("Initial AI observation cannot contain unreceived human truth")
    inherited = next(o for o in baseline["model"]["native_only_V2_observations"]
                     if o["id"] == spec["inherited_via_id"])
    if (inherited["layer"] != "V2" or inherited["layer_pair"] != ["M2", "M3"]
            or inherited["source_frame"] != "m2"
            or inherited["identity_status"] != "human_confirmed"
            or inherited["M3_connection_confirmed"]):
        raise ValueError("Inherited V2 identity must not include an unreviewed M3")
    if initial["inherited_via"] != inherited:
        raise ValueError("Inherited V2 evidence cannot move or change layer")
    region = spec["source_regions"]["m2"]
    if len(region) != 1 or region[0]["bounds"] != inherited["source_bounds"]:
        raise ValueError("Reviewed V2 native window cannot move")
    for field in ("source_regions", "native_traces", "hypothesis", "features_by_layer"):
        if spec[field] != initial[field]:
            raise ValueError("Frozen initial source or hypothesis changed: " + field)
    if (question_origin["human_questions"] != initial["human_questions"]
            or not question_origin["human_questions"] or spec["observations"]):
        raise ValueError("Retain destination review; no fabricated M3 via centers")
    layers = spec["features_by_layer"]
    lower = next(f for f in baseline["spec"]["M2_features"]
                 if f["id"] == spec["hypothesis"]["lower_metal_id"])
    if layers["M2"] != [lower] or layers["M2"] != initial["frozen_lower_features"]:
        raise ValueError("Frozen lower M2 geometry cannot change in pair migration")
    audits, polygons = {}, {}
    for layer in ("M2", "M3"):
        if not layers[layer] or any(o["layer"] != layer for o in layers[layer]):
            raise ValueError("Wrong or missing conductor layer")
        audits[layer], ps = geometry_audit(
            layers[layer], spec["metal_budget"], snapshot["manifest"]["canvas_wh"]
        )
        polygons[layer] = {o["id"]: p for o, p in zip(layers[layer], ps, strict=True)}
    cuts = spec["interface_support_regions"]
    hypothesis = spec["hypothesis"]
    if (hypothesis["via_group_id"] != inherited["id"] or hypothesis["via_layer"] != "V2"
            or hypothesis["status"] != "AI_candidate_not_human_confirmed"):
        raise ValueError("Inherited via identity cannot confer new destination approval")
    if (len(cuts) != 1 or cuts[0]["observation_id"] != inherited["id"]
            or cuts[0]["via_group_id"] != inherited["id"]
            or cuts[0]["lower_metal_id"] != hypothesis["lower_metal_id"]
            or cuts[0]["upper_metal_id"] != hypothesis["upper_metal_id"]
            or cuts[0]["electrical_connection_confirmed"] is not False
            or cuts[0]["role"] != "group_support_proxy_not_measured_cut"):
        raise ValueError("Via support must bind inherited evidence and declared bearings")
    via = interface_audit(cuts, polygons["M2"][hypothesis["lower_metal_id"]],
                          polygons["M3"][hypothesis["upper_metal_id"]],
                          spec["via_budget"], layer_stack=spec["layer_stack"])
    via["support_region_count"] = via.pop("candidate_cut_count")
    via["physical_cut_count"] = None
    controls = []
    for control in spec["overlap_controls"]:
        a = polygons["M2"][control["lower_metal_id"]]
        b = polygons["M3"][control["upper_metal_id"]]
        if a.intersection(b).area <= 0:
            raise ValueError("Control must exercise real cross-layer overlap")
        if control["upper_metal_id"] == hypothesis["upper_metal_id"]:
            raise ValueError("Control cannot masquerade as the proposed interface")
        controls.append(dict(**control, overlap_area_px2=a.intersection(b).area,
                             inferred_connection=False, physical_absence_confirmed=False))
    if not controls:
        raise ValueError("Missing overlap-without-via-evidence control")
    failed = any(a["status"] == "FAIL" for a in [*audits.values(), via])
    report = dict(
        status="FAIL" if failed else "REVIEW_REQUIRED", layer_stack=spec["layer_stack"],
        geometry=audits, via_geometry=via, overlap_controls=controls,
        inherited_via_identity="human_confirmed_V2_not_reasked",
        hypothesized_local_connection=hypothesis, physical_cut_count=None,
        source_correspondence=dict(status="NOT_QUALIFIED", matrix=None,
                                   independent_structure_status="NOT_QUALIFIED",
                                   reason=initial["correspondence_limit"]),
        precise_projection_allowed=False, extrapolation_allowed=False,
        baseline_artifacts_preserved=True, lower_geometry_unchanged=True,
        baseline_unknown_scopes=snapshot["values"]["unknown"],
        source_to_design_transform=None, physical_PDK_DRC=False,
        automatic_network_export_allowed=False, new_physical_connections=0,
        human_questions=spec["human_questions"], requires_user_action_now=True,
        skill_generalization_validated=False,
    )
    connection = None
    if adjudication:
        connection = dict(**adjudication["decisions"], status="human_confirmed_local_interface",
                          human_review=spec["adjudication"]["human_review"])
        report["status"] = "FAIL" if failed else "SCOPED_REVIEWED_WITH_LIMITATIONS"
        report["local_connection"] = connection
        report.pop("hypothesized_local_connection")
        report["scoped_human_review"] = adjudication
        report["evaluation_result"] = adjudication["evaluation_result"]
        report["new_physical_connections"] = 0 if failed else 1
        report["new_connection_basis"] = "human_scoped_adjudication_not_automatic_net_export"
        report["requires_user_action_now"] = False
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".layer-pair-", dir=output.parent) as tmp:
        stage = Path(tmp) / "delivery"
        stage.mkdir()
        write_json(stage / "spec.json", spec)
        write_json(stage / "report.json", report)
        if not failed:
            write_json(stage / "model.json", dict(
                kind="metal_via_layer_pair_companion", coordinate_space="shared_design_px",
                objects_by_layer=layers, V2_support_regions=cuts,
                inherited_native_V2=inherited, physical_cut_count=None,
                hypothesized_local_connections=[] if adjudication else [hypothesis],
                reviewed_local_connections=[connection] if adjudication else [],
                net_edges=[], adopted_into_joint_snapshot=False,
                source_to_design_transform=None, initial_observation=spec["initial_observation"],
                parent_snapshot=parent["snapshot"], baseline=spec["baseline"],
            ))
            source_panels(root, snapshot["manifest"], spec, stage, frames=("m2", "m3"))
            groups = [(list(polygons["M2"].items()), "#6ad8ff", 85),
                      (list(polygons["M3"].items()), "#d28cff", 90),
                      ([(c["id"], box(*c["bounds"])) for c in cuts], "#fff4bd", 255)]
            preview(groups, spec["design_bounds"], stage / "joint-design.png")
            svg = model_svg(snapshot, spec["design_bounds"]).replace("</svg>", "")
            for (items, color, alpha), layer in zip(groups, spec["layer_stack"][::2]
                                                   + ["V2"], strict=True):
                svg += svg_group(items, color, layer, alpha / 255)
            svg += "</svg>"
            (stage / "joint-design.svg").write_text(svg)
            (stage / "index.html").write_text(layer_pair_page(svg, spec, adjudication))
        write_json(stage / "manifest.json", dict(
            verified_inputs=inputs.files, spec_sha256=digest(spec_path),
            code_sha256=digest(__file__),
            template_sha256=digest(Path(__file__).with_suffix(".html")),
            reused_code={name: digest(Path(__file__).with_name(name)) for name in (
                "metal_reconstruction.py", "joint_layers.py", "layer_review.py", "review_package.py"
            )},
            artifacts={p.name: digest(p) for p in stage.iterdir()}, status=report["status"],
        ))
        stage.rename(output)
    return report


def layer_pair_page(svg, spec, review=None):
    template = Path(__file__).with_suffix(".html").read_text()
    style = template[template.index("<style>"):template.index("</style>") + 8]
    script = template[template.index("<script>"):template.index("</script>") + 9]
    page = '<!doctype html><html lang="zh"><meta charset="utf-8">'
    page += '<meta name="viewport" content="width=device-width,initial-scale=1">'
    page += '<title>M2／V2／M3 联合小样</title>' + style
    page += '<h1>M2／V2／M3 联合小样：第一组左缘V2向上接续</h1>'
    page += '<div class="card"><h2>只需确认M3承载金属</h2><ol>'
    page += ''.join('<li>' + html.escape(q["question"]) + '</li>'
                    for q in spec["human_questions"])
    page += '</ol><p>M2橙框的V2身份已经确认，不重复审批。B1紫色粗横线是本次M3候选；'
    page += 'B0为其上方相邻细横线，仅作隔离及重叠对照。M3没有标出虚构的对应孔中心。</p></div>'
    page += '<div class="card"><h2>几何通过，跨层承载关系待审</h2><p>'
    page += 'M2沿用原记录不动，M3横平竖直，粗细横线隔离；V2组的最小支持区被两层包围。'
    page += '这个支持区不代表实测单孔或完整孔数。交叠对照不自动生成连接，也不证明物理无孔。'
    page += '</p><p class="notice">尚无足够独立结构对应，精确配准门未放行。照片各自保留原生坐标，'
    page += '没有强行跨层叠图；设计图表达相对候选。相对像素检查不等于真实PDK DRC。'
    page += 'M3两端均继续出窗，未追整网；AA／POLY／CT及此前批准不变。</p></div>'
    page += '<h2>共同设计坐标（支持层切换）</h2><p>蓝色M2；紫色M3；米白V2支持区。</p>'
    for layer in ("M2", "M3", "V2", "AA", "POLY", "CT", "unknown"):
        checked = "checked" if layer in {"M2", "M3", "V2"} else ""
        page += f'<label><input type="checkbox" {checked} data-toggle="{layer}">{layer}</label>'
    page += svg + '<h2>原图并列：含上下两排及相邻横线</h2>'
    page += '<button id="raw">原图</button><button id="marked">候选标记</button><div class="grid">'
    for mode in ("wide", "detail"):
        for frame in ("m2", "m3"):
            key = frame + "-" + mode
            page += f'<div><h2>{frame.upper()} {mode}</h2><a data-image="{key}" '
            page += f'href="{key}-marked.png"><img data-source="{key}" '
            page += f'src="{key}-marked.png"></a></div>'
    page += '</div><details><summary>全幅定位</summary><div class="grid">'
    page += '<img src="m2-location.png"><img src="m3-location.png"></div></details>'
    page += '<p><a href="model.json">候选模型</a> · <a href="report.json">质量门</a> · '
    page += '<a href="spec.json">输入</a> · <a href="manifest.json">来源哈希</a></p>'
    if review:
        start = page.index('<div class="card"><h2>只需确认M3承载金属')
        end = page.index('<div class="card"><h2>几何通过', start)
        card = '<div class="card"><h2>K1已确认：V2接入B1粗横向M3母线</h2><p>用户裁决：'
        card += html.escape(review["statement"]) + '</p><p>M2-J01 → J-M2-EDGE-V2 → '
        card += 'M3-J-B1的局部接入已记录，无待重复审批问题。B0仍是相邻细线对照，'
        card += '未新增其连接或判定物理无孔。首次候选、原几何和照片标记均保留。</p></div>'
        page = page[:start] + card + page[end:]
        page = page.replace('几何通过，跨层承载关系待审', '局部承载关系已审，精确投影仍未核准')
        page = page.replace('设计图表达相对候选', '几何尺寸仍为相对候选，连接身份已确认')
        page = page.replace('>候选模型</a>', '>已审接口与候选几何</a>')
    return page + script + '</html>'


def transfer_page(svg, statement):
    """Reuse the same source-mode and layer controls for an independent scene."""
    template = Path(__file__).with_suffix(".html").read_text()
    style = template[template.index("<style>"):template.index("</style>") + 8]
    script = template[template.index("<script>"):template.index("</script>") + 9]
    page = '<!doctype html><html lang="zh"><meta charset="utf-8">'
    page += '<meta name="viewport" content="width=device-width,initial-scale=1">'
    page += "<title>第二组：短支路接口迁移验证</title>" + style
    page += "<h1>第二组：W1短竖M1／V1／M2接口</h1>"
    page += '<div class="card"><h2>已知样本迁移回放，不是新盲测</h2><p>'
    page += html.escape(statement) + "</p><p>这条连接沿用此前人审。当前检查新规则几何是否"
    page += "保持短M1与上下横线隔离、由M2短竖端部承载V1，不重复请求批准。</p></div>"
    page += "<p>蓝色：三条独立M1（W1短竖、上横线、下横线）；紫色：M2短竖及宽端部。"
    page += "米白色为V1组的最小包围支持区，不能解读成实测只有一个孔。</p>"
    page += '<div class="card"><h2>通过与限制</h2><p>逐层几何、隔离、上下层包围通过。'
    page += "M2与上横M1在模型中重叠，但没有对应V1证据，因此不生成连接；"
    page += "这也不宣称照片已证明此处物理无孔。</p><p class=\"notice\">"
    page += "第一组的V1／V2区分及无V1边缘保持。不能把M2宽端部的亮点自动当V1。"
    page += "本组没有独立合格的精确M1↔M2投影；原图并列，不强行叠图。设计坐标仅为"
    page += "共同画布中的AI候选定位，不据此建立新CT／AA归属或自动并网。</p></div>"
    for layer in ("M1", "M2", "V1", "AA", "POLY", "CT", "unknown"):
        checked = "checked" if layer in {"M1", "M2", "V1"} else ""
        page += f'<label><input type="checkbox" {checked} data-toggle="{layer}">{layer}</label>'
    page += svg + '<h2>两层原图：宽上下文及4倍放大</h2>'
    page += '<button id="raw">原图</button><button id="marked">观察线／接口参考点</button>'
    page += '<div class="grid">'
    for mode in ("wide", "detail"):
        for frame in ("m1", "m2"):
            key = frame + "-" + mode
            page += f'<div><h2>{frame.upper()} {mode}</h2><a data-image="{key}" '
            page += f'href="{key}-marked.png"><img data-source="{key}" '
            page += f'src="{key}-marked.png"></a></div>'
    page += '</div><details><summary>全图定位</summary><div class="grid">'
    page += '<img src="m1-location.png"><img src="m2-location.png"></div></details>'
    page += '<p><a href="model.json">模型</a> · <a href="report.json">检查与继承裁决</a> · '
    page += '<a href="spec.json">输入</a> · <a href="manifest.json">哈希</a></p>'
    return page + script + "</html>"


def candidate_page(page, spec):
    """Keep new hypotheses visibly distinct from the two frozen reviewed examples."""
    start = page.index('<div class="card"><h2>已知样本迁移回放')
    end = page.index("<p>蓝色", start)
    card = '<div class="card"><h2>新候选：请只裁决N1</h2><p>'
    card += html.escape(spec["candidate_summary"]) + "</p><ol>"
    card += "".join(f'<li><b>{html.escape(q["id"])}</b>：{html.escape(q["question"])}</li>'
                    for q in spec["human_questions"])
    card += "</ol><p>本次AI判断已先保存；未填正确率、人工答案或返工次数。"
    card += "此前W1设计放行与第一组J1/J2继续有效，不转移为N1接入批准。</p></div>"
    page = page[:start] + card + page[end:]
    page = page.replace("第二组：短支路接口迁移验证", "第三组：新短支路接口候选N1")
    page = page.replace("第二组：W1短竖M1／V1／M2接口", "第三组：W1左侧新短支路N1")
    page = page.replace("W1短竖、上横线、下横线", "N1短竖及上下文横线")
    page = page.replace("紫色：M2短竖及宽端部", "紫色：M2折线短支路候选")
    page = page.replace('<h2>通过与限制</h2>', '<h2>几何通过，N1身份与接入待审</h2>')
    page = page.replace("本组没有独立合格", "N1没有独立合格")
    marker = '<label><input type="checkbox" checked data-toggle="M1">'
    page = page.replace(marker, '<p>灰色为第二组已审W1设计参照，原图中的REF-W1同样只作参照。</p>'
                        '<label><input type="checkbox" checked '
                        'data-toggle="reference">已审参照</label>'
                        + marker)
    return page


def reviewed_candidate_page(page, review):
    start = page.index('<div class="card"><h2>新候选：请只裁决N1')
    end = page.index("<p>蓝色", start)
    card = '<div class="card"><h2>N1身份与接入已确认</h2><p>用户裁决：'
    card += html.escape(review["statement"]) + "</p><p>短竖M1上端V1接到折线M2下端，"
    card += "N1关闭，无待重复审批问题。首次AI判断及候选版本保持原样，"
    card += "本轮身份和接入判断各通过1例，未发生身份／接入修订；"
    card += "这不代表陌生照片准确率或全项目返工统计。</p>"
    card += "<p>未扩大为实测孔数、精确边界或原生投影批准。"
    card += "M2上部亮带仍未分型，自动网络导出保持关闭。</p></div>"
    page = page[:start] + card + page[end:]
    page = page.replace("新短支路接口候选N1", "N1接口已审")
    page = page.replace("第三组：W1左侧新短支路N1", "第三组：N1接口已审")
    return page.replace("几何通过，N1身份与接入待审", "N1已审，精确投影仍未放行")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.root, args.spec, args.output)
    print(json.dumps(dict(status=result["status"], geometry=result["via_geometry"]["status"])))
    if result["status"] == "FAIL":
        raise SystemExit(2)
