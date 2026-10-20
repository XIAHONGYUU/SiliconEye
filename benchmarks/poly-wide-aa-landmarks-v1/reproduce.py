"""Check one wide-POLY cross-layer match using AA frame evidence, without editing layers.

Run: .venv/bin/python benchmarks/poly-wide-aa-landmarks-v1/reproduce.py --output runs/NEW
Requires the project NumPy/OpenCV/Pillow environment; spec carries all case coordinates.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crop(array, bounds):
    left, top, right, bottom = bounds
    return array[top:bottom, left:right]


def match(poly, aa, poly_roi, aa_roi):
    result = cv2.matchTemplate(crop(aa, aa_roi), crop(poly, poly_roi), cv2.TM_CCOEFF_NORMED)
    _, score, _, (x, y) = cv2.minMaxLoc(result)
    border = x in (0, result.shape[1] - 1) or y in (0, result.shape[0] - 1)
    if border:
        raise ValueError("Search hit its boundary; enlarge search instead of accepting it")
    return dict(
        dx=x + aa_roi[0] - poly_roi[0],
        dy=y + aa_roi[1] - poly_roi[1],
        NCC=score,
        search_boundary_hit=border,
    )


def line_point(images, sample, dx, half):
    measured = {"id": sample["id"]}
    for name in ("poly", "aa"):
        x = sample["x_poly"] + (dx if name == "aa" else 0)
        low, high = sample[name + "_y_search"]
        profile = images[name][low:high, x - half : x + half + 1].mean(axis=1)
        index = int(np.argmax(profile))
        if index in (0, len(profile) - 1):
            raise ValueError("Line measurement hit search boundary: " + sample["id"])
        measured[name + "_xy"] = [x, low + index]
    return measured


def annotate(image, roi, bbox, points):
    left, top, _, _ = roi
    out = image.crop(roi).convert("RGB")
    draw = ImageDraw.Draw(out)
    box = [bbox[0] - left, bbox[1] - top, bbox[2] - left, bbox[3] - top]
    draw.rectangle(box, outline="#dd75ff", width=3)
    draw.text((box[0], box[3] + 5), "W: wide POLY source / projected position", fill="#efaaff")
    for label, (x, y) in points:
        x, y = x - left, y - top
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), outline="#ffe14d", width=2)
        draw.text((x + 8, y - 15), label, fill="#ffe14d")
    return out


def run(root, spec_path, output):
    if output.exists():
        raise ValueError("Use a fresh output directory")
    spec = json.loads(spec_path.read_text())
    locked = {**spec["sources"], **spec["protected"]}
    for item in locked.values():
        if sha(root / item["path"]) != item["sha256"]:
            raise ValueError("Locked input changed: " + item["path"])
    photos = {
        name: Image.open(root / item["path"]).convert("RGB")
        for name, item in spec["sources"].items()
    }
    images = {
        name: cv2.GaussianBlur(
            np.asarray(im.convert("L")).astype("float32"), (0, 0), spec["gaussian_sigma_px"]
        )
        for name, im in photos.items()
    }
    step = match(
        images["poly"], images["aa"], spec["step_fit_poly_roi"], spec["step_search_aa_roi"]
    )
    lower = match(
        images["poly"], images["aa"], spec["lower_step_poly_roi"], spec["lower_step_search_aa_roi"]
    )
    samples = [
        line_point(images, s, step["dx"], spec["line_sample_half_width"])
        for s in spec["scale_fit_samples"]
    ]
    py = np.array([s["poly_xy"][1] for s in samples], dtype=float)
    ay = np.array([s["aa_xy"][1] for s in samples], dtype=float)
    scale, offset = np.linalg.solve(np.column_stack([py, np.ones(2)]), ay)
    if not 0.9 < scale < 1.1:
        raise ValueError("Unexpected local scale; do not stretch to force agreement")
    matrix = np.array([[1, 0, step["dx"]], [0, scale, offset], [0, 0, 1]], float)
    holdouts = [
        line_point(images, s, step["dx"], spec["line_sample_half_width"])
        for s in spec["held_out_samples"]
    ]
    for s in holdouts:
        y, expected = s["poly_xy"][1], s["aa_xy"][1]
        s["translation_residual_y_px"] = float(expected - y - step["dy"])
        s["local_affine_residual_y_px"] = float(expected - scale * y - offset)
    translation_max = max(abs(s["translation_residual_y_px"]) for s in holdouts)
    affine_max = max(abs(s["local_affine_residual_y_px"]) for s in holdouts)
    budget = spec["diagnostic_budget"]
    checks = dict(
        upper_step_NCC=step["NCC"] >= budget["min_step_NCC"],
        held_out_lower_step_NCC=lower["NCC"] >= budget["min_step_NCC"],
        held_out_lower_step_dx=abs(step["dx"] - lower["dx"]) <= budget["max_step_dx_difference_px"],
        spatial_line_holdouts=affine_max <= budget["max_line_residual_px"],
    )
    left, top, right, bottom = spec["poly_native_bbox"]
    projected = [
        left + step["dx"],
        top * scale + offset,
        right + step["dx"],
        bottom * scale + offset,
    ]
    for item in locked.values():
        assert sha(root / item["path"]) == item["sha256"]
    report = dict(
        date=spec["date"],
        observation_id=spec["observation_id"],
        source_to_target="POLY_native_to_AA_native_local_only",
        source_hashes=spec["sources"],
        protected_hashes=spec["protected"],
        initial_step_translation=step,
        held_out_lower_step_translation=lower,
        scale_fit_line_samples=samples,
        held_out_line_samples=holdouts,
        translation_max_abs_y_residual_px=translation_max,
        affine_max_abs_y_residual_px=affine_max,
        matrix=matrix.tolist(),
        projected_POLY_bbox_AA_native=projected,
        diagnostic_checks=checks,
        diagnostic_status="PASS" if all(checks.values()) else "FAIL",
        prior_crop_problem="AA crop y>=570 excluded upper stepped AA at y~553",
        correspondence_status="AI_landmark_candidate_pending_human_review",
        AA_assignment=None,
        material_identity="human_confirmed_wide_POLY_kept",
        geometry_changed=False,
        unchanged_locked_inputs=True,
        limitations=[
            "Local frame landmarks only; no global registration claim",
            "Spatial holdouts from same photo pair, not new evaluation data",
            ("AA material under projected W remains unresolved; no field-POLY inference"),
            "Broad bright-band centers have appearance-dependent uncertainty",
            "No MOS/CT/net inference or foundry DRC",
        ],
        next_human_review=spec["next_human_review"],
    )
    output.mkdir(parents=True)
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (output / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    labels = ["A fit upper bend", "B fit bottom ring"]
    labels += [
        "C upper left",
        "D upper right",
        "E lower bend",
        "F lower left",
        "G lower right",
        "H bottom left",
        "I bottom right",
    ]
    all_points = samples + holdouts
    for name in ("poly", "aa"):
        roi = spec[name + "_display_roi"]
        photos[name].crop(roi).save(output / (name + "-raw.png"))
        points = [(label, s[name + "_xy"]) for label, s in zip(labels, all_points, strict=True)]
        bbox = spec["poly_native_bbox"] if name == "poly" else projected
        annotate(photos[name], roi, bbox, points).save(output / (name + "-marked.png"))
    roi = spec["aa_display_roi"]
    shifted = matrix[:2].copy()
    shifted[:, 2] -= np.array(roi[:2])
    size = (roi[2] - roi[0], roi[3] - roi[1])
    warped = cv2.warpAffine(np.asarray(photos["poly"]), shifted, size, flags=cv2.INTER_LINEAR)
    poly_aligned = Image.fromarray(warped)
    poly_aligned.save(output / "poly-aligned.png")
    aa_crop = photos["aa"].crop(roi)
    blend = Image.blend(aa_crop, poly_aligned, 0.5)
    points = [(label, s["aa_xy"]) for label, s in zip(labels, all_points, strict=True)]
    annotate(
        blend,
        [0, 0, *size],
        [
            projected[0] - roi[0],
            projected[1] - roi[1],
            projected[2] - roi[0],
            projected[3] - roi[1],
        ],
        [(label, [xy[0] - roi[0], xy[1] - roi[1]]) for label, xy in points],
    ).save(output / "overlay-marked.png")
    rows = "".join(
        "<tr><td>"
        + html.escape(s["id"])
        + "</td><td>"
        + str(s["poly_xy"])
        + "</td><td>"
        + str(s["aa_xy"])
        + "</td><td>"
        + f"{s['translation_residual_y_px']:.2f}"
        + "</td><td>"
        + f"{s['local_affine_residual_y_px']:.2f}"
        + "</td></tr>"
        for s in holdouts
    )
    page = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>宽POLY：拐弯AA局部对应复核</title>
<style>body{background:#101923;color:#e5edf5;font:16px system-ui;
max-width:1250px;margin:24px auto;padding:0 18px}
a{color:#8ecbff}
img{max-width:100%;height:auto}
section{background:#1a2b39;padding:16px;margin:18px 0;border-radius:10px}
button,select,input{font:inherit}
table{border-collapse:collapse}
td,th{padding:7px;border:1px solid #607386}
.stack{position:relative}
.stack img{display:block;width:100%}
#top{position:absolute;left:0;top:0}
.notice{border-left:5px solid #eab64f;padding:14px}</style>
<h1>宽POLY：以其上方拐弯AA匹配</h1>
<p class="notice">黄色 A–I 是同一结构的对应标记；
紫色 W 在 POLY 图是已确认宽POLY的既有观察框，
在 AA 图仅表示投影位置，<strong>不是新提取的 AA 边界</strong>。
宽POLY身份不重问，AA归属尚未裁决。</p>
<section><h2>1. 原图与编号：保留上下环、两侧器件参照</h2>
<select id="native">
<option value="marked">编号图</option>
<option value="raw">不遮挡原图</option>
</select>
<h3>POLY 原生坐标</h3>
<img id="poly" src="poly-marked.png">
<h3>AA 原生坐标</h3>
<img id="aa" src="aa-marked.png"></section>
<section><h2>2. 相同 AA 坐标下切层与叠图</h2>
<select id="layer">
<option value="blend">滑动叠图</option>
<option value="aa">AA</option>
<option value="poly">已对齐POLY</option>
<option value="marked">编号叠图</option>
</select>
<label>POLY透明度 <input id="alpha" type="range" min="0" max="100" value="50"></label>
<div class="stack" id="stack">
<img src="aa-raw.png">
<img id="top" src="poly-aligned.png" style="opacity:.5"></div>
<img id="single" hidden src="overlay-marked.png"></section>"""
    page += (
        f"<section><h2>3. 匹配及独立位置检查</h2><p>上侧拐弯平移估计 "
        f"dx={step['dx']}, dy={step['dy']} px，NCC={step['NCC']:.3f}。"
        f"直接平移对下方横环最大偏差 {translation_max:.2f} px，不能称已精准对齐。"
        f"使用上侧拐弯中心A与下方横环中心B估计局部纵向比例 {scale:.6f}；"
        f"保留 x+{step['dx']}，y={scale:.6f}×y+{offset:.6f}。"
        f"其余7个位置检查最大纵向残差 {affine_max:.2f} px；下侧拐弯独立匹配 "
        f"NCC={lower['NCC']:.3f}。只适用于本局部，诊断预算5px不是实际PDK规则。</p>"
    )
    page += (
        "<table><tr><th>未参与纵向拟合的位置</th><th>POLY实测</th>"
        "<th>AA实测</th><th>平移残差Y</th><th>局部缩放残差Y</th></tr>" + rows + "</table></section>"
    )
    page += """<section><h2>4. 此次修正与待判断</h2>
<p>昨天的AA裁剪从y=570开始，截掉了上侧拐弯的凸起（约y=553）；旧页面上下参照不完整。现在通过同一拐弯、另一条平行环和下方横环检查位置，未把紫框强行移到邻近AA。</p>
<p>紫框仍处于拐弯下方、两侧AA之间。当前AA重建模型对此处没有分配器件AA，但这不能证明原图中没有AA，更不能据此改判为场区POLY。请先核对本页标记和叠图是否指向同一位置；若对应成立，再确定这里AA的实际范围或可见性。</p>
<p>本轮没有修改AA/POLY层几何或已审关系；U05及昨天批准范围保持。</p>
<p><a href="report.json">变换、位置测量与保护记录</a> ·
<a href="spec.json">参数和来源哈希</a> ·
<a href="../poly-small-aa-correspondence-v1/reviewed.html">昨日已审记录</a></p></section>
<script>
const native=document.getElementById('native');
const layer=document.getElementById('layer'),alpha=document.getElementById('alpha');
native.onchange=()=>{for(const n of ['aa','poly']){
document.getElementById(n).src=n+'-'+native.value+'.png';}};
function update(){
const mode=layer.value,stack=document.getElementById('stack');
const single=document.getElementById('single');
stack.hidden=mode!=='blend';single.hidden=mode==='blend';
single.src=mode==='aa'?'aa-raw.png':mode==='poly'?'poly-aligned.png':'overlay-marked.png';
document.getElementById('top').style.opacity=alpha.value/100;
}
layer.onchange=update;alpha.oninput=update;update();
</script></html>"""
    (output / "index.html").write_text(page)
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "diagnostic_status",
                    "translation_max_abs_y_residual_px",
                    "affine_max_abs_y_residual_px",
                    "projected_POLY_bbox_AA_native",
                )
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.root / "benchmarks/poly-wide-aa-landmarks-v1/spec-v1.json", args.output)
