"""Inspect local CT/terminal hypotheses: annotate terminals --spec CASE -o NEW_DIR.

Requires the frozen local MOS and material evidence; windows are AI hypotheses.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from .registration_audit import digest, write_image, write_json


def _inside(point: list, box: list) -> bool:
    x, y, w, h = box
    return x <= point[0] < x+w and y <= point[1] < y+h


def _intersects(a: list, b: list) -> bool:
    return (max(a[0], b[0]) < min(a[0]+a[2], b[0]+b[2]) and
            max(a[1], b[1]) < min(a[1]+a[3], b[1]+b[3]))


def assign_contact(center: list, bbox: list, roi: list, zones: list) -> dict:
    """A geometric match proposes an association, never an electrical connection."""
    hit = [z['id'] for z in zones if _inside(center, z['xywh_poly_crop'])]
    touched = [z['id'] for z in zones if _intersects(bbox, z['xywh_poly_crop'])]
    if not _inside(center, roi):
        status = 'cropped_boundary_unknown'
    elif len(hit) > 1 or len(touched) > 1:
        status = 'conflict'
    elif len(hit) == 1:
        status = 'candidate'
    else:
        status = 'unknown'
    return dict(status=status, candidate_zone=hit[0] if status == 'candidate' else None,
                center_in_windows=hit, bbox_touches_windows=touched,
                basis='CT centroid in AI inspection window; not electrical proof')


def _verified(root: Path, binding: dict) -> Path:
    path = root / binding['path']
    if digest(path) != binding['sha256']:
        raise ValueError(f"Changed evidence: {binding['path']}")
    return path


def run_terminal_review(spec_path: str, output: str) -> dict:
    spec_file = Path(spec_path).resolve()
    root = spec_file.parent.parent
    spec = json.loads(spec_file.read_text())
    out = Path(output)
    if out.exists():
        raise ValueError('Output directory already exists')
    paths = {key: _verified(root, value) for key, value in spec['inputs'].items()}
    approval = json.loads(paths['structure_approval'].read_text())
    approved_regions = {r['roi_id']: r for r in approval['reviewed_regions']}
    if _verified(root, approval['source_manifest']) != paths['mos_manifest']:
        raise ValueError('MOS approval source mismatch')
    _verified(root, approval['source_report'])
    for region in approval['reviewed_regions']:
        _verified(root, region['artifact'])
    material_approval = json.loads(_verified(root, approval['material_approval']).read_text())
    if digest(paths['material_manifest']) != material_approval['source_manifest_sha256']:
        raise ValueError('Material approval mismatch')
    for key, layer in [('ct_mask', 'CT'), ('poly_mask', 'poly')]:
        if digest(paths[key]) != material_approval['layers'][layer]['mask_sha256']:
            raise ValueError(f'Unapproved mask: {layer}')
    mos = json.loads(paths['mos_manifest'].read_text())
    for binding in mos['source_spec']['inputs'].values():
        _verified(root, binding)
    sample = json.loads((root / mos['source_spec']['inputs']['sample']['path']).read_text())
    panel = sample['panels']['poly']
    source = Path(panel['source_path'])
    if digest(source) != panel['source_sha256']:
        raise ValueError('Changed source photo')
    raw = cv2.imread(str(paths['raw_poly']))
    x, y, w, h = panel['source_crop_xywh']
    if raw is None or not np.array_equal(raw, cv2.imread(str(source))[y:y+h, x:x+w]):
        raise ValueError('Raw crop differs from source')
    ct = cv2.imread(str(paths['ct_mask']), 0)
    poly = cv2.imread(str(paths['poly_mask']), 0)
    if ct is None or poly is None or ct.shape != (h, w) or poly.shape != (h, w):
        raise ValueError('Invalid mask dimensions')
    _, labels, stats, centers = cv2.connectedComponentsWithStats((ct > 0).astype('uint8'))
    approved_ids = {i for r in approval['reviewed_regions'] for i in r['device_ids']}
    if len(approved_ids) != approval['approved_local_mos_count']:
        raise ValueError('Inconsistent human-approved device count')
    if {d['id'] for d in spec['devices']} != approved_ids:
        raise ValueError('Device IDs differ from human-approved structure')
    zones = {z['id']: z for z in spec['zones']}
    if len(zones) != len(spec['zones']):
        raise ValueError('Duplicate inspection window ID')
    for z in zones.values():
        x, y, zw, zh = z['xywh_poly_crop']
        if min(x, y) < 0 or min(zw, zh) <= 0 or x+zw > w or y+zh > h:
            raise ValueError('Inspection window outside crop')
        if not set(z['devices']) <= approved_ids:
            raise ValueError('Unknown device in inspection window')
    for d in spec['devices']:
        for terminal in [d['gate'], *d['diffusion_terminals']]:
            if terminal not in zones or d['id'] not in zones[terminal]['devices']:
                raise ValueError('Device/window membership mismatch')
    contacts = []
    annotated = []
    bright_spots = [dict(s) for s in spec['unmasked_bright_spot_review']]
    for candidate in mos['candidates']:
        roi_id = candidate['id']
        roi = candidate['xywh_poly_crop']
        roi_zones = [z for z in zones.values() if z['id'].startswith(roi_id+'_')]
        x, y, rw, rh = roi
        zoom = 4
        raw_crop = cv2.resize(raw[y:y+rh, x:x+rw], (rw*zoom, rh*zoom),
                              interpolation=cv2.INTER_NEAREST)
        image = raw_crop.copy()
        for z in roi_zones:
            zx, zy, zw, zh = z['xywh_poly_crop']
            color = (220, 80, 220) if z['kind'] == 'gate' else (240, 200, 40)
            if len(z['devices']) > 1:
                color = (40, 230, 40)
            p1 = ((zx-x)*zoom, (zy-y)*zoom)
            p2 = ((zx+zw-x)*zoom-1, (zy+zh-y)*zoom-1)
            cv2.rectangle(image, p1, p2, color, 2)
            cv2.putText(image, z['id'], (p1[0], max(14, p1[1]-4)),
                        cv2.FONT_HERSHEY_SIMPLEX, .45, color, 1, cv2.LINE_AA)
        for old in candidate['contacts']:
            cid = old['ct_component_id']
            if not np.array_equal(stats[cid, :4], old['bbox_poly_crop_xywh']) or (
                not np.allclose(centers[cid], old['center_poly_crop_xy'])
            ):
                raise ValueError('CT component labels changed')
            decision = assign_contact(centers[cid].tolist(), stats[cid, :4].tolist(),
                                      roi, roi_zones)
            contacts.append(dict(roi_id=roi_id, **old, **decision,
                                 center_poly_native_xy=(centers[cid] +
                                                        panel['source_crop_xywh'][:2]).tolist(),
                                 electrical_connection='unknown'))
            cx, cy = np.rint((centers[cid] - [x, y])*zoom).astype(int)
            color = (255, 255, 255) if decision['status'] == 'candidate' else (0, 130, 255)
            cv2.circle(image, (cx, cy), 6, color, 1, cv2.LINE_AA)
            cv2.putText(image, str(cid), (cx-11, cy-9), cv2.FONT_HERSHEY_SIMPLEX,
                        .35, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(image, str(cid), (cx-11, cy-9), cv2.FONT_HERSHEY_SIMPLEX,
                        .35, color, 1, cv2.LINE_AA)
        for spot in bright_spots:
            if spot['roi_id'] == roi_id:
                sx, sy = spot['xy_poly_crop']
                spot['mask_present_at_point'] = bool(ct[sy, sx])
                cv2.drawMarker(image, ((sx-x)*zoom, (sy-y)*zoom), (0, 100, 255),
                               cv2.MARKER_TILTED_CROSS, 16, 2)
        sheet = np.vstack([raw_crop, np.full((32, rw*zoom, 3), 25, np.uint8), image])
        cv2.putText(sheet, f'{roi_id}: raw above / AI windows + CT IDs below',
                    (5, rh*zoom+21), cv2.FONT_HERSHEY_SIMPLEX,
                    .38 if rw < 100 else .6, (255, 255, 255), 1, cv2.LINE_AA)
        annotated.append((roi_id, sheet))
    # A common poly component is evidence for review, not authority to merge gates.
    _, plabels = cv2.connectedComponents((poly > 0).astype('uint8'))
    gate_labels = {}
    for name in ['V3_G1', 'V3_G2']:
        x, y, zw, zh = zones[name]['xywh_poly_crop']
        gate_labels[name] = sorted(int(i) for i in np.unique(plabels[y:y+zh, x:x+zw]) if i)
    common = sorted(set(gate_labels['V3_G1']) & set(gate_labels['V3_G2']))
    result = dict(status='candidate', unit='poly_source_px', runtime_ai_used=False,
                  device_count=approval['approved_local_mos_count'],
                  structure_status='human_approved_local_only',
                  devices=[dict(**d, terminal_mapping_status='candidate',
                                source_drain_polarity='unknown', body_terminal='unknown')
                           for d in spec['devices']],
                  zones=list(zones.values()), contacts=contacts,
                  assignment_status_counts=dict(Counter(c['status'] for c in contacts)),
                  hypotheses=spec['hypotheses'],
                  common_poly_component_evidence=dict(gate_labels=gate_labels, common=common,
                                                      gate_connectivity='unknown_not_merged'),
                  bright_spot_review=bright_spots,
                  human_shared_diffusion=approved_regions['V3']['shared_diffusion'],
                  source_spec=spec, spec_sha256=digest(spec_file),
                  code_sha256=digest(Path(__file__)),
                  confirmed_netlist_generated=False)
    out.mkdir(parents=True)
    for name, image in annotated:
        write_image(out / f'{name}-terminals.png', image)
    write_json(out / 'manifest.json', result)
    graph = ['flowchart LR']
    for d in spec['devices']:
        graph.append(f"  {d['gate']} -. candidate_gate .-> {d['id']}[{d['id']}]")
        for sd in d['diffusion_terminals']:
            graph.append(f"  {d['id']} -. candidate_diffusion .-> {sd}")
    graph += ['  V3_G1 -. same_gate_unknown .- V3_G2',
              '  style V3_M fill:#b7e4b2']
    (out / 'connections.mmd').write_text('\n'.join(graph)+'\n')
    with (out / 'contacts.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['roi', 'ct_component', 'poly_native_x', 'poly_native_y',
                         'window_candidate', 'status', 'electrical_connection'])
        for c in contacts:
            writer.writerow([c['roi_id'], c['ct_component_id'], *c['center_poly_native_xy'],
                             c['candidate_zone'], c['status'], 'unknown'])
    lines = ['# 局部端子与CT归属候选', '',
             '用户确认四个MOS及V3共享扩散关系；本轮仅提出端子位置和CT归属候选。',
             '上图原始poly裁剪，下图4倍最近邻放大标号；坐标仍按原生px记录。',
             '紫框=栅接触检查窗，青框=扩散接触检查窗，绿框=共用扩散区位置候选。',
             '窗口不是材料边界。白圈数字为CT mask连通分量ID；橙色为未分配或边界分量。',
             '橙色叉为AI目视亮斑漏检候选，不是新增确认CT，批准mask不变。', '',
             'V1/V2：G为上端栅接触候选，A/B为左右扩散接触候选，源漏极性未知。',
             'V3：Q1为上栅，Q2为下栅；A为上行、M为中间共用行、B为下行扩散候选。',
             '中间行的共用位置是AI假设；用户批准的是存在共享关系。',
             f'G1/G2检查窗内共同poly分量：{common}；不能据此确认两栅电气连接。',
             'V2中部/底部CT分量311及裁剪边缘分量保留unknown，不强行归属。', '',
             f"CT分量窗口检查统计：{result['assignment_status_counts']}。", '',
             '逐项坐标见contacts.csv，窗口/器件关系/哈希见manifest.json。', '']
    lines += ['## 四个MOS的端子位置候选', '',
              '| MOS | 栅接触窗口 | 未定源漏端子窗口 |', '| --- | --- | --- |']
    for d in spec['devices']:
        lines.append(f"| {d['id']} | {d['gate']} | {' / '.join(d['diffusion_terminals'])} |")
    lines += ['', '所有映射均待复核；V3_M为共享扩散区的位置假设。', '',
              '```mermaid', *graph, '```', '']
    for name, _ in annotated:
        lines += [f'## {name}', '', f'![{name}]({name}-terminals.png)', '']
    lines += ['下一关：复核V3中间行是否共用扩散区、G1/G2是否同栅，以及V1/V2侧边CT归属。',
              '本阶段未接入金属层，不生成确认网表；NMOS/PMOS、体端及W/L仍未知。']
    (out / 'report.md').write_text('\n'.join(lines)+'\n')
    return result
