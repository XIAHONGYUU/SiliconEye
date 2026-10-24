"""Candidate/review/resume/local-revision behavior on fixed spatial samples."""
import copy
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from silicon_eye.conductive_workflow import page, prepare, run
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'benchmarks/conductive-workflow-trial-v1'


def read(path):
    return json.loads(path.read_text())


def ref(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=digest(path))


@pytest.fixture(scope='module')
def workspace():
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as directory:
        yield Path(directory)


@pytest.fixture(scope='module')
def initial(workspace):
    request = read(TRIAL / 'independent-request-v1.json')
    out = workspace / 'initial'
    model, _ = run(ROOT, TRIAL / 'independent-request-v1.json', out)
    return request, out, model


def mutated_sample(workspace, request, mutate, name):
    current = copy.deepcopy(request)
    sample = read(ROOT / current['sample']['path'])
    mutate(sample)
    path = workspace / (name + '.json')
    path.write_text(json.dumps(sample))
    current['sample'] = ref(path)
    return current


def test_pending_q1_is_not_false_or_approved(initial):
    _, _, model = initial
    assert model['pending_interface_ids'] == ['IT1-V1-A']
    assert model['deferred_unknown_ids'] == ['IT1-V1-A']
    assert [c['id'] for c in model['reviewed_local_connections']] == ['IT1-V2-B']
    assert not model['geometry_adopted'] and not model['automatic_network_export_allowed']
    assert model['net_edges'] == [] and not model['complete_network']
    assert all(c['connection_confirmed'] is None for c in model['candidate_interfaces'])


def test_main_carries_u3_and_latest_ab_groups():
    request = read(ROOT / 'benchmarks/conductive-quality-review-v1/medium-request-v1.json')
    model, _, _, _, _ = prepare(ROOT, request)
    assert model['branch']['terminal_closed']
    assert model['branch']['reviewed_terminal_connection']['physical_cut_count'] is None
    groups = {g['group_id']: g['M1_members'] for g in model['accepted_structural_groups']}
    assert groups['MID-AB-GROUP-A'] == ['M1-T3-LOCAL', 'M1-L2-LOCAL']


def test_resume_inherits_q2_without_requiring_resubmission(initial):
    request, out, before = initial
    request = copy.deepcopy(request)
    request.update(parent=ref(out / 'manifest.json'), reviews=[])
    after, report, _, _, _ = prepare(ROOT, request)
    assert after['reviewed_local_connections'] == before['reviewed_local_connections']
    assert report['changed_object_ids'] == []
    assert after['pending_interface_ids'] == ['IT1-V1-A']


def test_explicit_local_revision_changes_only_one_object(workspace, initial):
    request, out, before = initial
    def change(sample):
        sample['features_by_layer']['M1'][0]['design_width'] += 2
    request = mutated_sample(workspace, request, change, 'one-width')
    evidence = workspace / 'revision-evidence.json'
    evidence.write_text(json.dumps(dict(actor='AI', reason='Synthetic transaction test only')))
    request.update(parent=ref(out / 'manifest.json'), reviews=[],
                   allowed_changed_ids=['IT1-M1-RING'], revision_evidence=ref(evidence))
    after, report, _, _, _ = prepare(ROOT, request)
    assert report['changed_object_ids'] == ['IT1-M1-RING']
    assert after['reviewed_local_connections'] == before['reviewed_local_connections']
    assert after['objects_by_layer']['M2'] == before['objects_by_layer']['M2']
    assert after['pending_interface_ids'] == before['pending_interface_ids']


@pytest.mark.parametrize('change,reason', [
    ('unlisted', 'change scope'), ('budget', 'budgets'), ('drop_order', 'budgets'),
    ('identity', 'interface identity'), ('drop_limits', 'limitations'),
])
def test_resume_rejects_scope_and_quality_regressions(workspace, initial, change, reason):
    request, out, _ = initial
    def mutate(sample):
        if change == 'unlisted':
            sample['features_by_layer']['M1'][0]['design_width'] += 2
        elif change == 'budget':
            sample['metal_budget']['minimum_width_px'] += 1
        elif change == 'drop_order':
            sample.pop('source_order_checks')
        elif change == 'identity':
            sample['interfaces'][1]['native_bounds'][0] += 1
    request = mutated_sample(workspace, request, mutate, change)
    request.update(parent=ref(out / 'manifest.json'), reviews=[])
    if change == 'identity':
        request['allowed_changed_ids'] = ['IT1-V2-B']
        evidence = workspace / 'identity-evidence.json'
        evidence.write_text(json.dumps(dict(actor='AI', reason='Test invalid identity change')))
        request['revision_evidence'] = ref(evidence)
    if change == 'drop_limits':
        request['limits'] = []
    with pytest.raises(ValueError, match=reason):
        prepare(ROOT, request)


