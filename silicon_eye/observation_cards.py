"""Render adapter cards in the existing unified package, preserving native geometry."""
from __future__ import annotations

from html import escape

import numpy as np
from PIL import Image, ImageDraw

from .review_package import save_image

STATUS = {
    "matches_human_review": "与既有人审一致",
    "differs_from_human_review": "与既有人审有差异，需复核",
    "model_unknown_existing_decision_retained": "AI未定，保留既有人审结论",
    "not_previously_confirmed": "尚无对应的确定结论",
}
PREDICATES = {
    "device_exists": "MOS栅指存在", "material_identity": "材料身份",
    "same_net": "电气同网", "different_net": "电气隔离",
    "joined_in_region": "指定层局部直接相连",
    "terminal_maps_to_conductor": "端子对应导体",
}


def render_observation_cards(state, inputs, out):
    parts = [
        '<!doctype html><html lang="zh-CN"><meta charset="utf-8">',
        '<title>AI观察适配复核稿</title><style>',
        'body{font:17px/1.6 system-ui;max-width:1100px;margin:32px auto;padding:0 20px;'
        'background:#f5f6f8;color:#20252b}article,section{background:white;padding:22px;'
        'margin:20px 0;border-radius:10px}img{max-width:100%;height:auto}code{word-break:break-all}'
        '.zoom{max-height:480px;width:auto}.warning{color:#a33}.muted{color:#58616c}'
        'a{color:#1267a5}</style>',
        '<h1>AI观察 → case／材料卡：复核样稿</h1>',
        '<p>请核查对象是否好找、状态是否清楚、连接结论是否符合既有裁决。'
        '新观察均为候选或未知；既有人审保留，检查窗口不作为材料边界。</p>',
        '<p><a href="report.md">完整统一包</a> · <a href="circuit/report.md">四端表与连接矩阵</a>'
        ' · <a href="bundle-state.json">结构化状态</a>'
        ' · <a href="../adaptation.json">适配记录</a></p>',
        '<section><h2>已有人审电路状态</h2><img src="circuit/local-schematic.png" '
        'alt="已有人审电路图"><p>不同节点标签不证明隔离；未知不自动并网。</p></section>',
    ]
    if "device_index" in state:
        parts += ['<p><a href="device-index.html">打开器件跨层编号视图</a></p>']
    for i, adaptation in enumerate(state["observation_adaptations"], 1):
        historical = adaptation["observation_purpose"] == "historical_reexpression"
        label = ("历史结果转写样稿：用于核查接口和使用体验，不计为新AI识别成绩。" if historical
                 else "模型观察复核：是否正确仍需结合证据判断。")
        parts += [f'<section><h2>{escape(adaptation["case_id"])}</h2><p>{label}</p>',
                  f'<p>run_id：<code>{escape(adaptation["run_id"])}</code></p></section>']
        frames = {f["id"]: f for f in adaptation["source_frames"]}
        parts += ['<section><h2>原图位置索引</h2><p>橙框和数字仅标出观察窗口，'
                  '不是材料轮廓。数字对应下方卡片；三层保持各自原生坐标。</p>']
        for k, region in enumerate(adaptation["task_regions"], 1):
            frame = frames[region["frame_id"]]
            source = adaptation["task_sources"][frame["source_ref"]]
            x, y, w, h = region["xywh"]
            with Image.open(inputs.root / source["path"]) as image:
                overview = image.convert("RGB").crop((x, y, x+w, y+h))
            draw = ImageDraw.Draw(overview)
            for j, card in enumerate(adaptation["cards"], 1):
                loc = card["location"]
                if not loc or loc["frame_id"] != region["frame_id"]:
                    continue
                lx, ly, lw, lh = loc["xywh"]
                if not (x <= lx and y <= ly and lx+lw <= x+w and ly+lh <= y+h):
                    continue
                draw.rectangle((lx-x, ly-y, lx+lw-x-1, ly+lh-y-1),
                               outline="#ff9933", width=1)
                draw.text((lx-x+2, ly-y+2), str(j), fill="#ff9933")
            name = f"observation-{i:03}-context-{k:03}.png"
            save_image(out / name, np.array(overview), state["bundle_id"])
            parts += [f'<h3>{escape(region["frame_id"])}</h3>',
                      f'<img src="{name}" width="540" alt="原图观察位置索引">']
        parts += ['</section>']
        for j, card in enumerate(adaptation["cards"], 1):
            existing = card["existing_review"]
            value = ("未知" if card["status"] == "unknown" else
                     "是" if card["value"] is True else "否" if card["value"] is False
                     else card["value"].upper())
            heading = " / ".join(card["subject_ids"])
            parts += [f'<article id="card-{i}-{j}"><h2>{j}. {escape(heading)}</h2>',
                      f'<p>{PREDICATES[card["predicate"]]}：<strong>{escape(value)}</strong>；'
                      f'新记录状态：{"候选" if card["status"] == "candidate" else "未知"}。</p>',
                      f'<p class="warning">{STATUS[existing["status"]]}；既有裁决保持不变。</p>',
                      f'<p>理由：{escape(card["rationale"])}</p>']
            if card["location"]:
                loc = card["location"]
                frame = frames[loc["frame_id"]]
                source = adaptation["task_sources"][frame["source_ref"]]
                x, y, w, h = loc["xywh"]
                with Image.open(inputs.root / source["path"]) as image:
                    crop = image.convert("RGB").crop((x, y, x+w, y+h))
                prefix = f"observation-{i:03}-{j:03}"
                save_image(out / f"{prefix}-raw.png", np.array(crop), state["bundle_id"])
                marked = crop.copy()
                if card["boundary_polygon_xy"]:
                    points = [(px-x, py-y) for px, py in card["boundary_polygon_xy"]]
                    ImageDraw.Draw(marked).line(points + points[:1], fill="#ff9933", width=2)
                    boundary = "橙线仅为候选轮廓，尚无人审像素真值。"
                else:
                    boundary = "边界未知；此图仅为观察窗口，未生成轮廓或掩膜。"
                save_image(out / f"{prefix}-view.png", np.array(marked), state["bundle_id"])
                parts += [f'<img class="zoom" src="{prefix}-view.png" '
                          f'alt="{escape(heading)}原生像素观察窗口">',
                          f'<p>{boundary} <a href="{prefix}-raw.png">打开原像素裁剪</a></p>',
                          f'<p class="muted">{escape(loc["frame_id"])}；xywh(px)='
                          f'{loc["xywh"]}；来源：{escape(source["path"])}</p>']
            else:
                parts += ['<p class="muted">未提供局部定位；请结合已有电路图与材料图复核。'
                          '不自动将端子逻辑关系映射为金属路径。</p>']
            parts += [f'<details><summary>记录来源</summary><p>scope：'
                      f'{escape(card["scope_id"])}；观察ID：{escape(card["id"])}；'
                      f'去向：{escape(card["route"])}</p></details>',
                      '</article>']
    parts += ['<section><h2>已有材料与宏观配准证据</h2>',
              '<p>以下为原复核包输出；材料身份/大致位置已确认，轮廓仍为候选。'
              '宏观配准不证明精确CT落点。</p>']
    for path in sorted(out.glob("*-support.png")) + sorted(out.glob("*-overlay.png")):
        parts += [f'<p>{escape(path.name)}</p><img src="{escape(path.name)}">']
    parts += ['</section><p>本稿不新增物理尺寸、精确边界或金属路径结论。</p></html>']
    (out / "index.html").write_text("\n".join(parts) + "\n")
    return ["", "## AI观察适配", "", "[打开可视复核稿](index.html)", "",
            "新观察与既有人审分开显示；unknown不生成带假定布尔值的case断言。",
            "差异仅作为复核提示，不覆盖原裁决、不改变已确认网络。"]
