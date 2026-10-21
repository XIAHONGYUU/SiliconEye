"""Transfer reviewed CT reconstruction to explicitly observed material families.

Run: python -m silicon_eye.ct_transfer --spec SPEC --output NEW_DIR
Requires project environment. Frozen CT/material inputs remain untouched; all new
contacts need source support and the same whole-proposal geometry/landing gate.
"""

from __future__ import annotations

import argparse
import copy
import html
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon
from shapely.ops import unary_union

from .ct_joint_reconstruction import (
    check_source_boundaries,
    fit_family,
    promote_confirmed_slots,
    require_exportable,
)
from .geometry_reconstruction import digest, object_polygon
from .joint_layers import load_snapshot, reject_retired_ids, require_joint, write_snapshot
from .poly_closeout import svg
from .scene_geometry import load_locked


def fit_observed_row(prior, row, budget):
    """Fit occupied lattice sites only; preserve exclusions and gaps as evidence."""
    axis = row["axis"]
    left, top, right, bottom = row["source_roi"]
    chosen = {}
    excluded = []
    tracked = {}
    if row.get("track_local_spacing"):
        ordered = sorted(
            (
                o
                for o in prior["objects"]
                if left <= o["source_observation"]["source_native_center_xy"][0] <= right
                and top <= o["source_observation"]["source_native_center_xy"][1] <= bottom
            ),
            key=lambda o: o["source_observation"]["source_native_center_xy"][axis],
        )
        previous, slot = row["source_origin"], 0
        for old in ordered:
            value = old["source_observation"]["source_native_center_xy"][axis]
            step = int(np.rint((value - previous) / row["source_pitch"]))
            residual = abs(value - previous - step * row["source_pitch"])
            slot += step
            tracked[old["id"]] = (slot, residual)
            previous = value
    for old in prior["objects"]:
        obs = old["source_observation"]
        x, y = obs["source_native_center_xy"]
        if not (left <= x <= right and top <= y <= bottom):
            continue
        value = [x, y][axis]
        slot = int(np.rint((value - row["source_origin"]) / row["source_pitch"]))
        error = abs(value - (row["source_origin"] + slot * row["source_pitch"]))
        if tracked:
            slot, error = tracked[old["id"]]
        if error > row["source_fit_tolerance"]:
            excluded.append(
                dict(source_id=old["id"], reason="source_lattice_residual", residual=error)
            )
            continue
        score = (error, -obs["local_residual"])
        if slot in chosen:
            if score >= chosen[slot][0]:
                excluded.append(dict(source_id=old["id"], reason="alternate_peak_same_slot"))
                continue
            excluded.append(
                dict(source_id=chosen[slot][1]["id"], reason="alternate_peak_same_slot")
            )
        chosen[slot] = (score, old)
    if not chosen:
        raise ValueError("No source-supported observations for " + row["id"])
    objects = []
    for slot, (_, old) in sorted(chosen.items()):
        obs = copy.deepcopy(old["source_observation"])
        evidence = dict(
            obs,
            native_center=obs["source_native_center_xy"],
            source_observation_id=old["id"],
            evidence_tier=old["evidence_tier"],
            evidence_type="algorithm_peak_with_AI_local_material_correspondence",
            supported=obs["peak_gray"] >= row["min_gray"]
            and obs["local_residual"] >= row["min_residual"],
        )
        center = list(row["layout_origin"])
        center[axis] += slot * row["layout_pitch"]
        x, y = center
        half = budget["square_side"] / 2
        contact = dict(
            id=f"CTT-{row['id']}-S{slot:03}",
            family=row["id"],
            column=slot if axis == 0 else 0,
            row=0 if axis == 0 else slot,
            layer="CT",
            landing_material=row["material"],
            layout_center=center,
            layout_outline=[
                [x - half, y - half],
                [x + half, y - half],
                [x + half, y + half],
                [x - half, y + half],
            ],
            source_evidence=evidence,
            source_frame="poly",
            status="AI_transfer_candidate",
            M1_enclosure="unknown",
            net_id=None,
        )
        contact["AA_target" if row["material"] == "AA" else "POLY_target"] = row["target"]
        objects.append(contact)
    slots = sorted(chosen)
    return objects, dict(
        id=row["id"],
        occupied_slots=slots,
        unobserved_slots=[
            i
            for i in range(
                row.get("inspection_slot_range", [slots[0], slots[-1]])[0],
                row.get("inspection_slot_range", [slots[0], slots[-1]])[1] + 1,
            )
            if i not in chosen
        ],
        exclusions_not_deleted_evidence=excluded,
        correspondence="AI_local_row_and_material_hypothesis",
        completeness="observed_row_subset_not_full_material_coverage",
        source_assignment_mode=("local_observed_spacing" if tracked else "fixed_source_lattice"),
    )


