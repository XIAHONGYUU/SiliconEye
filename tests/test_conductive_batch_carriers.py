"""Batch source verdicts stay scoped to original answers, never counts or geometry."""
import copy
import json
import tempfile
from pathlib import Path

import pytest

from silicon_eye.conductive_workflow import prepare
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / 'benchmarks/upper-cap-joint-revision-v1'


def read(path):
    return json.loads(path.read_text())


def ref(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


@pytest.fixture

def changed_review():
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as directory:
        directory = Path(directory)
        request = read(BATCH / 'request.json')
        review = read(ROOT / request['reviews'][0]['path'])
        yield directory, request, review


def replay_changed_review(fixture, change):
    directory, request, review = fixture
    change(review)
    path = directory / 'review.json'
    path.write_text(json.dumps(review))
    request['reviews'][0] = ref(path)
    return prepare(ROOT, request)


def test_batch_answers_replay_without_reopening_or_inventing_counts():
    model, report, _, _, _ = prepare(ROOT, read(BATCH / 'request.json'))
    assert model['pending_interface_ids'] == []
    reviewed = {d['id']: d for d in model['reviewed_local_connections']}
    assert len(reviewed) == 7
    for key, upper in [('C03-V2', 'C-M3-T01'), ('C04-V2', 'C-M3-T02')]:
        assert reviewed[key]['upper_metal_id'] == upper
        assert reviewed[key]['physical_cut_count'] is None
    assert not model['geometry_adopted'] and not model['complete_network']
    assert model['net_edges'] == []


@pytest.mark.parametrize('change', [
    lambda r: r.update(observed_cut_count=2),
    lambda r: r.update(statement='03接T01，已确认两个孔'),
    lambda r: r['decisions'].update(connection_confirmed=False),
    lambda r: r['decisions'].update(upper_metal_id='C-M3-T02'),
    lambda r: r.update(question_id='missing'),
])
def test_derived_answer_cannot_change_original_verdict_or_add_count(changed_review, change):
    with pytest.raises(ValueError):
        replay_changed_review(changed_review, change)


def test_batch_binding_cannot_hide_source_scope_drift(changed_review):
    directory, request, review = changed_review
    batch = read(ROOT / review['sources']['batch_human_review']['path'])
    batch['decisions'][0]['native_bounds'][0] += 1
    path = directory / 'batch.json'
    path.write_text(json.dumps(batch))
    review['sources']['batch_human_review'] = ref(path)
    with pytest.raises(ValueError, match='answer scope'):
        replay_changed_review(changed_review, lambda r: None)


def test_inherited_geometry_still_fails_new_whole_group_enclosure():
    sample = read(BATCH / 'observations.json')
    before = read(ROOT / 'benchmarks/n1-v2-local-reconstruction-v1/observations.json')
    originals = {f['id']: f for fs in before['features_by_layer'].values() for f in fs}
    for fs in sample['features_by_layer'].values():
        for f in fs:
            if f['id'] in ('C-M2-03', 'C-M2-04'):
                f['design_path'] = copy.deepcopy(originals[f['id']]['design_path'])
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as directory:
        path = Path(directory) / 'bad-placement.json'
        path.write_text(json.dumps(sample))
        request = read(BATCH / 'request.json')
        request['sample'] = ref(path)
        with pytest.raises(ValueError, match='Via enclosure/spacing gate failed'):
            prepare(ROOT, request)
