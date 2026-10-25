"""Preserve reviewed interfaces while migrating AI-observed whole via groups."""
import copy
import json
from pathlib import Path

import pytest

from silicon_eye.conductive_workflow import prepare
from silicon_eye.metal_via_pilot import observed_array_audit

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'benchmarks/five-layer-geometry-v1'


def read(path):
    return json.loads(path.read_text())


@pytest.fixture(scope='module')
def medium():
    return prepare(ROOT, read(BASE / 'review-request-v1.json'))


def test_complete_chain_keeps_approvals_skeletons_and_unrelated_objects(medium):
    model, report, sample, _, _ = medium
    before = read(ROOT / 'docs/assets/medium-v2-array-v1/review/model.json')
    old = {o['id']: o for os in before['objects_by_layer'].values() for o in os}
    new = {o['id']: o for os in model['objects_by_layer'].values() for o in os}
    assert {k for k in old if old[k] != new[k]} == {
        'M1-P08', 'SUPPORT-J-M1-P08-V1-M2-J01'}
    for key in ('reviewed_local_connections', 'accepted_structural_groups', 'branch'):
        assert model[key] == before[key]
    previous = read(ROOT / 'benchmarks/medium-v2-array-v1/observations-v1.json')
    for layer, features in sample['features_by_layer'].items():
        for old_f, new_f in zip(previous['features_by_layer'][layer], features, strict=True):
            for key in ('native_path', 'design_path', 'design_width'):
                assert new_f[key] == old_f[key]
    q = report['quality']
    assert q['explicit_design_array_count'] == 2
    assert len(q['proxy_interface_ids']) == 9
    v1 = next(r for r in q['interface_geometry']
              if r['id'] == 'SUPPORT-J-M1-P08-V1-M2-J01')
    assert v1['human_cut_count'] is None and v1['design_cut_count'] == 9
    assert q['source_qualified_array_count'] == 0
    assert not model['geometry_adopted'] and not model['complete_network']
    assert not model['net_edges']


def test_independent_transfer_keeps_wide_b_carrier_and_all_metals():
    model, report, *_ = prepare(ROOT, read(BASE / 'independent-request-v1.json'))
    before = read(ROOT / 'docs/assets/conductive-quality-review-v1/review-independent/model.json')
    for layer in ('M1', 'M2', 'M3', 'V1'):
        assert model['objects_by_layer'][layer] == before['objects_by_layer'][layer]
    assert model['reviewed_local_connections'] == before['reviewed_local_connections']
    assert report['changed_object_ids'] == ['IT1-V2-B']
    assert report['quality']['explicit_design_array_count'] == 2
    assert not report['quality']['proxy_interface_ids']
    row = next(r for r in report['quality']['interface_geometry'] if r['layer'] == 'V2')
    assert row['human_cut_count'] is None and row['design_cut_count'] == 6
    assert row['lower_metal_id'] == 'IT1-M2-B'
    assert report['audits']['array_source_observations']['IT1-V2-B'][
        'status'] == 'BOUND_AI_OBSERVATION_NOT_HUMAN_COUNT'


@pytest.mark.parametrize('change', ['wrong_photo', 'wrong_interface', 'human_count',
                                    'missing_site', 'outside', 'duplicate', 'row_order'])
def test_ai_observation_cannot_gain_authority_or_hide_whole_group_errors(change):
    sample = read(BASE / 'observations-v1.json')
    claim = next(c for c in sample['interfaces']
                 if c['id'] == 'SUPPORT-J-M1-P08-V1-M2-J01')
    evidence = read(ROOT / claim['array_source_evidence']['path'])
    photo = copy.deepcopy(evidence['source_photo'])
    if change == 'wrong_photo':
        evidence['source_photo']['sha256'] = '0' * 64
    elif change == 'wrong_interface':
        evidence['interface_id'] = 'another-via'
    elif change == 'human_count':
        evidence['count_status'] = 'human_confirmed'
    elif change == 'missing_site':
        evidence['sites'].pop()
    elif change == 'outside':
        evidence['sites'][0]['native_xy'] = [1, 1]
    elif change == 'duplicate':
        evidence['sites'][1] = copy.deepcopy(evidence['sites'][0])
    else:
        evidence['sites'][0]['native_xy'], evidence['sites'][1]['native_xy'] = (
            evidence['sites'][1]['native_xy'], evidence['sites'][0]['native_xy'])
    with pytest.raises(ValueError, match='AI array'):
        observed_array_audit(evidence, claim, photo, claim['reviewed_id'], 'V1')
