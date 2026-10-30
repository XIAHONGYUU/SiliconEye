"""Review/revise metal and via candidates without manufacturing physical approvals.

Run: python -m silicon_eye.conductive_workflow --request REQUEST --output NEW_DIR
Requires project dependencies and AI-authored observations. No image recognition,
registration, canonical-layer adoption or automatic net extraction is performed.
"""
from __future__ import annotations

import argparse
import copy
import html
import json
import os
import tempfile
from pathlib import Path
from string import Template

import numpy as np
from PIL import Image, ImageChops
from shapely.geometry import LineString, Point, Polygon, box

from .conductive_layers import LAYERS, geometry, source_identity_audit, svg_layers
from .conductive_medium import prepare as prepare_medium
from .conductive_medium import source_order_audit
from .conductive_quality import inherited_group_facts, quality_summary, source_shape_audit
from .geometry_reconstruction import digest
from .metal_reconstruction import design_canvas_bounds, feature_polygon, geometry_audit
from .metal_via_pilot import group_via_budget, interface_audit, observed_array_audit, source_panels
from .metal_via_pilot import regular_group_cuts as via_cuts
from .review_package import Inputs, pointer


def signature(cut):
    """Physical correspondence stays separate from editable design geometry."""
    return {k: cut[k] for k in ('id', 'layer', 'layer_pair', 'source_frame', 'native_bounds',
                               'lower_metal_id', 'upper_metal_id')}


def preserve_via_centers(parent, model, ids):
    """Size-only revisions must not translate or reorder individual design sites."""
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate preserved via center ID')
    indices = [{o['id']: o for layer in ('V1', 'V2')
                for o in value['objects_by_layer'][layer]} for value in (parent, model)]
    checked = {}
    for key in ids:
        centers = []
        for index in indices:
            cuts = index.get(key, {}).get('candidate_cut_bounds')
            if not cuts:
                raise ValueError('Preserved via centers require an explicit array: ' + key)
            centers.append([[(a+c)/2, (b+d)/2] for a, b, c, d in cuts])
        if centers[0] != centers[1]:
            raise ValueError('Via center preservation failed: ' + key)
        checked[key] = dict(status='PASS', design_centers_xy=centers[1],
                            source_registration_verified=False)
    return checked


def carrier_correction(review, before, after):
    """A human correction may reassign carriers, never a photograph or layer pair."""
    correction = review.get('carrier_correction')
    if not correction:
        return False
    if correction != dict(before=signature(before), after=signature(after)):
        raise ValueError('Human carrier correction does not match before/after identities')
    fixed = ('id', 'layer', 'layer_pair', 'source_frame', 'native_bounds')
    if any(before[k] != after[k] for k in fixed):
        raise ValueError('Carrier correction cannot move source support or change layer')
    if all(before[k] == after[k] for k in ('lower_metal_id', 'upper_metal_id')):
        raise ValueError('Carrier correction must actually change a carrier')
    return True


def candidate_model(sample, snapshot):
    if sample['kind'] not in ('conductive_layer_observations',
                              'independent_conductive_transfer_evaluation'):
        raise ValueError('Unsupported observation sample')
    objects, shapes, audits = {k: [] for k in LAYERS}, {}, {}
    for layer, features in sample['features_by_layer'].items():
        if layer not in ('M1', 'M2', 'M3'):
            raise ValueError('Unsupported metal layer')
        audit, polygons = geometry_audit(features, sample['metal_budget'], sample['canvas_wh'],
                                        sample.get('canvas_bounds'))
        if audit['status'] != 'PASS':
            raise ValueError('Metal geometry gate failed: ' + layer)
        audits[layer] = audit
        for f, polygon in zip(features, polygons, strict=True):
            native = np.asarray(f['native_path'], dtype=float)
            if (f['id'] in shapes or f['source_frame'] != layer.lower()
                    or f['layer'] != layer or native.ndim != 2 or native.shape[1] != 2
                    or len(native) < 2 or not np.isfinite(native).all()
                    or (native < 0).any() or (native >= snapshot['source_wh']).any()):
                raise ValueError('Invalid metal source or duplicate ID')
            shapes[f['id']] = polygon
            objects[layer].append(dict(id=f['id'], layer=layer, kind='metal',
                                       role=f.get('role', 'context_only'),
                                       geometry=geometry(polygon), native_path=f['native_path'],
                                       source_frame=f['source_frame']))
    seen = set(shapes)
    for cut in sample['interfaces']:
        if cut['id'] in seen or cut.get('connection_confirmed') is not None:
            raise ValueError('Duplicate or pre-approved AI interface')
        seen.add(cut['id'])
        layer = cut['layer']
        if layer not in ('V1', 'V2') or cut['status'] != 'candidate':
            raise ValueError('Invalid interface candidate')
        lo, hi = cut['lower_metal_id'], cut['upper_metal_id']
        lower_layer, upper_layer = cut['layer_pair']
        layers = {f['id']: k for k, fs in sample['features_by_layer'].items() for f in fs}
        if layers.get(lo) != lower_layer or layers.get(hi) != upper_layer:
            raise ValueError('Interface carrier layer mismatch')
        native = np.asarray(cut['native_bounds'], dtype=float)
        if (native.shape != (4,) or not np.isfinite(native).all() or (native < 0).any()
                or (native[2:] <= native[:2]).any()
                or (native[2:] > snapshot['source_wh']).any()):
            raise ValueError('Invalid native via support')
        group_budget = group_via_budget(cut, sample['via_budget'])
        cuts = via_cuts(cut, group_budget)
        audit = interface_audit(cuts, shapes[lo], shapes[hi], group_budget,
                                layer_stack=(lower_layer, layer, upper_layer))
        if audit['status'] != 'PASS':
            raise ValueError('Via enclosure/spacing gate failed')
        audits[cut['id']] = audit
        if cut.get('cut_array_candidate'):
            audit['group_footprint_checked'] = True
        for existing in objects[layer]:
            a = box(*existing['design_support_bounds'])
            b = box(*cut['bounds'])
            if a.intersects(b) or a.distance(b) < sample['via_budget']['minimum_cut_gap_px']:
                raise ValueError('Via support gap failed')
        objects[layer].append(dict(
            id=cut['id'], layer=layer, kind='via_group_support_proxy',
            role='structural_hypothesis', geometry=geometry(box(*cut['bounds'])),
            design_support_bounds=cut['bounds'], source_frame=cut['source_frame'],
            source_photo=snapshot['source_photos'][cut['source_frame']],
            source_observation=dict(layer=layer, source_frame=cut['source_frame'],
                                    native_bounds=cut['native_bounds']), physical_cut_count=None,
        ))
        if cut.get('cut_array_candidate'):
            objects[layer][-1]['candidate_cut_bounds'] = [c['bounds'] for c in cuts]
    result = dict(objects_by_layer=objects, source_photos=snapshot['source_photos'],
                canvas_wh=sample['canvas_wh'], reviewed_local_connections=[],
                candidate_interfaces=copy.deepcopy(sample['interfaces']))
    if 'canvas_bounds' in sample:
        result['canvas_bounds'] = copy.deepcopy(sample['canvas_bounds'])
    return result, audits


def load_parent(inputs, ref):
    manifest = inputs.document(ref)
    directory = Path(ref['path']).parent
    for path, sha in manifest['artifacts'].items():
        inputs.read(dict(path=str(directory / path), sha256=sha))
    model = inputs.document(dict(path=str(directory / 'model.json'),
                                 sha256=manifest['artifacts']['model.json']))
    request = inputs.document(dict(path=str(directory / 'request.json'),
                                   sha256=manifest['artifacts']['request.json']))
    if model['sample'] != request['sample']:
        raise ValueError('Parent sample binding mismatch')
    return model, request