@pytest.mark.parametrize('change,reason', [
    ('wrong_frame', 'identity/order'), ('no_bearing', 'enclosure'),
    ('false_approval', 'pre-approved'), ('diagonal', 'orthogonal'),
    ('projection', 'projection'), ('wrong_carrier', 'carrier layer'),
])
def test_candidate_gates_reject_unsafe_inputs(workspace, initial, change, reason):
    request = initial[0]
    def mutate(sample):
        if change == 'wrong_frame':
            sample['interfaces'][0]['source_frame'] = 'm2'
        elif change == 'no_bearing':
            sample['interfaces'][0]['bounds'] = [897, 277, 903, 283]
        elif change == 'false_approval':
            sample['interfaces'][0]['connection_confirmed'] = True
        elif change == 'diagonal':
            sample['features_by_layer']['M1'][0]['design_path'][1][1] += 1
        elif change == 'projection':
            sample['source_to_design_transform'] = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        elif change == 'wrong_carrier':
            sample['interfaces'][0]['upper_metal_id'] = 'IT1-M3-BUS'
    request = mutated_sample(workspace, request, mutate, change)
    with pytest.raises(ValueError, match=reason):
        prepare(ROOT, request)


def test_review_cannot_move_to_different_photograph_snapshot(workspace, initial):
    request = copy.deepcopy(initial[0])
    sample = read(ROOT / request['sample']['path'])
    snapshot = read(ROOT / sample['snapshot']['path'])
    snapshot['test_revision'] = 'different source-stack identity'
    snapshot_path = workspace / 'other-snapshot.json'
    snapshot_path.write_text(json.dumps(snapshot))
    sample['snapshot'] = ref(snapshot_path)
    path = workspace / 'other-sample.json'
    path.write_text(json.dumps(sample))
    request['sample'] = ref(path)
    with pytest.raises(ValueError, match='different photo snapshot'):
        prepare(ROOT, request)


def test_wrong_layer_source_crop_cannot_be_reused(initial):
    request = copy.deepcopy(initial[0])
    request['source_assets']['m1']['wide_raw'] = request['source_assets']['m2']['wide_raw']
    with pytest.raises(ValueError, match='source view does not match'):
        prepare(ROOT, request)


def test_invalid_candidate_leaves_only_rejection_diagnostic(workspace, initial):
    def mutate(sample):
        sample['interfaces'][0]['connection_confirmed'] = True
    request = mutated_sample(workspace, initial[0], mutate, 'bad-output')
    path = workspace / 'bad-request.json'
    path.write_text(json.dumps(request))
    output = workspace / 'rejected'
    with pytest.raises(ValueError, match='pre-approved'):
        run(ROOT, path, output)
    assert [p.name for p in output.iterdir()] == ['diagnostic.json']
    assert read(output / 'diagnostic.json')['status'] == 'REJECTED'


def test_real_cli_reloads_candidate_and_scoped_review(workspace):
    output = workspace / 'cli'
    result = subprocess.run([str(ROOT / '.venv/bin/python'), '-m',
                             'silicon_eye.conductive_workflow', '--request',
                             str(TRIAL / 'independent-request-v1.json'), '--output', str(output)],
                            cwd=ROOT, capture_output=True, text=True, check=True)
    assert result.returncode == 0
    model = read(output / 'model.json')
    assert model['pending_interface_ids'] == ['IT1-V1-A']
    assert model['reviewed_local_connections'][0]['id'] == 'IT1-V2-B'
    assert (output / 'index.html').is_file()


def test_canonical_observation_format_uses_same_workflow(workspace, initial):
    request = mutated_sample(workspace, initial[0],
                             lambda s: s.update(kind='conductive_layer_observations'), 'canonical')
    model = prepare(ROOT, request)[0]
    assert model['pending_interface_ids'] == ['IT1-V1-A']
    assert model['reviewed_local_connections'][0]['id'] == 'IT1-V2-B'


