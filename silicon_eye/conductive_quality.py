"""Separate candidate delivery checks from source, array and coverage acceptance.

Used by conductive_workflow; consumes declared observations and actual reviews,
not pixels or a process DRC deck. Unknown measurements remain unqualified.
"""
from __future__ import annotations

import numpy as np


def _turns(points):
    points = np.asarray(points, dtype=float)
    if (points.ndim != 2 or points.shape[1] != 2 or len(points) < 2
            or not np.isfinite(points).all()):
        raise ValueError('Invalid source/design shape path')
    directions = []
    for delta in np.diff(points, axis=0):
        axis = int(np.argmax(np.abs(delta)))
        if abs(delta[axis]) < 1e-6 or abs(delta[axis]) < 2 * abs(delta[1-axis]):
            return None  # Oblique/degenerate observations need a source review.
        direction = (axis, int(np.sign(delta[axis])))
        if not directions or directions[-1] != direction:
            directions.append(direction)
    turns = []
    for (a, sa), (b, sb) in zip(directions, directions[1:], strict=False):
        if a == b:
            return None  # A reversal is not a qualified right-angle turn.
        turns.append(sa * sb * (1 if a == 0 else -1))
    return turns


def source_shape_audit(features_by_layer):
    """Preserve signed turns, allowing camera skew and collinear simplification.

This stack assumes no mirrored source frames. It is a path consistency check,
not registration, pixel segmentation, width verification or physical truth.
"""
    checks = []
    for features in features_by_layer.values():
        for feature in features:
            native, design = (_turns(feature[k]) for k in ('native_path', 'design_path'))
            status = ('NOT_EVALUATED' if native is None or design is None else
                      'PASS' if native == design else 'FAIL')
            checks.append(dict(id=feature['id'], native_turns=native, design_turns=design,
                               status=status))
    return dict(status='FAIL' if any(c['status'] == 'FAIL' for c in checks) else
                'PARTIAL' if any(c['status'] == 'NOT_EVALUATED' for c in checks) else 'PASS',
                checks=checks, scope='declared_path_handedness_not_photo_geometry_acceptance')


def inherited_group_facts(inputs, baseline, model):
    """Keep known group counts through proxy adapters using exact member identities."""
    current = {c['id']: c for c in model['reviewed_local_connections']}
    facts = []
    for edge in baseline.get('reviewed_local_connections', []):
        if edge['id'] not in current:
            continue
        for group in baseline.get('confirmed_local_via_groups', []):
            if (not group.get('member_ids')
                    or set(edge.get('via_object_ids', [])) != set(group['member_ids'])
                    or edge['via_layer'] != group['layer']):
                continue
            review = inputs.human(group['human_review'])
            decision = review['decisions']
            if (decision['array_rows'] != group['rows']
                    or decision['array_columns'] != group['columns']
                    or decision['local_group_cut_count'] != group['cut_count']
                    or group['rows'] * group['columns'] != group['cut_count']
                    or decision['evidence_frame'] != group['source_frame']
                    or decision['visible_via_layer'] != group['layer']):
                raise ValueError('Inherited group fact contradicts human count/shape')
            for frame, photo in model['source_photos'].items():
                if frame == group['source_frame'] and review['sources'][frame.upper()] != photo:
                    raise ValueError('Inherited group fact belongs to a different source photo')
            facts.append(dict(interface_id=edge['id'],
                              support_id=current[edge['id']].get('support_id', edge['id']),
                              group_id=group['id'], rows=group['rows'], columns=group['columns'],
                              cut_count=group['cut_count'], human_review=group['human_review'],
                              geometry_ported=False))
    return facts


