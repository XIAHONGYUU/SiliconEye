"""Compare native-photo AA segmentation on a frozen spatial split, before geometry repair.

Run: python -m silicon_eye.aa_segmentation_eval --root . --spec SPEC --output NEW_DIR
Optional dependency: pip install -e '.[segmentation-eval]'. No CT or geometric completion.
Sparse AI draft evaluation labels are separate from training and are never dense truth.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import time
from pathlib import Path

import cv2
import numpy as np

from .geometry_reconstruction import digest


def annotation_mask(case):
    """Only explicit scribbles are labels; all unmarked pixels remain unknown (-1)."""
    left, top, right, bottom = case["native_bbox"]
    result = np.full((bottom - top, right - left), -1, np.int8)
    for item in case["annotations"]:
        x, y = item["native_xy"]
        radius = item["radius"]
        x0, x1 = x - left - radius, x - left + radius + 1
        y0, y1 = y - top - radius, y - top + radius + 1
        if min(x0, y0) < 0 or x1 > result.shape[1] or y1 > result.shape[0]:
            raise ValueError("Annotation outside its native crop")
        value = int(item["class_name"] == "AA")
        previous = result[y0:y1, x0:x1]
        if np.any((previous >= 0) & (previous != value)):
            raise ValueError("Conflicting sparse annotation")
        result[y0:y1, x0:x1] = value
    return result


def image_features(raw, sigmas):
    """Color, intensity, edges and local texture; no geometry or source coordinates."""
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    lab = cv2.cvtColor(raw, cv2.COLOR_BGR2LAB).astype(np.float32) / 255
    arrays = [lab[:, :, i] for i in range(3)]
    for sigma in sigmas:
        mean = cv2.GaussianBlur(gray, (0, 0), sigma)
        variance = np.maximum(0, cv2.GaussianBlur(gray * gray, (0, 0), sigma) - mean * mean)
        gx = cv2.Sobel(mean, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(mean, cv2.CV_32F, 0, 1, ksize=3)
        arrays.extend([mean, np.sqrt(variance), cv2.magnitude(gx, gy)])
    return np.stack(arrays, axis=-1).astype(np.float32)


def training_rows(cases, photos, settings):
    rng = np.random.default_rng(settings["seed"])
    xs, ys, colors = [], [], []
    for case in cases:
        if case["split"] != "train":
            continue
        labels = annotation_mask(case)
        selected = labels >= 0
        xs.append(image_features(photos[case["id"]], settings["feature_sigmas"])[selected])
        ys.append(labels[selected])
        colors.append(photos[case["id"]][selected])
    features, labels, colors = np.concatenate(xs), np.concatenate(ys), np.concatenate(colors)
    indices = []
    for category in [0, 1]:
        ids = np.flatnonzero(labels == category)
        if len(ids) < 20:
            raise ValueError("Insufficient independent foreground/background seeds")
        indices.extend(
            rng.choice(ids, min(len(ids), settings["max_training_pixels_per_class"]), replace=False)
        )
    indices = np.array(indices)
    return features[indices], labels[indices], colors[indices]


def threshold_masks(raw, settings):
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (0, 0), settings["blur_sigma"])
    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        settings["adaptive_block"],
        settings["adaptive_c"],
    )
    field = cv2.GaussianBlur(blur, (0, 0), settings["illumination_sigma"]).astype(np.float32)
    corrected = np.clip(blur.astype(np.float32) - field + 128, 0, 255).astype(np.uint8)
    _, corrected_mask = cv2.threshold(corrected, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return dict(
        fixed156=blur > 156, otsu=otsu > 0, adaptive=adaptive > 0, corrected_otsu=corrected_mask > 0
    )


def sparse_metrics(mask, labels):
    positive = labels == 1
    negative = labels == 0
    tp = int(np.count_nonzero(mask & positive))
    fn = int(np.count_nonzero(~mask & positive))
    fp = int(np.count_nonzero(mask & negative))
    tn = int(np.count_nonzero(~mask & negative))
    recall = tp / (tp + fn) if tp + fn else None
    fpr = fp / (fp + tn) if fp + tn else None
    return dict(
        tp=tp,
        fn=fn,
        fp=fp,
        tn=tn,
        AA_recall=recall,
        background_false_positive=fpr,
        balanced_accuracy=(recall + 1 - fpr) / 2
        if recall is not None and fpr is not None
        else None,
        scope="sparse_AI_draft_labels_only_not_full_frame_accuracy",
    )


def write_image(path, image):
    if not cv2.imwrite(str(path), image):
        raise OSError("Could not write " + str(path))


def run(root, spec_path, output):
    from sklearn.ensemble import RandomForestClassifier

    root, spec_path, output = (
        Path(root).resolve(),
        Path(spec_path).resolve(),
        Path(output).resolve(),
    )
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(spec_path.read_text())
    source = (root / spec["source"]["path"]).resolve()
    if not source.is_relative_to(root) or digest(source) != spec["source"]["sha256"]:
        raise ValueError("Changed or external source photograph")
    original = cv2.imread(str(source))
    cases = spec["cases"]
    settings = spec["settings"]
    photos = {}
    for case in cases:
        x, y, right, bottom = case["native_bbox"]
        photos[case["id"]] = original[y:bottom, x:right].copy()
    features, labels, colors = training_rows(cases, photos, settings)
    cv2.setRNGSeed(settings["seed"])
    cv2.setNumThreads(2)
    started = time.perf_counter()
    forest = RandomForestClassifier(
        n_estimators=settings["forest_trees"],
        max_depth=settings["forest_max_depth"],
        min_samples_leaf=3,
        random_state=settings["seed"],
        n_jobs=2,
    )
    forest.fit(features, labels)
    forest_training = time.perf_counter() - started
    bg_model, fg_model = np.zeros((1, 65)), np.zeros((1, 65))
    palette_labels = np.where(labels == 1, cv2.GC_FGD, cv2.GC_BGD).astype(np.uint8).reshape(-1, 1)
    started = time.perf_counter()
    cv2.grabCut(
        colors.reshape(-1, 1, 3), palette_labels, None, bg_model, fg_model, 1, cv2.GC_INIT_WITH_MASK
    )
    gc_training = time.perf_counter() - started
    output.mkdir(parents=True)
    results = []
    times = []
    for case in cases:
        identifier = case["id"]
        raw = photos[identifier]
        case_out = output / identifier
        case_out.mkdir()
        write_image(case_out / "raw.png", raw)
        labels_case = annotation_mask(case)
        marks = raw.copy()
        marks[labels_case == 1] = [0, 0, 255]
        marks[labels_case == 0] = [255, 120, 0]
        write_image(case_out / "annotations.png", marks)
        np.save(case_out / "sparse-labels.npy", labels_case)
        started = time.perf_counter()
        masks = threshold_masks(raw, settings)
        threshold_time = time.perf_counter() - started
        for method in masks:
            times.append(
                dict(
                    case=identifier,
                    method=method,
                    seconds=threshold_time,
                    timing_scope="all_four_threshold_variants_together",
                )
            )
        started = time.perf_counter()
        feats = image_features(raw, settings["feature_sigmas"])
        masks["random_forest"] = (
            forest.predict(feats.reshape(-1, feats.shape[-1])).reshape(raw.shape[:2]) == 1
        )
        times.append(
            dict(case=identifier, method="random_forest", seconds=time.perf_counter() - started)
        )
        for method, mode, iterations in [
            ("grabcut_frozen_gmm", cv2.GC_EVAL_FREEZE_MODEL, 1),
            ("grabcut", cv2.GC_EVAL, settings["grabcut_refine_iterations"]),
        ]:
            gc = np.where(masks["otsu"], cv2.GC_PR_FGD, cv2.GC_PR_BGD).astype(np.uint8)
            if case["split"] == "train":
                gc[labels_case == 1] = cv2.GC_FGD
                gc[labels_case == 0] = cv2.GC_BGD
            started = time.perf_counter()
            cv2.grabCut(raw, gc, None, bg_model.copy(), fg_model.copy(), iterations, mode)
            masks[method] = np.isin(gc, [cv2.GC_FGD, cv2.GC_PR_FGD])
            times.append(
                dict(case=identifier, method=method, seconds=time.perf_counter() - started)
            )
        valid = np.ones(raw.shape[:2], bool)
        left, top, _, _ = case["native_bbox"]
        for x0, y0, x1, y1 in spec.get("excluded_native_boxes", []):
            a, b = max(0, x0 - left), max(0, y0 - top)
            right, bottom = min(raw.shape[1], x1 - left), min(raw.shape[0], y1 - top)
            if right > a and bottom > b:
                valid[b:bottom, a:right] = False
        if np.any((labels_case >= 0) & ~valid):
            raise ValueError("Annotation intersects excluded screenshot artifact")
        write_image(case_out / "valid.png", valid.astype(np.uint8) * 255)
        for method, mask in masks.items():
            mask = mask & valid
            write_image(case_out / f"{method}-mask.png", mask.astype(np.uint8) * 255)
            overlay = raw.copy()
            overlay[mask] = (0.5 * raw[mask] + 0.5 * np.array([50, 230, 80])).astype(np.uint8)
            write_image(case_out / f"{method}-overlay.png", overlay)
            results.append(
                dict(
                    case=identifier,
                    method=method,
                    split=case["split"],
                    **sparse_metrics(mask, labels_case),
                )
            )
    methods = list(masks)
    summary = []
    for method in methods:
        held = [v for v in results if v["method"] == method and v["split"] == "holdout"]
        summary.append(
            dict(
                method=method,
                macro_sparse_balanced_accuracy=float(
                    np.mean([v["balanced_accuracy"] for v in held])
                ),
                macro_AA_recall=float(np.mean([v["AA_recall"] for v in held])),
                macro_background_false_positive=float(
                    np.mean([v["background_false_positive"] for v in held])
                ),
                prediction_seconds=sum(v["seconds"] for v in times if v["method"] == method),
            )
        )
    summary.sort(key=lambda s: s["macro_sparse_balanced_accuracy"], reverse=True)
    report = dict(
        schema_version=1,
        status="exploratory_AI_label_comparison_not_human_validated_accuracy",
        spec_sha256=digest(spec_path),
        code_sha256=digest(__file__),
        source_sha256=digest(source),
        training_cases=[v["id"] for v in cases if v["split"] == "train"],
        holdout_cases=[v["id"] for v in cases if v["split"] == "holdout"],
        training_pixels=int(len(labels)),
        summary=summary,
        results=results,
        times=times,
        training_seconds=dict(random_forest=forest_training, grabcut_GMM=gc_training),
        limitations=[
            "AI sparse scribbles not human pixel truth",
            "same development chip spatial split",
            "no full-mask IoU/recall or global topology completeness measured",
            "training panel GrabCut uses hard seeds; only heldout panels enter ranking",
            "threshold time repeats combined time, not an individual threshold benchmark",
            "no geometry completion or changes to accepted reconstruction",
        ],
        versions={
            name: importlib.metadata.version(name)
            for name in ["numpy", "opencv-python", "scikit-learn"]
        },
    )
    for name, value in [("report.json", report), ("spec.json", spec)]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    data = dict(
        cases=[dict(id=c["id"], name=c["name"], split=c["split"]) for c in cases],
        methods=methods,
        summary=summary,
        results=results,
    )
    (output / "data.js").write_text("const DATA=" + json.dumps(data, ensure_ascii=False) + ";\n")
    (output / "index.html").write_text(PAGE)
    if digest(source) != spec["source"]["sha256"]:
        raise ValueError("Source mutated during experiment")
    manifest = [
        dict(path=str(p.relative_to(output)), sha256=digest(p))
        for p in sorted(output.rglob("*"))
        if p.is_file()
    ]
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return report


PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>AA 算法原图对照</title>
<style>body{font:17px/1.6 sans-serif;background:#14212b;color:#edf5fa;margin:20px}
a{color:#7df}select{font:inherit;margin:8px}.pair{display:flex;gap:12px}
figure{width:50%;margin:0}img{width:100%;image-rendering:auto}table{border-collapse:collapse}
td,th{padding:6px;border:1px solid #678}</style>
<h1>AA 原始分割算法对照</h1>
<p>仅比较照片分割，不补环、不填矩形、不正交化。四个训练窗口、四个检查窗口。</p>
<p>红色标记为 AA，蓝色为背景。标记由 AI 根据原图拟定，未经人工像素验收；
所有分数仅适用于这些稀疏标记，不能理解为全幅准确率。</p>
<select id="case"></select><select id="method"></select>
<label><input id="marks" type="checkbox" checked>左图显示标签</label>
<label><input id="binary" type="checkbox">右图仅二值分割</label>
<p id="caption"></p><div class="pair"><figure><figcaption>原图／稀疏标签</figcaption>
<img id="raw"></figure><figure><figcaption>分割结果（绿色）</figcaption>
<img id="result"></figure></div>
<p id="score"></p><h2>检查区结果：AI 稀疏标记，不是人工准确率</h2>
<table><thead><tr><th>方法</th><th>稀疏平衡正确率</th><th>AA 检出</th><th>背景误报</th></tr></thead>
<tbody id="rows"></tbody></table>
<p><a href="spec.json">冻结样本／标签／参数</a> · <a href="report.json">逐项结果与限制</a></p>
<script src="data.js"></script><script>
const el=id=>document.getElementById(id);
const names={fixed156:'旧固定阈值 156',otsu:'Otsu 阈值',adaptive:'自适应阈值',
corrected_otsu:'光照校正＋Otsu',random_forest:'颜色／纹理随机森林',
grabcut_frozen_gmm:'GrabCut 固定颜色模型',grabcut:'GrabCut 三轮细化'};
for(const c of DATA.cases){let o=document.createElement('option');o.value=c.id;
o.textContent=c.id+' '+c.name+' '+(c.split==='train'?'训练区':'检查区');el('case').append(o);}
for(const m of DATA.methods){let o=document.createElement('option');o.value=m;
o.textContent=names[m];el('method').append(o);}
function pct(x){return (100*x).toFixed(1)+'%';}
for(const s of DATA.summary){let tr=document.createElement('tr');
for(const v of [names[s.method],pct(s.macro_sparse_balanced_accuracy),
pct(s.macro_AA_recall),pct(s.macro_background_false_positive)]){
let td=document.createElement('td');td.textContent=v;tr.append(td);}el('rows').append(tr);}
function update(){const c=el('case').value,m=el('method').value;
el('raw').src=c+'/'+(el('marks').checked?'annotations.png':'raw.png');
el('result').src=c+'/'+m+(el('binary').checked?'-mask.png':'-overlay.png');
const r=DATA.results.find(r=>r.case===c&&r.method===m);
el('caption').textContent=r.split==='train'?'训练区：分数不进入比较结论。'
:'空间保留检查区：标签未用于训练；仍来自同一颗开发芯片。';
el('score').textContent='本窗口稀疏标记：AA 检出 '+pct(r.AA_recall)
+'；背景误报 '+pct(r.background_false_positive);}
for(const e of document.querySelectorAll('select,input'))e.addEventListener('input',update);
el('method').value='random_forest';el('case').value='S02';update();
</script></html>"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.root, args.spec, args.output)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
