"""Human partial approval must replace stale candidates without inventing joins."""

from copy import deepcopy

import pytest

from silicon_eye.local_schematic import render_schematic
from silicon_eye.network_reviews import apply_network_reviews


def example():
    networks = [dict(id='N3_MG', terminals=['V3_G1', 'V3_G2', 'V3_M'], status='candidate'),
                dict(id='N3_A', terminals=['V3_A'], status='candidate'),
                dict(id='N3_B', terminals=['V3_B'], status='candidate')]
    decisions = [dict(id='V3_shared_middle', status='human_confirmed',
                      participants=['V3_Q1', 'V3_Q2']),
                 dict(id='V3_common_electrical_gate_net', status='human_confirmed',
                      physical_gate_ids=['V3_G1', 'V3_G2'], common_net_id='N3_G',
                      connection_layer='at_least_M2'),
                 dict(id='V3_gate_to_shared_diffusion', status='unknown')]
    return networks, [dict(actor='human', decisions=decisions)]


def test_common_gate_does_not_approve_gate_to_diffusion_and_input_stays_immutable():
    networks, reviews = example()
    old = deepcopy(networks)
    result = apply_network_reviews(networks, reviews)
    mapping = {t: n['id'] for n in result['networks'] for t in n['terminals']}
    assert mapping['V3_G1'] == mapping['V3_G2'] == 'N3_G'
    assert mapping['V3_M'] == 'N3_M' != mapping['V3_G1']
    assert result['unresolved_relations'][0]['status'] == 'unknown'
    assert 'N3_MG' not in {n['id'] for n in result['networks']}
    assert networks == old
    assert apply_network_reviews(result['networks'], reviews)['networks'] == result['networks']


def test_local_m1_gap_does_not_assert_global_isolation():
    record = dict(actor='human', decisions=[dict(id='V12_route_gap', status='human_confirmed',
                  local_m1_join=False, local_route_ids=['N12_A', 'N12_BG'])])
    fact = apply_network_reviews([], [record])['facts'][0]
    assert fact['layer'] == 'M1'
    assert fact['global_equivalence'] == 'unknown'


def test_reviewed_local_gap_rejects_new_m1_merge_but_not_possible_m2_join():
    record = dict(actor='human', decisions=[dict(id='V12_route_gap', status='human_confirmed',
                  local_m1_join=False, local_route_ids=['N12_A', 'N12_BG'])])
    net = dict(id='MERGED', terminals=['V1_A', 'V2_A', 'V1_B', 'V2_G'])
    with pytest.raises(ValueError, match='contradicts reviewed local gap'):
        apply_network_reviews([net], [record])
    net['connection_layer'] = 'M2'
    result = apply_network_reviews([net], [record])
    assert result['facts'][0]['global_equivalence'] == 'unknown'


def test_unrecognized_confirmed_decision_fails_instead_of_being_silently_dropped():
    record = dict(actor='human', decisions=[dict(id='NEW_UNSUPPORTED', status='human_confirmed')])
    with pytest.raises(ValueError, match='Unsupported confirmed'):
        apply_network_reviews([], [record])


def test_missing_shared_diffusion_approval_is_not_invented():
    networks, reviews = example()
    reviews[0]['decisions'].pop(0)
    with pytest.raises(ValueError, match='Missing human shared'):
        apply_network_reviews(networks, reviews)


def test_ai_cannot_supply_human_confirmation_or_silently_drop_unknown_relation():
    networks, reviews = example()
    reviews[0]['actor'] = 'AI'
    with pytest.raises(ValueError, match='Only human'):
        apply_network_reviews(networks, reviews)
    reviews[0]['actor'] = 'human'
    reviews[0]['decisions'].pop()
    with pytest.raises(ValueError, match='unresolved gate-to-M'):
        apply_network_reviews(networks, reviews)


def test_conflicting_reviews_fail_instead_of_using_last_record():
    networks, reviews = example()
    conflicting = deepcopy(reviews[0]['decisions'][1])
    conflicting['common_net_id'] = 'DIFFERENT'
    reviews.append(dict(actor='human', decisions=[conflicting]))
    with pytest.raises(ValueError, match='Conflicting common-gate'):
        apply_network_reviews(networks, reviews)


def test_standalone_svg_preserves_four_devices_and_unresolved_relation(tmp_path):
    devices = [dict(id=f'Q{i}', G='N3_G', diffusion_A='N3_A', diffusion_B='N3_M',
                    bulk='unknown') for i in range(4)]
    render_schematic(tmp_path, devices, {})
    svg = (tmp_path / 'local-schematic.svg').read_text()
    assert all(f'Q{i}' in svg for i in range(4))
    assert 'N3_G &lt;-&gt; N3_M' in svg
    assert 'do NOT prove isolation' in svg
    assert svg.count('Bulk ?') == 4
    assert '<marker' not in svg
    assert (tmp_path / 'local-schematic.png').stat().st_size > 1000


def test_explicit_human_supersession_joins_gate_and_middle_without_merging_devices(tmp_path):
    networks, reviews = example()
    previous = deepcopy(reviews[0]['decisions'][-1])
    approval = dict(id='V3_gate_to_shared_diffusion', status='human_confirmed',
                    connected=True, net_ids=['N3_G', 'N3_M'], common_net_id='N3_GM',
                    supersedes_decision=previous)
    reviews.append(dict(actor='human', decisions=[approval]))
    result = apply_network_reviews(networks, reviews)
    joined = next(n for n in result['networks'] if n['id'] == 'N3_GM')
    assert set(joined['terminals']) == {'V3_G1', 'V3_G2', 'V3_M'}
    assert result['unresolved_relations'] == []
    assert apply_network_reviews(result['networks'], reviews)['networks'] == result['networks']
    devices = [dict(id='V3_Q1', G='N3_GM', diffusion_A='N3_A', diffusion_B='N3_GM'),
               dict(id='V3_Q2', G='N3_GM', diffusion_A='N3_GM', diffusion_B='N3_B')]
    render_schematic(tmp_path, devices, {}, result['unresolved_relations'])
    svg = (tmp_path / 'local-schematic.svg').read_text()
    assert 'V3_Q1' in svg and 'V3_Q2' in svg
    assert 'UNRESOLVED' not in svg and 'connected as N3_GM' in svg
    approval.pop('supersedes_decision')
    with pytest.raises(ValueError, match='Conflicting gate-to-diffusion'):
        apply_network_reviews(networks, reviews)


def test_invalid_confirmation_cannot_silently_join_gate_and_middle():
    networks, reviews = example()
    reviews[0]['decisions'][-1] = dict(id='V3_gate_to_shared_diffusion',
                                    status='human_confirmed', connected=False)
    with pytest.raises(ValueError, match='Invalid confirmed gate-to-M'):
        apply_network_reviews(networks, reviews)
