"""Fit similarity transforms from named structural anchors, never validation points.

Anchor coordinates/ROIs and pilot budgets are versioned inputs. Structural centers
are observable image measurements, not evidence that two physical layers match.
"""

from __future__ import annotations

import cv2
import numpy as np


def rectangle_center(
    image: np.ndarray, box: list[int], band: int = 25, min_contrast: float = 10.0
) -> dict:
    """Measure opposite bright edge ridges within AI-selected edge search bands."""
    x, y, width, height = box
    if min(width, height) < 40 or band < 1 or x - band < 8 or y - band < 8:
        raise ValueError("invalid structural box")
    if x + width + band + 8 >= image.shape[1] or y + height + band + 8 >= image.shape[0]:
        raise ValueError("structural edge search outside source")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray.astype(np.float32), (13, 13), 2.5)
    edges, contrast, edge_checks = [], [], []
    horizontal = np.median(smooth[y + height // 5 : y + 4 * height // 5], axis=0)
    vertical = np.median(smooth[:, x + width // 5 : x + 4 * width // 5], axis=1)
    for profile, expected in (
        (horizontal, x),
        (horizontal, x + width),
        (vertical, y),
        (vertical, y + height),
    ):
        segment = profile[expected - band : expected + band + 1]
        baseline = float(np.percentile(segment, 20))
        candidates = [
            expected - band + index
            for index in range(8, len(segment) - 8)
            if segment[index] >= segment[index - 1]
            and segment[index] >= segment[index + 1]
            and segment[index] - baseline >= min_contrast
        ]
        # The AI-selected anatomical edge is the prior. A brighter internal stripe
        # must not displace it merely because it has the global maximum intensity.
        peak = (
            min(candidates, key=lambda value: abs(value - expected))
            if candidates
            else expected - band + int(np.argmax(segment))
        )
        support_inside = expected - band + 8 <= peak <= expected + band - 8
        positions = np.arange(max(peak - 8, expected - band), min(peak + 8, expected + band) + 1)
        weights = np.maximum(profile[positions] - baseline, 0)
        if weights.sum() <= 1e-6:
            raise ValueError("no measurable structural edge")
        edges.append(float(np.average(positions, weights=weights)))
        contrast.append(float(segment.max() - baseline))
        edge_checks.append(
            {
                "support_inside_search_band": bool(support_inside),
                "contrast_sufficient": contrast[-1] >= min_contrast,
            }
        )
    return {
        "xy": [(edges[0] + edges[1]) / 2, (edges[2] + edges[3]) / 2],
        "box_xywh": box,
        "edge_search_band_px": band,
        "edge_positions_lrtb": edges,
        "edge_contrast": contrast,
        "definition": "center of opposite bright rectangular edge ridges",
        "peak_selection": "nearest_supported_local_peak_to_declared_edge",
        "producer": "script_edge_measurement",
        "status": "candidate",
        "measurement_quality": {
            "valid": all(all(check.values()) for check in edge_checks),
            "min_contrast": min_contrast,
            "edge_checks_lrtb": edge_checks,
            "scope": "localization_only_not_structural_identity",
        },
    }


def solve_similarity(anchors: list[dict], limits: dict) -> dict:
    if len(anchors) < 3:
        return {"success": False, "reason": "insufficient_structural_anchors"}
    unreliable = []
    for anchor in anchors:
        for side in ("reference_measurement", "target_measurement"):
            measurement = anchor.get(side)
            if measurement is not None and not measurement.get("measurement_quality", {}).get(
                "valid"
            ):
                unreliable.append(
                    {
                        "anchor_id": anchor["id"],
                        "side": side,
                        "measurement_quality": measurement.get("measurement_quality"),
                        "reason": "missing_or_failed_measurement_quality",
                    }
                )
    if unreliable:
        return {
            "success": False,
            "reason": "unreliable_structural_measurement",
            "quality_failures": unreliable,
        }
    src = np.array([p["target_xy"] for p in anchors], dtype=float)
    dst = np.array([p["reference_xy"] for p in anchors], dtype=float)
    if not np.isfinite(src).all() or not np.isfinite(dst).all():
        raise ValueError("nonfinite structural anchor")
    area = min(cv2.contourArea(cv2.convexHull(p.astype(np.float32))) for p in (src, dst))
    if area < limits["min_anchor_hull_area_px2"]:
        return {
            "success": False,
            "reason": "degenerate_structural_anchors",
            "anchor_area_px2": area,
        }
    design = np.zeros((2 * len(src), 4))
    design[0::2] = np.column_stack([src[:, 0], -src[:, 1], np.ones(len(src)), np.zeros(len(src))])
    design[1::2] = np.column_stack([src[:, 1], src[:, 0], np.zeros(len(src)), np.ones(len(src))])
    solution, _, rank, _ = np.linalg.lstsq(design, dst.ravel(), rcond=None)
    if rank < 4:
        return {"success": False, "reason": "degenerate_structural_anchors"}
    a, b, tx, ty = solution
    matrix = np.array([[a, -b, tx], [b, a, ty], [0, 0, 1]])
    predicted = src @ matrix[:2, :2].T + matrix[:2, 2]
    residuals = np.linalg.norm(predicted - dst, axis=1)
    scale, rotation = float(np.hypot(a, b)), float(np.degrees(np.arctan2(b, a)))
    checks = {
        "scale": limits["min_scale"] <= scale <= limits["max_scale"],
        "rotation": abs(rotation) <= limits["max_rotation_deg"],
        "translation": max(abs(tx), abs(ty)) <= limits["max_translation_px"],
        "anchor_residual": float(max(residuals)) <= limits["max_anchor_residual_px"],
    }
    checks = {key: bool(value) for key, value in checks.items()}
    return {
        "success": all(checks.values()),
        "reason": None if all(checks.values()) else "structural_constraint_violation",
        "matrix": matrix,
        "scale": scale,
        "rotation_deg": rotation,
        "anchor_area_px2": area,
        "anchor_residuals_px": residuals.tolist(),
        "checks": checks,
    }


def validate_constraints(
    document: dict, reference: str, sources: dict, points: dict, fit_roi: list[int]
) -> None:
    if document.get("schema_version") != 1 or document.get("reference") != reference:
        raise ValueError("constraint schema/reference mismatch")
    budget = document["budget"]
    if budget.get("locked_before_registration") is not True:
        raise ValueError("budget must be locked before registration")
    for key in ("p95_px", "max_px"):
        if not np.isfinite(budget[key]) or budget[key] <= 0:
            raise ValueError("invalid locked budget")
    if budget["p95_px"] > budget["max_px"] or not budget.get("basis"):
        raise ValueError("invalid budget ordering/basis")
    limits = document["limits"]
    for key in (
        "min_scale",
        "max_scale",
        "max_rotation_deg",
        "max_translation_px",
        "max_anchor_residual_px",
        "min_anchor_hull_area_px2",
    ):
        if not np.isfinite(limits[key]) or limits[key] <= 0:
            raise ValueError("constraint limits must be finite and positive")
    if limits["min_scale"] > limits["max_scale"]:
        raise ValueError("constraint scale limits reversed")
    for name, anchors in document["layers"].items():
        if name not in sources or name == reference:
            raise ValueError("unknown layer in structural constraints")
        if len({p["id"] for p in anchors}) != len(anchors):
            raise ValueError("duplicate structural anchor ID")
        for anchor in anchors:
            if anchor["role"] != "fitting" or not anchor.get("description"):
                raise ValueError("anchor must be a named fitting structure")
            for key, layer in [("reference_xy", reference), ("target_xy", name)]:
                xy = np.asarray(anchor[key], dtype=float)
                x, y, w, h = fit_roi
                if xy.shape != (2,) or not np.isfinite(xy).all():
                    raise ValueError("invalid anchor coordinates")
                if not x <= xy[0] < x + w or not y <= xy[1] < y + h:
                    raise ValueError("fitting anchor outside declared fit ROI")
                if document["source_sha256"].get(layer) != sources[layer]["sha256"]:
                    raise ValueError("structural anchor source hash mismatch")
                for validation in points.get("layers", {}).get(name, []):
                    radius = validation.get("exclusion_radius_px", 32)
                    if np.linalg.norm(xy - np.array(validation[key])) <= radius:
                        raise ValueError("fitting anchor overlaps independent point")
