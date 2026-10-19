"""Locate POLY observation candidates using explicitly selected photo templates.

Run: python -m silicon_eye.poly_gate_matching --root . --spec SPEC --output NEW_DIR
Requires OpenCV, NumPy and SciPy. Scores measure resemblance, not material truth.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from scipy.ndimage import maximum_filter

from .geometry_reconstruction import digest
from .poly_full_frame import save
from .scene_geometry import load_locked


def match_region(gray, bbox, templates, threshold, separation):
    """Return independent peaks without imposing an expected count or pitch."""
    x, y, right, bottom = bbox
    if separation <= 0 or not -1 <= threshold <= 1:
        raise ValueError("Invalid matching parameters")
    if not (0 <= x < right <= gray.shape[1] and 0 <= y < bottom <= gray.shape[0]):
        raise ValueError("Search region outside source")
    crop = gray[y:bottom, x:right]
    peaks = []
    for template in templates:
        image = template["image"]
        if image.size == 0 or float(image.std()) < 1e-6:
            raise ValueError("Empty or constant template")
        if image.shape[0] > crop.shape[0] or image.shape[1] > crop.shape[1]:
            continue
        scores = cv2.matchTemplate(crop, image, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where((scores == maximum_filter(scores, size=(13, 17))) & (scores > threshold))
        dx, dy, width, height = template["body_offset_xywh"]
        for yy, xx in zip(ys, xs, strict=True):
            peaks.append(
                dict(
                    template_id=template["id"],
                    score=float(scores[yy, xx]),
                    bbox=[
                        int(x + xx + dx),
                        int(y + yy + dy),
                        int(x + xx + dx + width),
                        int(y + yy + dy + height),
                    ],
                )
            )
    selected = []
    for peak in sorted(peaks, key=lambda item: -item["score"]):
        center = (peak["bbox"][0] + peak["bbox"][2]) / 2
        if any(abs(center - (p["bbox"][0] + p["bbox"][2]) / 2) < separation for p in selected):
            continue
        selected.append(peak)
    return sorted(selected, key=lambda p: p["bbox"][0])


def run(root, spec_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Use a new output directory")
    spec = json.loads(Path(spec_path).read_text())
    model = load_locked(root, spec["parent_model"])
    if digest(root / spec["source"]["path"]) != spec["source"]["sha256"]:
        raise ValueError("Changed source photograph")
    source = cv2.imread(str(root / spec["source"]["path"]))
    gray = cv2.GaussianBlur(cv2.cvtColor(source, cv2.COLOR_BGR2GRAY), (0, 0), spec["blur_sigma_px"])
    by_id = {obj["id"]: obj for obj in model["objects"]}
    templates = []
    pad = spec["template_padding_px"]
    for key in spec["template_object_ids"]:
        points = np.asarray(by_id[key]["native_outline"])
        x, y = points.min(0).astype(int)
        right, bottom = points.max(0).astype(int)
        if x < pad or y < pad or right + pad > gray.shape[1] or bottom + pad > gray.shape[0]:
            raise ValueError("Template padding outside source")
        templates.append(
            dict(
                id=key,
                image=gray[y - pad : bottom + pad, x - pad : right + pad],
                body_offset_xywh=[pad, pad, right - x, bottom - y],
            )
        )
    rows = [
        dict(
            region=region,
            proposals=match_region(
                gray, region["bbox"], templates, spec["threshold"], spec["min_center_separation_px"]
            ),
        )
        for region in spec["regions"]
    ]
    output.mkdir(parents=True)
    save(output / "proposals.json", rows)
    save(output / "spec.json", spec)
    save(
        output / "report.json",
        dict(
            counts={row["region"]["id"]: len(row["proposals"]) for row in rows},
            status="algorithm_candidates_require_AI_and_human_review",
            no_expected_count_or_pitch_used=True,
            code_sha256=digest(Path(__file__)),
        ),
    )
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.spec, args.output)
