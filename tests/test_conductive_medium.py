"""Joint candidates must not promote overlap, old membership or missing terminals."""

import copy
import json
import tempfile
from pathlib import Path

import pytest

from silicon_eye.conductive_medium import deliver, prepare, review_page, source_order_audit
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / 'benchmarks/conductive-medium-closeout-v1/request-v1.json'


@pytest.fixture(scope='module')
def request_data():
    return json.loads(REQUEST.read_text())


@pytest.fixture(scope='module')
def result(request_data):
    return prepare(ROOT, request_data)


def test_one_local_canvas_keeps_reviewed_interfaces_and_unknown_terminal(result):
    model, report, _, _ = result
    assert report['object_counts'] == dict(M1=9, M2=8, M3=5, V1=5, V2=6)
    assert report['input_interface_union_count'] == 38
    assert len(model['reviewed_local_connections']) == 11
    assert model['coordinate_space'] == 'local_regular_design_px_not_photo_projection'
    assert model['branch']['reviewed_metal_route_continuous']
    assert not model['branch']['terminal_closed'] and not model['complete_network']
    assert model['net_edges'] == [] and not model['automatic_network_export_allowed']
    assert model['common_canvas_placement'] is None
    assert all(obj['geometry']['status'] == obj['geometry_status']
               for objects in model['objects_by_layer'].values() for obj in objects)
    assert all(obj['physical_cut_count'] is None for layer in ('V1', 'V2')
               for obj in model['objects_by_layer'][layer])


def test_latest_group_correction_and_source_frame_are_retained(result):
    model = result[0]
    groups = {g['group_id']: g['M1_members'] for g in model['accepted_structural_groups']}
    assert groups['MID-AB-GROUP-A'] == ['M1-T3-LOCAL', 'M1-L2-LOCAL']
    assert groups['MID-AB-GROUP-B'] == ['M1-T1-LOCAL', 'M1-L4-LOCAL']
    assert all(obj['source_frame'] == frame for layer, frame in [('V1', 'm1'), ('V2', 'm2')]
               for obj in model['objects_by_layer'][layer])
    assert all(h['connection_confirmed'] is None for h in model['path_hypotheses'])


@pytest.mark.parametrize('change,reason', [
    ('diagonal', 'orthogonal'),
    ('narrow', 'Metal geometry gate failed'),
    ('same_layer_join', 'Metal geometry gate failed'),
    ('via_frame', 'Via source frame mismatch'),
    ('via_enclosure', 'Via support enclosure gate failed'),
    ('duplicate_edge', 'Duplicate support or reviewed interface'),
    ('hypothesis_approval', 'Unreviewed path cannot be promoted'),
    ('terminal_approval', 'Terminal requires separate evidence'),
    ('terminal_wrong_metal', 'Terminal does not continue'),
    ('false_branch', 'Branch continuity mismatch'),
    ('unknown_branch', 'unreviewed interface'),
    ('net_export', 'cannot authorize projection or net export'),
    ('projection', 'cannot authorize projection or net export'),
])
def test_regressions_fail_before_output(request_data, change, reason):
    request = copy.deepcopy(request_data)
    if change == 'diagonal':
        request['features_by_layer']['M1'][0]['design_path'][1][1] += 1
    elif change == 'narrow':
        request['features_by_layer']['M1'][0]['design_width'] = 2
    elif change == 'same_layer_join':
        request['features_by_layer']['M1'][2]['design_path'] = [[50, 130], [1200, 130]]
    elif change == 'via_frame':
        request['interfaces'][2]['source_frame'] = 'm2'
    elif change == 'via_enclosure':
        request['interfaces'][0]['support_bounds'] = [10, 10, 16, 16]
    elif change == 'duplicate_edge':
        claim = copy.deepcopy(request['interfaces'][0])
        claim['id'] += '-duplicate'
        request['interfaces'].append(claim)
    elif change == 'hypothesis_approval':
        request['path_hypotheses'][0]['connection_confirmed'] = True
    elif change == 'terminal_approval':
        request['branch']['terminal_candidate']['connection_confirmed'] = True
    elif change == 'terminal_wrong_metal':
        request['branch']['terminal_candidate']['from_metal_id'] = 'MID-H1'
    elif change == 'false_branch':
        request['branch']['metal_route'][1] = 'N2-U1-V1-CARRIER'
    elif change == 'unknown_branch':
        request['branch']['metal_route'][1] = 'AB-B-return-path'
    elif change == 'net_export':
        request['automatic_network_export_allowed'] = True
    elif change == 'projection':
        request['source_to_design_transform'] = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    with pytest.raises(ValueError, match=reason):
        prepare(ROOT, request)


