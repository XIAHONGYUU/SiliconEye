"""Render explicitly proposed terminal-to-metal segments; never infer connectivity.

Used by review-package terminal_highlights. Model supplies native candidate geometry;
scripts validate evidence and rasterize copies. No automatic tracing or case mutation.
"""
from __future__ import annotations

import json
from html import escape
from typing import Literal

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pydantic import Field, FiniteFloat

from .device_index import corners, project
from .schemas.block_case import Record, Source, inside


class ContactBridge(Record):
    gate_frame_id: str
    source_context_xywh: tuple[int, int, int, int]
    ct_window_xywh: tuple[int, int, int, int]
    ct_center_native_xy: tuple[FiniteFloat, FiniteFloat]
    registration_profile_id: str
    target_search_radius_px: FiniteFloat = Field(gt=0, le=40)
    status: Literal["candidate"]
    rationale: str = Field(min_length=1)


class TerminalHighlight(Record):
    schema_version: Literal[1]
    document_kind: Literal["terminal_highlight_candidate"]
    case_id: str
    terminal_id: str
    frame_id: str
    native_source: Source
    window_xywh: tuple[int, int, int, int]
    segment_id: str
    polygon_native_xy: list[tuple[FiniteFloat, FiniteFloat]] = Field(min_length=3)
    anchor_native_xy: tuple[FiniteFloat, FiniteFloat]
    status: Literal["candidate"]
    producer: Literal["reasoning_model", "vision_model"]
    rationale: str = Field(min_length=1)
    evidence: list[Source] = Field(min_length=1)
    continuation: Literal["unknown_stop_at_declared_segment"]
    contact_landing: Literal["unknown"]
    contact_bridge: ContactBridge | None = None


def prepare_highlight(inputs, entry, case, block, registrations=()):
    spec = TerminalHighlight.model_validate(inputs.document(entry))
    if spec.case_id != case.case_id:
        raise ValueError("Terminal highlight belongs to another case")
    terminals = {t["id"]: t for t in block["terminals"]}
    if spec.terminal_id not in terminals:
        raise ValueError("Unknown highlight terminal")
    frames = {f.id: f for f in case.frames}
    if spec.frame_id not in frames:
        raise ValueError("Unknown highlight frame")
    frame = frames[spec.frame_id]
    if case.sources[frame.source_ref] != spec.native_source:
        raise ValueError("Highlight source/frame mismatch")
    inputs.read(spec.native_source)
    for source in spec.evidence:
        inputs.read(source)
    inside(spec.window_xywh, frame.size_wh)
    x, y, w, h = spec.window_xywh
    points = np.array(spec.polygon_native_xy, dtype="float32")
    anchor = spec.anchor_native_xy
    if (not cv2.isContourConvex(points)
            or cv2.contourArea(points) <= 0
            or not ((points >= [x, y]) & (points < [x+w, y+h])).all()
            or not (x <= anchor[0] < x+w and y <= anchor[1] < y+h)
            or cv2.pointPolygonTest(points, anchor, False) < 0):
        raise ValueError("Candidate segment/anchor outside window or invalid convex geometry")
    result = dict(spec.model_dump(mode="json"),
                confirmed_net_id=terminals[spec.terminal_id]["confirmed_net_id"],
                terminal_to_segment_status="candidate_not_human_confirmed",
                electrical_state_changed=False, exact_boundary_accepted=False,
                automatic_metal_tracing=False)
    if spec.contact_bridge is not None:
        bridge = spec.contact_bridge
        if terminals[spec.terminal_id]["role"] != "G":
            raise ValueError("CT bridge v1 requires an explicit gate terminal")
        if bridge.gate_frame_id not in frames:
            raise ValueError("Unknown gate/CT source frame")
        source_frame = frames[bridge.gate_frame_id]
        inside(bridge.source_context_xywh, source_frame.size_wh)
        inside(bridge.ct_window_xywh, source_frame.size_wh)
        cx, cy, cw, ch = bridge.ct_window_xywh
        tx, ty, tw, th = bridge.source_context_xywh
        if not (tx <= cx and ty <= cy and cx+cw <= tx+tw and cy+ch <= ty+th
                and cx <= bridge.ct_center_native_xy[0] < cx+cw
                and cy <= bridge.ct_center_native_xy[1] < cy+ch):
            raise ValueError("CT center/window outside source context")
        geometry = [g for g in case.geometry_observations
                    if g.entity_id == terminals[spec.terminal_id]["device_id"]
                    and g.frame_id == bridge.gate_frame_id]
        if len(geometry) != 1:
            raise ValueError("CT bridge needs one explicit gate inspection window")
        profiles = [r for r in registrations
                    if r["profile"].get("profile_id") == bridge.registration_profile_id]
        if len(profiles) != 1:
            raise ValueError("CT bridge requires one reviewed registration")
        registration = profiles[0]
        mapped, reason = project(corners(bridge.ct_window_xywh), registration,
                                 bridge.gate_frame_id, spec.frame_id, frame.size_wh)
        if mapped is None:
            raise ValueError("CT projection unavailable: " + reason)
        if not ((mapped >= [x, y]) & (mapped < [x+w, y+h])).all():
            raise ValueError("Projected CT window outside highlight context")
        inverse = np.linalg.inv(np.array(registration["profile"]["matrix"], dtype=float))
        point = inverse @ np.r_[bridge.ct_center_native_xy, 1]
        projected = point[:2] / point[2]
        offset = float(np.linalg.norm(projected - spec.anchor_native_xy))
        if offset > bridge.target_search_radius_px:
            raise ValueError("Metal anchor outside declared CT search radius")
        gx, gy, gw, gh = geometry[0].xywh
        pcx, pcy = bridge.ct_center_native_xy
        if not (gx-20 <= pcx <= gx+gw+20 and gy-20 <= pcy <= gy+gh+20):
            raise ValueError("Candidate CT too far from the declared gate window")
        source = case.sources[source_frame.source_ref]
        inputs.read(source)
        result["contact_bridge"].update(
            native_source=source.model_dump(), gate_geometry=geometry[0].model_dump(mode="json"),
            projected_ct_native_xy=projected.tolist(), projected_ct_window_xy=mapped.tolist(),
            anchor_offset_px=offset, search_radius_is_accuracy_bound=False,
            ct_on_gate_status="candidate", ct_to_metal_status="candidate",
        )
    return result


