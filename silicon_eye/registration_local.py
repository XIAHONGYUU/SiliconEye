"""Audit one ring neighborhood, without fitting on independent check structures.

Run: python -m silicon_eye.registration_local --spec <json> --output <new-dir>
Requires project OpenCV/NumPy dependencies; raw inputs are never rewritten.
"""

from __future__ import annotations

import argparse
import ast
import json
import platform
from pathlib import Path

import cv2
import numpy as np

from .registration_audit import digest, overlay, patch, write_image, write_json
from .registration_constraints import rectangle_center


def crop_measurement(image: np.ndarray, origin: list[int], box: list[int], band: int) -> dict:
    local_box = [box[0] - origin[0], box[1] - origin[1], *box[2:]]
    measurement = rectangle_center(image, local_box, band=band)
    measurement["xy"] = (np.array(measurement["xy"]) + origin).tolist()
    edges = np.array(measurement["edge_positions_lrtb"]) + [*([origin[0]] * 2), *([origin[1]] * 2)]
    measurement["edge_positions_lrtb"] = edges.tolist()
    measurement["box_xywh"] = box
    return measurement


def corners(measurement: dict) -> np.ndarray:
    left, right, top, bottom = measurement["edge_positions_lrtb"]
    return np.array([[left, top], [right, top], [right, bottom], [left, bottom]])


def ring_translation(reference: dict, target: dict) -> np.ndarray:
    for measurement in (reference, target):
        if not measurement.get("measurement_quality", {}).get("valid"):
            raise ValueError("ring measurement quality failed")
    delta = np.asarray(reference["xy"], dtype=float) - np.asarray(target["xy"], dtype=float)
    if delta.shape != (2,) or not np.isfinite(delta).all():
        raise ValueError("invalid ring center")
    matrix = np.eye(3)
    matrix[:2, 2] = delta
    return matrix


def ring_edge_lines(
    image: np.ndarray, origin: list[int], box: list[int], band: int, settings: dict
) -> dict:
    """Sample declared outer ridges and fit four lines without using check points."""
    # Also validates the full search support against the crop bounds.
    result = crop_measurement(image, origin, box, band)
    gray = cv2.GaussianBlur(
        cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32), (13, 13), 2.5
    )
    x, y = np.array(box[:2]) - origin
    width, height = box[2:]
    fraction = settings["central_fraction"]
    lines, evidence = [], []
    for edge, expected in enumerate((x, x + width, y, y + height)):
        vertical = edge < 2
        start, length = (y, height) if vertical else (x, width)
        positions = (
            np.linspace(
                start + length * (1 - fraction) / 2,
                start + length * (1 + fraction) / 2,
                settings["sample_count"],
            )
            .round()
            .astype(int)
        )
        points = []
        for position in positions:
            profile = gray[position, :] if vertical else gray[:, position]
            segment = profile[expected - band : expected + band + 1]
            baseline = float(np.percentile(segment, 20))
            candidates = [
                i
                for i in range(8, len(segment) - 8)
                if segment[i] >= segment[i - 1]
                and segment[i] >= segment[i + 1]
                and segment[i] - baseline >= settings["min_contrast"]
            ]
            if not candidates:
                continue
            peak = min(candidates, key=lambda i: abs(i - band))
            indices = np.arange(peak - 8, peak + 9)
            weights = np.maximum(segment[indices] - baseline, 0)
            location = expected - band + float(np.average(indices, weights=weights))
            points.append([location, position] if vertical else [position, location])
        if len(points) < settings["min_valid_fraction"] * len(positions):
            raise ValueError(f"ring edge {edge}: insufficient valid samples")
        points = np.array(points, dtype=float)
        independent = points[:, 1 if vertical else 0]
        dependent = points[:, 0 if vertical else 1]
        # Welsch supplies a robust seed; explicit trimming and least squares make
        # the retained support and residual gate reproducible in the evidence.
        vx, vy, cx, cy = cv2.fitLine(
            points.astype(np.float32), cv2.DIST_WELSCH, 0, 0.01, 0.01
        ).ravel()
        slope = float(vx / vy if vertical else vy / vx)
        intercept = float(cx - slope * cy if vertical else cy - slope * cx)
        retained = (
            np.abs(dependent - (slope * independent + intercept)) <= settings["trim_residual_px"]
        )
        if retained.sum() < settings["min_valid_fraction"] * len(positions):
            raise ValueError(f"ring edge {edge}: insufficient consistent samples")
        slope, intercept = np.linalg.lstsq(
            np.column_stack([independent[retained], np.ones(retained.sum())]),
            dependent[retained],
            rcond=None,
        )[0]
        residuals = np.abs(dependent - (slope * independent + intercept)) / np.hypot(1, slope)
        p95 = float(np.percentile(residuals[retained], 95))
        if p95 > settings["max_line_p95_px"]:
            raise ValueError(f"ring edge {edge}: retained line residual exceeds budget")
        # Lines are ax+by+c=0 in crop coordinates.
        line = np.array([1, -slope, -intercept] if vertical else [-slope, 1, -intercept])
        lines.append(line)
        evidence.append(
            {
                "sample_xy_native": (points + origin).tolist(),
                "retained": retained.tolist(),
                "line_crop_abc": line.tolist(),
                "p95_residual_px": p95,
                "all_sample_p95_px": float(np.percentile(residuals, 95)),
                "residuals_px": residuals.tolist(),
                "valid_count": len(points),
            }
        )
    vertices = []
    for vertical, horizontal in ((0, 2), (1, 2), (1, 3), (0, 3)):
        point = np.linalg.solve(
            np.array([lines[vertical][:2], lines[horizontal][:2]]),
            -np.array([lines[vertical][2], lines[horizontal][2]]),
        )
        vertices.append((point + origin).tolist())
    result["corners_native"] = vertices
    result["edge_line_evidence_lrtb"] = evidence
    result["measurement_quality"]["valid"] = True
    result["measurement_quality"]["scope"] = "sampled_line_localization_only"
    result["definition"] = "intersections of sampled outer edge ridge lines"
    return result