def canvas_extension_audit(inputs, request, previous, sample, parent_request):
    """Extend one viewport edge atomically; coordinate origin and old sites stay fixed."""
    evidence = inputs.document(request['canvas_extension_evidence'])
    before, after = previous['canvas_wh'], sample['canvas_wh']
    if (not isinstance(before, list) or not isinstance(after, list)
            or len(before) != 2 or len(after) != 2
            or any(type(v) is not int or v <= 0 for v in before + after)):
        raise ValueError('Canvas extension requires positive integer dimensions')
    old_bounds = design_canvas_bounds(before, previous.get('canvas_bounds'))
    new_bounds = design_canvas_bounds(after, sample.get('canvas_bounds'))
    bottom = new_bounds[:3] == old_bounds[:3] and new_bounds[3] > old_bounds[3]
    left = new_bounds[1:] == old_bounds[1:] and new_bounds[0] < old_bounds[0]
    direction = 'BOTTOM_ONLY' if bottom else 'LEFT_ONLY' if left else None
    if direction is None or any(type(v) is not int for v in old_bounds + new_bounds):
        raise ValueError('Canvas extension supports strictly bottom-only or left-only growth')
    if (evidence.get('kind') != 'conductive_canvas_extension'
            or evidence.get('actor') != 'AI' or not evidence.get('reason')
            or evidence.get('parent') != request['parent']
            or evidence.get('from_canvas_wh') != before or evidence.get('to_canvas_wh') != after
            or evidence.get('direction') != direction
            or evidence.get('origin_xy') != [0, 0] or evidence.get('scale_xy') != [1, 1]
            or evidence.get('translation_xy') != [0, 0]
            or evidence.get('geometry_human_approved') is not False):
        raise ValueError('Canvas extension evidence does not bind parent/extents/origin')
    signed = 'canvas_bounds' in previous or 'canvas_bounds' in sample
    if signed and (evidence.get('from_canvas_bounds') != old_bounds
                   or evidence.get('to_canvas_bounds') != new_bounds):
        raise ValueError('Signed canvas extension must bind both viewport bounds')
    expected = copy.deepcopy(previous)
    expected['canvas_wh'] = after
    if 'canvas_bounds' in sample:
        expected['canvas_bounds'] = sample['canvas_bounds']
    if sample != expected or any(request.get(k) for k in (
            'allowed_changed_ids', 'added_metal_ids', 'added_interface_ids', 'revision_evidence',
            'extension_evidence', 'interface_extension_evidence', 'reviews', 'resolved_limits')):
        raise ValueError('Canvas extension must preserve every non-canvas sample field')
    for key in ('frames', 'source_assets', 'source_panel_spec', 'deferred_unknown_ids',
                'questions'):
        if request.get(key) != parent_request.get(key):
            raise ValueError('Canvas extension cannot change source views or review scope')
    inputs.evidence(evidence)
    result = dict(status=direction + '_CANVAS_EXTENSION_PASS', evidence=request[
        'canvas_extension_evidence'], from_canvas_wh=before, to_canvas_wh=after,
        origin_xy=[0, 0], scale_xy=[1, 1], translation_xy=[0, 0],
        all_existing_records_exact=True, native_source_scope_changed=False,
        exact_geometry_human_approved=False)
    if signed:
        result.update(from_canvas_bounds=old_bounds, to_canvas_bounds=new_bounds,
                      design_origin_xy=[0, 0], coordinate_translation_xy=[0, 0])
    return result


def inventory_geometry_audit(inputs, sample, snapshot):
    """Account for declared fragments without certifying source exhaustiveness."""
    inventory = inputs.document(sample['visible_inventory'])
    if inventory.get('kind') != 'conductive_visible_inventory':
        raise ValueError('Expected a bound visible inventory')
    for frame, source in inventory['scope']['frames'].items():
        if source['photo'] != snapshot['source_photos'][frame]:
            raise ValueError('Geometry inventory belongs to another photograph')
        inputs.read(source['photo'])
    observations = {o['id']: o for o in inventory['metal_observations']}
    if len(observations) != len(inventory['metal_observations']):
        raise ValueError('Duplicate inventory observation')
    mappings = sample['inventory_geometry_mapping']
    supplements = sample.get('supplemental_visible_inventories', [])
    for ref in supplements:
        supplement = inputs.document(ref)
        if (supplement.get('kind') != 'conductive_visible_inventory_supplement'
                or supplement.get('actor') != 'AI' or not supplement.get('reason')
                or supplement.get('base_inventory') != sample['visible_inventory']
                or supplement.get('geometry_human_approved') is not False
                or not supplement.get('metal_observations')):
            raise ValueError('Invalid additive inventory supplement')
        inputs.evidence(supplement)
        for frame, scope in supplement['scope']['frames'].items():
            if scope['photo'] != snapshot['source_photos'].get(frame):
                raise ValueError('Supplement belongs to another photograph')
            bounds = np.asarray(scope['native_bounds'], dtype=float)
            if (bounds.shape != (4,) or not np.isfinite(bounds).all() or (bounds < 0).any()
                    or (bounds[2:] <= bounds[:2]).any()
                    or (bounds[2:] > snapshot['source_wh']).any()):
                raise ValueError('Invalid supplemental source scope')
            inputs.read(scope['photo'])
        for observation in supplement['metal_observations']:
            frame = observation['source_frame']
            bounds = supplement['scope']['frames'][frame]['native_bounds']
            path = np.asarray(observation['native_path'], dtype=float)
            if (observation['id'] in observations or observation.get('mapped_model_id')
                    or path.ndim != 2 or path.shape[1] != 2 or len(path) < 2
                    or not np.isfinite(path).all()
                    or any(not box(*bounds).covers(Point(x, y)) for x, y in path)):
                raise ValueError('Supplement reassigns an inventory identity or leaves scope')
            observations[observation['id']] = observation
        mappings = mappings + supplement['inventory_geometry_mapping']
    if (len(mappings) != len(observations)
            or {r['observation_id'] for r in mappings} != set(observations)
            or len({r['metal_id'] for r in mappings}) != len(mappings)):
        raise ValueError('Inventory geometry mapping incomplete or duplicated')
    features = {f['id']: f for fs in sample['features_by_layer'].values() for f in fs}
    if {r['metal_id'] for r in mappings} != set(features):
        raise ValueError('Geometry includes unlisted fragments or omits listed metal')
    partial = []
    for row in mappings:
        observation, feature = observations[row['observation_id']], features[row['metal_id']]
        if feature['source_frame'] != observation['source_frame']:
            raise ValueError('Inventory geometry frame mismatch')
        old = observation['mapped_model_id']
        if old:
            if feature['id'] != old:
                raise ValueError('Existing inventory correspondence reassigned')
            partial.append(old)
        elif feature['native_path'] != observation['native_path']:
            raise ValueError('New fragment moved away from inventory source path')
    result = dict(status='DECLARED_FRAGMENT_GEOMETRY_MAPPING_PASS',
                inventory=sample['visible_inventory'],
                listed_metal_observations=len(observations), mapped_geometry_count=len(mappings),
                unmapped_observation_ids=[],
                existing_partial_source_extent_ids=partial,
                unresolved_observation_ids=[r['id'] for r in inventory['unknown_observations']],
                boundary_source_observation_endpoints=sum(
                    e['state'] == 'exits_scope' for o in observations.values()
                    for e in o['endpoints']),
                complete_source_extent_geometry=False,
                physical_inventory_exhaustiveness='AI_SCANNED_NOT_INDEPENDENTLY_VERIFIED',
                actual_photo_coverage_fraction=None)
    if supplements:
        result['supplemental_visible_inventories'] = supplements
        result['scope_qualification'] = 'BASE_INVENTORY_PLUS_EXPLICIT_PARTIAL_SUPPLEMENTS'
    return result