def render_contact_bridge(record, marked, inputs):
    bridge = record["contact_bridge"]
    sx, sy, sw, sh = bridge["source_context_xywh"]
    with Image.open(inputs.root / bridge["native_source"]["path"]) as image:
        source = image.convert("RGB").crop((sx, sy, sx+sw, sy+sh))
    scale = 3
    source = source.resize((sw*scale, sh*scale), Image.Resampling.NEAREST)
    drawing = ImageDraw.Draw(source)
    gx, gy, gw, gh = bridge["gate_geometry"]["xywh"]
    drawing.rectangle(((gx-sx)*scale, (gy-sy)*scale,
                       (gx+gw-sx)*scale, (gy+gh-sy)*scale), outline="#ff50dc", width=2)
    cx, cy, cw, ch = bridge["ct_window_xywh"]
    drawing.rectangle(((cx-sx)*scale, (cy-sy)*scale,
                       (cx+cw-sx)*scale, (cy+ch-sy)*scale), outline="#00eaff", width=3)
    mx, my, mw, mh = record["window_xywh"]
    target = Image.fromarray(marked).resize((mw*2, mh*2), Image.Resampling.NEAREST)
    target_draw = ImageDraw.Draw(target)
    px, py = bridge["projected_ct_native_xy"]
    radius = bridge["target_search_radius_px"]
    target_draw.ellipse(((px-radius-mx)*2, (py-radius-my)*2,
                         (px+radius-mx)*2, (py+radius-my)*2), outline="#00eaff", width=2)
    target_draw.line(((px-mx)*2-8, (py-my)*2, (px-mx)*2+8, (py-my)*2),
                     fill="#00eaff", width=2)
    target_draw.line(((px-mx)*2, (py-my)*2-8, (px-mx)*2, (py-my)*2+8),
                     fill="#00eaff", width=2)
    width = max(sw*scale+40, mw*2+40, 800)
    height = sh*scale + mh*2 + 230
    sheet = Image.new("RGB", (width, height), "#f3f5f8")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=20)
    small = ImageFont.load_default(size=16)
    draw.text((20, 12), record["terminal_id"] + ": gate -> candidate CT -> M1", font=font,
              fill="#17202b")
    draw.text((20, 48), "1. Poly: magenta gate window; cyan CT cluster at lower gate extension",
              font=small, fill="#46566a")
    sheet.paste(source, (20, 80))
    top = sh*scale+104
    draw.text((20, top),
              "2. M1: cyan = projected CT/search area; yellow = proposed connected segment",
              font=small, fill="#46566a")
    sheet.paste(target, (20, top+30))
    draw.text((20, height-64),
              f"CT projection to anchor offset: {bridge['anchor_offset_px']:.1f} native px; "
              "search radius is not certified accuracy.", font=small, fill="#46566a")
    draw.text((20, height-34),
              "Both CT-on-gate and CT-to-M1 remain candidates. No netlist changes.",
              font=small, fill="#46566a")
    return np.array(sheet)


