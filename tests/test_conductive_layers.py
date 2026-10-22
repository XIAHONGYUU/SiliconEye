"""A common snapshot must preserve scoped reviews and not invent full networks."""

import copy
import json
import tempfile
from pathlib import Path

import pytest
from shapely.geometry import Polygon, box

from silicon_eye.conductive_layers import LAYERS, deliver, load_registry
from silicon_eye.geometry_reconstruction import digest
from silicon_eye.joint_layers import load_snapshot, run, write_snapshot
from silicon_eye.layer_review import model_svg, records
from silicon_eye.metal_reconstruction import feature_polygon

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / 'benchmarks/conductive-stack-v1/request-v1.json'


@pytest.fixture(scope='module')
def package():
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as temp:
        out = Path(temp) / 'delivery'
        report = deliver(ROOT, REQUEST, out)
        yield out, report


def test_continuous_chain_preserves_ids_geometry_source_and_review_scope(package):
    out, report = package
    model = json.loads((out / 'model.json').read_text())
    parent = json.loads((ROOT / 'docs/assets/m1-v1-m2-joint-reviewed-v2/model.json').read_text())
    assert list(model['objects_by_layer']) == list(LAYERS)
    assert report['object_counts'] == dict(M1=9, V1=9, M2=1, V2=1, M3=2)
    assert model['continuous_chain']['conductor_ids'] == ['M1-P08', 'M2-J01', 'M3-J-B1']
    assert model['continuous_chain']['via_layers'] == ['V1', 'V2']
    assert len(model['reviewed_local_connections']) == 2
    assert model['net_edges'] == [] and not model['continuous_chain']['complete_network']
    assert report['new_physical_connections'] == 0 and not report['human_questions']
    assert model['source_to_design_transform'] is None
    m1 = {o['id']: o for o in model['objects_by_layer']['M1']}
    for old in parent['inherited_M1_objects']:
        assert m1[old['id']]['inherited_record'] == old
        effective = copy.deepcopy(old)
        if old['id'] == 'M1-P08':
            effective['local_parts'].append(parent['proposed_M1_addition']['part'])
        actual = Polygon(m1[old['id']]['geometry']['outer_xy'],
                         m1[old['id']]['geometry']['holes_xy'])
        assert actual.equals(feature_polygon(effective))
    cut = model['objects_by_layer']['V2'][0]
    assert cut['id'] == 'V2-J-EDGE-SUPPORT'
    assert cut['kind'] == 'via_group_support_proxy' and cut['physical_cut_count'] is None
    assert cut['source_frame'] == 'm2'
    assert cut['source_observation']['source_bounds'] == [1935, 1905, 1953, 1953]
    assert model['objects_by_layer']['V1'][0]['source_observation']['m1_xy'] == [1969, 1939]
    assert model['objects_by_layer']['V1'][0]['source_observation']['m2_xy'] == [1961, 1912]
    assert model['objects_by_layer']['M3'][1]['role'] == 'context_only'
    assert all(x['status'] == 'PASS' for x in model['geometry_audits'].values())


def test_common_loader_renderer_and_audit_consume_five_layers_without_reextracting(package):
    out, _ = package
    current = load_snapshot(ROOT, out / 'joint-snapshot.json')
    before = load_snapshot(ROOT, ROOT / 'configs/joint-work-layer-v3.json')
    assert current['materials'] == before['materials']
    assert current['contacts'] == before['contacts']
    assert current['values'] == before['values']
    assert len(records(current, 'M2')) == 1
    assert len(records(current, 'CT')) == 10287
    svg = model_svg(current, [1900, 1840, 2520, 2320])
    for layer in LAYERS:
        assert f'data-layer="{layer}"' in svg
    assert 'data-object="M1-P08"' in svg
    assert current['conductors']['automatic_network_export_allowed'] is False
    report = run(ROOT, out / 'joint-snapshot.json', out.parent / 'audit')
    assert report['status'] == 'PASS'
    assert report['conductive_layers']['reviewed_interface_count'] == 2
    assert report['conductive_layers']['object_counts']['M3'] == 2


