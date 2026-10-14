"""Build dual-polarity local contour hypotheses, never confirmed material masks.

Run: silicon-eye annotate contours --spec <json> --output <new-dir>
Requires local OpenCV/NumPy. Uses only named source-pixel region candidates.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from .registration_audit import digest, write_image, write_json
from .schemas.pixel_annotation import PixelAnnotationSet


def threshold_candidates(
    crop: np.ndarray, origin: list[int], sigma: float = 1.5, kernel: int = 7
) -> tuple[dict, dict]:
    if crop.dtype != np.uint8 or crop.ndim != 3 or crop.shape[2] != 3:
        raise ValueError("expected uint8 BGR crop")
    if (
        not np.isfinite(sigma)
        or not 0 < sigma <= 10
        or not isinstance(kernel, int)
        or kernel < 3
        or kernel > 31
        or kernel % 2 == 0
    ):
        raise ValueError("invalid smoothing parameters")
    if min(crop.shape[:2]) < kernel:
        raise ValueError("crop too small")
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray, (kernel, kernel), sigma)
    contrast = float(np.percentile(smooth, 95) - np.percentile(smooth, 5))
    if contrast < 10:
        return {
            "status": "unknown",
            "reason": "insufficient_local_contrast",
            "contrast_p95_minus_p5": contrast,
            "variants": {},
        }, {}
    threshold, bright = cv2.threshold(smooth, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    masks = {"bright": bright, "dark": cv2.bitwise_not(bright)}
    variants = {}
    for polarity, mask in masks.items():
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        records = []
        for index, contour in enumerate(contours):
            local = contour.reshape(-1, 2)
            x, y, w, h = cv2.boundingRect(contour)
            clipped = bool(
                np.any(local[:, 0] == 0)
                or np.any(local[:, 1] == 0)
                or np.any(local[:, 0] == mask.shape[1] - 1)
                or np.any(local[:, 1] == mask.shape[0] - 1)
            )
            records.append(
                {
                    "index": index,
                    "xy_native": (local + origin).tolist(),
                    "bbox_native_xywh": [x + origin[0], y + origin[1], w, h],
                    "hierarchy_next_prev_child_parent": hierarchy[0, index].tolist(),
                    "polygon_area_px2": float(cv2.contourArea(contour)),
                    "perimeter_px": float(cv2.arcLength(contour, True)),
                    "touches_roi_border": clipped,
                    "status": "candidate",
                    "material_identity": "unknown",
                }
            )
        variants[polarity] = {
            "mask_area_px2": int(np.count_nonzero(mask)),
            "contours": records,
            "closed_material_boundary_confirmed": False,
        }
    return {
        "status": "candidate",
        "threshold": float(threshold),
        "contrast_p95_minus_p5": contrast,
        "variants": variants,
        "interpretation": "brightness support alternatives; not material or device truth",
    }, masks


def run_contours(spec_path: str, output: str) -> dict:
    spec_file = Path(spec_path).resolve()
    spec = json.loads(spec_file.read_text())
    if (
        spec["schema_version"] != 1
        or spec["threshold_method"] != "otsu_dual_polarity"
        or spec["morphology"] != "none"
        or spec["semantic_status"] != "unknown"
        or spec["coordinate_frame"] != "native_source_pixel_center_xy"
    ):
        raise ValueError("unsupported contour specification")
    annotation_path = Path(spec["annotations"]).resolve()
    doc = PixelAnnotationSet.model_validate_json(annotation_path.read_text())
    objects = {obj.id: obj for obj in doc.objects}
    ids = spec["object_ids"]
    if not ids or len(ids) != len(set(ids)) or any(name not in objects for name in ids):
        raise ValueError("invalid selected object IDs")
    if any(objects[name].role != "region_candidate" for name in ids):
        raise ValueError("only region candidates may be processed")
    destination = Path(output).resolve()
    if destination.exists():
        raise ValueError("output must be a new directory")
    images, sources = {}, {}
    for source_id in {objects[name].source_id for name in ids}:
        source = doc.sources[source_id]
        path = Path(source.path).resolve()
        if path.is_relative_to(destination) or destination.is_relative_to(path.parent):
            raise ValueError("output cannot contain or reside beside source images")
        if digest(path) != source.sha256:
            raise ValueError("source hash mismatch")
        image = cv2.imread(str(path))
        if image is None or (image.shape[1], image.shape[0]) != source.size_wh:
            raise ValueError("unreadable source or size mismatch")
        images[source_id], sources[source_id] = image, path
    registration = Path(doc.registration_manifest)
    if digest(registration) != doc.registration_sha256:
        raise ValueError("registration reference hash mismatch")
    registered = json.loads(registration.read_text())
    if registered.get("status") != "complete":
        raise ValueError("registration reference is incomplete")
    for source_id in sources:
        source = doc.sources[source_id]
        if source.sha256 != registered.get("source_sha256", {}).get(source.registration_side):
            raise ValueError("source does not match registration reference side")
    # Measure before creating output so invalid parameters fail without artifacts.
    results = {}
    for name in ids:
        obj = objects[name]
        x, y, w, h = obj.bbox_xywh
        x0, y0 = np.floor([x, y]).astype(int)
        x1, y1 = np.ceil([x + w, y + h]).astype(int)
        crop = images[obj.source_id][y0:y1, x0:x1].copy()
        record, masks = threshold_candidates(
            crop, [int(x0), int(y0)], spec["gaussian_sigma"], spec["gaussian_kernel"]
        )
        record.update(
            source_id=obj.source_id,
            crop_native_xywh=[int(x0), int(y0), int(x1 - x0), int(y1 - y0)],
            layer_label=doc.sources[obj.source_id].layer_label,
        )
        results[name] = (record, masks, crop)
    destination.mkdir(parents=True)
    write_json(destination / "manifest.json", {"status": "running"})
    write_json(destination / "spec.json", spec)
    write_json(destination / "annotations.json", doc.model_dump(mode="json"))
    report = {
        "status": "complete",
        "unit": "px",
        "material_ground_truth_ready": False,
        "device_ground_truth_ready": False,
        "processing": "script_threshold_and_contours",
        "ai_role": "development_selected_ROIs_and_reviews_only_no_runtime_vision_model",
        "spec_sha256": digest(spec_file),
        "annotation_sha256": digest(annotation_path),
        "registration_sha256": doc.registration_sha256,
        "source_sha256": {s: doc.sources[s].sha256 for s in sources},
        "objects": {},
    }
    lines = [
        "# 两处内部区域的边界候选",
        "",
        "只有 aa/poly 的 H-inner、V-inner；单位为原图像素。每幅图依次为原图、亮支持、暗支持。",
        "Otsu 的明/暗极性是两种解释，未选定物理材料；孔洞、细小结构保留，不连接或填充。",
        "触及 ROI 边缘的轮廓存在截断风险，不能当作闭合材料边界。无独立 mask，不报告准确率。",
        "",
    ]
    for name, (record, masks, crop) in results.items():
        folder = destination / name
        folder.mkdir()
        write_image(folder / "raw.png", crop)
        panels = [crop.copy()]
        for polarity, mask in masks.items():
            write_image(folder / f"{polarity}-mask.png", mask)
            panel = crop.copy()
            color = np.array([0, 255, 255] if polarity == "bright" else [255, 0, 255], np.uint8)
            panel[mask > 0] = (0.65 * panel[mask > 0] + 0.35 * color).astype(np.uint8)
            origin = np.array(record["crop_native_xywh"][:2])
            for contour in record["variants"][polarity]["contours"]:
                points = (np.array(contour["xy_native"]) - origin).astype(np.int32)
                cv2.polylines(panel, [points], True, tuple(int(v) for v in color), 1)
            panels.append(panel)
        write_image(folder / "comparison.png", np.hstack(panels))
        write_json(folder / "contours.json", record)
        report["objects"][name] = record
        lines += [
            f"## {name}",
            "",
            f"状态：{record['status']}；材料身份 unknown。",
            "",
            f"![原图与候选支持]({name}/comparison.png)",
            "",
            f"[完整原生坐标与拓扑]({name}/contours.json)",
            "",
        ]
    snapshot = destination / "source-snapshot"
    snapshot.mkdir()
    report["code_sha256"] = {}
    for source in (
        Path(__file__),
        Path(__file__).with_name("registration_audit.py"),
        Path(__file__).parent / "schemas/pixel_annotation.py",
    ):
        (snapshot / source.name).write_bytes(source.read_bytes())
        report["code_sha256"][source.name] = digest(source)
    for name, path in sources.items():
        if digest(path) != doc.sources[name].sha256:
            raise ValueError("source changed during processing")
    (destination / "report.md").write_text("\n".join(lines) + "\n")
    write_json(destination / "manifest.json", report)
    return report