def ring_similarity(reference: dict, target: dict, limits: dict) -> tuple[np.ndarray, dict]:
    for measurement in (reference, target):
        if not measurement.get("measurement_quality", {}).get("valid"):
            raise ValueError("ring measurement quality failed")
    src, dst = np.asarray(target["corners_native"]), np.asarray(reference["corners_native"])
    if src.shape != (4, 2) or dst.shape != (4, 2) or not np.isfinite([src, dst]).all():
        raise ValueError("invalid ring corners")
    src_center, dst_center = src.mean(axis=0), dst.mean(axis=0)
    centered = src - src_center
    denominator = np.sum(centered**2)
    if denominator < 1:
        raise ValueError("degenerate ring corners")
    delta = dst - dst_center
    a = float(np.sum(centered * delta) / denominator)
    b = float(np.sum(centered[:, 0] * delta[:, 1] - centered[:, 1] * delta[:, 0]) / denominator)
    linear = np.array([[a, -b], [b, a]])
    matrix = np.eye(3)
    matrix[:2, :2] = linear
    matrix[:2, 2] = dst_center - linear @ src_center
    errors = np.linalg.norm(src @ linear.T + matrix[:2, 2] - dst, axis=1)
    scale, rotation = float(np.hypot(a, b)), float(np.degrees(np.arctan2(b, a)))
    checks = {
        "scale": limits["min_scale"] <= scale <= limits["max_scale"],
        "rotation": abs(rotation) <= limits["max_rotation_deg"],
        "corner_residual": max(errors) <= limits["max_corner_residual_px"],
    }
    diagnostics = {
        "scale": scale,
        "rotation_deg": rotation,
        "corner_residuals_px": errors.tolist(),
        "checks": {key: bool(value) for key, value in checks.items()},
    }
    if not all(checks.values()):
        raise ValueError("ring similarity constraint failed: " + json.dumps(diagnostics))
    return matrix, diagnostics


