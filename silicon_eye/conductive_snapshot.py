"""Assemble replayable local conductor workspaces over a locked material snapshot.

Run: python -m silicon_eye.conductive_snapshot --request CONFIG --output NEW_DIR
Requires project dependencies. Keeps local coordinate domains separate; neither
adopts canonical geometry nor infers new connections from geometric overlap.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
import os
import re
import tempfile
from pathlib import Path
from string import Template

from shapely.geometry import box
from shapely.ops import unary_union

from .conductive_layers import svg_layers
from .conductive_workflow import load_parent, prepare
from .geometry_reconstruction import digest
from .joint_layers import load_snapshot
from .review_package import Inputs


def object_index(model):
    result = {}
    for layer, objects in model["objects_by_layer"].items():
        for obj in objects:
            if obj["id"] in result or obj["layer"] != layer:
                raise ValueError("Duplicate object ID or wrong layer")
            result[obj["id"]] = obj
    return result


def load_work(inputs, ref):
    manifest = inputs.document(ref)
    directory = Path(ref["path"]).parent
    for name, sha in manifest["artifacts"].items():
        inputs.read(dict(path=str(directory / name), sha256=sha))
    return inputs.document(
        dict(path=str(directory / "snapshot.json"), sha256=manifest["artifacts"]["snapshot.json"])
    )


def require_preserved(parent, current):
    if parent["material_snapshot"] != current["material_snapshot"]:
        raise ValueError("Work continuation cannot change the material snapshot")
    if not parent["domains"].keys() <= current["domains"].keys():
        raise ValueError("Work continuation lost a coordinate domain")
    old = {o["key"]: (o["id"], o["layer"], o["coordinate_space"]) for o in parent["objects"]}
    new = {o["key"]: (o["id"], o["layer"], o["coordinate_space"]) for o in current["objects"]}
    if any(new.get(key) != identity for key, identity in old.items()):
        raise ValueError("Work continuation lost or reassigned stable IDs")
    for field in ("reviewed_interfaces", "accepted_groups", "reviewed_terminal_links"):
        if any(row not in current[field] for row in parent[field]):
            raise ValueError("Work continuation lost reviewed records: " + field)
    for key in parent["coordinate_spaces"]:
        if parent["coordinate_spaces"][key] != current["coordinate_spaces"][key]:
            raise ValueError("Work continuation changed a coordinate space")
    if parent["material_unknowns"] != current["material_unknowns"]:
        raise ValueError("Work continuation changed unresolved material scopes")


def focus_metrics(model, focus):
    objects = object_index(model)
    unions, carriers, counts, cut_metrics = {}, {}, {}, {}
    for layer, field in [("V1", "v1_id"), ("V2", "v2_id")]:
        obj = objects[focus[field]]
        if obj["layer"] != layer or not obj.get("candidate_cut_bounds"):
            raise ValueError("Focus must name two explicit arrays on different via layers")
        unions[layer] = unary_union([box(*b) for b in obj["candidate_cut_bounds"]])
        counts[layer] = len(obj["candidate_cut_bounds"])
        cuts = obj["candidate_cut_bounds"]
        cut_metrics[layer] = dict(
            sizes_xy=[list(size) for size in sorted({(r-a, b-y) for a, y, r, b in cuts})],
            centers_xy=[[(a+r)/2, (y+b)/2] for a, y, r, b in cuts],
        )
        interface = next(
            c
            for c in model["reviewed_local_connections"]
            if c.get("support_id", c["id"]) == focus[field]
        )
        carriers[layer] = interface
    m2_id = carriers["V2"]["lower_metal_id"]
    if carriers["V1"]["upper_metal_id"] != m2_id:
        raise ValueError("Focused via groups do not share an M2 carrier")
    metal = objects[m2_id]["geometry"]["outer_xy"]
    xs, ys = zip(*metal, strict=True)
    x, y, r, b = unions["V2"].bounds
    return dict(
        unit="relative_design_px_not_photo_registration_or_PDK",
        V1_design_cuts=counts["V1"],
        V2_design_cuts=counts["V2"],
        V1_V2_overlap_area=unions["V1"].intersection(unions["V2"]).area,
        V1_V2_group_overlap_area=unions["V1"].envelope.intersection(unions["V2"].envelope).area,
        common_M2=m2_id,
        V2_M2_width_fraction=(r - x) / (max(xs) - min(xs)),
        V2_M2_height_fraction=(b - y) / (max(ys) - min(ys)),
        exact_geometry_accepted=False,
        via_geometry=cut_metrics,
    )


def assemble(root, request):
    root, inputs = Path(root).resolve(), Inputs(root)
    if request["schema_version"] != 1 or request["kind"] != "conductive_work_snapshot_request":
        raise ValueError("Unsupported work snapshot request")
    for flag in (
        "material_geometry_adoption",
        "cross_canvas_projection",
        "automatic_network_export_allowed",
    ):
        if request.get(flag) is not False:
            raise ValueError("Work snapshot cannot enable geometry adoption or projection/export")
    inputs.document(request["material_snapshot"])
    material = load_snapshot(root, root / request["material_snapshot"]["path"])
    for ref in material["manifest"]["inputs"].values():
        inputs.read(ref)
    for ref in material["manifest"]["source_photos"].values():
        inputs.read(ref)
    if material["manifest"].get("conductive_layers"):
        inputs.read(material["manifest"]["conductive_layers"])
    work = dict(
        schema_version=1,
        kind="conductive_work_snapshot",
        id=request["id"],
        material_snapshot=request["material_snapshot"],
        inherited_conductive_registry=material["manifest"].get("conductive_layers"),
        native_frames={
            key: dict(photo=ref, size_wh=material["manifest"]["source_wh"], unit="px")
            for key, ref in material["manifest"]["source_photos"].items()
        },
        coordinate_spaces={
            "materials": dict(
                canvas_wh=material["manifest"]["canvas_wh"], role="inherited_material_design_canvas"
            )
        },
        material_counts=dict(
            AA=len(material["materials"]["AA_objects"]),
            POLY=len(material["materials"]["objects"]),
            CT=len(material["contacts"]),
        ),
        material_unknowns=copy.deepcopy(material["values"]["unknown"]),
        domains={},
        objects=[],
        reviewed_interfaces=[],
        accepted_groups=[],
        reviewed_terminal_links=[],
        net_edges=[],
        automatic_network_export_allowed=False,
        complete_network=False,
        canonical_geometry_adopted=False,
        cross_canvas_projection=False,
        precise_projection_allowed=False,
    )
    render, reports, focus_ids = {}, {}, set()
    for domain in request["domains"]:
        key = domain["id"]
        if key in work["coordinate_spaces"] or not re.fullmatch(r"[A-Za-z0-9_-]+", key):
            raise ValueError("Duplicate or invalid coordinate domain")
        focus_id = domain["focus"]["id"]
        if focus_id in focus_ids or not re.fullmatch(r"[A-Za-z0-9_-]+", focus_id):
            raise ValueError("Duplicate or invalid focus ID")
        focus_ids.add(focus_id)
        if (
            domain.get("placement_in_material_canvas") is not None
            or domain.get("source_to_design_transform") is not None
        ):
            raise ValueError("Unqualified local canvas cannot claim a placement or projection")
        model, _ = load_parent(inputs, domain["package"])
        folder = Path(domain["package"]["path"]).parent
        manifest = inputs.document(domain["package"])
        report = inputs.document(
            dict(path=str(folder / "report.json"), sha256=manifest["artifacts"]["report.json"])
        )
        next_request = inputs.document(domain["next_request"])
        if next_request.get("parent") != domain["package"]:
            raise ValueError("Continuation request must bind the current package")
        replay, replay_report, sample, snapshot, files = prepare(root, next_request)
        inputs.files.update(files)
        if (
            sample["snapshot"] != request["material_snapshot"]
            or model["source_photos"] != material["manifest"]["source_photos"]
        ):
            raise ValueError("Conductor and material photo snapshot differ")
        if (
            replay != model
            or replay_report["changed_object_ids"]
            or report["quality"]["execution_checks"] != "PASS"
        ):
            raise ValueError("Work package fails exact no-change continuation")
        previous, _ = load_parent(inputs, domain["comparison_parent"])
        old, current = object_index(previous), object_index(model)
        if old.keys() != current.keys():
            raise ValueError("Comparison silently adds or retires IDs")
        changes = sorted(k for k in old if old[k] != current[k])
        if changes != sorted(domain["expected_geometry_changes"]):
            raise ValueError("Geometry change scope differs from declared comparison")
        if previous["reviewed_local_connections"] != model["reviewed_local_connections"]:
            raise ValueError("Previously approved connections changed")
        for layer in domain["preserve_layers"]:
            if previous["objects_by_layer"][layer] != model["objects_by_layer"][layer]:
                raise ValueError("Preserved layer changed")
        if model.get("source_to_design_transform") is not None:
            raise ValueError("Unqualified local canvas cannot claim photo projection")
        x, y, width, height = domain["focus"]["viewbox"]
        if not (
            0 <= x < x + width <= model["canvas_wh"][0]
            and 0 <= y < y + height <= model["canvas_wh"][1]
        ):
            raise ValueError("Focus view is outside local canvas")
        feedback = inputs.human(domain["focus"]["feedback"])
        if feedback.get("exact_candidate_geometry_accepted") is not False:
            raise ValueError("Qualitative feedback must retain its geometry limitation")
        metrics = focus_metrics(model, domain["focus"])
        zoom = domain["focus"]["zoom_viewbox"]
        zoom_window = box(zoom[0], zoom[1], zoom[0] + zoom[2], zoom[1] + zoom[3])
        for value in (previous, model):
            objects = object_index(value)
            for name in ("v1_id", "v2_id"):
                for cut in objects[domain["focus"][name]]["candidate_cut_bounds"]:
                    if not zoom_window.covers(box(*cut)):
                        raise ValueError("Zoom view omits part of a focused via group")
        for layer, name in (("V1", "v1_id"), ("V2", "v2_id")):
            row = next(
                r
                for r in report["quality"]["interface_geometry"]
                if r["id"] == domain["focus"][name]
            )
            metrics[layer + "_human_count"] = row["human_cut_count"]
        # Qualitative group overlap must not force inflated individual cut sizes.
        if metrics["V1_V2_group_overlap_area"] <= 0:
            raise ValueError("Current focus does not implement the reviewed overlap intent")
        work["coordinate_spaces"][key] = dict(
            canvas_wh=model["canvas_wh"],
            role="local_regular_design_candidate",
            placement_in_material_canvas=None,
            source_to_design_transform=None,
        )
        work["domains"][key] = dict(
            package=domain["package"],
            next_request=domain["next_request"],
            geometry_status="candidate_not_new_human_approval",
            focus_metrics=metrics,
            changed_since_feedback=changes,
            material_ID_mapping_status="not_established_no_coordinate_merge",
            limits=copy.deepcopy(model["limits"]),
            pending_interfaces=copy.deepcopy(model["pending_interface_ids"]),
            quality_gaps=copy.deepcopy(report["quality"]["blocking_adoption_reasons"]),
            coverage=copy.deepcopy(report["quality"]["coverage"]),
            interface_geometry=copy.deepcopy(report["quality"]["interface_geometry"]),
            candidate_paths=copy.deepcopy(model.get("path_hypotheses", [])),
        )
        for obj in current.values():
            work["objects"].append(
                dict(
                    key=key + "::" + obj["id"],
                    id=obj["id"],
                    layer=obj["layer"],
                    coordinate_space=key,
                    package=domain["package"],
                    kind=obj["kind"],
                    source_frame=obj.get("source_frame"),
                    native_locator=(
                        dict(path=obj["native_path"])
                        if obj.get("native_path")
                        else obj.get("source_observation")
                    ),
                    geometry_status="candidate",
                )
            )
        for edge in model["reviewed_local_connections"]:
            work["reviewed_interfaces"].append(dict(coordinate_space=key, record=edge))
        for group in model.get("accepted_structural_groups", []):
            work["accepted_groups"].append(dict(coordinate_space=key, record=group))
        terminal = model.get("branch", {}).get("reviewed_terminal_connection")
        if terminal:
            work["reviewed_terminal_links"].append(
                dict(
                    coordinate_space=key,
                    record=terminal,
                    material_ID_mapping_status="unknown_not_filled_from_nearby_geometry",
                )
            )
        render[key] = (model, previous, sample, next_request, domain)
        reports[key] = dict(
            continuation_exact=True,
            connections_preserved=True,
            geometry_changes=changes,
            metrics=metrics,
            package_quality=report["quality"]["status"],
        )
    if not work["domains"]:
        raise ValueError("A work snapshot needs at least one conductor domain")
    if request.get("parent_work_snapshot"):
        require_preserved(load_work(inputs, request["parent_work_snapshot"]), work)
    summary = dict(
        status="WORK_SNAPSHOT_READY_GEOMETRY_REVIEW_PENDING",
        work_snapshot_ready=True,
        domain_count=len(work["domains"]),
        object_count=len(work["objects"]),
        reviewed_interface_count=len(work["reviewed_interfaces"]),
        reviewed_terminal_count=len(work["reviewed_terminal_links"]),
        material_counts=work["material_counts"],
        domains=reports,
        canonical_geometry_adoption=False,
        complete_network_export=False,
        material_canvas_registration=False,
        note="Readiness means scoped continuation, not physical approval.",
    )
    return work, summary, render, inputs.files


def page(root, output, work, summary, render):
    sections = []
    for key, (model, previous, _sample, req, domain) in render.items():
        x, y, width, height = domain["focus"]["viewbox"]
        bounds = [x, y, x + width, y + height]

        def drawing(value, x=x, y=y, width=width, height=height, bounds=bounds):
            centers = ""
            for layer in ("V1", "V2"):
                centers += f'<g data-layer="{layer}"><g class="via-centers">'
                for obj in value["objects_by_layer"][layer]:
                    for a, b, c, d in obj.get("candidate_cut_bounds", []):
                        cx, cy = (a+c)/2, (b+d)/2
                        centers += (
                            f'<path d="M{cx-1} {cy}H{cx+1}M{cx} {cy-1}V{cy+1}" '
                            'fill="none" stroke="white" stroke-width="1.5" '
                            'vector-effect="non-scaling-stroke"/>'
                        )
                centers += "</g></g>"
            return (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {width} {height}">'
                '<style>[data-layer="V1"] path{fill-opacity:.65}'
                '[data-layer="V2"] path{fill-opacity:.25}</style>'
                + svg_layers(value, bounds)
                + centers
                + "</svg>"
            )

        metrics = summary["domains"][key]["metrics"]
        evidence = []
        for frame in ("m1", "m2", "m3"):
            items = []
            for size, label in [("wide", "宽图"), ("detail", "完整放大图")]:
                for style, caption in [("marked", "标记"), ("raw", "无标记")]:
                    ref = req["source_assets"][frame][size + "_" + style]
                    url = html.escape(os.path.relpath(root / ref["path"], output))
                    items.append(
                        f"<figure><figcaption>{frame.upper()} {label} · {caption}</figcaption>"
                        f'<a href="{url}" target="_blank"><img src="{url}" '
                        f'alt="{frame} {size} {style}" loading="lazy"></a></figure>'
                    )
            evidence.append(
                f"<details><summary>{frame.upper()}原生宽图与放大图</summary>"
                + "".join(items)
                + "</details>"
            )
        current_page = html.escape(
            os.path.relpath(root / Path(domain["package"]["path"]).parent / "index.html", output)
        )
        sections.append(
            dict(
                id=domain["focus"]["id"],
                domain=key,
                before=drawing(previous),
                after=drawing(model),
                metrics=metrics,
                question=domain["focus"]["question"],
                label=domain["focus"]["label"],
                zoom_viewbox=domain["focus"]["zoom_viewbox"],
                evidence="".join(evidence),
                package_page=current_page,
            )
        )
    payload = json.dumps(
        dict(sections=sections, work=work, summary=summary), ensure_ascii=False
    ).replace("</", "<\\/")
    return Template(Path(__file__).with_name("conductive_snapshot.html").read_text()).substitute(
        payload=payload
    )


def run(root, request_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or not output.is_relative_to(root):
        raise ValueError("Output must be a new directory inside the project")
    request = json.loads(Path(request_path).read_text())
    work, summary, render, files = assemble(root, request)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".work-snapshot-", dir=output.parent) as temporary:
        stage = Path(temporary) / "package"
        stage.mkdir()
        for name, value in [("snapshot", work), ("report", summary), ("request", request)]:
            (stage / (name + ".json")).write_text(
                json.dumps(value, ensure_ascii=False, indent=2) + "\n"
            )
        (stage / "index.html").write_text(page(root, output, work, summary, render))
        manifest = dict(inputs=files, artifacts={p.name: digest(p) for p in stage.iterdir()})
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        stage.rename(output)
    return work, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        _, report = run(Path.cwd(), args.request, args.output)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f"Work snapshot rejected: {error}\n")
    print(json.dumps({k: v for k, v in report.items() if k != "domains"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
