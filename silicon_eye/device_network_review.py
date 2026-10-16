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
from .network_reviews import apply_network_reviews
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


def draw_graph(devices: list, networks: list, colors: dict,
               title='LOCAL DEVICE / M1 NETWORK CANDIDATES') -> np.ndarray:
    image = np.full((max(780, 170+len(networks)*90), 1100, 3), 28, np.uint8)
    _text(image, title, (30, 30), scale=.7)
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


def annotate_native_observations(image: np.ndarray, view: dict, network_ids: set) -> np.ndarray:
    """Draw AI observation windows on a copy, using source-native coordinates only."""
    x, y, w, h = view['crop_xywh_native']
    if (image is None or min(x, y) < 0 or min(w, h) <= 0 or
            x+w > image.shape[1] or y+h > image.shape[0]):
        raise ValueError('Invalid critical native view')
    marked = image[y:y+h, x:x+w].copy()
    seen = set()
    for obs in view.get('observations', []):
        if obs['id'] in seen:
            raise ValueError('Duplicate observation ID')
        seen.add(obs['id'])
        if obs['status'] != 'AI_visual_candidate':
            raise ValueError('Observation windows cannot confirm topology')
        if not set(obs['suggested_net_ids']) <= network_ids:
            raise ValueError('Observation references unknown network')
        if view.get('correspondence_status') == 'unregistered' and obs['suggested_net_ids']:
            raise ValueError('Unregistered cross-layer observations must stay unassigned')
        bx, by, bw, bh = obs['xywh_native']
        if min(bw, bh) <= 0 or bx < x or by < y or bx+bw > x+w or by+bh > y+h:
            raise ValueError('Observation outside native view')
        a, b = (bx-x, by-y), (bx+bw-x-1, by+bh-y-1)
        cv2.rectangle(marked, a, b, (0, 210, 255), 1)
        _text(marked, obs['id'], (max(2, a[0]), max(18, a[1]-5)),
              (0, 210, 255), .45)
    return marked


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
    review_records = []
    for binding in spec.get('review_records', []):
        record = json.loads(_verified(root, binding).read_text())
        for source in record.get('sources', {}).values():
            if isinstance(source, dict) and 'path' in source and 'sha256' in source:
                _verified(root, source)
        review_records.append(record)
    state = apply_network_reviews(spec['networks'], review_records)
    networks = state['networks']
    devices = device_connections(terminal_spec['devices'], terminal_spec['zones'], networks)
    resolved = {f['id'] for f in state['facts'] if f['status'] == 'human_confirmed'}
    questions = [q for q in spec['critical_questions'] if q['id'] not in resolved]
    dimensions = {d['device']: geometry_proxy(aa, masks['poly_positive_support'], masks['CT'],
                                              d['xywh_poly_crop'], d['source_drain_axis'])
                  for d in spec['dimension_windows']}
    palette = [(220, 80, 220), (70, 230, 230), (70, 150, 255), (220, 220, 60),
               (60, 230, 60), (255, 150, 70), (170, 90, 255)]
    colors = {n['id']: palette[i % len(palette)] for i, n in enumerate(networks)}
    overlay = aligned.copy()
    network_records = []
    for net in networks:
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
                                    electrical_approval='reviewed_relation_only'
                                    if net['status'].startswith('human_confirmed')
                                    else 'not_human_reviewed'))
    zone_net = {t: n['id'] for n in networks for t in n['terminals']}
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
    title = 'LOCAL DEVICE / M1-M2 REVIEWED RELATIONS' if review_records else (
        'LOCAL DEVICE / M1 NETWORK CANDIDATES')
    write_image(out / 'device-network-graph.png', draw_graph(devices, networks, colors, title))
    if review_records:
        from .local_schematic import render_schematic

        render_schematic(out, devices, dimensions, state['unresolved_relations'])
    critical_evidence = []
    for view in spec.get('critical_views', []):
        image = cv2.imread(str(paths[view['source']]))
        x, y, rw, rh = view['crop_xywh_native']
        if image is None or min(x, y) < 0 or min(rw, rh) <= 0 or (
            x+rw > image.shape[1] or y+rh > image.shape[0]
        ):
            raise ValueError('Invalid critical native view')
        filename = view['id']+'.png'
        write_image(out / filename, image[y:y+rh, x:x+rw])
        display = filename
        if rw <= 300:
            display = view['id']+'-zoom.png'
            write_image(out / display, cv2.resize(image[y:y+rh, x:x+rw], (rw*4, rh*4),
                                                 interpolation=cv2.INTER_NEAREST))
        observation_artifact = {}
        if view.get('observations'):
            marked = annotate_native_observations(image, view, set(zone_net.values()))
            annotated = view['id']+'-observations.png'
            write_image(out / annotated, marked)
            observation_artifact = dict(observation_artifact=annotated,
                                        observation_sha256=digest(out / annotated))
        critical_evidence.append(dict(**view, **observation_artifact,
                                      artifact=filename, display=display,
                                      sha256=digest(out / filename),
                                      resampled=False))
    boundary_review = spec.get('boundary_review')
    if boundary_review:
        prior = json.loads(paths['prior_network_manifest'].read_text())
        old_nets = {n['id']: sorted(n['terminals']) for n in prior['networks']}
        new_nets = {n['id']: sorted(n['terminals']) for n in network_records}
        if devices != prior['devices'] or old_nets != new_nets:
            raise ValueError('Boundary observation review cannot change prior topology')
        write_json(out / 'network-boundary.json', dict(
            analysis=boundary_review, observations=critical_evidence,
            devices=devices, networks=network_records, topology_changed=False,
            cross_layer_correspondence='unknown', runtime_ai_used=False))
    result = dict(status='device_network_candidates', runtime_ai_used=False,
                  source_spec=spec, spec_sha256=digest(spec_file),
                  code_sha256=digest(Path(__file__)),
                  registration=dict(source=spec['inputs']['registration'],
                                    matrix_m1_native_to_poly_native=matrix.tolist(),
                                    validation_metrics=reg['validation_metrics'],
                                    acceptance=reg['acceptance']),
                  devices=devices, networks=network_records, dimension_proxies=dimensions,
                  critical_questions=questions,
                  applied_review_records=spec.get('review_records', []),
                  review_facts=state['facts'], unresolved_relations=state['unresolved_relations'],
                  superseded_hypotheses=state['superseded_hypotheses'],
                  critical_path_evidence=critical_evidence, boundary_review=boundary_review,
                  helper_code_sha256={n: digest(Path(__file__).with_name(n)) for n in
                                      ['network_reviews.py', 'local_schematic.py']},
                  inherited_human_constraints=topology['constraints'],
                  gate_identity='G1/G2 retain distinct physical identities; review layers explicit',
                  confirmed_netlist_generated=False, unit='poly_source_px')
    write_json(out / 'manifest.json', result)
    write_json(out / 'local-netlist.json', dict(
        schema_version=1, kind='partial_structural_netlist_not_simulation_ready',
        devices=devices, networks=network_records, facts=state['facts'],
        unresolved_relations=state['unresolved_relations'], dimension_proxies=dimensions,
        reviews=spec.get('review_records', []),
        limitations=['bulk and MOS polarity unknown', 'image geometry is not physical W/L',
                     'M2 precise via path not validated']))
    gm_joined = any(f['id'] == 'V3_gate_to_shared_diffusion' for f in state['facts'])
    gm_note = ('公共栅与共享扩散区已由用户确认同网N3_GM；具体金属/过孔路径未自动验证。'
               if gm_joined else 'N3_G与N3_M关系仍未知，分列不代表证明断开。')
    lines = ['# 四MOS局部电路与M1/M2关系（部分确认）' if review_records
             else '# 四MOS局部M1网络候选', '',
             '以器件/接触区域为单位追踪连接，不要求逐个CT批准。AI看图给出路线，脚本仅校验与绘图。',
             '彩线是AI路线示意，不是自动分割的金属边界；CT mask未修改。',
             'G1/G2保持两个物理poly栅；人工裁决可确认经M2同网，不能改写成poly端部相连。', '',
             '## 尚待裁决的关键关系', '']
    for q in questions:
        lines += [f"- {q['question']}"]
    if not questions:
        lines += ['当前列出的关键连接裁决已应用；其余蓝色映射仍为候选，体端及类型未知。']
    if review_records:
        lines += ['', '## 无需Virtuoso的局部电路示意', '',
                  'SVG可在浏览器打开、缩放；PNG可直接查看。每个MOS独立绘制四个端子。',
                  '同名网络代表连接；绿色为已确认关系，蓝色虚线为候选，黄色为未知。',
                  'A/B不指派源漏方向；通用MOS符号无极性箭头，体端明确未知。',
                  gm_note + '不输出可仿真的SPICE。', '',
                  '[打开矢量图](local-schematic.svg)', '',
                  '![局部电路示意](local-schematic.png)', '',
                  '已应用的人工裁决：两栅至少经M2同网、M共用、局部poly端部不连、V1/V2局部M1断开。',
                  '历史AI整体候选保留来源；当前连接由绑定的人工裁决生成。']
    if boundary_review:
        lines += ['', '## V3外侧网络与局部边界候选', '',
                  '下述为原图观察及复核说明，确认范围按表注明；观察框不是材料分割边界。',
                  'M1原生像素使用各自坐标；M2仅为未配准搜索区，不能按相近位置自动接线。', '',
                  '| 网络/对象 | 当前观察 | 替代解释与未知 |', '| --- | --- | --- |']
        for item in boundary_review['findings']:
            lines.append(f"| {item['target']} | {item['observation']} | "
                         f"{item['uncertainty']} |")
        lines += ['', boundary_review['next_gate'], '']
    lines += ['', '![器件网络候选图](device-network-graph.png)', '',
              '## 器件—网络表', '', '| MOS | 栅G | 扩散端A | 扩散端B | 体端 |',
              '| --- | --- | --- | --- | --- |']
    for d in devices:
        lines.append(f"| {d['id']} | {d['G']} | {d['diffusion_A']} | {d['diffusion_B']} | 未知 |")
    if gm_joined:
        lines += ['', '## V3局部拓扑归纳', '',
                  'V3_Q1的G/B、V3_Q2的G/A同属N3_GM；两器件及两物理栅仍独立。',
                  '当前V3有N3_A、N3_GM、N3_B三个局部信号网络名；',
                  'N3_A/N3_B端子映射仍为候选，三者外部去向及是否远处相连未确认。',
                  '未确定源漏与体端，不能直接命名为二极管连接、指定功能或生成仿真模型。']
    lines += ['', '人工确认关系单独记录，其余映射为候选；不指定源漏极性或NMOS/PMOS。',
              '不同局部网络名不证明远处断开。' + gm_note,
              '', '## 网络依据与歧义', '',
              '| 网络 | 接触组 | 原图判断 | 尚未确定 |', '| --- | --- | --- | --- |']
    for n in networks:
        lines.append(f"| {n['id']} | {', '.join(n['terminals'])} | "
                     f"{n['visual_basis']} | {n['uncertainty']} |")
    lines += ['', '## 原图与路线', '']
    for roi in spec['rois']:
        lines += [f"![{roi['id']}]({roi['id']}-networks.png)", '']
    if critical_evidence:
        lines += ['## 关键M1/M2路径核查', '',
                  gm_note,
                  '自动M2相似变换得到近零缩放的退化结果，已拒绝；过孔阵列身份也尚未独立确认。',
                  '没有用残差0冒充对齐通过，也没有将搜索范围内任意M2线认作已匹配路径。',
                  '两栅至少经M2同网的人工事实继续生效；物理poly仍为两条栅。',
                  '所需证据是相关落点之间是否存在连通路径，不是每一个CT的数量。', '']
        for view in critical_evidence:
            if view.get('observations'):
                lines += [f"### {view['id']}：AI观察窗口", '',
                          f"![观察标号]({view['observation_artifact']})", '',
                          '| 标号 | 原图窗口xywh（px） | 建议归属 | 判断/未知 |',
                          '| --- | --- | --- | --- |']
                for obs in view['observations']:
                    names = ', '.join(obs['suggested_net_ids']) or '未分配'
                    lines.append(f"| {obs['id']} | {obs['xywh_native']} | {names} | "
                                 f"{obs['note']} |")
                lines += ['']
            lines += [view['description'], '', f"[原生像素文件]({view['artifact']})；"
                      '小图展示版本仅最近邻放大，不增加图像信息。', '',
                      f"![{view['id']}]({view['display']})", '']
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
              '原图、已批准材料与未知域不变；M2人工判断不等于精确M2配准或过孔路径已验证。',
              '下一关：只追踪尚未解决的关键关系，不重新请求已确认关系或逐CT验收。']
    (out / 'report.md').write_text('\n'.join(lines)+'\n')
    return result
