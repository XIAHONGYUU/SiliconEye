"""Export enumerated AI CT reviews: annotate ct-audit --spec CASE -o NEW_DIR.

Requires the approved repaired baseline. Runs deterministic checks/rendering only;
AI visual observations are explicit input records, not inferred from a window hit.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from .local_terminal_review import _verified
from .registration_audit import digest, write_image, write_json


def validate_reviews(reviews: list, contacts: list, zones: dict) -> None:
    expected = {(c['roi_id'], c['ct_component_id']): c for c in contacts}
    observed = [(r['roi_id'], r['ct_component_id']) for r in reviews]
    if len(set(observed)) != len(observed) or set(observed) != set(expected):
        raise ValueError('Duplicate, missing or extra CT review records')
    allowed = {'candidate', 'candidate_detection_uncertain', 'excluded', 'conflict'}
    for r in reviews:
        if r['association_review'] not in allowed:
            raise ValueError('CT associations cannot be automatically confirmed')
        terminal = r['candidate_terminal']
        old = expected[(r['roi_id'], r['ct_component_id'])]
        if r['association_review'] in {'excluded', 'conflict'}:
            if terminal is not None:
                raise ValueError('Excluded/conflict CT cannot have an assigned terminal')
        elif terminal not in zones or terminal != old['candidate_zone']:
            raise ValueError('Candidate terminal differs from inspected layout')


def support_evidence(component: np.ndarray, poly: np.ndarray, unknown: np.ndarray,
                     aa: np.ndarray, labels: np.ndarray, gate_labels: dict) -> dict:
    """Overlap is diagnostic; neither overlap nor missing support proves a net."""
    touched = [gate for gate, label in gate_labels.items()
               if label > 0 and np.any(component & (labels == label))]
    return dict(poly_positive_overlap_px=int((component & poly).sum()),
                poly_unknown_overlap_px=int((component & unknown).sum()),
                registered_AA_overlap_px=int((component & aa).sum()),
                poly_gate_domains_touched=touched, confirmed_material_absence=False,
                electrical_connection='unknown')


def render_page(raw: np.ndarray, poly: np.ndarray, unknown: np.ndarray,
                labels: np.ndarray, contacts: list, context: int) -> np.ndarray:
    """Original and mask context side by side; every component has its own tile."""
    sheet = np.full((((len(contacts)+4)//5)*190, 1600, 3), 25, np.uint8)
    for j, c in enumerate(contacts):
        cx, cy = c['center_poly_crop_xy']
        x, y = round(cx)-context//2, round(cy)-context//2
        if min(x, y) < 0 or x+context > raw.shape[1] or y+context > raw.shape[0]:
            raise ValueError('Thumbnail context outside source crop')
        patch = raw[y:y+context, x:x+context].copy()
        overlay = patch.copy()
        pm, um = poly[y:y+context, x:x+context], unknown[y:y+context, x:x+context]
        overlay[pm] = (.45*overlay[pm] + .55*np.array([240, 80, 20])).astype('uint8')
        overlay[um] = (0, 140, 255)
        component = (labels[y:y+context, x:x+context] == c['ct_component_id']).astype('uint8')
        contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, (0, 255, 255), 1)
        for im in [patch, overlay]:
            cv2.drawMarker(im, (round(cx)-x, round(cy)-y), (0, 0, 255),
                           cv2.MARKER_CROSS, 4, 1)
        top, left = j//5*190, j%5*320
        sheet[top+32:top+176, left:left+144] = cv2.resize(
            patch, (144, 144), interpolation=cv2.INTER_NEAREST)
        sheet[top+32:top+176, left+152:left+296] = cv2.resize(
            overlay, (144, 144), interpolation=cv2.INTER_NEAREST)
        title = f"C{c['ct_component_id']} {c['candidate_terminal'] or c['association_review']}"
        cv2.putText(sheet, title,
                    (left+2, top+13), cv2.FONT_HERSHEY_SIMPLEX, .37, (255, 255, 255), 1)
        cv2.putText(sheet, f'crop({cx:.1f},{cy:.1f}) ctx={context}px',
                    (left+2, top+27), cv2.FONT_HERSHEY_SIMPLEX, .35, (255, 255, 255), 1)
    return sheet


def run_ct_audit(spec_path: str, output: str) -> dict:
    spec_file = Path(spec_path).resolve()
    root, out = spec_file.parent.parent, Path(output)
    if out.exists():
        raise ValueError('Output directory already exists')
    spec = json.loads(spec_file.read_text())
    paths = {k: _verified(root, v) for k, v in spec['inputs'].items()}
    approval = json.loads(paths['baseline_approval'].read_text())
    if approval['review_status'] != 'approved_for_this_local_view':
        raise ValueError('Missing repaired-baseline approval')
    repair = json.loads(_verified(root, approval['source_manifest']).read_text())
    _verified(root, approval['source_report'])
    topology = json.loads(_verified(root, approval['prior_topology_review']).read_text())
    inputs = {k: _verified(root, approval['baseline'][k]) for k in [
        'AA', 'CT', 'poly_positive_support', 'poly_topology_unknown',
        'retired_CT_underlying_unknown']}
    for binding in repair['source_spec']['inputs'].values():
        _verified(root, binding)
    prior = json.loads(paths['prior_terminal_manifest'].read_text())
    terminal_spec = json.loads(paths['terminal_spec'].read_text())
    if prior['source_spec'] != terminal_spec:
        raise ValueError('Prior terminal spec mismatch')
    for binding in terminal_spec['inputs'].values():
        _verified(root, binding)
    mos = json.loads(paths['mos_manifest'].read_text())
    sample = json.loads(paths['sample'].read_text())
    for binding in mos['source_spec']['inputs'].values():
        _verified(root, binding)
    raw_path = _verified(root, repair['source_spec']['inputs']['raw_poly'])
    raw = cv2.imread(str(raw_path))
    panel = sample['panels']['poly']
    source = Path(panel['source_path'])
    if digest(source) != panel['source_sha256']:
        raise ValueError('Changed raw photo')
    x, y, w, h = panel['source_crop_xywh']
    if raw is None or not np.array_equal(raw, cv2.imread(str(source))[y:y+h, x:x+w]):
        raise ValueError('Raw crop changed')
    masks = {k: cv2.imread(str(p), 0) for k, p in inputs.items()}
    if any(im is None or im.shape != (h, w) for im in masks.values()):
        raise ValueError('Invalid baseline mask dimensions')
    masks = {k: v > 0 for k, v in masks.items()}
    poly, ct = masks['poly_positive_support'], masks['CT']
    unknown = masks['poly_topology_unknown'] | masks['retired_CT_underlying_unknown']
    aa = cv2.warpPerspective(masks['AA'].astype('uint8'), np.array(mos['matrix']),
                             (w, h), flags=cv2.INTER_NEAREST) > 0
    _, labels, stats, centers = cv2.connectedComponentsWithStats(ct.astype('uint8'))
    _, plabels = cv2.connectedComponents(poly.astype('uint8'))
    gate_labels = {gate: int(plabels[sy, sx]) for gate, (sx, sy) in zip(
        ['V3_G1', 'V3_G2'], repair['gate_seed_pair_xy_poly_crop'], strict=True)}
    if 0 in gate_labels.values() or len(set(gate_labels.values())) != 2:
        raise ValueError('Approved V3 gate separation lost')
    zones = {z['id']: z for z in prior['zones']}
    validate_reviews(spec['reviews'], prior['contacts'], zones)
    reviews = {(r['roi_id'], r['ct_component_id']): r for r in spec['reviews']}
    records, groups = [], {}
    for old in prior['contacts']:
        cid = old['ct_component_id']
        if not np.array_equal(stats[cid, :4], old['bbox_poly_crop_xywh']) or (
            not np.allclose(centers[cid], old['center_poly_crop_xy'])
        ):
            raise ValueError('CT component identity changed')
        row = dict(**reviews[(old['roi_id'], cid)],
                   center_poly_crop_xy=old['center_poly_crop_xy'],
                   center_poly_native_xy=(centers[cid] + panel['source_crop_xywh'][:2]).tolist(),
                   bbox_poly_crop_xywh=stats[cid, :4].tolist(),
                   metrics=support_evidence(labels == cid, poly, unknown, aa,
                                            plabels, gate_labels),
                   terminal_assignment_approval='not_human_reviewed')
        group = row['roi_id']
        if group == 'V3':
            group = row['candidate_terminal'] if row['candidate_terminal'] in {
                'V3_A', 'V3_M', 'V3_B'} else 'V3_gate'
        row['evidence_page'] = f'{group}.png'
        records.append(row)
        groups.setdefault(group, []).append(row)
    misses = []
    for point in spec['miss_candidates']:
        cx, cy = point['xy_poly_crop']
        radius = spec['miss_probe_radius_px']
        rectangle = ct[cy-radius:cy+radius+1, cx-radius:cx+radius+1]
        misses.append(dict(**point, center_poly_native_xy=[cx+panel['source_crop_xywh'][0],
                                                         cy+panel['source_crop_xywh'][1]],
                           existing_CT_support_in_probe_px=int(rectangle.sum()),
                           mask_modified=False, electrical_connection='unknown'))
    out.mkdir(parents=True)
    for name, contacts in groups.items():
        contacts.sort(key=lambda c: c['center_poly_crop_xy'][0]
                      if name in {'V3_A', 'V3_M', 'V3_B'} else c['ct_component_id'])
        for index, contact in enumerate(contacts):
            contact['evidence_tile_xywh'] = [index % 5*320, index // 5*190, 320, 190]
        write_image(out / f'{name}.png', render_page(raw, poly, unknown, labels, contacts,
                                                     64 if name in {'V1', 'V2'} else 40))
    for point in misses:
        cx, cy = point['xy_poly_crop']
        crop = raw[cy-22:cy+22, cx-22:cx+22].copy()
        cv2.drawMarker(crop, (22, 22), (0, 0, 255), cv2.MARKER_CROSS, 4, 1)
        write_image(out / f"{point['id']}.png", cv2.resize(
            crop, (352, 352), interpolation=cv2.INTER_NEAREST))
    exceptions = [('C311: likely screen texture', [273, 305]),
                  ('P1: CT missing support?', [159, 268]),
                  ('P2: CT missing support?', [306, 270]),
                  ('P3: narrow CT or screen stripe?', [954, 466])]
    sheet = np.full((520, 960, 3), 25, np.uint8)
    for index, (title, (cx, cy)) in enumerate(exceptions):
        patch = raw[cy-32:cy+32, cx-32:cx+32].copy()
        overlay = patch.copy()
        pm, um = poly[cy-32:cy+32, cx-32:cx+32], unknown[cy-32:cy+32, cx-32:cx+32]
        overlay[pm] = (.45*overlay[pm] + .55*np.array([240, 80, 20])).astype('uint8')
        overlay[um] = (0, 140, 255)
        contours, _ = cv2.findContours(ct[cy-32:cy+32, cx-32:cx+32].astype('uint8'),
                                       cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, (0, 255, 255), 1)
        top, left = index//2*260, index % 2*480
        for offset, im in [(0, patch), (240, overlay)]:
            cv2.drawMarker(im, (32, 32), (0, 0, 255), cv2.MARKER_CROSS, 4, 1)
            sheet[top+30:top+254, left+offset:left+offset+224] = cv2.resize(
                im, (224, 224), interpolation=cv2.INTER_NEAREST)
        cv2.putText(sheet, title, (left+3, top+20), cv2.FONT_HERSHEY_SIMPLEX,
                    .48, (255, 255, 255), 1, cv2.LINE_AA)
    write_image(out / 'exceptions.png', sheet)
    result = dict(status='AI_review_candidates', unit='poly_source_px', runtime_ai_used=False,
                  source_spec=spec, spec_sha256=digest(spec_file),
                  code_sha256=digest(Path(__file__)),
                  records=records, miss_candidates=misses,
                  review_counts=dict(Counter(r['association_review'] for r in records)),
                  inherited_human_constraints=topology['constraints'],
                  V3_gate_domain_labels=gate_labels, netlist_generated=False)
    write_json(out / 'manifest.json', result)
    fields = ['roi_id', 'ct_component_id', 'candidate_terminal', 'association_review',
              'visual_detection', 'multiplicity_review', 'center_poly_native_xy', 'visual_note']
    with (out / 'per-contact.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    lines = ['# 逐CT原图与端子归属核对', '',
             'AI逐项复核90个既有检测分量，不是90个已确认物理触点。运行时仅校验和导出。',
             '采用用户批准的修正版poly及两类未知域；M共享、G1/G2局部不连继承人工裁决。',
             f"检查状态：{result['review_counts']}。具体CT归属均尚未获人工批准。",
             '每格左=原图，右=修正版poly蓝色/未知橙色/该CT分量黄轮廓，红十字为质心。',
             '坐标保留原生px；缩略图按最近邻放大，仅供核对。', '',
             'AA来自冻结跨层配准，交叠计数仅诊断，不是接触或本地配准准确性的证明。', '',
             '## 需优先裁决', '',
             '- C311：原图更像栅内拍屏纹理，疑似CT误报；不分配端子，不改mask。',
             '- P1/P2：V1左侧与V2右侧上方亮斑无CT支持；漏检候选。',
             '- P3：V3下排(954,466)窄亮斑无支持；CT与屏幕条纹难分，保持未知。',
             f"- {sum(r['multiplicity_review'] == 'multiple_bright_lobes' for r in records)}"
             '个分量含多亮斑，包括C266/C375/C438及部分V3横向合并亮斑，不能按一个CT计数。',
             f"- {result['review_counts'].get('candidate_detection_uncertain', 0)}"
             '个窄/弱亮斑检测保留存在性歧义；另'
             f"{result['review_counts'].get('excluded', 0)}个分量质心在MOS ROI外，不强行归属。", '',
             '![异常汇总：左原图/右支持图](exceptions.png)', '',
             '## 端子候选清单', '', '| 端子 | 分量ID（均为候选） |', '| --- | --- |']
    for zone in zones:
        ids = [f"C{r['ct_component_id']}" for r in records if r['candidate_terminal'] == zone]
        lines.append(f"| {zone} | {', '.join(ids)} |")
    for name in groups:
        lines += ['', f'## {name}', '', f'![{name}]({name}.png)']
    lines += ['', '## 无支持亮斑候选', '']
    for point in misses:
        lines += [f"{point['id']}：{point['note']}", '', f"![{point['id']}]({point['id']}.png)", '']
    lines += ['逐项视觉判断及坐标见per-contact.csv；mask交叠/未知域计数见manifest.json。',
              '未知poly不能作为无poly证据；CT与两个栅mask相交也不合并栅。',
              '本轮不补CT、不删误报、不改批准mask、不引入金属层或确认网表。']
    (out / 'report.md').write_text('\n'.join(lines)+'\n')
    return result
