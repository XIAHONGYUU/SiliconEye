"""Export AA/poly/CT candidates in review order within the existing local crop.

Run: silicon-eye annotate materials --spec <json> --output <new-dir>.
Uses frozen guided evidence; full-area AA/CT additions are unvalidated candidates.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from .guided_materials import ct_support, preserve_prompt_separation
from .registration_audit import digest, write_image, write_json


def extend_aa(
    raw: np.ndarray, refined: np.ndarray, domain: np.ndarray, prompt: np.ndarray
) -> tuple:
    """Propose unmarked bright AA while preserving previously corrected neighborhoods."""
    if (
        raw.shape[:2] != refined.shape
        or domain.shape != refined.shape
        or prompt.shape != refined.shape
    ):
        raise ValueError("incompatible AA input shapes")
    gray = cv2.GaussianBlur(cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY), (7, 7), 1.5)
    threshold, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    proposal = mask > 0
    proposal[domain] = refined[domain]
    proposal, unknown, conflicts = preserve_prompt_separation(proposal, prompt)
    if not np.array_equal(proposal[domain], refined[domain]):
        raise ValueError("AA extension conflicts with the corrected known neighborhood")
    return (
        proposal,
        unknown,
        {
            "threshold": float(threshold),
            "unreviewed_added_pixels": int(np.count_nonzero(proposal & ~domain)),
            "merge_rejections": conflicts,
        },
    )


def run_material_review(spec_path: str, output: str) -> dict:
    spec_file = Path(spec_path).resolve()
    spec = json.loads(spec_file.read_text())
    if spec["schema_version"] != 1:
        raise ValueError("unsupported material review schema")
    evidence = Path(spec["guided_evidence"]).resolve()
    if digest(evidence / "manifest.json") != spec["guided_manifest_sha256"]:
        raise ValueError("guided evidence hash mismatch")
    prior = json.loads((evidence / "manifest.json").read_text())
    if prior.get("material_status") != "candidate":
        raise ValueError("cannot export conflicted guided evidence")
    for name, expected in spec["artifact_sha256"].items():
        if digest(evidence / name) != expected:
            raise ValueError(f"guided artifact changed: {name}")
    sample = Path(spec["sample_manifest"]).resolve()
    if digest(sample) != spec["sample_manifest_sha256"]:
        raise ValueError("sample mapping hash mismatch")
    meta = json.loads(sample.read_text())
    destination = Path(output).resolve()
    if destination.exists():
        raise ValueError("output must be a new directory")
    images, sources = {}, {}
    for layer in ("aa", "poly"):
        info = meta["panels"][layer]
        source = Path(info["source_path"]).resolve()
        if source.is_relative_to(destination) or destination.is_relative_to(source.parent):
            raise ValueError("output cannot contain or reside beside source images")
        if digest(source) != prior["source_sha256"][layer]:
            raise ValueError("source hash mismatch")
        raw = cv2.imread(str(evidence / layer / "raw.png"))
        x, y, w, h = info["source_crop_xywh"]
        actual = cv2.imread(str(source))
        if actual is None or not np.array_equal(raw, actual[y : y + h, x : x + w]):
            raise ValueError("derived crop differs from original image")
        images[layer], sources[layer] = raw, source
    refined = cv2.imread(str(evidence / "aa/visible.png"), 0) > 0
    domain = cv2.imread(str(evidence / "aa/search_domain.png"), 0) > 0
    prompt = cv2.imread(str(evidence / "aa/human-positive.png"), 0)
    aa, unknown, aa_info = extend_aa(images["aa"], refined, domain, prompt)
    poly = cv2.imread(str(evidence / "poly/visible.png"), 0) > 0
    ct = ct_support(images["poly"])
    _, labels = cv2.connectedComponents(aa.astype(np.uint8), connectivity=8)
    origin = np.array(meta["panels"]["aa"]["source_crop_xywh"][:2])
    checks = []
    for check in prior.get("aa_user_separation_checks", []):
        points = np.array(check["points_native_xy"]) - origin
        values = [int(labels[int(y), int(x)]) for x, y in points]
        valid = values[0] > 0 and values[1] > 0 and values[0] != values[1]
        checks.append(
            {"points_native_xy": check["points_native_xy"], "labels": values, "passed": valid}
        )
        if not valid:
            raise ValueError("AA center/ring separation regressed")
    destination.mkdir(parents=True)
    write_json(destination / "manifest.json", {"status": "running"})
    write_json(destination / "spec.json", spec)
    report = {
        "status": "complete",
        "materials_status": "candidate",
        "unit": "px",
        "layers": {},
        "aa_unmarked_scan": aa_info,
        "aa_user_separation_checks": checks,
        "poly_unchanged": True,
        "ct_scope": "entire_poly_crop_not_only_poly_prompt_area",
        "ct_underlying_material": "unknown",
        "independent_accuracy_evaluated": False,
        "source_sha256": prior["source_sha256"],
        "spec_sha256": digest(spec_file),
    }
    lines = [
        "# AA → poly → CT 顺序检查",
        "",
        "三类结果均为候选，原生像素单位，不推断器件/连接。",
        "AA未标区域为新增亮度候选，可能漏掉灰暗内部；保留示例邻域的修正结果。",
        "poly保持既有示例引导结果；CT扫描整个第二张裁剪，可漏检/混入亮边，不据此判断底层材料。",
        "",
    ]
    configs = [
        ("01-AA", "aa", aa, (0, 0, 255)),
        ("02-poly", "poly", poly, (255, 160, 0)),
        ("03-CT", "poly", ct, (0, 255, 255)),
    ]
    for label, source_id, mask, color in configs:
        raw = images[source_id]
        over = raw.copy()
        over[mask] = (0.55 * over[mask] + 0.45 * np.array(color)).astype(np.uint8)
        write_image(destination / (label + "-mask.png"), mask.astype(np.uint8) * 255)
        write_image(destination / (label + "-overlay.png"), over)
        raw_only = np.zeros_like(raw)
        raw_only[mask] = raw[mask]
        write_image(destination / (label + "-extracted.png"), raw_only)
        contours, hierarchy = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        native_origin = np.array(meta["panels"][source_id]["source_crop_xywh"][:2])
        records = [
            {
                "xy_native": (c.reshape(-1, 2) + native_origin).tolist(),
                "hierarchy_next_prev_child_parent": hierarchy[0, i].tolist(),
            }
            for i, c in enumerate(contours)
        ]
        count, _, stats, centers = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
        items = [
            {
                "component_id": i,
                "bbox_native_xywh": [
                    int(stats[i, 0] + native_origin[0]),
                    int(stats[i, 1] + native_origin[1]),
                    int(stats[i, 2]),
                    int(stats[i, 3]),
                ],
                "pixel_area": int(stats[i, 4]),
                "center_native_xy": (centers[i] + native_origin).tolist(),
            }
            for i in range(1, count)
        ]
        data = {
            "source_id": source_id,
            "source_crop_xywh": meta["panels"][source_id]["source_crop_xywh"],
            "status": "candidate",
            "pixels": int(mask.sum()),
            "components": items,
            "contours": records,
            "component_count_is_not_verified_object_count": True,
        }
        write_json(destination / (label + "-geometry.json"), data)
        report["layers"][label] = {
            "pixels": int(mask.sum()),
            "candidate_components": count - 1,
            "source_id": source_id,
            "status": "candidate",
        }
        lines += [
            f"## {label}",
            "",
            f"![原图叠加]({label}-overlay.png)",
            "",
            f"[二值掩膜]({label}-mask.png) · [单独提取]({label}-extracted.png) · "
            f"[原生几何]({label}-geometry.json)",
            "",
        ]
    write_image(destination / "AA-unmarked-unreviewed.png", (aa & ~domain).astype(np.uint8) * 255)
    write_image(destination / "AA-topology-unknown.png", unknown.astype(np.uint8) * 255)
    write_image(destination / "raw-aa.png", images["aa"])
    write_image(destination / "raw-poly.png", images["poly"])
    snapshot = destination / "source-snapshot"
    snapshot.mkdir()
    report["code_sha256"] = {}
    for source in (
        Path(__file__),
        Path(__file__).with_name("guided_materials.py"),
        Path(__file__).with_name("registration_audit.py"),
    ):
        (snapshot / source.name).write_bytes(source.read_bytes())
        report["code_sha256"][source.name] = digest(source)
    for name, source in sources.items():
        if digest(source) != prior["source_sha256"][name]:
            raise ValueError("source changed during export")
    (destination / "report.md").write_text("\n".join(lines) + "\n")
    write_json(destination / "manifest.json", report)
    return report