def native_entry_review_source(inputs, sample, review, question, claim):
    """Bind a new lower-layer entry to its native question, never to macro alignment."""
    batch = inputs.human(review['sources']['batch_human_review'])
    regions = {r['id']: r for r in question['regions']}
    answers = [d for d in batch['decisions'] if d['interface_id'] == claim['id']]
    if len(answers) != 1 or review.get('region_id') not in regions:
        raise ValueError('Native entry answer is missing or duplicated')
    region, answer = regions[review['region_id']], answers[0]
    observations = inputs.document(question['observations'])
    working = inputs.document(observations['working_request'])
    source = inputs.document(working['sample'])
    snapshot = inputs.document(sample['snapshot'])
    features = {f['id']: f for fs in sample['features_by_layer'].values() for f in fs}
    lower = features[claim['lower_metal_id']]
    if (review.get('kind') != 'native_entry_confirmation'
            or batch.get('kind') != 'native_entry_human_judgment'
            or review.get('question_id') != question['question_id']
            or batch.get('question_id') != question['question_id']
            or review['statement'] != batch['statement']
            or batch['sources']['submitted_request'] != review['sources']['submitted_request']
            or review.get('observed_cut_count') is not None
            or batch.get('observed_cut_count') is not None
            or answer.get('physical_cut_count') is not None
            or answer.get('design_geometry_human_approved') is not False
            or answer.get('V1_present') is not True
            or answer.get('via_layer') != 'V1'
            or answer.get('connection_confirmed') is not True
            or review['decisions'].get('connection_confirmed') is not True
            or answer.get('region_id') != region['id']
            or answer.get('source_frame') != region['source_frame']
            or answer.get('native_bounds') != region['native_bounds']
            or claim['source_frame'] != region['source_frame'] or region['source_frame'] != 'm1'
            or claim['native_bounds'] != region['native_bounds']
            or claim['layer'] != 'V1' or claim['layer_pair'] != ['M1', 'M2']
            or answer.get('upper_metal_id') != region['upper_M2_candidate']
            or claim['upper_metal_id'] != region['upper_M2_candidate']
            or lower['source_frame'] != 'm1' or lower['layer'] != 'M1'
            or not any(box(*region['native_bounds']).covers(Point(x, y))
                       for x, y in lower['native_path'])
            or source['snapshot'] != sample['snapshot']
            or any(snapshot['source_photos'].get(k) != v
                   for k, v in observations['source_photos'].items())
            or not {'m1', 'm2'} <= set(observations['source_photos'])):
        raise ValueError('Native entry review exceeds the original identity/carrier scope')
    for ref in question['images'].values():
        inputs.read(ref)
    # The new M1 ID and geometry are an AI mapping of the approved source region.
    # Only the original M2 anchor is inherited from the submitted baseline.
    source['features_by_layer']['M1'] = [lower]
    source['interfaces'] = [signature(claim)]
    return source


def source_extent_audit(inputs, sample):
    """Bind new extent observations while keeping original native anchors intact."""
    evidence = inputs.document(sample['source_extent_evidence'])
    if (evidence.get('actor') != 'AI' or not evidence.get('reason')
            or evidence.get('geometry_human_approved') is not False
            or evidence.get('inventory') != sample.get('visible_inventory')):
        raise ValueError('Extent evidence must remain an AI candidate bound to the inventory')
    basis, _ = load_parent(inputs, evidence['basis_parent'])
    inventory = inputs.document(evidence['inventory'])
    if any(basis['source_photos'].get(frame) != source['photo']
           for frame, source in inventory['scope']['frames'].items()):
        raise ValueError('Extent basis belongs to another source photograph')
    observations = {o['mapped_model_id']:o for o in inventory['metal_observations']
                    if o['mapped_model_id']}
    features = {f['id']:f for fs in sample['features_by_layer'].values() for f in fs}
    old = {o['id']:o for objects in basis['objects_by_layer'].values() for o in objects}
    rows = evidence['metals']
    if len(rows) != len(observations) or {r['metal_id'] for r in rows} != set(observations):
        raise ValueError('Extent evidence omits or duplicates an existing metal')
    for row in rows:
        key = row['metal_id']
        feature, observation = features[key], observations[key]
        if (feature['native_path'] != old[key]['native_path']
                or row['native_anchor_path'] != feature['native_path']
                or row['visible_native_path'] != observation['native_path']
                or row['endpoint_states'] != [e['state'] for e in observation['endpoints']]
                or row['source_frame'] != feature['source_frame']
                or row['design_path'] != feature['design_path']):
            raise ValueError('Extent evidence source/path/endpoint binding mismatch')
        previous = Polygon(old[key]['geometry']['outer_xy'], old[key]['geometry']['holes_xy'])
        current = feature_polygon(feature)
        if row['preserve_old_footprint']:
            if not current.covers(previous):
                raise ValueError('Outward extent revision removed or failed to extend old metal')
        elif not row.get('reposition_reason'):
            raise ValueError('Endpoint reposition requires a separate source reason')
    return dict(status='SOURCE_EXTENT_CANDIDATES_BOUND', evidence=sample['source_extent_evidence'],
                metal_count=len(rows),
                source_boundary_endpoints=sum(s == 'exits_scope' for r in rows
                                              for s in r['endpoint_states']),
                original_native_anchors_preserved=True, geometry_human_approved=False,
                precise_extent_geometry_qualified=False, complete_network=False)


def local_part_source_audit(inputs, sample, snapshot):
    """Bind every declared local addition to native evidence without certifying pixels."""
    evidence = inputs.document(sample['local_part_source_evidence'])
    if (evidence.get('kind') != 'local_metal_part_source_evidence'
            or evidence.get('actor') != 'AI' or not evidence.get('reason')
            or evidence.get('geometry_human_approved') is not False):
        raise ValueError('Local parts need explicit AI source evidence')
    inputs.evidence(evidence)
    features = {f['id']: f for fs in sample['features_by_layer'].values() for f in fs}
    parts = {(f['id'], p['id']): p for f in features.values() for p in f.get('local_parts', [])}
    rows = evidence['parts']
    if (len(rows) != len(parts)
            or {(row['metal_id'], row['part_id']) for row in rows} != set(parts)):
        raise ValueError('Local part source ledger omits or duplicates geometry')
    for row in rows:
        feature, part = features[row['metal_id']], parts[row['metal_id'], row['part_id']]
        frame = feature['source_frame']
        if (row['source_frame'] != frame
                or row['source_photo'] != snapshot['source_photos'][frame]
                or row['design_bounds'] != part['bounds']
                or row.get('geometry_human_approved') is not False):
            raise ValueError('Local part geometry/source binding mismatch')
        native = np.asarray(row['native_path'], dtype=float)
        bounds = np.asarray(row['native_scope_bounds'], dtype=float)
        if (native.ndim != 2 or native.shape[1] != 2 or len(native) < 2
                or not np.isfinite(native).all() or bounds.shape != (4,)
                or not np.isfinite(bounds).all() or (bounds < 0).any()
                or (bounds[2:] <= bounds[:2]).any()
                or (bounds[2:] > snapshot['source_wh']).any()
                or any(not box(*bounds).covers(Point(x, y)) for x, y in native)):
            raise ValueError('Local part leaves its native source scope')
        spread = np.ptp(native, axis=0)
        left, top, right, bottom = part['bounds']
        if (max(spread) <= 0 or max(spread) < 2 * min(spread)
                or int(np.argmax(spread)) != int(np.argmax([right-left, bottom-top]))):
            raise ValueError('Local part source/design principal direction mismatch')
    return dict(status='SOURCE_BOUND_LOCAL_PART_CANDIDATES',
                evidence=sample['local_part_source_evidence'], part_count=len(parts),
                source_geometry_qualified=False, geometry_human_approved=False)