def test_resume_cannot_drop_main_terminal_approval(workspace):
    request = read(ROOT / 'benchmarks/conductive-quality-review-v1/medium-request-v1.json')
    request['parent'] = ref(ROOT / 'docs/assets/conductive-workflow-trial-v1/main/manifest.json')
    request = mutated_sample(workspace, request, lambda s: s.pop('reviewed_terminal_state'),
                             'drop-u3')
    with pytest.raises(ValueError, match='approved terminal was lost'):
        prepare(ROOT, request)


def test_ai_record_cannot_impersonate_a_review(workspace, initial):
    request = copy.deepcopy(initial[0])
    review = read(ROOT / request['reviews'][0]['path'])
    review['actor'] = 'AI'
    path = workspace / 'fake-human.json'
    path.write_text(json.dumps(review))
    request['reviews'] = [ref(path)]
    with pytest.raises(ValueError, match='human review statement'):
        prepare(ROOT, request)


def test_reconstruction_cannot_hide_required_source_layer(initial):
    request = copy.deepcopy(initial[0])
    request['frames'] = ['m2', 'm3']
    with pytest.raises(ValueError, match='omit a reconstructed metal'):
        prepare(ROOT, request)


def test_scoped_review_cannot_follow_reassigned_native_metal(workspace, initial):
    def mutate(sample):
        sample['features_by_layer']['M2'][1]['native_path'][0][0] += 5
    request = mutated_sample(workspace, initial[0], mutate, 'moved-reviewed-source')
    with pytest.raises(ValueError, match='Reviewed metal source anchor drift'):
        prepare(ROOT, request)


@pytest.mark.parametrize('verdict', [True, False, None])
def test_new_workflow_package_review_round_trip(workspace, initial, verdict):
    request, out, _ = initial
    request = copy.deepcopy(request)
    review = dict(actor='human', statement='Synthetic workflow-round-trip test',
                  sources=dict(submitted_request=ref(out / 'request.json'),
                               submitted_manifest=ref(out / 'manifest.json'),
                               submitted_page=ref(out / 'index.html')),
                  decisions=dict(interface_id='IT1-V1-A', via_layer='V1',
                                 lower_metal_id='IT1-M1-RING', upper_metal_id='IT1-M2-A',
                                 connection_confirmed=verdict))
    path = workspace / ('synthetic-review-'+str(verdict)+'.json')
    path.write_text(json.dumps(review))
    request.update(parent=ref(out / 'manifest.json'), reviews=[ref(path)],
                   deferred_unknown_ids=['IT1-V1-A'] if verdict is None else [])
    model, report, sample, _, _ = prepare(ROOT, request)
    ids = [c['id'] for c in model['reviewed_local_connections']]
    assert 'IT1-V2-B' in ids
    assert ('IT1-V1-A' in ids) == (verdict is True)
    assert ('IT1-V1-A' in model['pending_interface_ids']) == (verdict is None)
    assert model['review_decisions']['IT1-V1-A']['connection_confirmed'] is verdict
    assert not model['complete_network'] and model['net_edges'] == []
    rendered = page(model, report, sample, request, workspace, ROOT)
    assert ('候选接入已否决' in rendered) == (verdict is False)


