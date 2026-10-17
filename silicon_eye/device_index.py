"""Export stable device IDs across native layer windows, without inferring metal paths.

Enabled by optional device_view in the existing review-package request.
Uses case inspection windows and accepted macro registration only; no model calls.
"""
from __future__ import annotations

import csv
import hashlib
import json
from html import escape

import cv2
import numpy as np
from PIL import Image
from pydantic import Field, model_validator

from .schemas.block_case import Record, indexed, inside


class LayerWindow(Record):
    id: str
    frame_id: str
    label: str = Field(min_length=1)
    xywh: tuple[int, int, int, int]
    projection_profile_id: str | None = None


class DeviceViewRequest(Record):
    windows: list[LayerWindow] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_windows(self):
        indexed(self.windows)
        return self


def corners(box):
    x, y, w, h = box
    return np.array([[x, y], [x+w, y], [x+w, y+h], [x, y+h]], dtype=float)


def contained(points, box):
    x, y, w, h = box
    return bool(((points >= [x, y]) & (points < [x+w, y+h])).all())


def project(points, registration, reference_frame, target_frame, target_size):
    if (reference_frame != registration["reference_frame"]
            or target_frame != registration["target_frame"]):
        raise ValueError("Projection requires the declared reference-to-target frame pair")
    profile = registration["profile"]
    covered = False
    for polygon in profile["reviewed_reference_frame_polygons_xy"]:
        contour = np.array(polygon, dtype="float32")
        # Convex scope plus all corners inside proves the entire rectangular window is inside.
        if cv2.isContourConvex(contour) and all(
            cv2.pointPolygonTest(contour, (float(x), float(y)), False) >= 0 for x, y in points
        ):
            covered = True
            break
    if not covered:
        return None, "outside_reviewed_macro_scope"
    inverse = np.linalg.inv(np.array(profile["matrix"], dtype=float))
    homogeneous = np.c_[points, np.ones(len(points))] @ inverse.T
    denominator = homogeneous[:, 2]
    if min(denominator) * max(denominator) <= 0:
        return None, "registration_horizon"
    mapped = homogeneous[:, :2] / denominator[:, None]
    if not np.isfinite(mapped).all() or not contained(mapped, [0, 0, *target_size]):
        return None, "outside_target_photo"
    return mapped, None


def build_device_index(case, block, registrations, request):
    frames = {f.id: f for f in case.frames}
    devices = sorted(e.id for e in case.entities if e.kind == "device")
    named = [r for r in registrations if r["profile"].get("profile_id")]
    profiles = {r["profile"]["profile_id"]: r for r in named}
    if len(profiles) != len(named):
        raise ValueError("Ambiguous registration profile IDs")
    windows = []
    for window in request.windows:
        if window.frame_id not in frames:
            raise ValueError("Device view refers to unknown frame")
        frame = frames[window.frame_id]
        inside(window.xywh, frame.size_wh)
        registration = None
        if window.projection_profile_id:
            if window.projection_profile_id not in profiles:
                raise ValueError("Device view requires a verified registration profile")
            registration = profiles[window.projection_profile_id]
            if registration["target_frame"] != frame.id:
                raise ValueError("Projection target differs from display frame")
        rows = []
        for device in devices:
            direct = [g for g in case.geometry_observations
                      if g.entity_id == device and g.frame_id == frame.id]
            if len(direct) > 1:
                raise ValueError("Multiple device inspection windows need explicit reconciliation")
            geometry = direct
            projected = False
            if not geometry and registration:
                geometry = [g for g in case.geometry_observations if g.entity_id == device
                            and g.frame_id == registration["reference_frame"]]
                if len(geometry) > 1:
                    raise ValueError("Ambiguous projection source inspection windows")
                projected = bool(geometry)
            row = dict(device_id=device, status="unknown", reason="no_device_location_evidence",
                       polygon_native_xy=None, source_geometry=None, projection_profile_id=None)
            if geometry:
                g = geometry[0]
                points = corners(g.xywh)
                row["source_geometry"] = g.model_dump(mode="json")
                if projected:
                    points, reason = project(points, registration, g.frame_id, frame.id,
                                             frame.size_wh)
                    row["projection_profile_id"] = window.projection_profile_id
                    row["reason"] = reason
                if points is not None and contained(points, window.xywh):
                    row.update(status="macro_projection" if projected else "native_candidate",
                               reason=None, polygon_native_xy=points.tolist())
                elif points is not None:
                    row["reason"] = "outside_display_window"
            rows.append(row)
        windows.append(dict(**window.model_dump(mode="json"), unit="px",
                            photo=case.sources[frame.source_ref].model_dump(), devices=rows))
    return dict(
        schema_version=1, document_kind="cross_layer_device_index", case_id=case.case_id,
        block_state_id=block["state_id"], windows=windows,
        devices=[dict(id=id, object_kind="existing_MOS_review_slot_not_aggregate_device_count",
                      existence=next(d["existence"] for d in block["devices"] if d["id"] == id),
                      terminals=[t for t in block["terminals"] if t["device_id"] == id])
                 for id in devices],
        physical_boundary_accepted=False, contact_landing_accepted=False,
        metal_paths_inferred=False, runtime_ai_used=False,
    )