def native_carrier_review_source(inputs, sample, review, question, claim):
    """Adapt a source-only carrier verdict without approving new design coordinates."""
    scope = question['scope']
    analysis = inputs.document(question['analysis'])
    facts = inputs.document(analysis['source_facts'])
    identity = inputs.human(facts['human_review'])
    expected = dict(id=scope['interface_id'], layer='V2', layer_pair=['M2', 'M3'],
                    source_frame=scope['source_frame'], native_bounds=scope['native_bounds'],
                    lower_metal_id=scope['lower_metal_id'],
                    upper_metal_id=scope['upper_candidate'])
    identity_scope = dict(source_frame=expected['source_frame'],
                          native_bounds=expected['native_bounds'],
                          lower_metal_id=expected['lower_metal_id'])
    if (review.get('kind') != 'native_carrier_confirmation'
            or review.get('question_id') != question['question_id']
            or signature(claim) != expected
            or analysis['source_photos'] != inputs.document(sample['snapshot'])['source_photos']
            or review.get('observed_cut_count') is not None
            or not any(d.get('via_layer') == 'V2' and d.get('V2_present') is True
                       and all(d.get(k) == v for k, v in identity_scope.items())
                       for d in identity['decisions'])):
        raise ValueError('Native carrier review exceeds the submitted source scope')
    for ref in question['images'].values():
        inputs.read(ref)
    working = inputs.document(analysis['working_geometry_baseline'])
    if facts['working_geometry_baseline'] != analysis['working_geometry_baseline']:
        raise ValueError('Native carrier review working baseline mismatch')
    _, request = load_parent(inputs, working['geometry_package'])
    source = inputs.document(request['sample'])
    # This synthesized source signature is only an adapter for the exact native
    # question. It deliberately contains no approved cut count or design bounds.
    source['interfaces'] = [expected]
    return source


def native_batch_carrier_review_source(inputs, sample, review, question, claim):
    """Replay one answer from a bound native batch without promoting geometry or counts."""
    batch = inputs.human(review['sources']['batch_human_review'])
    identity = inputs.human(question['prior_identity_approval'])
    analysis = inputs.document(question['analysis'])
    matches = [q for q in question['questions']
               if q['question_id'] == review.get('question_id')]
    answers = [d for d in batch['decisions']
               if d['question_id'] == review.get('question_id')]
    if len(matches) != 1 or len(answers) != 1:
        raise ValueError('Native batch carrier answer is missing or duplicated')
    scope, answer = matches[0], answers[0]
    source_keys = ('source_frame', 'native_bounds', 'lower_metal_id')
    if (review.get('kind') != 'native_carrier_confirmation'
            or batch.get('kind') != 'native_carrier_batch_human_judgment'
            or review['statement'] != batch['statement']
            or batch['sources']['submitted_request'] != review['sources']['submitted_request']
            or batch['sources']['identity_approval'] != question['prior_identity_approval']
            or review.get('observed_cut_count') is not None
            or batch.get('observed_cut_count') is not None
            or answer.get('physical_cut_count') is not None
            or answer.get('design_geometry_human_approved') is not False
            or answer.get('via_layer') != 'V2'
            or answer.get('connection_confirmed') is not True
            or review['decisions'].get('connection_confirmed') is not True
            or analysis['identity_approval'] != question['prior_identity_approval']
            or any(scope[k] != answer[k] or claim[k] != answer[k] for k in source_keys)
            or claim['layer'] != 'V2' or claim['layer_pair'] != ['M2', 'M3']
            or claim['upper_metal_id'] != answer['upper_metal_id']
            or answer['upper_metal_id'] not in scope['alternative_ids']
            or not any(d.get('V2_present_human_confirmed') is True
                       and d.get('via_layer') == 'V2'
                       and d.get('candidate_id') == answer.get('candidate_id')
                       and all(d.get(k) == answer[k] for k in source_keys)
                       for d in identity['decisions'])):
        raise ValueError('Native batch carrier review exceeds the original answer scope')
    for ref in question['images'].values():
        inputs.read(ref)
    snapshot = inputs.document(sample['snapshot'])
    if (not {'m2', 'm3'} <= set(analysis['source_photos'])
            or any(snapshot['source_photos'].get(k) != v
                   for k, v in analysis['source_photos'].items())):
        raise ValueError('Native batch carrier source photograph drift')
    source_request = inputs.document(analysis['working_request'])
    source = inputs.document(source_request['sample'])
    # The copied signature conveys the reviewed interface, never the new array geometry.
    source['interfaces'] = [signature(claim)]
    return source


def native_source_decision_adapter(inputs, sample, review, question, claim):
    """Map an existing native human verdict to source-bound working IDs, not dimensions."""
    batch = inputs.human(review['sources']['original_human_review'])
    original = inputs.document(question['original_submitted_request'])
    scope_document = inputs.document(question['scope_source'])
    scope = pointer(scope_document, question['scope_pointer'])
    answer = pointer(batch, question['decision_pointer'])
    questions = original.get('questions', [original])
    layer = claim['layer']
    native_bounds = (scope.get('m1_native_search_bounds') if layer == 'V1'
                     else scope.get('native_search_bounds'))
    if (review.get('actor') != 'AI'
            or question.get('kind') != 'scoped_native_interface_decision_binding'
            or review.get('statement') != batch['statement']
            or batch['sources']['submitted_request'] != question['original_submitted_request']
            or len([q for q in questions if q.get('question_id') == question['question_id']]) != 1
            or answer.get('question_id', batch.get('question_id')) != question['question_id']
            or question['scope_source'] not in [original.get('observation_source'),
                                               original.get('sources', {}).get('observations')]
            or answer.get('interface_id') != claim['id'] or scope.get('id') != claim['id']
            or answer.get('via_layer') != layer
            or answer.get(layer + '_present') is not True
            or answer.get('source_frame') != claim['source_frame']
            or answer.get('native_search_bounds') != native_bounds
            or native_bounds != claim['native_bounds']
            or answer.get('connection_confirmed') is not True
            or answer.get('physical_cut_count') is not None
            or answer.get('design_geometry_human_approved') is not False
            or review.get('observed_cut_count') is not None
            or review['decisions'].get('connection_confirmed') is not True
            or question.get('scope_signature') != signature(claim)):
        raise ValueError('Native decision adapter exceeds original question/verdict scope')
    inputs.evidence(review)
    features = {f['id']: f for fs in sample['features_by_layer'].values() for f in fs}
    snapshot = inputs.document(sample['snapshot'])
    if (not scope_document.get('photos') or any(snapshot['source_photos'].get(frame) != photo
            for frame, photo in scope_document['photos'].items())):
        raise ValueError('Native decision adapter photograph drift')
    bindings = question['carrier_bindings']
    if set(bindings) != {'lower', 'upper'}:
        raise ValueError('Native decision adapter needs both source carrier bindings')
    for side in ('lower', 'upper'):
        binding = bindings[side]
        feature = features[claim[side + '_metal_id']]
        record = pointer(inputs.document(binding['source']), binding['pointer'])
        frame = record.get('source_frame', record.get('frame'))
        if (binding['model_id'] != feature['id'] or binding['source_id'] != record['id']
                or answer[side + '_source_id'] != record['id']
                or frame != feature['source_frame']):
            raise ValueError('Native decision adapter carrier identity drift')
        if binding.get('local_part_id'):
            ledger = inputs.document(sample['local_part_source_evidence'])
            rows = [r for r in ledger['parts'] if r['metal_id'] == feature['id']
                    and r['part_id'] == binding['local_part_id']]
            if (len(rows) != 1 or rows[0].get('source_observation_id') != record['id']
                    or rows[0]['native_path'] != record['native_path']
                    or rows[0]['source_photo'] != snapshot['source_photos'][frame]
                    or not LineString(record['native_path']).intersects(box(*native_bounds))):
                raise ValueError('Native decision adapter local source part drift')
        elif feature['id'] != record['id'] or feature['native_path'] != record['native_path']:
            raise ValueError('Native decision adapter direct source anchor drift')
    # Only the reviewed source signature is adapted. No new image or geometry is
    # represented as having been shown to the human, and no count is synthesized.
    source = copy.deepcopy(sample)
    source['interfaces'] = [signature(claim)]
    return source


