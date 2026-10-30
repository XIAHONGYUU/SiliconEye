"""A native M1 entry answer is scoped identity/carrier evidence, never a geometry license."""

import copy
import json
import tempfile
from pathlib import Path

import pytest

from silicon_eye.conductive_workflow import (
    inventory_geometry_audit,
    native_entry_review_source,
    prepare,
)
from silicon_eye.geometry_reconstruction import digest
from silicon_eye.review_package import Inputs

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'benchmarks/corridor-m1-v1-reviewed-v2'


def read(path):
    return json.loads(path.read_text())


def temporary_ref(folder, name, value):
    path = folder / name
    path.write_text(json.dumps(value))
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


def test_native_entries_preserve_old_geometry_counts_reviews_and_replay():
    model, report, sample, *_ = prepare(ROOT, read(BASE / 'request.json'))
    previous = read(ROOT / 'docs/assets/corridor-0506-joint-reviewed-v3/work/model.json')
    for layer in ('M2', 'M3', 'V2'):
        assert model['objects_by_layer'][layer] == previous['objects_by_layer'][layer]
    assert model['reviewed_local_connections'][:9] == previous['reviewed_local_connections']
    assert model['candidate_interfaces'][:9] == previous['candidate_interfaces']
    assert report['object_counts'] == dict(M1=1, V1=2, M2=8, V2=9, M3=22)
    assert not model['pending_interface_ids']
    assert not model['net_edges'] and not model['complete_network']
    assert sample['source_to_design_transform'] is None
    assert all(c['physical_cut_count'] is None for c in model['reviewed_local_connections'])
    new_quality = report['quality']['interface_geometry'][:2]
    assert all(q['design_cut_count'] == 2 and q['human_cut_count'] is None
               and q['source_array_geometry'] == 'NOT_QUALIFIED'
               and q['full_group_design_enclosure'] == 'CHECKED' for q in new_quality)
    assert report['quality']['visible_inventory_geometry']['mapped_geometry_count'] == 31
    assert prepare(ROOT, read(BASE / 'next-request.json'))[0] == model


@pytest.mark.parametrize('mutation', [
    'count', 'geometry', 'wrong_layer', 'macro_only', 'changed_scope',
    'changed_carrier', 'changed_statement', 'source_frame', 'unrelated_m1',
])
def test_entry_adapter_rejects_answer_scope_expansion(mutation):
    request = read(BASE / 'request.json')
    sample = read(ROOT / request['sample']['path'])
    claim = copy.deepcopy(sample['interfaces'][-2])
    review = read(ROOT / request['reviews'][0]['path'])
    question = read(ROOT / review['sources']['submitted_request']['path'])
    batch = read(ROOT / review['sources']['batch_human_review']['path'])
    answer = batch['decisions'][0]
    if mutation == 'count':
        answer['physical_cut_count'] = 2
    elif mutation == 'geometry':
        answer['design_geometry_human_approved'] = True
    elif mutation == 'wrong_layer':
        answer['via_layer'] = 'V2'
    elif mutation == 'macro_only':
        answer['V1_present'] = None
    elif mutation == 'changed_scope':
        claim['native_bounds'][0] += 1
    elif mutation == 'changed_carrier':
        claim['upper_metal_id'] = 'RT-M2-R02'
    elif mutation == 'changed_statement':
        review['statement'] = 'Only macro position'
    elif mutation == 'source_frame':
        claim['source_frame'] = 'm2'
    else:
        sample['features_by_layer']['M1'][0]['native_path'] = [[100, 100], [100, 200]]
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        review['sources']['batch_human_review'] = temporary_ref(
            Path(temporary), 'human.json', batch)
        with pytest.raises(ValueError, match='original identity/carrier scope'):
            native_entry_review_source(Inputs(ROOT), sample, review, question, claim)


@pytest.mark.parametrize('mutation', [
    'duplicate_id', 'reassigned_metal', 'wrong_photo', 'outside_scope', 'empty',
])
def test_inventory_supplement_cannot_replace_base_or_invent_source_scope(mutation):
    request = read(BASE / 'request.json')
    sample = read(ROOT / request['sample']['path'])
    supplement = read(ROOT / sample['supplemental_visible_inventories'][0]['path'])
    snapshot = read(ROOT / sample['snapshot']['path'])
    if mutation == 'duplicate_id':
        base_inventory = read(ROOT / sample['visible_inventory']['path'])
        supplement['metal_observations'][0]['id'] = base_inventory['metal_observations'][0]['id']
    elif mutation == 'reassigned_metal':
        supplement['inventory_geometry_mapping'][0]['metal_id'] = 'RT-M2-R01'
    elif mutation == 'wrong_photo':
        supplement['scope']['frames']['m1']['photo'] = snapshot['source_photos']['m2']
    elif mutation == 'outside_scope':
        supplement['metal_observations'][0]['native_path'][0][0] = 100
    else:
        supplement['metal_observations'] = []
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        sample['supplemental_visible_inventories'] = [
            temporary_ref(Path(temporary), 'supplement.json', supplement)]
        with pytest.raises(ValueError):
            inventory_geometry_audit(Inputs(ROOT), sample, snapshot)


def test_entire_new_group_must_fit_without_weakening_old_enclosure_budget():
    request = read(BASE / 'request.json')
    sample = read(ROOT / request['sample']['path'])
    sample['interfaces'][-2]['bounds'] = [194, 275, 200, 290]
    sample['interfaces'][-2]['cut_array_candidate']['origin_xy'] = [194, 275]
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        request['sample'] = temporary_ref(Path(temporary), 'sample.json', sample)
        with pytest.raises(ValueError, match='Via enclosure/spacing gate failed'):
            prepare(ROOT, request)


def test_resume_cannot_rewrite_an_existing_supplement_even_with_identical_geometry():
    request = read(BASE / 'next-request.json')
    sample = read(ROOT / request['sample']['path'])
    supplement = read(ROOT / sample['supplemental_visible_inventories'][0]['path'])
    supplement['reason'] = 'Unscoped replacement of the previously bound inventory'
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        folder = Path(temporary)
        sample['supplemental_visible_inventories'] = [
            temporary_ref(folder, 'supplement.json', supplement)]
        request['sample'] = temporary_ref(folder, 'sample.json', sample)
        with pytest.raises(ValueError, match='append-only with added metal'):
            prepare(ROOT, request)
