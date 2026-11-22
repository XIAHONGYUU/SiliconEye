"""Make local rectangular pilots from explicitly reviewed horizontal source paths.

Run: python -m silicon_eye.ridge_regularization --spec FILE --output NEW_RUN_DIR
Requires Pillow/OpenCV/NumPy. Photometric widths are proposals, never PDK dimensions.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .metal_extent_batch import put, read, ref, require
from .review_package import Inputs
from .review_sheet import build


def horizontal_candidate(gray, fragments, relations):
    """Bridge only approved adjacent pairs; propose a separate, axis-aligned local ribbon."""
    require(gray.ndim == 2 and np.isfinite(gray).all(), "Invalid source image")
    fragments = sorted(fragments, key=lambda row: row["points"][0][0])
    require(len(fragments) >= 2, "At least two reviewed fragments are required")
    require(len({f["fragment_id"] for f in fragments}) == len(fragments), "Duplicate fragment")
    reviewed = {frozenset(row["fragments"]) for row in relations}
    gaps = []
    for left, right in zip(fragments, fragments[1:], strict=False):
        require(
            frozenset([left["fragment_id"], right["fragment_id"]]) in reviewed,
            "Unreviewed adjacent pair; cannot bridge",
        )
        gap = right["points"][0][0] - left["points"][-1][0]
        require(gap > 0, "Overlapping source intervals require separate topology analysis")
        gaps.append(gap)
    points = np.asarray([p for row in fragments for p in row["points"]], dtype=float)
    require(np.isfinite(points).all() and (np.diff(points[:, 0]) > 0).all(), "Invalid path")
    require(
        (points >= 0).all() and (points < np.array([gray.shape[1], gray.shape[0]])).all(),
        "Path outside source image",
    )
    span = float(points[-1, 0] - points[0, 0])
    require(np.ptp(points[:, 1]) < span / 10, "Not a near-horizontal source path")
    smooth = cv2.GaussianBlur(gray.astype(np.float32), (0, 0), sigmaX=3, sigmaY=1)
    widths = []
    for x, y in points[::4]:
        x, y = round(x), round(y)
        require(20 <= y < gray.shape[0] - 20, "Width profile is source-clipped")
        profile = smooth[y - 20 : y + 21, x]
        background = float(np.quantile(profile, 0.2))
        require(profile[20] - background > 5, "Insufficient ridge contrast for width proposal")
        cutoff = background + (float(profile[20]) - background) / 2
        low = high = 20
        while low > 0 and profile[low - 1] > cutoff:
            low -= 1
        while high < 40 and profile[high + 1] > cutoff:
            high += 1
        require(low > 0 and high < 40, "Width profile reaches sampling limit")
        widths.append(high - low + 1)
    width = int(round(float(np.median(widths))))
    return dict(
        fragments=[row["fragment_id"] for row in fragments],
        source_points=points.tolist(),
        approved_gap_spans_px=gaps,
        source_x_interval_px=[float(points[0, 0]), float(points[-1, 0])],
        source_y_excursion_px=float(np.ptp(points[:, 1])),
        photometric_width_px=width,
        width_p10_p90_px=np.quantile(widths, [0.1, 0.9]).tolist(),
        width_method="half-contrast width after sigmaX=3/sigmaY=1 smoothing; radius=20",
        local_polygon=[[0, 0], [span, 0], [span, width], [0, width]],
        local_frame="independent illustrative pixel frame; not a global source projection",
        physical_endpoints="unknown",
        width_human_approved=False,
        geometry_adopted=False,
        source_to_design_transform=None,
    )


def evidence(image, candidate, target_id, path):
    points = candidate["source_points"]
    xs, ys = np.asarray(points).T
    width = candidate["photometric_width_px"]
    margin = max(80, (width or 0) * 3)
    bounds = [
        max(0, int(min(xs)) - 50), max(0, int(min(ys)) - margin),
        min(image.width, int(max(xs)) + 51), min(image.height, int(max(ys)) + margin + 1),
    ]
    raw = image.crop(bounds)
    marked = raw.copy()
    draw = ImageDraw.Draw(marked)
    # Dashed ridge guide; a bright ridge need not be the conductor's center.
    for i in range(0, len(points) - 1, 2):
        a, b = points[i : i + 2]
        draw.line([(a[0] - bounds[0], a[1] - bounds[1]),
                   (b[0] - bounds[0], b[1] - bounds[1])], fill="#00cfff", width=2)
    scale = min(1500 / raw.width, 350 / raw.height)
    size = tuple(round(n * scale) for n in raw.size)
    panel = Image.new("RGB", (max(1000, size[0] + 40), 2 * size[1] + 260), "#fafafa")
    draw = ImageDraw.Draw(panel)
    draw.text((20, 10), f"{target_id} | SOURCE CONTEXT (top) / REVIEWED RIDGE GUIDE (middle)",
              fill="black", font_size=20)
    panel.paste(raw.resize(size), (20, 45))
    panel.paste(marked.resize(size), (20, 65 + size[1]))
    y = 100 + 2 * size[1]
    if width is None:
        draw.text((20, y), "HOLD: bright ridge may be a wide-band EDGE, not its center.",
                  fill="#b45309", font_size=22)
        draw.text((20, y + 40), "No rectangle or width fabricated. Boundary analysis required.",
                  fill="black", font_size=20)
        panel.save(path)
        return bounds
    span = candidate["local_polygon"][1][0]
    height = max(3, round(candidate["photometric_width_px"] * scale))
    draw.text((20, y), "LOCAL RECTANGLE PROPOSAL | separate frame, not projected onto photo",
              fill="black", font_size=18)
    draw.rectangle((20, y + 40, 20 + round(span * scale), y + 40 + height),
                   fill="#8b5cf6")
    draw.text((20, y + 65 + height),
              f"width proposal: {candidate['photometric_width_px']} px | "
              f"visible span: {span:g} px",
              fill="black", font_size=17)
    draw.text((20, y + 90 + height), "Physical ends and neighboring spacing UNKNOWN",
              fill="black", font_size=17)
    panel.save(path)
    return bounds


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    require(output.is_relative_to(root / "runs") and not output.exists(), "Use new runs directory")
    spec = read(spec_path)
    inputs = Inputs(root)
    state = inputs.document(spec["state"])
    inputs.evidence(state)
    triage = inputs.document(spec["triage"])
    inputs.evidence(triage)
    inputs.read(spec["photo"])
    require(spec["photo"] == triage["sources"]["photo"], "Wrong source photograph")
    rows = {row["fragment_id"]: row for row in triage["rows"]}
    excluded = {row["fragment_id"] for row in state["reviewed_edges"]}
    image = Image.open(root / spec["photo"]["path"]).convert("RGB")
    gray = np.asarray(image.convert("L"))
    candidates, held = [], []
    require(len({t["id"] for t in spec["targets"]}) == len(spec["targets"]), "Duplicate target")
    for target in spec["targets"]:
        require(set(target["fragments"]).isdisjoint(excluded), "Target includes reviewed edge")
        require(all(f in rows for f in target["fragments"]), "Unknown fragment")
        fragments = [rows[f] for f in target["fragments"]]
        try:
            c = horizontal_candidate(gray, fragments, state["reviewed_relations"])
        except ValueError as exc:
            if str(exc) not in {"Width profile reaches sampling limit",
                                "Insufficient ridge contrast for width proposal"}:
                raise
            held.append(dict(
                id=target["id"], fragments=target["fragments"], reason=str(exc),
                source_points=[p for row in fragments for p in row["points"]],
                photometric_width_px=None, local_polygon=None,
                status="boundary_analysis_required", geometry_adopted=False,
            ))
        else:
            candidates.append(dict(id=target["id"], **c))
    require(candidates, "No width candidates; all targets require boundary analysis")
    output.mkdir(parents=True)
    items = []
    for c in candidates:
        path = output / (c["id"] + ".png")
        c["source_context_bounds"] = evidence(image, c, c["id"], path)
        items.append(dict(
            id=c["id"], type="metal_fragment", title=f"{c['id']}：局部水平矩形候选",
            prompt="只审本段是否适合用连续水平矩形表达，以及所示线宽有无明显失真。"
                   "青虚线为已审来源亮脊参考，不保证是中心或边界；紫色矩形在独立局部坐标中。"
                   "可备注偏宽/偏窄；已审片段关系不重问，不批准物理端点、邻线间距或跨层连接。",
            required=True,
            facts={k: c[k] for k in ["fragments", "photometric_width_px", "width_p10_p90_px",
                                     "source_y_excursion_px", "source_x_interval_px"]},
            evidence=[dict(**ref(root, path), label="原图／亮脊参考／独立矩形候选",
                           role="detail", frame="m3")],
            checks=[dict(id="rectangle", label="本段水平矩形表达合理", required=True),
                    dict(id="width", label="候选线宽无明显失真", required=True)],
        ))
    for c in held:
        path = output / (c["id"] + ".png")
        c["source_context_bounds"] = evidence(image, c, c["id"], path)
        items.append(dict(
            id=c["id"], type="metal_fragment", title=f"{c['id']}：宽带边界待分析（仅参考）",
            prompt="亮脊关系已经批准，但宽度剖面触及采样上限，不能将亮脊当金属中心。"
                   "本项暂停矩形化，先分析真实上下边界；不要求重审已批准来源关系。",
            review_mode="context", required=False, facts=dict(reason=c["reason"]), checks=[],
            evidence=[dict(**ref(root, path), label="原图／亮脊：未生成矩形",
                           role="detail", frame="m3")],
        ))
    result = dict(kind="local_rectangular_geometry_pilot", candidates=candidates, held=held,
                  sources=dict(spec=ref(root, spec_path), algorithm=ref(root, Path(__file__))),
                  geometry_adopted=False, net_edges=[], complete_network=False,
                  checks=dict(axis_aligned=True, reviewed_adjacent_pairs_only=True,
                              global_registration_verified=False, spacing_verified=False,
                              physical_drc_verified=False))
    put(output / "candidates.json", result)
    review = dict(
        schema_version=1, kind="silicon_eye_review_sheet", package_id=spec["package_id"],
        date=spec["date"], stage="METAL", title="已审M3路径：局部矩形候选与宽带暂停项",
        summary=f"{len(candidates)}处矩形/线宽候选；{len(held)}处边界待分析，仅供参考。"
                "不重复审批来源身份。",
        scope=dict(frame="m3", native_bounds=[0, 0, image.width, image.height],
                   note="仅三个列明局部路径；每个矩形使用独立局部坐标，不是全幅配准或全部覆盖。"),
        sources=dict(candidates=ref(root, output / "candidates.json"), **spec),
        items=items, questions=[], limits=[
            "线宽是照片半对比宽度候选，不是工艺尺寸、PDK规则或DRC通过。",
            "不批准邻线间距、实际物理终点、全局投影、VIA、跨层承载或网表。",
            "每个矩形为独立局部坐标；不能直接拼接到既有54金属模型。",
        ],
    )
    # Only source references belong in the fixed sheet's sources dictionary.
    review["sources"] = {k: v for k, v in review["sources"].items()
                         if isinstance(v, dict) and "sha256" in v}
    put(output / "review-spec.json", review)
    build(root, output / "review-spec.json", output / "review")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(Path.cwd(), args.spec.resolve(), args.output)