def load_frozen_transform(spec: dict) -> dict | None:
    frozen = spec.get("frozen_transform")
    if frozen is None:
        return None
    path = Path(frozen["baseline_manifest"]).resolve()
    if digest(path) != frozen["baseline_sha256"]:
        raise ValueError("frozen baseline hash mismatch")
    baseline = json.loads(path.read_text())
    original = json.loads((path.parent / "spec.json").read_text())
    if baseline.get("status") != "complete" or digest(path.parent / "spec.json") != baseline.get(
        "spec_snapshot_sha256", baseline["spec_sha256"]
    ):
        raise ValueError("incomplete or changed frozen baseline")
    if spec["fitting"] != original["fitting"] or spec["budget"] != original["budget"]:
        raise ValueError("frozen fitting settings or budget changed")
    matrix = np.array(baseline["matrix_native"], dtype=float)
    if (
        matrix.shape != (3, 3)
        or not np.isfinite(matrix).all()
        or not np.array_equal(matrix, np.array(frozen["matrix_native"]))
    ):
        raise ValueError("frozen matrix changed")
    for side in ("reference", "target"):
        if (
            spec[side]["sha256"] != baseline["source_sha256"][side]
            or spec[side]["fit_box_xywh"] != original[side]["fit_box_xywh"]
        ):
            raise ValueError("frozen source or fit structure changed")
    snapshot = path.parent / "source-snapshot" / "registration_local.py"
    if digest(snapshot) != baseline["code_sha256"]["registration_local.py"]:
        raise ValueError("frozen fitting code snapshot changed")
    # Changes to reporting/check orchestration are allowed; the fitted algorithms
    # remain byte-identical to the frozen baseline's function definitions.
    for source in (snapshot, Path(__file__)):
        content = source.read_text()
        functions = {
            node.name: ast.get_source_segment(content, node)
            for node in ast.parse(content).body
            if isinstance(node, ast.FunctionDef)
        }
        if source == snapshot:
            old_functions = functions
        else:
            for name in (
                "crop_measurement",
                "ring_edge_lines",
                "ring_similarity",
                "ring_translation",
            ):
                if functions[name] != old_functions[name]:
                    raise ValueError("frozen fitting algorithm changed")
    return baseline


