"""Migrate the reviewed J 3x4 V2 array without stretching either metal carrier."""
import copy
import json
import tempfile
from pathlib import Path

import pytest

from silicon_eye.conductive_medium import review_page
from silicon_eye.conductive_workflow import page, prepare
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / 'benchmarks/medium-v2-array-v1/review-request-v1.json'
GROUP = 'SUPPORT-J-M2-V2-M3-B1'


def read(path):
    return json.loads(path.read_text())


@pytest.fixture(scope='module')
def result():
    return prepare(ROOT, read(REQUEST))


def test_complete_array_preserves_all_metals_approvals_and_other_supports(result):
    model, report, _, _, _ = result
    parent = read(ROOT / 'docs/assets/conductive-quality-review-v1/review-medium/model.json')
    old = {o['id']: o for os in parent['objects_by_layer'].values() for o in os}
    new = {o['id']: o for os in model['objects_by_layer'].values() for o in os}
    assert old.keys() == new.keys()
    assert [k for k in old if old[k] != new[k]] == [GROUP]
    for key in ('reviewed_local_connections', 'accepted_structural_groups', 'branch'):
        assert model[key] == parent[key]
    assert report['changed_object_ids'] == [GROUP]
    assert not model['geometry_adopted'] and not model['complete_network']
    assert report['object_counts'] == dict(M1=9, V1=5, M2=8, V2=6, M3=5)


def test_twelve_cuts_pass_enclosure_and_fact_migration_without_source_geometry_promotion(result):
    model, report, _, _, _ = result
    q = report['quality']
    assert len(q['proxy_interface_ids']) == 10 and q['explicit_design_array_count'] == 1
    fact = model['inherited_group_facts'][0]
    assert fact['rows'] == 3 and fact['columns'] == 4 and fact['cut_count'] == 12
    assert fact['geometry_ported']
    audit = report['audits']['explicit_array_audits'][GROUP]
    assert audit['status'] == 'PASS' and audit['candidate_cut_count'] == 12
    assert q['source_qualified_array_count'] == 0
    assert not q['readiness']['canonical_geometry_adoption']


def test_both_review_renderers_draw_twelve_separate_cuts(result):
    model, report, sample, _, _ = result
    unified = page(model, report, sample, read(REQUEST), ROOT / 'runs', ROOT)
    legacy = review_page(model, report['audits'], sample)
    for content in (unified, legacy):
        assert content.count('data-object="'+GROUP+'/C') == 12
        assert 'data-object="'+GROUP+'"' not in content


@pytest.mark.parametrize('change,reason', [
    ('three_by_three', 'reviewed rows/columns/count'),
    ('rotated_four_by_three', 'reviewed rows/columns/count'),
    ('one_box', 'entire array'),
    ('narrow_metal', 'enclosure gate'),
    ('wrong_photo', 'Via source frame mismatch'),
    ('different_group', 'exactly matched reviewed group'),
])
def test_array_cannot_bypass_known_shape_whole_group_or_carriers(change, reason):
    request = read(REQUEST)
    sample = read(ROOT / request['sample']['path'])
    claim = next(c for c in sample['interfaces'] if c['id'] == GROUP)
    if change == 'three_by_three':
        claim['cut_array_candidate']['columns'] = 3
    elif change == 'rotated_four_by_three':
        claim['cut_array_candidate'].update(rows=4, columns=3)
    elif change == 'one_box':
        claim['support_bounds'] = [1377, 167, 1383, 173]
    elif change == 'narrow_metal':
        next(f for f in sample['features_by_layer']['M2']
             if f['id'] == 'M2-J01')['design_width'] = 30
    elif change == 'wrong_photo':
        claim['source_frame'] = 'm1'
    elif change == 'different_group':
        claim['reviewed_id'] = 'N2-M2-V2-M3-B1'
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as directory:
        path = Path(directory) / 'sample.json'
        path.write_text(json.dumps(sample))
        request = copy.deepcopy(request)
        request['sample'] = dict(path=str(path.relative_to(ROOT)), sha256=digest(path))
        with pytest.raises(ValueError, match=reason):
            prepare(ROOT, request)
