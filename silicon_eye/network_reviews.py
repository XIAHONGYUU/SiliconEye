"""Apply explicit human topology decisions without changing physical gate identities."""

from __future__ import annotations

from copy import deepcopy


def apply_network_reviews(networks: list, reviews: list) -> dict:
    """Preserve unknown equivalence instead of treating partial approval as a net union."""
    current = deepcopy(networks)
    facts, superseded = [], []
    common_gate = None
    gate_to_m = None
    for review in reviews:
        if review.get('actor') != 'human':
            raise ValueError('Only human review records may supply confirmed topology')
        for decision in review.get('decisions', []):
            name, status = decision['id'], decision['status']
            if name == 'V12_route_gap' and status == 'human_confirmed':
                if decision['local_m1_join'] is not False:
                    raise ValueError('Conflicting local M1 gap decision')
                side_a, side_b = {'V1_A', 'V2_A'}, {'V1_B', 'V2_G'}
                for net in current:
                    members = set(net['terminals'])
                    if members & side_a and members & side_b and (
                        net.get('connection_layer', 'M1') == 'M1'
                    ):
                        raise ValueError('M1 candidate merge contradicts reviewed local gap')
                facts.append(dict(id=name, status=status, kind='local_layer_disconnection',
                                  layer='M1', networks=decision['local_route_ids'],
                                  physical_terminal_groups=[sorted(side_a), sorted(side_b)],
                                  global_equivalence='unknown'))
            elif name == 'V3_shared_middle' and status == 'human_confirmed':
                facts.append(dict(id=name, status=status, kind='shared_diffusion',
                                  terminals=['V3_M'], devices=decision['participants']))
            elif name == 'V3_common_gate' and status == 'human_rejected':
                facts.append(dict(id=name, status=status, kind='local_poly_connection',
                                  connected=False, physical_gates=decision['gate_ids']))
            elif name == 'V3_common_electrical_gate_net' and status == 'human_confirmed':
                if common_gate is not None and common_gate != decision:
                    raise ValueError('Conflicting common-gate reviews')
                common_gate = decision
            elif name == 'V3_gate_to_shared_diffusion':
                if (gate_to_m is not None and gate_to_m != decision and not (
                    gate_to_m['status'] == 'unknown' and status == 'human_confirmed' and
                    decision.get('supersedes_decision') == gate_to_m
                )):
                    raise ValueError('Conflicting gate-to-diffusion reviews')
                gate_to_m = decision
            elif status in {'human_confirmed', 'human_rejected'}:
                raise ValueError(f'Unsupported confirmed topology decision: {name}')
    if common_gate is not None:
        if not any(f['id'] == 'V3_shared_middle' for f in facts):
            raise ValueError('Missing human shared-diffusion decision')
        if gate_to_m is None or gate_to_m['status'] not in {'unknown', 'human_confirmed'}:
            raise ValueError('Common-gate review must specify the unresolved gate-to-M relation')
        joined = gate_to_m['status'] == 'human_confirmed'
        if joined and (gate_to_m.get('connected') is not True or
                       gate_to_m.get('net_ids') != ['N3_G', 'N3_M'] or
                       gate_to_m.get('common_net_id') != 'N3_GM'):
            raise ValueError('Invalid confirmed gate-to-M connection')
        gates = common_gate['physical_gate_ids']
        if set(gates) != {'V3_G1', 'V3_G2'}:
            raise ValueError('Unexpected physical gate identities')
        targets = set(gates) | {'V3_M'}
        preserved = []
        for net in current:
            touched = targets & set(net['terminals'])
            if touched:
                superseded.append(deepcopy(net))
                net['terminals'] = [t for t in net['terminals'] if t not in targets]
            if net['terminals']:
                preserved.append(net)
        if not targets <= {t for n in current for t in n['terminals']} | {
            t for n in superseded for t in n['terminals']
        }:
            raise ValueError('Reviewed terminals missing from candidate topology')
        current = preserved + [
            dict(id=common_gate['common_net_id'], terminals=list(gates),
                 status='human_confirmed_gate_relation', traces_xy_poly_crop=[],
                 connection_layer=common_gate['connection_layer'],
                 visual_basis='Human confirms gate-to-gate net via at least M2.',
                 uncertainty='Exact M2 path and gate-to-M connection remain unresolved.'),
            dict(id='N3_M', terminals=['V3_M'], status='human_confirmed_shared_diffusion',
                 traces_xy_poly_crop=[], visual_basis='Human confirms shared diffusion M.',
                 uncertainty='Connection to the common gate net remains unknown.'),
        ]
        if joined:
            current = [n for n in current if n['id'] not in {'N3_G', 'N3_M'}] + [
                dict(id='N3_GM', terminals=list(gates)+['V3_M'],
                     status='human_confirmed_gate_diffusion_relation',
                     traces_xy_poly_crop=[], connection_layer='not_resolved',
                     visual_basis='Human confirms common gate connected to shared diffusion.',
                     uncertainty='Exact metal/via path not script-validated; bulk/type unknown.')]
            facts.append(deepcopy(gate_to_m))
        facts.append(deepcopy(common_gate))
    unresolved = ([] if gate_to_m is None or gate_to_m['status'] == 'human_confirmed'
                  else [deepcopy(gate_to_m)])
    return dict(networks=current, facts=facts, superseded_hypotheses=superseded,
                unresolved_relations=unresolved)