def run_local(spec_path: str, output: str) -> dict:
    spec_file = Path(spec_path).resolve()
    spec = json.loads(spec_file.read_text())
    if spec["schema_version"] != 1 or spec["fitting"]["model"] not in {
        "translation_only",
        "ring_similarity",
    }:
        raise ValueError("unsupported local audit schema/model")
    budget = spec["budget"]
    if (
        budget.get("locked_before_registration") is not True
        or not 0 < budget["p95_px"] <= budget["max_px"]
        or not np.isfinite([budget["p95_px"], budget["max_px"]]).all()
    ):
        raise ValueError("invalid locked budget")
    frozen_baseline = load_frozen_transform(spec)
    destination = Path(output).resolve()
    if destination.exists():
        raise ValueError("output must be a new directory")
    sources, crops, origins, measurements = {}, {}, {}, {}
    cv2.setNumThreads(2)
    for side in ("reference", "target"):
        entry = spec[side]
        source = Path(entry["path"]).resolve()
        if source == destination or source.is_relative_to(destination):
            raise ValueError("output cannot contain source")
        if digest(source) != entry["sha256"]:
            raise ValueError(f"{side}: source hash mismatch")
        image = cv2.imread(str(source))
        if image is None:
            raise ValueError(f"{side}: cannot read source")
        x, y, width, height = entry["crop_xywh"]
        if min(x, y) < 0 or min(width, height) < 40:
            raise ValueError("invalid local crop")
        if x + width > image.shape[1] or y + height > image.shape[0]:
            raise ValueError("local crop outside source")
        crops[side] = image[y : y + height, x : x + width].copy()
        origins[side] = [x, y]
        sources[side] = source
        fit, check = entry["fit_box_xywh"], entry["check_box_xywh"]
        margin = spec["validation"]["minimum_structure_gap_px"]
        if margin < 0 or not any(
            (
                fit[0] + fit[2] + margin < check[0],
                check[0] + check[2] + margin < fit[0],
                fit[1] + fit[3] + margin < check[1],
                check[1] + check[3] + margin < fit[1],
            )
        ):
            raise ValueError("check structure overlaps fitting structure/exclusion gap")
        measurements[side] = {
            role: frozen_baseline["measurements"][side]["fit"]
            if role == "fit" and frozen_baseline is not None
            else crop_measurement(
                crops[side],
                origins[side],
                entry[f"{role}_box_xywh"],
                spec["fitting" if role == "fit" else "validation"]["edge_search_band_px"],
            )
            for role in ("fit", "check")
        }
    model = spec["fitting"]["model"]
    diagnostics = None
    if model == "ring_similarity" and frozen_baseline is None:
        for side in sources:
            measurements[side]["fit"] = ring_edge_lines(
                crops[side],
                origins[side],
                spec[side]["fit_box_xywh"],
                spec["fitting"]["edge_search_band_px"],
                spec["fitting"]["line_sampling"],
            )
    # Frozen validation never invokes a solver or refines the saved matrix.
    if frozen_baseline is not None:
        matrix = np.array(frozen_baseline["matrix_native"], dtype=float)
        diagnostics = frozen_baseline["fit_diagnostics"]
    elif model == "ring_similarity":
        matrix, diagnostics = ring_similarity(
            measurements["reference"]["fit"],
            measurements["target"]["fit"],
            spec["fitting"]["limits"],
        )
    else:
        matrix = ring_translation(measurements["reference"]["fit"], measurements["target"]["fit"])
    check_valid = all(measurements[s]["check"]["measurement_quality"]["valid"] for s in sources)
    ref_points = corners(measurements["reference"]["check"])
    target_points = corners(measurements["target"]["check"])
    predicted = target_points @ matrix[:2, :2].T + matrix[:2, 2]
    errors = np.linalg.norm(predicted - ref_points, axis=1)
    metrics = {
        "median_px": float(np.median(errors)),
        "p95_px": float(np.percentile(errors, 95)),
        "max_px": float(max(errors)),
        "count": 4,
        "before_median_px": float(np.median(np.linalg.norm(target_points - ref_points, axis=1))),
        "center_error_px": float(np.linalg.norm(predicted.mean(axis=0) - ref_points.mean(axis=0))),
    }
    numeric_met = bool(
        check_valid
        and metrics["p95_px"] <= budget["p95_px"]
        and metrics["max_px"] <= budget["max_px"]
    )
    ref_to_local, target_to_native = np.eye(3), np.eye(3)
    ref_to_local[:2, 2] = -np.array(origins["reference"])
    target_to_native[:2, 2] = origins["target"]
    local_matrix = ref_to_local @ matrix @ target_to_native
    ref = crops["reference"]
    target = crops["target"]
    size = (ref.shape[1], ref.shape[0])
    aligned = cv2.warpAffine(target, local_matrix[:2], size)
    valid = cv2.warpAffine(
        np.ones(target.shape[:2], np.uint8), local_matrix[:2], size, flags=cv2.INTER_NEAREST
    )
    before = cv2.warpAffine(target, (ref_to_local @ target_to_native)[:2], size)
    report = {
        "status": "complete",
        "acceptance": "unknown",
        "scope": spec["scope"],
        "reason": "candidate_correspondences" if numeric_met else "local_budget_not_met",
        "matrix_direction": "target_native_to_reference_native",
        "matrix_native": matrix.tolist(),
        "matrix_crop": local_matrix.tolist(),
        "model": model,
        "fit_diagnostics": diagnostics,
        "frozen_transform": spec.get("frozen_transform"),
        "unestimated": ["rotation", "scale", "perspective"]
        if diagnostics is None
        else ["perspective"],
        "validation_usage": spec["validation"].get("usage", "candidate_diagnostic"),
        "measurements": measurements,
        "validation_metrics": metrics,
        "check_measurement_valid": check_valid,
        "numeric_budget_met": numeric_met,
        "budget": budget,
        "correlation_note": spec["validation"]["correlation_note"],
        "source_paths": {s: str(p) for s, p in sources.items()},
        "source_sha256": {s: digest(p) for s, p in sources.items()},
        "spec_sha256": digest(spec_file),
        "environment": {
            "python": platform.python_version(),
            "opencv": cv2.__version__,
            "numpy": np.__version__,
        },
        "points": [],
    }
    if not check_valid:
        report["reason"] = "check_measurement_quality_failed"
    destination.mkdir(parents=True)
    write_json(destination / "manifest.json", {"status": "running"})
    write_json(destination / "spec.json", spec)
    report["spec_snapshot_sha256"] = digest(destination / "spec.json")
    snapshot = destination / "source-snapshot"
    snapshot.mkdir()
    report["code_sha256"] = {}
    for name in ("registration_local.py", "registration_constraints.py", "registration_audit.py"):
        source = Path(__file__).with_name(name)
        (snapshot / name).write_bytes(source.read_bytes())
        report["code_sha256"][name] = digest(source)
    for name, image in {
        "reference.jpg": ref,
        "target.jpg": target,
        "before-overlay.jpg": overlay(ref, before),
        "after-overlay-candidate.jpg": overlay(ref, aligned),
        "valid-mask.png": valid * 255,
    }.items():
        write_image(destination / name, image)
    for i, (r, t, p, error) in enumerate(
        zip(ref_points, target_points, predicted, errors, strict=True)
    ):
        report["points"].append(
            {
                "id": f"CHECK-{i + 1}",
                "status": "candidate",
                "reference_xy": r.tolist(),
                "target_xy": t.tolist(),
                "predicted_reference_xy": p.tolist(),
                "error_px": float(error),
            }
        )
        local_r, local_t = r - origins["reference"], t - origins["target"]
        panel = np.hstack(
            [
                patch(ref, local_r),
                patch(target, local_t),
                overlay(patch(ref, local_r), patch(aligned, local_r)),
            ]
        )
        cv2.drawMarker(panel, (640, 128), (0, 255, 255), cv2.MARKER_CROSS, 14, 1)
        cv2.drawMarker(
            panel,
            tuple(np.round(p - r + [640, 128]).astype(int)),
            (255, 0, 255),
            cv2.MARKER_CROSS,
            14,
            1,
        )
        write_image(destination / f"check-{i + 1}.jpg", panel)
    for side in sources:
        annotated = crops[side].copy()
        for role, color in (("fit", (0, 255, 255)), ("check", (0, 255, 0))):
            box = measurements[side][role]["box_xywh"]
            x, y = np.array(box[:2]) - origins[side]
            cv2.rectangle(annotated, (int(x), int(y)), (int(x + box[2]), int(y + box[3])), color, 2)
            cv2.putText(
                annotated, role, (int(x), int(y) - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
            )
        if "corners_native" in measurements[side]["fit"]:
            vertices = np.round(
                np.array(measurements[side]["fit"]["corners_native"]) - origins[side]
            ).astype(np.int32)
            cv2.polylines(annotated, [vertices], True, (0, 255, 255), 2)
            for vertex in vertices:
                cv2.circle(annotated, tuple(vertex), 4, (0, 255, 255), -1)
        write_image(destination / f"{side}-structures.jpg", annotated)
    parameter_text = (
        f"scale={diagnostics['scale']:.6f}, rotation={diagnostics['rotation_deg']:.4f} deg"
        if diagnostics is not None
        else "single center translation"
    )
    (destination / "report.md").write_text(
        "# 局部环锚点试验\n\n"
        "只评估两层选定小区域；对应关系是 AI 候选，不能证明全片或八层通过。\n\n"
        f"- 结果：{report['reason']}；acceptance=unknown。\n"
        f"- 原生像素平移：dx={matrix[0, 2]:.2f}，dy={matrix[1, 2]:.2f}。\n"
        f"- 模型：{model}；拟合参数：{parameter_text}；未估计：{report['unestimated']}。\n"
        "- 对应关系为 AI 候选；检查结果仅适用于所选局部结构。\n"
        f"- 独立检查结构四角：P95={metrics['p95_px']:.2f}，"
        f"最大={metrics['max_px']:.2f} px；预算={budget['p95_px']}/{budget['max_px']} px。\n"
        f"- 检查结构：{spec['validation'].get('structure', 'declared check rectangle')}。\n"
        "- 四角来自同一结构，角位置由相对边缘剖面构造。\n"
        f"- 检查用途：{report['validation_usage']}；冻结记录：{spec.get('frozen_transform')}。\n"
        "- 配准后的图是候选诊断图，不能视作通过验收。\n\n"
        "[变换和测量记录](manifest.json) · [冻结输入](spec.json)\n\n"
        "![结构定义：黄=拟合，绿=检查](reference-structures.jpg)\n\n"
        "![候选叠加：红=参考，青=目标](after-overlay-candidate.jpg)\n\n"
        "![检查角1：参考/目标/叠加；黄=参考，紫=投影](check-1.jpg)\n"
    )
    for side, source in sources.items():
        if digest(source) != spec[side]["sha256"]:
            raise ValueError("source changed during audit")
    write_json(destination / "manifest.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_local(args.spec, args.output)
    print(
        json.dumps({k: result[k] for k in ("acceptance", "reason", "validation_metrics")}, indent=2)
    )


if __name__ == "__main__":
    main()