def apply_reviews(inputs, sample, refs):
    claims = {c['id']: c for c in sample['interfaces']}
    decisions, approved = {}, []
    for ref in refs:
        review = inputs.document(ref)
        adapted = review.get('kind') == 'native_source_decision_adapter'
        if not adapted:
            review = inputs.human(ref)
        authority_ref = review['sources']['original_human_review'] if adapted else ref
        decision = review['decisions']
        key = decision.get('interface_id', decision.get('id'))
        if (key not in claims or set(decision) - {'interface_id', 'id', 'via_layer',
                'lower_metal_id', 'upper_metal_id', 'connection_confirmed'}):
            raise ValueError('Review exceeds interface scope')
        source = inputs.document(review['sources']['submitted_request'])
        if adapted:
            source = native_source_decision_adapter(
                inputs, sample, review, source, claims[key])
        elif source.get('kind') == 'scoped_native_carrier_review_request':
            source = native_carrier_review_source(inputs, sample, review, source, claims[key])
        elif source.get('kind') == 'scoped_native_carrier_comparison_review_request':
            source = native_batch_carrier_review_source(
                inputs, sample, review, source, claims[key])
        elif source.get('kind') == 'scoped_native_M1_V1_entry_review_request':
            source = native_entry_review_source(inputs, sample, review, source, claims[key])
        if source.get('kind') == 'conductive_reconstruction_workflow':
            binding = review['sources']['submitted_manifest']
            manifest = inputs.document(binding)
            directory = Path(binding['path']).parent
            for label, filename in [('submitted_request', 'request.json'),
                                    ('submitted_page', 'index.html')]:
                expected = dict(path=str(directory / filename),
                                sha256=manifest['artifacts'][filename])
                if review['sources'][label] != expected:
                    raise ValueError('Review not bound to the submitted workflow package')
            source = inputs.document(source['sample'])
        if source['snapshot'] != sample['snapshot']:
            raise ValueError('Review belongs to a different photo snapshot')
        original = next((c for c in source['interfaces'] if c.get('id') == key), None)
        claim = claims[key]
        if original is None or (signature(original) != signature(claim)
                                 and not carrier_correction(review, original, claim)):
            raise ValueError('Review source correspondence drift')
        source_metals = {f['id']: f for fs in source['features_by_layer'].values() for f in fs}
        current_metals = {f['id']: f for fs in sample['features_by_layer'].values() for f in fs}
        for metal_id in (claim['lower_metal_id'], claim['upper_metal_id']):
            if any(source_metals[metal_id][k] != current_metals[metal_id][k]
                   for k in ('source_frame', 'native_path', 'layer')):
                raise ValueError('Reviewed metal source anchor drift')
        expected = dict(via_layer=claim['layer'], lower_metal_id=claim['lower_metal_id'],
                        upper_metal_id=claim['upper_metal_id'])
        if any(decision[k] != value for k, value in expected.items()):
            raise ValueError('Review carrier contradicts candidate')
        verdict = decision['connection_confirmed']
        if verdict is not None and type(verdict) is not bool:
            raise ValueError('Invalid review verdict')
        count = review.get('observed_cut_count')
        if count is not None and (type(count) is not int or count <= 0):
            raise ValueError('Invalid human observed cut count')
        if count is not None and verdict is True:
            array = claim.get('cut_array_candidate')
            if (not array or array['rows'] * array['columns'] != count
                    or claim.get('count_evidence') != ref):
                raise ValueError('Reviewed multi-cut count/footprint evidence was lost or changed')
        result = dict(id=key, connection_confirmed=verdict, human_review=authority_ref)
        if key in decisions and decisions[key] != result:
            raise ValueError('Conflicting human decisions need explicit correction')
        decisions[key] = result
        if verdict is True:
            approved.append(dict(**signature(claim), status='human_confirmed_scoped_interface',
                                 connection_confirmed=True, human_review=authority_ref,
                                 physical_cut_count=count))
    return approved, decisions


