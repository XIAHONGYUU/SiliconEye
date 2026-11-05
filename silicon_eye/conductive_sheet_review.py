"""Bind accepted fixed-sheet source identities/carriers to working interfaces.

Used by conductive_workflow; no geometry, counts or human answers are generated.
"""

import copy
from pathlib import Path

from .review_package import pointer
from .review_sheet import check, load_package


def checked_item(inputs, binding):
    """Validate an actual archived sheet and retain its complete evidence binding."""
    inputs.read(binding['manifest'])
    folder = inputs.root / Path(binding['manifest']['path']).parent
    manifest, spec = load_package(folder)
    check(inputs.root, folder, inputs.root / binding['decision']['path'])
    record = inputs.document(binding['decision'])
    expected = dict(path=str(Path(binding['manifest']['path']).parent),
                    manifest_sha256=binding['manifest']['sha256'])
    if record.get('sources', {}).get('submitted_package') != expected:
        raise ValueError('Sheet decision is not the archived submitted package')
    for name, digest in [('index.html', manifest['page_sha256']),
                         ('review-spec.json', manifest['spec_sha256'])]:
        inputs.read(dict(path=str(Path(binding['manifest']['path']).parent / name),
                         sha256=digest))
    for asset in manifest['assets']:
        inputs.read(dict(path=str(Path(binding['manifest']['path']).parent
                                  / asset['output_path']), sha256=asset['output_sha256']))
    inputs.evidence(spec)
    item = next((x for x in spec['items'] if x['id'] == binding['item_id']), None)
    answer = next((x for x in record['answers'] if x['item_id'] == binding['item_id']), None)
    if (not item or item['type'] != 'via_interface' or item['review_mode'] == 'context'
            or not answer or answer['verdict'] != 'accepted'
            or answer['checks'].get(binding['check_id']) is not True):
        raise ValueError('Sheet interface item/check is not accepted')
    observation = pointer(inputs.document(spec['sources'][binding['source_key']]),
                          binding['pointer'])
    for field, label in binding['fact_keys'].items():
        if item['facts'].get(label) != observation[field]:
            raise ValueError('Sheet displayed facts contradict the bound source record')
    return spec, observation


def interface_source(inputs, sample, adapter):
    """Adapt source approval only; keep counts and design adoption unapproved."""
    if (adapter.get('actor') != 'AI' or not adapter.get('reason')
            or adapter.get('observed_cut_count') is not None):
        raise ValueError('Invalid fixed-sheet interface adapter')
    claim = next((x for x in sample['interfaces'] if x['id'] == adapter['interface_id']), None)
    if claim is None:
        raise ValueError('Sheet adapter interface is not in the current sample')
    identity_spec, identity = checked_item(inputs, adapter['identity'])
    carrier_spec, carrier = checked_item(inputs, adapter['carrier'])
    required_facts = {'native_bounds', 'lower_metal_id'}
    if (not required_facts <= set(adapter['identity']['fact_keys'])
            or 'candidate_M3_native_path' not in adapter['carrier']['fact_keys']
            or identity.get('candidate_interface_id') != claim['id']
            or identity.get('AI_candidate_layer') != claim['layer']
            or identity.get('source_frame') != claim['source_frame']
            or identity.get('native_bounds') != claim['native_bounds']
            or identity.get('lower_metal_id') != claim['lower_metal_id']
            or identity.get('id') != adapter['identity']['item_id']
            or carrier.get('id') != identity.get('id')
            or claim['layer'] != 'V2' or claim['layer_pair'] != ['M2', 'M3']
            or carrier.get('known_V2_identity') is not True):
        raise ValueError('Sheet identity/source signature drift')
    row_label = carrier['proposed_M3_source_row'].removeprefix('WM3-')
    facts = next(x['facts'] for x in carrier_spec['items']
                 if x['id'] == adapter['carrier']['item_id'])
    if (facts.get(adapter['carrier_row_fact_key']) != row_label
            or facts.get(adapter['carrier_lower_fact_key']) != claim['lower_metal_id']):
        raise ValueError('Sheet carrier item belongs to another source row or metal')
    old_model = inputs.document(carrier_spec['sources'][adapter['model_source_key']])
    snapshot = inputs.document(sample['snapshot'])
    observations = inputs.document(identity_spec['sources'][adapter['identity']['source_key']])
    upper_source = inputs.document(carrier_spec['sources'][adapter['upper_source_key']])
    upper_row = next((r for r in upper_source['rows']
                      if r['id'] == carrier['proposed_M3_source_row']), None)
    if (old_model['source_photos'] != snapshot['source_photos']
            or observations['photo'] != snapshot['source_photos'][claim['source_frame']]
            or upper_source['source_photo'] != snapshot['source_photos']['m3']
            or not upper_row
            or upper_row.get('native_path') != carrier['candidate_M3_native_path']):
        raise ValueError('Sheet source photograph drift')
    features = {f['id']: f for fs in sample['features_by_layer'].values() for f in fs}
    originals = {f['id']: f for fs in old_model['objects_by_layer'].values() for f in fs}
    lower, upper = features[claim['lower_metal_id']], features[claim['upper_metal_id']]
    if (lower['native_path'] != originals[lower['id']]['native_path']
            or lower['source_frame'] != claim['source_frame'] or upper['source_frame'] != 'm3'):
        raise ValueError('Sheet source metal anchor drift')
    alias = carrier.get('existing_model_id_candidate')
    if alias:
        if (alias != upper['id'] or upper['native_path'] != originals[alias]['native_path']):
            raise ValueError('Sheet upper carrier alias/anchor drift')
    elif upper['native_path'] != carrier['candidate_M3_native_path']:
        raise ValueError('New sheet upper carrier moved away from its source path')
    source = copy.deepcopy(sample)
    source['interfaces'] = [{k: claim[k] for k in (
        'id', 'layer', 'layer_pair', 'source_frame', 'native_bounds',
        'lower_metal_id', 'upper_metal_id')}]
    decision = dict(interface_id=claim['id'], via_layer=claim['layer'],
                    lower_metal_id=lower['id'], upper_metal_id=upper['id'],
                    connection_confirmed=True)
    return source, decision, adapter['carrier']['decision']
