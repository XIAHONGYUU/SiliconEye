"""Refine local positive material examples on raw images, with CT occlusion unknown.

Run: silicon-eye annotate guided --spec <json> --output <new-dir>.
OpenCV GrabCut is a bounded refinement, not a learned/validated device extractor.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from .registration_audit import digest, write_image, write_json


def read_paint(marked: np.ndarray, original: np.ndarray) -> dict:
    if marked.shape != original.shape or marked.dtype != np.uint8:
        raise ValueError("annotation sheet size/type changed")
    hsv = cv2.cvtColor(marked, cv2.COLOR_BGR2HSV)
    changed = np.max(cv2.absdiff(marked, original), axis=2) > 20
    red = changed & (hsv[:, :, 1] > 140) & ((hsv[:, :, 0] < 12) | (hsv[:, :, 0] > 168))
    blue = changed & (hsv[:, :, 1] > 140) & (hsv[:, :, 0] > 80) & (hsv[:, :, 0] < 135)
    if np.any(changed & ~red & ~blue):
        raise ValueError("unexplained sheet edits; cannot assume original coordinate mapping")
    return {"aa": red.astype(np.uint8) * 255, "poly": blue.astype(np.uint8) * 255}


def ct_support(image: np.ndarray, *, profile: str = "legacy") -> np.ndarray:
    """Bright compact residuals only; CT shape remains an inferred localization."""
    if profile not in {"legacy", "narrow_vertical"}:
        raise ValueError(f"unsupported CT profile: {profile}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray, (5, 5), 1)
    residual = smooth.astype(float) - cv2.GaussianBlur(smooth, (0, 0), 4).astype(float)
    peaks = ((smooth > 190) & (residual > 18)).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(peaks)
    result = np.zeros_like(peaks)
    for index in range(1, count):
        _, _, w, h, area = stats[index]
        shape_ok = (
            min(w, h) >= 5 and 0.5 < w / h < 2
            if profile == "legacy"
            else w >= 3 and h >= 5 and 0.25 <= w / h < 2
        )
        if 20 <= area <= 450 and max(w, h) <= 40 and shape_ok:
            result[labels == index] = 1
    return cv2.dilate(result, np.ones((3, 3), np.uint8)).astype(bool)


def preserve_prompt_separation(selected: np.ndarray, prompt: np.ndarray) -> tuple:
    """Remove unproven growth if it merges separately painted regions.

    Separate prompt pieces do not prove physical isolation. This conservative
    policy merely refuses to create a new connection without evidence.
    """
    _, seeds = cv2.connectedComponents((prompt > 0).astype(np.uint8), connectivity=8)
    count, candidate = cv2.connectedComponents(selected.astype(np.uint8), connectivity=8)
    corrected = selected.copy()
    unknown = np.zeros_like(selected)
    conflicts = []
    for index in range(1, count):
        region = candidate == index
        identities = np.unique(seeds[region])
        identities = identities[identities > 0]
        if len(identities) > 1:
            unsupported = region & (prompt == 0)
            corrected[unsupported] = False
            unknown[unsupported] = True
            conflicts.append(
                {
                    "merged_prompt_components": identities.tolist(),
                    "removed_unproven_pixels": int(unsupported.sum()),
                }
            )
    return corrected, unknown, conflicts


def guided_mask(
    raw: np.ndarray,
    prompt: np.ndarray,
    material: str,
    radius: int = 8,
    iterations: int = 5,
    aa_max_expansion: int = 2,
) -> dict:
    if (
        material not in {"aa", "poly"}
        or raw.dtype != np.uint8
        or raw.ndim != 3
        or raw.shape[2] != 3
    ):
        raise ValueError("invalid raw image/material")
    if prompt.shape != raw.shape[:2] or not np.any(prompt):
        raise ValueError("missing or incompatible positive examples")
    if (
        not isinstance(radius, int)
        or not isinstance(iterations, int)
        or not 1 <= radius <= 20
        or not 1 <= iterations <= 10
    ):
        raise ValueError("invalid refinement parameters")
    if not isinstance(aa_max_expansion, int) or not 0 <= aa_max_expansion <= 2:
        raise ValueError("AA expansion must be conservative, within 0..2 pixels")
    if material == "aa":
        radius = min(radius, aa_max_expansion)
    domain = cv2.dilate((prompt > 0).astype(np.uint8), np.ones((2 * radius + 1,) * 2, np.uint8)) > 0
    ct = ct_support(raw) & domain if material == "poly" else np.zeros_like(domain)
    sure = (cv2.erode((prompt > 0).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~ct
    if np.count_nonzero(sure) < 5 or np.all(domain):
        raise ValueError("insufficient material seed or exterior context")
    labels = np.full(prompt.shape, cv2.GC_BGD, np.uint8)
    labels[domain] = cv2.GC_PR_BGD
    labels[prompt > 0] = cv2.GC_PR_FGD
    labels[sure] = cv2.GC_FGD
    # CT is excluded from visible material classification only. The hidden lower
    # material remains unknown; no claim is made that poly cannot exist below CT.
    labels[ct] = cv2.GC_BGD
    cv2.setRNGSeed(0)
    cv2.grabCut(
        raw, labels, None, np.zeros((1, 65)), np.zeros((1, 65)), iterations, cv2.GC_INIT_WITH_MASK
    )
    selected = np.isin(labels, [cv2.GC_FGD, cv2.GC_PR_FGD]) & domain & ~ct
    topology_unknown = np.zeros_like(selected)
    if material == "aa":
        selected, topology_unknown, _ = preserve_prompt_separation(selected, prompt)
    return {
        "visible": selected,
        "topology_unknown": topology_unknown,
        "ct_unknown": ct,
        "search_domain": domain,
        "outside_search_unknown": ~domain,
    }


def run_guided(spec_path: str, output: str) -> dict:
    spec_file = Path(spec_path).resolve()
    spec = json.loads(spec_file.read_text())
    if spec["schema_version"] != 1:
        raise ValueError("unsupported guided schema")
    paths = {
        key: Path(spec[key]).resolve()
        for key in ("marked_sheet", "original_sheet", "sample_manifest", "registration_manifest")
    }
    for key, path in paths.items():
        if digest(path) != spec[key + "_sha256"]:
            raise ValueError(f"{key}: hash mismatch")
    meta = json.loads(paths["sample_manifest"].read_text())
    if meta["sheet_sha256"] != digest(paths["original_sheet"]):
        raise ValueError("sample manifest does not bind original sheet")
    original = cv2.imread(str(paths["original_sheet"]))
    marked = cv2.imread(str(paths["marked_sheet"]))
    if original is None or marked is None:
        raise ValueError("unreadable sheets")
    paint = read_paint(marked, original)
    destination = Path(output).resolve()
    if destination.exists():
        raise ValueError("output must be a new directory")
    registration = json.loads(paths["registration_manifest"].read_text())
    sources, inputs = {}, {}
    for name in ("aa", "poly"):
        panel = meta["panels"][name]
        source = Path(panel["source_path"]).resolve()
        if source.is_relative_to(destination) or destination.is_relative_to(source.parent):
            raise ValueError("output cannot contain or reside beside source images")
        if digest(source) != panel["source_sha256"] or panel["scale"] != 1 or panel["resampling"]:
            raise ValueError("changed source or unsupported sample mapping")
        side = "reference" if name == "aa" else "target"
        if panel["source_sha256"] != registration["source_sha256"][side]:
            raise ValueError("sample source differs from frozen registration source")
        image = cv2.imread(str(source))
        x, y, w, h = panel["source_crop_xywh"]
        sx, sy, sw, sh = panel["sheet_panel_xywh"]
        crop = image[y : y + h, x : x + w].copy()
        if (sw, sh) != (w, h) or not np.array_equal(original[sy : sy + h, sx : sx + w], crop):
            raise ValueError("sample panel is not the unchanged native source crop")
        prompt = paint[name][sy : sy + h, sx : sx + w]
        inputs[name] = (crop, prompt, panel)
        sources[name] = source
    cv2.setNumThreads(2)
    destination.mkdir(parents=True)
    write_json(destination / "manifest.json", {"status": "running"})
    write_json(destination / "spec.json", spec)
    report = {
        "status": "complete",
        "material_status": "candidate",
        "unit": "px",
        "objects": {},
        "method": "human_positive_prompts_plus_bounded_GrabCut_on_raw_sources",
        "accuracy_evaluated": False,
        "environment": {"opencv": cv2.__version__, "numpy": np.__version__},
        "device_ground_truth_ready": False,
        "outside_prompt_search": "unknown_not_material_negative",
        "aa_policy": "max2px_growth_and_no_unproven_merging_of_prompt_components",
        "ct_rule": "visible CT support excluded; underlying AA/poly unknown",
        "spec_sha256": digest(spec_file),
        "input_sha256": {k: digest(p) for k, p in paths.items()},
        "source_sha256": {n: digest(p) for n, p in sources.items()},
    }
    lines = [
        "# 用户示例引导的 AA / poly 重提取",
        "",
        "仅为当前局部的提示引导候选，不是未标注区域的自动识别验收。",
        "AA 只覆盖已示范区域，最多扩展2px且不得无依据合并提示组件。"
        "poly 仍依赖蓝色位置提示。原始照片用于计算，涂色只用于提示。",
        "CT 黄色支持是推测的位置，可能混入亮边；其下材料未知，既不当成poly，也不宣称不存在poly。",
        "未标注区域和搜索带外区域是未知；没有把部分AA标注当成完整负样本。",
        "",
        "",
    ]
    generated = {}
    for name, (crop, prompt, panel) in inputs.items():
        result = guided_mask(
            crop,
            prompt,
            name,
            spec["search_radius_px"],
            spec["iterations"],
            aa_max_expansion=spec.get("aa_max_expansion_px", 2),
        )
        generated[name] = result
        folder = destination / name
        folder.mkdir()
        color = np.array([0, 0, 255] if name == "aa" else [255, 160, 0])
        overlay = crop.copy()
        mask = result["visible"]
        overlay[mask] = (0.6 * overlay[mask] + 0.4 * color).astype(np.uint8)
        ct = result["ct_unknown"]
        with_ct = overlay.copy()
        with_ct[ct] = (0.4 * with_ct[ct] + 0.6 * np.array([0, 255, 255])).astype(np.uint8)
        write_image(folder / "raw.png", crop)
        write_image(folder / "human-positive.png", prompt)
        write_image(folder / "overlay.png", overlay)
        write_image(folder / "overlay-with-ct-unknown.png", with_ct)
        for key, mask_value in result.items():
            write_image(folder / (key + ".png"), mask_value.astype(np.uint8) * 255)
        contours, hierarchy = cv2.findContours(
            result["visible"].astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        origin = np.array(panel["source_crop_xywh"][:2])
        records = [
            {
                "xy_native": (c.reshape(-1, 2) + origin).tolist(),
                "hierarchy_next_prev_child_parent": hierarchy[0, i].tolist(),
            }
            for i, c in enumerate(contours)
        ]
        write_json(
            folder / "contours.json",
            {
                "coordinate_frame": "native_source_pixel_center_xy",
                "status": "candidate",
                "contours": records,
            },
        )
        report["objects"][name] = {
            "source_crop_xywh": panel["source_crop_xywh"],
            "positive_prompt_pixels": int(np.count_nonzero(prompt)),
            "visible_material_pixels": int(mask.sum()),
            "ct_occlusion_unknown_pixels": int(ct.sum()),
            "independent_validation": False,
            "topology_unknown_pixels": int(result["topology_unknown"].sum()),
            "prompt_component_count": int(
                cv2.connectedComponents((prompt > 0).astype(np.uint8))[0] - 1
            ),
            "output_component_count": int(cv2.connectedComponents(mask.astype(np.uint8))[0] - 1),
        }
        lines += [
            f"## {name}",
            "",
            f"![原始照片]({name}/raw.png)",
            "",
            f"![候选：AA红 / poly蓝]({name}/overlay.png)",
            "",
            f"[CT不确定支持与搜索域]({name}/overlay-with-ct-unknown.png)",
            "",
        ]
    report["aa_user_separation_checks"] = []
    _, aa_labels = cv2.connectedComponents(
        generated["aa"]["visible"].astype(np.uint8), connectivity=8
    )
    aa_origin = np.array(inputs["aa"][2]["source_crop_xywh"][:2])
    for points in spec.get("aa_separation_checks_native_xy", []):
        local_points = np.array(points) - aa_origin
        if local_points.shape != (2, 2) or not np.isfinite(local_points).all():
            raise ValueError("invalid user AA separation check")
        labels = []
        for x, y in np.round(local_points).astype(int):
            if not 0 <= x < aa_labels.shape[1] or not 0 <= y < aa_labels.shape[0]:
                raise ValueError("AA separation check outside source crop")
            labels.append(int(aa_labels[y, x]))
        passed = labels[0] > 0 and labels[1] > 0 and labels[0] != labels[1]
        report["aa_user_separation_checks"].append(
            {
                "points_native_xy": points,
                "output_labels": labels,
                "passed": passed,
                "independent_validation": False,
            }
        )
        if not passed:
            report["material_status"] = "conflict"
    aa_to_native, poly_to_crop = np.eye(3), np.eye(3)
    aa_to_native[:2, 2] = inputs["aa"][2]["source_crop_xywh"][:2]
    poly_to_crop[:2, 2] = -np.array(inputs["poly"][2]["source_crop_xywh"][:2])
    context_matrix = (
        poly_to_crop @ np.linalg.inv(np.array(registration["matrix_native"])) @ aa_to_native
    )
    context = cv2.warpPerspective(
        generated["aa"]["visible"].astype(np.uint8),
        context_matrix,
        (inputs["poly"][0].shape[1], inputs["poly"][0].shape[0]),
        flags=cv2.INTER_NEAREST,
    )
    write_image(destination / "partial-aa-context-in-poly.png", context * 255)
    panel = cv2.imread(str(destination / "poly/overlay.png"))
    aa_contours, _ = cv2.findContours(context, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(panel, aa_contours, -1, (0, 0, 255), 1)
    write_image(destination / "poly-with-aa-context.png", panel)
    report["aa_context"] = {
        "matrix_aa_crop_to_poly_crop": context_matrix.tolist(),
        "status": "partial_candidate_only_not_a_negative_mask",
        "used_to_veto_poly": False,
    }
    lines += [
        "## AA 空间关系复核",
        "",
        "红线是经冻结配准映射的部分 AA 候选，蓝色为 poly 候选。"
        "未覆盖不代表没有 AA；不以此硬裁剪 poly。",
        "",
        "![部分AA上下文与poly](poly-with-aa-context.png)",
        "",
    ]
    snapshot = destination / "source-snapshot"
    snapshot.mkdir()
    (snapshot / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    report["code_sha256"] = {Path(__file__).name: digest(Path(__file__))}
    for name, source in sources.items():
        if digest(source) != report["source_sha256"][name]:
            raise ValueError("source changed during processing")
    for key, path in paths.items():
        if digest(path) != report["input_sha256"][key]:
            raise ValueError("annotation input changed during processing")
    (destination / "report.md").write_text("\n".join(lines) + "\n")
    write_json(destination / "manifest.json", report)
    return report