def render_highlights(state, inputs, out):
    from .review_package import save_image

    links = []
    for number, record in enumerate(state["terminal_highlights"], 1):
        x, y, w, h = record["window_xywh"]
        with Image.open(inputs.root / record["native_source"]["path"]) as image:
            raw = np.array(image.convert("RGB").crop((x, y, x+w, y+h)))
        points = np.array(record["polygon_native_xy"]) - [x, y]
        mask = np.zeros((h, w), dtype="uint8")
        cv2.fillPoly(mask, [np.rint(points).astype("int32")], 255)
        marked = raw.copy()
        selected = mask > 0
        marked[selected] = (raw[selected].astype(float)*.50 + np.array([255, 210, 0])*.50
                            ).astype("uint8")
        cv2.polylines(marked, [np.rint(points).astype("int32")], True, (255, 210, 0), 1)
        ax, ay = np.rint(np.array(record["anchor_native_xy"]) - [x, y]).astype(int)
        cv2.drawMarker(marked, (int(ax), int(ay)), (255, 80, 220), cv2.MARKER_CROSS, 11, 1)
        prefix = f"terminal-highlight-{number:03}"
        for suffix, array in [("raw", raw), ("overlay", marked), ("candidate-mask", mask)]:
            save_image(out / f"{prefix}-{suffix}.png", array, state["bundle_id"])
        # Raster demo works without localhost or browser access. Labels stay outside raw crops.
        font = ImageFont.load_default(size=20)
        caption = ImageFont.load_default(size=16)
        scale = 2
        sheet = Image.new("RGB", (w*scale+40, h*scale*2+206), "#f3f5f8")
        draw = ImageDraw.Draw(sheet)
        draw.text((20, 12), record["terminal_id"] + " -> " + record["frame_id"] + " candidate",
                  fill="#182433", font=font)
        draw.text((20, 42), "Candidate only | magenta cross = proposed anchor, not CT landing",
                  fill="#46566a", font=caption)
        draw.text((20, 76), "Original native crop", fill="#182433", font=font)
        sheet.paste(Image.fromarray(raw).resize((w*scale, h*scale), Image.Resampling.NEAREST),
                    (20, 106))
        start = 126+h*scale
        draw.text((20, start), "Yellow = proposed metal segment (boundary/connection unreviewed)",
                  fill="#182433", font=caption)
        sheet.paste(Image.fromarray(marked).resize((w*scale, h*scale), Image.Resampling.NEAREST),
                    (20, start+28))
        draw.text((20, sheet.height-32),
                  "Stop at segment ends; continuation unknown; no netlist edits.",
                  fill="#46566a", font=caption)
        save_image(out / f"{prefix}-demo.png", np.array(sheet), state["bundle_id"])
        if record["contact_bridge"] is not None:
            save_image(out / f"{prefix}-ct-bridge.png",
                       render_contact_bridge(record, marked, inputs), state["bundle_id"])
            links += ["", "![gate→候选CT→M1证据链]"
                      f"({prefix}-ct-bridge.png)", ""]
        (out / f"{prefix}.json").write_text(json.dumps(
            dict(record, bundle_id=state["bundle_id"], block_state_id=state["block_state_id"]),
            ensure_ascii=False, indent=2)+'\n')
        title = escape(record["terminal_id"])
        html = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<style>body{font:18px/1.6 system-ui;max-width:900px;margin:24px auto;'
                'padding:16px}img{max-width:100%}button{font:inherit;padding:10px}</style>'
                f'<h1>{title} 金属高亮 demo</h1><p>黄色：AI候选局部金属段；'
                '紫色十字：候选锚点，不是已确认CT落点。连接、边界和延伸尚未审核。</p>'
                f'<p>{escape(record["rationale"])}</p>'
                '<button id="toggle" aria-pressed="true">关闭高亮</button><p>'
                f'<img id="photo" src="{prefix}-overlay.png" alt="局部金属高亮"></p>'
                f'<p><a href="{prefix}-demo.png">静态对照图</a> · '
                f'<a href="{prefix}.json">来源与候选记录</a> · '
                + ('<a href="device-index.html">器件编号</a></p>' if "device_index" in state
                   else '<a href="circuit/report.md">四端连接</a></p>') +
                '<script>const b=document.getElementById("toggle"),'
                'p=document.getElementById("photo");b.addEventListener("click",()=>{'
                'const on=b.getAttribute("aria-pressed")!=="true";'
                'b.setAttribute("aria-pressed",String(on));'
                'b.textContent=on?"关闭高亮":"开启高亮";'
                f'p.src=on?"{prefix}-overlay.png":"{prefix}-raw.png";'
                '});</script></html>')
        (out / f"{prefix}.html").write_text(html)
        links += ["", f"## {record['terminal_id']} 金属高亮候选", "",
                  f"![原图与候选对照]({prefix}-demo.png)", "",
                  f"[交互开关]({prefix}.html) · [结构化来源]({prefix}.json)", "",
                  "仅局部候选，不改变已确认同网；CT落点和未显示延伸仍未知。"]
    return links