def profile_observations(gray, row):
    """Measure actual band maxima; an empty lattice site never becomes evidence."""
    left, top, right, bottom = row["source_roi"]
    axis = row["axis"]
    if "source_path" in row:
        anchors = np.asarray(row["source_path"], dtype=np.float32)
        if np.any(np.diff(anchors[:, axis]) <= 0):
            raise ValueError("Profile path must increase along its axis")
        along = np.arange(int(anchors[0, axis]), int(anchors[-1, axis]) + 1, dtype=np.float32)
        cross = np.interp(along, anchors[:, axis], anchors[:, 1 - axis])
        offsets = np.arange(-row["band_half_width"], row["band_half_width"] + 1)
        grid_along = np.tile(along, (len(offsets), 1))
        grid_cross = (cross[None, :] + offsets[:, None]).astype(np.float32)
        xs, ys = (grid_along, grid_cross) if axis == 0 else (grid_cross, grid_along)
        if xs.min() < 0 or ys.min() < 0 or xs.max() >= gray.shape[1] or ys.max() >= gray.shape[0]:
            raise ValueError("Profile path leaves source image")
        band = cv2.remap(gray, xs, ys, cv2.INTER_LINEAR).astype(np.float32)
        profile = band.mean(axis=0)
    else:
        band = gray[top:bottom, left:right].astype(np.float32)
        profile = band.mean(axis=axis)
    smooth = cv2.GaussianBlur(profile.reshape(1, -1), (0, 0), row["sigma"])[0]
    observations = []
    for i in range(6, len(smooth) - 6):
        peak = float(smooth[i])
        contrast = peak - float(smooth[i - 6 : i + 7].min())
        if peak < row["min_gray"] or contrast < row["min_residual"]:
            continue
        if peak <= max(float(smooth[i - 4 : i].max()), float(smooth[i + 1 : i + 5].max())):
            continue
        if "source_path" in row:
            index = int(np.argmax(band[:, i]))
            xy = [float(xs[index, i]), float(ys[index, i])]
        else:
            cross_index = int(np.argmax(band[:, i] if axis == 0 else band[i, :]))
            xy = [left + i, top + cross_index] if axis == 0 else [left + cross_index, top + i]
        observations.append(
            dict(
                id=f"PROFILE-{row['id']}-{i}",
                evidence_tier="raw_band_profile_peak",
                source_observation=dict(
                    source_native_center_xy=xy, peak_gray=peak, local_residual=contrast
                ),
            )
        )
    return dict(objects=observations)


def check_scoped_revision(before, after, material_before, material_after, shifts, retired):
    """Only explicit geometry shifts and retirement of unapproved candidates may pass."""
    expected = []
    for old in before:
        if old["family"] in retired:
            continue
        obj = copy.deepcopy(old)
        if old["family"] in shifts:
            dx, dy = shifts[old["family"]]
            obj["layout_center"] = [obj["layout_center"][0] + dx, obj["layout_center"][1] + dy]
            obj["layout_outline"] = [[x + dx, y + dy] for x, y in obj["layout_outline"]]
        expected.append(obj)
    if after[: len(expected)] != expected:
        raise ValueError("Unauthorized contact or source-evidence revision")
    expected_material = copy.deepcopy(material_before)
    for obj in expected_material["objects"]:
        if obj["id"] == "POLY-RIGHT6-COMMON":
            from shapely.geometry import Polygon, box
            from shapely.ops import unary_union

            merged = unary_union(
                [Polygon(o["layout_outline"]) for o in obj["gate_fingers"]]
                + [box(1407, 1500, 1560, 1507)]
            )
            obj["layout_outline"] = [list(xy) for xy in list(merged.exterior.coords)[:-1]]
    if material_after != expected_material:
        raise ValueError("Unauthorized material revision")
    return len(expected) - sum(o["family"] in shifts for o in expected)


