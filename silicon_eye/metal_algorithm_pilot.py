"""Run frozen CPU segmentation and V1 template baselines without adopting geometry.

Run: python -m silicon_eye.metal_algorithm_pilot --spec SPEC --output NEW_DIR
Requires project dependencies, torch and official SAM2; no network calls at runtime.
Probe labels are AI diagnostics, not dense truth or new human decisions.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .geometry_reconstruction import digest


def crop(image, bounds):
    x0, y0, x1, y1 = bounds
    if not (0 <= x0 < x1 <= image.shape[1] and 0 <= y0 < y1 <= image.shape[0]):
        raise ValueError("Crop outside source")
    return image[y0:y1, x0:x1].copy()


def local_points(points, bounds):
    result = np.asarray(points, dtype=np.int32) - np.asarray(bounds[:2])
    if np.any(result < 0) or np.any(result >= np.subtract(bounds[2:], bounds[:2])):
        raise ValueError("Point outside crop")
    return result


def seeded_components(mask, points):
    """Retain only threshold components actually hit by positive prompts; never snap."""
    _, labels = cv2.connectedComponents(mask.astype(np.uint8), connectivity=8)
    selected = set(int(labels[y, x]) for x, y in points) - {0}
    return np.isin(labels, list(selected))


def diagnostics(mask, case):
    points = local_points([p[0:2] for p in case['probes']], case['bounds'])
    expected = np.array([p[2] for p in case['probes']], dtype=bool)
    actual = mask[points[:, 1], points[:, 0]]
    _, components = cv2.connectedComponents(mask.astype(np.uint8), connectivity=8)
    positive_ids = components[points[expected, 1], points[expected, 0]]
    return {
        'positive_probes': int(expected.sum()),
        'missed_positive_probes': int(np.sum(expected & ~actual)),
        'negative_probes': int((~expected).sum()),
        'hit_negative_probes': int(np.sum(~expected & actual)),
        'positive_probes_one_component': bool(
            len(positive_ids) > 0 and np.all(positive_ids > 0)
            and len(set(positive_ids.tolist())) == 1
        ),
        'mask_pixels': int(mask.sum()),
        'scope': 'AI-authored sparse diagnostics; not IoU, human truth or circuit connectivity',
    }


def panel(raw, mask, title):
    rgb = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)
    if mask is not None:
        rgb[mask] = (rgb[mask] * .55 + np.array([0, 255, 160]) * .45).astype(np.uint8)
    im = Image.fromarray(rgb).resize((raw.shape[1] * 2, raw.shape[0] * 2))
    canvas = Image.new('RGB', (max(240, im.width), im.height + 36), 'white')
    canvas.paste(im, (0, 36))
    ImageDraw.Draw(canvas).text((8, 10), title, fill='black')
    return canvas


def run(spec_path, output):
    import torch
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    spec_path, output = Path(spec_path), Path(output)
    if output.exists():
        raise ValueError('Use a new output directory')
    spec = json.loads(spec_path.read_text())
    for source in spec['sources'].values():
        if digest(Path(source['path'])) != source['sha256']:
            raise ValueError('Source hash mismatch')
    if digest(Path(spec['checkpoint']['path'])) != spec['checkpoint']['sha256']:
        raise ValueError('Checkpoint hash mismatch')
    output.mkdir(parents=True)
    (output / 'spec.json').write_text(spec_path.read_text())
    torch.set_num_threads(2)
    torch.manual_seed(spec['seed'])
    cv2.setNumThreads(2)
    cv2.setRNGSeed(spec['seed'])
    start = time.perf_counter()
    model = build_sam2('configs/sam2.1/sam2.1_hiera_t.yaml',
                       spec['checkpoint']['path'], device='cpu', apply_postprocessing=False)
    predictor = SAM2ImagePredictor(model, max_hole_area=0, max_sprinkle_area=0)
    load_seconds = time.perf_counter() - start
    photos = {key: cv2.imread(source['path']) for key, source in spec['sources'].items()}
    rows, review_items = [], []
    for case in spec['cases']:
        raw = crop(photos['m2'], case['bounds'])
        positive = local_points(case['positive'], case['bounds'])
        negative = local_points(case['negative'], case['bounds'])
        box = np.asarray(case['box']) - np.tile(case['bounds'][:2], 2)
        masks, timings, scores = {}, {}, {}
        start = time.perf_counter()
        gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        threshold, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        masks['otsu_seeded'] = seeded_components(binary > 0, positive)
        timings['otsu_seeded'] = time.perf_counter() - start
        start = time.perf_counter()
        labels = np.full(gray.shape, cv2.GC_BGD, np.uint8)
        x0, y0, x1, y1 = box
        labels[y0:y1, x0:x1] = cv2.GC_PR_BGD
        labels[(binary > 0) & (labels == cv2.GC_PR_BGD)] = cv2.GC_PR_FGD
        for points, value in [(positive, cv2.GC_FGD), (negative, cv2.GC_BGD)]:
            for point in points:
                cv2.circle(labels, tuple(point), 1, value, -1)
        cv2.grabCut(raw, labels, None, np.zeros((1, 65)), np.zeros((1, 65)),
                    3, cv2.GC_INIT_WITH_MASK)
        masks['grabcut'] = np.isin(labels, [cv2.GC_FGD, cv2.GC_PR_FGD])
        timings['grabcut'] = time.perf_counter() - start
        with torch.inference_mode():
            start = time.perf_counter()
            predictor.set_image(cv2.cvtColor(raw, cv2.COLOR_BGR2RGB))
            encoding = time.perf_counter() - start
            start = time.perf_counter()
            predicted, quality, _ = predictor.predict(
                point_coords=np.concatenate([positive, negative]),
                point_labels=np.array([1] * len(positive) + [0] * len(negative)),
                box=box, multimask_output=False,
            )
            decoding = time.perf_counter() - start
        masks['sam2_tiny'] = predicted[0].astype(bool)
        timings['sam2_tiny'] = encoding + decoding
        scores['sam2_tiny'] = float(quality[0])
        prefix = output / case['id']
        cv2.imwrite(str(prefix.with_name(case['id'] + '-raw.png')), raw)
        tiles = [panel(raw, None, case['id'] + ' raw')]
        for method, mask in masks.items():
            cv2.imwrite(str(output / f"{case['id']}-{method}-mask.png"), mask.astype('uint8') * 255)
            tiles.append(panel(raw, mask, method))
            rows.append({'case': case['id'], 'method': method, 'seconds': timings[method],
                         'diagnostics': diagnostics(mask, case),
                         'predicted_quality_not_accuracy': scores.get(method),
                         'otsu_threshold': threshold if method == 'otsu_seeded' else None})
        mosaic_size = (sum(t.width for t in tiles), max(t.height for t in tiles))
        mosaic = Image.new('RGB', mosaic_size, 'white')
        x = 0
        for tile in tiles:
            mosaic.paste(tile, (x, 0))
            x += tile.width
        mosaic_path = output / f"{case['id']}-comparison.png"
        mosaic.save(mosaic_path)
        review_items.append({
            'id': case['id'], 'type': 'metal_fragment', 'title': case['description'],
            'prompt': '仅比较分割候选：哪种方法漏线、跨间隙或包含邻线？请在备注写方法名。',
            'review_mode': 'context',
            'facts': {'原生范围': case['bounds'], '性质': '算法对照，不重新审批既有几何'},
            'evidence': [{'path': str(mosaic_path), 'label': '原图 / Otsu / GrabCut / SAM2',
                          'role': 'detail', 'frame': 'm2'}],
        })
        print(case['id'], {m: round(t, 3) for m, t in timings.items()}, flush=True)
    template = spec['template']
    m1 = cv2.cvtColor(photos['m1'], cv2.COLOR_BGR2GRAY)
    patch = crop(m1, template['bounds'])
    template_results = []
    for target in template['targets']:
        search = crop(m1, target['bounds'])
        start = time.perf_counter()
        best, best_box = -1., None
        for scale in template['scales']:
            resized = cv2.resize(patch, None, fx=scale, fy=scale)
            if any(a > b for a, b in zip(resized.shape, search.shape, strict=True)):
                continue
            result = cv2.matchTemplate(search, resized, cv2.TM_CCOEFF_NORMED)
            _, score, _, location = cv2.minMaxLoc(result)
            if score > best:
                best = float(score)
                best_box = [location[0], location[1], resized.shape[1], resized.shape[0]]
        if best_box is None:
            raise ValueError('No template scale fits target')
        template_results.append({**target, 'score': best, 'local_xywh': best_box,
                                 'seconds': time.perf_counter() - start,
                                 'candidate_at_threshold': {str(t): best >= t
                                     for t in template['thresholds']}})
    report = {
        'kind': 'exploratory_algorithm_comparison', 'geometry_adopted': False,
        'human_correction_seconds': None, 'human_baseline_seconds': None,
        'speedup_proven': False, 'dense_truth_available': False,
        'device': 'cpu', 'threads': 2, 'sam_load_seconds': load_seconds,
        'spec_sha256': digest(spec_path), 'code_sha256': digest(Path(__file__)),
        'versions': {p: importlib.metadata.version(p) for p in
                     ['torch', 'torchvision', 'numpy', 'opencv-python']},
        'segmentation': rows, 'template': template_results,
        'limits': spec['limits'],
    }
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    review = {
        'schema_version': 1, 'kind': 'silicon_eye_review_sheet', 'stage': 'METAL',
        'package_id': 'METAL-ALGORITHM-PILOT-20261106', 'date': '2026-11-06',
        'title': '金属算法对照：只读比较，不重审模型',
        'summary': '绿色为候选掩膜；各图原生尺寸相同。稀疏诊断来自AI，不是像素真值。',
        'scope': {'frame': 'm2', 'native_bounds': [180, 2150, 850, 2430],
                  'note': '四个局部窗口；非全幅验收。'},
        'items': review_items, 'questions': [], 'sources': spec['sources'],
        'limitations': spec['limits'],
    }
    (output / 'review-spec.json').write_text(json.dumps(review, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    run(args.spec, args.output)
