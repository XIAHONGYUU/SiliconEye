"""Replay three known AA skill tasks without training or full-frame inference.

Run: .venv/bin/python benchmarks/aa-skill-three-task-v1/run.py --output runs/NEW_DIR
Requires existing locked evidence, numpy, OpenCV and project geometry helpers.
Uses a frozen AI corner hypothesis; does not autonomously infer material semantics.
"""

import argparse
import hashlib
import html
import json
import shutil
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon

from silicon_eye.aa_completion import source_polygon
from silicon_eye.geometry_reconstruction import build_aa_polygons, project

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def overlay(raw, polygons, origin, color):
    result = raw.copy()
    for polygon in polygons:
        points = np.rint(np.asarray(polygon) - origin).astype(np.int32)
        cv2.polylines(result, [points], True, color, 2, cv2.LINE_AA)
    return result


def shared_components(mask, first, second):
    _, labels = cv2.connectedComponents(mask.astype(np.uint8), connectivity=8)
    a = set(np.unique(labels[first])) - {0}
    b = set(np.unique(labels[second])) - {0}
    return sorted(int(value) for value in a & b)


def run(output):
    if output.exists():
        raise ValueError("Use a new output directory")
    plan_path = Path(__file__).with_name("plan-v1.json")
    plan = json.loads(plan_path.read_text())
    refs = plan["references"]
    for ref in refs.values():
        if digest(ROOT / ref["path"]) != ref["sha256"]:
            raise ValueError(f"Changed evidence: {ref['path']}")
    output.mkdir(parents=True)
    source = cv2.imread(str(ROOT / refs["source"]["path"]))
    # T1 reuses the exact approved-context candidate; it does not regenerate states.
    shutil.copy2(ROOT / refs["s05_states"]["path"], output / "T1-reused-states.npy")
    shutil.copy2(ROOT / refs["s05_domain"]["path"], output / "T1-reused-domain.png")
    assert digest(output / "T1-reused-states.npy") == refs["s05_states"]["sha256"]
    t1 = dict(
        status="PASS_scoped_reuse",
        changed_material_pixels=0,
        new_training=False,
        new_inference=False,
        repeat_human_questions=0,
        approval_scope="existing local two-ring position/gap; not exact dense truth",
    )
    # T2: unchanged direct result, cached algorithm evidence, then existing HV fitter.
    task = plan["tasks"]["T2"]
    base = json.loads((ROOT / refs["direct_model"]["path"]).read_text())
    direct = next(o for o in base["objects"] if o["id"] == task["direct_object"])
    direct_native = np.asarray(source_polygon(direct, base).exterior.coords)[:-1]
    coordinate_model = json.loads((ROOT / refs["coordinate_model"]["path"]).read_text())
    matrix = np.asarray(coordinate_model["aa_native_to_layout"])
    fitted = build_aa_polygons([task["b1_observation"]], matrix, 1)[0]
    b1_native = project(fitted["outer_xy"], np.linalg.inv(matrix))
    polygon = Polygon(fitted["outer_xy"])
    edges = np.diff(np.vstack([fitted["outer_xy"], fitted["outer_xy"][0]]), axis=0)
    hv = bool(np.all((edges[:, 0] == 0) ^ (edges[:, 1] == 0)))
    assert hv and polygon.is_valid and len(fitted["outer_xy"]) == 6
    (output / "T2-A-original-object.json").write_text(
        json.dumps(direct, ensure_ascii=False, indent=2) + "\n"
    )
    (output / "T2-B1-candidate.json").write_text(
        json.dumps(
            dict(
                object=fitted,
                aa_native_to_layout=matrix.tolist(),
                native_outline=b1_native.tolist(),
                scope="single object candidate only; not installed in main AA layer",
                algorithm_dependency=refs["b0_detail"],
                ai_hypothesis=task["b1_observation"],
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    x, y, right, bottom = task["context_bbox"]
    raw = source[y:bottom, x:right]
    cv2.imwrite(str(output / "T2-source.jpg"), raw)
    cv2.imwrite(str(output / "T2-A.jpg"), overlay(raw, [direct_native], [x, y], (0, 210, 255)))
    b0 = cv2.imread(str(ROOT / refs["b0_detail"]["path"]), 0) > 0
    preview = raw.copy()
    bx, by, br, bb = task["native_bbox"]
    region = preview[by - y : bb - y, bx - x : br - x]
    region[b0] = (region[b0] * 0.65 + np.array([60, 220, 60]) * 0.35).astype(np.uint8)
    cv2.imwrite(str(output / "T2-B0.jpg"), preview)
    cv2.imwrite(str(output / "T2-B1.jpg"), overlay(raw, [b1_native], [x, y], (220, 140, 0)))
    comparison = overlay(raw, [direct_native], [x, y], (0, 210, 255))
    cv2.imwrite(
        str(output / "T2-comparison.jpg"), overlay(comparison, [b1_native], [x, y], (220, 140, 0))
    )
    minx, miny, maxx, maxy = polygon.bounds
    points = " ".join(f"{px},{py}" for px, py in fitted["outer_xy"])
    (output / "T2-B1-layout.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx - 10} {miny - 10} '
        f'{maxx - minx + 20} {maxy - miny + 20}"><polygon points="{points}" '
        'fill="#168bc7" stroke="#c7eeff" stroke-width="1"/></svg>'
    )
    # Compare notch against a pre-existing AI optical observation, not pixel truth.
    shape = json.loads((ROOT / refs["shape_spec"]["path"]).read_text())
    case = next(c for c in shape["cases"] if c["id"] == task["detail_case"])
    prior_corner = np.asarray(case["objects"][0]["outer_native_xy"][3])
    a_notch = direct_native[np.argmin(np.linalg.norm(direct_native - prior_corner, axis=1))]
    b_notch = b1_native[3]
    t2 = dict(
        status="NEEDS_REVIEW_quality_gain_not_established",
        new_training=False,
        new_inference=False,
        cached_B0=True,
        new_B1_regular_geometry=True,
        valid_polygon=bool(polygon.is_valid),
        orthogonal=hv,
        components=1,
        holes=0,
        edges=6,
        topology_preserved=True,
        direct_native_notch=a_notch.tolist(),
        B1_native_notch=b_notch.tolist(),
        historical_AI_observation=prior_corner.tolist(),
        A_distance_to_AI_observation_px=float(np.linalg.norm(a_notch - prior_corner)),
        B1_distance_to_AI_observation_px=float(np.linalg.norm(b_notch - prior_corner)),
        metric_limitation="Historical AI observation is not independent precise boundary truth.",
        decision="candidate_only_do_not_replace_original",
        human_corrections_this_execution=0,
        runtime_comparison="NOT_MEASURED_cached_inputs",
    )
    # T3 scopes component tests to the reviewed local span, not an entire chip net.
    states = np.load(ROOT / refs["s05_states"]["path"])
    bad = cv2.imread(str(ROOT / refs["b0_regression"]["path"]), 0) > 0
    paths = json.loads((ROOT / refs["s05_report"]["path"]).read_text())["results"][0]
    paths = paths["paths_native_y"]
    left, top, _, _ = plan["tasks"]["T3"]["native_bbox"]
    yy = np.arange(states.shape[0])[:, None] + top
    xx = np.arange(states.shape[1])[None, :] + left
    rx, ry, rr, rb = plan["tasks"]["T3"]["connection_test_native_bbox"]
    roi = (xx >= rx) & (xx < rr) & (yy >= ry) & (yy < rb)
    first = roi & (yy > np.array(paths["ring_inner"])[None, :] + 3)
    first &= yy < np.array(paths["ring_outer"])[None, :] - 3
    second = roi & (yy > np.array(paths["second_ring_inner"])[None, :] + 3)
    second &= yy < np.array(paths["second_ring_outer"])[None, :] - 3
    old_shared = shared_components((states == 1) & roi, first, second)
    bad_shared = shared_components(bad & roi, first, second)
    assert first.any() and second.any() and not old_shared and bad_shared
    t3 = dict(
        status="PASS_rejected_regression",
        retained_shared_components=old_shared,
        rejected_shared_components=bad_shared,
        decision="reject_B0_retain_existing_S05",
        evidence_scope="local span only; no electrical/whole-ring conclusion",
        anchor_scope="AI edge cores under human reviewed local two-ring relationship",
        repeat_human_questions=0,
    )
    sx, sy, sr, sb = plan["tasks"]["T3"]["native_bbox"]
    raw_s = source[sy:sb, sx:sr]
    cv2.imwrite(str(output / "T3-source.jpg"), raw_s)
    bad_img = raw_s.copy()
    bad_img[bad] = (bad_img[bad] * 0.55 + np.array([60, 220, 60]) * 0.45).astype(np.uint8)
    cv2.imwrite(str(output / "T3-rejected.jpg"), bad_img)
    good = raw_s.copy()
    for selected, color in [(states == 1, [60, 220, 60]), (states == 0, [220, 140, 0])]:
        good[selected] = (good[selected] * 0.55 + np.array(color) * 0.45).astype(np.uint8)
    cv2.imwrite(str(output / "T1-T3-retained.jpg"), good)
    # Verify all locked inputs stayed untouched, including raw photos and decisions.
    assert all(digest(ROOT / v["path"]) == v["sha256"] for v in refs.values())
    report = dict(
        schema_version=1,
        evaluation=plan["evaluation"],
        plan_sha256=digest(plan_path),
        runner_sha256=digest(__file__),
        tasks=dict(T1=t1, T2=t2, T3=t3),
        inputs_unchanged=True,
        overall="scoped_reuse_and_regression_rejection_demonstrated; quality_gain_pending",
        scope="same agent executes and judges known cases; not independent skill evaluation",
    )
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    shutil.copy2(plan_path, output / "plan.json")
    cards = [
        ("T2-source.jpg", "原图与宽上下文"),
        ("T2-A.jpg", "A：旧直接提取（黄色）"),
        ("T2-B0.jpg", "B0：缓存GrabCut候选"),
        ("T2-B1.jpg", "B1：AI修订后正交几何（蓝色）"),
        ("T2-comparison.jpg", "A/B1原生坐标叠加；右下凹角为比较重点"),
        ("T2-B1-layout.svg", "B1规则几何：重建坐标下全部为水平/竖直边"),
        ("T3-source.jpg", "S05原图"),
        ("T3-rejected.jpg", "拒绝：算法把双环局部连成同一组件"),
        ("T1-T3-retained.jpg", "保留：已有双环与间隙；不重复询问身份"),
    ]
    content = "".join(
        f'<figure><figcaption>{html.escape(label)}</figcaption><img src="{path}"></figure>'
        for path, label in cards
    )
    page = '<!doctype html><meta charset="utf-8"><title>AA skill三个任务</title>'
    page += (
        "<style>body{font-family:sans-serif;max-width:1100px;margin:30px auto;"
        "background:#171d27;color:#eee}img{width:100%}figure{margin:25px 0}"
        "a{color:#87cfff}</style>"
    )
    page += (
        "<h1>AA skill：三个已知案例任务</h1><p>T1接续通过；T3拒绝退化通过；"
        "T2仅候选，质量提升尚未正式确立。没有重训、全图推断或修改原成果。"
        "此为同Agent已知案例回归。</p>"
    )
    page += (
        "<p>黄色为旧几何，蓝色为新候选。距离变小仅指接近历史AI观察，"
        "不是精确边界误差或准确率。无需重新验收N01–N12。</p>"
    )
    page += (
        content + '<p><a href="report.json">结果</a> · <a href="plan.json">冻结任务与证据</a></p>'
    )
    (output / "index.html").write_text(page)
    manifest = {p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().output), ensure_ascii=False, indent=2))
