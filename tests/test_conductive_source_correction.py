"""Via-layer identity outranks a numerically plausible cross-photo array fit."""

import copy
import json
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from silicon_eye.conductive_layers import deliver, source_identity_audit
from silicon_eye.joint_layers import load_snapshot

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / 'benchmarks/conductive-stack-v2/request-v1.json'


@pytest.fixture(scope='module')
def corrected():
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as tmp:
        out = Path(tmp) / 'corrected'
        report = deliver(ROOT, REQUEST, out)
        yield out, report, json.loads((out / 'model.json').read_text())


def test_m2_is_a_twelve_cut_v2_array_not_v1_or_single_proxy(corrected):
    out, report, model = corrected
    assert report['status'] == 'SCOPED_REVIEWED_CHAIN_SOURCE_CORRECTED'
    assert report['object_counts'] == dict(M1=9, V1=9, M2=1, V2=12, M3=2)
    group = model['confirmed_local_via_groups'][0]
    assert (group['rows'], group['columns'], group['cut_count']) == (3, 4, 12)
    cuts = model['objects_by_layer']['V2']
    assert len({o['id'] for o in cuts}) == 12
    assert all(o['source_frame'] == 'm2' and o['physical_cut_count'] == 1 for o in cuts)
    centers = [Polygon(o['geometry']['outer_xy']).centroid for o in cuts]
    assert len({p.x for p in centers}) == 4 and len({p.y for p in centers}) == 3
    assert model['geometry_audits']['V2']['status'] == 'PASS'
    assert model['geometry_audits']['V2']['human_confirmed_local_group_cut_count'] == 12
    assert 'V2-J-EDGE-SUPPORT' in model['retired_object_ids']
    assert all(o['id'] != 'V2-J-EDGE-SUPPORT' for o in cuts)
    assert set(model['reviewed_local_connections'][1]['via_object_ids']) == {o['id'] for o in cuts}
    assert model['reviewed_local_connections'][1]['upper_metal_id'] == 'M3-J-B1'
    assert not model['net_edges'] and report['new_physical_connections'] == 0
    assert not report['precise_projection_allowed'] and model['physical_cut_count'] is None
    page = (out / 'index.html').read_text()
    assert '3行×4列V2，共12个' in page
    assert '撤销M2上的V1标记' in page
    assert 'V2米白小方块是孔组最小支持区' not in page
    assert 'data-isolate="V2"' in page
    assert 'data-isolate="V1"' in page


def test_m1_evidence_is_preserved_but_wrong_pair_fit_is_rejected(corrected):
    _, report, model = corrected
    before = json.loads((ROOT / 'docs/assets/conductive-stack-v1/model.json').read_text())
    for layer in ['M1', 'M2', 'M3']:
        assert model['objects_by_layer'][layer] == before['objects_by_layer'][layer]
    for old, new in zip(before['objects_by_layer']['V1'], model['objects_by_layer']['V1'],
                        strict=True):
        assert new['id'] == old['id'] and new['geometry'] == old['geometry']
        assert new['source_observation']['m1_xy'] == old['source_observation']['m1_xy']
        assert 'm2_xy' not in new['source_observation']
        assert new['source_observation']['layer'] == 'V1'
    correction = model['evidence_correction']
    assert correction['prior_M1_M2_array_fit_status'] == 'REJECTED_DIFFERENT_VIA_LAYER'
    assert correction['prior_4_52px_holdout_is_valid_registration_evidence'] is False
    assert len(correction['invalidated_correspondence_ids']) == 9
    assert model['source_identity_gate']['status'] == 'PASS'
    assert report['source_correspondence_status'].startswith('PRIOR_ARRAY_FIT_REJECTED')


@pytest.mark.parametrize('change', ['wrong_frame', 'borrow_m2_point', 'wrong_photo'])
def test_identity_gate_blocks_reusing_v2_pixels_as_v1_evidence(corrected, change):
    _, _, model = corrected
    changed = copy.deepcopy(model)
    obj = changed['objects_by_layer']['V1'][0]
    if change == 'wrong_frame':
        obj['source_frame'] = 'm2'
    elif change == 'borrow_m2_point':
        obj['source_observation']['m2_xy'] = [1961, 1912]
    else:
        obj['source_photo'] = changed['source_photos']['m2']
    gate = source_identity_audit(changed, changed['source_identity_policy'])
    assert gate['status'] == 'FAIL'
    assert gate['errors']


def test_corrected_common_snapshot_preserves_materials_and_limits(corrected):
    out, _, _ = corrected
    after = load_snapshot(ROOT, out / 'joint-snapshot.json')
    before = load_snapshot(ROOT, ROOT / 'configs/joint-work-layer-v3.json')
    assert before['materials'] == after['materials']
    assert before['contacts'] == after['contacts']
    assert before['values'] == after['values']
    assert len(after['conductors']['objects_by_layer']['V2']) == 12
    assert after['manifest']['id'].endswith(':conductive-stack-v2-source-corrected')


def test_fitter_rejects_typed_v1_to_v2_pairs_before_using_numeric_residuals():
    from silicon_eye.metal_via_pilot import local_correspondence

    old = json.loads((ROOT / 'benchmarks/m1-v1-m2-joint-reviewed-v2/spec-v1.json').read_text())
    points = copy.deepcopy(old['observations'])
    for point in points:
        point['via_layer_by_frame'] = dict(m1='V1', m2='V2')
    with pytest.raises(ValueError, match='Different via layers'):
        local_correspondence(points, old['fit_ids'], 5)
