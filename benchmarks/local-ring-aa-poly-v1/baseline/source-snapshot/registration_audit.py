"""Reproducible registration evidence packs; invoked by `silicon-eye register`.

Requires the declared OpenCV/NumPy dependencies. Independent points are evaluated
only after fitting on a disjoint ROI; unreviewed points cannot establish acceptance.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import cv2
import numpy as np

from .config import load_config
from .phase1_image.stitcher import Stitcher
from .registration_constraints import solve_similarity, validate_constraints


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def write_image(path: Path, image: np.ndarray) -> None:
    if not cv2.imwrite(str(path), image):
        raise OSError(f"Cannot write image: {path}")


def fit_image(image: np.ndarray, roi: list[int], max_dimension: int) -> tuple:
    x, y, width, height = roi
    if x < 0 or y < 0 or width < 8 or height < 8:
        raise ValueError("fit ROI must have nonnegative origin and size >= 8")
    if x + width > image.shape[1] or y + height > image.shape[0]:
        raise ValueError("fit ROI is outside an input image")
    scale = min(1.0, max_dimension / max(width, height))
    size = (round(width * scale), round(height * scale))
    if min(size) < 8:
        raise ValueError("resized fit ROI must retain at least 8 pixels per side")
    crop = cv2.resize(image[y : y + height, x : x + width], size, interpolation=cv2.INTER_AREA)
    # Use actual rounded x/y scale; all matrices use x/y, not row/column.
    to_fit = np.float64(
        [
            [size[0] / width, 0, -x * size[0] / width],
            [0, size[1] / height, -y * size[1] / height],
            [0, 0, 1],
        ]
    )
    return crop, to_fit


def full_matrix(
    matrix: np.ndarray, ref_to_fit: np.ndarray, target_to_fit: np.ndarray
) -> np.ndarray:
    homogeneous = matrix if matrix.shape == (3, 3) else np.vstack([matrix, [0, 0, 1]])
    return np.linalg.inv(ref_to_fit) @ homogeneous @ target_to_fit


def validate_points(document: dict, reference: str, sources: dict, roi: list[int]) -> None:
    if document.get("reference") != reference or document.get("schema_version") != 1:
        raise ValueError("point schema version/reference mismatch")
    x, y, width, height = roi
    used_ids = set()
    for layer, records in document.get("layers", {}).items():
        if layer not in sources or layer == reference:
            raise ValueError(f"Unknown target layer in points: {layer}")
        for record in records:
            identifier = record["id"]
            if not isinstance(identifier, str) or not identifier.replace("-", "").isalnum():
                raise ValueError("point IDs must be alphanumeric with optional hyphens")
            if (layer, identifier) in used_ids:
                raise ValueError("duplicate point ID")
            used_ids.add((layer, identifier))
            if record.get("role") != "validation" or record.get("status") not in {
                "candidate",
                "confirmed",
                "unknown",
                "conflict",
            }:
                raise ValueError("points need validation role and explicit status")
            if not record.get("producer") or not record.get("description"):
                raise ValueError("points need producer and structural description")
            margin = record.get("exclusion_radius_px", 32)
            if not isinstance(margin, (int, float)) or not np.isfinite(margin) or margin < 0:
                raise ValueError("invalid point exclusion radius")
            for key, name in [("reference_xy", reference), ("target_xy", layer)]:
                point = np.asarray(record[key], dtype=float)
                if point.shape != (2,) or not np.isfinite(point).all():
                    raise ValueError("point coordinates must be finite x/y pairs")
                px, py = point
                image_width, image_height = sources[name]["size"]
                if not 0 <= px < image_width or not 0 <= py < image_height:
                    raise ValueError(f"{layer}/{identifier}: point outside source")
                if (
                    x - margin <= px <= x + width + margin
                    and y - margin <= py <= y + height + margin
                ):
                    raise ValueError(f"{layer}/{identifier}: validation point overlaps fit ROI")
                if document.get("source_sha256", {}).get(name) != sources[name]["sha256"]:
                    raise ValueError(f"{name}: point annotation source hash mismatch")
            if record["status"] == "confirmed" and not record.get("reviewed_by"):
                raise ValueError("confirmed points require a reviewer")


def evaluate_points(
    matrix: np.ndarray | None, records: list[dict], threshold_px: float | None, ref_shape: tuple
) -> dict:
    if matrix is None:
        return {"status": "unknown", "reason": "registration_failed", "count": len(records)}
    if not records:
        return {"status": "unknown", "reason": "no_independent_points", "count": 0}
    values = []
    for record in records:
        target = np.append(record["target_xy"], 1.0)
        transformed = matrix @ target
        if abs(transformed[2]) < 1e-12:
            raise ValueError("point projected to infinity")
        predicted = transformed[:2] / transformed[2]
        residual = predicted - record["reference_xy"]
        values.append(
            {
                **record,
                "predicted_reference_xy": predicted.tolist(),
                "residual_xy_px": residual.tolist(),
                "error_px": float(np.linalg.norm(residual)),
                "before_error_px": float(
                    np.linalg.norm(np.array(record["target_xy"]) - record["reference_xy"])
                ),
            }
        )
    errors = [p["error_px"] for p in values]
    xy = np.array([p["reference_xy"] for p in values])
    bbox = [*xy.min(axis=0).tolist(), *xy.max(axis=0).tolist()]
    quadrants = {(int(p[0] >= ref_shape[1] / 2), int(p[1] >= ref_shape[0] / 2)) for p in xy}
    reason = None
    if any(p["status"] != "confirmed" for p in records):
        reason = "points_need_review"
    elif threshold_px is None:
        reason = "no_locked_error_budget"
    elif len(records) < 6 or len(quadrants) < 3:
        reason = "insufficient_spatial_coverage"
    return {
        "status": "unknown"
        if reason
        else ("confirmed" if max(errors) <= threshold_px else "conflict"),
        "reason": reason,
        "count": len(records),
        "points": values,
        "median_px": float(np.median(errors)),
        "p95_px": float(np.percentile(errors, 95)),
        "max_px": float(max(errors)),
        "before_median_px": float(np.median([p["before_error_px"] for p in values])),
        "reference_bbox_xyxy": bbox,
        "covered_quadrants": len(quadrants),
        "threshold_px": threshold_px,
        "scope": "annotated_structures_only",
    }


def preview(image: np.ndarray, limit: int = 1200) -> np.ndarray:
    scale = min(1, limit / max(image.shape[:2]))
    return cv2.resize(
        image,
        (round(image.shape[1] * scale), round(image.shape[0] * scale)),
        interpolation=cv2.INTER_AREA,
    )


def overlay(reference: np.ndarray, target: np.ndarray) -> np.ndarray:
    red = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    cyan = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
    return cv2.merge([cyan, cyan, red])


def patch(image: np.ndarray, center: list, side: int = 256) -> np.ndarray:
    x, y = (round(v) for v in center)
    canvas = np.zeros((side, side, 3), dtype=np.uint8)
    left, top = x - side // 2, y - side // 2
    x0, y0 = max(0, left), max(0, top)
    x1, y1 = min(image.shape[1], left + side), min(image.shape[0], top + side)
    if x1 > x0 and y1 > y0:
        canvas[y0 - top : y1 - top, x0 - left : x1 - left] = image[y0:y1, x0:x1]
    return canvas


def local_panel(
    reference: np.ndarray, target: np.ndarray, aligned: np.ndarray | None, record: dict
) -> np.ndarray:
    ref = patch(reference, record["reference_xy"])
    raw = patch(target, record["target_xy"])
    before = overlay(
        patch(reference, record["reference_xy"]), patch(target, record["reference_xy"])
    )
    after = (
        overlay(patch(reference, record["reference_xy"]), patch(aligned, record["reference_xy"]))
        if aligned is not None
        else np.zeros_like(ref)
    )
    panels = [ref, raw, before, after]
    for image in (ref, raw, after):
        cv2.drawMarker(image, (128, 128), (0, 255, 255), cv2.MARKER_CROSS, 14, 1)
    predicted = record.get("predicted_reference_xy")
    if predicted is not None:
        location = tuple(
            round(p - r + 128) for p, r in zip(predicted, record["reference_xy"], strict=True)
        )
        if all(0 <= v < 256 for v in location):
            cv2.drawMarker(after, location, (255, 0, 255), cv2.MARKER_CROSS, 14, 1)
    titles = [
        "reference (yellow cross)",
        "target at annotated point",
        "before: ref red/target cyan",
        "after" if aligned is not None else "FAILED: no aligned image",
    ]
    result = np.zeros((286, 1024, 3), dtype=np.uint8)
    for index, (image, title) in enumerate(zip(panels, titles, strict=True)):
        result[30:, index * 256 : (index + 1) * 256] = image
        cv2.putText(
            result, title, (index * 256 + 4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1
        )
    return result


def run_audit(
    config_path: str,
    data_root: str,
    reference_name: str,
    output: str,
    fit_roi: list[int],
    points_path: str | None = None,
    method: str = "orb",
    transform_type: str = "similarity",
    max_dimension: int = 1600,
    threshold_px: float | None = None,
    constraints_path: str | None = None,
) -> dict:
    config = load_config(config_path)
    if len(config.tiles) != 1:
        raise ValueError("registration audit currently requires exactly one tile")
    names = [layer.name for layer in config.layers]
    if reference_name not in names or len(names) != len(set(names)):
        raise ValueError("reference must be a unique configured layer")
    if max_dimension < 32 or (
        threshold_px is not None and (not np.isfinite(threshold_px) or threshold_px <= 0)
    ):
        raise ValueError("invalid max dimension/error budget")
    cv2.setNumThreads(2)
    sources = {}
    directory = Path(data_root) / config.chip.name / config.tiles[0].id
    for name in names:
        files = [directory / f"{name}{ext}" for ext in (".jpg", ".png", ".jpeg", ".tif", ".tiff")]
        files = [p for p in files if p.exists()]
        if len(files) != 1:
            raise ValueError(f"{name}: expected exactly one source image, found {len(files)}")
        image = cv2.imread(str(files[0]))
        if image is None:
            raise ValueError(f"Cannot read {files[0]}")
        fit_image(image, fit_roi, max_dimension)
        sources[name] = {
            "path": str(files[0].resolve()),
            "sha256": digest(files[0]),
            "size": [image.shape[1], image.shape[0]],
        }
    document = (
        json.loads(Path(points_path).read_text())
        if points_path
        else {"schema_version": 1, "reference": reference_name, "layers": {}}
    )
    validate_points(document, reference_name, sources, fit_roi)
    constraints = json.loads(Path(constraints_path).read_text()) if constraints_path else None
    if constraints is not None:
        if transform_type != "similarity" or threshold_px is not None:
            raise ValueError("constraints require similarity and their own locked budget")
        validate_constraints(constraints, reference_name, sources, document, fit_roi)
    output_dir = Path(output).resolve()
    source_dir = directory.resolve()
    if output_dir == source_dir or output_dir.is_relative_to(source_dir):
        raise ValueError("output cannot be inside original input directory")
    output_dir.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    manifest = {
        "schema_version": 1,
        "status": "running",
        "created_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "reference": reference_name,
        "inputs": sources,
        "parameters": {
            "fit_roi_xywh": fit_roi,
            "max_dimension": max_dimension,
            "method": method,
            "transform_type": transform_type,
            "threshold_px": threshold_px,
            "solver_mode": "structural_similarity" if constraints else method,
            "opencv_threads": 2,
            "rng_seed": 0,
            "max_features": 5000,
            "match_ratio": 0.75,
        },
        "code": {
            "git_head": head,
            "sha256": {
                str(p.relative_to(root)): digest(p)
                for p in [
                    Path(__file__),
                    root / "silicon_eye/phase1_image/stitcher.py",
                    root / "silicon_eye/cli.py",
                    root / "silicon_eye/registration_constraints.py",
                ]
            },
        },
        "environment": {
            "python": platform.python_version(),
            "opencv": cv2.__version__,
            "numpy": np.__version__,
        },
        "config": {"path": str(Path(config_path).resolve()), "sha256": digest(Path(config_path))},
        "point_annotations": {
            "path": str(Path(points_path).resolve()) if points_path else None,
            "sha256": digest(Path(points_path)) if points_path else None,
            "snapshot": "points.json",
        },
        "layers": {},
        "structural_constraints": {
            "path": str(Path(constraints_path).resolve()) if constraints_path else None,
            "sha256": digest(Path(constraints_path)) if constraints_path else None,
            "budget": constraints["budget"] if constraints else None,
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "points.json", document)
    if constraints:
        write_json(output_dir / "constraints.json", constraints)
    # Capture actual uncommitted code as well as hashes, so this run stays reproducible.
    for relative, expected in manifest["code"]["sha256"].items():
        content = (root / relative).read_bytes()
        if hashlib.sha256(content).hexdigest() != expected:
            raise RuntimeError("Code changed while preparing the evidence pack")
        destination = output_dir / "source-snapshot" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    (output_dir / "source-snapshot" / "config.yaml").write_bytes(Path(config_path).read_bytes())
    reference = cv2.imread(sources[reference_name]["path"])
    ref_fit, ref_to_fit = fit_image(reference, fit_roi, max_dimension)
    ref_preview = preview(reference)
    write_image(output_dir / "reference.jpg", ref_preview)
    for name in names:
        print(f"Registration audit: {name} -> {reference_name}", flush=True)
        target = cv2.imread(sources[name]["path"])
        target_fit, target_to_fit = fit_image(target, fit_roi, max_dimension)
        layer_dir = output_dir / name
        layer_dir.mkdir()
        write_image(layer_dir / "original_preview.jpg", preview(target))
        structural = None
        if name == reference_name:
            result = {
                "success": True,
                "method": "reference_identity",
                "reason": None,
                "matrix": np.eye(3),
                "num_matches": 0,
                "inlier_ratio": None,
                "rmse": None,
                "correlation": None,
                "attempts": [],
            }
        elif constraints is not None:
            structural = solve_similarity(
                constraints["layers"].get(name, []), constraints["limits"]
            )
            proposal = structural.get("matrix")
            result = {
                "success": structural["success"],
                "method": "structural_similarity",
                "reason": structural["reason"],
                "matrix": proposal if proposal is not None else np.eye(3),
                "num_matches": 0,
                "inlier_ratio": None,
                "rmse": None,
                "correlation": None,
                "attempts": [],
            }
        else:
            cv2.setRNGSeed(0)
            result = Stitcher().register_layers(
                ref_fit, target_fit, method=method, transform_type=transform_type
            )
        proposal_matrix = (
            structural.get("matrix")
            if structural is not None
            else full_matrix(result["matrix"], ref_to_fit, target_to_fit)
            if result["success"]
            else None
        )
        matrix = proposal_matrix if result["success"] else None
        aligned, mask = (
            Stitcher._warp(target, matrix, reference.shape[:2])
            if matrix is not None
            else (None, None)
        )
        preview_scale = np.float64(
            [
                [ref_preview.shape[1] / reference.shape[1], 0, 0],
                [0, ref_preview.shape[0] / reference.shape[0], 0],
            ]
        )
        target_at_identity = cv2.warpAffine(target, preview_scale, ref_preview.shape[1::-1])
        before = overlay(ref_preview, target_at_identity)
        write_image(layer_dir / "before_overlay.jpg", before)
        if aligned is not None:
            write_image(layer_dir / "aligned_preview.jpg", preview(aligned))
            write_image(layer_dir / "after_overlay.jpg", overlay(ref_preview, preview(aligned)))
            write_image(layer_dir / "valid_mask_preview.png", preview(mask.astype(np.uint8) * 255))
        records = document.get("layers", {}).get(name, [])
        evaluation = (
            evaluate_points(
                proposal_matrix,
                records,
                constraints["budget"]["max_px"] if constraints else threshold_px,
                reference.shape,
            )
            if name != reference_name
            else {"status": "reference", "count": 0}
        )
        if constraints is not None and name != reference_name:
            budget = constraints["budget"]
            numeric_met = (
                (
                    evaluation["p95_px"] <= budget["p95_px"]
                    and evaluation["max_px"] <= budget["max_px"]
                )
                if "p95_px" in evaluation
                else None
            )
            evaluation["budget_check"] = {
                "p95_limit_px": budget["p95_px"],
                "max_limit_px": budget["max_px"],
                "numeric_met": numeric_met,
                "structural_constraints_met": result["success"],
                "scope": budget["scope"],
                "human_confirmed": bool(records)
                and all(p["status"] == "confirmed" for p in records),
            }
            evaluation["transform_accepted_by_solver"] = result["success"]
            if not result["success"]:
                evaluation["status"] = "unknown"
                evaluation["reason"] = result["reason"]
            elif evaluation["status"] == "confirmed" and not numeric_met:
                evaluation["status"] = "conflict"
                evaluation["reason"] = "independent_error_budget_exceeded"
        locations = evaluation.get("points", records) or [
            {
                "id": f"grid-{index}",
                "reference_xy": [reference.shape[1] * x, reference.shape[0] * 0.85],
                "target_xy": [target.shape[1] * x, target.shape[0] * 0.85],
            }
            for index, x in enumerate((0.2, 0.5, 0.8))
        ]
        for record in locations:
            write_image(
                layer_dir / f"local-{record['id']}.jpg",
                local_panel(reference, target, aligned, record),
            )
        info = {
            key: result[key]
            for key in (
                "success",
                "method",
                "reason",
                "num_matches",
                "inlier_ratio",
                "rmse",
                "correlation",
                "attempts",
            )
        }
        info.update(
            {
                "matrix_target_to_reference_native": matrix.tolist()
                if matrix is not None
                else None,
                "matrix_fit": result["matrix"].tolist() if matrix is not None else None,
                "ref_to_fit": ref_to_fit.tolist(),
                "target_to_fit": target_to_fit.tolist(),
                "overlap_fraction": float(mask.mean()) if mask is not None else 0,
                "evaluation": evaluation,
                "metric_units": {
                    "rmse": "resized_fit_pixels",
                    "independent_point_error": "native_reference_pixels",
                    "correlation": "unitless",
                },
                "artifact_directory": name,
                "local_views": [
                    {"id": p["id"], "reference_xy": p["reference_xy"], "target_xy": p["target_xy"]}
                    for p in locations
                ],
                "proposal_matrix_native": proposal_matrix.tolist()
                if proposal_matrix is not None
                else None,
                "structural_fit": {
                    key: value for key, value in structural.items() if key != "matrix"
                }
                if structural is not None
                else None,
            }
        )
        if constraints is not None and name != reference_name:
            info["fit_anchors"] = constraints["layers"].get(name, [])
            info["matrix_fit"] = None  # structural fitting uses native pixel coordinates
        write_json(layer_dir / "transform.json", info)
        manifest["layers"][name] = info
        write_json(output_dir / "manifest.json", manifest)
        del aligned, target, mask
    for source in sources.values():
        if digest(Path(source["path"])) != source["sha256"]:
            raise RuntimeError("Original input changed during audit")
    rows = []
    for name, info in manifest["layers"].items():
        ev = info["evaluation"]
        median = f"{ev['median_px']:.2f}" if "median_px" in ev else "N/A"
        maximum = f"{ev['max_px']:.2f}" if "max_px" in ev else "N/A"
        rows.append(
            f"| [{name}]({name}/transform.json) | {info['success']} | "
            f"{info['method']} | {ev['count']} | "
            f"{median} | {maximum} | {ev['status']} | "
            f"{ev.get('reason') or info['reason'] or '-'} |"
        )
    report = (
        "# Registration evidence pack\n\n"
        f"Reference: {reference_name}. All coordinates/errors are native pixels.\n\n"
        "| Layer | Solver | Method | Points | Median px | Max px | Verdict | Reason |\n"
        "|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
        "Solver success is not geometric acceptance. Candidate points need review; "
        "no accepted error budget means unknown. Point scope and P95 are in transform.json. "
        "Red is reference; cyan is target. Preview images are resized; "
        "local images are 256px native crops. ORB fit RMSE uses resized fit pixels; "
        "the point errors in this table use original reference pixels. Rejected structural "
        "proposals may have diagnostic point errors, but are never accepted or warped.\n\n"
        "Fit and validation regions are disjoint. No model inference service is called. "
        "Original input hashes were checked again after the run.\n"
    )
    report += "\n## Images\n\n"
    for name, info in manifest["layers"].items():
        report += f"- {name}: [original]({name}/original_preview.jpg), "
        report += f"[before]({name}/before_overlay.jpg)"
        if info["success"]:
            report += f", [after]({name}/after_overlay.jpg)"
        for location in info["local_views"]:
            identifier = location["id"]
            report += f", [{identifier}]({name}/local-{identifier}.jpg)"
        report += "\n"
    (output_dir / "report.md").write_text(report)
    manifest["status"] = "complete"
    write_json(output_dir / "manifest.json", manifest)
    return manifest