def test_cli_rejection_has_no_success_model_or_traceback(workspace):
    output = workspace / 'cli-reject'
    request = ROOT / 'benchmarks/conductive-quality-review-v1/negative-source-order-request.json'
    result = subprocess.run([str(ROOT / '.venv/bin/python'), '-m',
                             'silicon_eye.conductive_workflow', '--request',
                             str(request),
                             '--output', str(output)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 2 and 'Source relative order' in result.stderr
    assert 'Traceback' not in result.stderr
    assert [p.name for p in output.iterdir()] == ['diagnostic.json']


def test_render_failure_does_not_publish_partial_success(workspace, initial):
    def mutate(sample):
        sample['source_panels']['source_regions']['m1'][0]['bounds'] = [9998, 1, 9999, 2]
    request = mutated_sample(workspace, initial[0], mutate, 'bad-marked-window')
    request.pop('source_assets')
    path = workspace / 'render-failure-request.json'
    path.write_text(json.dumps(request))
    output = workspace / 'render-failure'
    with pytest.raises(ValueError, match='Source region outside photo'):
        run(ROOT, path, output)
    assert [p.name for p in output.iterdir()] == ['diagnostic.json']
    assert not list(workspace.glob('.conductive-workflow-*'))


CORRECTION = ROOT / 'benchmarks/metal-independent-q1-correction-v2/request-scoped-v3.json'


def test_human_q1_carrier_correction_preserves_q2_and_full_group():
    model, report, sample, _, _ = prepare(ROOT, read(CORRECTION))
    assert report['changed_object_ids'] == ['IT1-M2-B', 'IT1-V1-A']
    assert model['pending_interface_ids'] == []
    assert model['deferred_unknown_ids'] == []
    reviewed = {c['id']: c for c in model['reviewed_local_connections']}
    assert reviewed['IT1-V1-A']['upper_metal_id'] == 'IT1-M2-B'
    assert reviewed['IT1-V1-A']['physical_cut_count'] == 6
    assert reviewed['IT1-V2-B']['lower_metal_id'] == 'IT1-M2-B'
    old = read(ROOT / 'docs/assets/conductive-workflow-trial-v1/final-independent/model.json')
    assert reviewed['IT1-V2-B'] == old['reviewed_local_connections'][0]
    assert report['audits']['IT1-V1-A']['candidate_cut_count'] == 6
    assert report['audits']['IT1-V1-A']['group_footprint_checked']
    assert not model['geometry_adopted'] and not model['complete_network']
    cuts = model['objects_by_layer']['V1'][0]['candidate_cut_bounds']
    assert len(cuts) == 6 and len({tuple(b) for b in cuts}) == 6
    rendered = page(model, report, sample, read(CORRECTION), ROOT / 'runs', ROOT)
    assert 'IT1-V1-A/C06' in rendered
    assert 'IT1-M1-RING → IT1-M2-B' in rendered


def test_six_cut_group_cannot_fit_old_narrow_carrier(workspace):
    request = mutated_sample(workspace, read(CORRECTION),
                             lambda s: s['interfaces'][0].update(upper_metal_id='IT1-M2-A'),
                             'six-cuts-wrong-narrow-bearing')
    with pytest.raises(ValueError, match='enclosure'):
        prepare(ROOT, request)


def test_observed_six_holes_cannot_collapse_to_single_proxy(workspace):
    request = mutated_sample(workspace, read(CORRECTION),
                             lambda s: s['interfaces'][0].pop('cut_array_candidate'),
                             'six-cuts-collapsed-proxy')
    with pytest.raises(ValueError, match='count differs'):
        prepare(ROOT, request)


def test_unapproved_carrier_reassignment_still_rejected():
    request = read(CORRECTION)
    request['reviews'] = []
    with pytest.raises(ValueError, match='interface identity'):
        prepare(ROOT, request)


def test_human_count_evidence_cannot_change_to_four(workspace):
    request = mutated_sample(workspace, read(CORRECTION),
                             lambda s: s['interfaces'][0]['cut_array_candidate'].update(rows=2),
                             'six-cuts-changed-count')
    with pytest.raises(ValueError, match='count differs'):
        prepare(ROOT, request)


def test_group_bounds_cannot_hide_outer_cuts(workspace):
    request = mutated_sample(workspace, read(CORRECTION),
                             lambda s: s['interfaces'][0].update(bounds=[367, 277, 373, 283]),
                             'six-cuts-hidden-footprint')
    with pytest.raises(ValueError, match='entire array'):
        prepare(ROOT, request)


def test_carrier_correction_cannot_relocate_source(workspace):
    request = mutated_sample(workspace, read(CORRECTION),
                             lambda s: s['interfaces'][0]['native_bounds'].__setitem__(0, 2541),
                             'six-cuts-moved-source')
    with pytest.raises(ValueError, match='before/after identities'):
        prepare(ROOT, request)


def test_resolved_limit_requires_actual_review_reference():
    request = read(CORRECTION)
    key = next(iter(request['resolved_limits']))
    request['resolved_limits'][key] = request['revision_evidence']
    with pytest.raises(ValueError, match='human review statement'):
        prepare(ROOT, request)


def test_q1_verdict_cannot_remove_unrelated_ab_unknown():
    request = read(CORRECTION)
    unrelated = 'A/B是否同层连续仍未知。'
    request['limits'].remove(unrelated)
    request['resolved_limits'][unrelated] = request['reviews'][0]
    with pytest.raises(ValueError, match='bound pending-interface verdict'):
        prepare(ROOT, request)


def test_resume_after_q1_correction_keeps_both_approvals():
    request = read(CORRECTION)
    request.update(parent=ref(ROOT / 'docs/assets/metal-independent-q1-reviewed-v3/manifest.json'),
                   reviews=[], allowed_changed_ids=[], resolved_limits={})
    request.pop('revision_evidence')
    model, report, _, _, _ = prepare(ROOT, request)
    assert report['changed_object_ids'] == [] and report['pending_interface_ids'] == []
    assert set(report['reviewed_interface_ids']) == {'IT1-V1-A', 'IT1-V2-B'}
    assert len(model['resolved_limits']) == 1


def test_inherited_human_count_survives_removal_of_both_candidate_fields(workspace):
    def collapse(sample):
        cut = sample['interfaces'][0]
        cut.pop('cut_array_candidate')
        cut.pop('count_evidence')
        cut['bounds'] = [367, 277, 373, 283]
    request = mutated_sample(workspace, read(CORRECTION), collapse,
                             'both-count-fields-removed')
    with pytest.raises(ValueError, match='count/footprint evidence was lost'):
        prepare(ROOT, request)


def test_old_medium_mirrored_return_is_rejected():
    request = read(TRIAL / 'main-request-v1.json')
    with pytest.raises(ValueError, match='turn handedness mismatch: R-M2-3'):
        prepare(ROOT, request)


def test_quality_keeps_geometry_and_coverage_unqualified_after_carrier_approval():
    _, report, _, _, _ = prepare(ROOT, read(CORRECTION))
    quality = report['quality']
    assert quality['reviewed_represented_interface_count'] == 2
    assert quality['explicit_design_array_count'] == 1
    assert quality['source_qualified_array_count'] == 0
    assert quality['proxy_interface_ids'] == ['IT1-V2-B']
    assert quality['coverage']['photo_coverage_fraction'] is None
    assert not quality['readiness']['canonical_geometry_adoption']
    assert not quality['readiness']['unrestricted_skill_release']
    proxy = next(c for c in quality['interface_geometry'] if c['id'] == 'IT1-V2-B')
    assert proxy['full_group_design_enclosure'] == 'NOT_EVALUATED'
    assert proxy['design_cut_count'] is None


def test_quality_reports_medium_inventory_without_claiming_full_photo_coverage():
    request = read(ROOT / 'benchmarks/conductive-quality-review-v1/medium-request-v1.json')
    model, report, _, _, _ = prepare(ROOT, request)
    q = report['quality']
    assert q['represented_interface_count'] == q['reviewed_represented_interface_count'] == 11
    assert len(q['proxy_interface_ids']) == 11 and q['explicit_design_array_count'] == 0
    assert q['coverage']['known_review_inventory_count'] == 38
    assert q['coverage']['represented_review_inventory_count'] == 11
    assert q['coverage']['photo_coverage_fraction'] is None
    assert len(q['coverage']['endpoints']) == 22
    assert model['branch']['terminal_closed']


def test_review_views_must_include_the_observed_group(workspace, initial):
    def hide_group(sample):
        for mode in ('wide', 'detail'):
            sample['source_panels']['source_windows']['m1'][mode] = [2250, 100, 2400, 300]
    request = mutated_sample(workspace, initial[0], hide_group, 'hidden-via-source')
    with pytest.raises(ValueError, match='omits the observed via group: IT1-V1-A'):
        prepare(ROOT, request)


def test_legacy_proxy_keeps_existing_twelve_hole_fact_without_claiming_geometry():
    request = read(ROOT / 'benchmarks/conductive-quality-review-v1/medium-request-v1.json')
    model, report, _, _, _ = prepare(ROOT, request)
    assert len(model['inherited_group_facts']) == 1
    fact = model['inherited_group_facts'][0]
    assert fact['rows'] == 3 and fact['columns'] == 4 and fact['cut_count'] == 12
    assert not fact['geometry_ported']
    row = next(r for r in report['quality']['interface_geometry']
               if r['id'] == 'SUPPORT-J-M2-V2-M3-B1')
    assert row['human_cut_count'] == 12
    assert row['representation'] == 'GROUP_SUPPORT_PROXY'
    assert row['full_group_design_enclosure'] == 'NOT_EVALUATED'
    assert row['design_cut_count'] is None
