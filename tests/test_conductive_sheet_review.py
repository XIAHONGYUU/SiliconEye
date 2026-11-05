"""Fixed-sheet acceptance must not lose source scope or create count approval."""

import copy
import json
import tempfile
from pathlib import Path

import pytest

from silicon_eye.conductive_sheet_review import interface_source
from silicon_eye.conductive_workflow import prepare
from silicon_eye.geometry_reconstruction import digest
from silicon_eye.review_package import Inputs

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'benchmarks/w34-joint-geometry-v1'


def read(path):
    return json.loads(path.read_text())


@pytest.mark.parametrize('site', ['S01', 'S02', 'S03', 'S04'])
def test_actual_archived_sheet_preserves_identity_and_carrier_without_count_truth(site):
    sample = read(BASE / 'S3-interface-sample.json')
    adapter = read(BASE / f'{site}-sheet-adapter.json')
    source, verdict, authority = interface_source(Inputs(ROOT), sample, adapter)
    assert verdict['connection_confirmed'] is True
    assert verdict['interface_id'] == adapter['interface_id']
    assert authority == adapter['carrier']['decision']
    assert source['interfaces'][0]['native_bounds'] == next(
        c['native_bounds'] for c in sample['interfaces'] if c['id'] == adapter['interface_id'])
    assert 'observed_cut_count' not in verdict and 'geometry_adopted' not in verdict
    assert source['features_by_layer'] == sample['features_by_layer']


@pytest.mark.parametrize('mutation', [
    'actor', 'count', 'native_bounds', 'lower_anchor', 'upper_alias', 'new_upper_anchor',
    'missing_required_fact', 'wrong_displayed_fact', 'context_item',
    'uncertain_identity', 'uncertain_carrier', 'wrong_build',
])
def test_sheet_adapter_rejects_source_or_authority_drift(mutation):
    sample = read(BASE / 'S3-interface-sample.json')
    adapter = read(BASE / 'S01-sheet-adapter.json')
    claim = next(c for c in sample['interfaces'] if c['id'] == adapter['interface_id'])
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        folder = Path(temporary)
        if mutation == 'actor':
            adapter['actor'] = 'human'
        elif mutation == 'count':
            adapter['observed_cut_count'] = 2
        elif mutation == 'native_bounds':
            claim['native_bounds'][0] += 1
        elif mutation == 'lower_anchor':
            next(f for f in sample['features_by_layer']['M2']
                 if f['id'] == claim['lower_metal_id'])['native_path'][0][0] += 1
        elif mutation == 'upper_alias':
            claim['upper_metal_id'] = 'C-M3-M05'
        elif mutation == 'new_upper_anchor':
            adapter = read(BASE / 'S04-sheet-adapter.json')
            next(f for f in sample['features_by_layer']['M3']
                 if f['id'] == 'W34-M3-R03')['native_path'][0][0] += 1
        elif mutation == 'missing_required_fact':
            adapter['identity']['fact_keys'].pop('native_bounds')
        elif mutation == 'wrong_displayed_fact':
            adapter['identity']['fact_keys']['native_bounds'] = 'missing_fact'
        elif mutation == 'context_item':
            adapter['carrier']['item_id'] = 'CTX-V2-IDENTITY'
        else:
            part = 'identity' if mutation == 'uncertain_identity' else 'carrier'
            record = read(ROOT / adapter[part]['decision']['path'])
            if mutation == 'wrong_build':
                record['build_id'] = 'another-submission'
            else:
                next(a for a in record['answers']
                     if a['item_id'] == adapter[part]['item_id'])['verdict'] = 'uncertain'
                for question in record['questions']:
                    question['verdict'] = 'uncertain'
            path = folder / 'decision.json'
            path.write_text(json.dumps(record))
            adapter[part]['decision'] = dict(path=str(path.relative_to(ROOT)),
                                             sha256=digest(path))
        with pytest.raises(ValueError):
            interface_source(Inputs(ROOT), sample, adapter)


def test_four_sheet_connections_resume_without_changing_old_sites_or_metal():
    request = read(BASE / 'S3-interface-request.json')
    parent = read(ROOT / 'docs/assets/w34-joint-geometry-v1/S2-joint-metals/model.json')
    model, report, *_ = prepare(ROOT, request)
    for layer in ('M1', 'M2', 'M3', 'V1'):
        assert model['objects_by_layer'][layer] == parent['objects_by_layer'][layer]
    assert model['objects_by_layer']['V2'][:-4] == parent['objects_by_layer']['V2']
    assert model['reviewed_local_connections'][:30] == parent['reviewed_local_connections']
    assert len(model['reviewed_local_connections']) == 34
    assert all(c['physical_cut_count'] is None for c in model['reviewed_local_connections'][30:])
    assert report['changed_object_ids'] == []
    assert not model['net_edges'] and not model['geometry_adopted']
    resumed = copy.deepcopy(request)
    resumed.pop('added_interface_ids')
    resumed.pop('interface_extension_evidence')
    resumed['reviews'] = []
    path = ROOT / 'docs/assets/w34-joint-geometry-v1/S3-joint-work/manifest.json'
    resumed['parent'] = dict(path=str(path.relative_to(ROOT)), sha256=digest(path))
    assert prepare(ROOT, resumed)[0] == model
