"""Device networks preserve terminal identity and image-only dimensions."""

import numpy as np
import pytest

from silicon_eye.device_network_review import device_connections, geometry_proxy, poly_to_m1


def test_routes_are_mapped_back_to_native_m1_with_inverse_transform():
    matrix = np.array([[2, 0, 3], [0, 2, 4], [0, 0, 1]], float)
    assert np.allclose(poly_to_m1([[3, 4]], matrix, [100, 200]), [[50, 100]])


def test_m1_can_tie_distinct_gates_without_collapsing_physical_identities():
    devices = [{'id': 'Q1', 'gate': 'G1', 'diffusion_terminals': ['A', 'M']},
               {'id': 'Q2', 'gate': 'G2', 'diffusion_terminals': ['M', 'B']}]
    zones = [{'id': i} for i in ['G1', 'G2', 'A', 'M', 'B']]
    networks = [{'id': 'MG', 'terminals': ['G1', 'G2', 'M']},
                {'id': 'NA', 'terminals': ['A']}, {'id': 'NB', 'terminals': ['B']}]
    rows = device_connections(devices, zones, networks)
    assert [d['physical_gate'] for d in rows] == ['G1', 'G2']
    assert rows[0]['G'] == rows[1]['G'] == 'MG'
    assert rows[0]['diffusion_B'] == rows[1]['diffusion_A'] == 'MG'
    assert all(d['bulk'] == d['source_drain_polarity'] == 'unknown' for d in rows)
    networks[1]['terminals'].append('M')
    with pytest.raises(ValueError, match='multiple candidate networks'):
        device_connections(devices, zones, networks)


@pytest.mark.parametrize('axis,ys,xs,width,length', [
    ('x', slice(5, 15), slice(7, 10), 10, 3),
    ('y', slice(5, 8), slice(4, 16), 12, 3),
])
def test_dimensions_follow_channel_axis_and_never_claim_physical_scale(axis, ys, xs, width, length):
    aa = np.ones((20, 20), bool)
    poly = np.zeros_like(aa)
    poly[ys, xs] = True
    result = geometry_proxy(aa, poly, np.zeros_like(poly), [0, 0, 20, 20], axis)
    assert result['W_span_px'] == width
    assert result['L_run_median_px'] == length
    assert result['physical_scale'] == 'unknown'
    assert not result['window_clipped']


def test_absent_visible_overlap_does_not_invent_dimensions():
    empty = np.zeros((20, 20), bool)
    assert geometry_proxy(empty, empty, empty, [0, 0, 20, 20], 'x')['status'].startswith('unknown')


def test_native_observation_windows_use_source_origin_without_mutating_source():
    from silicon_eye.device_network_review import annotate_native_observations

    image = np.zeros((100, 150, 3), np.uint8)
    view = dict(crop_xywh_native=[50, 30, 70, 60], observations=[dict(
        id='A', status='AI_visual_candidate', xywh_native=[60, 40, 20, 10],
        suggested_net_ids=['NA'])])
    marked = annotate_native_observations(image, view, {'NA'})
    assert marked.shape == (60, 70, 3)
    assert marked[10, 10].any() and marked[19, 29].any()
    assert not image.any()
    view['observations'][0]['xywh_native'][0] = 49
    with pytest.raises(ValueError, match='outside native view'):
        annotate_native_observations(image, view, {'NA'})


def test_observation_windows_cannot_confirm_or_assign_unregistered_cross_layer_nets():
    from silicon_eye.device_network_review import annotate_native_observations

    image = np.zeros((100, 150, 3), np.uint8)
    obs = dict(id='P1', status='human_confirmed', xywh_native=[60, 40, 20, 10],
               suggested_net_ids=['NA'])
    view = dict(crop_xywh_native=[50, 30, 70, 60], observations=[obs],
                correspondence_status='unregistered')
    with pytest.raises(ValueError, match='cannot confirm topology'):
        annotate_native_observations(image, view, {'NA'})
    obs['status'] = 'AI_visual_candidate'
    with pytest.raises(ValueError, match='must stay unassigned'):
        annotate_native_observations(image, view, {'NA'})
    obs['suggested_net_ids'] = ['NO_SUCH_NET']
    with pytest.raises(ValueError, match='unknown network'):
        annotate_native_observations(image, view, {'NA'})
    obs['suggested_net_ids'] = []
    annotate_native_observations(image, view, {'NA'})
