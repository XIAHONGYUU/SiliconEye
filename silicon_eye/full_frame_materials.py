"""Extract full-canvas AA and AA-associated CT candidates, retaining uncertainty.

Run: python -m silicon_eye.full_frame_materials --root . --spec spec.json --output NEW_DIR
Uses existing OpenCV/Pillow dependencies; no region labels or external model calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np

from .guided_materials import ct_support


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def native_valid(shape, boxes):
    valid = np.ones(shape, np.uint8)
    height, width = shape
    for box in boxes:
        if len(box) != 4 or any(type(x) is not int for x in box):
            raise ValueError("Exclusion requires native integer xyxy")
        x, y, x1, y1 = box
        if not 0 <= x < x1 <= width or not 0 <= y < y1 <= height:
            raise ValueError("Exclusion outside full source")
        valid[y:y1, x:x1] = 0
    return valid.astype(bool)


def segment_aa(image, valid, settings):
    """Bright support plus edge-supported rectangular completion; never fill enclosing fields."""
    if image.ndim != 3 or valid.shape != image.shape[:2]:
        raise ValueError("AA source and full-canvas validity disagree")
    height, width = valid.shape
    gray = cv2.GaussianBlur(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (7, 7), settings["blur_sigma"])
    observed = (gray > settings["threshold"]) & valid
    seed = observed.astype(np.uint8) * 255
    # Closing only proposes envelopes; closing pixels are not raw observations.
    closed = cv2.morphologyEx(seed, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    result = seed.copy()
    records = []
    if hierarchy is not None:
        hierarchy = hierarchy[0]
        near = cv2.dilate(seed, np.ones((9, 9), np.uint8)) > 0
        for index, contour in enumerate(contours):
            depth, parent = 0, index
            while hierarchy[parent, 3] >= 0:
                depth += 1
                parent = hierarchy[parent, 3]
            if depth % 2:
                continue
            rect = cv2.minAreaRect(contour)
            rw, rh = rect[1]
            area = rw * rh
            if (
                min(rw, rh) < 3
                or area < 100
                or area > settings["max_completion_area_px"]
                or min(rw, rh) > settings["max_completion_short_side_px"]
            ):
                continue
            # A hole containing another substantial island is field between AA
            # objects, not an AA interior to fill (e.g. a ring around a MOS).
            hole, has_island = hierarchy[index, 2], False
            while hole >= 0:
                _, _, hw, hh = cv2.boundingRect(contours[hole])
                child = hierarchy[hole, 2]
                while child >= 0:
                    _, _, cw, ch = cv2.boundingRect(contours[child])
                    if cw * ch > max(1200, hw * hh * 0.18):
                        has_island = True
                    child = hierarchy[child, 0]
                hole = hierarchy[hole, 0]
            if has_island:
                continue
            box = cv2.boxPoints(rect)
            scores = []
            for side in range(4):
                start, end = box[side], box[(side + 1) % 4]
                count = max(2, int(np.linalg.norm(start - end)))
                xy = np.linspace(start, end, count).round().astype(int)
                xy[:, 0] = np.clip(xy[:, 0], 0, width - 1)
                xy[:, 1] = np.clip(xy[:, 1], 0, height - 1)
                scores.append(float(np.mean(near[xy[:, 1], xy[:, 0]])))
            four_sides = (
                min(scores) >= settings["min_edge_fraction"]
                and np.mean(scores) >= settings["mean_edge_fraction"]
            )
            three_sides = (
                sum(s >= settings["three_sides_fraction"] for s in scores) >= 3
                and min(scores) >= settings["weak_fourth_side_fraction"]
            )
            if not (four_sides or three_sides):
                continue
            cv2.fillConvexPoly(result, np.round(box).astype(np.int32), 255)
            records.append(
                {
                    "corners_native_xy": box.tolist(),
                    "edge_support": scores,
                    "completion": "candidate_not_observed_material_boundary",
                }
            )
    candidate = (result > 0) & valid
    kernel = np.ones((7, 7), np.uint8)
    boundary = (
        cv2.dilate(candidate.astype(np.uint8), kernel)
        != cv2.erode(candidate.astype(np.uint8), kernel)
    ) & valid
    sensitivity = ((gray > settings["threshold"] - 5) != (gray > settings["threshold"] + 5)) & valid
    return dict(
        mask=candidate,
        observed=observed,
        inferred=candidate & ~observed,
        unknown=boundary | sensitivity,
        valid=valid,
        completions=records,
    )


def associate_ct(aa, ct, matrix, anchors, settings, reference_valid=None):
    """Geometric AA landing proposals, not electrical or poly-vs-AA ground truth."""
    matrix = np.asarray(matrix, float)
    if matrix.shape != (3, 3) or not np.isfinite(matrix).all():
        raise ValueError("Invalid source-to-reference transform")
    height, width = aa.shape
    if reference_valid is None:
        reference_valid = np.ones(aa.shape, bool)
    if reference_valid.shape != aa.shape:
        raise ValueError("Reference validity shape disagrees")
    corners = np.float32([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
    mapped = cv2.perspectiveTransform(corners[:, None, :], matrix).reshape(-1, 2)
    area_ratio = cv2.contourArea(mapped.astype(np.float32), oriented=True) / (width * height)
    if not np.isfinite(mapped).all() or not 0.6 < area_ratio < 1.5:
        raise ValueError("Degenerate or implausible full-frame transform")
    anchors = np.asarray(anchors, np.float32)
    if anchors.ndim != 2 or anchors.shape[1] != 2 or len(anchors) < 4:
        raise ValueError("Missing registration support envelope")
    hull = cv2.convexHull(anchors)
    if cv2.contourArea(hull) < 100:
        raise ValueError("Degenerate registration anchor distribution")
    inside = cv2.distanceTransform(aa.astype(np.uint8), cv2.DIST_L2, 5)
    outside = cv2.distanceTransform((~aa).astype(np.uint8), cv2.DIST_L2, 5)
    count, labels, stats, centers = cv2.connectedComponentsWithStats(ct.astype(np.uint8))
    projected = cv2.perspectiveTransform(centers[1:, None, :].astype(np.float32), matrix)
    selected, uncertain = np.zeros(count, bool), np.zeros(count, bool)
    records = []
    for index, point in enumerate(projected.reshape(-1, 2), 1):
        x, y = np.round(point).astype(int)
        hull_distance = cv2.pointPolygonTest(hull, tuple(map(float, point)), True)
        band = min(
            settings["max_px"],
            settings["base_px"]
            + max(0, -hull_distance) * settings["outside_anchor_hull_growth_px_per_px"],
        )
        band += max(stats[index, 2:4]) * 0.5
        if not 0 <= x < width or not 0 <= y < height:
            status = "outside_reference_coverage"
            uncertain[index] = True
            distance = None
        elif not reference_valid[y, x]:
            status = "invalid_reference_coverage"
            uncertain[index] = True
            distance = None
        else:
            distance = float(inside[y, x] if aa[y, x] else -outside[y, x])
            selected[index] = distance > band
            uncertain[index] = abs(distance) <= band
            status = (
                "AA_interior_candidate"
                if selected[index]
                else "AA_boundary_or_registration_unknown"
                if uncertain[index]
                else "not_assigned_to_AA_not_proof_of_poly"
            )
        records.append(
            {
                "component_id": f"CT-support-{index:05}",
                "poly_native_center_xy": centers[index].tolist(),
                "aa_reference_center_xy": point.tolist(),
                "poly_native_bbox_xywh": stats[index, :4].tolist(),
                "signed_AA_distance_px": distance,
                "working_guard_band_px": band,
                "status": status,
                "physical_contact_count": None,
                "electrical_ownership": "unknown",
            }
        )
    return dict(selected=selected[labels], unknown=uncertain[labels], records=records)


def save(path, array):
    if not cv2.imwrite(str(path), array):
        raise OSError("Unable to write " + str(path))


def overlay(mask, bgr):
    rgba = np.zeros((*mask.shape, 4), np.uint8)
    rgba[mask] = (*bgr, 180)
    return rgba


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or output.is_relative_to(root / "data"):
        raise ValueError("Output must be new and outside raw data/")
    spec_path = Path(spec_path).resolve()
    spec = json.loads(spec_path.read_text())
    if spec.get("schema_version") != 1 or "regions" in spec:
        raise ValueError("Expected full-frame extraction settings without region crops")
    cv2.setNumThreads(2)
    images, valids = {}, {}
    for layer in ["aa", "poly"]:
        source = spec["sources"][layer]
        path = (root / source["path"]).resolve()
        if not path.is_relative_to(root) or digest(path) != source["sha256"]:
            raise ValueError("Source path or hash mismatch")
        image = cv2.imread(str(path))
        if image is None or image.shape[:2] != (source["height"], source["width"]):
            raise ValueError("Unusable or changed full source")
        images[layer] = image
        valids[layer] = native_valid(image.shape[:2], spec["excluded_native_boxes"][layer])
    if images["aa"].shape != images["poly"].shape:
        raise ValueError("This candidate exporter requires equal native frame dimensions")
    reference = spec["registration"]
    reg_path = (root / reference["path"]).resolve()
    if not reg_path.is_relative_to(root) or digest(reg_path) != reference["sha256"]:
        raise ValueError("Registration evidence changed")
    reg = json.loads(reg_path.read_text())
    aa = segment_aa(images["aa"], valids["aa"], spec["aa"])
    ct = ct_support(images["poly"], profile=spec["ct_profile"]) & valids["poly"]
    association = associate_ct(
        aa["mask"],
        ct,
        reg["matrix"],
        [x["aa_native_xy"] for x in reg["anchors"]],
        spec["association_guard_band"],
        valids["aa"],
    )
    height, width = aa["mask"].shape
    matrix = np.asarray(reg["matrix"], float)
    ct_ref = (
        cv2.warpPerspective(
            association["selected"].astype(np.uint8),
            matrix,
            (width, height),
            flags=cv2.INTER_NEAREST,
        )
        > 0
    )
    unknown_ref = (
        cv2.warpPerspective(
            association["unknown"].astype(np.uint8),
            matrix,
            (width, height),
            flags=cv2.INTER_NEAREST,
        )
        > 0
    )
    ct_ref &= valids["aa"]
    unknown_ref &= valids["aa"]
    aa_poly = (
        cv2.warpPerspective(
            aa["mask"].astype(np.uint8),
            np.linalg.inv(matrix),
            (width, height),
            flags=cv2.INTER_NEAREST,
        )
        > 0
    )
    aa_poly &= valids["poly"]
    _, aa_labels = cv2.connectedComponents(aa["mask"].astype(np.uint8))
    checks = []
    for points in spec.get("development_separation_checks_native_xy", []):
        labels = []
        for x, y in points:
            if not 0 <= x < width or not 0 <= y < height:
                raise ValueError("Separation check outside source")
            labels.append(int(aa_labels[y, x]))
        passed = len(labels) == 2 and labels[0] > 0 and labels[1] > 0 and labels[0] != labels[1]
        checks.append(
            dict(native_points=points, labels=labels, passed=passed, independent_validation=False)
        )
        if not passed:
            raise ValueError("Previously reviewed AA separation regressed")
    del aa_labels
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".full-materials-", dir=output.parent) as temp:
        stage = Path(temp)
        masks = {
            "AA-mask": aa["mask"],
            "AA-observed": aa["observed"],
            "AA-inferred": aa["inferred"],
            "AA-unknown": aa["unknown"],
            "AA-valid": aa["valid"],
            "CT-on-AA-poly-native": association["selected"],
            "CT-on-AA-AA-reference": ct_ref,
            "CT-unknown-poly-native": association["unknown"],
            "CT-all-poly-native": ct,
            "CT-source-valid": valids["poly"],
        }
        for name, mask in masks.items():
            save(stage / (name + ".png"), mask.astype(np.uint8) * 255)
        for frame, a, c, u in [
            ("aa", aa["mask"], ct_ref, unknown_ref),
            ("poly", aa_poly, association["selected"], association["unknown"]),
        ]:
            save(stage / (frame + "-AA-overlay.png"), overlay(a, (70, 220, 80)))
            save(stage / (frame + "-CT-overlay.png"), overlay(c, (255, 200, 30)))
            save(stage / (frame + "-CT-unknown-overlay.png"), overlay(u, (0, 190, 255)))
        report = {
            "status": "candidate_full_frame_extraction",
            "unit": "px",
            "full_canvas_wh": [width, height],
            "region_categories_used": False,
            "sources": spec["sources"],
            "spec_sha256": digest(spec_path),
            "registration": reference,
            "registration_acceptance": "not_human_accepted_fullframe",
            "AA_positive_pixels": int(aa["mask"].sum()),
            "AA_inferred_pixels": int(aa["inferred"].sum()),
            "AA_unknown_pixels": int(aa["unknown"].sum()),
            "AA_completion_count": len(aa["completions"]),
            "CT_support_components": len(association["records"]),
            "CT_AA_candidate_components": sum(
                x["status"] == "AA_interior_candidate" for x in association["records"]
            ),
            "CT_unknown_components": sum(
                x["status"]
                in [
                    "AA_boundary_or_registration_unknown",
                    "outside_reference_coverage",
                    "invalid_reference_coverage",
                ]
                for x in association["records"]
            ),
            "counts_are_physical_contact_counts": False,
            "materials_accepted": False,
            "development_AA_separation_checks": checks,
            "zero_mask_meaning": "no positive support; not human-confirmed material absence",
            "unknown_mask_semantics": "boundary/threshold uncertainty can overlap positive support",
            "guard_band_semantics": "working rule, not a measured confidence interval",
            "code_sha256": {
                Path(__file__).name: digest(__file__),
                "guided_materials.py": digest(Path(__file__).with_name("guided_materials.py")),
            },
        }
        for name, data in [
            ("report.json", report),
            ("contacts.json", association["records"]),
            ("AA-completions.json", aa["completions"]),
            ("spec.json", spec),
        ]:
            (stage / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        paths = {
            k: os.path.relpath(root / spec["sources"][k]["path"], output) for k in ["aa", "poly"]
        }
        page = """<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<title>全幅 AA / AA上的CT 候选 v1</title>