def prepare(root, request):
    root, inputs = Path(root), Inputs(root)
    if request['kind'] != 'conductive_reconstruction_workflow' or request['schema_version'] != 1:
        raise ValueError('Unsupported workflow request')
    if (request.get('net_edges') or request.get('automatic_network_export_allowed')
            or request.get('geometry_adopted')):
        raise ValueError('Workflow request cannot authorize adoption or export')
    sample = inputs.document(request['sample'])
    if request.get('source_panel_spec'):
        sample['source_panels'] = inputs.document(request['source_panel_spec'])
    if (sample.get('net_edges') or sample.get('automatic_network_export_allowed')
            or sample.get('complete_network')
            or sample.get('source_to_design_transform') is not None):
        raise ValueError('Sample cannot authorize export, completion or projection')
    snapshot = inputs.document(sample['snapshot'])
    baseline = inputs.document(snapshot['conductive_layers'])
    for ref in snapshot['source_photos'].values():
        inputs.read(ref)
    observed_arrays, count_evidence_docs = {}, {}
    for cut in sample['interfaces']:
        if cut.get('array_source_evidence') and sample['kind'] != 'continuous_conductive_medium':
            observation = inputs.document(cut['array_source_evidence'])
            inputs.evidence(observation)
            observed_arrays[cut['id']] = observed_array_audit(
                observation, cut, snapshot['source_photos'][cut['source_frame']],
                cut['id'], cut['layer'])
        if cut.get('count_evidence'):
            evidence = inputs.human(cut['count_evidence'])
            array = cut.get('cut_array_candidate', {})
            if (evidence['decisions'].get('interface_id') != cut['id']
                    or type(evidence.get('observed_cut_count')) is not int
                    or evidence['observed_cut_count'] != array.get('rows', 0)
                    * array.get('columns', 0)):
                raise ValueError('Via array count differs from bound human evidence')
            if evidence.get('kind') == 'via_group_geometry_feedback':
                submitted = inputs.document(evidence['sources']['submitted_request'])
                previous = inputs.document(submitted['sample'])
                old = next((c for c in previous['interfaces'] if c['id'] == cut['id']), None)
                if (old is None or signature(old) != signature(cut)
                        or evidence.get('scope_signature') != signature(cut)
                        or evidence['sources'].get(cut['source_frame'])
                        != snapshot['source_photos'][cut['source_frame']]):
                    raise ValueError('Geometry feedback count belongs to another interface/source')
            count_evidence_docs[cut['id']] = evidence
    legacy = sample['kind'] == 'continuous_conductive_medium'
    shape = source_shape_audit(sample['features_by_layer'])
    if shape['status'] == 'FAIL':
        failed = [c['id'] for c in shape['checks'] if c['status'] == 'FAIL']
        raise ValueError('Source turn handedness mismatch: ' + ', '.join(failed))
    legacy_report = None
    if legacy:
        model, legacy_report, _, files = prepare_medium(root, sample)
        audits = legacy_report
        inputs.files.update(files)
    else:
        model, audits = candidate_model(sample, snapshot)
        identity = source_identity_audit(model, baseline['source_identity_policy'])
        order = source_order_audit(sample['features_by_layer'],
                                   sample.get('source_order_checks', []))
        if identity['status'] != 'PASS' or order['status'] != 'PASS':
            raise ValueError('Source identity/order gate failed')
        audits.update(source_identity=identity, source_order=order)
        if observed_arrays:
            audits['array_source_observations'] = observed_arrays
    if sample.get('additional_source_order_checks'):
        extra_order = source_order_audit(sample['features_by_layer'],
                                         sample['additional_source_order_checks'])
        if extra_order['status'] != 'PASS':
            raise ValueError('Additional source order gate failed')
        audits['additional_source_order'] = extra_order
    inventory_mapping = None
    if sample.get('visible_inventory'):
        inventory_mapping = inventory_geometry_audit(inputs, sample, snapshot)
        audits['visible_inventory_geometry'] = inventory_mapping
    extent_candidates = None
    if sample.get('source_extent_evidence'):
        extent_candidates = source_extent_audit(inputs, sample)
        audits['source_extent_candidates'] = extent_candidates
    if sample.get('local_part_source_evidence'):
        audits['local_part_source_candidates'] = local_part_source_audit(inputs, sample, snapshot)
    added = []
    added_interfaces = []
    parent = parent_request = canvas_extension = None
    if request.get('parent'):
        parent, parent_request = load_parent(inputs, request['parent'])
        if request.get('preserve_via_center_ids'):
            audits['preserved_via_centers'] = preserve_via_centers(
                parent, model, request['preserve_via_center_ids'])
        previous = inputs.document(parent_request['sample'])
        if any(sample.get(k) != previous.get(k) for k in ('snapshot', 'metal_budget',
                                                        'via_budget', 'source_order_checks')):
            raise ValueError('Revision cannot change snapshot, canvas or budgets')
        if (sample['canvas_wh'] != previous['canvas_wh']
                or sample.get('canvas_bounds') != previous.get('canvas_bounds')):
            if legacy or not request.get('canvas_extension_evidence'):
                raise ValueError('Revision cannot change snapshot, canvas or budgets')
            canvas_extension = canvas_extension_audit(
                inputs, request, previous, sample, parent_request)
            audits['canvas_extension'] = canvas_extension
        elif request.get('canvas_extension_evidence'):
            raise ValueError('Canvas extension declaration without an increased canvas')
        old = {f['id']: f for fs in previous['features_by_layer'].values() for f in fs}
        new = {f['id']: f for fs in sample['features_by_layer'].values() for f in fs}
        old.update({c['id']: c for c in previous['interfaces']})
        new.update({c['id']: c for c in sample['interfaces']})
        added = sorted(set(new) - set(old))
        if set(old) - set(new):
            raise ValueError('Revision cannot silently add or retire stable IDs')
        if added:
            interface_ids = {c['id'] for c in sample['interfaces']}
            if request.get('added_interface_ids'):
                declared = request['added_interface_ids']
                if (legacy or sorted(declared) != added or len(set(declared)) != len(declared)
                        or not set(added) <= interface_ids
                        or request.get('added_metal_ids') or request.get('extension_evidence')
                        or not request.get('interface_extension_evidence')):
                    raise ValueError('Invalid explicit interface extension')
                if any(old[k] != new[k] for k in old):
                    raise ValueError('Interface extension must preserve every existing record')
                evidence = inputs.document(request['interface_extension_evidence'])
                observations = evidence.get('interface_observations', {})
                if (evidence.get('actor') != 'AI' or not evidence.get('reason')
                        or evidence.get('parent') != request['parent']
                        or sorted(evidence.get('added_interface_ids', [])) != added
                        or set(observations) != set(added)):
                    raise ValueError('Interface extension evidence does not bind parent/IDs')
                for claim in sample['interfaces']:
                    if claim['id'] in added and (
                            not claim.get('array_source_evidence')
                            or observations[claim['id']] != claim['array_source_evidence']):
                        raise ValueError('Interface extension requires bound array observations')
                inputs.evidence(evidence)
                added_interfaces, added = added, []
                audits['interface_extension'] = dict(
                    status='PASS', added_interface_ids=added_interfaces,
                    existing_records_exact=True, evidence=request['interface_extension_evidence'])
        if added:
            declared = request.get('added_metal_ids', [])
            if (legacy or sorted(declared) != added or len(set(declared)) != len(declared)
                    or any(k not in {f['id'] for fs in sample['features_by_layer'].values()
                                     for f in fs} for k in added)
                    or not request.get('extension_evidence') or inventory_mapping is None):
                raise ValueError('Revision cannot silently add or retire stable IDs')
            if any(old[k] != new[k] for k in old):
                raise ValueError(
                    'Metal extension must preserve every existing feature and interface')
            evidence = inputs.document(request['extension_evidence'])
            if (evidence.get('actor') != 'AI' or not evidence.get('reason')
                    or evidence.get('parent') != request['parent']
                    or evidence.get('inventory') != sample['visible_inventory']
                    or sorted(evidence.get('added_metal_ids', [])) != added):
                raise ValueError('Metal extension evidence does not bind parent/inventory/IDs')
            inputs.evidence(evidence)
            audits['metal_extension'] = dict(status='PASS', added_metal_ids=added,
                                             existing_records_exact=True,
                                             evidence=request['extension_evidence'])
        elif request.get('added_metal_ids') or request.get('extension_evidence'):
            raise ValueError('Extension declaration without added metal')
        if not added_interfaces and (request.get('added_interface_ids')
                                     or request.get('interface_extension_evidence')):
            raise ValueError('Interface extension declaration without added interfaces')
        for key in ('visible_inventory', 'inventory_geometry_mapping',
                    'additional_source_order_checks'):
            if previous.get(key) is not None and sample.get(key) != previous[key]:
                raise ValueError('Existing inventory/order binding cannot silently change')
        previous_supplements = previous.get('supplemental_visible_inventories', [])
        supplements = sample.get('supplemental_visible_inventories', [])
        if (supplements[:len(previous_supplements)] != previous_supplements
                or (supplements != previous_supplements and not added)):
            raise ValueError('Inventory supplements must be append-only with added metal')
        old_extent, new_extent = (value.get('source_extent_evidence')
                                  for value in (previous, sample))
        if old_extent and not new_extent:
            raise ValueError('Existing inventory/order binding cannot silently change')
        if new_extent and new_extent != old_extent:
            evidence = inputs.document(new_extent)
            if (not request.get('revision_evidence')
                    or evidence.get('basis_parent') != request['parent']):
                raise ValueError('New extent evidence must bind the current revision parent')
        old_parts, new_parts = (value.get('local_part_source_evidence')
                                for value in (previous, sample))
        if (old_parts and not new_parts) or (
                new_parts and new_parts != old_parts and not request.get('revision_evidence')):
            raise ValueError('Local part evidence cannot disappear or change without a revision')
        changes = sorted(k for k in old if old[k] != new[k])
        if changes != sorted(request.get('allowed_changed_ids', [])):
            raise ValueError('Revision change scope mismatch')
        if changes and not request.get('revision_evidence'):
            raise ValueError('Revision requires source evidence')
        if changes:
            evidence = inputs.document(request['revision_evidence'])
            if evidence.get('actor') != 'AI' or not evidence.get('reason'):
                raise ValueError('Revision needs an explicit AI proposal and reason')
            inputs.evidence(evidence)
        for key in old:
            if not legacy and key in {c['id'] for c in sample['interfaces']} and (
                    signature(old[key]) != signature(new[key])):
                corrected = False
                for ref in request.get('reviews', []):
                    review = inputs.human(ref)
                    if review.get('decisions', {}).get('interface_id') == key:
                        corrected = carrier_correction(review, old[key], new[key])
                        if corrected:
                            break
                if not corrected:
                    raise ValueError('Revision cannot silently change interface identity')
            if 'native_path' in old[key] and any(old[key][k] != new[key][k]
                                                for k in ('source_frame', 'native_path', 'layer')):
                raise ValueError('Revision cannot silently move native source anchors')
    else:
        changes = []
        if 'canvas_bounds' in sample:
            raise ValueError('Signed canvas bounds require an explicit parent extension')
        if request.get('canvas_extension_evidence'):
            raise ValueError('Canvas extension requires a parent package')
        if request.get('added_metal_ids') or request.get('extension_evidence'):
            raise ValueError('Metal extension requires a parent package')
        if request.get('added_interface_ids') or request.get('interface_extension_evidence'):
            raise ValueError('Interface extension requires a parent package')
        if request.get('preserve_via_center_ids'):
            raise ValueError('Preserved via centers require a parent package')
        if request.get('allowed_changed_ids'):
            raise ValueError('Changed IDs require a parent package')
    refs = copy.deepcopy(parent['review_sources']) if parent else []
    for ref in request.get('reviews', []):
        if ref not in refs:
            refs.append(ref)
    if legacy and refs:
        raise ValueError('Legacy samples retain their own bound approvals')
    if legacy:
        decisions = {}
        pending = []
    else:
        approved, decisions = apply_reviews(inputs, sample, refs)
        model['reviewed_local_connections'] = approved
        pending = [c['id'] for c in sample['interfaces']
                   if decisions.get(c['id'], {}).get('connection_confirmed') is None]
    deferred = request.get('deferred_unknown_ids', [])
    if not set(deferred) <= set(pending):
        raise ValueError('Only pending candidates may be deferred as unknown')
    if parent:
        if (parent.get('branch', {}).get('terminal_closed')
                and not model.get('branch', {}).get('terminal_closed')):
            raise ValueError('Previously approved terminal was lost')
        missing_limits = set(parent['limits']) - set(request.get('limits', []))
        resolved_limits = request.get('resolved_limits', {})
        if missing_limits != set(resolved_limits):
            raise ValueError('Inherited limitations cannot silently disappear')
        for text, ref in resolved_limits.items():
            review = inputs.human(ref)
            key = review['decisions'].get('interface_id')
            if (ref not in refs or key not in parent['pending_interface_ids']
                    or decisions.get(key, {}).get('connection_confirmed') is None
                    or text not in review.get('resolves_limit_texts', [])):
                raise ValueError('Resolved limitation requires a bound pending-interface verdict')
        before = {c['id']: c for c in parent['reviewed_local_connections']}
        after = {c['id']: c for c in model['reviewed_local_connections']}
        if any(key not in after or before[key] != after[key] for key in before):
            raise ValueError('Previously approved connection was lost or changed')
    assets = request.get('source_assets', {})
    spec = sample['source_panels']
    frames = request['frames']
    if not frames or len(set(frames)) != len(frames):
        raise ValueError('Missing or duplicate source frames')
    needed = {f['source_frame'] for fs in sample['features_by_layer'].values() for f in fs}
    if not needed <= set(frames):
        raise ValueError('Source views omit a reconstructed metal layer')
    for cut in sample['interfaces']:
        if 'native_bounds' not in cut:
            continue  # Legacy support proxies do not contain measured native footprints.
        window = box(*cut['native_bounds'])
        windows = spec['source_windows'].get(cut['source_frame'], {})
        if not any(box(*bounds).covers(window) for bounds in windows.values()):
            raise ValueError('Source review omits the observed via group: ' + cut['id'])
    for frame in frames:
        if frame not in snapshot['source_photos'] or frame not in spec['source_windows']:
            raise ValueError('Missing source frame/window')
        with Image.open(root / snapshot['source_photos'][frame]['path']) as photo:
            for mode in ('wide', 'detail'):
                bounds = spec['source_windows'][frame][mode]
                if not (0 <= bounds[0] < bounds[2] <= photo.width
                        and 0 <= bounds[1] < bounds[3] <= photo.height):
                    raise ValueError('Source view outside photograph')
                if assets:
                    for style in ('raw', 'marked'):
                        inputs.read(assets[frame][mode + '_' + style])
                    expected = photo.crop(bounds).convert('RGB')
                    if mode == 'detail':
                        expected = expected.resize((expected.width * 4, expected.height * 4))
                    raw = Image.open(root / assets[frame][mode + '_raw']['path']).convert('RGB')
                    marked = Image.open(root / assets[frame][mode + '_marked']['path'])
                    if (expected.size != raw.size or marked.size != raw.size
                            or ImageChops.difference(expected, raw).getbbox()):
                        raise ValueError('Reused source view does not match photograph/window')
    model.update(kind='conductive_workflow_candidate', sample=request['sample'],
                 review_sources=refs, limits=request.get('limits', []),
                 pending_interface_ids=pending,
                 deferred_unknown_ids=deferred, review_decisions=decisions,
                 net_edges=[], complete_network=False, automatic_network_export_allowed=False,
                 precise_projection_allowed=False, geometry_adopted=False)
    canvas_history = copy.deepcopy(parent.get('canvas_extension_history', [])) if parent else []
    if canvas_extension:
        if (model['objects_by_layer'] != parent['objects_by_layer']
                or model['candidate_interfaces'] != parent['candidate_interfaces']
                or model['reviewed_local_connections'] != parent['reviewed_local_connections']
                or model['pending_interface_ids'] != parent['pending_interface_ids']
                or model['review_sources'] != parent['review_sources']):
            raise ValueError('Canvas-only transaction changed geometry or reviewed connections')
        canvas_history.append(canvas_extension)
    if canvas_history:
        model['canvas_extension_history'] = canvas_history
    resolved = dict(parent.get('resolved_limits', {})) if parent else {}
    resolved.update(request.get('resolved_limits', {}))
    if resolved:
        model['resolved_limits'] = resolved
    inherited = inherited_group_facts(inputs, baseline, model)
    if inherited:
        model['inherited_group_facts'] = inherited
    if inventory_mapping:
        model['visible_inventory_geometry'] = inventory_mapping
    if extent_candidates:
        model['source_extent_candidates'] = extent_candidates
    additional_counts = []
    for cut in sample['interfaces']:
        evidence = count_evidence_docs.get(cut['id'])
        if evidence and evidence.get('kind') == 'via_group_geometry_feedback':
            additional_counts.append(dict(support_id=cut['id'],
                                          cut_count=evidence['observed_cut_count'],
                                          human_review=cut['count_evidence']))
    if additional_counts:
        model['observed_group_count_facts'] = additional_counts
    report = dict(status='TECHNICAL_PASS_WITH_SCOPED_REVIEWS_AND_UNKNOWNS', audits=audits,
                  object_counts={k: len(v) for k, v in model['objects_by_layer'].items()},
                  pending_interface_ids=pending, deferred_unknown_ids=deferred,
                  reviewed_interface_ids=[c['id'] for c in model['reviewed_local_connections']],
                  changed_object_ids=changes, previously_approved_preserved=True,
                  physical_accuracy=None, autonomous_image_recognition=False,
                  complete_network=False, canonical_geometry_adopted=False)
    if added_interfaces:
        report['added_interface_ids'] = added_interfaces
    report['quality'] = quality_summary(model, sample, shape, legacy_report)
    if inventory_mapping:
        report['added_metal_ids'] = added
        report['quality']['visible_inventory_geometry'] = inventory_mapping
        report['quality']['blocking_adoption_reasons'] = [
            ('声明的来源片段已建模；旧对象端部仍部分覆盖，像素穷尽性和来源疑点未验收。'
             if text == '未建立全部可见导体/接口清单，不能给出照片覆盖率或整网完成率。'
             else text) for text in report['quality']['blocking_adoption_reasons']]
    if extent_candidates:
        report['quality']['source_extent_candidates'] = extent_candidates
    return model, report, sample, snapshot, inputs.files


