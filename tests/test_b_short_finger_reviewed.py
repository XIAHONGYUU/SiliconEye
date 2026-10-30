"""Three reviewed local contacts do not approve neighboring fingers or global isolation."""

import json
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from silicon_eye.conductive_workflow import prepare
from silicon_eye.geometry_reconstruction import digest
from silicon_eye.review_package import Inputs

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'benchmarks/B-short-finger-reviewed-v2'


def read(path):
    return json.loads(path.read_text())


def write_ref(folder, sample):
    path = folder / 'sample.json'
    path.write_text(json.dumps(sample))
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


def test_reviewed_local_contacts_keep_old_source_anchors_vias_and_unknowns():
    model, report, sample, *_ = prepare(ROOT, read(BASE / 'request.json'))
    old = read(ROOT / 'docs/assets/corridor-m1-horizontal-branches-v1/work/model.json')
    for layer in ('M2', 'M3', 'V1', 'V2'):
        assert model['objects_by_layer'][layer] == old['objects_by_layer'][layer]
    assert model['reviewed_local_connections'] == old['reviewed_local_connections']
    assert model['candidate_interfaces'] == old['candidate_interfaces']
    spine, strip = model['objects_by_layer']['M1']
    assert spine['id'] == 'C-M1-SPINE' and strip['id'] == 'BF25-M1-CANDIDATE'
    assert spine['native_path'] == old['objects_by_layer']['M1'][0]['native_path']
    expanded = Polygon(spine['geometry']['outer_xy'])
    assert expanded.covers(Polygon(old['objects_by_layer']['M1'][0]['geometry']['outer_xy']))
    separate = Polygon(strip['geometry']['outer_xy'])
    assert expanded.distance(separate) == 21
    assert report['added_metal_ids'] == ['BF25-M1-CANDIDATE']
    assert report['changed_object_ids'] == []
    assert len(sample['features_by_layer']['M1'][0]['local_parts']) == 4
    assert all(c['physical_cut_count'] is None for c in model['reviewed_local_connections'])
    assert sample['source_to_design_transform'] is None
    assert not model['geometry_adopted'] and not model['net_edges']


def test_answer_is_bound_to_only_three_original_source_observations():
    human = Inputs(ROOT).human(dict(path=str((BASE / 'human-review.json').relative_to(ROOT)),
                                   sha256=digest(BASE / 'human-review.json')))
    question = Inputs(ROOT).document(human['sources']['submitted_request'])
    source = Inputs(ROOT).document(question['observations'])
    originals = {o['id']: o for o in source['finger_observations']}
    assert question['answer'] is None  # Original submitted question stays frozen.
    assert human['statement'] == '这个局部区分正确'
    assert [d['observation_id'] for d in human['decisions']] == question['scope_finger_ids']
    assert question['scope_finger_ids'] == ['BF24', 'BF25', 'BF26']
    for d in human['decisions']:
        observation = originals[d['observation_id']]
        assert d['source_window'] == observation['source_window']
        assert d['source_photo'] == observation['source_photo']
        assert d['local_contact_to_BU'] == (d['observation_id'] != 'BF25')
        assert d['local_contact_to_L1'] is (False if d['observation_id'] == 'BF25' else None)
        assert d['local_contact_to_L2'] is (False if d['observation_id'] == 'BF25' else None)
        assert not d['exact_geometry_human_approved']
        assert d['physical_cut_count'] is None and d['global_same_net_with_BU'] is None
    overlay = read(BASE / 'source-review-state.json')
    assert len(overlay['unchanged_candidate_ids']) == 23
    assert set(overlay['reviewed_ids']).isdisjoint(overlay['unchanged_candidate_ids'])


def test_reconstructing_a_bridge_for_bf25_is_blocked_by_same_layer_spacing():
    request = read(BASE / 'request.json')
    sample = read(ROOT / request['sample']['path'])
    sample['features_by_layer']['M1'][1]['design_path'][0][1] = 1018
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        request['sample'] = write_ref(Path(temporary), sample)
        with pytest.raises(ValueError, match='Metal geometry gate failed'):
            prepare(ROOT, request)


def test_dropping_one_positive_finger_cannot_keep_the_source_ledger_pass():
    request = read(BASE / 'request.json')
    sample = read(ROOT / request['sample']['path'])
    sample['features_by_layer']['M1'][0]['local_parts'].pop()
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        request['sample'] = write_ref(Path(temporary), sample)
        with pytest.raises(ValueError, match='omits or duplicates geometry'):
            prepare(ROOT, request)


def test_three_contact_revision_resumes_without_new_via_approvals():
    expected = read(ROOT / 'docs/assets/B-short-finger-reviewed-v2/work/model.json')
    model, report, *_ = prepare(ROOT, read(BASE / 'next-request.json'))
    assert model == expected
    assert not report['changed_object_ids']
    assert not model['pending_interface_ids']
    assert len(model['reviewed_local_connections']) == 11
    assert len(model['objects_by_layer']['M1']) == 2