<style>body{font:18px/1.6 sans-serif;
background:#14202b;
color:#eef4f8;
margin:24px}select,button,label{font:inherit;
margin:8px}a{color:#72d8ff}.stage{position:relative;
background:#000}.base{width:100%;
display:block}.layer{position:absolute;
inset:0;
width:100%;
height:100%}</style>
<h1>全幅 AA 与 AA 上 CT：候选 v1</h1>
<p>绿色 AA，蓝色 AA 内部 CT 候选，黄色归属/配准待核 CT。全部保留原生全幅；无器件区域裁割。
AA 灰暗内部含几何补全，CT→AA 变换未获精确落点验收。
零值不是已确认不存在。</p>
<select id="frame">
<option value="aa">AA 原生坐标（CT 为候选投影）</option>
<option value="poly">poly 原生坐标（CT 原生，AA 为候选投影）</option>
</select>
<select id="zoom">
<option value="fit">适应窗口</option>
<option value="native">原生像素大小</option>
</select>
<label>
<input id="aa" type="checkbox" checked>AA</label>
<label>
<input id="ct" type="checkbox" checked>AA 上 CT</label>
<label>
<input id="unknown" type="checkbox" checked>待核 CT</label>
<label>
<input id="source" type="checkbox" checked>原图背景</label>
<p>
<a href="AA-mask.png">AA 全幅二值候选</a> ·
<a href="CT-on-AA-poly-native.png">AA 上 CT 原生候选</a> ·
<a href="AA-unknown.png">AA 不确定图</a> ·
<a href="report.json">报告与坐标说明</a>
</p>
<div class="stage">
<img class="base" id="base">
<img class="layer" id="aaLayer">
<img class="layer" id="ctLayer">
<img class="layer" id="unknownLayer">
</div>
<script>const paths=PATHS;

