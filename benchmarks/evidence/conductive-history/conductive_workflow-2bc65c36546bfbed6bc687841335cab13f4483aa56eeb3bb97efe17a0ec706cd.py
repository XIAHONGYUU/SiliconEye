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
from shapely.geometry import box

from .conductive_layers import LAYERS, geometry, source_identity_audit, svg_layers
from .conductive_medium import prepare as prepare_medium
from .conductive_medium import source_order_audit
from .conductive_quality import inherited_group_facts, quality_summary, source_shape_audit
from .geometry_reconstruction import digest
from .metal_reconstruction import geometry_audit
from .metal_via_pilot import group_via_budget, interface_audit, observed_array_audit, source_panels
from .metal_via_pilot import regular_group_cuts as via_cuts
from .review_package import Inputs


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
        audit, polygons = geometry_audit(features, sample['metal_budget'], sample['canvas_wh'])
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
    return dict(objects_by_layer=objects, source_photos=snapshot['source_photos'],
                canvas_wh=sample['canvas_wh'], reviewed_local_connections=[],
                candidate_interfaces=copy.deepcopy(sample['interfaces'])), audits


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
    return dict(status='DECLARED_FRAGMENT_GEOMETRY_MAPPING_PASS',
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


def apply_reviews(inputs, sample, refs):
    claims = {c['id']: c for c in sample['interfaces']}
    decisions, approved = {}, []
    for ref in refs:
        review = inputs.human(ref)
        decision = review['decisions']
        key = decision.get('interface_id', decision.get('id'))
        if (key not in claims or set(decision) - {'interface_id', 'id', 'via_layer',
                'lower_metal_id', 'upper_metal_id', 'connection_confirmed'}):
            raise ValueError('Review exceeds interface scope')
        source = inputs.document(review['sources']['submitted_request'])
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
        result = dict(id=key, connection_confirmed=verdict, human_review=ref)
        if key in decisions and decisions[key] != result:
            raise ValueError('Conflicting human decisions need explicit correction')
        decisions[key] = result
        if verdict is True:
            approved.append(dict(**signature(claim), status='human_confirmed_scoped_interface',
                                 connection_confirmed=True, human_review=ref,
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
    added = []
    parent = parent_request = None
    if request.get('parent'):
        parent, parent_request = load_parent(inputs, request['parent'])
        if request.get('preserve_via_center_ids'):
            audits['preserved_via_centers'] = preserve_via_centers(
                parent, model, request['preserve_via_center_ids'])
        previous = inputs.document(parent_request['sample'])
        if any(sample.get(k) != previous.get(k) for k in ('snapshot', 'canvas_wh', 'metal_budget',
                                                  'via_budget', 'source_order_checks')):
            raise ValueError('Revision cannot change snapshot, canvas or budgets')
        old = {f['id']: f for fs in previous['features_by_layer'].values() for f in fs}
        new = {f['id']: f for fs in sample['features_by_layer'].values() for f in fs}
        old.update({c['id']: c for c in previous['interfaces']})
        new.update({c['id']: c for c in sample['interfaces']})
        added = sorted(set(new) - set(old))
        if set(old) - set(new):
            raise ValueError('Revision cannot silently add or retire stable IDs')
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
        for key in ('visible_inventory', 'inventory_geometry_mapping',
                    'additional_source_order_checks'):
            if previous.get(key) is not None and sample.get(key) != previous[key]:
                raise ValueError('Existing inventory/order binding cannot silently change')
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
        if request.get('added_metal_ids') or request.get('extension_evidence'):
            raise ValueError('Metal extension requires a parent package')
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
    resolved = dict(parent.get('resolved_limits', {})) if parent else {}
    resolved.update(request.get('resolved_limits', {}))
    if resolved:
        model['resolved_limits'] = resolved
    inherited = inherited_group_facts(inputs, baseline, model)
    if inherited:
        model['inherited_group_facts'] = inherited
    if inventory_mapping:
        model['visible_inventory_geometry'] = inventory_mapping
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
    report['quality'] = quality_summary(model, sample, shape, legacy_report)
    if inventory_mapping:
        report['added_metal_ids'] = added
        report['quality']['visible_inventory_geometry'] = inventory_mapping
        report['quality']['blocking_adoption_reasons'] = [
            ('声明的来源片段已建模；旧对象端部仍部分覆盖，像素穷尽性和来源疑点未验收。'
             if text == '未建立全部可见导体/接口清单，不能给出照片覆盖率或整网完成率。'
             else text) for text in report['quality']['blocking_adoption_reasons']]
    return model, report, sample, snapshot, inputs.files


def page(model, report, sample, request, output, root):
    w, h = model['canvas_wh']
    drawing = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+f'{w} {h}">'
    drawing += svg_layers(model, [0, 0, w, h])
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
