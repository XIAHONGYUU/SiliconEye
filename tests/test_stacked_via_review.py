"""Different via levels may overlap in XY; same-level spacing still applies."""
import copy
import json
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import box
from shapely.ops import unary_union

from silicon_eye.conductive_workflow import candidate_model, prepare
from silicon_eye.geometry_reconstruction import digest
from silicon_eye.metal_via_pilot import group_via_budget, interface_audit

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'benchmarks/stacked-via-review-v2'


def read(path):
    return json.loads(path.read_text())


@pytest.fixture(scope='module', params=['review-request-v1.json', 'independent-request-v1.json'])
def result(request):
    return request.param, prepare(ROOT, read(BASE / request.param))


def test_stacks_keep_approved_connections_and_actual_projected_cut_overlap(result):
    name, (model, report, sample, *_rest) = result
    pkg = 'review' if name.startswith('review') else 'independent'
    parent = read(ROOT / f'docs/assets/five-layer-geometry-v1/{pkg}/model.json')
    assert model['reviewed_local_connections'] == parent['reviewed_local_connections']
    assert model['objects_by_layer']['V1'] == parent['objects_by_layer']['V1']
    unions = {}
    for layer in ('V1', 'V2'):
        arrays = [o for o in model['objects_by_layer'][layer] if o.get('candidate_cut_bounds')]
        unions[layer] = unary_union([box(*bb) for o in arrays for bb in o['candidate_cut_bounds']])
    assert unions['V1'].intersection(unions['V2']).area > 0
    assert report['quality']['execution_checks'] == 'PASS'
    assert sample['via_budget']['minimum_cut_gap_px'] == 3
    if pkg == 'review':
        for layer in ('M1', 'M2', 'M3'):
            assert model['objects_by_layer'][layer] == parent['objects_by_layer'][layer]
        assert report['changed_object_ids'] == ['SUPPORT-J-M2-V2-M3-B1']
    else:
        assert report['changed_object_ids'] == ['IT1-M2-B', 'IT1-V2-B']
        row = next(r for r in report['quality']['interface_geometry'] if r['id'] == 'IT1-V2-B')
        assert row['human_cut_count'] == 6 and row['design_cut_count'] == 6
        assert row['geometry_acceptance'] == 'CANDIDATE_NOT_HUMAN_ACCEPTED'
        pad = next(o for o in model['objects_by_layer']['M2'] if o['id'] == 'IT1-M2-B')
        xs, ys = zip(*pad['geometry']['outer_xy'], strict=True)
        group = next(c for c in sample['interfaces'] if c['id'] == 'IT1-V2-B')['bounds']
        assert (group[2]-group[0]) / (max(xs)-min(xs)) > .85
        assert (group[3]-group[1]) / (max(ys)-min(ys)) > .80
    assert not model['geometry_adopted'] and not model['complete_network']


def test_exact_xy_stack_is_allowed_but_same_layer_coincident_cuts_fail():
    budget = dict(minimum_cut_width_px=6, minimum_cut_gap_px=3,
                  enclosure_px=1, cut_size_px=6, pitch_xy=[9, 9])
    metal = box(0, 0, 50, 50)
    for pair in [('M1', 'V1', 'M2'), ('M2', 'V2', 'M3')]:
        cut = dict(id=pair[1], layer=pair[1], layer_pair=[pair[0], pair[2]],
                   observation_id='separate-source-' + pair[1], bounds=[20, 20, 26, 26])
        assert interface_audit([cut], metal, metal, budget, pair)['status'] == 'PASS'
        duplicate = dict(cut, id='same-layer-duplicate')
        audit = interface_audit([cut, duplicate], metal, metal, budget, pair)
        assert any(e['reason'] == 'cut_gap_failed' for e in audit['errors'])


@pytest.mark.parametrize('params', [
    dict(cut_size_px=5, pitch_xy=[20, 23], basis='below minimum'),
    dict(cut_size_px=14, pitch_xy=[16, 23], basis='gap too small'),
    dict(cut_size_px=14, pitch_xy=[20, 23], enclosure_px=0, basis='weaken rule'),
])
def test_local_size_choice_cannot_weaken_hard_rules(params):
    sample = read(BASE / 'independent-observations-v1.json')
    cut = next(c for c in sample['interfaces'] if c['id'] == 'IT1-V2-B')
    cut['cut_array_candidate']['geometry_parameters'] = params
    with pytest.raises(ValueError, match='Array geometry parameters'):
        group_via_budget(cut, sample['via_budget'])


def test_same_layer_groups_still_reject_overlap_even_when_both_fit_the_metal():
    sample = read(BASE / 'independent-observations-v1.json')
    duplicate = copy.deepcopy(next(c for c in sample['interfaces'] if c['id'] == 'IT1-V2-B'))
    duplicate['id'] = 'second-same-V2-group'
    sample['interfaces'].append(duplicate)
    snapshot = read(ROOT / sample['snapshot']['path'])
    with pytest.raises(ValueError, match='Via support gap failed'):
        candidate_model(sample, snapshot)


def test_geometry_count_feedback_cannot_be_assigned_to_another_carrier():
    request = read(BASE / 'independent-request-v1.json')
    sample = read(ROOT / request['sample']['path'])
    cut = next(c for c in sample['interfaces'] if c['id'] == 'IT1-V2-B')
    review = read(ROOT / cut['count_evidence']['path'])
    review['scope_signature']['lower_metal_id'] = 'IT1-M2-A'
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as directory:
        directory = Path(directory)
        review_path = directory / 'review.json'
        review_path.write_text(json.dumps(review))
        cut['count_evidence'] = dict(path=str(review_path.relative_to(ROOT)),
                                     sha256=digest(review_path))
        sample_path = directory / 'sample.json'
        sample_path.write_text(json.dumps(sample))
        request['sample'] = dict(path=str(sample_path.relative_to(ROOT)),
                                 sha256=digest(sample_path))
        with pytest.raises(ValueError, match='Geometry feedback count belongs to another'):
            prepare(ROOT, request)
