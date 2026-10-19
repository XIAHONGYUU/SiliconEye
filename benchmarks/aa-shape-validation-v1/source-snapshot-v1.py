"""Evaluate source segmentation of ring/concave AA from coarse reviewed shape priors.

Run: python -m silicon_eye.aa_shape_validation --root . --spec SPEC --output NEW_DIR
Requires segmentation-eval extras. Prior-derived seeds are AI assumptions, not dense truth.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from .aa_scribble_eval import grabcut_masks
from .aa_segmentation_eval import image_features, write_image
from .geometry_reconstruction import digest
from .scene_geometry import load_locked


def prior_samples(case, settings):
    """Respect holes and nearby islands; only a sparse subset of cores become samples."""
    x, y, r, b = case["native_bbox"]
    mask = np.zeros((b - y, r - x), np.uint8)
    for obj in case["objects"]:
        local = np.zeros_like(mask)
        points = np.array(obj["outer_native_xy"], np.int32) - [x, y]
        if np.any(points < 0) or np.any(points >= [r - x, b - y]):
            raise ValueError("Prior outside crop")
        cv2.fillPoly(local, [points], 1)
        for hole in obj["holes_native_xy"]:
            cv2.fillPoly(local, [np.array(hole, np.int32) - [x, y]], 0)
        mask |= local
    inside = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    outside = cv2.distanceTransform(1 - mask, cv2.DIST_L2, 5)
    dense = np.full(mask.shape, -1, np.int8)
    dense[inside >= settings["seed_margin"]] = 1
    dense[
        (outside >= settings["seed_margin"]) & (outside <= settings["background_outer_margin"])
    ] = 0
    samples = np.full(mask.shape, -1, np.int8)
    rng = np.random.default_rng(settings["seed"])
    for value in [0, 1]:
        ids = np.flatnonzero(dense == value)
        if len(ids) < 5:
            raise ValueError("Insufficient prior-derived samples")
        pick = rng.choice(
            ids, min(len(ids), settings["max_training_pixels_per_class"]), replace=False
        )
        samples.flat[pick] = value
    return mask.astype(bool), samples, outside <= settings["domain_margin"]


def topology(mask, significant_area):
    """Count all and significant components/holes; specks remain explicitly visible."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), connectivity=8
    )
    significant = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] >= significant_area]
    kept = np.isin(labels, significant).astype(np.uint8)
    contours, hierarchy = cv2.findContours(kept, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    holes = 0
    if hierarchy is not None:
        holes = sum(
            h[3] >= 0 and cv2.contourArea(c) >= significant_area
            for c, h in zip(contours, hierarchy[0], strict=True)
        )
    return dict(
        components=len(significant),
        holes=int(holes),
        small_components=(count - 1 - len(significant)),
    )


def scoped_topology(mask, domain, prior, significant_area):
    """Separate anchored target pieces from clipped, unmodeled boundary components."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    boundary = domain & cv2.dilate((~domain).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(
        bool
    )
    boundary[0] |= domain[0]
    boundary[-1] |= domain[-1]
    boundary[:, 0] |= domain[:, 0]
    boundary[:, -1] |= domain[:, -1]
    targets, clipped, interior = [], [], []
    for i in range(1, count):
        if stats[i, cv2.CC_STAT_AREA] < significant_area:
            continue
        component = labels == i
        if np.count_nonzero(component & prior) >= significant_area:
            targets.append(i)
        elif np.any(component & boundary):
            clipped.append(i)
        else:
            interior.append(i)
    return dict(
        target=topology(np.isin(labels, targets), significant_area),
        clipped_unmodeled_components=len(clipped),
        unexplained_interior_components=len(interior),
    )


def candidate_states(mask, domain, uncertainty):
    """Boundary uncertainty and unprocessed area are distinct from candidate non-AA."""
    inside = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 5)
    outside = cv2.distanceTransform((~mask).astype(np.uint8), cv2.DIST_L2, 5)
    states = np.full(mask.shape, -1, np.int8)
    states[(inside > uncertainty) & domain] = 1
    states[(outside > uncertainty) & domain] = 0
    return states


def run(root, spec_path, output):
    from sklearn.ensemble import RandomForestClassifier

    root, spec_path, output = Path(root).resolve(), Path(spec_path).resolve(), Path(output)
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(spec_path.read_text())
    settings = spec["settings"]
    load_locked(root, spec["prior_spec"])
    load_locked(root, spec["prior_structure_review"])
    path = root / spec["source"]["path"]
    if digest(path) != spec["source"]["sha256"]:
        raise ValueError("Changed source")
    photo = cv2.imread(str(path))
    cv2.setNumThreads(2)
    output.mkdir(parents=True)
    rows = []
    for case in spec["cases"]:
        x, y, r, b = case["native_bbox"]
        raw = photo[y:b, x:r].copy()
        prior, samples, domain = prior_samples(case, settings)
        selected = samples >= 0
        features = image_features(raw, settings["feature_sigmas"])
        forest = RandomForestClassifier(
            n_estimators=settings["forest_trees"],
            max_depth=settings["forest_max_depth"],
            min_samples_leaf=3,
            class_weight="balanced_subsample",
            random_state=settings["seed"],
            n_jobs=2,
        )
        forest.fit(features[selected], samples[selected])
        masks = dict(
            rf_texture=forest.predict(features.reshape(-1, features.shape[-1])).reshape(prior.shape)
            == 1
        )
        masks.update(grabcut_masks(raw, samples, settings["seed"], settings["grabcut_iterations"]))
        out = output / case["id"]
        out.mkdir()
        write_image(out / "raw.png", raw)
        write_image(out / "processing-domain.png", domain.astype(np.uint8) * 255)
        np.save(out / "prior-sample-labels.npy", samples)
        priorview = raw.copy()
        contours, _ = cv2.findContours(
            prior.astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(priorview, contours, -1, (0, 220, 255), 1)
        write_image(out / "prior-outline.png", priorview)
        markers = raw.copy()
        markers[samples == 1] = [40, 40, 240]
        markers[samples == 0] = [240, 120, 0]
        write_image(out / "derived-samples.png", markers)
        for method, prediction in masks.items():
            mask = prediction & domain
            states = candidate_states(mask, domain, settings["uncertainty_px"])
            np.save(out / f"{method}-states.npy", states)
            write_image(out / f"{method}-mask.png", mask.astype(np.uint8) * 255)
            overlay = raw.copy()
            for value, color in [(1, [70, 220, 90]), (0, [220, 120, 20])]:
                chosen = states == value
                overlay[chosen] = (raw[chosen] * 0.6 + np.array(color) * 0.4).astype(np.uint8)
            write_image(out / f"{method}-overlay.png", overlay)
            top = topology(mask, settings["significant_area"])
            expected = case["expected_topology"]
            coretop = topology(states == 1, settings["significant_area"])
            scoped = scoped_topology(mask, domain, prior, settings["significant_area"])
            scoped_core = scoped_topology(states == 1, domain, prior, settings["significant_area"])
            signature_ok = all(
                scoped["target"][k] == expected[k] and scoped_core["target"][k] == expected[k]
                for k in ["components", "holes"]
            )
            if not signature_ok or scoped["unexplained_interior_components"]:
                gate = "FAIL"
            elif scoped["clipped_unmodeled_components"] or top["small_components"]:
                gate = "NEEDS_REVIEW"
            else:
                gate = "PASS"
            rows.append(
                dict(
                    case=case["id"],
                    method=method,
                    expected_topology=expected,
                    binary_topology=top,
                    AA_core_signature_matches_expected=all(
                        scoped_core["target"][k] == expected[k] for k in ["components", "holes"]
                    ),
                    AA_core_topology=coretop,
                    topology_gate=gate,
                    scoped_topology=scoped,
                    scoped_AA_core_topology=scoped_core,
                    pixel_truth_available=False,
                    full_mask_accepted=False,
                    samples_AA=int((samples == 1).sum()),
                    samples_non_AA=int((samples == 0).sum()),
                    changed_from_prior_pixels=int(((mask != prior) & domain).sum()),
                    AA_pixels=int((states == 1).sum()),
                    non_AA_pixels=int((states == 0).sum()),
                    unknown_pixels=int((states < 0).sum()),
                    warning=(
                        "Topology gate checks raw and core signatures, not boundary truth. "
                        "Extra edge fragments do not by themselves prove the main ring is broken."
                    ),
                )
            )
        # Strict method disagreement, not a vote-fused mask.
        stack = np.stack([m & domain for m in masks.values()])
        conflict = stack.any(axis=0) & ~stack.all(axis=0) & domain
        view = raw.copy()
        view[conflict] = (raw[conflict] * 0.5 + np.array([30, 160, 250]) * 0.5).astype(np.uint8)
        write_image(out / "disagreement.png", view)
    report = dict(
        status="prior_guided_same_chip_shape_regression_needs_review",
        rows=rows,
        source_sha256=digest(path),
        spec_sha256=digest(spec_path),
        code_sha256=digest(__file__),
        dependency_hashes={
            name: digest(Path(__file__).with_name(name))
            for name in ["aa_scribble_eval.py", "aa_segmentation_eval.py"]
        },
        seed_status="AI-derived from coarse geometry; not approved dense material pixels",
        CT_processed=False,
        formal_geometry_changed=False,
    )
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (output / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    data = dict(
        cases=[
            dict(id=c["id"], title=c["title"], review_status=c["review_status"])
            for c in spec["cases"]
        ],
        rows=rows,
    )
    (output / "data.js").write_text("const DATA=" + json.dumps(data, ensure_ascii=False) + ";\n")
    (output / "index.html").write_text(PAGE)
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


PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>竖环与折线AA验证</title>
<style>body{background:#14212b;color:#eee;font:18px/1.7 sans-serif;margin:20px}a{color:#7df}
select{font:inherit}.pair{display:flex;gap:18px}.pair>div{width:50%}
img{width:100%;max-height:85vh;object-fit:contain;object-position:top left}</style>
<h1>竖向环、台阶与折线AA：skill结构回归</h1>
<p>绿＝候选AA，蓝＝候选非AA，未着色＝未知/未处理。旧已审轮廓只作粗定位和AI取样先验，
不是稠密真值；新边界仍需复核。没有正交化或直接填多边形作为结果。</p>
<select id="case"></select><select id="method">
<option value="rf_texture">纹理RF</option><option value="gc_fixed">固定GMM GrabCut</option>
<option value="gc_refine">迭代GrabCut</option></select>
<select id="view"><option value="result">材料三态候选</option>
<option value="disagreement">多算法分歧</option>
<option value="prior-outline">旧粗轮廓（非本轮结果）</option>
<option value="derived-samples">AI派生样本（非新增人审）</option></select>
<div class="pair"><div>原图<img id="raw"></div><div>同坐标候选<img id="result"></div></div>
<p id="score"></p><p id="scope"></p>
<p>V01：只处理内侧竖环及内部AA条，图中更外侧结构不属于本轮覆盖。
P01：保留右下凹角，不自动填成矩形。
B01：两条折线的上下截口为未建模延续，不是物理断点；不得误连两条折线。</p>
<p>请只核查新结果是否保住这些结构。此前P01/P05/P06结构已审，不重复询问原形状；
拓扑PASS只是显著组件/孔数与先验一致，不能替代位置、边界和材料判断。</p>
<p><a href="spec.json">输入与AI假设</a> · <a href="report.json">全部结果与失败</a></p>
<script src="data.js"></script><script>
const el=id=>document.getElementById(id);
for(const c of DATA.cases){let o=document.createElement('option');o.value=c.id;
o.textContent=c.id+' '+c.title;
el('case').append(o);}
function update(){let c=el('case').value,m=el('method').value,v=el('view').value;
el('raw').src=c+'/raw.png';el('result').src=c+'/'+(v==='result'?m+'-overlay.png':v+'.png');
const r=DATA.rows.find(v=>v.case===c&&v.method===m);
el('score').textContent='结构门 '+r.topology_gate+'；显著组件/孔：'+r.binary_topology.components+
'/'+r.binary_topology.holes+'；AA核心组件/孔：'+r.AA_core_topology.components+'/'+r.AA_core_topology.holes+
'；目标AA核心组件/孔：'+r.scoped_AA_core_topology.target.components+'/'+
r.scoped_AA_core_topology.target.holes+'；小组件 '+r.binary_topology.small_components+
'；与旧轮廓不同 '+r.changed_from_prior_pixels+'像素';
el('scope').textContent=DATA.cases.find(v=>v.id===c).review_status;}
for(const e of document.querySelectorAll('select'))e.addEventListener('input',update);
update();</script></html>"""

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--spec", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    run(a.root, a.spec, a.output)
