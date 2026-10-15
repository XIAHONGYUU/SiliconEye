"""Export local MOS hypotheses: annotate mos --spec CASE.json -o NEW_DIR.

Requires approved material masks and frozen registration; no device inference service.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import cv2
import numpy as np

from .registration_audit import digest, write_image, write_json


def crop_transform(native: np.ndarray, aa_origin: list, poly_origin: list) -> np.ndarray:
    """Convert poly-native -> AA-native into AA-crop -> poly-crop."""
    aa = np.eye(3)
    aa[:2, 2] = aa_origin[:2]
    poly = np.eye(3)
    poly[:2, 2] = -np.asarray(poly_origin[:2])
    return poly @ np.linalg.inv(native) @ aa


def geometry(aa: np.ndarray, poly: np.ndarray, ct: np.ndarray,
             matrix: np.ndarray, radius: int) -> dict:
    """Compute supports only; CT occlusion never establishes hidden material."""
    h, w = poly.shape
    aligned = cv2.warpPerspective(aa.astype('uint8'), matrix, (w, h),
                                  flags=cv2.INTER_NEAREST) > 0
    valid = cv2.warpPerspective(np.ones(aa.shape, np.uint8), matrix, (w, h),
                                flags=cv2.INTER_NEAREST) > 0
    overlap = aligned & poly & valid
    kernel = np.ones((2 * radius + 1, 2 * radius + 1), np.uint8)
    interior = cv2.erode((aligned & valid).astype('uint8'), kernel,
                         borderType=cv2.BORDER_CONSTANT, borderValue=0) > 0
    core = interior & poly & ~ct & valid
    return dict(aa_aligned=aligned, valid=valid, overlap=overlap,
                visible_overlap=overlap & ~ct, ct_occluded=overlap & ct,
                sensitivity_core=core, sensitivity_band=overlap & ~ct & ~core)


def _overlay(raw: np.ndarray, supports: list) -> np.ndarray:
    result = raw.copy()
    for mask, color in supports:
        result[mask] = (0.45 * result[mask] + 0.55 * np.asarray(color)).astype('uint8')
    return result


def run_mos_review(spec_path: str, output: str) -> dict:
    """Fail on changed evidence, export three AI-selected inspection windows."""
    spec_file = Path(spec_path).resolve()
    spec = json.loads(spec_file.read_text())
    root = spec_file.parent.parent
    out = Path(output)
    if out.exists():
        raise ValueError('Output directory already exists')
    inputs = {}
    for name, item in spec['inputs'].items():
        path = root / item['path']
        if digest(path) != item['sha256']:
            raise ValueError(f'Changed input: {name}')
        inputs[name] = path
    approval = json.loads(inputs['approval'].read_text())
    sample = json.loads(inputs['sample'].read_text())
    registration = json.loads(inputs['registration'].read_text())
    if registration['matrix_direction'] != 'target_native_to_reference_native':
        raise ValueError('Unsupported registration direction')
    if digest(inputs['materials']) != approval['source_manifest_sha256']:
        raise ValueError('Material manifest differs from approval')
    material_dir = inputs['materials'].parent
    masks = {}
    for name, filename in [('AA', '01-AA-mask.png'), ('poly', '02-poly-mask.png'),
                           ('CT', '03-CT-mask.png')]:
        path = material_dir / filename
        if digest(path) != approval['layers'][name]['mask_sha256']:
            raise ValueError(f'Mask differs from approved snapshot: {name}')
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f'Unreadable mask: {name}')
        masks[name] = image > 0
    raw = {}
    for name, side in [('aa', 'reference'), ('poly', 'target')]:
        panel = sample['panels'][name]
        source = Path(panel['source_path'])
        if digest(source) != panel['source_sha256'] or (
            panel['source_sha256'] != registration['source_sha256'][side]
        ):
            raise ValueError(f'Source mismatch: {name}')
        x, y, w, h = panel['source_crop_xywh']
        raw[name] = cv2.imread(str(material_dir / f'raw-{name}.png'))
        native = cv2.imread(str(source))
        if raw[name] is None or not np.array_equal(raw[name], native[y:y+h, x:x+w]):
            raise ValueError(f'Raw crop mismatch: {name}')
        mask = masks['AA' if name == 'aa' else 'poly']
        if mask.shape != (h, w):
            raise ValueError(f'Mask dimensions mismatch: {name}')
    if masks['CT'].shape != masks['poly'].shape:
        raise ValueError('CT dimensions mismatch')
    matrix = crop_transform(np.array(registration['matrix_native']),
                            sample['panels']['aa']['source_crop_xywh'],
                            sample['panels']['poly']['source_crop_xywh'])
    # The macro budget is in reference (AA) pixels; express its envelope on poly canvas.
    radius = math.ceil(registration['budget']['max_px'] * np.linalg.norm(matrix[:2, :2], 2))
    supports = geometry(masks['AA'], masks['poly'], masks['CT'], matrix, radius)
    registered_raw_aa = cv2.warpPerspective(raw['aa'], matrix,
                                           (raw['poly'].shape[1], raw['poly'].shape[0]))
    _, labels, stats, centers = cv2.connectedComponentsWithStats(masks['CT'].astype('uint8'))
    distances = {
        'aa': cv2.distanceTransform((~supports['aa_aligned']).astype('uint8'), cv2.DIST_L2, 5),
        'poly': cv2.distanceTransform((~masks['poly']).astype('uint8'), cv2.DIST_L2, 5),
    }
    combined = _overlay(raw['poly'], [(supports['aa_aligned'], (40, 40, 230)),
                                      (masks['poly'], (230, 90, 30)),
                                      (supports['visible_overlap'], (40, 220, 40)),
                                      (masks['CT'], (0, 220, 255))])
    uncertainty = _overlay(raw['poly'], [(supports['sensitivity_core'], (40, 220, 40)),
                                        (supports['sensitivity_band'], (0, 150, 255)),
                                        (supports['ct_occluded'], (230, 40, 230))])
    candidates = []
    height, width = masks['poly'].shape
    for roi in spec['rois']:
        x, y, w, h = roi['xywh_poly_crop']
        if min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height:
            raise ValueError('ROI outside source crop')
        region = np.s_[y:y+h, x:x+w]
        contacts = []
        for label in np.unique(labels[region]):
            if label == 0:
                continue
            component = labels == label
            contacts.append(dict(
                ct_component_id=int(label), center_poly_crop_xy=centers[label].tolist(),
                bbox_poly_crop_xywh=stats[label, :4].tolist(),
                min_distance_to_visible_support_px={
                    name: float(distance[component].min()) for name, distance in distances.items()
                }, assignment='unknown', underlying_material='unknown',
            ))
        counts = {name: int(mask[region].sum()) for name, mask in supports.items()}
        candidates.append(dict(**roi, status='candidate', counts_px=counts, contacts=contacts,
                               device_count=None, terminal_assignment='unknown',
                               poly_native_xywh=[x+sample['panels']['poly']['source_crop_xywh'][0],
                                                 y+sample['panels']['poly']['source_crop_xywh'][1],
                                                 w, h]))
    out.mkdir(parents=True)
    for name, mask in supports.items():
        write_image(out / f'{name}.png', mask.astype('uint8') * 255)
    for candidate in candidates:
        x, y, w, h = candidate['xywh_poly_crop']
        region = np.s_[y:y+h, x:x+w]
        panels = [raw['poly'][region], registered_raw_aa[region],
                  combined[region], uncertainty[region]]
        sheet = np.concatenate(panels, axis=1)
        write_image(out / f"{candidate['id']}.png", sheet)
        cv2.rectangle(combined, (x, y), (x+w-1, y+h-1), (255, 255, 255), 2)
        cv2.putText(combined, candidate['id'], (x, y-6), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255, 255, 255), 2)
    write_image(out / 'overview.png', combined)
    result = dict(
        status='candidate', unit='poly_source_px', runtime_ai_used=False,
        roi_selection_actor='AI_visual_review_in_current_chat', candidates=candidates,
        matrix_direction='aa_crop_to_poly_crop', matrix=matrix.tolist(),
        registration_acceptance=registration['acceptance'],
        sensitivity_radius_poly_px=radius,
        sensitivity_basis='macro engineering trial max budget; not measured local uncertainty',
        registration_budget=registration['budget'], source_spec=spec,
        spec_sha256=digest(spec_file), code_sha256=digest(Path(__file__)),
        material_mask_sha256={k: v['mask_sha256'] for k, v in approval['layers'].items()},
        device_ground_truth_ready=False,
    )
    write_json(out / 'manifest.json', result)
    lines = ['# 局部 MOS 结构候选（待复核）', '',
             '四联图从左到右：poly 原图 / 配准后的AA原图 / 材料交叠 / 配准敏感性。', '',
             '交叠图：红=变换后的 AA，蓝=poly，绿=可见交叠，黄=CT。',
             f'敏感性图：绿=AA边界内缩{radius}px后保留交叠，橙=边界敏感，紫=CT遮挡。',
             '内缩仅检查AA几何变化；不含poly分割误差，不是可信区间或器件验收。', '',
             'AA与poly来自不同去层照片；使用冻结配准，材料mask未修改。',
             '配准仍为unknown；12 AA px宏观试验预算换算为本图敏感半径。',
             'CT距离是可见mask间最短距离，0仅表示相交，不能证明端子连接。',
             'CT下层材料、源漏/栅/体端命名和器件数量均未确认。单位始终为px。', '']
    for c in candidates:
        lines += [f"## {c['id']}", '', c['interpretation'], '',
                  f"![{c['id']}]({c['id']}.png)", '',
                  f"可见交叠 {c['counts_px']['visible_overlap']} px；"
                  f"内缩后保留 {c['counts_px']['sensitivity_core']} px；"
                  f"相交ROI的CT分量 {len(c['contacts'])} 个（非触点/器件真值计数）。", '']
    lines += ['下一关：人工复核V1/V2是否为单栅结构，以及V3两条带的栅归属；',
              '通过前不生成确认器件或网表。详细CT坐标、距离及输入哈希见manifest.json。']
    (out / 'report.md').write_text('\n'.join(lines) + '\n')
    return result