def run_revision(root, spec, output):
    """Apply a source-backed bounded review revision, retaining its parent snapshots."""
    root, output = Path(root).resolve(), Path(output)
    if output.exists():
        raise ValueError("Output must be new")
    parents = {key: load_locked(root, ref) for key, ref in spec["inputs"].items() if key != "photo"}
    photo_ref = spec["inputs"]["photo"]
    if digest(root / photo_ref["path"]) != photo_ref["sha256"]:
        raise ValueError("Source photo changed")
    photo = cv2.imread(str(root / photo_ref["path"]))
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    before, material_before = parents["contacts"]["objects"], parents["materials"]
    material = copy.deepcopy(material_before)
    common = next(o for o in material["objects"] if o["id"] == "POLY-RIGHT6-COMMON")
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union

    merged = unary_union(
        [Polygon(o["layout_outline"]) for o in common["gate_fingers"]] + [box(*spec["bus_bbox"])]
    )
    common["layout_outline"] = [list(xy) for xy in list(merged.exterior.coords)[:-1]]
    objects, retired, shifted = [], [], []
    for old in before:
        obj = copy.deepcopy(old)
        if obj["family"] in spec["retired_families"]:
            retired.append(obj)
            continue
        if obj["family"] in spec["contact_shifts"]:
            dx, dy = spec["contact_shifts"][obj["family"]]
            obj["layout_center"] = [obj["layout_center"][0] + dx, obj["layout_center"][1] + dy]
            obj["layout_outline"] = [[x + dx, y + dy] for x, y in obj["layout_outline"]]
            shifted.append(dict(before=old, after=obj))
        objects.append(obj)
    fits = []
    for row in spec["profile_rows"]:
        observations = profile_observations(gray, row)
        additions, fit = fit_observed_row(observations, row, spec["budget"])
        for obj in additions:
            obj["source_evidence"].update(
                evidence_type="raw_band_profile_peak_with_AI_material_correspondence",
                algorithm_detected=True,
                source_roi=row["source_roi"],
                sigma=row["sigma"],
            )
        fit["measured_observations"] = observations
        objects.extend(additions)
        fits.append(fit)
    unchanged = check_scoped_revision(
        before, objects, material_before, material, spec["contact_shifts"], spec["retired_families"]
    )
    report = require_exportable(objects, material, spec["budget"])
    for ref in spec["inputs"].values():
        if digest(root / ref["path"]) != ref["sha256"]:
            raise ValueError("Input changed during revision")
    report.update(
        complete_contact_records_unchanged=unchanged,
        geometry_only_contact_revisions=len(shifted),
        retired_unapproved_ring_candidates=len(retired),
        unrelated_materials_unchanged=True,
        human_review="pending_changed_geometry_only",
        implementation_sha256=digest(Path(__file__)),
    )
    output.mkdir(parents=True)
    protected_ids = {
        o["id"]
        for o in before
        if o["family"] not in list(spec["contact_shifts"]) + spec["retired_families"]
    }
    pil_photo = Image.fromarray(cv2.cvtColor(photo, cv2.COLOR_BGR2RGB))
    cards = "".join(
        render_case(c, material, objects, protected_ids, pil_photo, output) for c in spec["cases"]
    )
    (output / "index.html").write_text(
        """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>CT 局部修订 v2</title><style>body{max-width:1400px;margin:24px auto;background:#111c28;
color:#eee;font:17px sans-serif}section{border:1px solid #567;padding:16px;margin:20px 0}
img{width:100%}select{padding:10px}a{color:#65baff}</style><h1>只复核本轮改动</h1>
<p>W1宽MOS、E1电阻上端已获认可，灰蓝表示未改动CT。紫色为六管共栅孔的局部位置修订，蓝色为环补查候选。
栅指数量、共栅关系和原图观察不变；没有用设计规则生成无证据孔。</p>
<p>源图与规则图是独立坐标视图，可切换对照，不是像素级投影。环仅检查左上可见子段，
未声明全环覆盖。几何检查使用相对像素预算，不等于真实PDK DRC；M1及网络仍未知。</p>
<p><a href="ledger.json">修订前后台账</a> · <a href="report.json">质量门</a> ·
<a href="fits.json">原图峰值与拟合</a></p>"""
        + cards
        + "</html>"
    )
    ledger = dict(
        retired_candidates=retired,
        shifted_contacts=shifted,
        parent_common_material=next(
            o for o in material_before["objects"] if o["id"] == common["id"]
        ),
        rationale=spec["rationale"],
    )
    for name, value in dict(
        spec=spec,
        report=report,
        fits=fits,
        model=dict(objects=objects),
        material_model=material,
        ledger=ledger,
    ).items():
        (output / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return report


def review_unknown_sites(rows, fits, budget):
    """Explicit review slots are not contacts and never enter physical geometry checks."""
    by_id = {f["id"]: f for f in fits}
    sites = []
    for row in rows:
        for slot in by_id[row["id"]]["unobserved_slots"]:
            center = list(row["layout_origin"])
            center[row["axis"]] += slot * row["layout_pitch"]
            x, y = center
            half = budget["square_side"] / 2
            sites.append(
                dict(
                    id=f"UNKNOWN-{row['id']}-{slot}",
                    family=row["id"],
                    slot=slot,
                    status="inspection_slot_unknown_not_a_contact",
                    layout_outline=[
                        [x - half, y - half],
                        [x + half, y - half],
                        [x + half, y + half],
                        [x - half, y + half],
                    ],
                )
            )
    return sites


def render_case(case, materials, objects, protected_ids, photo, output, unknown_sites=()):
    key = case["id"]
    view = svg(materials, case["layout_bbox"])
    glyphs = []
    for obj in objects:
        color = (
            "#829ca6"
            if obj["id"] in protected_ids
            else "#ed8eff"
            if obj.get("landing_material") == "POLY"
            else "#65baff"
        )
        points = " ".join(f"{x},{y}" for x, y in obj["layout_outline"])
        glyphs.append(
            f'<polygon points="{points}" fill="{color}"><title>{obj["id"]}</title></polygon>'
        )
    for site in unknown_sites:
        points = " ".join(f"{x},{y}" for x, y in site["layout_outline"])
        glyphs.append(
            f'<polygon points="{points}" fill="none" stroke="#ffb45b" '
            f'stroke-width="0.7" stroke-dasharray="1 1"><title>'
            f"{site['id']}: unknown, not CT</title></polygon>"
        )
    (output / f"{key}-layout.svg").write_text(view.replace("</svg>", "".join(glyphs) + "</svg>"))
    left, top, right, bottom = case["source_bbox"]
    raw = photo.crop((left, top, right, bottom))
    raw.save(output / f"{key}-raw.png")
    marked = raw.copy()
    draw = ImageDraw.Draw(marked)
    for obj in objects:
        x, y = obj["source_evidence"]["native_center"]
        if not left <= x < right or not top <= y < bottom:
            continue
        color = (
            "#829ca6"
            if obj["id"] in protected_ids
            else "#ed8eff"
            if obj.get("landing_material") == "POLY"
            else "#65baff"
        )
        x -= left
        y -= top
        draw.line((x - 3, y, x + 3, y), fill=color, width=1)
        draw.line((x, y - 3, x, y + 3), fill=color, width=1)
    marked.save(output / f"{key}-source.png")
    return (
        f"<section><h2>{key} {html.escape(case['title'])}</h2>"
        f"<p>{html.escape(case['scope'])}</p>"
        f"<select onchange=\"document.getElementById('{key}').src=this.value\">"
        + "".join(
            f'<option value="{key}-{mode}.{ext}">{label}</option>'
            for mode, ext, label in [
                ("layout", "svg", "规则AA/POLY/CT联合图"),
                ("source", "png", "原图＋观察支持"),
                ("raw", "png", "纯原图"),
            ]
            + case.get("additional_modes", [])
        )
        + "</select><p>双击图像可在新页放大查看。</p>"
        + f'<img id="{key}" src="{key}-layout.svg" ondblclick="window.open(this.src)"></section>'
    )


def check_protected(objects, materials, accepted_objects, accepted_materials):
    """Reject any regression in an already reviewed contact or material record."""
    if objects[: len(accepted_objects)] != accepted_objects:
        raise ValueError("Protected reviewed contact records changed")
    if materials != accepted_materials:
        raise ValueError("Protected reviewed material records changed")


def translate_reviewed_geometry(objects, materials, translations, review):
    """Apply an explicitly reviewed canonical translation; retain all source evidence."""
    if translations != review.get("local_translations", []):
        raise ValueError("Canonical translations require matching human review scope")
    objects, materials = copy.deepcopy(objects), copy.deepcopy(materials)
    groups = {"CT": objects, "AA": materials["AA_objects"], "POLY": materials["objects"]}
    seen, ledger = set(), []
    for change in translations:
        layer, key = change["layer"], change["id"]
        if (layer, key) in seen or layer not in groups:
            raise ValueError("Duplicate or unsupported canonical translation")
        seen.add((layer, key))
        delta = np.asarray(change["delta_xy"], dtype=float)
        if delta.shape != (2,) or not np.isfinite(delta).all():
            raise ValueError("Invalid translation vector")
        matches = [o for o in groups[layer] if o["id"] == key]
        if len(matches) != 1:
            raise ValueError("Translation target must exist exactly once")
        target = matches[0]
        before = copy.deepcopy(target)
        fields = ("layout_outline",) if layer != "AA" else ("outer_xy",)
        if layer == "AA" and target.get("holes_xy"):
            raise ValueError("AA translation with holes needs an explicit geometry recipe")
        for field in fields:
            target[field] = (np.asarray(target[field]) + delta).tolist()
        if layer == "CT":
            target["layout_center"] = (np.asarray(target["layout_center"]) + delta).tolist()
        if layer == "AA":
            if target.get("hole_xyxy"):
                raise ValueError("AA translation with holes needs an explicit geometry recipe")
            target["outer_xyxy"] = (np.asarray(target["outer_xyxy"]) + np.tile(delta, 2)).tolist()
        ledger.append(
            dict(
                layer=layer,
                id=key,
                delta_xy=delta.tolist(),
                before=before,
                after=copy.deepcopy(target),
            )
        )
    return objects, materials, ledger


def run_confirmation(root, spec, output):
    """Promote only user-confirmed displayed slots without inventing optical peaks."""
    root, output = Path(root).resolve(), Path(output)
    if output.exists():
        raise ValueError("Output must be new")
    loaded = {
        key: load_locked(root, spec["inputs"][key])
        for key in ("materials", "contacts", "unknown_sites", "parent_spec", "human_review")
    }
    source_spec = loaded["parent_spec"]
    if spec["budget"] != source_spec["budget"]:
        raise ValueError("Confirmation cannot relax the parent geometry budget")
    photo_ref = spec["inputs"]["photo"]
    if digest(root / photo_ref["path"]) != photo_ref["sha256"]:
        raise ValueError("Source photo changed")
    rows = {r["id"]: r for r in source_spec["profile_rows"] + source_spec.get("rows", [])}
    pending = []
    for item in loaded["unknown_sites"]["sites"]:
        row = rows[item["family"]]
        points = np.asarray(item["layout_outline"])
        native_axis = row["source_origin"] + item["slot"] * row["source_pitch"]
        path = np.asarray(row["source_path"])
        native_cross = float(np.interp(native_axis, path[:, row["axis"]], path[:, 1 - row["axis"]]))
        native = [native_axis, native_cross] if row["axis"] == 0 else [native_cross, native_axis]
        pending.append(
            dict(
                item,
                axis=row["axis"],
                layout_center=points.mean(axis=0).tolist(),
                estimated_native_center=native,
            )
        )
    parent = dict(objects=loaded["contacts"]["objects"], unresolved_slots=pending)
    objects = promote_confirmed_slots(
        parent["objects"],
        parent,
        loaded["human_review"],
        spec["inputs"]["human_review"],
        spec["budget"],
    )
    check_protected(objects, loaded["materials"], parent["objects"], loaded["materials"])
    objects, material, revisions = translate_reviewed_geometry(
        objects, loaded["materials"], spec.get("local_translations", []), loaded["human_review"]
    )
    report = require_exportable(objects, material, spec["budget"])
    resolved = {(r["family"], r["slot"]) for r in loaded["human_review"]["confirmed_slots"]}
    remaining = [o for o in pending if (o["family"], o["slot"]) not in resolved]
    report.update(
        protected_contact_count=len(parent["objects"]) - sum(r["layer"] == "CT" for r in revisions),
        canonical_translations=[
            dict(layer=r["layer"], id=r["id"], delta_xy=r["delta_xy"]) for r in revisions
        ],
        source_evidence_unchanged_for_translations=True,
        human_confirmed_additions=len(objects) - len(parent["objects"]),
        remaining_unknown_slots=len(remaining),
        unknown_slot_scope="previously displayed orange inspection slots only",
        gate_terminal_CT_status=spec.get(
            "gate_terminal_CT_status", "not resolved by this confirmation"
        ),
        material_model_unchanged=not any(r["layer"] != "CT" for r in revisions),
        evidence_type="human_confirmation_not_algorithm_detection",
        implementation_sha256=digest(Path(__file__)),
        shared_geometry_implementation_sha256=digest(
            Path(__file__).with_name("ct_joint_reconstruction.py")
        ),
    )
    for ref in spec["inputs"].values():
        if digest(root / ref["path"]) != ref["sha256"]:
            raise ValueError("Input changed during confirmation")
    output.mkdir(parents=True)
    photo = Image.open(root / photo_ref["path"]).convert("RGB")
    for image_ref in spec.get("review_images", []):
        source_ref = spec["inputs"][image_ref["input_key"]]
        (output / image_ref["output_name"]).write_bytes((root / source_ref["path"]).read_bytes())
    protected = {o["id"] for o in parent["objects"]}
    cards = "".join(
        render_case(c, material, objects, protected, photo, output, remaining)
        for c in spec["cases"]
    )
    default_header = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>中部MOS补充确认</title><style>body{max-width:1400px;margin:24px auto;background:#111c28;
color:#eee;font:17px sans-serif}section{border:1px solid #567;padding:16px;margin:20px 0}
img{width:100%;max-height:85vh;object-fit:contain}select{padding:10px}a{color:#65baff}</style>
<h1>中部MOS：48处原橙框已按人工确认纳入CT</h1>
<p>蓝色为本轮48个新增人工确认CT，灰蓝为原1777个保留CT。AA/POLY及原CT不改。
补充确认只覆盖上一版显示的橙框；原图定位来自原检查格点估计，不冒充精确像素确认或算法亮峰。</p>
<p>栅极主体已经表达；栅端CT仍待专项检查。上一轮51条取样路径全部是AA，
流程未覆盖不能表述为照片无法辨认。栅端候选边界与真实孔需继续分别核查。</p>
<p><a href="gate-assessment.md">栅极／栅端CT诊断</a> · <a href="report.json">质量门</a> ·
<a href="human-review.json">补充裁决</a></p>"""
    header = default_header
    if "review_title" in spec:
        header = (
            '<!doctype html><html lang="zh"><meta charset="utf-8"><title>'
            + html.escape(spec["review_title"])
            + "</title><style>body{max-width:1400px;margin:24px auto;background:#111c28;"
            + "color:#eee;font:17px sans-serif}section{border:1px solid #567;padding:16px;"
            + "margin:20px 0}img{width:100%;max-height:85vh;object-fit:contain}"
            + "select{padding:10px}a{color:#65baff}</style><h1>"
            + html.escape(spec["review_title"])
            + "</h1><p>"
            + html.escape(spec["review_notes"])
            + '</p><p><a href="report.json">质量门</a> · '
            + '<a href="human-review.json">人审范围</a> · '
            + '<a href="ledger.json">逐对象修订台账</a></p>'
        )
    (output / "index.html").write_text(header + cards + "</html>")
    for name, value in dict(
        spec=spec,
        report=report,
        model=dict(objects=objects),
        material_model=material,
        ledger=dict(
            canonical_translations=revisions,
            previous_unknown_slots=pending,
            confirmed_slots=loaded["human_review"]["confirmed_slots"],
        ),
        human_review=loaded["human_review"],
        unknown_sites=dict(sites=remaining),
    ).items():
        (output / f"{name.replace('_', '-')}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        )
    return report


def apply_reviewed_record_changes(records, changes, authorized_ids, preserve_fields=()):
    """Apply named before/after records, rejecting stale parents and collateral changes."""
    result = copy.deepcopy(records)
    seen = set()
    for change in changes:
        key, before, after = change["id"], change["before"], change["after"]
        if key not in authorized_ids or key in seen:
            raise ValueError("Record change outside human review scope or duplicate target")
        seen.add(key)
        matches = [i for i, record in enumerate(result) if record["id"] == key]
        if before is None:
            if matches or after is None or after["id"] != key:
                raise ValueError("Invalid record addition")
            result.append(copy.deepcopy(after))
            continue
        if len(matches) != 1 or result[matches[0]] != before:
            raise ValueError("Stale or missing revision parent record")
        if after is None:
            result.pop(matches[0])
            continue
        if after["id"] != key or any(before.get(f) != after.get(f) for f in preserve_fields):
            raise ValueError("Revision would alter preserved identity or source evidence")
        result[matches[0]] = copy.deepcopy(after)
    return result


def apply_source_correspondence_corrections(records, corrections, authorized_ids, review_ref):
    """Correct named photo observations while retaining prior evidence and all design fields."""
    result = copy.deepcopy(records)
    by_id = {o["id"]: o for o in result}
    if len(by_id) != len(result):
        raise ValueError("Duplicate source correction parent ID")
    seen = set()
    for change in corrections:
        key = change["id"]
        if key not in authorized_ids or key in seen or key not in by_id:
            raise ValueError("Source correction outside review scope or duplicate target")
        seen.add(key)
        obj = by_id[key]
        if obj["source_evidence"] != change["before_source_evidence"]:
            raise ValueError("Stale source correspondence parent")
        after = change["after_source_evidence"]
        center = np.asarray(after.get("native_center", []), dtype=float)
        if (
            center.shape != (2,)
            or not np.isfinite(center).all()
            or (
                "source_native_center_xy" in after
                and after["source_native_center_xy"] != after.get("native_center")
            )
            or after.get("supported") is not True
            or not change.get("reason")
        ):
            raise ValueError("Source correction needs finite observed support and a reason")
        obj.setdefault("source_correspondence_history", []).append(
            dict(
                before=copy.deepcopy(obj["source_evidence"]),
                after=copy.deepcopy(after),
                reason=change["reason"],
                review_ref=copy.deepcopy(review_ref),
            )
        )
        obj["source_evidence"] = copy.deepcopy(after)
    return result


def audit_terminal_access(objects, materials, minimum_region_area=25):
    """Inventory observed access, without requiring cuts on internal diffusion nodes."""
    polys = {g["id"]: Polygon(g["layout_outline"]) for g in materials["objects"]}
    by_poly, by_active, associated = {}, {}, {}
    for obj in objects:
        target = obj.get("POLY_target")
        if target:
            by_poly.setdefault(target, []).append(obj["id"])
        target = obj.get("AA_target")
        if target:
            by_active.setdefault(target, []).append(obj)
    inherited_access = {key: set(values) for key, values in by_poly.items()}
    # Explicit common terminals are usable only where the reconstructed bridge connects.
    for g in materials["objects"]:
        for member in g.get("member_POLY_ids", []):
            if member in polys and polys[g["id"]].intersection(polys[member]).area > 1e-8:
                inherited_access.setdefault(member, set()).update(by_poly.get(g["id"], []))
        if g.get("AA_target"):
            associated.setdefault(g["AA_target"], []).append(g["id"])
    regions = []
    for aa in materials["AA_objects"]:
        gates = associated.get(aa["id"], [])
        if not gates:
            continue
        remaining = object_polygon(aa).difference(unary_union([polys[g] for g in gates]))
        parts = list(remaining.geoms) if hasattr(remaining, "geoms") else [remaining]
        parts = sorted(
            (p for p in parts if p.geom_type == "Polygon" and p.area >= minimum_region_area),
            key=lambda p: (p.centroid.x, p.centroid.y),
        )
        for index, part in enumerate(parts):
            contacts = [
                o["id"]
                for o in by_active.get(aa["id"], [])
                if part.covers(Polygon(o["layout_outline"]))
            ]
            regions.append(
                dict(
                    id=f"{aa['id']}:D{index}",
                    AA_target=aa["id"],
                    gate_ids=gates,
                    layout_bounds=list(part.bounds),
                    contact_ids=contacts,
                    status="candidate_direct_CT_access" if contacts else "no_direct_CT_evidence",
                    no_CT_is_not_a_missing_cut_or_failed_internal_node=not contacts,
                )
            )
    gates = [
        dict(
            material_id=g["id"],
            AA_target=g.get("AA_target"),
            contact_ids=sorted(inherited_access.get(g["id"], [])),
            status="candidate_direct_or_shared_CT_access"
            if inherited_access.get(g["id"])
            else "no_direct_CT_evidence_or_body_fragment",
        )
        for g in materials["objects"]
    ]
    return dict(
        status="access_inventory_not_physical_completion_gate",
        diffusion_regions=regions,
        POLY_materials=gates,
        diffusion_region_count=len(regions),
        diffusion_regions_without_direct_CT=sum(not x["contact_ids"] for x in regions),
        POLY_materials_without_direct_CT=sum(not x["contact_ids"] for x in gates),
        all_access_is_candidate_not_confirmed_M1_connectivity=True,
        no_synthetic_CT_for_internal_diffusion=True,
    )


def run_local_review_revision(root, spec, output):
    """Execute a bounded human-directed revision without rerunning approved extraction."""
    root, output = Path(root).resolve(), Path(output)
    if output.exists():
        raise ValueError("Output must be new")
    refs = spec["inputs"]
    for ref in refs.values():
        if digest(root / ref["path"]) != ref["sha256"]:
            raise ValueError("Local revision input changed")
    loaded = {
        k: load_locked(root, refs[k])
        for k in (
            "materials",
            "contacts",
            "human_review",
            "new_contacts",
            "unknown_sites",
            "parent_spec",
        )
    }
    snapshot = None
    if spec.get('joint_snapshot'):
        snapshot_ref = spec['joint_snapshot']
        load_locked(root, snapshot_ref)
        snapshot = load_snapshot(root, root / snapshot_ref['path'])
        if (
            loaded['materials'] != snapshot['materials']
            or loaded['contacts']['objects'] != snapshot['contacts']
            or loaded['unknown_sites'] != snapshot['values']['unknown']
        ):
            raise ValueError('Revision inputs do not match the current joint snapshot')
    if spec["budget"] != loaded["parent_spec"]["budget"]:
        raise ValueError("Local revision cannot relax the parent geometry budget")
    review = loaded["human_review"]
    material = copy.deepcopy(loaded["materials"])
    ledger = {}
    for collection in ("objects", "AA_objects"):
        changes = spec["material_changes"].get(collection, [])
        material[collection] = apply_reviewed_record_changes(
            material[collection],
            changes,
            review["authorized_material_ids"],
            ("native_outline", "native_corners", "layout_observation_bbox_xywh"),
        )
        ledger[collection] = changes
    material["local_material_revision"] = dict(
        parent_ref=refs["materials"],
        human_review_ref=refs["human_review"],
        alias_map={
            alias: obj["id"]
            for collection in ("objects", "AA_objects")
            for obj in material[collection]
            for alias in obj.get("material_aliases", [])
        },
        exact_new_geometry_status="candidate_except_explicitly_approved_patch",
    )
    changes = spec["contact_changes"]
    objects = apply_reviewed_record_changes(
        loaded["contacts"]["objects"],
        changes,
        review["authorized_contact_ids"],
        ("source_evidence", "source_frame"),
    )
    source_corrections = spec.get("source_correspondence_corrections", [])
    if {c["id"] for c in source_corrections} & {c["id"] for c in changes}:
        raise ValueError("Source correction must not also revise or retire the design record")
    objects = apply_source_correspondence_corrections(
        objects,
        source_corrections,
        review.get("authorized_source_correspondence_ids", []),
        refs["human_review"],
    )
    additions = loaded["new_contacts"]["objects"]
    if {o["id"] for o in additions} != set(review["authorized_new_contact_ids"]):
        raise ValueError("New contacts exceed the reviewed task scope")
    existing = {o["id"] for o in objects}
    if len({o["id"] for o in additions}) != len(additions) or existing & {
        o["id"] for o in additions
    }:
        raise ValueError("Duplicate contact addition")
    objects.extend(copy.deepcopy(additions))
    if snapshot is not None:
        reject_retired_ids(snapshot['manifest'], material)
    joint_report = require_joint(objects, material, spec['budget'], loaded['contacts']['objects'])
    report = copy.deepcopy(joint_report['CT'])
    report['joint_layers'] = joint_report
    report['CT_geometry_status'] = report['status']
    report['status'] = joint_report['status']
    report['automatic_network_export_allowed'] = False
    access = audit_terminal_access(objects, material) if spec.get("audit_terminal_access") else None
    parent_by_id = {o["id"]: o for o in loaded["contacts"]["objects"]}
    report.update(
        unchanged_parent_contacts=sum(o == parent_by_id.get(o["id"]) for o in objects),
        revised_contact_count=len(changes),
        new_contact_count=len(additions),
        source_correspondence_revision_ids=[c["id"] for c in source_corrections],
        material_revision_ids=[c["id"] for cs in spec["material_changes"].values() for c in cs],
        human_review="scoped decisions retained; revised geometry and new CT pending review",
        implementation_sha256=digest(Path(__file__)),
    )
    for ref in refs.values():
        if digest(root / ref["path"]) != ref["sha256"]:
            raise ValueError("Input changed during local revision")
    output.mkdir(parents=True)
    for image_ref in spec.get("review_images", []):
        source_ref = refs[image_ref["input_key"]]
        (output / image_ref["output_name"]).write_bytes((root / source_ref["path"]).read_bytes())
    photo = Image.open(root / refs["photo"]["path"]).convert("RGB")
    sites = loaded["unknown_sites"]["sites"]
    changed = {c["id"] for c in changes}
    protected = set(parent_by_id) - changed
    cards = "".join(
        render_case(c, material, objects, protected, photo, output, sites) for c in spec["cases"]
    )
    (output / "index.html").write_text(
        '<!doctype html><html lang="zh"><meta charset="utf-8"><style>'
        "body{max-width:1400px;margin:24px auto;background:#111c28;color:#eee;font:17px sans-serif}"
        "section{border:1px solid #567;padding:16px;margin:20px 0}"
        "img{width:100%;max-height:85vh;object-fit:contain}a{color:#65baff}select{padding:10px}"
        "</style><title>"
        + html.escape(spec["review_title"])
        + "</title><h1>"
        + html.escape(spec["review_title"])
        + "</h1><p>"
        + html.escape(spec["review_notes"])
        + '</p><p><a href="report.json">联合质量门</a> · '
        '<a href="human-review.json">逐项裁决</a> · <a href="ledger.json">变更台账</a></p>'
        + cards
        + "</html>"
    )
    for name, value in dict(
        spec=spec,
        report=report,
        model=dict(objects=objects),
        material_model=material,
        ledger=dict(
            material_changes=ledger,
            contact_changes=changes,
            source_correspondence_corrections=source_corrections,
            added_contact_ids=[o["id"] for o in additions],
        ),
        human_review=review,
        unknown_sites=loaded["unknown_sites"],
    ).items():
        (output / f"{name.replace('_', '-')}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n"
        )
    if access is not None:
        (output / "terminal-access.json").write_text(
            json.dumps(access, ensure_ascii=False, indent=2) + "\n"
        )
    if snapshot is not None:
        continued = copy.deepcopy(snapshot)
        continued.update(materials=material, contacts=objects)
        write_snapshot(root, continued, output)
        # Approval/limitations remain locked context, not a new blanket release.
        (output / 'continuation-context.json').write_text(
            json.dumps(dict(
                parent_snapshot=spec['joint_snapshot'],
                stage=snapshot['values']['stage'],
                use_contract=snapshot['values']['use_contract'],
                source_reinspection=snapshot['values']['source_reinspection'],
                joint_report=joint_report,
                changed_geometry_requires_scoped_review=True,
            ), ensure_ascii=False, indent=2) + '\n'
        )
    return report


def run(root, spec_path, output):
    root = Path(root).resolve()
    output = Path(output)
    if output.exists():
        raise ValueError("Output must be new")
    spec = json.loads(Path(spec_path).read_text())
    if spec.get("operation") == "apply_local_review_revision":
        return run_local_review_revision(root, spec, output)
    if spec.get("operation") == "confirm_review_slots":
        return run_confirmation(root, spec, output)
    if spec.get("operation") == "review_revision":
        return run_revision(root, spec, output)
    material = load_locked(root, spec["inputs"]["materials"])
    protected = load_locked(root, spec["inputs"]["protected_contacts"])
    accepted = load_locked(root, spec["inputs"]["acceptance"])
    prior = load_locked(root, spec["inputs"]["observations"])
    for name, key in [
        ("materials", "material-model-v1.json"),
        ("protected_contacts", "model-v1.json"),
    ]:
        if spec["inputs"][name]["sha256"] != accepted["locked_files"][key]:
            raise ValueError("Baseline acceptance mismatch")
    photo_ref = spec["inputs"]["photo"]
    if digest(root / photo_ref["path"]) != photo_ref["sha256"]:
        raise ValueError("Source photo changed")
    photo = cv2.imread(str(root / photo_ref["path"]))
    original_contacts = copy.deepcopy(protected["objects"])
    parent_snapshot_count = len(original_contacts)
    reviewed_count = (
        parent_snapshot_count if accepted.get("whole_snapshot_human_accepted", True) else None
    )
    if "retained_contacts" in spec["inputs"]:
        retained = load_locked(root, spec["inputs"]["retained_contacts"])["objects"]
        check_protected(retained, material, original_contacts, material)
        original_contacts = copy.deepcopy(retained)
    original_material = copy.deepcopy(material)
    objects = copy.deepcopy(original_contacts)
    fits = []
    for family in spec["families"]:
        additions, fit = fit_family(photo, material, family, spec["budget"])
        check_source_boundaries(additions, family)
        objects.extend(additions)
        fits.append(fit)
    for row in spec["rows"]:
        additions, fit = fit_observed_row(prior, row, spec["budget"])
        objects.extend(additions)
        fits.append(fit)
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    for row in spec.get("profile_rows", []):
        observations = profile_observations(gray, row)
        additions, fit = fit_observed_row(observations, row, spec["budget"])
        for obj in additions:
            obj["source_evidence"].update(
                evidence_type="raw_path_profile_peak_with_AI_material_correspondence",
                algorithm_detected=True,
                source_path=row.get("source_path"),
                source_roi=row["source_roi"],
                sigma=row["sigma"],
            )
        fit["measured_observations"] = observations
        objects.extend(additions)
        fits.append(fit)
    report = require_exportable(objects, material, spec["budget"])
    check_protected(objects, material, original_contacts, original_material)
    for ref in spec["inputs"].values():
        if digest(root / ref["path"]) != ref["sha256"]:
            raise ValueError("Input changed during transfer")
    report.update(
        protected_contact_count=len(original_contacts),
        previously_accepted_contact_count=reviewed_count,
        retained_working_geometry_count=len(original_contacts) - parent_snapshot_count,
        inherited_acceptance_is_whole_snapshot=accepted.get("whole_snapshot_human_accepted", True),
        explicit_parent_scope_contact_count=len(accepted.get("accepted_contact_ids", [])),
        new_contact_count=len(objects) - len(original_contacts),
        protected_materials_unchanged=True,
        scope=spec.get("scope", "three_local_transfer_cases_not_fullframe"),
        human_review="pending_new_cases_only",
        photo_correspondence="AI_local_candidates",
        implementation_sha256=digest(Path(__file__)),
        shared_geometry_implementation_sha256=digest(
            Path(__file__).with_name("ct_joint_reconstruction.py")
        ),
    )
    output.mkdir(parents=True)
    pil_photo = Image.fromarray(cv2.cvtColor(photo, cv2.COLOR_BGR2RGB))
    for image_ref in spec.get("review_images", []):
        source_ref = spec["inputs"][image_ref["input_key"]]
        (output / image_ref["output_name"]).write_bytes((root / source_ref["path"]).read_bytes())
    protected_ids = {o["id"] for o in original_contacts}
    unknown_sites = review_unknown_sites(
        spec.get("rows", []) + spec.get("profile_rows", []), fits, spec["budget"]
    )
    cards = "".join(
        render_case(case, material, objects, protected_ids, pil_photo, output, unknown_sites)
        for case in spec["cases"]
    )
    (output / "index.html").write_text(
        """<!doctype html><html lang="zh"><meta charset="utf-8"><title>CT局部联合复核</title>
<style>body{max-width:1400px;margin:24px auto;background:#111c28;color:#eee;font:16px sans-serif}
section{border:1px solid #567;padding:16px;margin:20px 0}
img{width:100%;max-height:85vh;object-fit:contain}select{padding:8px}
a{color:#65baff}</style>
<h1>CT材料联合重建复核</h1><p>蓝色：新增AA接触；紫色：新增POLY接触；灰蓝：既有CT工作快照，保留原分项批准和未知状态，不重复验收。
新孔均有照片观察支持，采用局部材料对应，未使用全幅盲投影。AA/POLY材料未修改。
橙色虚框仅为待查槽位，不计为CT，也不代表实际缺孔。</p>
<p>仅重建下列局部观察支持的孔列；未补齐缺少证据的位置，未画不代表没有孔。
新区域的材料对应仍为AI候选，孔数不是人工确认值。几何检查不是真实工艺DRC，M1归属未知。
<a href="report.json">整体质量门与防退化检查</a> ·
<a href="fits.json">匹配与未选择观察记录</a></p>"""
        + "<h2>"
        + html.escape(spec.get("review_title", ""))
        + "</h2>"
        + "<p>"
        + html.escape(spec.get("review_notes", ""))
        + "</p>"
        + "<details><summary>逐孔列数量与待查槽位（0起编号）</summary><ul>"
        + "".join(
            "<li>"
            + html.escape(f["id"])
            + ": "
            + str(len(f["occupied_slots"]))
            + " 孔；待查槽位 "
            + html.escape(str(f["unobserved_slots"]))
            + "</li>"
            for f in fits
            if "occupied_slots" in f
        )
        + "</ul></details>"
        + cards
        + "</html>"
    )
    for name, value in [
        ("spec", spec),
        ("report", report),
        ("fits", fits),
        ("model", dict(objects=objects, protected_contact_ids=sorted(protected_ids))),
        ("unknown-sites", dict(sites=unknown_sites, interpretation="not_contacts")),
    ]:
        (output / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.spec, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