def page(model, report, sample, request, output, root):
    w, h = model['canvas_wh']
    bounds = design_canvas_bounds([w, h], model.get('canvas_bounds'))
    drawing = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="'
               + f'{bounds[0]} {bounds[1]} {w} {h}">')
    drawing += svg_layers(model, bounds)
    for layer, features in sample['features_by_layer'].items():
        drawing += f'<g data-layer="{layer}" fill="white" font-size="24">'
        for f in features:
            x, y = f['label_xy']
            drawing += (f'<text x="{x}" y="{y}" stroke="#101a27" stroke-width="4" '
                        f'paint-order="stroke">{html.escape(f["label"])}</text>')
        drawing += '</g>'
    drawing += '</svg>'
    controls = ''.join(f'<label><input type="checkbox" data-layer-toggle="{k}" checked>{k}</label>'
                       for k in LAYERS)
    statuses = ''.join(f'<li>{html.escape(c["id"])}：'
                       f'{html.escape(c["lower_metal_id"])} → '
                       f'{html.escape(c["upper_metal_id"])}；已审连接，几何仍候选</li>'
                       for c in model['reviewed_local_connections'])
    statuses += ''.join(f'<li>{html.escape(k)}：未知／待裁决，不视为断开</li>'
                        for k in report['pending_interface_ids'])
    statuses += ''.join(f'<li>{html.escape(k)}：候选接入已否决；不证明无孔或全局断开</li>'
                        for k, d in model['review_decisions'].items()
                        if d['connection_confirmed'] is False)
    branch = ('<p>已审U3端子路径继续保留；体端身份、孔数及其他分支仍未知。</p>'
              if model.get('branch', {}).get('terminal_closed') else '')
    photos = ''
    for frame in request['frames']:
        photos += f'<section data-photo="{frame}"'+('' if frame == request['frames'][0]
                                                     else ' hidden')+f'><h2>{frame.upper()}</h2>'
        for mode in ('wide', 'detail'):
            paths = {}
            for style in ('raw', 'marked'):
                if request.get('source_assets'):
                    target = root / request['source_assets'][frame][mode + '_' + style]['path']
                    paths[style] = os.path.relpath(target, output)
                else:
                    paths[style] = f'{frame}-{mode}-{style}.png'
            photos += (f'<p><a href="{html.escape(paths["raw"])}">无标记原图</a> · '
                       f'<a href="{html.escape(paths["marked"])}">完整标记图</a></p>'
                       f'<img src="{html.escape(paths["marked"])}" alt="{frame} {mode}">')
        photos += '</section>'
    buttons = ''.join(f'<button data-frame="{f}">{f.upper()}原图</button>'
                      for f in request['frames'])
    limits = ''.join('<li>'+html.escape(x)+'</li>' for x in model['limits'])
    questions = ''.join('<li>'+html.escape(request.get('questions', {}).get(k, k))+'</li>'
                        for k in report['pending_interface_ids'])
    quality = report['quality']
    quality_html = ('<h2>质量分项：可复核，尚不能采用为完整几何</h2><ul>'
                    f'<li>程序检查通过；来源折线方向：{quality["source_path_shape"]["status"]}。'
                    '这不是照片几何验收。</li>'
                    f'<li>已审承载 {quality["reviewed_represented_interface_count"]}/'
                    f'{quality["represented_interface_count"]} 个当前接口；'
                    f'仍有 {len(quality["proxy_interface_ids"])} 个孔组代理框。</li>'
                    f'<li>显式设计阵列 {quality["explicit_design_array_count"]} 组；'
                    '来源阵列几何验收 0 组。人工连接批准不等于排列/尺寸批准。</li>'
                    '<li>覆盖不完整，照片覆盖率未建立；真实工艺尺寸与DRC未验证。</li></ul>')
    quality_html += '<ul>'+''.join('<li>'+html.escape(x)+'</li>'
                                  for x in quality['blocking_adoption_reasons'])+'</ul>'
    quality_html += ('<div class="scroll"><table><tr><th>接口/支持区</th><th>承载</th>'
                     '<th>已知人审孔数</th><th>几何表示</th><th>完整设计孔组覆盖</th>'
                     '<th>来源阵列几何</th></tr>')
    for row in quality['interface_geometry']:
        count = '未知' if row['human_cut_count'] is None else str(row['human_cut_count'])
        if row['inherited_group_fact']:
            fact = row['inherited_group_fact']
            status = ('已迁移设计阵列，来源尺寸待验收' if fact['geometry_ported']
                      else '尚未迁移完整几何')
            count += f'（已审{fact["rows"]}×{fact["columns"]}，{status}）'
        representation = ('显式设计阵列（仍是候选）' if row['design_cut_count'] else '孔组代理框')
        bearing = '逐孔设计检查通过' if row['design_cut_count'] else '未评估，单框不能代表整组'
        carrier = '已审局部连接' if row['carrier_status'] == 'HUMAN_CONFIRMED_SCOPED' else '未确认'
        quality_html += '<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in (
            row['id'], carrier, count, representation, bearing, '未验收'))+'</tr>'
    quality_html += '</table></div>'
    template = Path(__file__).with_suffix('.html').read_text()
    return Template(template).substitute(statuses=statuses, branch=branch, controls=controls,
                                          drawing=drawing, buttons=buttons, photos=photos,
                                          limits=limits, questions=questions, quality=quality_html)



