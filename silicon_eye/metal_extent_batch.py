"""Batch near-horizontal same-layer extents. Run with --spec FILE --output NEW_DIR.

Requires the metal-batch extra. Design intervals are explicit, not inferred projections.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import LineString, box
from shapely.ops import unary_union

from .conductive_workflow import load_parent
from .conductive_workflow import run as integrate
from .review_package import Inputs
from .review_sheet import build
from .ridge_tracing import DEFAULTS, trace


def read(path):
    return json.loads(Path(path).read_text())


def put(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def ref(root, path):
    path = Path(path).resolve()
    return dict(
        path=str(path.relative_to(root)), sha256=hashlib.sha256(path.read_bytes()).hexdigest()
    )


def require(condition, message):
    if not condition:
        raise ValueError(message)


def clean(request):
    request = copy.deepcopy(request)
    for key in (
        "added_metal_ids",
        "added_interface_ids",
        "extension_evidence",
        "interface_extension_evidence",
        "allowed_changed_ids",
        "revision_evidence",
        "canvas_extension_evidence",
        "resolved_limits",
    ):
        request.pop(key, None)
    request["reviews"] = []
    return request


def preflight(root, spec):
    require(spec["schema_version"] == 1, "Unsupported schema")
    for name in [spec["package_id"]] + [g["id"] for g in spec["groups"]]:
        require(re.fullmatch(r"[A-Za-z0-9_-]+", name), "Unsafe package/group id")
    inputs = Inputs(root)
    model, request = load_parent(inputs, spec["parent"])
    sample = inputs.document(request["sample"])
    inputs.read(spec["photo"])
    require(spec["frame"] in request["frames"], "Unknown source frame")
    # Bind the declared image to the existing model, not merely an arbitrary valid hash.
    require(spec["photo"] == model["source_photos"][spec["frame"]], "Wrong frame photo")
    with Image.open(root / spec["photo"]["path"]) as image:
        width, height = image.size

    def box_ok(box):
        return (
            len(box) == 4
            and all(type(v) is int for v in box)
            and 0 <= box[0] < box[2] <= width
            and 0 <= box[1] < box[3] <= height
        )

    bounds = spec["bounds"]
    require(box_ok(bounds), "Crop outside photo")
    require(
        type(spec["seed_x"]) is int and bounds[0] < spec["seed_x"] < bounds[2] - 1,
        "Seed x must be inside crop",
    )
    targets = spec["targets"]
    ids = [t["id"] for t in targets]
    seeds = [t["seed_y"] for t in targets]
    require(ids and len(set(ids)) == len(ids), "Empty or duplicate targets")
    require(
        all(type(y) is int and bounds[1] <= y < bounds[3] for y in seeds)
        and all(a < b for a, b in zip(seeds, seeds[1:], strict=False)),
        "Invalid seed order/range",
    )
    features = {f["id"]: f for f in sample["features_by_layer"][spec["layer"]]}
    require(set(ids) <= features.keys(), "Unknown metal id")
    require(
        spec["groups"] and len({g["id"] for g in spec["groups"]}) == len(spec["groups"]),
        "Empty or duplicate groups",
    )
    margin = spec.get("canvas_margin", 20)
    require(type(margin) is int and margin >= 0, "Invalid margin")
    require(spec.get("minimum_trace_gap_px", 2) > 0, "Invalid trace gap")
    for target in targets:
        f = features[target["id"]]
        ys = [p[1] for p in f["design_path"]]
        require(
            len(set(ys)) == 1 and f["design_width"] > 0, "Only horizontal design paths supported"
        )
        old_ids = {p["id"] for p in f.get("local_parts", [])}
        for group in spec["groups"]:
            require(spec["package_id"] + "-" + group["id"] not in old_ids, "Part already exists")
    for group in spec["groups"]:
        lo, hi = group["native_x"]
        require(bounds[0] <= lo < hi <= bounds[2] - 1, "Group outside trace range")
        a, b = group["design_x"]
        require(np.isfinite([a, b]).all() and a < b, "Invalid design interval")
        require(box_ok(group["source_view"]), "Evidence view outside photo")
        require(
            group["source_view"][0] <= lo and group["source_view"][2] > hi,
            "Evidence view must contain group x range",
        )
    for target in targets:
        f = features[target["id"]]
        require(f.get("source_frame", spec["frame"]) == spec["frame"], "Metal frame mismatch")
        footprint = unary_union(
            [LineString(f["design_path"]).buffer(f["design_width"] / 2, cap_style=2)]
            + [box(*p["bounds"]) for p in f.get("local_parts", [])]
        )
        y = f["design_path"][0][1]
        for g in spec["groups"]:
            addition = box(
                g["design_x"][0],
                y - f["design_width"] / 2,
                g["design_x"][1],
                y + f["design_width"] / 2,
            )
            require(footprint.intersects(addition), "Detached design extent")
            require(addition.difference(footprint).area > 0, "Extent adds no new area")
    return model, request, sample, inputs


def recognize(root, spec):
    x0, y0, x1, y1 = spec["bounds"]
    with Image.open(root / spec["photo"]["path"]) as image:
        gray = np.asarray(image.crop(spec["bounds"]).convert("L"))
    seeds = [t["seed_y"] - y0 for t in spec["targets"]]
    sx, end = spec["seed_x"] - x0, x1 - x0 - 1
    right = trace(gray, seeds, sx, end)
    left = trace(gray[:, ::-1], seeds, end - sx, end)
    tracks = []
    for target, a, b in zip(spec["targets"], left, right, strict=True):
        require(not a["unknown_spans"] and not b["unknown_spans"], "Unsupported trace span")
        points = [[x1 - 1 - x, y + y0] for x, y in a["points"]][::-1]
        points += [[x + x0, y + y0] for x, y in b["points"]][1:]
        for g in spec["groups"]:
            segment = [p for p in points if g["native_x"][0] <= p[0] <= g["native_x"][1]]
            require(len(segment) >= 2, "Group has fewer than two trace samples")
            require(
                all(g["source_view"][1] <= p[1] < g["source_view"][3] for p in segment),
                "Evidence view clips traced group",
            )
        tracks.append(
            dict(
                id=target["id"],
                points=points,
                unknown_spans=[],
                end_states=["scope_exit_not_physical_end"] * 2,
            )
        )
    rows = np.asarray([np.asarray(t["points"])[:, 1] for t in tracks])
    gap = float(np.diff(rows, axis=0).min()) if len(rows) > 1 else None
    require(gap is None or gap >= spec.get("minimum_trace_gap_px", 2), "Crossed or merged traces")
    return dict(
        actor="AI_algorithm_candidate",
        photo=spec["photo"],
        bounds=spec["bounds"],
        parameters=DEFAULTS,
        tracks=tracks,
        minimum_interline_gap_px=gap,
    )


def evidence(root, output, spec, tracks, old_sample, sample, replay):
    items = []
    colors = ["#ff4040", "#00ffff", "#ffff00", "#ff40ff", "#00ff40", "#4080ff"]
    features = {f["id"]: f for f in sample["features_by_layer"][spec["layer"]]}
    old = {f["id"]: f for f in old_sample["features_by_layer"][spec["layer"]]}
    with Image.open(root / spec["photo"]["path"]) as image:
        for group in spec["groups"]:
            box = group["source_view"]
            raw = image.crop(box).convert("RGB")
            marked = raw.copy()
            draw = ImageDraw.Draw(marked)
            for i, tr in enumerate(tracks):
                color = colors[i % len(colors)]
                draw.line([(x - box[0], y - box[1]) for x, y in tr["points"]], fill=color, width=1)
                x = max(box[0] + 8, spec["bounds"][0])
                y = np.interp(x, *np.asarray(tr["points"]).T)
                draw.text((x - box[0], y - box[1] - 11), tr["id"], fill=color)
            panel = Image.new("RGB", (raw.width, raw.height * 2 + 24), "white")
            panel.paste(raw, (0, 24))
            panel.paste(marked, (0, 24 + raw.height))
            ImageDraw.Draw(panel).text(
                (5, 5), "SOURCE / CANDIDATE: crop exits are not endpoints", fill="black"
            )
            source_path = output / (group["id"] + "-source.png")
            panel.save(source_path)
            # Design view uses shared coordinates, displaying the existing footprint in gray.
            a, b = group["design_x"]
            ys = [features[t["id"]]["design_path"][0][1] for t in tracks]
            db = [a - 40, min(ys) - 20, b + 40, max(ys) + 20]
            scale = min(1.0, 1600 / (db[2] - db[0]))
            design = Image.new(
                "RGB",
                (int((db[2] - db[0]) * scale) + 1, int((db[3] - db[1]) * scale) + 25),
                "white",
            )
            d = ImageDraw.Draw(design)

            def rectangle(bounds, color, d=d, db=db, scale=scale):
                d.rectangle(
                    [
                        (int((bounds[0] - db[0]) * scale), int((bounds[1] - db[1]) * scale) + 24),
                        (int((bounds[2] - db[0]) * scale), int((bounds[3] - db[1]) * scale) + 24),
                    ],
                    fill=color,
                )

            for tr in tracks:
                f = old[tr["id"]]
                half = f["design_width"] / 2
                xs = [p[0] for p in f["design_path"]]
                y = f["design_path"][0][1]
                rectangle([min(xs), y - half, max(xs), y + half], "#aaaaaa")
                for p in f.get("local_parts", []):
                    rectangle(p["bounds"], "#aaaaaa")
                rectangle([a, y - half, b, y + half], "#3488ee")
            d.text((5, 5), "GRAY: existing / BLUE: candidate; relative design only", fill="black")
            design_path = output / (group["id"] + "-design.png")
            design.save(design_path)
            items.append(
                dict(
                    id=group["id"],
                    type="metal_fragment",
                    title=group["title"],
                    prompt="整组核对新增范围的连续性与行序；范围出口不是物理端点。",
                    review_mode="context" if replay else "decision",
                    required=not replay,
                    facts={"对象": [t["id"] for t in tracks], "原生范围x": group["native_x"]},
                    evidence=[
                        dict(
                            **ref(root, source_path),
                            label="原图与路径",
                            role="detail",
                            frame=spec["frame"],
                        ),
                        dict(
                            **ref(root, design_path),
                            label="旧足迹与新增几何",
                            role="design",
                            frame="design",
                        ),
                    ],
                )
            )
    review = dict(
        schema_version=1,
        kind="silicon_eye_review_sheet",
        package_id=spec["package_id"],
        date=spec["date"],
        stage="METAL",
        stage_label="金属",
        title=spec["title"],
        summary="软件重放验证，无需重复裁决。" if replay else "整批同层范围扩展候选，集中复核。",
        scope=dict(
            frame=spec["frame"],
            native_bounds=spec["bounds"],
            note="仅本轮范围，不声明物理端点或跨层连接。",
        ),
        sources={spec["frame"]: spec["photo"]},
        items=items,
        questions=[],
        limits=[
            "原生锚点保留；相对规则设计不是精确像素投影。",
            "不新增孔、接口或连接；原有未知保持。",
        ],
    )
    put(output / "review-spec.json", review)


def run(root, spec_path, output, *, replay=False):
    root, output = Path(root).resolve(), Path(output).resolve()
    require(
        not output.exists() and output.is_relative_to(root / "runs"),
        "Output must be a new directory under project runs/",
    )
    start = time.perf_counter()
    timings = {}
    stage = "preflight"
    spec = read(spec_path)
    previous, request, original, inputs = preflight(root, spec)
    timings[stage] = time.perf_counter() - start
    output.mkdir(parents=True)
    put(output / "spec.json", spec)

    def checkpoint(name):
        nonlocal stage, tick
        timings[stage] = time.perf_counter() - tick
        stage, tick = name, time.perf_counter()

    tick = time.perf_counter()
    stage = "recognition"
    try:
        traces = recognize(root, spec)
        traces["algorithm"] = ref(root, Path(__file__).with_name("ridge_tracing.py"))
        put(output / "traces.json", traces)
        checkpoint("candidate_preparation")
        sample = copy.deepcopy(original)
        ledger = inputs.document(sample["local_part_source_evidence"])
        ledger.update(
            date=spec["date"], reason="Batch same-layer outward extents; native anchors retained."
        )
        features = {f["id"]: f for f in sample["features_by_layer"][spec["layer"]]}
        changes, rectangles = [], []
        for tr in traces["tracks"]:
            f = features[tr["id"]]
            y = f["design_path"][0][1]
            half = f["design_width"] / 2
            parts = []
            for group in spec["groups"]:
                pid = spec["package_id"] + "-" + group["id"]
                a, b = group["design_x"]
                bounds = [a, y - half, b, y + half]
                rectangles.append(bounds)
                parts.append(pid)
                f.setdefault("local_parts", []).append(
                    dict(
                        id=pid,
                        bounds=bounds,
                        basis="Same-layer continuation; relative design, not projection.",
                    )
                )
                ledger["parts"].append(
                    dict(
                        metal_id=f["id"],
                        part_id=pid,
                        source_frame=spec["frame"],
                        source_photo=spec["photo"],
                        native_scope_bounds=spec["bounds"],
                        native_path=[
                            p
                            for p in tr["points"]
                            if group["native_x"][0] <= p[0] <= group["native_x"][1]
                        ],
                        design_bounds=bounds,
                        source_role="AI_OBSERVED_SAME_LAYER_CONTINUATION",
                        geometry_human_approved=False,
                        native_width_measured=False,
                        precise_projection_qualified=False,
                        scope_exit=dict(state="scope_exit_not_physical_end", physical_end=False),
                    )
                )
            changes.append(
                dict(
                    id=f["id"],
                    native_anchor_preserved=True,
                    old_footprint_preserved=True,
                    new_parts=parts,
                )
            )
        margin = spec.get("canvas_margin", 20)
        canvas = original.get("canvas_bounds", [0, 0, *original["canvas_wh"]])
        wanted = [
            min(canvas[0], int(np.floor(min(r[0] for r in rectangles) - margin))),
            canvas[1],
            max(canvas[2], int(np.ceil(max(r[2] for r in rectangles) + margin))),
            max(canvas[3], int(np.ceil(max(r[3] for r in rectangles) + margin))),
        ]
        require(min(r[1] for r in rectangles) >= canvas[1], "Top canvas extension unsupported")
        put(output / "local-parts-ledger.json", ledger)
        sample["local_part_source_evidence"] = ref(root, output / "local-parts-ledger.json")
        checkpoint("canvas_and_integration")
        parent = spec["parent"]
        canvas_sample = copy.deepcopy(original)
        for side, index in [("left", 0), ("right", 2), ("bottom", 3)]:
            if wanted[index] == canvas[index]:
                continue
            after = canvas.copy()
            after[index] = wanted[index]
            beforewh = canvas_sample["canvas_wh"]
            canvas_sample.update(
                canvas_bounds=after, canvas_wh=[after[2] - after[0], after[3] - after[1]]
            )
            prefix = output / ("canvas-" + side)
            put(prefix.with_suffix(".sample.json"), canvas_sample)
            ev = dict(
                kind="conductive_canvas_extension",
                actor="AI",
                reason="Batch viewport extension only.",
                parent=parent,
                from_canvas_wh=beforewh,
                to_canvas_wh=canvas_sample["canvas_wh"],
                from_canvas_bounds=canvas,
                to_canvas_bounds=after,
                direction=side.upper() + "_ONLY",
                origin_xy=[0, 0],
                scale_xy=[1, 1],
                translation_xy=[0, 0],
                geometry_human_approved=False,
            )
            put(prefix.with_suffix(".evidence.json"), ev)
            req = clean(request)
            req.update(
                parent=parent,
                sample=ref(root, prefix.with_suffix(".sample.json")),
                canvas_extension_evidence=ref(root, prefix.with_suffix(".evidence.json")),
            )
            put(prefix.with_suffix(".request.json"), req)
            integrate(root, prefix.with_suffix(".request.json"), prefix)
            parent = ref(root, prefix / "manifest.json")
            request = read(prefix / "request.json")
            canvas = after
        sample.update(
            canvas_bounds=canvas, canvas_wh=[canvas[2] - canvas[0], canvas[3] - canvas[1]]
        )
        put(output / "sample.json", sample)
        put(
            output / "revision-evidence.json",
            dict(
                actor="AI",
                reason=ledger["reason"],
                geometry_human_approved=False,
                sources=dict(
                    traces=ref(root, output / "traces.json"),
                    ledger=ref(root, output / "local-parts-ledger.json"),
                ),
                changes=changes,
            ),
        )
        req = clean(request)
        req.update(
            parent=parent,
            sample=ref(root, output / "sample.json"),
            allowed_changed_ids=[t["id"] for t in traces["tracks"]],
            revision_evidence=ref(root, output / "revision-evidence.json"),
        )
        put(output / "request.json", req)
        model, report = integrate(root, output / "request.json", output / "work")
        require(report["status"].startswith("TECHNICAL_PASS"), "Integration did not pass")
        checkpoint("preservation")
        ids = {t["id"] for t in traces["tracks"]}
        for layer, objects in original["features_by_layer"].items():
            revised = {f["id"]: f for f in sample["features_by_layer"][layer]}
            require(len(objects) == len(revised), "Changed object count")
            for old in objects:
                new = copy.deepcopy(revised[old["id"]])
                if old["id"] in ids:
                    require(
                        new["local_parts"][: len(old.get("local_parts", []))]
                        == old.get("local_parts", []),
                        "Old parts changed",
                    )
                    if "local_parts" in old:
                        new["local_parts"] = old["local_parts"]
                    else:
                        new.pop("local_parts")
                require(new == old, "Existing feature changed: " + old["id"])
        preserved = [
            "candidate_interfaces",
            "reviewed_local_connections",
            "review_decisions",
            "review_sources",
            "source_photos",
            "net_edges",
        ]
        for key in preserved:
            require(previous[key] == model[key], "Preservation failed: " + key)
        put(
            output / "preservation.json",
            dict(
                status="PASS",
                preserved_model_fields=preserved,
                target_count=len(ids),
                added_parts=len(rectangles),
                old_features_unchanged_except_appended_parts=True,
            ),
        )
        checkpoint("evidence")
        evidence(root, output, spec, traces["tracks"], original, sample, replay)
        checkpoint("review")
        build(root, output / "review-spec.json", output / "review")
        timings[stage] = time.perf_counter() - tick
        put(
            output / "timing.json",
            dict(
                status="PASS",
                stages_seconds=timings,
                total_seconds=time.perf_counter() - start,
                replay=replay,
                human_review_seconds=None,
                input_spec=ref(root, spec_path),
                entrypoint=ref(root, Path(__file__)),
            ),
        )
    except Exception as exc:
        put(
            output / "diagnostic.json",
            dict(
                status="REJECTED",
                stage=stage,
                reason=str(exc),
                stages_seconds=timings,
                total_seconds=time.perf_counter() - start,
            ),
        )
        raise
    return read(output / "timing.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--replay", action="store_true", help="Context-only review; no repeated decisions"
    )
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.root, args.spec, args.output, replay=args.replay), ensure_ascii=False, indent=2
        )
    )


if __name__ == "__main__":
    main()