def quality_summary(model, sample, shape_audit, legacy_report=None):
    """Report denominators and gaps without inferring an unobserved full inventory."""
    legacy_report = legacy_report or {}
    features = [f for group in sample['features_by_layer'].values() for f in group]
    rows = []
    represented = {c.get('support_id', c['id']): c
                   for c in model['reviewed_local_connections']}
    facts = {f['support_id']: f for f in model.get('inherited_group_facts', [])}
    claims = {c['id']: c for c in sample['interfaces']}
    for layer in ('V1', 'V2'):
        for obj in model['objects_by_layer'][layer]:
            claim = claims[obj['id']]
            approved = represented.get(obj['id'])
            cuts = obj.get('candidate_cut_bounds', [])
            fact = facts.get(obj['id'])
            rows.append(dict(
                id=obj['id'], layer=layer,
                lower_metal_id=approved.get('lower_metal_id') if approved else
                claim.get('lower_metal_id'),
                upper_metal_id=approved.get('upper_metal_id') if approved else
                claim.get('upper_metal_id'),
                carrier_status='HUMAN_CONFIRMED_SCOPED' if approved else
                'REJECTED_CANDIDATE' if model.get('review_decisions', {}).get(
                    obj['id'], {}).get('connection_confirmed') is False else 'PENDING',
                human_cut_count=fact['cut_count'] if fact else
                approved.get('physical_cut_count') if approved else None,
                inherited_group_fact=fact,
                representation='EXPLICIT_DESIGN_ARRAY' if cuts else 'GROUP_SUPPORT_PROXY',
                design_cut_count=len(cuts) if cuts else None,
                full_group_design_enclosure='CHECKED' if cuts else 'NOT_EVALUATED',
                source_array_geometry='NOT_QUALIFIED',
                native_group_window_recorded='native_bounds' in claim,
                geometry_acceptance='CANDIDATE_NOT_HUMAN_ACCEPTED',
            ))
    proxy_ids = [r['id'] for r in rows if r['representation'] == 'GROUP_SUPPORT_PROXY']
    endpoints = [dict(id=f['id'], end_states=f.get('end_states'),
                      status='NOT_QUALIFIED') for f in features]
    gaps = [
        '原生导体宽度、端部完整性及规则几何与照片的尺寸对应未验收。',
        '孔组阵列的真实尺寸/间距/排列尚未通过来源几何验收。',
        '未建立全部可见导体/接口清单，不能给出照片覆盖率或整网完成率。',
        '当前预算是相对设计像素，未建立真实工艺尺寸和PDK DRC资格。',
    ]
    if proxy_ids:
        gaps.insert(0, '仍有孔组代理框；单框包围检查不证明整组孔能被承载。')
    if model.get('pending_interface_ids'):
        gaps.insert(0, '存在待裁决承载，不能作为已确认连接采用。')
    return dict(
        status='REVIEWABLE_WITH_QUALITY_GAPS',
        execution_checks='PASS',
        source_path_shape=shape_audit,
        represented_interface_count=len(rows),
        reviewed_represented_interface_count=sum(
            r['carrier_status'] == 'HUMAN_CONFIRMED_SCOPED' for r in rows),
        interface_geometry=rows,
        proxy_interface_ids=proxy_ids,
        explicit_design_array_count=sum(bool(r['design_cut_count']) for r in rows),
        source_qualified_array_count=0,
        metal_geometry_acceptance='CANDIDATE_NOT_HUMAN_ACCEPTED',
        coverage=dict(status='PARTIAL', represented_metal_count=len(features),
                      known_review_inventory_count=legacy_report.get('input_interface_union_count'),
                      represented_review_inventory_count=legacy_report.get('interfaces_represented'),
                      visible_photo_inventory_complete=False, photo_coverage_fraction=None,
                      endpoints=endpoints),
        error_budget=dict(unit='relative_design_px_not_PDK',
                          photo_to_design_metric_budget='NOT_ESTABLISHED'),
        readiness=dict(review_package=True, canonical_geometry_adoption=False,
                       complete_network_export=False, unrestricted_skill_release=False),
        blocking_adoption_reasons=gaps,
    )
