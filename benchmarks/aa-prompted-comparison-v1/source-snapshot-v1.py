"""Compare equal-budget local AA prompts on previously observed, human-labeled centers.

Run: python -m silicon_eye.aa_prompted_eval --root . --spec SPEC --output NEW_DIR
Requires optional segmentation-eval dependencies. This is development evidence,
not blind validation. Prompt neighborhoods are AI assumptions, centers are human-reviewed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from .aa_segmentation_eval import annotation_mask, image_features, sparse_metrics, write_image
from .geometry_reconstruction import digest
from .scene_geometry import load_locked


def check_labels(case):
    """Score only reviewed check centers, never the sampled prompt neighborhoods."""
    left, top, right, bottom = case["native_bbox"]
    labels = np.full((bottom - top, right - left), -1, np.int8)
    for item in case["checks"]:
        x, y = item["native_xy"]
        if not left <= x < right or not top <= y < bottom:
            raise ValueError("Check center outside crop")
        for prompt in case["prompts"]:
            px, py = prompt["native_xy"]
            radius = prompt["radius"]
            if abs(x - px) <= radius and abs(y - py) <= radius:
                raise ValueError("Check overlaps prompt neighborhood")
        labels[y - top, x - left] = int(item["class_name"] == "AA")
    return labels


def local_masks(raw, case, settings):
    from sklearn.ensemble import RandomForestClassifier

    sample_labels = annotation_mask(
        dict(native_bbox=case["native_bbox"], annotations=case["prompts"])
    )
    selected = sample_labels >= 0
    feats = image_features(raw, settings["feature_sigmas"])
    targets = sample_labels[selected]
    if min(np.count_nonzero(targets == c) for c in [0, 1]) < 5:
        raise ValueError("GMM needs at least five color observations per class")
    forest = RandomForestClassifier(
        n_estimators=settings["forest_trees"],
        max_depth=settings["forest_max_depth"],
        class_weight="balanced_subsample",
        min_samples_leaf=1,
        random_state=settings["seed"],
        n_jobs=2,
    )
    forest.fit(feats[selected], targets)
    result = dict(
        local_rf=forest.predict(feats.reshape(-1, feats.shape[-1])).reshape(raw.shape[:2]) == 1
    )
    colors = raw[selected]
    palette = np.where(targets == 1, cv2.GC_FGD, cv2.GC_BGD).astype(np.uint8).reshape(-1, 1)
    bg, fg = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.setRNGSeed(settings["seed"])
    cv2.grabCut(colors.reshape(-1, 1, 3), palette, None, bg, fg, 1, cv2.GC_INIT_WITH_MASK)
    # Every pixel starts probable background; the local color likelihood and edges
    # decide the split. Only human-reviewed prompt centers are hard constraints.
    left, top, _, _ = case["native_bbox"]
    for name, mode, iterations in [
        ("local_gc_fixed", cv2.GC_EVAL_FREEZE_MODEL, 1),
        ("local_gc_refine", cv2.GC_EVAL, settings["grabcut_iterations"]),
    ]:
        labels = np.full(raw.shape[:2], cv2.GC_PR_BGD, np.uint8)
        if name == "local_gc_refine" and settings.get("refine_from_fixed", False):
            labels[result["local_gc_fixed"]] = cv2.GC_PR_FGD
        for item in case["prompts"]:
            x, y = item["native_xy"]
            labels[y - top, x - left] = cv2.GC_FGD if item["class_name"] == "AA" else cv2.GC_BGD
        cv2.grabCut(raw, labels, None, bg.copy(), fg.copy(), iterations, mode)
        result[name] = np.isin(labels, [cv2.GC_FGD, cv2.GC_PR_FGD])
    return result, sample_labels


def run(root, spec_path, output):
    root, spec_path, output = (
        Path(root).resolve(),
        Path(spec_path).resolve(),
        Path(output).resolve(),
    )
    if output.exists():
        raise ValueError("Use a new directory")
    spec = json.loads(spec_path.read_text())
    review = load_locked(root, spec["human_review"])
    load_locked(root, spec["baseline_report"])
    manifest = {v["path"]: v["sha256"] for v in load_locked(root, spec["baseline_manifest"])}
    approved = {
        (c["id"], tuple(a["native_xy"]), a["class_name"])
        for c in review["cases"]
        for a in c["approved_centers"]
    }
    source = (root / spec["source"]["path"]).resolve()
    if not source.is_relative_to(root) or digest(source) != spec["source"]["sha256"]:
        raise ValueError("Changed source photograph")
    raw = cv2.imread(str(source))
    results = []
    output.mkdir(parents=True)
    cv2.setNumThreads(2)
    for case in spec["cases"]:
        for item in case["prompts"] + case["checks"]:
            if (case["id"], tuple(item["native_xy"]), item["class_name"]) not in approved:
                raise ValueError("Center not covered by human review")
        checks = check_labels(case)
        x, y, right, bottom = case["native_bbox"]
        photo = raw[y:bottom, x:right].copy()
        masks, seeds = local_masks(photo, case, spec["settings"])
        valid_path = root / spec["baseline_run"] / case["id"] / "valid.png"
        if digest(valid_path) != manifest[f"{case['id']}/valid.png"]:
            raise ValueError("Changed baseline validity mask")
        valid = cv2.imread(str(valid_path), 0) > 0
        baselines = {}
        for original, key in [
            ("adaptive", "before_adaptive"),
            ("random_forest", "before_rf"),
            ("grabcut_frozen_gmm", "before_grabcut"),
        ]:
            relative = f"{case['id']}/{original}-mask.png"
            path = root / spec["baseline_run"] / relative
            if digest(path) != manifest[relative]:
                raise ValueError("Changed baseline mask")
            baselines[key] = cv2.imread(str(path), 0) > 0
        masks = {**baselines, **masks}
        out = output / case["id"]
        out.mkdir()
        write_image(out / "raw.png", photo)
        markers = photo.copy()
        for index, item in enumerate(case["prompts"] + case["checks"], 1):
            px, py = item["native_xy"]
            color = (0, 0, 255) if item["class_name"] == "AA" else (255, 140, 0)
            cv2.circle(markers, (px - x, py - y), 7, color, 1)
            cv2.putText(
                markers, str(index), (px - x + 9, py - y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1
            )
        write_image(out / "centers.png", markers)
        prompt_view = photo.copy()
        prompt_view[seeds == 1] = [0, 0, 255]
        prompt_view[seeds == 0] = [255, 140, 0]
        write_image(out / "prompts.png", prompt_view)
        np.save(out / "check-centers.npy", checks)
        np.save(out / "sample-labels.npy", seeds)
        for method, mask in masks.items():
            mask = mask & valid
            write_image(out / f"{method}-mask.png", mask.astype(np.uint8) * 255)
            overlay = photo.copy()
            overlay[mask] = (0.5 * photo[mask] + 0.5 * np.array([50, 230, 80])).astype(np.uint8)
            write_image(out / f"{method}-overlay.png", overlay)
            metric = sparse_metrics(mask, checks)
            metric["scope"] = "human_confirmed_nonprompt_centers_only"
            results.append(dict(case=case["id"], method=method, **metric))
    summary = []
    for method in masks:
        rows = [v for v in results if v["method"] == method]
        summary.append(
            dict(
                method=method,
                AA_hit=sum(v["tp"] for v in rows),
                AA_total=sum(v["tp"] + v["fn"] for v in rows),
                background_false_positive=sum(v["fp"] for v in rows),
                background_total=sum(v["fp"] + v["tn"] for v in rows),
            )
        )
    report = dict(
        status="prompted_development_comparison_not_blind_validation",
        results=results,
        summary=summary,
        source_sha256=digest(source),
        code_sha256=digest(__file__),
        spec_sha256=digest(spec_path),
        human_review=spec["human_review"],
        prompt_budget_per_case=dict(AA_centers=2, background_centers=1),
        neighborhood_sampling=(
            "AA radius3/background radius1 is AI assumption, not human pixel truth"
        ),
        full_mask_accepted=False,
        geometry_processed=False,
        CT_processed=False,
    )
    for name, data in [("report.json", report), ("spec.json", spec)]:
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    data = dict(
        cases=[dict(id=c["id"], name=c["name"]) for c in spec["cases"]],
        summary=summary,
        results=results,
    )
    (output / "data.js").write_text("const DATA=" + json.dumps(data, ensure_ascii=False) + ";\n")
    (output / "index.html").write_text(PAGE)
    if digest(source) != spec["source"]["sha256"]:
        raise ValueError("Source changed")
    entries = [
        dict(path=str(p.relative_to(output)), sha256=digest(p))
        for p in sorted(output.rglob("*"))
        if p.is_file()
    ]
    (output / "manifest.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
    return report


PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>AA 少量局部提示对照</title>
<style>body{background:#14212b;color:#eef6fa;font:17px/1.6 sans-serif;margin:20px}
a{color:#7df}select{font:inherit}.pair{display:flex;gap:12px}figure{width:50%;margin:0}
img{width:100%}td,th{border:1px solid #678;padding:6px}table{border-collapse:collapse}</style>
<h1>AA 少量局部提示实验</h1>
<p>每窗只给2个AA中心、1个背景中心；剩余6个人工确认中心用于检查。
训练采样邻域为AI假设，不是人确认的整块mask。本轮为已知案例开发实验，不是独立盲测。</p>
<select id="case"></select><select id="method"></select>
<label><input id="binary" type="checkbox">只看二值mask</label>
<label><input id="prompts" type="checkbox" checked>左图只看训练提示</label>
<div class="pair"><figure><figcaption>原图与提示／中心位置</figcaption><img id="raw"></figure>
<figure><figcaption>分割候选（绿色）</figcaption><img id="result"></figure></div><p id="score"></p>
<table><thead><tr><th>方法</th><th>8个AA检查点</th><th>4个背景点误报</th></tr></thead>
<tbody id="rows"></tbody></table>
<p>检查点不进入训练；提示中心也不计入分数。没有补环、填矩形或正交化。
点检查通过仍不表示整块边界、连续性和环结构通过。</p>
<p><a href="report.json">结果和范围</a> · <a href="spec.json">提示／检查点及参数</a></p>
<script src="data.js"></script><script>
const el=id=>document.getElementById(id),names={before_adaptive:'原自适应阈值',
before_rf:'原随机森林',before_grabcut:'原固定颜色GrabCut',local_rf:'局部提示随机森林',
local_gc_fixed:'局部提示固定颜色GrabCut',local_gc_refine:'局部提示三轮GrabCut'};
for(const c of DATA.cases){let o=document.createElement('option');o.value=c.id;
o.textContent=c.id+' '+c.name;el('case').append(o);}
for(const s of DATA.summary){let o=document.createElement('option');o.value=s.method;
o.textContent=names[s.method];el('method').append(o);let tr=document.createElement('tr');
for(const v of [names[s.method],s.AA_hit+'/'+s.AA_total,
s.background_false_positive+'/'+s.background_total]){let td=document.createElement('td');
td.textContent=v;tr.append(td);}el('rows').append(tr);}
function update(){let c=el('case').value,m=el('method').value;
el('raw').src=c+'/'+(el('prompts').checked?'prompts.png':'centers.png');
el('result').src=c+'/'+m+(el('binary').checked?'-mask.png':'-overlay.png');
const r=DATA.results.find(v=>v.case===c&&v.method===m);
el('score').textContent='本窗AA检查点 '+r.tp+'/'+(r.tp+r.fn)
+'；背景误报 '+r.fp+'/'+(r.fp+r.tn);}
for(const e of document.querySelectorAll('select,input'))e.addEventListener('input',update);
el('method').value='local_rf';update();</script></html>"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.root, args.spec, args.output)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
