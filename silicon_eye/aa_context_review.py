"""Render evidence-preserving AA disagreement and AI-context review, without mask fusion.

Run: python -m silicon_eye.aa_context_review --root . --spec SPEC --output NEW_DIR
Requires Pillow and OpenCV. Input masks are hash-locked; raw source remains unchanged.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .aa_segmentation_eval import write_image
from .geometry_reconstruction import digest
from .scene_geometry import load_locked

COLORS = {"Q1": "#ffb44c", "Q2": "#ffb44c", "Q3": "#72e69c", "Q4": "#66d9f0"}
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def disagreements(masks):
    """Strict agreement categories, not majority vote, confidence or truth labels."""
    stack = np.stack(masks).astype(bool)
    return np.where(stack.all(axis=0), 1, np.where(stack.any(axis=0), 2, 0)).astype(np.uint8)


def run(root, spec_path, output):
    root, spec_path, output = Path(root).resolve(), Path(spec_path).resolve(), Path(output)
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(spec_path.read_text())
    load_locked(root, spec["stroke_review"])
    manifest = {e["path"]: e["sha256"] for e in load_locked(root, spec["run_manifest"])}
    source = root / spec["source"]["path"]
    if digest(source) != spec["source"]["sha256"]:
        raise ValueError("Changed source")
    raw = cv2.imread(str(source))
    output.mkdir(parents=True)
    source_run = root / spec["run"]
    assets = {}
    stats = {}

    def locked(relative):
        p = source_run / relative
        if digest(p) != manifest[relative]:
            raise ValueError("Changed mask/input")
        return cv2.imread(str(p))

    for case in ["S03", "S05"]:
        out = output / case
        out.mkdir()
        crop = locked(f"{case}/raw.png")
        write_image(out / "raw.png", crop)
        write_image(out / "strokes.png", locked(f"{case}/strokes.png"))
        valid = locked(f"{case}/valid.png")[..., 0] > 0
        masks = []
        for method in spec["methods"]:
            for seed in spec["seeds"]:
                masks.append(locked(f"{case}/{method}-{seed}-mask.png")[..., 0] > 0)
            for suffix in ["mask", "overlay"]:
                write_image(
                    out / f"{method}-{suffix}.png",
                    locked(f"{case}/{method}-{spec['display_seed']}-{suffix}.png"),
                )
        classes = disagreements(masks)
        np.save(out / "agreement-categories.npy", classes)
        overlay = crop.copy()
        for val, color in [(1, [85, 220, 100]), (2, [40, 170, 255])]:
            selected = (classes == val) & valid
            overlay[selected] = (crop[selected] * 0.45 + np.array(color) * 0.55).astype(np.uint8)
        write_image(out / "disagreement-overlay.png", overlay)
        stats[case] = {
            key: int(np.count_nonzero((classes == v) & valid))
            for key, v in [("all_predict_background", 0), ("all_predict_AA", 1), ("disagree", 2)]
        }
        assets[case] = dict(native_shape=list(crop.shape[:2]))
    # Only S05 has contextual AI questions this round. No candidate geometry is edited.
    box = [3300, 3330, 4000, 3560]
    x, y, rr, bb = box
    crop = raw[y:bb, x:rr].copy()
    marked = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(marked)
    for q in spec["questions"]:
        a, b, c, d = q["native_bbox"]
        draw.rectangle([a - x, b - y, c - x, d - y], outline=COLORS[q["id"]], width=2)
        # Tags are placed inside the corresponding review ROI and use source-native coordinates.
        draw.text(
            (a - x + 4, b - y),
            q["id"],
            fill=COLORS[q["id"]],
            font=ImageFont.truetype(FONT, 14),
            stroke_width=1,
            stroke_fill="black",
        )
    marked.save(output / "S05/ai-review.png")
    wide = spec["wide_context_native_bbox"]
    a, b, c, d = wide
    wide_image = Image.fromarray(cv2.cvtColor(raw[b:d, a:c], cv2.COLOR_BGR2RGB))
    wd = ImageDraw.Draw(wide_image)
    wd.rectangle([x - a, y - b, rr - a, bb - b], outline="#66d9f0", width=7)
    wide_image.save(output / "wide-context.png")
    context = spec["context_native_bbox"]
    a, b, c, d = context
    context_raw = raw[b:d, a:c].copy()
    context_rf = context_raw.copy()
    rf = cv2.imread(str(output / "S05/rf_texture-overlay.png"))
    context_rf[y - b : bb - b, x - a : rr - a] = rf
    write_image(output / "context-source.png", context_raw)
    write_image(output / "context-rf.png", context_rf)
    # Standalone Chinese review sheet; all comparison panels use the same native S05 crop.
    sheet = Image.new("RGB", (2000, 2200), "#14212b")
    sd = ImageDraw.Draw(sheet)

    def text(x, y, s, size=25, fill="#eef6fa"):
        sd.text((x, y), s, font=ImageFont.truetype(FONT, size), fill=fill)

    text(36, 18, "AA 多方法分歧与上下文复核 v1", 40)
    text(36, 76, "绿色＝所有方法/种子均判AA；橙色＝存在分歧；均判非AA处不着色。", 26)
    text(36, 117, "一致也可能一起错误。不是投票融合；框选为AI复核范围，不是精确材料边界。", 25)

    def panel(path, px, py, w, h, title):
        text(px, py, title, 26)
        im = Image.open(path).convert("RGB")
        im.thumbnail((w, h), Image.Resampling.LANCZOS)
        sheet.paste(im, (px, py + 43))

    panel(output / "wide-context.png", 36, 174, 900, 720, "宽上下文原图：青框为本轮计算窗口")
    text(1020, 180, "AI结合整体结构后的复核意见", 30)
    ty = 240
    for q in spec["questions"]:
        text(1020, ty, q["id"] + " " + q["title"], 25, COLORS[q["id"]])
        ty += 42
        # Explicitly wrap text by measured width, without splitting annotation records.
        for content in [q["judgment"], q["status"]]:
            line = ""
            for ch in content:
                if sd.textlength(line + ch, font=ImageFont.truetype(FONT, 23)) > 915:
                    text(1020, ty, line, 23)
                    ty += 34
                    line = ""
                line += ch
            if line:
                text(1020, ty, line, 23)
                ty += 34
        ty += 25
    panel(
        output / "context-source.png", 36, 970, 930, 410, "位置参照：宽局部原图（AA照片原生坐标）"
    )
    panel(output / "context-rf.png", 1020, 970, 930, 410, "主候选：纹理RF，仅青框范围计算过分割")
    panel(
        output / "S05/strokes.png", 36, 1450, 930, 307, "已审材料笔画：红AA／蓝非AA；黄圈为检查点"
    )
    panel(
        output / "S05/disagreement-overlay.png",
        1020,
        1450,
        930,
        307,
        "4方案 × 3种子：共同AA与分歧（同一窗口）",
    )
    panel(
        output / "S05/ai-review.png",
        36,
        1850,
        930,
        307,
        "AI复核定位：Q1电阻／Q2间隙／Q3暗AA／Q4边界",
    )
    panel(
        output / "S05/gc_refine-overlay.png",
        1020,
        1850,
        930,
        307,
        "对照：GrabCut较整齐，但已审间隙被误填",
    )
    sheet.save(output / "review-sheet.png")
    data = dict(questions=spec["questions"], stats=stats, display_seed=spec["display_seed"])
    (output / "data.js").write_text("const DATA=" + json.dumps(data, ensure_ascii=False) + ";\n")
    (output / "index.html").write_text(PAGE)
    report = dict(
        status="human_review_required",
        source=spec["source"],
        spec_sha256=digest(spec_path),
        code_sha256=digest(__file__),
        stats=stats,
        questions=spec["questions"],
        fused_mask_created=False,
        geometry_changed=False,
        note="S05 only for AI contextual conclusions; S03 is an algorithm control. "
        "Agreement of 12 correlated outputs is not independent confidence. No numeric "
        "target-process DRC or physical scale is known.",
    )
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (output / "manifest.json").write_text(
        json.dumps(
            [
                dict(path=str(p.relative_to(output)), sha256=digest(p))
                for p in sorted(output.rglob("*"))
                if p.is_file()
            ],
            indent=2,
        )
        + "\n"
    )
    return report


PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>AA上下文复核</title>
<style>body{background:#14212b;color:#eee;font:18px/1.7 sans-serif;margin:22px}
a{color:#7df}select{font:inherit}.pair{display:flex;gap:18px}.pair>div{width:50%}
img{width:100%}li{margin-bottom:15px}strong{color:#fc8}</style>
<h1>AA多方法分歧与AI上下文复核</h1><p>保留原始照片与原候选mask，只新增复核图。
绿色为4方案×3种子全部判AA，橙色为分歧，均判非AA处不着色；一致不是正确性证明。
两类RF、两类GrabCut各有共同假设，不是12个独立专家。</p>
<p><a href="review-sheet.png">打开整张复核图（可放大）</a> ·
<a href="wide-context.png">宽上下文原图与计算范围</a></p>
<select id="case"><option>S05</option><option>S03</option></select>
<select id="mode"><option value="disagreement-overlay.png">共同AA与分歧</option>
<option value="rf_texture-overlay.png">纹理RF主候选</option>
<option value="rf_combined-overlay.png">纹理＋结构RF</option>
<option value="gc_fixed-overlay.png">固定GMM GrabCut</option>
<option value="gc_refine-overlay.png">迭代GrabCut</option>
<option value="ai-review.png">AI复核定位（仅S05）</option></select>
<label><input id="samples" type="checkbox">左图显示已审笔画</label>
<div class="pair"><div>原图／已审样本<img id="left"></div>
<div>同原生坐标对照<img id="right"></div></div>
<p>算法单图固定显示预定种子20261018；分歧图包含全部三个种子。计算窗口以外未提取。</p>
<h2>请一次核对以下四项（Q1–Q4均在S05）</h2><ol id="questions"></ol>
<p>Q4允许回答“仍不清楚”。没有因版图通常连续而自动补边、补环或并网。</p>
<script src="data.js"></script><script>
const el=id=>document.getElementById(id);
for(const q of DATA.questions){let li=document.createElement('li');
let strong=document.createElement('strong');strong.textContent=q.id+'：'+q.title;li.append(strong);
for(const s of [q.judgment,q.status,'请判断：'+q.check]){let p=document.createElement('div');
p.textContent=s;li.append(p);}el('questions').append(li);}
function update(){let c=el('case').value,m=el('mode').value;
if(c==='S03'&&m==='ai-review.png'){m='disagreement-overlay.png';el('mode').value=m;}
el('left').src=c+'/'+(el('samples').checked?'strokes.png':'raw.png');el('right').src=c+'/'+m;}
for(const e of document.querySelectorAll('select,input'))e.addEventListener('input',update);
update();</script></html>"""

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--spec", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    run(a.root, a.spec, a.output)
