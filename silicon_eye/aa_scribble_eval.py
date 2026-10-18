"""Compare AA algorithms using explicit AI-draft polylines and frozen human checks.

Run: python -m silicon_eye.aa_scribble_eval --root . --spec SPEC --output NEW_DIR
Requires segmentation-eval extras. Draft stroke pixels are not human-approved truth.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from .aa_prompted_eval import check_labels
from .aa_segmentation_eval import annotation_mask, sparse_metrics, write_image
from .aa_texture_eval import feature_groups
from .geometry_reconstruction import digest
from .scene_geometry import load_locked


def stroke_labels(case, strokes, valid, guard):
    """Rasterize only explicit strokes; remove a guard band around every held check."""
    if guard < 0:
        raise ValueError("Negative check guard")
    left, top, right, bottom = case["native_bbox"]
    labels = annotation_mask(dict(native_bbox=case["native_bbox"], annotations=case["prompts"]))
    for stroke in strokes:
        if stroke["class_name"] not in ["AA", "background"]:
            raise ValueError("Unknown material class")
        if stroke["thickness"] < 1 or stroke["thickness"] % 2 == 0:
            raise ValueError("Stroke thickness must be positive and odd")
        points = np.array(stroke["native_points"], np.int32) - [left, top]
        if len(points) < 2 or np.any(points < 0) or np.any(points >= [right - left, bottom - top]):
            raise ValueError("Stroke outside crop")
        selected = np.zeros(labels.shape, np.uint8)
        cv2.polylines(selected, [points], False, 1, stroke["thickness"])
        mask = selected.astype(bool)
        value = int(stroke["class_name"] == "AA")
        if np.any((labels[mask] >= 0) & (labels[mask] != value)):
            raise ValueError("Conflicting stroke classes")
        labels[mask] = value
    labels[~valid] = -1
    for check in case["checks"]:
        x, y = np.array(check["native_xy"]) - [left, top]
        labels[max(0, y - guard) : y + guard + 1, max(0, x - guard) : x + guard + 1] = -1
    return labels


def grabcut_masks(raw, samples, seed, iterations):
    selected = samples >= 0
    colors = raw[selected]
    targets = samples[selected]
    if min(np.count_nonzero(targets == c) for c in [0, 1]) < 5:
        raise ValueError("Insufficient GMM samples")
    palette = np.where(targets == 1, cv2.GC_FGD, cv2.GC_BGD).astype(np.uint8).reshape(-1, 1)
    bg, fg = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.setRNGSeed(seed)
    cv2.grabCut(colors.reshape(-1, 1, 3), palette, None, bg, fg, 1, cv2.GC_INIT_WITH_MASK)
    result = {}
    for method, mode, n in [
        ("gc_fixed", cv2.GC_EVAL_FREEZE_MODEL, 1),
        ("gc_refine", cv2.GC_EVAL, iterations),
    ]:
        labels = np.full(raw.shape[:2], cv2.GC_PR_BGD, np.uint8)
        if method == "gc_refine":
            labels[result["gc_fixed"]] = cv2.GC_PR_FGD
        labels[samples == 0] = cv2.GC_BGD
        labels[samples == 1] = cv2.GC_FGD
        cv2.grabCut(raw, labels, None, bg.copy(), fg.copy(), n, mode)
        result[method] = np.isin(labels, [cv2.GC_FGD, cv2.GC_PR_FGD])
    return result


def run(root, spec_path, output):
    from sklearn.ensemble import RandomForestClassifier

    root, spec_path, output = Path(root).resolve(), Path(spec_path).resolve(), Path(output)
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(spec_path.read_text())
    previous = load_locked(root, spec["previous_protocol"])
    prompts = load_locked(root, previous["prompt_spec"])
    review = load_locked(root, prompts["human_review"])
    approved = {
        (c["id"], tuple(p["native_xy"]), p["class_name"])
        for c in review["cases"]
        for p in c["approved_centers"]
    }
    baseline_manifest = {
        v["path"]: v["sha256"] for v in load_locked(root, spec["baseline_manifest"])
    }
    source = root / prompts["source"]["path"]
    if digest(source) != prompts["source"]["sha256"]:
        raise ValueError("Changed source")
    photo = cv2.imread(str(source))
    cv2.setNumThreads(2)
    output.mkdir(parents=True)
    rows = []
    counts = {}
    for case in prompts["cases"]:
        for item in case["prompts"] + case["checks"]:
            if (case["id"], tuple(item["native_xy"]), item["class_name"]) not in approved:
                raise ValueError("Unreviewed original center")
        x, y, right, bottom = case["native_bbox"]
        raw = photo[y:bottom, x:right]
        valid_path = root / spec["baseline_run"] / case["id"] / "valid.png"
        if digest(valid_path) != baseline_manifest[f"{case['id']}/valid.png"]:
            raise ValueError("Changed baseline validity")
        valid = cv2.imread(str(valid_path), 0) > 0
        samples = stroke_labels(
            case, spec["strokes"][case["id"]], valid, spec["check_guard_radius"]
        )
        checks = check_labels(case)
        if np.any((checks >= 0) & ~valid):
            raise ValueError("Check center outside valid coverage")
        if np.any((checks >= 0) & (samples >= 0)):
            raise ValueError("Training/check overlap")
        out = output / case["id"]
        out.mkdir()
        write_image(out / "raw.png", raw)
        np.save(out / "samples.npy", samples)
        np.save(out / "checks.npy", checks)
        write_image(out / "valid.png", valid.astype(np.uint8) * 255)
        marked = raw.copy()
        marked[samples == 1] = [30, 30, 240]
        marked[samples == 0] = [240, 120, 0]
        for stroke in spec["strokes"][case["id"]]:
            px, py = np.array(stroke["native_points"][0]) - [x, y]
            cv2.putText(
                marked,
                stroke["id"],
                (px, py - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (30, 30, 240) if stroke["class_name"] == "AA" else (240, 140, 0),
                1,
            )
        for item in case["checks"]:
            px, py = np.array(item["native_xy"]) - [x, y]
            cv2.circle(marked, (int(px), int(py)), spec["check_guard_radius"], (0, 240, 240), 1)
        write_image(out / "strokes.png", marked)
        counts[case["id"]] = {
            name: int(np.count_nonzero(samples == v)) for name, v in [("AA", 1), ("background", 0)]
        }
        groups = feature_groups(raw, previous["features"])
        selected = samples >= 0
        baseline = {}
        for old, new in [
            ("color", "rf_color"),
            ("texture", "rf_texture"),
            ("combined", "rf_combined"),
        ]:
            for seed in previous["seeds"]:
                relative = f"{case['id']}/{old}-{seed}-mask.png"
                path = root / spec["baseline_run"] / relative
                if digest(path) != baseline_manifest[relative]:
                    raise ValueError("Changed baseline mask")
                baseline[(new, seed)] = cv2.imread(str(path), 0) > 0
        for seed in previous["seeds"]:
            masks = {}
            for mode in ["color", "texture", "combined"]:
                feats = groups[mode]
                model = RandomForestClassifier(
                    n_estimators=prompts["settings"]["forest_trees"],
                    max_depth=prompts["settings"]["forest_max_depth"],
                    min_samples_leaf=1,
                    class_weight="balanced_subsample",
                    max_features="sqrt",
                    random_state=seed,
                    n_jobs=2,
                )
                model.fit(feats[selected], samples[selected])
                masks["rf_" + mode] = (
                    model.predict(feats.reshape(-1, feats.shape[-1])).reshape(samples.shape) == 1
                )
            masks.update(
                grabcut_masks(raw, samples, seed, prompts["settings"]["grabcut_iterations"])
            )
            for method, mask in masks.items():
                mask &= valid
                stem = f"{method}-{seed}"
                write_image(out / f"{stem}-mask.png", mask.astype(np.uint8) * 255)
                overlay = raw.copy()
                overlay[mask] = (raw[mask] * 0.5 + np.array([50, 230, 80]) * 0.5).astype(np.uint8)
                write_image(out / f"{stem}-overlay.png", overlay)
                probe = previous["diagnostic_boxes"].get(case["id"], [])
                diagnostic = {}
                for box in probe:
                    a, b, c, d = box["native_bbox"]
                    v = valid[b - y : d - y, a - x : c - x]
                    # Exclude training pixels so the diagnostic is not dominated by hard strokes.
                    v = v & (samples[b - y : d - y, a - x : c - x] < 0)
                    diagnostic[box["id"]] = dict(
                        predicted_AA_fraction=float(mask[b - y : d - y, a - x : c - x][v].mean()),
                        pixels=int(v.sum()),
                        status="AI_box_not_dense_truth_training_pixels_excluded",
                    )
                row = dict(
                    case=case["id"],
                    method=method,
                    seed=seed,
                    **sparse_metrics(mask, checks),
                    diagnostic=diagnostic,
                )
                if (method, seed) in baseline:
                    row["previous_center_only"] = sparse_metrics(baseline[(method, seed)], checks)
                    relative = f"{method}-{seed}-previous-overlay.png"
                    oldmask = baseline[(method, seed)]
                    oldview = raw.copy()
                    oldview[oldmask] = (raw[oldmask] * 0.5 + np.array([50, 230, 80]) * 0.5).astype(
                        np.uint8
                    )
                    write_image(out / relative, oldview)
                rows.append(row)
    report = dict(
        status="AI_draft_stroke_development_comparison",
        rows=rows,
        training_pixels=counts,
        training_labels_status="original_centers_human_confirmed_new_strokes_AI_draft",
        source_sha256=digest(source),
        dependency_code_sha256={
            name: digest(Path(__file__).with_name(name))
            for name in ["aa_prompted_eval.py", "aa_texture_eval.py", "aa_segmentation_eval.py"]
        },
        spec_sha256=digest(spec_path),
        code_sha256=digest(__file__),
        stroke_labels_human_approved=False,
        full_mask_accepted=False,
        geometry_processed=False,
        note="Same raster samples used by RF and GMM; GrabCut additionally fixes all stroke "
        "pixels as hard labels, RF does not. Budget differs from old center-only runs. "
        "Only original 12 human check centers are scored; no dense or blind metrics.",
    )
    for name, data in [("report.json", report), ("spec.json", spec)]:
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    data = dict(
        cases=list(spec["strokes"]), seeds=previous["seeds"], rows=rows, strokes=spec["strokes"]
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


PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>AA区域笔画对照</title>
<style>body{font:17px/1.6 sans-serif;background:#14212b;color:#eee;margin:20px}a{color:#7df}
select{font:inherit}.pair{display:flex;gap:12px}.pair>div{width:50%}img{width:100%}
table{border-collapse:collapse}th,td{border:1px solid #789;padding:6px}</style>
<h1>AA区域笔画样稿与算法对照</h1><p>红色＝AA笔画，蓝色＝非AA笔画；新增整段笔画为AI候选，
等待材料身份核查。黄色圈＝原12个检查中心的训练避让区，不是新增标注。
只评分原检查中心，不评分笔画；这里是开发试验，不是全图验收。</p>
<select id="case"></select><select id="method"></select><select id="seed"></select>
<label><input id="rawOnly" type="checkbox">左侧只看原图</label>
<label><input id="before" type="checkbox">右侧看上一轮中心提示RF</label>
<label><input id="binary" type="checkbox">右侧二值mask</label>
<div class="pair"><div>原图／待核查笔画<img id="raw"></div>
<div>分割候选<img id="result"></div></div>
<p id="score"></p><h2>本窗口笔画核查清单</h2><ul id="list"></ul>
<table><thead><tr><th>窗口</th><th>算法</th><th>种子</th><th>AA命中</th><th>背景误报</th>
<th>电阻诊断框AA占比（排除训练像素，非准确率）</th></tr></thead><tbody id="rows"></tbody></table>
<p><a href="spec.json">笔画原生坐标与参数</a> · <a href="report.json">结果</a> ·
<a href="../../docs/assets/aa-prompted-comparison-v1/U-native-context.png">宽范围位置参照</a></p>
<script src="data.js"></script><script>
const el=id=>document.getElementById(id),names={rf_color:'RF颜色',rf_texture:'RF颜色+纹理',
rf_combined:'RF颜色+纹理+结构',gc_fixed:'固定GMM GrabCut',gc_refine:'迭代GrabCut'};
for(const [k,vs] of Object.entries({case:DATA.cases,method:Object.keys(names),seed:DATA.seeds})){
for(const v of vs){let o=document.createElement('option');o.value=v;o.textContent=names[v]||v;
el(k).append(o);}}
for(const r of DATA.rows){let tr=document.createElement('tr');let d=r.diagnostic.resistor_interior;
for(const v of [r.case,names[r.method],r.seed,r.tp+'/'+(r.tp+r.fn),r.fp+'/'+(r.fp+r.tn),
d?(100*d.predicted_AA_fraction).toFixed(1)+'%':'—']){let td=document.createElement('td');
td.textContent=v;tr.append(td);}el('rows').append(tr);}
function update(){let c=el('case').value,m=el('method').value,s=Number(el('seed').value);
el('raw').src=c+'/'+(el('rawOnly').checked?'raw.png':'strokes.png');
let old=el('before').checked&&m.startsWith('rf_');
el('result').src=c+'/'+m+'-'+s+(old?'-previous-overlay.png':
(el('binary').checked?'-mask.png':'-overlay.png'));
const r=DATA.rows.find(v=>v.case===c&&v.method===m&&v.seed===s);
const q=old?r.previous_center_only:r;
el('score').textContent=(old?'上一轮中心提示：':'本轮AI笔画：')+'AA检查 '+q.tp+'/'+(q.tp+q.fn)
+'，背景误报 '+q.fp+'/'+(q.fp+q.tn);
el('list').replaceChildren();for(const p of DATA.strokes[c]){let li=document.createElement('li');
li.textContent=p.id+'：'+(p.class_name==='AA'?'AA':'非AA')+'；'+p.reason+'（待核查）';
el('list').append(li);}}
for(const e of document.querySelectorAll('select,input'))e.addEventListener('input',update);
el('method').value='rf_combined';update();</script></html>"""

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--spec", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    run(a.root, a.spec, a.output)
