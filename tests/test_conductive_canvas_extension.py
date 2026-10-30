"""Bottom-only canvas growth is atomic and cannot translate or reapprove existing data."""

import copy
import json
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import Polygon, box

from silicon_eye.conductive_workflow import prepare
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'benchmarks/BR-R-return-work-v3'


def read(path):
    return json.loads(path.read_text())


def write_ref(folder, name, value):
    path = folder / name
    path.write_text(json.dumps(value))
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


def test_canvas_growth_preserves_every_existing_object_site_and_review():
    model, report, sample, *_ = prepare(ROOT, read(BASE / 'canvas-only-request.json'))
    before = read(ROOT / 'docs/assets/B-short-finger-reviewed-v2/work/model.json')
    assert model['canvas_wh'] == [780, 1440]
    assert model['objects_by_layer'] == before['objects_by_layer']
    assert model['reviewed_local_connections'] == before['reviewed_local_connections']
    assert model['candidate_interfaces'] == before['candidate_interfaces']
    assert model['review_sources'] == before['review_sources']
    old_sample = read(ROOT / before['sample']['path'])
    old_sample['canvas_wh'] = [780, 1440]
    assert sample == old_sample
    audit = report['audits']['canvas_extension']
    assert audit['from_canvas_wh'] == [780, 1240] and audit['to_canvas_wh'] == [780, 1440]
    assert audit['all_existing_records_exact'] and not audit['native_source_scope_changed']
    assert len(model['canvas_extension_history']) == 1
    assert not report['changed_object_ids'] and not report['added_metal_ids']
    assert not model['net_edges'] and not model['geometry_adopted']


@pytest.mark.parametrize('mutation', [
    'undeclared', 'width', 'shrink', 'fractional', 'origin', 'scale', 'translation',
    'wrong_parent', 'from_extent', 'geometry', 'source_metadata', 'review',
    'budget', 'frames', 'no_parent', 'stale', 'mixed_revision',
])
def test_growth_rejects_silent_or_mixed_changes(mutation):
    request = copy.deepcopy(read(BASE / 'canvas-only-request.json'))
    sample = read(ROOT / request['sample']['path'])
    evidence = read(ROOT / request['canvas_extension_evidence']['path'])
    if mutation == 'undeclared':
        request.pop('canvas_extension_evidence')
    elif mutation == 'width':
        sample['canvas_wh'][0] = 800
        evidence['to_canvas_wh'] = sample['canvas_wh']
    elif mutation == 'shrink':
        sample['canvas_wh'][1] = 1239
        evidence['to_canvas_wh'] = sample['canvas_wh']
    elif mutation == 'fractional':
        sample['canvas_wh'][1] = 1440.5
        evidence['to_canvas_wh'] = sample['canvas_wh']
    elif mutation == 'origin':
        evidence['origin_xy'] = [0, 200]
    elif mutation == 'scale':
        evidence['scale_xy'] = [1, 0.9]
    elif mutation == 'translation':
        evidence['translation_xy'] = [0, 200]
    elif mutation == 'wrong_parent':
        evidence['parent']['sha256'] = '0' * 64
    elif mutation == 'from_extent':
        evidence['from_canvas_wh'] = [780, 1200]
    elif mutation == 'geometry':
        sample['features_by_layer']['M1'][0]['design_width'] = 13
    elif mutation == 'source_metadata':
        sample['features_by_layer']['M1'][0]['role'] = 'silently_reclassified'
    elif mutation == 'review':
        old = read(ROOT / 'docs/assets/B-short-finger-reviewed-v2/work/model.json')
        request['reviews'] = [old['review_sources'][0]]
    elif mutation == 'budget':
        sample['metal_budget']['unit'] = 'different_units'
    elif mutation == 'frames':
        request['frames'] = list(reversed(request['frames']))
    elif mutation == 'no_parent':
        request.pop('parent')
    elif mutation == 'stale':
        sample['canvas_wh'] = [780, 1240]
    else:
        sample = read(ROOT / 'benchmarks/BR-R-return-reviewed-v2/final-state-proposal-sample.json')
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        folder = Path(temporary)
        if 'canvas_extension_evidence' in request:
            request['canvas_extension_evidence'] = write_ref(folder, 'evidence.json', evidence)
        request['sample'] = write_ref(folder, 'sample.json', sample)
        with pytest.raises(ValueError):
            prepare(ROOT, request)


def test_three_transactions_preserve_vias_and_local_gaps_in_the_extended_canvas():
    model, report, sample, *_ = prepare(ROOT, read(BASE / 'request.json'))
    before = read(ROOT / 'docs/assets/B-short-finger-reviewed-v2/work/model.json')
    for layer in ('M2', 'M3', 'V1', 'V2'):
        assert model['objects_by_layer'][layer] == before['objects_by_layer'][layer]
    assert model['objects_by_layer']['M1'][1] == before['objects_by_layer']['M1'][1]
    assert model['reviewed_local_connections'] == before['reviewed_local_connections']
    assert model['candidate_interfaces'] == before['candidate_interfaces']
    old_feature = read(ROOT / before['sample']['path'])['features_by_layer']['M1'][0]
    feature = sample['features_by_layer']['M1'][0]
    assert feature['native_path'] == old_feature['native_path']
    assert feature['local_parts'][:4] == old_feature['local_parts']
    objects = {o['id']: o for o in model['objects_by_layer']['M1']}
    main = Polygon(objects['C-M1-SPINE']['geometry']['outer_xy'])
    assert main.covers(Polygon(before['objects_by_layer']['M1'][0]['geometry']['outer_xy']))
    brr = box(136, 1014, 144, 1339)
    for key in ('BRR-L1-CANDIDATE', 'BRR-L2-CANDIDATE'):
        assert brr.distance(Polygon(objects[key]['geometry']['outer_xy'])) == 26
    assert sum(len(v['candidate_cut_bounds']) for k in ('V1', 'V2')
               for v in model['objects_by_layer'][k]) == 46
    assert report['object_counts'] == dict(M1=4, V1=2, M2=8, V2=9, M3=22)
    assert len(model['canvas_extension_history']) == 1
    assert sample['source_to_design_transform'] is None
    assert not model['complete_network'] and not model['net_edges']
    assert prepare(ROOT, read(BASE / 'next-request.json'))[0] == model
