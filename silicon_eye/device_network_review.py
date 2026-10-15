"""Review device-level M1 routes: annotate networks --spec CASE -o NEW_DIR.

AI supplies route hypotheses; scripts map coordinates, measure image geometry and
render evidence. Requires approved local material evidence and local registration.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from .local_terminal_review import _verified
from .registration_audit import digest, write_image, write_json


def poly_to_m1(points: list, matrix: np.ndarray, origin: list) -> list:
    """Invert M1-native -> poly-native before mapping poly-crop route guides."""
    native = np.asarray(points, float) + np.asarray(origin)
    homogeneous = np.column_stack([native, np.ones(len(native))])
    mapped = homogeneous @ np.linalg.inv(matrix).T
    return (mapped[:, :2] / mapped[:, 2:]).tolist()


def device_connections(devices: list, zones: list, networks: list) -> list:
    """Keep physical terminal identities even if a candidate M1 net ties gates."""
    mapping = {}
    ids = [n['id'] for n in networks]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate network IDs')
    for net in networks:
        for terminal in net['terminals']:
            if terminal in mapping:
                raise ValueError('Terminal assigned to multiple candidate networks')
            mapping[terminal] = net['id']
    if set(mapping) != {z['id'] for z in zones}:
        raise ValueError('Missing or extra physical terminal groups')
    return [dict(id=d['id'], physical_gate=d['gate'], G=mapping[d['gate']],
                 diffusion_A=mapping[d['diffusion_terminals'][0]],
                 diffusion_B=mapping[d['diffusion_terminals'][1]], bulk='unknown',
                 source_drain_polarity='unknown', device_type='MOS_polarity_unknown',
                 connection_status='candidate') for d in devices]


def geometry_proxy(aa: np.ndarray, poly: np.ndarray, ct: np.ndarray,
                   box: list, axis: str) -> dict:
    """Report support spans, not calibrated physical or electrical W/L."""
    x, y, w, h = box
    if axis not in {'x', 'y'} or min(x, y) < 0 or min(w, h) <= 0 or (
        x+w > poly.shape[1] or y+h > poly.shape[0]
    ):
        raise ValueError('Invalid dimension window/axis')
    support = (aa & poly & ~ct)[y:y+h, x:x+w]
    oriented = support if axis == 'x' else support.T
    lengths, positions = [], []
    for index, line in enumerate(oriented):
        indices = np.flatnonzero(line)
        if not len(indices):
            continue
        runs = np.split(indices, np.where(np.diff(indices) > 1)[0]+1)
        longest = max(len(r) for r in runs)
        if longest >= 3:
            positions.append(index)
            lengths.append(longest)
    if not lengths:
        return dict(status='unknown_no_visible_overlap', unit='poly_source_px')
    return dict(status='visible_support_geometry_proxy_not_physical_WL', unit='poly_source_px',
                W_span_px=max(positions)-min(positions)+1,
                L_run_median_px=float(np.median(lengths)),
                L_run_p10_p90_px=np.percentile(lengths, [10, 90]).tolist(),
                sampling_lines=len(lengths), source_drain_axis=axis,
                window_clipped=bool(support[0].any() or support[-1].any() or
                                    support[:, 0].any() or support[:, -1].any()),
                physical_scale='unknown', accuracy='not_independently_measured')


def _text(image, text, point, color=(255, 255, 255), scale=.45):
    cv2.putText(image, text, point, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 3,
                cv2.LINE_AA)
    cv2.putText(image, text, point, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1,
                cv2.LINE_AA)


def draw_graph(devices: list, networks: list, colors: dict) -> np.ndarray:
    image = np.full((780, 1100, 3), 28, np.uint8)
    _text(image, 'LOCAL DEVICE / M1 NETWORK CANDIDATES', (30, 30), scale=.7)
    _text(image, 'A/B = unoriented diffusion terminals; Bulk = unknown', (30, 58))
    _text(image, 'Crossing lines are not junctions. Physical gates remain distinct.', (30, 80))
    net_y = {n['id']: 125+i*90 for i, n in enumerate(networks)}
    for i, d in enumerate(devices):
        y = 180+i*150
        destinations = {}
        for port in ['G', 'diffusion_A', 'diffusion_B']:
            destinations.setdefault(d[port], []).append(port.replace('diffusion_', ''))
        for index, (net, ports) in enumerate(destinations.items()):
            start = (300, y-24+index*24)
            end = (770, net_y[net])
            cv2.line(image, start, end, colors[net], 2, cv2.LINE_AA)
            _text(image, ','.join(ports), (start[0]+5, start[1]-5), colors[net])
        cv2.rectangle(image, (35, y-42), (295, y+42), (95, 95, 95), -1)
        _text(image, d['id'], (55, y-10), scale=.6)
        _text(image, 'Bulk ? / MOS type ?', (55, y+20))
    for net, y in net_y.items():
        cv2.circle(image, (770, y), 6, colors[net], -1)
        cv2.rectangle(image, (785, y-22), (1060, y+25), colors[net], 1)
        _text(image, net, (800, y+5), colors[net], .6)
    return image


def run_network_review(spec_path: str, output: str) -> dict:
    spec_file = Path(spec_path).resolve()
    root, out = spec_file.parent.parent, Path(output)
    if out.exists():
        raise ValueError('Output directory already exists')
    spec = json.loads(spec_file.read_text())
    paths = {k: _verified(root, v) for k, v in spec['inputs'].items()}
    approval = json.loads(paths['baseline_approval'].read_text())
    if approval['review_status'] != 'approved_for_this_local_view':
        raise ValueError('Missing approved local baseline')
    repair = json.loads(_verified(root, approval['source_manifest']).read_text())
    for binding in repair['source_spec']['inputs'].values():
        _verified(root, binding)
    if _verified(root, approval['prior_topology_review']) != paths['topology_review']:
        raise ValueError('Topology review differs from approved repair')
    topology = json.loads(paths['topology_review'].read_text())
    reg = json.loads(paths['registration'].read_text())
    if reg['matrix_direction'] != 'target_native_to_reference_native':
        raise ValueError('Incorrect registration direction')
    if not reg['numeric_budget_met']:
        raise ValueError('Macro registration budget failed')
    for side, path in reg['source_paths'].items():
        if digest(Path(path)) != reg['source_sha256'][side]:
            raise ValueError('Changed registration photo')
    if digest(paths['m1_source']) != reg['source_sha256']['target']:
        raise ValueError('M1 source mismatch')
    mos = json.loads(paths['mos_manifest'].read_text())
    if mos['source_spec']['inputs']['approval']['sha256'] != (
        repair['source_spec']['inputs']['material_approval']['sha256']
    ):
        raise ValueError('MOS evidence differs from approved material lineage')
    material_paths = {k: _verified(root, approval['baseline'][k]) for k in [
        'AA', 'CT', 'poly_positive_support', 'poly_topology_unknown',
        'retired_CT_underlying_unknown']}
    images = {k: cv2.imread(str(p), 0) for k, p in material_paths.items()}
    if any(image is None for image in images.values()):
        raise ValueError('Unreadable material masks')
    masks = {k: image > 0 for k, image in images.items()}
    ox, oy, w, h = spec['canvas_xywh_poly_native']
    if any(m.shape != (h, w) for m in masks.values()):
        raise ValueError('Incompatible material dimensions')
    raw_poly_path = _verified(root, repair['source_spec']['inputs']['raw_poly'])
    raw_poly = cv2.imread(str(raw_poly_path))
    native_poly = cv2.imread(reg['source_paths']['reference'])
    if not np.array_equal(raw_poly, native_poly[oy:oy+h, ox:ox+w]):
        raise ValueError('Canvas does not match the source poly crop')
    matrix = np.array(reg['matrix_native'])
    shift = np.eye(3)
    shift[:2, 2] = [-ox, -oy]
    local_matrix = shift @ matrix
    native_m1 = cv2.imread(str(paths['m1_source']))
    aligned = cv2.warpPerspective(native_m1, local_matrix, (w, h))
    valid = cv2.warpPerspective(np.ones(native_m1.shape[:2], np.uint8), local_matrix,
                                (w, h), flags=cv2.INTER_NEAREST) > 0
    aa = cv2.warpPerspective(masks['AA'].astype('uint8'), np.array(mos['matrix']),
                             (w, h), flags=cv2.INTER_NEAREST) > 0
    terminal_spec = json.loads(paths['terminal_spec'].read_text())
    devices = device_connections(terminal_spec['devices'], terminal_spec['zones'], spec['networks'])
    dimensions = {d['device']: geometry_proxy(aa, masks['poly_positive_support'], masks['CT'],
                                              d['xywh_poly_crop'], d['source_drain_axis'])
                  for d in spec['dimension_windows']}
    palette = [(220, 80, 220), (70, 230, 230), (70, 150, 255), (220, 220, 60),
               (60, 230, 60), (255, 150, 70), (170, 90, 255)]
    colors = {n['id']: palette[i % len(palette)] for i, n in enumerate(spec['networks'])}
    overlay = aligned.copy()
    network_records = []
    for net in spec['networks']:
        native_traces = []
        for trace in net['traces_xy_poly_crop']:
            points = np.rint(trace).astype(int)
            if np.any(points < 0) or np.any(points[:, 0] >= w) or np.any(points[:, 1] >= h):
                raise ValueError('Route guide outside source canvas')
            if not valid[points[:, 1], points[:, 0]].all():
                raise ValueError('Route guide outside M1 coverage')
            cv2.polylines(overlay, [points], False, colors[net['id']], 2, cv2.LINE_AA)
            native_traces.append(poly_to_m1(trace, matrix, [ox, oy]))
        network_records.append(dict(**net, traces_xy_m1_native=native_traces,
                                    electrical_approval='not_human_reviewed'))
    zone_net = {t: n['id'] for n in spec['networks'] for t in n['terminals']}
    for zone in terminal_spec['zones']:
        x, y, zw, zh = zone['xywh_poly_crop']
        color = colors[zone_net[zone['id']]]
        cv2.rectangle(overlay, (x, y), (x+zw-1, y+zh-1), color, 1)
        _text(overlay, zone['id'], (x, max(13, y-5)), color, .38)
    for roi in spec['rois']:
        x, y, rw, rh = roi['xywh_poly_crop']
        if min(x, y) < 0 or x+rw > w or y+rh > h or min(rw, rh) <= 0:
            raise ValueError('ROI outside source crop')
        if not valid[y:y+rh, x:x+rw].all():
            raise ValueError('Incomplete M1 coverage of device ROI')
    out.mkdir(parents=True)
    write_image(out / 'm1-aligned.png', aligned)
    write_image(out / 'valid-coverage.png', valid.astype('uint8')*255)
    write_image(out / 'network-overview.png', overlay)
    for roi in spec['rois']:
        x, y, rw, rh = roi['xywh_poly_crop']
        region = np.s_[y:y+rh, x:x+rw]
        panels = []
        for title, im in [('POLY / CONTACT REGIONS', raw_poly), ('ALIGNED M1', aligned),
                           ('M1 + AI NETWORK ROUTE GUIDES', overlay)]:
            panel = cv2.resize(im[region], (rw*3, rh*3), interpolation=cv2.INTER_NEAREST)
            header = np.full((30, rw*3, 3), 25, np.uint8)
            _text(header, title, (5, 20), scale=.5)
            panels.extend([header, panel])
        write_image(out / f"{roi['id']}-networks.png", np.vstack(panels))
    write_image(out / 'device-network-graph.png', draw_graph(devices, spec['networks'], colors))
    result = dict(status='device_network_candidates', runtime_ai_used=False,
                  source_spec=spec, spec_sha256=digest(spec_file),
                  code_sha256=digest(Path(__file__)),
                  registration=dict(source=spec['inputs']['registration'],
                                    matrix_m1_native_to_poly_native=matrix.tolist(),
                                    validation_metrics=reg['validation_metrics'],
                                    acceptance=reg['acceptance']),
                  devices=devices, networks=network_records, dimension_proxies=dimensions,
                  critical_questions=spec['critical_questions'],
                  inherited_human_constraints=topology['constraints'],
                  gate_identity='G1/G2 distinct poly gates; candidate shared net only through M1',
                  confirmed_netlist_generated=False, unit='poly_source_px')
    write_json(out / 'manifest.json', result)
    lines = ['# 四MOS局部M1网络候选', '',
             '以器件/接触区域为单位追踪连接，不要求逐个CT批准。AI看图给出路线，脚本仅校验与绘图。',
             '彩线是AI路线示意，不是自动分割的金属边界；CT mask未修改。',
             'G1/G2仍是两个独立poly栅；若同网，本轮假设由M1跨接，不能写成poly端部相连。', '',
             '## 优先复核两处会改变网络的关系', '']
    for q in spec['critical_questions']:
        lines += [f"- {q['question']}"]
    lines += ['', '![器件网络候选图](device-network-graph.png)', '',
              '## 器件—网络表', '', '| MOS | 栅G | 扩散端A | 扩散端B | 体端 |',
              '| --- | --- | --- | --- | --- |']
    for d in devices:
        lines.append(f"| {d['id']} | {d['G']} | {d['diffusion_A']} | {d['diffusion_B']} | 未知 |")
    lines += ['', '所有新M1连接都是候选，不指定源漏极性或NMOS/PMOS；不同局部网络名不证明远处断开。',
              '', '## 网络依据与歧义', '',
              '| 网络 | 接触组 | 原图判断 | 尚未确定 |', '| --- | --- | --- | --- |']
    for n in spec['networks']:
        lines.append(f"| {n['id']} | {', '.join(n['terminals'])} | "
                     f"{n['visual_basis']} | {n['uncertainty']} |")
    lines += ['', '## 原图与路线', '']
    for roi in spec['rois']:
        lines += [f"![{roi['id']}]({roi['id']}-networks.png)", '']
    lines += ['## 图像几何尺寸参考（px，非真实W/L）', '',
              'W为AA/poly可见交叠跨度；L为横截面最长连续支持段的中位数及P10–P90。',
              '这些分位数只描述分割形状差异，非测量置信区间；CT遮挡、边界和跨层配准会影响数值。',
              '窗口截断时跨度只是窗口内结果，不可作完整器件尺寸。未知域不填补，不换算μm。', '',
              '| MOS | W跨度 | L段中位数 | L段P10–P90 | 窗口截断 |',
              '| --- | --- | --- | --- | --- |']
    for name, d in dimensions.items():
        lines.append(f"| {name} | {d.get('W_span_px', '?')} | {d.get('L_run_median_px', '?')} | "
                     f"{d.get('L_run_p10_p90_px', '?')} | {d.get('window_clipped', '?')} |")
    metrics = reg['validation_metrics']
    lines += ['', '## 配准与范围', '',
              f"独立竖环四角诊断：P95={metrics['p95_px']:.2f}px，最大={metrics['max_px']:.2f}px；",
              '满足预设宏观8/12px预算，结构对应仍为AI候选，同一环四角并非四个独立结构。',
              '配准acceptance仍unknown；没有据此宣称微小接触准确性。拟合及检查证据见绑定registration目录。',
              '原图、已批准材料与未知域不变；尚未使用M2/注入层确认外部网络和体端。',
              '下一关：仅复核上述两条关键M1关系，随后向外追踪网络及检查体端。']
    (out / 'report.md').write_text('\n'.join(lines)+'\n')
    return result
