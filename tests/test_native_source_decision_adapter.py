"""Human native scope must survive an AI adapter without approving geometry/counts."""
import copy
import json
import tempfile
from pathlib import Path

import pytest

from silicon_eye.conductive_workflow import apply_reviews, prepare
from silicon_eye.geometry_reconstruction import digest
from silicon_eye.review_package import Inputs

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'benchmarks/left-bu-joint-work-v3'


def read(path):
    return json.loads(path.read_text())


def write(folder, name, value):
    path = folder / name
    path.write_text(json.dumps(value))
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


@pytest.mark.parametrize('key', ['LEFT-BU-V1-CANDIDATE', 'LEFT-M2-A-V2-U', 'LEFT-M2-A-V2-D'])
def test_adapter_retains_actual_human_authority_and_unknown_physical_count(key):
    sample = read(BASE / 'S4-interfaces-sample.json')
    reference = dict(path=f'benchmarks/left-bu-joint-work-v3/{key}-review-adapter.json',
                     sha256=digest(BASE / (key + '-review-adapter.json')))
    adapter = read(ROOT / reference['path'])
    approved, _ = apply_reviews(Inputs(ROOT), sample, [reference])
    assert approved[0]['human_review'] == adapter['sources']['original_human_review']
    assert approved[0]['physical_cut_count'] is None
    assert approved[0]['connection_confirmed'] is True


@pytest.mark.parametrize('mutation', ['statement', 'count', 'actor', 'scope', 'question',
                                    'carrier', 'source_alias', 'decision', 'photo', 'native_part'])
def test_adapter_rejects_scope_authority_or_source_mapping_drift(mutation):
    key = 'LEFT-BU-V1-CANDIDATE'
    sample = copy.deepcopy(read(BASE / 'S4-interfaces-sample.json'))
    adapter = copy.deepcopy(read(BASE / (key + '-review-adapter.json')))
    binding = read(ROOT / adapter['sources']['submitted_request']['path'])
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        folder = Path(temporary)
        if mutation == 'statement':
            adapter['statement'] = 'A different answer'
        elif mutation == 'count':
            adapter['observed_cut_count'] = 10
        elif mutation == 'actor':
            adapter['actor'] = 'human'
        elif mutation == 'scope':
            binding['scope_signature']['native_bounds'][1] += 1
        elif mutation == 'question':
            binding['question_id'] = 'not submitted'
        elif mutation == 'carrier':
            binding['carrier_bindings']['upper']['model_id'] = 'RT-M2-R01'
        elif mutation == 'source_alias':
            binding['carrier_bindings']['lower']['source_id'] = 'other M1'
        elif mutation == 'decision':
            adapter['decisions']['connection_confirmed'] = False
        elif mutation == 'photo':
            scope = read(ROOT / binding['scope_source']['path'])
            scope['photos']['m1'] = scope['photos']['m2']
            binding['scope_source'] = write(folder, 'scope.json', scope)
        else:
            ledger = read(ROOT / sample['local_part_source_evidence']['path'])
            row = next(r for r in ledger['parts'] if r['part_id'] == 'LEFT-BU-UP')
            row['native_path'][0][0] += 1
            sample['local_part_source_evidence'] = write(folder, 'ledger.json', ledger)
        adapter['sources']['submitted_request'] = write(folder, 'binding.json', binding)
        reference = write(folder, 'adapter.json', adapter)
        with pytest.raises(ValueError):
            apply_reviews(Inputs(ROOT), sample, [reference])


def test_left_joint_resume_preserves_all14_decisions_and_old46_centers():
    model, report, *_ = prepare(ROOT, read(BASE / 'next-request.json'))
    assert len(model['reviewed_local_connections']) == 14
    assert not model['pending_interface_ids']
    assert len(report['audits']['preserved_via_centers']) == 11
    assert sum(len(v['design_centers_xy']) for v in report['audits'][
        'preserved_via_centers'].values()) == 46
    assert all(c['physical_cut_count'] is None for c in model['reviewed_local_connections'])
    assert not model['net_edges'] and not model['geometry_adopted']


@pytest.mark.parametrize('wrong_side', ['decision_pointer', 'carrier_pointer'])
def test_upper_answer_cannot_be_replaced_by_lower_answer_or_lower_bus(wrong_side):
    sample = read(BASE / 'S4-interfaces-sample.json')
    adapter = copy.deepcopy(read(BASE / 'LEFT-M2-A-V2-U-review-adapter.json'))
    binding = read(ROOT / adapter['sources']['submitted_request']['path'])
    if wrong_side == 'decision_pointer':
        binding['decision_pointer'] = '/decisions/1'
    else:
        other = read(BASE / 'LEFT-M2-A-V2-D-source-binding.json')
        binding['carrier_bindings']['upper'] = other['carrier_bindings']['upper']
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temporary:
        folder = Path(temporary)
        adapter['sources']['submitted_request'] = write(folder, 'binding.json', binding)
        with pytest.raises(ValueError):
            apply_reviews(Inputs(ROOT), sample, [write(folder, 'adapter.json', adapter)])