def run(root, request_path, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() or not output.is_relative_to(root):
        raise ValueError('Output must be a new directory inside the project')
    try:
        request = json.loads(Path(request_path).read_text())
        model, report, sample, snapshot, files = prepare(root, request)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.conductive-workflow-',
                                         dir=output.parent) as temporary:
            stage = Path(temporary) / 'package'
            stage.mkdir()
            for name, value in [('model', model), ('report', report), ('request', request)]:
                (stage / (name+'.json')).write_text(
                    json.dumps(value, ensure_ascii=False, indent=2)+'\n')
            if not request.get('source_assets'):
                source_panels(root, snapshot, sample['source_panels'], stage,
                              frames=request['frames'])
            (stage / 'index.html').write_text(page(model, report, sample, request, output, root))
            manifest = dict(inputs=files, artifacts={str(p.relative_to(stage)): digest(p)
                                                   for p in stage.iterdir() if p.is_file()})
            (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
            stage.rename(output)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        if not output.exists():
            output.mkdir(parents=True)
            (output / 'diagnostic.json').write_text(json.dumps(
                dict(status='REJECTED', reason=str(exc)), ensure_ascii=False, indent=2)+'\n')
        raise
    return model, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        run(Path.cwd(), args.request, args.output)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f'Rejected: {exc}\n')


if __name__ == '__main__':
    main()