def test_superseded_l3_cannot_reenter_a_group_with_old_human_reference(request_data):
    request = copy.deepcopy(request_data)
    source = ROOT / request['structural_groups']['path']
    document = json.loads(source.read_text())
    group = next(g for g in document['grouping_decisions'] if g['group_id']=='MID-AB-GROUP-A')
    group['M1_members'] = ['M1-T3-LOCAL', 'M1-L3-LOCAL']
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as tmp:
        path = Path(tmp) / 'tampered-group.json'
        path.write_text(json.dumps(document))
        request['structural_groups'] = dict(path=str(path.relative_to(ROOT)), sha256=digest(path))
        with pytest.raises(ValueError, match='Structural group contradicts human decision'):
            prepare(ROOT, request)


def test_m2_v2_cannot_be_retyped_as_v1_by_changing_an_inventory(request_data):
    request = copy.deepcopy(request_data)
    source = ROOT / request['interface_inventories'][2]['path']
    document = json.loads(source.read_text())
    document['reviewed_local_connections'][0]['via_layer'] = 'V1'
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as tmp:
        path = Path(tmp) / 'wrong-layer.json'
        path.write_text(json.dumps(document))
        request['interface_inventories'][2] = dict(
            path=str(path.relative_to(ROOT)), sha256=digest(path)
        )
        with pytest.raises(ValueError, match='Wrong interface layer pair'):
            prepare(ROOT, request)


def test_invalid_candidate_does_not_create_partial_review_package(request_data):
    request = copy.deepcopy(request_data)
    request['branch']['terminal_candidate']['connection_confirmed'] = True
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as tmp:
        path, output = Path(tmp) / 'request.json', Path(tmp) / 'output'
        path.write_text(json.dumps(request))
        with pytest.raises(ValueError, match='Terminal requires separate evidence'):
            deliver(ROOT, path, output)
        assert not output.exists()


def test_review_separates_candidate_routes_from_solid_geometry(result, request_data):
    text = review_page(result[0], result[1], request_data)
    assert 'stroke-dasharray="12 7"' in text
    assert 'terminal/index.html' in text
    assert all(f'data-toggle="{layer}"' in text for layer in ('M1', 'M2', 'M3', 'V1', 'V2'))
    assert '不是实测单孔' in text and '未宣布支路到器件端子完成' in text


def test_geometry_pass_does_not_hide_reversed_source_order(request_data):
    current = json.loads((ROOT / 'benchmarks/conductive-medium-source-review-v2/request-v1.json')
                         .read_text())
    old = copy.deepcopy(request_data)
    old['source_order_checks'] = current['source_order_checks']
    with pytest.raises(ValueError, match='Source relative order gate failed'):
        prepare(ROOT, old)


def test_local_endpoint_revision_keeps_reviewed_terminal_and_other_geometry():
    request = json.loads((ROOT / 'benchmarks/conductive-medium-source-review-v2/request-v1.json')
                         .read_text())
    model, report, _, _ = prepare(ROOT, request)
    assert report['source_order_audit']['status'] == 'PASS'
    assert model['branch']['terminal_closed']
    assert model['branch']['reviewed_terminal_connection']['target_structure'] == 'ring'
    assert not model['branch']['all_along_route_interfaces_checked']
    assert model['branch']['reviewed_terminal_connection']['body_terminal_assignment'] is None
    assert model['net_edges'] == [] and not model['complete_network']
    parent = json.loads((ROOT / 'docs/assets/conductive-medium-closeout-v1/model.json').read_text())
    before = {o['id']: o for group in parent['objects_by_layer'].values() for o in group}
    after = {o['id']: o for group in model['objects_by_layer'].values() for o in group}
    assert [key for key in before if before[key] != after[key]] == ['M1-N2-U1-U2']
    assert '不重复审批' in review_page(model, report, request)


def test_source_order_cannot_compare_two_independent_photo_frames(request_data):
    checks = [dict(id='bad-cross-layer', axis='x',
                   first=dict(id='M1-N2-U1-U2', extreme='min'),
                   second=dict(id='M2-J01', extreme='max'))]
    with pytest.raises(ValueError, match='same native frame'):
        source_order_audit(request_data['features_by_layer'], checks)


def test_terminal_approval_cannot_acquire_unreviewed_material_object_mapping():
    request = json.loads((ROOT / 'benchmarks/conductive-medium-source-review-v2/request-v1.json')
                         .read_text())
    state = json.loads((ROOT / request['reviewed_terminal_state']['path']).read_text())
    state['approved_terminal_connections'][0]['canonical_CT_object_ids'] = ['fabricated-CT']
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as tmp:
        p = Path(tmp) / 'bad-terminal.json'
        p.write_text(json.dumps(state))
        request['reviewed_terminal_state'] = dict(path=str(p.relative_to(ROOT)), sha256=digest(p))
        with pytest.raises(ValueError, match='exceeds reviewed scope'):
            prepare(ROOT, request)
