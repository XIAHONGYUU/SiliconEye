"""Inspect upper-metal routes without changing the reviewed electrical topology.

Run: python -m silicon_eye.upper_routing_review --spec CASE -o NEW_DIR
Requires existing local review evidence and the project's OpenCV/Pillow environment.
AI supplies feature identities/route hypotheses; scripts measure and export diagnostics.
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

import cv2
import numpy as np

from .device_network_review import run_network_review
from .local_schematic import Canvas
from .local_terminal_review import _verified
from .registration_audit import digest, write_image, write_json


def structure_identities(review: dict, views: list, devices: list) -> list:
    """Consume identity approval separately from electrical connectivity approval."""
    if review.get('actor') != 'human':
        raise ValueError('Identity confirmation requires a human record')
    facts = []
    for decision in review['decisions']:
        if (decision['id'] != 'M2_P2_V3_identity' or
                decision['status'] != 'human_confirmed' or decision['source_layer'] != 'm2' or
                decision.get('connectivity_changes') != [] or
                decision.get('terminal_to_segment_mapping') != 'unknown'):
            raise ValueError('Unsupported identity scope or attempted electrical change')
        ids = decision['corresponding_devices']
        if set(ids) != {'V3_Q1', 'V3_Q2'} or not set(ids) <= {d['id'] for d in devices}:
            raise ValueError('Identity references unexpected devices')
        matches = [o for v in views if v['source'] == 'm2_source'
                   for o in v.get('observations', [])
                   if o['id'] == decision['observation_id']]
        if not matches or any(o['xywh_native'] != decision['observation_window_xywh_native']
                              for o in matches):
            raise ValueError('Reviewed identity window differs from current evidence')
        facts.append(deepcopy(decision))
    if not facts:
        raise ValueError('Missing structure identity decision')
    return facts


def bright_center(image: np.ndarray, box: list, quantile: float) -> dict:
    """Measure a declared landmark, retaining the AI-selected ROI as a limitation."""
    x, y, w, h = box
    if min(x, y) < 0 or min(w, h) <= 0 or x+w > image.shape[1] or y+h > image.shape[0]:
        raise ValueError('Landmark window outside source')
    if not 0 < quantile < 1:
        raise ValueError('Invalid weight quantile')
    gray = cv2.cvtColor(image[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY).astype(float)
    gray = cv2.GaussianBlur(gray, (5, 5), 1)
    if np.ptp(gray) < 40:
        raise ValueError('Landmark lacks usable contrast')
    threshold = float(np.quantile(gray, quantile))
    weights = np.maximum(gray-threshold, 0)
    if weights.sum() <= 0:
        raise ValueError('Landmark has no bright support')
    yy, xx = np.indices(gray.shape)
    center = [x+float((weights*xx).sum()/weights.sum()),
              y+float((weights*yy).sum()/weights.sum())]
    return dict(xy_native=center, threshold=threshold, weight_quantile=quantile,
                window_xywh_native=box, status='diagnostic_not_physical_truth')


def translation_diagnostic(fit: list, check: list) -> dict:
    """Fit only declared fit landmarks; never optimize against held-out structures."""
    if not fit or not check or {p['id'] for p in fit} & {p['id'] for p in check}:
        raise ValueError('Fit/check need disjoint nonempty structure identities')
    delta = np.mean([np.array(p['reference_xy'])-p['source_xy'] for p in fit], axis=0)
    if delta.shape != (2,) or not np.isfinite(delta).all():
        raise ValueError('Nonfinite translation')
    matrix = np.eye(3)
    matrix[:2, 2] = delta
    held = [dict(id=p['id'], residual_px=float(np.linalg.norm(
        np.array(p['source_xy'])+delta-p['reference_xy']))) for p in check]
    return dict(matrix_source_to_reference=matrix.tolist(), held_out=held,
                acceptance='unknown', usage='macro_search_only_not_terminal_registration')


def hierarchy_image(out: Path) -> None:
    c = Canvas(1600, 820)
    c.text('LOCAL CIRCUIT / UPPER-METAL REVIEW', (30, 18), size=28)
    c.text('Electrical nets, physical feature identity and spatial candidates are distinct.',
           (30, 62), size=20)
    def box(x, y, w, h, color):
        for a, b in [((x,y),(x+w,y)), ((x+w,y),(x+w,y+h)),
                     ((x+w,y+h),(x,y+h)), ((x,y+h),(x,y))]:
            c.line(a, b, color)
    box(30, 125, 685, 340, '#63e7b2')
    c.text('DEVICE GROUP: V3', (55, 145), '#63e7b2', 25)
    for i, text in enumerate([
        '2 MOS / 2 physical gates', 'Q1: G = B = N3_GM', 'Q2: G = A = N3_GM',
        'Outer diffusion labels: N3_A, N3_B (candidate)',
        'Bulk / N-P / S-D / physical W-L: unknown',
        'No circuit function assigned from shape alone']):
        c.text(text, (55, 198+i*38), size=20)
    box(770, 125, 795, 340, '#70b8ff')
    c.text('PHYSICAL ROUTING CONTEXT', (795, 145), '#70b8ff', 25)
    for i, text in enumerate([
        'M2 P2: identity with V3 reviewed by human',
        'M3 H1 / H2: horizontal bundles (multiple tracks)',
        'M3 S3: short feature; M2 P3 identity candidate',
        'M4 V4: long vertical strip; network unassigned',
        'P2 upper end near H1 lower edge: route candidate',
        'No upper-layer feature merged into netlist']):
        c.text(text, (795, 198+i*38), size=19)
    c.text('PATH HYPOTHESES / EVIDENCE LEVEL', (30, 510), size=25)
    for i, (text, color) in enumerate([
        ('V3 <-> M2 P2: group identity confirmed; per-terminal mapping unknown.', '#63e7b2'),
        ('P2 upper end -> H1 left-going tracks: candidate; exact track/net unresolved.', '#ffcb6b'),
        ('M2 P3 <-> M3 S3: held-out feature candidate; this does not prove a via.', '#ffcb6b'),
        ('M3 S3 <-> M4 V4: spatial candidate; M3/M4 transform not validated.', '#ffcb6b'),
        ('P2 -> P3 and all new electrical joins: UNKNOWN. No simulation implied.', '#ffcb6b')]):
        c.text(text, (35, 563+i*41), color, 20)
    (out/'circuit-hierarchy.svg').write_text('\n'.join(c.parts+['</svg>'])+'\n')
    c.image.save(out/'circuit-hierarchy.png')


def run(spec_path: str, output: str) -> dict:
    spec_file = Path(spec_path).resolve()
    root, out = spec_file.parent.parent, Path(output)
    spec = json.loads(spec_file.read_text())
    paths = {k: _verified(root, b) for k, b in spec['inputs'].items()}
    prior = json.loads(paths['prior_network_manifest'].read_text())
    facts = []
    for binding in spec['identity_reviews']:
        review = json.loads(_verified(root, binding).read_text())
        for source in review['sources'].values():
            _verified(root, source)
        facts += structure_identities(review, spec['critical_views'], prior['devices'])
    setting = spec['macro_diagnostic']
    images = {key: cv2.imread(str(paths[setting[key]])) for key in ['source', 'reference']}
    if any(image is None for image in images.values()):
        raise ValueError('Missing diagnostic source image')
    diagnostics = []
    for q in setting['weight_quantiles']:
        pairs = {}
        for role in ['fit', 'check']:
            pairs[role] = []
            for p in setting[role]:
                a = bright_center(images['source'], p['source_xywh'], q)
                b = bright_center(images['reference'], p['reference_xywh'], q)
                pairs[role].append(dict(id=p['id'], source_xy=a['xy_native'],
                                        reference_xy=b['xy_native'],
                                        source_measurement=a, reference_measurement=b))
        diagnostics.append(dict(quantile=q, landmarks=pairs,
                                **translation_diagnostic(pairs['fit'], pairs['check'])))
    primary = next(d for d in diagnostics if d['quantile'] == setting['primary_quantile'])
    result = run_network_review(str(spec_file), str(out))
    if result['devices'] != prior['devices'] or result['networks'] != prior['networks']:
        raise ValueError('Upper routing review changed electrical topology')
    hierarchy_image(out)
    landmark_files = []
    for role in ['fit', 'check']:
        for p in setting[role]:
            for side in ['source', 'reference']:
                bx, by, bw, bh = p[side+'_xywh']
                filename = f"macro-{role}-{p['id']}-{side}-native.png"
                write_image(out/filename, images[side][by:by+bh, bx:bx+bw])
                landmark_files.append(dict(role=role, structure_id=p['id'], side=side,
                    source=spec['inputs'][setting[side]], crop_xywh_native=[bx,by,bw,bh],
                    artifact=filename, sha256=digest(out/filename)))
    # Only a macro search box: do not use this projection to assign a terminal or via.
    decision = facts[0]
    x, y, w, h = decision['observation_window_xywh_native']
    delta = np.array(primary['matrix_source_to_reference'])[:2, 2]
    px, py = np.rint([x, y]+delta).astype(int)
    image = images['reference'][1480:1730, 2600:2900].copy()
    if not (2600 <= px < px+w <= 2900 and 1480 <= py < py+h <= 1730):
        raise ValueError('Projected P2 search box outside declared diagnostic crop')
    write_image(out/'M3-P2-search-native.png', image)
    cv2.rectangle(image, (px-2600, py-1480), (px+w-2600, py+h-1480), (0,210,255), 1)
    cv2.putText(image, 'P2 projected / candidate', (5, 242),
                cv2.FONT_HERSHEY_SIMPLEX, .5, (0,210,255), 1)
    write_image(out/'M3-P2-search-diagnostic.png', image)
    result.update(structure_identity_facts=facts, identity_review_bindings=spec['identity_reviews'],
                  upper_macro_diagnostics=diagnostics,
                  upper_routing_code_sha256=digest(Path(__file__)))
    result['upper_landmark_evidence'] = landmark_files
    result['P2_projection_diagnostic'] = dict(
        source_window_m2=decision['observation_window_xywh_native'],
        projected_window_m3=[int(px), int(py), w, h],
        display_crop_m3=[2600,1480,300,250],
        status='macro_candidate_search_not_accepted_alignment',
        source_binding=spec['inputs']['m3_source'])
    result['upper_artifact_sha256'] = {f: digest(out/f) for f in [
        'circuit-hierarchy.svg', 'circuit-hierarchy.png',
        'M3-P2-search-native.png', 'M3-P2-search-diagnostic.png']}
    write_json(out/'manifest.json', result)
    write_json(out/'upper-routing.json', dict(structure_identity_facts=facts,
        diagnostics=diagnostics, topology_changed=False, formal_registration_acceptance='unknown',
        route_hypotheses=[dict(id='P2_upper_H1', status='AI_visual_candidate',
                              exact_track='unknown', terminal_net='unknown'),
                          dict(id='P3_S3_V4', status='spatial_identity_candidate_only',
                               connection_to_V3='unknown')]))
    note = ['# 上层走线与局部电路层次检查', '',
            'P2对应V3两MOS已按绑定反馈自动消费；此处不重复请求身份确认。',
            '原四MOS和所有电气网络与前轮逐项一致。新增的是结构对应/走线候选。', '',
            '![层次总览](circuit-hierarchy.png)', '',
            '## M2到M3局部宏观诊断', '',
            '上方阵列用于拟合平移，P3/S3短段只作留出检查；都是AI结构对应候选。',
            '一个留出结构不足以证明端子级精度、全图几何或过孔连通；未正式验收。', '',
            '| 亮支持分位 | dx | dy | 留出误差px |', '| --- | --- | --- | --- |']
    for d in diagnostics:
        a = np.array(d['matrix_source_to_reference'])
        note.append(f"| {d['quantile']} | {a[0,2]:.2f} | {a[1,2]:.2f} | "
                    f"{d['held_out'][0]['residual_px']:.2f} |")
    for f in landmark_files:
        note += ['', f"{f['role']} / {f['structure_id']} / {f['side']}：",
                 f"![原生结构窗口]({f['artifact']})"]
    note += ['', '## 新的路线候选', '',
             'P2上端的诊断投影位于M3上方横向走线束下缘附近；可能向左引出。',
             '误差和邻近多条走线使准确轨道仍不确定；尚不能指派N3_A/N3_GM/N3_B。',
             '以下黄框是AI候选平移的搜索窗口，不是确认对齐或金属边界。', '',
             '![P2在M3的搜索投影](M3-P2-search-diagnostic.png)', '',
             'M3短段S3与M2-P3为结构同源候选；M4长条V4在附近向下延续至所看窗口边缘。',
             '这只形成另一条候选检查链，不证明P3接到P2，也不证明M3/M4有过孔。',
             '不把横向束当作单一网络，不从宽度或走向命名VDD/VSS、偏置或电路功能。', '',
             '下一关优先核对P2上端是否进入H1并向左延伸，再确认其端子网络；',
             'S3/V4链暂保持独立。无需逐CT审批，不重复批准现有N3_GM。', '',
             '---', '', (out/'report.md').read_text()]
    (out/'report.md').write_text('\n'.join(note)+'\n')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', required=True)
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args()
    run(args.spec, args.output)


if __name__ == '__main__':
    main()
