"""Build one native AA candidate canvas with scoped provenance and review tiles.

Run: python -m silicon_eye.aa_native_canvas --root . --spec SPEC --output NEW_DIR
Requires segmentation-eval extras. Full-frame inference is an unaccepted model baseline;
local reviewed-context candidates retain unknowns. Tiles are review views, not separate layers.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from .aa_segmentation_eval import image_features, write_image
from .geometry_reconstruction import digest
from .scene_geometry import load_locked


def probabilities_to_states(probability, low, high):
    if not 0 <= low < high <= 1:
        raise ValueError("Invalid probability thresholds")
    states = np.full(probability.shape, -1, np.int8)
    states[probability <= low] = 0
    states[probability >= high] = 1
    return states


def review_grid(bbox, columns, rows, prefix):
    x, y, r, b = bbox
    xx = np.rint(np.linspace(x, r, columns + 1)).astype(int)
    yy = np.rint(np.linspace(y, b, rows + 1)).astype(int)
    return [
        dict(
            id=f"{prefix}{j * columns + i + 1:02d}",
            native_bbox=[int(xx[i]), int(yy[j]), int(xx[i + 1]), int(yy[j + 1])],
        )
        for j in range(rows)
        for i in range(columns)
    ]


def place_local(canvas, domain_seen, conflict, contributors, local, domain, bbox, bit):
    """Local peers cannot outvote a contradiction or erase explicit unknown boundaries."""
    x, y, r, b = bbox
    if local.shape != (b - y, r - x) or domain.shape != local.shape:
        raise ValueError("Local array shape/bbox mismatch")
    if not set(np.unique(local)) <= {-1, 0, 1}:
        raise ValueError("Invalid material states")
    view = canvas[y:b, x:r]
    seen = domain_seen[y:b, x:r]
    flags = conflict[y:b, x:r]
    overlap = seen & domain
    flags |= overlap & (view >= 0) & (local >= 0) & (view != local)
    new = domain & ~seen
    view[new] = local[new]
    incompatible = overlap & ((view != local) | (view < 0) | (local < 0))
    view[incompatible] = -1
    seen |= domain
    contributors[y:b, x:r][domain] |= bit


def strip_probabilities(photo, model, settings):
    """Compute globally consistent neighborhoods; strip boundaries are not material edges."""
    height, width = photo.shape[:2]
    halo = settings["halo"]
    step = settings["strip_height"]
    probability = np.empty((height, width), np.float32)
    for top in range(0, height, step):
        bottom = min(height, top + step)
        a = max(0, top - halo)
        b = min(height, bottom + halo)
        features = image_features(photo[a:b], settings["feature_sigmas"])
        features = features[top - a : bottom - a]
        probability[top:bottom] = model.predict_proba(features.reshape(-1, features.shape[-1]))[
            :, 1
        ].reshape(bottom - top, width)
        print(f"native inference rows {top}:{bottom}/{height}", flush=True)
    return probability


def render(raw, states, valid, mode, local_domain=None, conflict=None, adaptive=None):
    result = raw.copy()
    if mode == "AA":
        layers = [(states == 1, [70, 220, 90])]
    elif mode == "states":
        layers = [(states == 1, [70, 220, 90]), (states == 0, [220, 120, 20])]
    elif mode == "unknown":
        layers = [((states < 0) & valid, [220, 210, 70])]
    elif mode == "local":
        layers = [(local_domain, [210, 180, 50])]
    elif mode == "conflict":
        layers = [(conflict, [180, 30, 240])]
    elif mode == "adaptive":
        layers = [(adaptive & valid, [70, 220, 90])]
    else:
        raise ValueError("Unknown view")
    for selected, color in layers:
        result[selected] = (raw[selected] * 0.55 + np.array(color) * 0.45).astype(np.uint8)
    return result


def run(root, spec_path, output):
    from sklearn.ensemble import RandomForestClassifier

    root, spec_path, output = Path(root).resolve(), Path(spec_path).resolve(), Path(output)
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(spec_path.read_text())
    settings = spec["settings"]
    load_locked(root, spec["training_review"])
    path = root / spec["source"]["path"]
    if digest(path) != spec["source"]["sha256"]:
        raise ValueError("Changed source")
    photo = cv2.imread(str(path))
    height, width = photo.shape[:2]
    if [width, height] != spec["canvas_wh"]:
        raise ValueError("Canvas/source mismatch")
    cv2.setNumThreads(2)
    output.mkdir(parents=True)
    features = []
    targets = []
    halo = settings["halo"]
    for case in spec["training"]:
        p = root / case["labels"]["path"]
        if digest(p) != case["labels"]["sha256"]:
            raise ValueError("Changed training labels")
        labels = np.load(p)
        x, y, r, b = case["native_bbox"]
        a, c = max(0, x - halo), max(0, y - halo)
        right, bottom = min(width, r + halo), min(height, b + halo)
        f = image_features(photo[c:bottom, a:right], settings["feature_sigmas"])[
            y - c : b - c, x - a : r - a
        ]
        if labels.shape != f.shape[:2]:
            raise ValueError("Training frame mismatch")
        selected = labels >= 0
        features.append(f[selected])
        targets.append(labels[selected])
    features = np.concatenate(features)
    targets = np.concatenate(targets)
    rng = np.random.default_rng(settings["seed"])
    ids = []
    for value in [0, 1]:
        choices = np.flatnonzero(targets == value)
        ids.extend(
            rng.choice(
                choices, min(len(choices), settings["max_training_pixels_per_class"]), replace=False
            )
        )
    model = RandomForestClassifier(
        n_estimators=settings["forest_trees"],
        max_depth=settings["forest_max_depth"],
        min_samples_leaf=settings["min_samples_leaf"],
        class_weight="balanced_subsample",
        random_state=settings["seed"],
        n_jobs=2,
    )
    model.fit(features[ids], targets[ids])
    probability = strip_probabilities(photo, model, settings)
    np.save(output / "global-AA-probability.npy", probability)
    global_states = probabilities_to_states(
        probability, settings["non_AA_threshold"], settings["AA_threshold"]
    )
    valid = np.zeros((height, width), bool)
    x, y, r, b = spec["source_valid_bbox"]
    valid[y:b, x:r] = True
    for x, y, r, b in spec["excluded_native_boxes"]:
        valid[y:b, x:r] = False
    global_states[~valid] = -1
    np.save(output / "global-model-states.npy", global_states)
    canvas = global_states.copy()
    seen = np.zeros_like(valid)
    conflict = np.zeros_like(valid)
    contributors = np.zeros((height, width), np.uint16)
    placements = []
    for i, local in enumerate(spec["local_candidates"]):
        load_locked(root, local["human_review"])
        for key in ["states", "domain"]:
            p = root / local[key]["path"]
            if digest(p) != local[key]["sha256"]:
                raise ValueError("Changed local candidate")
        states = np.load(root / local["states"]["path"])
        domain = cv2.imread(str(root / local["domain"]["path"]), 0) > 0
        x, y, r, b = local["native_bbox"]
        domain &= valid[y:b, x:r]
        before = global_states[y:b, x:r]
        disagreement = domain & (states >= 0) & (before >= 0) & (states != before)
        # Tier difference is explicit, not a vote: local context candidate is preferred.
        conflict[y:b, x:r] |= disagreement
        place_local(
            canvas, seen, conflict, contributors, states, domain, local["native_bbox"], 1 << i
        )
        placements.append(
            dict(
                id=local["id"],
                native_bbox=local["native_bbox"],
                local_to_native=[[1, 0, x], [0, 1, y], [0, 0, 1]],
                processed_pixels=int(domain.sum()),
                global_model_disagreement_pixels=int(disagreement.sum()),
                review_scope=local["scope"],
            )
        )
    canvas[~valid] = -1
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (0, 0), settings["blur_sigma"])
    adaptive = (
        cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            settings["adaptive_block"],
            settings["adaptive_c"],
        )
        > 0
    )
    adaptive_disagreement = valid & (global_states >= 0) & ((global_states == 1) != adaptive)
    np.save(output / "states.npy", canvas)
    np.save(output / "local-contributors.npy", contributors)
    for name, mask in [
        ("processing-domain", valid),
        ("local-context-domain", seen),
        ("candidate-conflicts", conflict),
        ("adaptive-disagreement", adaptive_disagreement),
        ("AA-candidate", canvas == 1),
    ]:
        write_image(output / (name + ".png"), mask.astype(np.uint8) * 255)
    tiles = review_grid(spec["source_valid_bbox"], **spec["grid"])
    margin = settings["context_margin"]
    for tile in tiles:
        x, y, r, b = tile["native_bbox"]
        a, c = max(0, x - margin), max(0, y - margin)
        right, bottom = min(width, r + margin), min(height, b + margin)
        box = (slice(c, bottom), slice(a, right))
        raw = photo[box]
        state = canvas[box]
        v = valid[box]
        out = output / tile["id"]
        out.mkdir()
        source_view = raw.copy()
        cv2.rectangle(source_view, (x - a, y - c), (r - a - 1, b - c - 1), (255, 255, 255), 2)
        write_image(out / "raw.jpg", source_view)
        for mode in ["AA", "states", "unknown", "local", "conflict", "adaptive"]:
            view = render(raw, state, v, mode, seen[box], conflict[box], adaptive[box])
            cv2.rectangle(view, (x - a, y - c), (r - a - 1, b - c - 1), (255, 255, 255), 2)
            write_image(out / (mode + ".jpg"), view)
        core = (slice(y, b), slice(x, r))
        values = canvas[core]
        vv = valid[core]
        ll = seen[core]
        tile.update(
            context_native_bbox=[a, c, right, bottom],
            stats=dict(
                valid_pixels=int(vv.sum()),
                candidate_AA_pixels=int(((values == 1) & vv).sum()),
                candidate_non_AA_pixels=int(((values == 0) & vv).sum()),
                unknown_pixels=int(((values < 0) & vv).sum()),
                local_context_pixels=int(ll.sum()),
                conflict_pixels=int(conflict[core].sum()),
                adaptive_disagreement_pixels=int(adaptive_disagreement[core].sum()),
            ),
            human_review_status="not_reviewed_as_a_whole_tile",
        )
    # Overview uses nearest-neighbor labels; no coordinate transformations enter data arrays.
    small = cv2.resize(photo, (1600, round(height * 1600 / width)), interpolation=cv2.INTER_AREA)
    ss = cv2.resize(canvas, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
    sv = cv2.resize(valid.astype(np.uint8), small.shape[1::-1], interpolation=cv2.INTER_NEAREST) > 0
    overview = render(small, ss, sv, "AA")
    sx, sy = small.shape[1] / width, small.shape[0] / height
    for tile in tiles:
        x, y, r, b = tile["native_bbox"]
        cv2.rectangle(
            overview,
            (round(x * sx), round(y * sy)),
            (round(r * sx) - 1, round(b * sy) - 1),
            (255, 210, 80),
            1,
        )
        cv2.putText(
            overview,
            tile["id"],
            (round(x * sx) + 8, round(y * sy) + 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            4,
        )
        cv2.putText(
            overview,
            tile["id"],
            (round(x * sx) + 8, round(y * sy) + 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            1,
        )
    write_image(output / "overview.jpg", overview)
    report = dict(
        status="full_native_candidate_not_fullframe_acceptance",
        canvas_wh=[width, height],
        source_sha256=digest(path),
        spec_sha256=digest(spec_path),
        code_sha256=digest(__file__),
        feature_code_sha256=digest(Path(__file__).with_name("aa_segmentation_eval.py")),
        training_pixels_per_class={str(v): int((targets[ids] == v).sum()) for v in [0, 1]},
        placements=placements,
        tiles=tiles,
        valid_pixels=int(valid.sum()),
        AA_pixels=int(((canvas == 1) & valid).sum()),
        non_AA_pixels=int(((canvas == 0) & valid).sum()),
        unknown_pixels=int(((canvas < 0) & valid).sum()),
        local_context_pixels=int(seen.sum()),
        conflict_pixels=int(conflict.sum()),
        full_frame_human_accepted=False,
        note="Global probabilities are uncalibrated candidate scores. Local context candidates, "
        "including unknown boundaries, explicitly override global model within processing "
        "domains. Equal-tier local contradictions remain unknown; disagreement flags remain. "
        "Review context coverage is not dense human-reviewed pixel coverage.",
    )
    for name, data in [("report.json", report), ("spec.json", spec)]:
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (output / "data.js").write_text(
        "const DATA=" + json.dumps(dict(tiles=tiles, report=report), ensure_ascii=False) + ";\n"
    )
    (output / "review-notes.js").write_text("const REVIEW={};\n")
    (output / "index.html").write_text(PAGE)
    refresh_manifest(output)
    return report


def refresh_manifest(output):
    output = Path(output)
    entries = [
        dict(path=str(p.relative_to(output)), sha256=digest(p))
        for p in sorted(output.rglob("*"))
        if p.is_file() and p.name != "manifest.json"
    ]
    (output / "manifest.json").write_text(json.dumps(entries, indent=2) + "\n")


PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>AA全幅原生坐标分块复核</title>
<style>body{background:#14212b;color:#eee;font:18px/1.7 sans-serif;margin:20px}a{color:#7df}
select{font:inherit}.pair{display:flex;gap:14px}.pair>div{width:50%}img{width:100%}
table{border-collapse:collapse}td,th{border:1px solid #789;padding:6px}
#overview{max-width:1200px}</style>
<h1>AA全幅原生坐标候选与12块质量复核</h1>
<p>所有块来自同一states.npy，不是12个独立版图。白框内是本块，外侧96像素为上下文。
绿色＝候选AA；三态视图蓝色＝候选非AA；未知视图青色＝未知；分歧视图紫色＝候选冲突。
全图RF仅用有限局部样本训练，分数不是已校准置信度。旧局部验收不能代表整块或全图通过。</p>
<img id="overview" src="overview.jpg"><br><select id="tile"></select><select id="view">
<option value="AA">AA候选</option><option value="states">AA／非AA三态</option>
<option value="unknown">未知区</option><option value="conflict">全图／局部候选分歧</option>
<option value="local">已有局部上下文覆盖（非逐像素人审）</option>
<option value="adaptive">自适应阈值参照</option></select>
<div class="pair"><div>原图与宽上下文<img id="raw"></div>
<div>同原生坐标候选<img id="result"></div></div>
<p id="coords"></p><p id="stats"></p><p id="notes"></p>
<h2>整批复核清单</h2><table><thead><tr><th>编号</th><th>原生范围</th><th>候选AA</th>
<th>未知</th><th>AI初检（非人工结论）</th></tr></thead><tbody id="rows"></tbody></table>
<p>请按N01–N12一次反馈：合理／漏AA或漏环／误检或误连／边界问题／不清楚，并说明大致位置。
精确边界、全幅完整性和连接分别验收，不逐CT询问。已有五个局部案例不重复要求身份裁决。</p>
<p><a href="report.json">结果及来源</a> · <a href="spec.json">输入与规则</a></p>
<script src="data.js"></script><script src="review-notes.js"></script><script>
const el=id=>document.getElementById(id),pct=(n,d)=>(100*n/Math.max(1,d)).toFixed(1)+'%';
for(const t of DATA.tiles){let o=document.createElement('option');o.value=t.id;o.textContent=t.id;
el('tile').append(o);let tr=document.createElement('tr');
for(const v of [t.id,t.native_bbox.join(', '),pct(t.stats.candidate_AA_pixels,t.stats.valid_pixels),
pct(t.stats.unknown_pixels,t.stats.valid_pixels),REVIEW[t.id]?.summary||'待AI/人工复核']){
let td=document.createElement('td');td.textContent=v;tr.append(td);}el('rows').append(tr);}
function update(){let t=DATA.tiles.find(v=>v.id===el('tile').value),v=el('view').value;
el('raw').src=t.id+'/raw.jpg';el('result').src=t.id+'/'+v+'.jpg';
el('coords').textContent=t.id+' 原生范围 '+t.native_bbox.join(', ')+
'；显示上下文 '+t.context_native_bbox.join(', ');
el('stats').textContent='候选AA '+pct(t.stats.candidate_AA_pixels,t.stats.valid_pixels)+
'；未知 '+pct(t.stats.unknown_pixels,t.stats.valid_pixels)+'；局部上下文覆盖 '+
pct(t.stats.local_context_pixels,t.stats.valid_pixels)+'（非逐像素验收）';
el('notes').textContent=REVIEW[t.id]?.summary||'尚未完成本块AI/人工检查';}
for(const e of document.querySelectorAll('select'))e.addEventListener('input',update);update();
</script></html>"""

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--spec", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    run(a.root, a.spec, a.output)
