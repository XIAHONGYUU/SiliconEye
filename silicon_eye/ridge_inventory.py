"""Inventory near-horizontal bright ridge fragments, not electrical conductors.

Run: python -m silicon_eye.ridge_inventory --spec FILE --output NEW_DIR
Requires project Pillow/OpenCV/NumPy dependencies. Input pixels remain immutable.
"""

import argparse
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .metal_extent_batch import put, read, ref, require
from .review_package import Inputs
from .review_sheet import build


def detect(gray, *, threshold=10.0, minimum_span=120):
    """Return source-bound components without closing gaps or assigning metal identity."""
    require(gray.ndim == 2 and np.isfinite(gray).all(), "Invalid grayscale image")
    require(threshold > 0 and minimum_span >= 2, "Invalid detector parameters")
    smooth = cv2.GaussianBlur(gray.astype(np.float32), (0, 0), sigmaX=3, sigmaY=1)
    background = cv2.GaussianBlur(smooth, (0, 0), sigmaX=0.01, sigmaY=6)
    ridge = smooth - background
    peaks = cv2.dilate(ridge, np.ones((5, 1), np.uint8))
    supported = ((ridge >= peaks - 1e-5) & (ridge >= threshold)).astype(np.uint8)
    # One pixel vertically accommodates shallow slopes. No horizontal closing/gap bridging.
    connected = cv2.dilate(supported, np.ones((3, 1), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(connected, connectivity=8)
    fragments = []
    rejected = dict(short=0, non_horizontal=0)
    for idx in range(1, count):
        x, y, w, h, area = map(int, stats[idx])
        if w < minimum_span:
            rejected["short"] += 1
            continue
        if w < h * 4:
            rejected["non_horizontal"] += 1
            continue
        region = (labels[y : y + h, x : x + w] == idx) & supported[y : y + h, x : x + w].astype(
            bool
        )
        points = []
        ambiguous_columns = 0
        # Keep column samples at 8px plus boundaries; branching is retained as an explicit flag.
        for col in range(w):
            ys = np.flatnonzero(region[:, col])
            if len(ys) and ys[-1] - ys[0] > 3:
                ambiguous_columns += 1
            if len(ys) and (col % 8 == 0 or col == w - 1):
                points.append([x + col, y + float(np.median(ys))])
        if len(points) < 2:
            continue
        fragments.append(
            dict(
                bounds=[x, y, x + w, y + h],
                points=points,
                native_x_span_px=w - 1,
                area_px=area,
                branch_or_parallel_overlap=ambiguous_columns > 0,
                ambiguous_columns=ambiguous_columns,
                identity="unassigned",
                physical_endpoints="unknown",
                geometry_human_approved=False,
            )
        )
    fragments.sort(
        key=lambda f: (sum(p[1] for p in f["points"]) / len(f["points"]), f["bounds"][0])
    )
    for i, f in enumerate(fragments, 1):
        f["id"] = f"RIDGE-{i:04}"
    return fragments, rejected


def run(root, spec_path, output):
    start = time.perf_counter()
    root, output = Path(root).resolve(), Path(output).resolve()
    require(not output.exists() and output.is_relative_to(root / "runs"), "Use new runs directory")
    spec = read(spec_path)
    inputs = Inputs(root)
    inputs.read(spec["photo"])
    image = Image.open(root / spec["photo"]["path"]).convert("RGB")
    require(image.size == tuple(spec["source_wh"]), "Photo dimensions mismatch")
    fragments, rejected = detect(np.asarray(image.convert("L")), **spec["parameters"])
    recognition_seconds = time.perf_counter() - start
    output.mkdir(parents=True)
    inventory = dict(
        kind="source_ridge_fragment_inventory",
        photo=spec["photo"],
        source_wh=spec["source_wh"],
        parameters=spec["parameters"],
        algorithm=ref(root, Path(__file__)),
        fragments=fragments,
        filtered_component_counts=rejected,
        limits=[
            "Fragments are not physical metal count or net identity.",
            "Broad metal interiors, vertical lines, weak/short features not covered.",
            "No source-to-design projection or network construction.",
        ],
    )
    put(output / "inventory.json", inventory)
    put(output / "spec.json", spec)
    # Match only to prior traced source paths; geometric overlap does not assign identity.
    reference_tracks = []
    for source in spec.get("previous_traces", []):
        doc = inputs.document(source)
        reference_tracks += doc["tracks"]
    for f in fragments:
        refs = set()
        sampled = np.asarray(f["points"])
        covered = np.zeros(len(sampled), dtype=bool)
        for track in reference_tracks:
            xy = np.asarray(track["points"])
            inside = (sampled[:, 0] >= xy[0, 0]) & (sampled[:, 0] <= xy[-1, 0])
            p = sampled[inside]
            if len(p) >= 3:
                close = np.abs(p[:, 1] - np.interp(p[:, 0], xy[:, 0], xy[:, 1])) <= 4
                if close.mean() >= 0.7:
                    refs.add(track["id"])
                    covered[np.flatnonzero(inside)[close]] = True
        f["prior_trace_overlap_ids"] = sorted(refs)
        f["prior_trace_coverage_fraction"] = float(covered.mean())
        f["review_category"] = (
            "previous_trace_context" if covered.mean() >= 0.9 else "unassigned_candidate"
        )
        f["peripheral_edge_risk"] = f["bounds"][0] >= 5200
    put(output / "inventory.json", inventory)
    items = []
    regions = []
    palette = ["#ee4444", "#00aaaa", "#d09000", "#cc44cc", "#229922", "#3366ee"]
    width, height = image.size
    band_height = spec.get("band_height", 540)
    for band, top in enumerate(range(0, height, band_height), 1):
        bottom = min(height, top + band_height)
        # Assign once by center y, show full-frame context separately for border-crossing fragments.
        selected = [
            f for f in fragments if top <= np.median(np.asarray(f["points"])[:, 1]) < bottom
        ]
        if not selected:
            continue
        group = f"BAND-{band:02}"
        regions.append(
            dict(id=group, bounds=[0, top, width, bottom], ids=[f["id"] for f in selected])
        )
        evidence = []
        for side, left, right in [("LEFT", 0, width // 2), ("RIGHT", width // 2, width)]:
            # Padding displays source continuity at tile borders; ownership remains by center y.
            box = [
                max(0, left - 50),
                max(0, top - 60),
                min(width, right + 50),
                min(height, bottom + 60),
            ]
            raw = image.crop(box)
            marked = raw.copy()
            draw = ImageDraw.Draw(marked)
            for i, f in enumerate(selected):
                points = [(x - box[0], y - box[1]) for x, y in f["points"]]
                color = (
                    "#888888"
                    if f["review_category"] == "previous_trace_context"
                    else palette[i % len(palette)]
                )
                draw.line(points, fill=color, width=2)
                visible = [
                    (x, y) for x, y in points if 0 <= x < marked.width and 0 <= y < marked.height
                ]
                if visible:
                    x, y = visible[min(3, len(visible) - 1)]
                    draw.text((max(0, x), max(0, y - 12)), f["id"], fill=color)
            panel = Image.new("RGB", (raw.width, raw.height * 2 + 24), "white")
            panel.paste(raw, (0, 24))
            panel.paste(marked, (0, raw.height + 24))
            ImageDraw.Draw(panel).text(
                (4, 5), "SOURCE / CANDIDATES (colored); prior trace context (gray)", fill="black"
            )
            path = output / f"{group}-{side}.png"
            panel.save(path)
            evidence.append(
                dict(
                    **ref(root, path),
                    label=f"{side} 原图/候选上下对照（可放大）",
                    role="detail",
                    frame=spec["frame"],
                )
            )
        new = [f for f in selected if f["review_category"] != "previous_trace_context"]
        items.append(
            dict(
                id=group,
                type="metal_fragment",
                title=f"区域{band}：原生y{top}–{bottom}",
                prompt="集中检查彩色候选是否落在可见金属线，以及是否明显漏检/串线。灰色旧路径仅作上下文，彩色片段内与旧路径重合的部分也不重审。右侧焊盘边缘不是细导体中心线，应备注排除。通过仅认可片段清单，不确认身份、端点、连接或规则几何。问题请备注RIDGE编号；密集区域不能确认时选不确定。",
                review_mode="decision" if new else "context",
                required=bool(new),
                evidence=evidence,
                facts={
                    "彩色未分配片段数": len(new),
                    "灰色旧路径重叠片段数": len(selected) - len(new),
                    "有分叉/并行合并风险的片段": [
                        f["id"] for f in new if f["branch_or_parallel_overlap"]
                    ],
                    "未分配片段编号": [f["id"] for f in new],
                    "外围边缘需排除或单独分类": [f["id"] for f in new if f["peripheral_edge_risk"]],
                },
                checks=[
                    dict(
                        id="source",
                        label="彩色候选与原图可见线对应，明显错误/遗漏已备注",
                        required=True,
                    ),
                    dict(
                        id="scope",
                        label="只审来源片段清单，不批准身份、连接或物理端点",
                        required=True,
                    ),
                ],
            )
        )
    put(output / "regions.json", regions)
    review = dict(
        schema_version=1,
        kind="silicon_eye_review_sheet",
        package_id=spec["package_id"],
        stage="METAL",
        stage_label="金属来源候选",
        date=spec["date"],
        title="全幅M3来源片段清查：按区域集中复核",
        summary="新范围发现阶段：候选片段不等于新导体；不改已审几何或连接。",
        scope=dict(
            frame=spec["frame"],
            native_bounds=[0, 0, width, height],
            note="整幅计算，近水平亮脊线专用；不承诺全类型金属召回率。",
        ),
        sources=dict(photo=spec["photo"], inventory=ref(root, output / "inventory.json")),
        items=items,
        questions=[],
        limits=inventory["limits"],
    )
    put(output / "review-spec.json", review)
    build(root, output / "review-spec.json", output / "review")
    timing = dict(
        status="PASS",
        recognition_seconds=recognition_seconds,
        total_seconds=time.perf_counter() - start,
        fragments=len(fragments),
        unassigned_fragments=sum(
            f["review_category"] != "previous_trace_context" for f in fragments
        ),
        review_groups=len(items),
        source_pixels=width * height,
    )
    put(output / "timing.json", timing)
    return timing


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--spec", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(run(args.root, args.spec, args.output))
