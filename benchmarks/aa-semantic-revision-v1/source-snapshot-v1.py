"""Fit source-image boundary candidates inside explicit AI semantic hypotheses.

Run: python -m silicon_eye.aa_semantic_revision --root . --spec SPEC --output NEW_DIR
Requires OpenCV/NumPy. Outputs -1 unknown, 0 non-AA, 1 AA. No geometry truth is inferred.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from .aa_segmentation_eval import write_image
from .geometry_reconstruction import digest
from .scene_geometry import load_locked


def reconstruct(raw, case, settings):
    """Material roles come from the spec; image evidence only localizes candidate edges."""
    left, top, right, bottom = case["native_bbox"]
    if raw.shape[:2] != (bottom - top, right - left):
        raise ValueError("Source crop shape mismatch")
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY).astype(np.float32)
    smooth = cv2.blur(gray, (settings["blur_x"], settings["blur_y"]))
    gradient = np.gradient(smooth, axis=0)
    paths = {}
    evidence = {}
    ordered = []
    for curve in case["curves"]:
        a, b = np.array(curve["search_native_y"]) - top
        if not 0 <= a < b <= raw.shape[0]:
            raise ValueError("Search outside crop")
        field = gradient[a:b] if curve["kind"] == "rise" else -gradient[a:b]
        if curve["kind"] == "valley":
            field = -smooth[a:b]
        elif curve["kind"] not in ["rise", "fall"]:
            raise ValueError("Unknown curve kind")
        indices = field.argmax(axis=0)
        path = indices.astype(np.float32) + a
        path = cv2.GaussianBlur(path.reshape(1, -1), (0, 0), settings["curve_sigma"]).ravel()
        if curve["kind"] == "valley":
            score = smooth[a:b].mean(axis=0) - smooth[a:b].min(axis=0)
        else:
            score = field.max(axis=0)
        paths[curve["id"]] = path
        evidence[curve["id"]] = score
        ordered.append(path)
    xs = np.arange(raw.shape[1]) + left
    valid = (xs >= case["x_span"][0]) & (xs < case["x_span"][1])
    for score in evidence.values():
        valid &= score >= settings["min_evidence"]
    for first, second in zip(ordered, ordered[1:], strict=False):
        valid &= second > first
    states = np.full(raw.shape[:2], -1, np.int8)
    contradiction = np.zeros(raw.shape[:2], bool)
    yy = np.arange(raw.shape[0])[:, None]
    for region in case["regions"]:
        if region["material"] not in (0, 1):
            raise ValueError("Unknown material state")
        margin = region.get("margin", settings["uncertainty_px"])
        if "above" in region:
            area = yy < paths[region["above"]] - margin
        elif "below" in region:
            area = yy > paths[region["below"]] + margin
        elif "between" in region:
            a, b = region["between"]
            area = (yy > paths[a] + margin) & (yy < paths[b] - margin)
        elif "around" in region:
            area = np.abs(yy - paths[region["around"]]) <= region["radius"]
        else:
            raise ValueError("Unknown semantic region")
        area &= valid[None, :]
        contradiction |= area & (states >= 0) & (states != region["material"])
        states[area] = region["material"]
    states[contradiction] = -1
    details = dict(
        paths_native_y={k: (v + top).tolist() for k, v in paths.items()},
        evidence={
            k: dict(min=float(v.min()), median=float(np.median(v))) for k, v in evidence.items()
        },
        eligible_columns=int(valid.sum()),
        eligible_native_x=(np.flatnonzero(valid) + left).tolist(),
        conflicting_pixels=int(contradiction.sum()),
    )
    return states, details


def reviewed_center_metrics(states, case, checks):
    left, top, _, _ = case["native_bbox"]
    rows = []
    for p in checks:
        x, y = p["native_xy"]
        value = int(states[y - top, x - left])
        expected = int(p["class_name"] == "AA")
        rows.append(
            dict(
                native_xy=[x, y],
                expected=expected,
                predicted=value,
                status="unknown" if value < 0 else "correct" if value == expected else "wrong",
            )
        )
    return dict(
        correct=sum(v["status"] == "correct" for v in rows),
        wrong=sum(v["status"] == "wrong" for v in rows),
        unknown=sum(v["status"] == "unknown" for v in rows),
        centers=rows,
    )


def run(root, spec_path, output):
    root, spec_path, output = Path(root).resolve(), Path(spec_path).resolve(), Path(output)
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(spec_path.read_text())
    for ref in ["human_review", "clarification"]:
        if ref in spec:
            load_locked(root, spec[ref])
    if "baseline_manifest" in spec:
        load_locked(root, spec["baseline_manifest"])
    path = root / spec["source"]["path"]
    if digest(path) != spec["source"]["sha256"]:
        raise ValueError("Changed source photo")
    photo = cv2.imread(str(path))
    output.mkdir(parents=True)
    results = []
    for case in spec["cases"]:
        left, top, right, bottom = case["native_bbox"]
        raw = photo[top:bottom, left:right].copy()
        states, details = reconstruct(raw, case, spec["settings"])
        out = output / case["id"]
        out.mkdir()
        np.save(out / "states.npy", states)
        domain = np.broadcast_to(
            np.isin(np.arange(raw.shape[1]) + left, details["eligible_native_x"]),
            raw.shape[:2],
        )
        write_image(out / "processing-domain.png", domain.astype(np.uint8) * 255)
        write_image(out / "raw.png", raw)
        overlay = raw.copy()
        for value, color in [(1, [70, 220, 90]), (0, [220, 120, 20])]:
            chosen = states == value
            overlay[chosen] = (raw[chosen] * 0.6 + np.array(color) * 0.4).astype(np.uint8)
        write_image(out / "revision-overlay.png", overlay)
        unknown = states < 0
        unknown_view = raw.copy()
        unknown_view[unknown] = (raw[unknown] * 0.6 + np.array([220, 210, 70]) * 0.4).astype(
            np.uint8
        )
        write_image(out / "unknown-overlay.png", unknown_view)
        curves = raw.copy()
        for native in details["paths_native_y"].values():
            points = np.stack([np.arange(raw.shape[1]), np.array(native) - top], axis=-1).astype(
                np.int32
            )
            cv2.polylines(curves, [points], False, (0, 210, 255), 1)
        write_image(out / "boundary-hypotheses.png", curves)
        result = dict(
            id=case["id"],
            semantics=case["semantics"],
            native_bbox=case["native_bbox"],
            pixels=dict(
                AA=int((states == 1).sum()),
                non_AA=int((states == 0).sum()),
                unknown=int((states < 0).sum()),
                unknown_outside_processing_domain=int(((states < 0) & ~domain).sum()),
                unknown_inside_processing_domain=int(((states < 0) & domain).sum()),
            ),
            **details,
            exact_boundaries_human_accepted=False,
        )
        if "human_check_source" in case:
            old = load_locked(root, case["human_check_source"])
            checks = next(c["checks"] for c in old["cases"] if c["id"] == case["id"])
            result["human_centers"] = reviewed_center_metrics(states, case, checks)
        if "comparison_overlay" in case:
            reference = case["comparison_overlay"]
            before = root / reference["path"]
            if digest(before) != reference["sha256"]:
                raise ValueError("Changed comparison overlay")
            write_image(out / "before-overlay.png", cv2.imread(str(before)))
        results.append(result)
    report = dict(
        status="AI_semantic_revision_candidate_needs_review",
        results=results,
        spec_sha256=digest(spec_path),
        source_sha256=digest(path),
        code_sha256=digest(__file__),
        note="Source-derived paths inside AI-selected search bands, NOT automatic semantic "
        "recognition or accepted layout geometry. Blue is inferred non-AA, green inferred "
        "AA; unknown remains separate, never silently background. Crop-edge regions "
        "continue outside modeled scope. New method window S02 has no human truth.",
        CT_processed=False,
        full_frame_accepted=False,
    )
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (output / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    data = dict(
        cases=[
            dict(
                id=c["id"],
                semantics=c["semantics"],
                has_before="comparison_overlay" in c,
                review_question=c.get("review_question", "核查材料角色、边界候选和未知带。"),
            )
            for c in spec["cases"]
        ],
        results=results,
    )
    (output / "data.js").write_text("const DATA=" + json.dumps(data, ensure_ascii=False) + ";\n")
    (output / "index.html").write_text(PAGE)
    manifest = [
        dict(path=str(p.relative_to(output)), sha256=digest(p))
        for p in sorted(output.rglob("*"))
        if p.is_file()
    ]
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return report


PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>AA语义修订候选</title>
<style>body{background:#14212b;color:#eee;font:18px/1.7 sans-serif;margin:20px}a{color:#7df}
select{font:inherit}.pair{display:flex;gap:15px}.pair>div{width:50%}img{width:100%}</style>
<h1>AA局部语义修订与不同窗口验证</h1>
<p>绿色＝候选AA核心，蓝色＝候选非AA；不着色处保持未知。材料角色由AI指定，边界从原图搜索。
不是多数票融合，不是自动GDS，不把整个矩形当已审真值。边界附近保留未知带。</p>
<p><a href="../../docs/assets/aa-context-review-v1/wide-context.png">S05宽上下文与原计算范围</a></p>
<select id="case"></select>
<select id="mode"><option value="revision-overlay.png">修订候选AA／非AA</option>
<option value="unknown-overlay.png">未知区（青色）</option>
<option value="boundary-hypotheses.png">源图边界假设（橙线）</option>
<option value="before-overlay.png">前一候选（有对照时）</option></select>
<div class="pair"><div>原始照片<img id="raw"></div><div>同坐标候选<img id="result"></div></div>
<p id="status"></p><h2>请核查</h2><ol id="questions"></ol>
<p>候选仅覆盖显示窗口内的部分横向范围，左右边缘与不清楚的过渡保留未知。
贴图框边的AA并非真实截断或孤立岛，不推断框外连接。</p>
<p><a href="spec.json">冻结参数与AI假设</a> · <a href="report.json">三态结果与证据</a></p>
<script src="data.js"></script><script>
const el=id=>document.getElementById(id);
for(const c of DATA.cases){let o=document.createElement('option');o.value=c.id;o.textContent=c.id;
el('case').append(o);let li=document.createElement('li');li.textContent=c.id+'：'+c.review_question;
el('questions').append(li);}
function update(){let c=el('case').value,m=el('mode').value;
if(!DATA.cases.find(v=>v.id===c).has_before&&m==='before-overlay.png'){m='revision-overlay.png';el('mode').value=m;}
el('raw').src=c+'/raw.png';el('result').src=c+'/'+m;
const r=DATA.results.find(v=>v.id===c),q=r.human_centers;
el('status').textContent=r.semantics+'；AA候选 '+r.pixels.AA+' 像素，非AA '+r.pixels.non_AA+
'，未知 '+r.pixels.unknown+(q?'；原6个检查中心：正确 '+q.correct+'，错误 '+q.wrong+
'，未知 '+q.unknown:'；无人工检查真值，不报准确率');}
for(const e of document.querySelectorAll('select'))e.addEventListener('input',update);
update();</script></html>"""

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--spec", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    run(a.root, a.spec, a.output)