@pytest.mark.parametrize('change', ['destination', 'geometry', 'missing_via'])
def test_registry_reload_rejects_destination_geometry_or_via_drift(package, change):
    out, _ = package
    model = json.loads((out / 'model.json').read_text())
    if change == 'destination':
        model['reviewed_local_connections'][1]['upper_metal_id'] = 'M3-J-B0'
    elif change == 'geometry':
        model['objects_by_layer']['M2'][0]['geometry']['outer_xy'][0][0] += 6
    else:
        model['objects_by_layer']['V1'].pop()
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as tmp:
        p = Path(tmp) / 'mutated.json'
        p.write_text(json.dumps(model))
        ref = dict(path=str(p.relative_to(ROOT)), sha256=digest(p))
        manifest = json.loads((out / 'joint-snapshot.json').read_text())
        with pytest.raises(ValueError, match='registry drifted'):
            load_registry(ROOT, ref, manifest)


def test_snapshot_write_preserves_registry_and_blocks_unscoped_conductive_mutation(package):
    out, _ = package
    snapshot = load_snapshot(ROOT, out / 'joint-snapshot.json')
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as tmp:
        path = write_snapshot(ROOT, snapshot, Path(tmp) / 'unchanged')
        restored = load_snapshot(ROOT, path)
        assert restored['conductors'] == snapshot['conductors']
        broken = copy.deepcopy(snapshot)
        broken['conductors']['objects_by_layer']['M1'][0]['geometry']['outer_xy'][0][0] += 10
        with pytest.raises(ValueError, match='outside a scoped transaction'):
            write_snapshot(ROOT, broken, Path(tmp) / 'rejected')
        assert not (Path(tmp) / 'rejected').exists()


def test_all_declared_via_support_is_enclosed_by_the_two_named_metals(package):
    out, _ = package
    m = json.loads((out / 'model.json').read_text())
    metal = {o['id']: Polygon(o['geometry']['outer_xy'], o['geometry']['holes_xy'])
             for layer in ['M1', 'M2', 'M3'] for o in m['objects_by_layer'][layer]}
    for layer in ['V1', 'V2']:
        for via in m['objects_by_layer'][layer]:
            cut = via['inherited_record']
            bearing = box(*cut['bounds']).buffer(2, join_style='mitre')
            assert metal[cut['lower_metal_id']].covers(bearing)
            assert metal[cut['upper_metal_id']].covers(bearing)


def test_common_review_schema_allows_five_inspect_targets_but_no_metal_revision(package):
    from silicon_eye.layer_review import ReviewRequest

    out, _ = package
    ref = dict(path=str((out / 'joint-snapshot.json').relative_to(ROOT)),
               sha256=digest(out / 'joint-snapshot.json'))
    for layer in LAYERS:
        request = dict(schema_version=1, document_kind='layer_reconstruction_review',
                       id='five-layer-inspect', target_layer=layer, mode='inspect', snapshot=ref,
                       windows=[dict(id='chain', layout_bounds=[1900, 1840, 2520, 2320])])
        assert ReviewRequest.model_validate(request).target_layer == layer
        request['mode'] = 'revise'
        with pytest.raises(ValueError, match='inspect mode only'):
            ReviewRequest.model_validate(request)


def test_existing_review_entry_delivers_all_five_layers_and_rejects_missing_registry(package):
    from silicon_eye.layer_review import deliver as review_deliver
    out, _ = package
    request = dict(
        schema_version=1, document_kind='layer_reconstruction_review', id='five-layer-read-test',
        target_layer='M1', mode='inspect',
        snapshot=dict(path=str((out / 'joint-snapshot.json').relative_to(ROOT)),
                      sha256=digest(out / 'joint-snapshot.json')),
        windows=[dict(id='chain', layout_bounds=[1900, 1840, 2520, 2320])],
    )
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as tmp:
        p = Path(tmp) / 'request.json'
        p.write_text(json.dumps(request))
        output = Path(tmp) / 'review'
        r = review_deliver(ROOT, p, output)
        assert r['status'] == 'PASS' and r['conductive_layers']['reviewed_interface_count'] == 2
        manifest = json.loads((output / 'manifest.json').read_text())
        assert manifest['model_counts']['M1'] == 9 and manifest['model_counts']['M2'] == 1
        assert manifest['model_counts']['CT'] == 10287
        page = (output / 'index.html').read_text()
        for layer in LAYERS:
            assert f'data-toggle="{layer}"' in page
        request['snapshot'] = dict(path='configs/joint-work-layer-v3.json',
                                   sha256=digest(ROOT / 'configs/joint-work-layer-v3.json'))
        p.write_text(json.dumps(request))
        with pytest.raises(ValueError, match='requires an attached registry'):
            review_deliver(ROOT, p, Path(tmp) / 'rejected')
        assert not (Path(tmp) / 'rejected').exists()
