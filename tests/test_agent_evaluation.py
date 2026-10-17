"""Synthetic assertion checks; these tests are not model performance measurements."""
import hashlib
import json
from copy import deepcopy

import pytest

from silicon_eye.agent_evaluation import evaluate
from silicon_eye.schemas.agent_observation import AgentObservations


@pytest.fixture
def evaluation(tmp_path):
    # Real seed reference is used as a format fixture, never claimed as fresh agent output.
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    ref_path = root / 'benchmarks/agent-eval/roi2-seed-v1/reference.json'
    ref = json.loads(ref_path.read_text())
    batch = json.loads((ref_path.parent / 'observations-template.json').read_text())
    packet = json.loads((root / ref['input_packet']['path']).read_text())
    batch['run_id'] = 'synthetic-unit-test'
    batch['observations'] = [dict(
        id=label['id'], predicate=label['predicate'], subject_ids=label['subject_ids'],
        scope_id=label['scope_id'], status='candidate' if label['value'] is not None else 'unknown',
        value=label['value'], evidence_refs=[next(iter(packet['sources']))],
        rationale='Synthetic fixture assertion, not an actual perception run.',
    ) for label in ref['labels']]
    path = tmp_path / 'synthetic.json'
    return root, ref_path, batch, path


def score(data):
    root, ref_path, batch, path = data
    path.write_text(json.dumps(batch))
    return evaluate(ref_path, path, root)


def test_exact_assertions_pass_but_do_not_fabricate_human_effort(evaluation):
    result = score(evaluation)
    assert result['reference_assertion_gate_pass']
    assert result['counts']['correct'] == 9
    assert result['counts']['kept_unknown'] == 1
    assert result['human_correction_count'] is None


def test_all_unknown_cannot_pass(evaluation):
    for observation in evaluation[2]['observations']:
        observation.update(status='unknown', value=None)
    result = score(evaluation)
    assert not result['reference_assertion_gate_pass']
    assert result['counts']['missed_known'] == 9


def test_asserting_unresolved_outer_connection_is_unsupported(evaluation):
    row = next(r for r in evaluation[2]['observations'] if r['id'] == 'outer_connected')
    row.update(status='candidate', value=True)
    result = score(evaluation)
    assert result['counts']['unsupported_certainty'] == 1
    assert not result['reference_assertion_gate_pass']


def test_wrong_material_identity_is_reported(evaluation):
    row = next(r for r in evaluation[2]['observations'] if r['predicate'] == 'material_identity')
    row['value'] = 'ct'
    assert score(evaluation)['counts']['wrong'] == 1


def test_known_net_replaced_by_separation_is_wrong(evaluation):
    row = next(r for r in evaluation[2]['observations'] if r['id'] == 'gates_connected')
    row['predicate'] = 'different_net'
    assert score(evaluation)['counts']['wrong'] == 1


def test_ai_cannot_mark_itself_human_confirmed(evaluation):
    evaluation[2]['observations'][0]['status'] = 'confirmed'
    with pytest.raises(ValueError):
        score(evaluation)


def test_packet_hash_mismatch_rejects_stale_photo_context(evaluation):
    evaluation[2]['input_packet']['sha256'] = hashlib.sha256(b'other').hexdigest()
    with pytest.raises(ValueError, match='different photo packets'):
        score(evaluation)


def test_local_poly_negative_cannot_be_moved_to_electrical_scope(evaluation):
    row = next(r for r in evaluation[2]['observations'] if r['predicate'] == 'joined_in_region')
    row['scope_id'] = 'electrical'
    with pytest.raises(ValueError, match='Physical joining'):
        score(evaluation)


def test_duplicate_proposition_and_self_reported_effort_rejected(evaluation):
    batch = deepcopy(evaluation[2])
    batch['observations'].append(dict(batch['observations'][0], id='duplicate'))
    evaluation[2].update(batch)
    with pytest.raises(ValueError):
        score(evaluation)
    batch = deepcopy(batch)
    batch['observations'].pop()
    batch['human_corrections'] = 0
    with pytest.raises(ValueError):
        AgentObservations.model_validate(batch)


def test_degenerate_boundary_is_not_a_valid_geometry_candidate(evaluation):
    row = evaluation[2]['observations'][0]
    row.update(boundary_status='candidate', boundary_polygon_xy=[[1745, 2710]] * 3,
               location=dict(id='loc', frame_id='poly_native', xywh=[1740, 2700, 40, 128],
                             role='inspection_window_not_material_boundary'))
    with pytest.raises(ValueError, match='Degenerate'):
        score(evaluation)


def test_material_identity_cannot_use_electrical_scope(evaluation):
    row = next(r for r in evaluation[2]['observations'] if r['predicate'] == 'material_identity')
    row['scope_id'] = 'electrical'
    with pytest.raises(ValueError, match='Material identity needs'):
        score(evaluation)
