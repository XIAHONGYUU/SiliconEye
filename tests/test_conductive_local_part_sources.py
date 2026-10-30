"""Local M1 continuations preserve approvals and cannot lose their source ledger."""

import copy
import json
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from silicon_eye.conductive_workflow import prepare
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'benchmarks/corridor-m1-horizontal-branches-v1'


def read(path):
    return json.loads(path.read_text())


def write_ref(folder, name, document):
    path = folder / name
    path.write_text(json.dumps(document))
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


def test_horizontal_parts_preserve_all_old_anchors_cuts_and_reviewed_connections():
    model, report, sample, *_ = prepare(ROOT, read(BASE / 'request.json'))
    old = read(ROOT / 'docs/assets/corridor-m1-v1-reviewed-v2/work/model.json')
    before = old['objects_by_layer']['M1'][0]
    after = model['objects_by_layer']['M1'][0]
    assert after['native_path'] == before['native_path']
    assert Polygon(after['geometry']['outer_xy']).covers(Polygon(before['geometry']['outer_xy']))
    assert (Polygon(after['geometry']['outer_xy']).area
            > Polygon(before['geometry']['outer_xy']).area)
    for layer in ('V1', 'M2', 'V2', 'M3'):
        assert model['objects_by_layer'][layer] == old['objects_by_layer'][layer]
    assert model['reviewed_local_connections'] == old['reviewed_local_connections']
    assert model['candidate_interfaces'] == old['candidate_interfaces']
    assert model['visible_inventory_geometry'] == old['visible_inventory_geometry']
    assert report['changed_object_ids'] == ['C-M1-SPINE']
    assert report['audits']['local_part_source_candidates']['part_count'] == 2
    assert not report['audits']['local_part_source_candidates']['source_geometry_qualified']
    assert all(q['full_group_design_enclosure'] == 'CHECKED'
               for q in report['quality']['interface_geometry'])
    assert len(model['reviewed_local_connections']) == 11
    assert not model['net_edges'] and not model['geometry_adopted']
    assert sample['source_to_design_transform'] is None
    assert prepare(ROOT, read(BASE / 'next-request.json'))[0] == model


@pytest.mark.parametrize('mutation, message', [
    ('missing_row', 'omits or duplicates'),
    ('changed_bounds', 'geometry/source binding mismatch'),
    ('wrong_photo', 'geometry/source binding mismatch'),
    ('outside_scope', 'leaves its native source scope'),
    ('wrong_direction', 'principal direction mismatch'),
    ('human_promotion', 'explicit AI source evidence'),
    ('disconnected', 'join the existing conductor'),
    ('drop_on_resume', 'cannot disappear or change without a revision'),
    ('no_revision', 'cannot disappear or change without a revision'),
])
def test_source_binding_and_local_geometry_regressions_are_blocked(mutation, message):
    name = 'next-request.json' if mutation == 'drop_on_resume' else 'request.json'
    request = copy.deepcopy(read(BASE / name))
    sample = read(ROOT / request['sample']['path'])
    ledger = read(ROOT / sample['local_part_source_evidence']['path'])
    if mutation == 'missing_row':
        ledger['parts'].pop()
    elif mutation == 'changed_bounds':
        sample['features_by_layer']['M1'][0]['local_parts'][0]['bounds'][2] -= 5
    elif mutation == 'wrong_photo':
        snapshot = read(ROOT / sample['snapshot']['path'])
        ledger['parts'][0]['source_photo'] = snapshot['source_photos']['m2']
    elif mutation == 'outside_scope':
        ledger['parts'][0]['native_path'][-1][0] = 4000
    elif mutation == 'wrong_direction':
        ledger['parts'][0]['native_path'] = [[3143, 1960], [3143, 1980]]
    elif mutation == 'human_promotion':
        ledger['geometry_human_approved'] = True
    elif mutation == 'disconnected':
        sample['features_by_layer']['M1'][0]['local_parts'][0]['bounds'] = [400, 700, 450, 715]
    elif mutation == 'drop_on_resume':
        sample.pop('local_part_source_evidence')
    else:
        request.pop('revision_evidence')
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        folder = Path(temporary)
        if 'local_part_source_evidence' in sample:
            sample['local_part_source_evidence'] = write_ref(folder, 'ledger.json', ledger)
        request['sample'] = write_ref(folder, 'sample.json', sample)
        with pytest.raises(ValueError, match=message):
            prepare(ROOT, request)
