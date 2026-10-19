"""Render declared visual observations for review; no material inference or source edits.

Run from repository: .venv/bin/python benchmarks/poly-vertical-reassessment-v3/render_review.py
    --spec benchmarks/poly-vertical-reassessment-v3/spec-v1.json --output NEW_DIRECTORY
Requires the existing project environment. Coordinates and scope live only in the spec.
"""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon

from silicon_eye.geometry_reconstruction import orthogonal_fit, project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def render(root, spec_path, output):
    spec = json.loads(spec_path.read_text())
    if output.exists():
        raise ValueError("Use a new output directory")
    for ref in [*spec["sources"].values(), spec["baseline"], spec["human_feedback"]]:
        assert digest(root / ref["path"]) == ref["sha256"], ref["path"]
    baseline = json.loads((root / spec["baseline"]["path"]).read_text())
    for ref in baseline["references"].values():
        assert digest(root / ref["path"]) == ref["sha256"], ref["path"]
    output.mkdir(parents=True)
    poly = cv2.imread(str(root / spec["sources"]["poly"]["path"]))
    aa = cv2.imread(str(root / spec["sources"]["aa"]["path"]))
    objects = []
    for obj in spec["objects"]:
        native = np.asarray(obj["observed_outline_native_xy"], float)
        layout = orthogonal_fit(native, obj["edge_axes"])
        matrix = cv2.getPerspectiveTransform(native.astype(np.float32), layout.astype(np.float32))
        assert np.max(np.abs(project(native, matrix) - layout)) < 0.001
        assert Polygon(native).contains(Polygon(obj["old_B1_native_outline"]))
        objects.append(dict(obj, layout_outline=layout.tolist(), native_to_layout=matrix.tolist()))
    for i, obj in enumerate(objects):
        for other in objects[:i]:
            assert (
                Polygon(obj["observed_outline_native_xy"])
                .intersection(Polygon(other["observed_outline_native_xy"]))
                .area
                == 0
            )
            assert (
                Polygon(obj["layout_outline"]).intersection(Polygon(other["layout_outline"])).area
                == 0
            )
    for view, bounds in spec["windows"].items():
        x, y, r, b = bounds
        raw = (aa if view.startswith("aa") else poly)[y:b, x:r].copy()
        cv2.imwrite(str(output / (view + "-raw.png")), raw)
        if view.startswith("aa"):
            continue
        for mode in ["new", "old", "comparison", "ends"]:
            image = raw.copy()
            for index, obj in enumerate(objects):
                if mode == "ends":
                    tint = image.copy()
                    for left, top, right, bottom in obj["end_zones_native_xyxy"]:
                        cv2.rectangle(
                            tint, (left - x, top - y), (right - x, bottom - y), (20, 145, 245), -1
                        )
                    image = cv2.addWeighted(image, 0.65, tint, 0.35, 0)
                paths = []
                if mode in {"old", "comparison"}:
                    paths.append((obj["old_B1_native_outline"], (0, 215, 255)))
                if mode in {"new", "comparison", "ends"}:
                    paths.append((obj["observed_outline_native_xy"], (255, 165, 30)))
                for points, color in paths:
                    points = np.rint(np.asarray(points) - [x, y]).astype(np.int32)
                    cv2.polylines(image, [points], True, color, 1, cv2.LINE_AA)
                anchor = np.asarray(obj["observed_outline_native_xy"])[0] - [x, y + 13]
                cv2.putText(
                    image,
                    "Q" + str(index + 1),
                    tuple(anchor.astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (255, 200, 70),
                    1,
                    cv2.LINE_AA,
                )
            cv2.imwrite(str(output / f"{view}-{mode}.png"), image)
    allpoints = np.concatenate([np.array(o["layout_outline"]) for o in objects])
    x, y = allpoints.min(0) - 12
    r, b = allpoints.max(0) + 12
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {r - x} {b - y}">'
    for obj in objects:
        pts = " ".join(f"{a},{b}" for a, b in obj["layout_outline"])
        svg += f'<polygon points="{pts}" fill="#258cca" stroke="#a4dfff" stroke-width=".6"/>'
    (output / "layout.svg").write_text(svg + "</svg>")
    report = dict(
        spec,
        objects=objects,
        status="AI_geometry_candidate_pending_human_review",
        technical_checks="source_locks_valid_HV_geometry_no_overlap_old_core_containment",
        completeness="broader_body_hypothesis_end_transitions_still_unknown",
        inference="visual_AI_not_algorithm_detection",
        code_sha256=digest(Path(__file__)),
        spec_sha256=digest(spec_path),
    )
    save(output / "report.json", report)
    save(output / "spec.json", spec)
    (output / "data.js").write_text("const DATA=" + json.dumps(report, ensure_ascii=False) + ";\n")
    (output / "index.html").write_text(PAGE)
    save(
        output / "manifest.json",
        {str(p.relative_to(output)): digest(p) for p in sorted(output.iterdir()) if p.is_file()},
    )


PAGE = """<!doctype html>
<html lang="zh">
<meta charset="utf-8">
<title>竖向POLY重新判断 v3</title>
<style>body{font-family:sans-serif;
background:#18202b;
color:#eee;
max-width:1450px;
margin:24px auto;
padding:16px}a{color:#86d8ff}select,button{padding:10px;
margin:4px}img{width:100%;
height:auto}#layout{width:220px}.pair{display:grid;
grid-template-columns:1fr 1fr;
gap:18px}.table{overflow:auto}table{border-collapse:collapse}td,th{padding:8px;
border:1px solid #586372}
.warning{color:#ffd486}
@media(max-width:850px){.pair{grid-template-columns:1fr}}</style>
<h1>竖向POLY：重新判断较完整的栅体范围</h1>
<p>判断：Q1、Q2是相邻的竖向MOS栅指；蓝色为本轮AI重新观察的较完整主体候选，黄色为上一轮偏小的B1（此次仅用作对照）。未改已审横向POLY。</p>
<p>这次重新观察上下延伸及两侧范围，没有按固定倍数放大。照片中的网格是拍屏纹理，亮点是CT线索，均不直接决定栅体轮廓。新范围仍需验收，未写回正式POLY层。</p>
<select id="view">
<option value="poly_detail">放大：保留邻近器件与环的上下文</option>
<option value="poly_context">宽视野：阵列相对位置</option>
</select>
<select id="mode">
<option value="comparison">旧黄色 / 新蓝色叠加</option>
<option value="new">仅本轮蓝色候选</option>
<option value="old">上一轮偏小轮廓</option>
<option value="ends">蓝色主体 + 橙色端部待核</option>
<option value="raw">纯原图</option>
</select>
<p id="range">
</p>
<div class="pair">
<div>同一窗口纯原图<img id="source">
</div>
<div>所选结果（点击图片打开原像素）<a id="open">
<img id="result">
</a>
</div>
</div>
<h2>本轮一次核查清单</h2>
<ol id="questions">
</ol>
<p class="warning">蓝色矩形端边是候选主体范围，不是已确认的物理终止；
橙色表示真实端部过渡、扩宽/接触引出形状仍需核查，不表示非POLY。没有新增CT归属或连接判断。</p>
<h2>AA / POLY宽上下文</h2>
<p>两图保持各自原生坐标，未细配准，没有把AA暗线直接投影成POLY。AA的竖向沟道线索用于理解方向与阵列，不提供本轮精确边界。</p>
<div class="pair">
<div>AA原生窗口<img src="aa_context-raw.png">
</div>
<div>POLY原生窗口<img src="poly_context-raw.png">
</div>
</div>
<h2>规则几何候选</h2>
<p>纯规则图与原图轮廓分开保存，局部矩阵仅记录对象来源对应；没有公共全幅配准或物理尺寸含义。</p>
<img id="layout" src="layout.svg">
<p>
<a href="report.json">判断、候选坐标与来源记录</a> ·
<a href="../../checkpoints/2026-10-19-poly-vertical-reassessment.md">复核说明</a>
</p>
<script src="data.js">
</script>
<script>
const el=id=>document.getElementById(id);

function update(){let v=el('view').value,m=el('mode').value;
el('source').src=v+'-raw.png';
el('result').src=v+'-'+m+'.png';
el('open').href=el('result').src;
el('range').textContent='POLY原生范围 '+DATA.windows[v].join(', ')+'；原图与叠加使用同一窗口';
}
for(const q of DATA.questions){let li=document.createElement('li');
li.textContent=q;
el('questions').append(li);
}
for(const id of ['view','mode'])el(id).addEventListener('change',update);
update();

</script>
</html>"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(Path.cwd(), args.spec, args.output)
