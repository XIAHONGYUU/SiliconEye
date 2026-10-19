"""Compare direct POLY bodies, guided local segmentation, and regularized candidates.

Run: python -m silicon_eye.poly_reconstruction_review --root . --spec SPEC --output NEW_DIR
Uses existing guided_mask/geometry helpers, OpenCV and Shapely. AI observations
and prior decisions are explicit inputs; no full-frame extrapolation or CT assignment.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon

from .geometry_reconstruction import digest, orthogonal_fit
from .guided_materials import guided_mask
from .scene_geometry import load_locked


def refine_strip(points, foreground, occlusion, origin, settings):
    """Locate normal edges from visible support; keep tangent extent an AI hypothesis."""
    points = np.asarray(points, float)
    original_points = points.copy()
    swapped = np.linalg.norm(points[3] - points[0]) > np.linalg.norm(points[1] - points[0])
    if swapped:
        points = points[[0, 3, 2, 1]]
    along, normal = points[1] - points[0], points[3] - points[0]
    length = float(np.linalg.norm(along))
    width = float(np.linalg.norm(normal))
    if length < 3 or width < 2 or foreground.shape != occlusion.shape:
        raise ValueError("Invalid strip or masks")
    inverse = np.linalg.inv(np.c_[along, normal])
    yy, xx = np.nonzero(foreground & ~occlusion)
    if len(xx) < 5:
        return None, dict(status="insufficient_visible_support")
    uv = (np.c_[xx, yy] + origin - points[0]) @ inverse.T
    trim = settings["trim_tangent_fraction"]
    radius = settings["normal_search_fraction"]
    eligible = (
        (uv[:, 0] >= trim)
        & (uv[:, 0] <= 1 - trim)
        & (uv[:, 1] >= -radius)
        & (uv[:, 1] <= 1 + radius)
    )
    uv = uv[eligible]
    bins = max(3, int(length))
    lower, upper = [], []
    for index in range(int(np.ceil(trim * bins)), int(np.floor((1 - trim) * bins))):
        values = uv[(uv[:, 0] >= index / bins) & (uv[:, 0] < (index + 1) / bins), 1]
        if len(values) >= 2:
            lower.append(float(values.min() - 0.5 / width))
            upper.append(float(values.max() + 0.5 / width))
    count = max(1, int(np.floor((1 - trim) * bins)) - int(np.ceil(trim * bins)))
    fraction = len(lower) / count
    if fraction < settings["minimum_supported_fraction"]:
        return None, dict(status="insufficient_tangent_coverage", supported_fraction=fraction)
    lo, hi = float(np.median(lower)), float(np.median(upper))
    if hi - lo < 0.2 or max(abs(lo), abs(hi - 1)) > settings["max_normal_shift_fraction"]:
        return None, dict(status="normal_shift_exceeds_working_budget", normal_interval=[lo, hi])
    refined = np.array(
        [
            points[0] + normal * lo,
            points[1] + normal * lo,
            points[1] + normal * hi,
            points[0] + normal * hi,
        ]
    )
    if swapped:
        refined = refined[[0, 3, 2, 1]]
    return refined, dict(
        status="candidate_normal_edges_from_algorithm_support",
        supported_fraction=fraction,
        normal_interval=[lo, hi],
        mean_corner_change_px=float(np.linalg.norm(refined - original_points, axis=1).mean()),
        tangent_end_status="AI_visible_fragment_extent_not_measured_terminal",
        quality_improvement="NOT_ESTABLISHED_without_source_review",
    )


def raster(points, shape, origin):
    mask = np.zeros(shape, np.uint8)
    cv2.fillPoly(mask, [np.rint(np.asarray(points) - origin).astype(np.int32)], 1)
    return mask > 0


def visible_states(support, unknown):
    states = np.full(support.shape, -1, np.int8)
    states[support & ~unknown] = 1
    return states


def outlines(raw, objects, origin, color):
    image = raw.copy()
    for obj in objects:
        p = np.rint(np.asarray(obj["native_outline"]) - origin).astype(np.int32)
        cv2.polylines(image, [p], True, color, 1, cv2.LINE_AA)
    return image


def svg(objects):
    polygons = [Polygon(o["layout_outline"]) for o in objects]
    bounds = np.array([p.bounds for p in polygons])
    x, y = bounds[:, :2].min(0) - 10
    right, bottom = bounds[:, 2:].max(0) + 10
    result = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {right - x} {bottom - y}">'
    for obj in objects:
        pts = " ".join(f"{a},{b}" for a, b in obj["layout_outline"])
        result += f'<polygon points="{pts}" fill="#47b8ed" stroke="#b4e6ff" stroke-width=".8"/>'
    return result + "</svg>"


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(Path(spec_path).read_text())
    baseline = load_locked(root, spec["baseline"])
    for item in baseline["references"].values():
        if digest(root / item["path"]) != item["sha256"]:
            raise ValueError("Changed baseline input: " + item["path"])
    if digest(root / spec["source"]["path"]) != spec["source"]["sha256"]:
        raise ValueError("Changed POLY source")
    source = cv2.imread(str(root / spec["source"]["path"]))
    output.mkdir(parents=True)
    records = []
    for case in spec["cases"]:
        folder = output / case["id"]
        folder.mkdir()
        x, y, right, bottom = case["native_bbox"]
        origin = np.array([x, y])
        raw = source[y:bottom, x:right]
        direct = []
        prompt = np.zeros(raw.shape[:2], bool)
        for obj in case["objects"]:
            p = np.asarray(obj["observed_outline_native_xy"], float)
            prompt |= raster(p, raw.shape[:2], origin)
            direct.append(
                dict(
                    id=obj["id"],
                    native_outline=p.tolist(),
                    layout_outline=orthogonal_fit(p, obj["edge_axes"]).tolist(),
                    extent="visible_body_fragment_not_complete_gate",
                    physical_tangent_ends="unknown_or_observation_scope",
                    identity=case["source_of_identity"],
                )
            )
        result = guided_mask(
            raw,
            prompt.astype(np.uint8) * 255,
            "poly",
            radius=spec["settings"]["search_radius_px"],
            iterations=spec["settings"]["grabcut_iterations"],
        )
        unknown = result["ct_unknown"].copy()
        for left, top, r, b in case.get("unknown_native_boxes", []):
            unknown[max(0, top - y) : min(bottom, b) - y, max(0, left - x) : min(right, r) - x] = (
                True
            )
        refined = []
        measurements = []
        for obj, item in zip(case["objects"], direct, strict=True):
            points, detail = refine_strip(
                item["native_outline"], result["visible"], unknown, origin, spec["settings"]
            )
            if points is None:
                points = np.asarray(item["native_outline"])
                detail["decision"] = "retain_direct_A_no_algorithm_gain_claim"
            layout = orthogonal_fit(points, obj["edge_axes"])
            p = Polygon(layout)
            if not p.is_valid or p.area <= 0:
                raise ValueError("Invalid regular POLY candidate")
            refined.append(
                dict(
                    id=obj["id"],
                    native_outline=points.tolist(),
                    layout_outline=layout.tolist(),
                    extent=item["extent"],
                    physical_tangent_ends=item["physical_tangent_ends"],
                    identity=item["identity"],
                    material_boundary="AI_candidate_not_pixel_truth",
                )
            )
            measurements.append(dict(id=obj["id"], **detail))
        for obj in direct + refined:
            obj["native_to_layout"] = cv2.getPerspectiveTransform(
                np.asarray(obj["native_outline"], np.float32),
                np.asarray(obj["layout_outline"], np.float32),
            ).tolist()
            obj["layout_unit"] = "relative_poly_layout_pixel_not_um"
            obj["coordinate_scope"] = "local_body_correspondence_not_AA_registration"
        overlaps = []
        for index, obj in enumerate(refined):
            for other in refined[:index]:
                area = (
                    Polygon(obj["layout_outline"])
                    .intersection(Polygon(other["layout_outline"]))
                    .area
                )
                if area > 0:
                    overlaps.append(dict(a=obj["id"], b=other["id"], area=area))
        mask = np.zeros(raw.shape[:2], bool)
        for obj in refined:
            mask |= raster(obj["native_outline"], raw.shape[:2], origin)
        np.save(folder / "B1-states.npy", visible_states(mask, unknown))
        cv2.imwrite(str(folder / "unknown.png"), unknown.astype(np.uint8) * 255)
        cv2.imwrite(str(folder / "B0-visible.png"), result["visible"].astype(np.uint8) * 255)
        cv2.imwrite(str(folder / "source.png"), raw)
        cv2.imwrite(str(folder / "A.png"), outlines(raw, direct, origin, (0, 210, 255)))
        cv2.imwrite(str(folder / "B1.png"), outlines(raw, refined, origin, (240, 160, 20)))
        cv2.imwrite(
            str(folder / "comparison.png"),
            outlines(outlines(raw, direct, origin, (0, 210, 255)), refined, origin, (240, 160, 20)),
        )
        b0 = raw.copy()
        b0[result["visible"]] = (
            b0[result["visible"]] * 0.6 + np.array([50, 210, 50]) * 0.4
        ).astype(np.uint8)
        cv2.imwrite(str(folder / "B0.png"), b0)
        uncertain = raw.copy()
        uncertain[unknown] = (uncertain[unknown] * 0.5 + np.array([30, 140, 250]) * 0.5).astype(
            np.uint8
        )
        cv2.imwrite(str(folder / "uncertainty.png"), uncertain)
        (folder / "layout.svg").write_text(svg(refined))
        _, labels = cv2.connectedComponents(result["visible"].astype(np.uint8), connectivity=8)
        seed_labels = []
        for item in direct:
            center = np.asarray(item["native_outline"]).mean(0) - origin
            cx, cy = np.rint(center).astype(int)
            seed_labels.append(int(labels[cy, cx]))
        record = dict(
            id=case["id"],
            name=case["name"],
            native_bbox=case["native_bbox"],
            context=case["context"],
            question=case["new_question"],
            direct=direct,
            refined=refined,
            measurements=measurements,
            regular_geometry="PASS",
            pair_overlap_gate="FAIL" if overlaps else "PASS",
            pair_overlaps=overlaps,
            B0_center_component_labels=seed_labels,
            B0_component_labels_not_material_truth=True,
            unknown_pixels=int(unknown.sum()),
            identity_reconfirmation_required=False,
            quality_improvement="NEEDS_REVIEW",
            full_gate_shape="NOT_COMPLETED_visible_fragments_only",
        )
        if "prior_positive" in case:
            q = case["prior_positive"]
            old = cv2.imread(str(root / q["path"]), 0) > 0
            if digest(root / q["path"]) != q["sha256"]:
                raise ValueError("Changed reviewed poly support")
            px, py = q["native_origin_xy"]
            cv2.imwrite(
                str(folder / "approved-prior.png"),
                old[y - py : bottom - py, x - px : right - px].astype(np.uint8) * 255,
            )
            record["approved_prior"] = "retained_unchanged_not_replaced_by_new_candidate"
        (folder / "objects.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n"
        )
        records.append(record)
    assert all(
        digest(root / item["path"]) == item["sha256"] for item in baseline["references"].values()
    )
    report = dict(
        status="local_POLY_geometry_candidates_require_review_before_fullframe",
        steps=dict(
            freeze_AA="DONE",
            reuse_POLY_history="DONE",
            representative_comparison="EXECUTED_NEW_GEOMETRY_PENDING",
            fullframe_POLY="NOT_STARTED_until_local_method_validated",
            skill_packaging="NOT_STARTED_until_validation",
        ),
        source=spec["source"],
        baseline=spec["baseline"],
        cases=records,
        AA_unchanged=True,
        CT_assignments_performed=False,
        fullframe_model_training=False,
        aa_to_poly_projection_applied=False,
        code_sha256=digest(__file__),
        spec_sha256=digest(spec_path),
        limitations=(
            "AI-selected cores guide local GrabCut; not independent discovery, "
            "pixel truth or full-gate reconstruction. E01 overlaps H01."
        ),
    )
    for name, value in [("report.json", report), ("spec.json", spec), ("baseline.json", baseline)]:
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    (output / "data.js").write_text("const DATA=" + json.dumps(report, ensure_ascii=False) + ";\n")
    (output / "index.html").write_text(PAGE)
    manifest = {
        str(p.relative_to(output)): digest(p) for p in sorted(output.rglob("*")) if p.is_file()
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return dict(
        status=report["status"],
        cases=[
            dict(
                id=c["id"],
                overlap=c["pair_overlap_gate"],
                refinement=[m["status"] for m in c["measurements"]],
            )
            for c in records
        ],
    )


PAGE = """<!doctype html><meta charset="utf-8"><title>POLY局部规则复原对照</title>
<style>body{font-family:sans-serif;
background:#18202b;
color:#eee;
max-width:1200px;
margin:25px auto}
img{width:100%;
image-rendering:auto}a{color:#86d8ff}.pair{display:grid;
grid-template-columns:1fr 1fr;
gap:15px}
select{padding:9px}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style>
<h1>POLY：复用既有身份，比较新规则几何</h1>
<p>黄色=A直接观察，绿色=B0算法候选，蓝色=B1算法辅助后AI规则几何。橙色为遮挡/端部未知。当前只恢复可见主体片段，不把矩形封口当作真实栅端。</p>
<p>AA基线已冻结；没有未经确认的跨层投影，没有CT归属判断或全图模型外推。横/竖栅身份及局部不相连的既有裁决不重复询问。</p>
<select id="case"></select><select id="mode"><option value="comparison">A/B1叠加对照</option>
<option value="A">A：直接观察</option><option value="B0">B0：局部算法</option>
<option value="B1">B1：规则几何候选</option><option value="uncertainty">遮挡/端部未知</option>
<option value="layout">纯规则几何</option></select><p id="note"></p>
<div class="pair"><div>原始POLY与宽上下文<img id="source"></div>
<div>所选结果<img id="result"></div>
</div>

<h2>本轮核查清单</h2><ul id="questions"></ul>
<p>只需核查新轮廓的位置/宽度和未知表达；不重新裁决是不是POLY，不逐个CT核对。局部方法通过后再推进全幅和skill封装。</p>
<p><a href="report.json">结果</a> ·
<a href="spec.json">冻结假设</a> ·
<a href="baseline.json">原标注与AA基线</a></p>
<script src="data.js"></script><script>
const el=id=>document.getElementById(id);

for(const c of DATA.cases){let o=document.createElement('option');
o.value=c.id;
o.textContent=c.id+' '+c.name;
el('case').append(o);

let li=document.createElement('li');
li.textContent=c.id+'：'+c.question;
el('questions').append(li);
}
function update(){const c=DATA.cases.find(v=>v.id===el('case').value),mode=el('mode').value;

el('source').src=c.id+'/source.png';
el('result').src=c.id+'/'+(mode==='layout'?'layout.svg':mode+'.png');

el('note').textContent=c.context+'；原生范围 '+c.native_bbox.join(', ')+'。新精确边界未审。';
}
for(const x of ['case','mode'])el(x).addEventListener('change',update);
update();

</script>"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.spec, args.output), ensure_ascii=False, indent=2))
