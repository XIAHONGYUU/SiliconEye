"""Deliver a scoped POLY/CT reconstruction review without re-extracting photographs.

Run: python -m silicon_eye.layer_review --request request.json --output NEW_DIRECTORY
Requires the project environment and locked joint snapshot. No recognition or adoption.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
import tempfile
from pathlib import Path
from typing import Literal

from PIL import Image
from pydantic import Field, FiniteFloat, model_validator
from shapely.geometry import Polygon, box

from .aa_completion import object_polygon
from .ct_transfer import apply_reviewed_record_changes
from .geometry_reconstruction import digest
from .joint_layers import audit_joint, load_snapshot, reject_retired_ids, write_snapshot
from .review_package import Inputs
from .schemas.agent_observation import AgentObservations, PhotoTask
from .schemas.block_case import Record, Source


class Change(Record):
    layer: Literal["AA", "POLY", "CT"]
    id: str
    before: dict | None
    after: dict | None
    reason: str = Field(min_length=1)
    evidence: list[Source] = Field(min_length=1)


class Window(Record):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    layout_bounds: tuple[FiniteFloat, FiniteFloat, FiniteFloat, FiniteFloat]
    source_windows: dict[str, tuple[int, int, int, int]] = Field(default_factory=dict)


class ReviewRequest(Record):
    schema_version: Literal[1]
    document_kind: Literal["layer_reconstruction_review"]
    id: str
    target_layer: Literal["POLY", "CT", "M1", "V1", "M2", "V2", "M3"]
    mode: Literal["inspect", "revise"]
    snapshot: Source
    authorized_ids: dict[Literal["AA", "POLY", "CT"], list[str]] = Field(default_factory=dict)
    changes: list[Change] = Field(default_factory=list)
    windows: list[Window] = Field(min_length=1)
    observations: Source | None = None

    @model_validator(mode="after")
    def scope(self):
        if self.target_layer in {"M1", "V1", "M2", "V2", "M3"} and self.mode != "inspect":
            raise ValueError("Conductive layer review currently supports inspect mode only")
        if self.mode == "inspect" and (self.changes or self.authorized_ids):
            raise ValueError("Inspect mode cannot change records")
        if self.mode == "revise" and not self.changes:
            raise ValueError("Revise mode needs an explicit transaction")
        if len({w.id for w in self.windows}) != len(self.windows):
            raise ValueError("Duplicate review window")
        for layer, ids in self.authorized_ids.items():
            if len(ids) != len(set(ids)):
                raise ValueError("Duplicate authorized ID: " + layer)
        return self


def records(snapshot, layer):
    if layer in snapshot.get("conductors", {}).get("objects_by_layer", {}):
        return snapshot["conductors"]["objects_by_layer"][layer]
    if layer == "CT":
        return snapshot["contacts"]
    return snapshot["materials"]["AA_objects" if layer == "AA" else "objects"]


def prepare(root, request):
    """One atomic cross-layer transaction, with exact parent records and fixed context."""
    inputs = Inputs(root)
    inputs.read(request.snapshot)
    parent = load_snapshot(root, Path(root) / request.snapshot.path)
    if request.target_layer in {"M1", "V1", "M2", "V2", "M3"} and "conductors" not in parent:
        raise ValueError("Conductive review requires an attached registry")
    for ref in list(parent["manifest"]["inputs"].values()) + list(
        parent["manifest"]["source_photos"].values()
    ):
        inputs.read(ref)
    if parent["manifest"].get("conductive_layers"):
        inputs.read(parent["manifest"]["conductive_layers"])
    for change in request.changes:
        for ref in change.evidence:
            inputs.read(ref)
    if request.observations:
        batch = AgentObservations.model_validate(inputs.document(request.observations))
        task = PhotoTask.model_validate(inputs.document(batch.input_packet))
        for ref in task.sources.values():
            inputs.read(ref)
            if ref.model_dump() not in parent["manifest"]["source_photos"].values():
                raise ValueError("Observation packet is not bound to snapshot photographs")
        for frame in task.frames:
            with Image.open(Path(root) / task.sources[frame.source_ref].path) as im:
                if im.size != frame.size_wh:
                    raise ValueError("Observation frame size differs from photograph")
        batch.check_task(task)
    width, height = parent["manifest"]["canvas_wh"]
    for win in request.windows:
        left, top, right, bottom = win.layout_bounds
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise ValueError("Review window outside design canvas")
        for frame, bounds in win.source_windows.items():
            if frame not in parent["manifest"]["source_photos"]:
                raise ValueError("Unknown source frame")
            with Image.open(Path(root) / parent["manifest"]["source_photos"][frame]["path"]) as im:
                lft, up, rgt, down = bounds
                if not (0 <= lft < rgt <= im.width and 0 <= up < down <= im.height):
                    raise ValueError("Review window outside native photo")
    proposed = copy.deepcopy(parent)
    for layer in ("AA", "POLY", "CT"):
        changes = [c.model_dump() for c in request.changes if c.layer == layer]
        revised = apply_reviewed_record_changes(
            records(parent, layer),
            changes,
            request.authorized_ids.get(layer, []),
            preserve_fields=("acceptance", "human_review", "review_status"),
        )
        if layer == "CT":
            proposed["contacts"] = revised
        else:
            proposed["materials"]["AA_objects" if layer == "AA" else "objects"] = revised
    # No request field can replace budgets, reviews, restrictions, aliases or unknowns.
    retired = set(parent["manifest"].get("retired_contact_ids", []))
    violations = sorted(retired & {c["id"] for c in proposed["contacts"]})
    reject_retired_ids(parent["manifest"], proposed["materials"])
    report = audit_joint(
        proposed["contacts"],
        proposed["materials"],
        parent["manifest"]["budget"],
        parent["contacts"],
    )
    if "conductors" in parent:
        from .conductive_layers import audit_summary

        report["conductive_layers"] = audit_summary(parent["conductors"])
    if violations:
        report.update(status="FAIL", retired_contact_ids_resurrected=violations)
    return parent, proposed, report, inputs


def model_svg(snapshot, bounds):
    left, top, right, bottom = bounds
    viewport = box(*bounds)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{left} {top} '
        f'{right - left} {bottom - top}">'
    ]
    for layer, color in [("AA", "#5ab987"), ("POLY", "#e9ac58"), ("CT", "#d9f6ff")]:
        parts.append(f'<g data-layer="{layer}" fill="{color}" stroke="{color}">')
        for obj in records(snapshot, layer):
            p = object_polygon(obj) if layer == "AA" else Polygon(obj["layout_outline"])
            if not p.intersects(viewport):
                continue
            path = " ".join(
                "M" + " L".join(f"{x},{y}" for x, y in ring.coords) + " Z"
                for ring in [p.exterior, *p.interiors]
            )
            parts.append(
                f'<path d="{path}" fill-opacity=".6" fill-rule="evenodd" '
                f'stroke-width=".5"><title>{html.escape(obj["id"])}</title></path>'
            )
        parts.append("</g>")
    parts.append(
        '<g data-layer="unknown" fill="none" stroke="#ff6be6" '
        'stroke-width="2" stroke-dasharray="5 3">'
    )
    for unknown in snapshot["values"]["unknown"].get("unknown_scopes", []):
        if "layout_bounds" in unknown:
            x1, y1, x2, y2 = unknown["layout_bounds"]
            parts.append(
                f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}">'
                f"<title>{html.escape(unknown['id'])}</title></rect>"
            )
    result = "".join(parts) + "</g>"
    if "conductors" in snapshot:
        from .conductive_layers import svg_layers

        result += svg_layers(snapshot["conductors"], bounds)
    return result + "</svg>"


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def deliver(root, request_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if not output.is_relative_to(root) or output.exists():
        raise ValueError("Output must be a new directory inside the project")
    raw = Path(request_path).read_bytes()
    request = ReviewRequest.model_validate_json(raw)
    parent, proposed, report, inputs = prepare(root, request)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".layer-review-", dir=output.parent) as temp:
        stage = Path(temp) / "delivery"
        stage.mkdir()
        (stage / "request.json").write_bytes(raw)
        write_json(stage / "delta.json", [c.model_dump() for c in request.changes])
        write_json(stage / "joint-report.json", report)
        write_json(
            stage / "continuation-context.json",
            dict(
                snapshot_id=parent["manifest"]["id"],
                coordinate_frames=dict(
                    design_px=parent["manifest"]["canvas_wh"],
                    native_px=parent["manifest"]["source_wh"],
                ),
                budget=parent["manifest"]["budget"],
                inherited_documents={
                    key: value
                    for key, value in parent["values"].items()
                    if key not in {"materials", "contacts", "AA_context"}
                },
                adoption_status="not_adopted_no_new_human_approval",
                automatic_network_export_allowed=False,
            ),
        )
        candidate = None
        if request.mode == "revise" and report["status"] != "FAIL":
            path = write_snapshot(root, proposed, stage)
            manifest = json.loads(path.read_text())
            for key in ("materials", "contacts"):
                name = Path(manifest["inputs"][key]["path"]).name
                manifest["inputs"][key]["path"] = str((output / name).relative_to(root))
            write_json(path, manifest)
            candidate = "joint-snapshot.json"
        cards = []
        for win in request.windows:
            models = []
            for label, snap in [("before", parent), ("proposed", proposed)]:
                name = f"{win.id}-{label}.svg"
                (stage / name).write_text(model_svg(snap, win.layout_bounds))
                models.append(f"<div><h3>{label}</h3>{(stage / name).read_text()}</div>")
            sources = []
            for frame, bounds in win.source_windows.items():
                name = f"{win.id}-{frame}.png"
                with Image.open(root / parent["manifest"]["source_photos"][frame]["path"]) as im:
                    im.crop(bounds).save(stage / name)
                sources.append(
                    f'<figure data-source="{frame}"><figcaption>{frame}: '
                    f'{bounds}</figcaption><img src="{name}"></figure>'
                )
            cards.append(
                f"<section><h2>{win.id}</h2><p>设计坐标 {win.layout_bounds}</p>"
                f'<div class="models">{"".join(models)}</div>'
                f'<div class="photos">{"".join(sources)}</div></section>'
            )
        page = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>层重建复核包</title><style>body{background:#14202d;color:#eee;font:16px sans-serif;
margin:24px}a{color:#82ccff}.models,.photos{display:flex;gap:16px;flex-wrap:wrap}
.models>div,figure{margin:0;flex:1;min-width:300px}svg,img{width:100%;background:#102030}
section{margin-top:28px}button,label{margin:8px}</style><h1>层重建复核包</h1>"""
        page += f"<p>模式 {request.mode} · 联合门 {report['status']} · 尚未采用或新增批准</p>"
        page += "<p>源图窗口与设计视图分别显示，不作未验证的叠图投影。"
        page += "紫色虚线为未知范围。FAIL时proposed仅为拒绝诊断，没有可接续快照。</p>"
        for layer in ("AA", "POLY", "CT", "unknown", *parent.get(
            "conductors", {}
        ).get("layer_stack", [])):
            page += f'<label><input type="checkbox" checked data-toggle="{layer}">{layer}</label>'
        for frame in parent["manifest"]["source_photos"]:
            page += (
                f'<label><input type="checkbox" checked data-photo="{frame}">{frame}原图</label>'
            )
        page += '<p><a href="continuation-context.json">裁决与未知</a> · '
        page += '<a href="delta.json">变化记录</a> · <a href="joint-report.json">质量门</a></p>'
        page += (
            "".join(cards)
            + """<script>
document.querySelectorAll('[data-toggle]').forEach(e=>e.onchange=()=>{
 document.querySelectorAll('[data-layer="'+e.dataset.toggle+'"]').forEach(g=>
  g.style.display=e.checked?'':'none');});
document.querySelectorAll('[data-photo]').forEach(e=>e.onchange=()=>{
 document.querySelectorAll('[data-source="'+e.dataset.photo+'"]').forEach(g=>
  g.style.display=e.checked?'':'none');});</script></html>"""
        )
        (stage / "index.html").write_text(page)
        artifacts = {str(p.relative_to(stage)): digest(p) for p in stage.iterdir()}
        code = {
            "silicon_eye/" + name: digest(Path(__file__).with_name(name))
            for name in (
                "layer_review.py",
                "joint_layers.py",
                "ct_transfer.py",
                "poly_closeout.py",
                "ct_joint_reconstruction.py",
                "aa_completion.py",
            )
        }
        if "conductors" in parent:
            code["silicon_eye/conductive_layers.py"] = digest(
                Path(__file__).with_name("conductive_layers.py")
            )
        write_json(
            stage / "manifest.json",
            dict(
                schema_version=1,
                id=request.id,
                status=report["status"],
                mode=request.mode,
                parent_snapshot=request.snapshot.model_dump(),
                candidate_snapshot=candidate,
                next_snapshot=candidate
                or (
                    request.snapshot.model_dump()
                    if request.mode == "inspect" and report["status"] != "FAIL"
                    else None
                ),
                verified_inputs=inputs.files,
                code=code,
                artifacts=artifacts,
                model_counts={
                    layer: len(records(proposed, layer))
                    for layer in ("AA", "POLY", "CT", *proposed.get(
                        "conductors", {}
                    ).get("layer_stack", []))
                },
                automatic_network_export_allowed=False,
            ),
        )
        stage.rename(output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        report = deliver(args.root, args.request, args.output)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"Layer review failed: {error}\n")
    print(json.dumps(dict(status=report["status"], automatic_network_export_allowed=False)))
    if report["status"] == "FAIL":
        parser.exit(2)


if __name__ == "__main__":
    main()