def color(id):
    hue = int(hashlib.sha256(id.encode()).hexdigest()[:8], 16) % 360
    return f"hsl({hue} 90% 65%)"


LABELS = {"native_candidate": "原生检查窗口（候选）", "macro_projection": "宏观投影位置",
          "unknown": "未定位"}
REASONS = {"no_device_location_evidence": "缺少该层器件定位证据",
           "outside_reviewed_macro_scope": "超出已审核宏观配准范围",
           "registration_horizon": "投影跨越变换奇点",
           "outside_target_photo": "投影超出原图",
           "outside_display_window": "定位超出当前显示窗口"}


def render_device_index(state, inputs, out):
    from .review_package import save_image

    index = state["device_index"]
    document = dict(index, bundle_id=state["bundle_id"])
    (out / "device-index.json").write_text(json.dumps(document, ensure_ascii=False, indent=2)+'\n')
    html = [
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>器件跨层编号视图</title><style>',
        'body{font:16px/1.6 system-ui;max-width:1400px;margin:24px auto;padding:0 18px;'
        'background:#f3f5f8;color:#17202b}button{font:inherit;padding:8px 14px;margin:4px;'
        'border:2px solid #8995a3;border-radius:8px;background:white;cursor:pointer}'
        'button[aria-pressed=true]{background:#123557;color:white;border-color:#123557}'
        '.toolbar{position:sticky;top:0;background:#f3f5f8;z-index:2;padding:8px 0}'
        '.layers{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,360px),1fr));'
        'gap:16px}section{padding:16px;background:white;border-radius:10px;margin:16px 0;'
        'min-width:0;scroll-margin-top:180px}.photo{position:relative;background:#111}'
        '.photo img{display:block;width:100%}'
        '.photo svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}'
        'svg .mark{transition:opacity .15s}svg text{font:14px monospace;font-weight:bold;'
        'paint-order:stroke;stroke:#111;stroke-width:3px;stroke-linejoin:round}'
        'table{border-collapse:collapse;width:100%;margin-top:12px}td,th{border:1px solid #ccd3dc;'
        'padding:7px;text-align:left;overflow-wrap:anywhere}.tablewrap{overflow-x:auto}'
        'tr.selected{background:#e3eef9}code{overflow-wrap:anywhere}a{color:#1460a0}'
        '.muted{color:#566575}.legend{font-size:14px}img.schematic{max-width:100%}</style>',
        '<h1>器件跨层编号视图</h1>',
        f'<p>案例：{escape(index["case_id"])}。沿用原有器件／栅指ID；选中编号可对照各层位置。</p>',
        '<p>实线框：原生检查窗口候选；虚线框：经已批准宏观配准投影的查找位置。'
        '两者均不是器件边界或金属端口。未定位层保留原图上下文，不猜测框的位置。</p>',
        '<p><a href="report.md">统一复核包</a> · <a href="circuit/report.md">连接与四端表</a>'
        ' · <a href="device-index.json">编号数据</a>'
        ' · <a href="device-index.csv">下载索引CSV</a></p>',
        '<div class="toolbar" role="group" aria-label="选择器件">',
        '<button type="button" data-select="" aria-pressed="true">全部器件</button>',
    ]
    for device in index["devices"]:
        id = escape(device["id"], quote=True)
        html += [f'<button type="button" data-select="{id}" aria-pressed="false">{id}</button>']
    html += ['<p id="selection" aria-live="polite">当前：全部器件</p><nav>查看：']
    for number, window in enumerate(index["windows"], 1):
        html += [f'<a href="#layer-{number:03}">{escape(window["label"])}</a> · ']
    html += ['<a href="#terminal-table">四端连接</a></nav></div><div class="layers">']
    csv_rows = []
    for number, window in enumerate(index["windows"], 1):
        x, y, w, h = window["xywh"]
        with Image.open(inputs.root / window["photo"]["path"]) as image:
            crop = np.array(image.convert("RGB").crop((x, y, x+w, y+h)))
        name = f"device-layer-{number:03}-raw.png"
        save_image(out / name, crop, state["bundle_id"])
        html += [f'<section id="layer-{number:03}"><h2>{escape(window["label"])}</h2>'
                 '<div class="photo">',
                 f'<img src="{name}" alt="{escape(window["label"], quote=True)}原生照片">',
                 f'<svg viewBox="0 0 {w} {h}" aria-label="器件检查窗口">']
        for row in window["devices"]:
            id = escape(row["device_id"], quote=True)
            if row["polygon_native_xy"] is not None:
                pts = np.array(row["polygon_native_xy"]) - [x, y]
                coords = " ".join(f"{px:.4f},{py:.4f}" for px, py in pts)
                dash = 'stroke-dasharray="5 4"' if row["status"] == "macro_projection" else ""
                tx = max(2, min(float(pts[:, 0].min()), w - len(row["device_id"])*9 - 4))
                ty = max(16, float(pts[:, 1].min()) - 5)
                html += [f'<g class="mark" data-device="{id}"><polygon points="{coords}" '
                         f'fill="none" stroke="{color(row["device_id"])}" stroke-width="2" '
                         f'{dash}/><text x="{tx:.4f}" y="{ty:.4f}" '
                         f'fill="{color(row["device_id"])}">{id}</text></g>']
            csv_rows.append(dict(device_id=row["device_id"], layer=window["label"],
                                 frame_id=window["frame_id"], status=row["status"],
                                 reason=row["reason"] or "", native_polygon_xy=json.dumps(
                                     row["polygon_native_xy"]), photo=window["photo"]["path"],
                                 projection_profile_id=row["projection_profile_id"] or ""))
        html += ['</svg></div>', f'<p><a href="{name}">打开无标记原像素裁剪</a></p>',
                 f'<p class="muted">{escape(window["frame_id"])}；xywh(px)={window["xywh"]}</p>',
                 '<div class="tablewrap"><table><tr><th>编号</th><th>本层定位</th></tr>']
        for row in window["devices"]:
            id = escape(row["device_id"], quote=True)
            status = LABELS[row["status"]]
            if row["reason"]:
                status += "：" + REASONS[row["reason"]]
            html += [f'<tr data-device="{id}"><td>{id}</td><td>{status}</td></tr>']
        html += ['</table></div></section>']
    html += ['</div><section id="terminal-table"><h2>同一编号的四端连接</h2>',
             '<p>A/B为原有几何端子约定，尚未指定S/D；未知不表示隔离。'
             '本页不归并栅指、不生成物理W/L或金属路径。</p>',
             '<div class="tablewrap"><table><tr><th>编号</th><th>G</th><th>A</th>'
             '<th>B</th><th>Bulk</th></tr>']
    for device in index["devices"]:
        terminals = {t["role"]: t for t in device["terminals"]}
        cells = []
        for role in ["G", "A", "B", "Bulk"]:
            terminal = terminals[role]
            cells.append(escape(terminal["confirmed_net_id"] or "未知") +
                         ("；导体关联：" + escape(", ".join(terminal["conductor_ids"]))
                          if terminal["conductor_ids"] else ""))
        id = escape(device["id"], quote=True)
        html += [f'<tr data-device="{id}"><td>{id}</td>' +
                 ''.join(f'<td>{cell}</td>' for cell in cells) + '</tr>']
    html += ['</table></div><p>同一C编号表示现有确认同网；不同编号不证明隔离。</p>',
             '<img class="schematic" src="circuit/local-schematic.png" alt="原有确认电路状态">',
             f'<details><summary>状态与来源</summary><p>bundle_id：'
             f'<code>{state["bundle_id"]}</code></p><p>block_state_id：'
             f'<code>{index["block_state_id"]}</code></p></details></section>',
             '<script>document.querySelectorAll("button[data-select]").forEach(button=>{'
             'button.addEventListener("click",()=>{const id=button.dataset.select;'
             'document.querySelectorAll("button[data-select]").forEach(b=>'
             'b.setAttribute("aria-pressed",String(b.dataset.select===id)));'
             'document.querySelectorAll("[data-device]").forEach(e=>{'
             'const selected=!id||e.dataset.device===id;'
             'if(e.classList.contains("mark"))e.style.opacity=selected?"1":"0.15";'
             'if(e.tagName==="TR")e.classList.toggle("selected",!!id&&selected);});'
             'document.getElementById("selection").textContent="当前："+(id||"全部器件");});});'
             '</script></html>']
    (out / "device-index.html").write_text('\n'.join(html)+'\n')
    with (out / "device-index.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)
    return ["", "[打开器件跨层编号视图](device-index.html)", "",
            "器件ID沿用case；实线为原生检查窗口，虚线为宏观投影；未定位不补框。"]
