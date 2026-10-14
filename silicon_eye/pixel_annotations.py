"""Validate and render source-pixel annotation drafts without generating devices.

Invocation: silicon-eye annotate review --input <json> --output <new-dir>
Requires project OpenCV/Pydantic dependencies. Raw images are never rewritten.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from .registration_audit import digest, write_image, write_json
from .schemas.pixel_annotation import PixelAnnotationSet


def review_annotations(input_path: str, output: str) -> dict:
    path = Path(input_path).resolve()
    document = PixelAnnotationSet.model_validate_json(path.read_text())
    destination = Path(output).resolve()
    if destination.exists():
        raise ValueError("output must be a new directory")
    registration_path = Path(document.registration_manifest).resolve()
    if digest(registration_path) != document.registration_sha256:
        raise ValueError("registration reference hash mismatch")
    registration = json.loads(registration_path.read_text())
    if registration.get("status") != "complete":
        raise ValueError("registration reference is incomplete")
    images, source_paths = {}, {}
    for name, source in document.sources.items():
        source_path = Path(source.path).resolve()
        if source_path.is_relative_to(destination) or destination.is_relative_to(
            source_path.parent
        ):
            raise ValueError("output cannot overwrite or reside in source image directory")
        if digest(source_path) != source.sha256:
            raise ValueError(f"{name}: source hash mismatch")
        if source.sha256 != registration.get("source_sha256", {}).get(source.registration_side):
            raise ValueError(f"{name}: source absent from registration reference")
        image = cv2.imread(str(source_path))
        if image is None or (image.shape[1], image.shape[0]) != source.size_wh:
            raise ValueError(f"{name}: unreadable image or size mismatch")
        images[name], source_paths[name] = image, source_path
    destination.mkdir(parents=True)
    write_json(destination / "manifest.json", {"status": "running"})
    write_json(destination / "annotations.json", document.model_dump(mode="json"))
    counts = dict(Counter(obj.status for obj in document.objects))
    lines = [
        "# 局部像素标注草案",
        "",
        "层语义、几何确认和器件身份分别记录；bbox 是观察区域，不是精确材料掩膜。",
        "",
        f"对象数：{len(document.objects)}；状态统计：{counts}。",
        "物理尺度未知，不输出 μm、器件尺寸、端子或连接。",
        "device_ground_truth_ready=false；segmentation_ground_truth_ready=false。",
        "",
        "| ID | 源图 | 标签 | 角色/用途 | 状态 |",
        "|---|---|---|---|---|",
    ]
    for obj in document.objects:
        lines.append(
            f"| {obj.id} | {obj.source_id} | {obj.label} | {obj.role}/{obj.usage} | {obj.status} |"
        )
        x, y, w, h = obj.bbox_xywh
        x0, y0 = np.floor([x, y]).astype(int)
        x1, y1 = np.ceil([x + w, y + h]).astype(int)
        image = images[obj.source_id]
        # Only derived crops are annotated; never touch an original source array.
        crop = image[
            max(0, y0 - 24) : min(image.shape[0], y1 + 24),
            max(0, x0 - 24) : min(image.shape[1], x1 + 24),
        ].copy()
        write_image(destination / f"{obj.id}-raw.jpg", crop)
    lines += ["", "| Pair | 原图对象 | 状态 |", "|---|---|---|"]
    for pair in document.correspondences:
        lines.append(f"| {pair.id} | {' / '.join(pair.object_ids)} | {pair.status} |")
    for name, source in document.sources.items():
        x, y, w, h = map(int, source.scope_xywh)
        panel = images[name][y : y + h, x : x + w].copy()
        for obj in document.objects:
            if obj.source_id != name:
                continue
            ox, oy, ow, oh = obj.bbox_xywh
            left, top = round(ox - x), round(oy - y)
            color = (0, 255, 255) if obj.role == "registration_control" else (255, 200, 0)
            cv2.rectangle(
                panel, (left, top), (round(ox + ow - x) - 1, round(oy + oh - y) - 1), color, 2
            )
            cv2.putText(
                panel, obj.id, (left, max(15, top - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1
            )
        write_image(destination / f"{name}-annotations.jpg", panel)
        lines += [
            "",
            f"![{name}: yellow=registration, cyan=region candidate]({name}-annotations.jpg)",
        ]
    lines += ["", "| 源图 | 层语义 | 状态 |", "|---|---|---|"]
    for name, source in document.sources.items():
        lines.append(f"| {name} | {source.layer_label} | {source.layer_status} |")
    lines += [
        "",
        "[完整标注和人工层语义确认记录](annotations.json)",
        "[来源、代码版本和状态摘要](manifest.json)",
    ]
    report = {
        "status": "complete",
        "case_id": document.case_id,
        "artifact_kind": "pixel_roi_draft_not_device_or_segmentation_truth",
        "object_count": len(document.objects),
        "correspondence_status_counts": dict(Counter(p.status for p in document.correspondences)),
        "geometry_status_counts": counts,
        "layer_status": {name: s.layer_status for name, s in document.sources.items()},
        "device_ground_truth_ready": False,
        "segmentation_ground_truth_ready": False,
        "physical_scale_status": document.physical_scale_status,
        "input_sha256": digest(path),
        "registration_sha256": document.registration_sha256,
        "registration_acceptance": registration.get("acceptance", "unknown"),
        "source_sha256": {name: s.sha256 for name, s in document.sources.items()},
        "code_sha256": {
            "pixel_annotations.py": digest(Path(__file__)),
            "pixel_annotation.py": digest(Path(__file__).parent / "schemas/pixel_annotation.py"),
        },
    }
    snapshot = destination / "source-snapshot"
    snapshot.mkdir()
    (snapshot / "pixel_annotations.py").write_bytes(Path(__file__).read_bytes())
    (snapshot / "pixel_annotation.py").write_bytes(
        (Path(__file__).parent / "schemas/pixel_annotation.py").read_bytes()
    )
    for name, source in source_paths.items():
        if digest(source) != document.sources[name].sha256:
            raise ValueError("source changed while rendering annotations")
    (destination / "report.md").write_text("\n".join(lines) + "\n")
    write_json(destination / "manifest.json", report)
    return report
