"""Ablate AA color, texture and directional structure with frozen local prompts.

Run: python -m silicon_eye.aa_texture_eval --root . --spec SPEC --output NEW_DIR
Requires segmentation-eval extras. Known-case development, not dense/blind validation.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

from .aa_prompted_eval import check_labels
from .aa_segmentation_eval import annotation_mask, image_features, sparse_metrics, write_image
from .geometry_reconstruction import digest
from .scene_geometry import load_locked


def feature_groups(raw, settings):
    """No coordinates, hand-cut regions, morphological filling or inferred connections."""
    existing = image_features(raw, settings["feature_sigmas"])
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    smooth = cv2.GaussianBlur(gray, (0, 0), 1)
    gx = cv2.Sobel(smooth, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(smooth, cv2.CV_32F, 0, 1, ksize=3)
    structure = []
    for sigma in settings["tensor_sigmas"]:
        xx = cv2.GaussianBlur(gx * gx, (0, 0), sigma)
        yy = cv2.GaussianBlur(gy * gy, (0, 0), sigma)
        xy = cv2.GaussianBlur(gx * gy, (0, 0), sigma)
        energy = xx + yy
        anisotropy = np.sqrt((xx - yy) ** 2 + 4 * xy * xy) / (energy + 1e-6)
        structure.extend(
            [energy, anisotropy, (xx - yy) / (energy + 1e-6), 2 * xy / (energy + 1e-6)]
        )
    for width in settings["directional_widths"]:
        horizontal = cv2.blur(gray, (width, 3))
        vertical = cv2.blur(gray, (3, width))
        structure.extend([horizontal, vertical, horizontal - vertical])
    structure = np.stack(structure, axis=-1)
    return dict(
        color=existing[..., :3],
        texture=existing,
        structure=np.concatenate([existing[..., :3], structure], axis=-1),
        combined=np.concatenate([existing, structure], axis=-1),
    )


def run(root, spec_path, output):
    from sklearn.ensemble import RandomForestClassifier

    root, spec_path, output = Path(root).resolve(), Path(spec_path).resolve(), Path(output)
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(spec_path.read_text())
    prompts = load_locked(root, spec["prompt_spec"])
    review = load_locked(root, prompts["human_review"])
    approved = {
        (c["id"], tuple(p["native_xy"]), p["class_name"])
        for c in review["cases"]
        for p in c["approved_centers"]
    }
    source = root / prompts["source"]["path"]
    if digest(source) != prompts["source"]["sha256"]:
        raise ValueError("Changed source")
    raw = cv2.imread(str(source))
    cv2.setNumThreads(2)
    output.mkdir(parents=True)
    rows = []
    for case in prompts["cases"]:
        for p in case["prompts"] + case["checks"]:
            if (case["id"], tuple(p["native_xy"]), p["class_name"]) not in approved:
                raise ValueError("Unreviewed center")
        x, y, right, bottom = case["native_bbox"]
        crop = raw[y:bottom, x:right]
        checks = check_labels(case)
        samples = annotation_mask(
            dict(native_bbox=case["native_bbox"], annotations=case["prompts"])
        )
        selected = samples >= 0
        valid = np.ones(crop.shape[:2], bool)
        for bx, by, br, bb in spec["excluded_native_boxes"]:
            valid[
                max(0, by - y) : max(0, min(bottom, bb) - y),
                max(0, bx - x) : max(0, min(right, br) - x),
            ] = False
        if np.any((checks >= 0) & ~valid) or np.any(selected & ~valid):
            raise ValueError("Reviewed centers/samples in excluded area")
        out = output / case["id"]
        out.mkdir()
        write_image(out / "raw.png", crop)
        np.save(out / "checks.npy", checks)
        np.save(out / "samples.npy", samples)
        write_image(out / "valid.png", valid.astype(np.uint8) * 255)
        groups = feature_groups(crop, spec["features"])
        for mode, feats in groups.items():
            predictions = []
            for seed in spec["seeds"]:
                start = time.perf_counter()
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
                mask = model.predict(feats.reshape(-1, feats.shape[-1]))
                mask = mask.reshape(crop.shape[:2]).astype(bool) & valid
                seconds = time.perf_counter() - start
                predictions.append(mask)
                stem = f"{mode}-{seed}"
                write_image(out / f"{stem}-mask.png", mask.astype(np.uint8) * 255)
                overlay = crop.copy()
                overlay[mask] = (crop[mask] * 0.5 + np.array([50, 230, 80]) * 0.5).astype(np.uint8)
                write_image(out / f"{stem}-overlay.png", overlay)
                diagnostics = {}
                for probe in spec["diagnostic_boxes"].get(case["id"], []):
                    a, b, c, d = probe["native_bbox"]
                    area = valid[b - y : d - y, a - x : c - x]
                    diagnostics[probe["id"]] = float(
                        mask[b - y : d - y, a - x : c - x][area].mean()
                    )
                rows.append(
                    dict(
                        case=case["id"],
                        mode=mode,
                        seed=seed,
                        features=feats.shape[-1],
                        seconds=seconds,
                        **sparse_metrics(mask, checks),
                        diagnostic_predicted_AA_fraction=diagnostics,
                    )
                )
            stack = np.stack(predictions)
            disagreement = stack.any(axis=0) != stack.all(axis=0)
            write_image(out / f"{mode}-seed-disagreement.png", disagreement.astype(np.uint8) * 255)
    report = dict(
        status="development_ablation_not_blind_or_dense_validation",
        rows=rows,
        spec_sha256=digest(spec_path),
        code_sha256=digest(__file__),
        source_sha256=digest(source),
        prompt_spec=spec["prompt_spec"],
        full_mask_accepted=False,
        note="Same prompts/checks/forest hyperparameters across arms. sqrt samples a "
        "dimension-dependent number of features. Probe boxes are AI-selected "
        "diagnostics, not dense human truth. Seed agreement is not correctness.",
    )
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (output / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    data = dict(cases=[c["id"] for c in prompts["cases"]], seeds=spec["seeds"], rows=rows)
    (output / "data.js").write_text("const DATA=" + json.dumps(data, ensure_ascii=False) + ";\n")
    (output / "index.html").write_text(PAGE)
    entries = [
        dict(path=str(p.relative_to(output)), sha256=digest(p))
        for p in sorted(output.rglob("*"))
        if p.is_file()
    ]
    (output / "manifest.json").write_text(json.dumps(entries, indent=2) + "\n")
    return report


PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>AA纹理与结构对照</title>
<style>body{font:17px/1.6 sans-serif;background:#14212b;color:#eee;margin:20px}
select{font:inherit}img{width:100%}.pair{display:flex;gap:16px}.pair>div{width:50%}
td,th{border:1px solid #789;padding:6px}table{border-collapse:collapse}a{color:#7df}</style>
<h1>AA颜色／纹理／方向结构消融</h1><p>固定7个训练中心、12个独立于训练的检查中心；
同一批已看过的开发窗口，非盲测。U用于训练。诊断框占比不代表准确率。
方向特征描述图像邻域，不强制补环或连线；没有正交化。</p>
<select id="case"></select><select id="mode"></select><select id="seed"></select>
<label><input id="binary" type="checkbox">二值mask</label>
<label><input id="unstable" type="checkbox">三个种子分歧（白色）</label>
<div class="pair"><div>原始照片<img id="raw"></div><div>候选<img id="result"></div></div>
<p id="score"></p><table><thead><tr><th>窗口</th><th>特征组</th><th>种子</th>
<th>AA命中</th><th>背景误报</th><th>诊断框AA预测比例（非准确率）</th></tr></thead>
<tbody id="rows"></tbody></table><p><a href="spec.json">参数与诊断框范围</a> ·
<a href="report.json">完整结果</a></p><script src="data.js"></script><script>
const el=id=>document.getElementById(id),names={color:'仅颜色',texture:'颜色+原纹理',
structure:'颜色+方向结构',combined:'颜色+纹理+方向结构'};
const choices={case:DATA.cases,mode:Object.keys(names),seed:DATA.seeds};
for(const [key,values] of Object.entries(choices)){
for(const v of values){let o=document.createElement('option');o.value=v;o.textContent=names[v]||v;
el(key).append(o);}}
for(const r of DATA.rows){let tr=document.createElement('tr');for(const v of [r.case,names[r.mode],
r.seed,r.tp+'/'+(r.tp+r.fn),r.fp+'/'+(r.fp+r.tn),
JSON.stringify(r.diagnostic_predicted_AA_fraction,
(k,v)=>typeof v==='number'?Math.round(v*1000)/1000:v)]){
let td=document.createElement('td');td.textContent=v;tr.append(td);}el('rows').append(tr);}
function update(){let c=el('case').value,m=el('mode').value,s=Number(el('seed').value);
el('raw').src=c+'/raw.png';el('result').src=c+'/'+m+(el('unstable').checked?
'-seed-disagreement.png':'-'+s+(el('binary').checked?'-mask.png':'-overlay.png'));
const r=DATA.rows.find(v=>v.case===c&&v.mode===m&&v.seed===s);
el('score').textContent='特征数 '+r.features+'；AA检查中心 '+r.tp+'/'+(r.tp+r.fn)+
'；背景误报 '+r.fp+'/'+(r.fp+r.tn)+'；运行秒数 '+r.seconds.toFixed(2);}
for(const e of document.querySelectorAll('select,input'))e.addEventListener('input',update);
el('mode').value='combined';update();</script></html>"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.spec, args.output)
