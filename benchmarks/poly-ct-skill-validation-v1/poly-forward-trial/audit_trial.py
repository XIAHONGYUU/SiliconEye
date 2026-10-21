"""Audit this bounded POLY continuation trial; run from the repository root.

Requires the project Python environment and both layer_review delivery packages.
Writes only this trial directory and does not adopt or modify model records.
"""
import hashlib
import json
from pathlib import Path

from shapely.geometry import Polygon, box

from silicon_eye.aa_completion import object_polygon
from silicon_eye.joint_layers import load_snapshot


BASE = Path('runs/skill-forward-poly-v1')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


parent = load_snapshot(Path('.'), Path('configs/joint-work-layer-v3.json'))
request = read('benchmarks/poly-ct-skill-validation-v1/poly-pending.json')
change = request['changes'][0]
aa = next(o for o in parent['materials']['AA_objects'] if o['id'] == change['before']['AA_target'])
target = object_polygon(aa)
geometry = {}
for label in ('before', 'after'):
    p = Polygon(change[label]['layout_outline'])
    local = target.intersection(box(p.bounds[0], 0, p.bounds[2], parent['manifest']['canvas_wh'][1]))
    geometry[label] = dict(
        poly_bounds=list(p.bounds),
        target_local_bounds=list(local.bounds),
        upper_extension_px=local.bounds[1] - p.bounds[1],
        lower_extension_px=p.bounds[3] - local.bounds[3],
        overlap_area_px2=p.intersection(local).area,
    )

checks = {}
package_statuses = {}
for directory in ('revision-review', 'current-inspect'):
    folder = BASE / directory
    manifest = read(folder / 'manifest.json')
    context = read(folder / 'continuation-context.json')
    expected = {k: v for k, v in parent['values'].items() if k not in {'materials', 'contacts', 'AA_context'}}
    checks[directory] = dict(
        artifact_hashes_match=all(sha(folder / name) == digest for name, digest in manifest['artifacts'].items()),
        locked_inputs_still_match=all(sha(name) == digest for name, digest in manifest['verified_inputs'].items()),
        code_hashes_match=all(sha(name) == digest for name, digest in manifest['code'].items()),
        all_inherited_documents_exact=context['inherited_documents'] == expected,
        budget_exact=context['budget'] == parent['manifest']['budget'],
        coordinate_frames_exact=context['coordinate_frames'] == dict(design_px=[5860, 4587], native_px=[5712, 4284]),
        no_adoption=context['adoption_status'] == 'not_adopted_no_new_human_approval',
        export_disabled=context['automatic_network_export_allowed'] is False and manifest['automatic_network_export_allowed'] is False,
        counts_exact=manifest['model_counts'] == dict(AA=334, POLY=696, CT=10287),
    )
    package_statuses[directory] = dict(status=manifest['status'], candidate_snapshot=manifest['candidate_snapshot'], next_snapshot=manifest['next_snapshot'])

original_window = request['windows'][0]['source_windows']['poly']
native_polygon = Polygon(change['before']['native_outline'])
source_window_defect = not box(*original_window).covers(native_polygon)
model = parent['materials']
poly_by_id = {o['id']: o for o in model['objects']}
contacts_by_id = {o['id']: o for o in parent['contacts']}
blue_id = 'CT-G66-P03-P04-SHARED-TOP-01'
blue = contacts_by_id[blue_id]
reviewed_constraints = model['reviewed_contact_constraints']
cross_layer = dict(
    current_G26_AA_target=change['before']['AA_target'],
    changed_fields=[k for k in change['before'] if change['before'][k] != change['after'].get(k)],
    changed_ids=[c['id'] for c in request['changes']],
    no_CT_or_AA_change=all(c['layer'] == 'POLY' for c in request['changes']),
    current_G26_CT_ids=[o['id'] for o in parent['contacts'] if o.get('POLY_target') == 'G26-P01'],
    blue_contact_material=blue['landing_material'],
    blue_contact_target=blue['POLY_target'],
    shared_bus_members=poly_by_id[blue['POLY_target']]['member_POLY_ids'],
    retired_error_absent=all(x not in contacts_by_id for x in parent['manifest']['retired_contact_ids']),
    reviewed_contact_constraints=reviewed_constraints,
)
unknown_ids = [x['id'] for x in parent['values']['unknown']['unknown_scopes']]
failure = read(BASE / 'revision-review/joint-report.json')
baseline = read(BASE / 'current-inspect/joint-report.json')
result = dict(
    schema_version=1,
    task='Known-chip scoped POLY continuation, supplied human review; not a blind test',
    conclusion='REJECT_PENDING_REVISION_KEEP_CURRENT_V3',
    can_adopt_pending_revision=False,
    reason='G26-P01 ends inside its explicit AA cross-section; the lower extension is -46.981 px, violating the locked 8 px relative gate-extension budget.',
    current_snapshot='configs/joint-work-layer-v3.json',
    actual_commands=[read(BASE / 'revision-command.json'), read(BASE / 'inspect-command.json')],
    verification_command='PYTHONDONTWRITEBYTECODE=1 .venv/bin/python runs/skill-forward-poly-v1/audit_trial.py',
    verification_exit_code=0,
    pending_report_status=failure['status'],
    baseline_inspect_status=baseline['status'],
    failure_errors=failure['POLY']['errors'],
    separate_gates=dict(CT=failure['CT']['status'], source=failure['source_gate']['status'], reviewed_identity=failure['reviewed_identity_status']),
    relative_gate_extension_budget=parent['materials']['relative_budget'],
    independent_geometry=geometry,
    package_statuses=package_statuses,
    continuity_checks=checks,
    cross_layer=cross_layer,
    preserved_unknown_ids=unknown_ids,
    human_review_preserved='All inherited human_review and prior_human_review documents compare equal; S1/S2 approval remains scoped; S3 exact bus geometry remains AI candidate.',
    source_window_defect=dict(original_window=original_window, native_outline_bounds=list(native_polygon.bounds), excludes_native_object=source_window_defect, corrected_inspect_window=[500, 1200, 800, 1580]),
    new_human_questions=[],
    new_human_question_required=False,
    human_corrections_count=None,
    safe_next_step='Continue from current v3. Reject this shortening; inspect correctly located source evidence and local AA correspondence before proposing any new per-ID transaction. Keep AA/CT and reviewed identities unchanged unless evidence separately justifies a jointly scoped change; rerun the shared delivery gate for any future proposal.',
    artifacts=dict(rejected_package=str(BASE / 'revision-review'), rejected_review_page=str(BASE / 'revision-review/index.html'), current_inspect=str(BASE / 'current-inspect/index.html'), verification_script=str(BASE / 'audit_trial.py')),
    unverified=['Complete physical POLY/CT recovery and precise contours', 'G26 local source-to-design correspondence beyond existing candidate records', 'M1 connectivity, netlist, process, polarity, physical scale, real W/L, PDK DRC/LVS', 'New-input or held-out-chip skill performance; this is a known-chip continuation'],
    production_changes=False,
    git_push=False,
)
assert all(all(v.values()) for v in checks.values()), checks
assert failure['status'] == 'FAIL' and baseline['status'] == 'PASS'
assert package_statuses['revision-review']['next_snapshot'] is None
assert package_statuses['revision-review']['candidate_snapshot'] is None
assert not (BASE / 'revision-review/joint-snapshot.json').exists()
assert len(unknown_ids) == 6 and 'S3-AA4-LEFT-SD-ACCESS' in unknown_ids
(BASE / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(continuity_checks='PASS', pending='FAIL', current='PASS', result=str(BASE / 'result.json'))))
