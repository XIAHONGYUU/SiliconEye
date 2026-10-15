"""Retire unsupported poly bridges: annotate poly-repair --spec CASE -o NEW_DIR.

Requires human topology review, frozen material masks, OpenCV and numpy.
Retired pixels are unknown, never confirmed material-negative labels.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import cv2
import numpy as np

from .registration_audit import digest, write_image, write_json


def rectangle(shape: tuple, box: list) -> np.ndarray:
    x, y, w, h = box
    if min(x, y) < 0 or min(w, h) <= 0 or x+w > shape[1] or y+h > shape[0]:
        raise ValueError('Repair/protection box outside image')
    result = np.zeros(shape, bool)
    result[y:y+h, x:x+w] = True
    return result


def repair_support(poly: np.ndarray, ct: np.ndarray, domain: np.ndarray,
                   seeds: list, protected: np.ndarray) -> dict:
    """Apply an explicit abstention domain and check global 8-connected topology."""
    if poly.shape != ct.shape or poly.shape != domain.shape or poly.shape != protected.shape:
        raise ValueError('Incompatible masks')
    if len(seeds) != 2:
        raise ValueError('Two gate seeds required')
    for x, y in seeds:
        if x < 0 or y < 0 or x >= poly.shape[1] or y >= poly.shape[0] or not poly[y, x]:
            raise ValueError('Gate seed outside positive support')
    retired = poly & domain
    if not retired.any() or (retired & protected).any():
        raise ValueError('Empty repair or protected gate support would change')
    corrected = poly & ~domain
    _, before = cv2.connectedComponents(poly.astype('uint8'), connectivity=8)
    _, after = cv2.connectedComponents(corrected.astype('uint8'), connectivity=8)
    old_ids = [int(before[y, x]) for x, y in seeds]
    new_ids = [int(after[y, x]) for x, y in seeds]
    if old_ids[0] != old_ids[1]:
        raise ValueError('Baseline no longer has the reviewed gate-merge conflict')
    if 0 in new_ids or new_ids[0] == new_ids[1]:
        raise ValueError('Repair failed to separate both gates globally')
    return dict(positive=corrected, retired=retired, topology_unknown=retired & ~ct,
                ct_underlying_unknown=retired & ct,
                before_seed_labels=old_ids, after_seed_labels=new_ids)


def run_poly_repair(spec_path: str, output: str) -> dict:
    spec_file = Path(spec_path).resolve()
    root = spec_file.parent.parent
    spec = json.loads(spec_file.read_text())
    out = Path(output)
    if out.exists():
        raise ValueError('Output directory already exists')
    paths = {}
    for name, binding in spec['inputs'].items():
        path = root / binding['path']
        if digest(path) != binding['sha256']:
            raise ValueError(f'Changed repair input: {name}')
        paths[name] = path
    review = json.loads(paths['topology_review'].read_text())
    for binding in review['sources'].values():
        if digest(root / binding['path']) != binding['sha256']:
            raise ValueError('Changed human-review evidence')
    decisions = {d['id']: d for d in review['decisions']}
    if decisions['V3_common_gate']['local_end_poly_connected'] is not False or (
        decisions['V3_shared_middle']['status'] != 'human_confirmed'
    ):
        raise ValueError('Missing human gate-separation/shared-M decision')
    material = json.loads(paths['material_approval'].read_text())
    for name, layer in [('aa_mask', 'AA'), ('poly_mask', 'poly'), ('ct_mask', 'CT')]:
        if digest(paths[name]) != material['layers'][layer]['mask_sha256']:
            raise ValueError(f'Input differs from reviewed material: {name}')
    raw = cv2.imread(str(paths['raw_poly']))
    poly = cv2.imread(str(paths['poly_mask']), 0)
    ct = cv2.imread(str(paths['ct_mask']), 0)
    if raw is None or poly is None or ct is None or raw.shape[:2] != poly.shape:
        raise ValueError('Unreadable or incompatible image')
    sample = json.loads(paths['sample'].read_text())
    for name in ['aa', 'poly']:
        panel = sample['panels'][name]
        source = Path(panel['source_path'])
        if digest(source) != panel['source_sha256']:
            raise ValueError('Changed original source')
        x, y, w, h = panel['source_crop_xywh']
        crop = cv2.imread(str(paths[f'raw_{name}']))
        if not np.array_equal(crop, cv2.imread(str(source))[y:y+h, x:x+w]):
            raise ValueError('Crop differs from original photo')
    poly, ct = poly > 0, ct > 0
    domain = rectangle(poly.shape, spec['separator_xywh_poly_crop'])
    protected = np.zeros_like(poly)
    for box in spec['protected_gate_bands_xywh']:
        protected |= rectangle(poly.shape, box)
    repaired = repair_support(poly, ct, domain, spec['gate_seed_pair_xy_poly_crop'], protected)
    sensitivity = []
    for box in spec['sensitivity_separators_xywh']:
        alternative = repair_support(poly, ct, rectangle(poly.shape, box),
                                     spec['gate_seed_pair_xy_poly_crop'], protected)
        sensitivity.append(dict(xywh_poly_crop=box,
                                retired_pixels=int(alternative['retired'].sum()),
                                separated=True))
    out.mkdir(parents=True)
    for key, filename in [('aa_mask', '01-AA-mask.png'), ('ct_mask', '03-CT-mask.png'),
                          ('raw_aa', 'raw-aa.png'), ('raw_poly', 'raw-poly.png')]:
        shutil.copyfile(paths[key], out / filename)
    for key, filename in [('positive', '02-poly-mask.png'), ('retired', 'retired-support.png'),
                          ('topology_unknown', 'poly-topology-unknown.png'),
                          ('ct_underlying_unknown', 'retired-CT-underlying-unknown.png')]:
        write_image(out / filename, repaired[key].astype('uint8') * 255)
    write_image(out / 'separator-review-domain.png', domain.astype('uint8') * 255)
    old, new, diff = raw.copy(), raw.copy(), raw.copy()
    for image, mask in [(old, poly), (new, repaired['positive'])]:
        image[mask] = (.4*image[mask] + .6*np.array([240, 90, 30])).astype('uint8')
    new[repaired['topology_unknown']] = (0, 170, 255)
    new[repaired['ct_underlying_unknown']] = (210, 50, 210)
    diff[repaired['retired']] = (0, 170, 255)
    # Panel titles use native coordinate rectangles, with no interpolated geometry.
    for name, box, scale in [('V3', spec['roi_xywh_poly_crop'], 3),
                              ('left-end', [830, 395, 65, 90], 4),
                              ('right-end', [1230, 395, 65, 90], 4)]:
        x, y, w, h = box
        rectangle(poly.shape, box)
        tiles = []
        for title, image in [('RAW POLY', raw), ('BEFORE', old),
                              ('AFTER: blue=support, orange/purple=unknown', new),
                              ('RETIRED SUPPORT (unknown)', diff)]:
            panel = cv2.resize(image[y:y+h, x:x+w], (w*scale, h*scale),
                               interpolation=cv2.INTER_NEAREST)
            header = np.full((28, w*scale, 3), 25, np.uint8)
            cv2.putText(header, title if w > 100 else title.split(':')[0], (4, 19),
                        cv2.FONT_HERSHEY_SIMPLEX, .45, (255, 255, 255), 1, cv2.LINE_AA)
            tiles.append(np.vstack([header, panel]))
        comparison = np.vstack(tiles) if w > 100 else np.hstack(tiles)
        write_image(out / f'{name}-comparison.png', comparison)
    x, y, w, h = spec['separator_xywh_poly_crop']
    ox, oy = sample['panels']['poly']['source_crop_xywh'][:2]
    result = dict(
        status='candidate_repair_pending_visual_review', unit='poly_source_px',
        source_spec=spec, spec_sha256=digest(spec_file), code_sha256=digest(Path(__file__)),
        runtime_ai_used=False, geometry_status='not_pixel_ground_truth',
        separator_poly_native_xywh=[x+ox, y+oy, w, h],
        gate_seed_pair_xy_poly_crop=spec['gate_seed_pair_xy_poly_crop'],
        seed_labels_before=repaired['before_seed_labels'],
        seed_labels_after=repaired['after_seed_labels'],
        retired_pixels=int(repaired['retired'].sum()),
        topology_unknown_pixels=int(repaired['topology_unknown'].sum()),
        ct_underlying_unknown_pixels=int(repaired['ct_underlying_unknown'].sum()),
        added_positive_pixels=int((repaired['positive'] & ~poly).sum()),
        outside_domain_unchanged=bool(np.array_equal(poly[~domain],
                                                    repaired['positive'][~domain])),
        protected_gate_support_unchanged=bool(np.array_equal(poly[protected],
                                                            repaired['positive'][protected])),
        material_output_sha256={n: digest(out / f) for n, f in [
            ('AA', '01-AA-mask.png'), ('poly', '02-poly-mask.png'), ('CT', '03-CT-mask.png')]},
        shared_M_relation=decisions['V3_shared_middle'], sensitivity=sensitivity,
        mask_zero_means='no_current_positive_support; not confirmed absence',
        gate_connection='local_end_poly_rejected_by_human; remote_metal_unknown',
        environment=dict(opencv=cv2.__version__, numpy=np.__version__),
        confirmed_netlist_ready=False,
    )
    write_json(out / 'manifest.json', result)
    lines = ['# V3 poly局部拓扑修正候选', '',
             '依据用户裁决：M为共享源漏区，G1/G2不经局部端部poly相连。',
             '原mask除端部外，在M行也有内部竖向误连；分隔带覆盖所有这些路径。',
             '蓝色为保留的poly正支持，橙色为撤销后拓扑未知，紫色为CT下层未知。',
             '这不是确认的无poly负例；边界不清的像素不强制分类。', '',
             f"撤销正支持 {result['retired_pixels']}px：拓扑未知"
             f" {result['topology_unknown_pixels']}px，CT下层未知"
             f" {result['ct_underlying_unknown_pixels']}px。无新增正支持。",
             '全图8连通检查：上下栅代表点从同分量变为不同分量；非器件计数。',
             '上下可见栅条带保护区和分隔带外逐像素不变。AA/CT文件字节不变，M共享关系保留。',
             '未知域宽度为AI局部判断，不是已测量误差或精确物理间隙。', '',
             '## 带宽敏感性', '', '| 分隔带高度(px) | 撤销正支持(px) | 两栅分离 |',
             '| --- | --- | --- |']
    for item in sensitivity:
        lines.append(f"| {item['xywh_poly_crop'][3]} | {item['retired_pixels']} | 是 |")
    lines += ['', '多带宽均分离只说明拓扑稳定，不证明选定像素边界正确。', '',
              '![V3前后对照](V3-comparison.png)', '',
              '## 左端', '', '![左端](left-end-comparison.png)', '',
              '## 右端', '', '![右端](right-end-comparison.png)', '',
              '下一关：复核本次撤销支持范围；随后基于分离后的两栅核对CT归属。',
              '旧mask、原图、冻结配准与既有批准记录保持不变。']
    (out / 'report.md').write_text('\n'.join(lines)+'\n')
    return result