const w=WIDTH;

const get=id=>document.getElementById(id);

function change(){const f=get('frame').value;

get('base').src=paths[f];

get('aaLayer').src=f+'-AA-overlay.png';

get('ctLayer').src=f+'-CT-overlay.png';

get('unknownLayer').src=f+'-CT-unknown-overlay.png';

get('aaLayer').hidden=!get('aa').checked;

get('ctLayer').hidden=!get('ct').checked;

get('unknownLayer').hidden=!get('unknown').checked;

get('base').style.visibility=get('source').checked?'visible':'hidden';

document.querySelector('.stage').style.width=get('zoom').value==='native'?w+'px':'100%'}
document.querySelectorAll('select,input').forEach(x=>x.onchange=change);
change();
</script>
</html>"""
        rendered = page.replace("PATHS", json.dumps(paths)).replace("WIDTH", str(width))
        (stage / "index.html").write_text(rendered)
        for layer, source in spec["sources"].items():
            if digest(root / source["path"]) != source["sha256"]:
                raise ValueError("Raw source changed during extraction: " + layer)
        hashes = {p.name: digest(p) for p in sorted(stage.iterdir()) if p.is_file()}
        (stage / "manifest.json").write_text(
            json.dumps({"outputs": hashes, "physical_truth_verified": False}, indent=2) + "\n"
        )
        if output.exists():
            raise ValueError("Output appeared during extraction")
        stage.rename(output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = run(args.root, args.spec, args.output)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"Full-frame material extraction failed: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
