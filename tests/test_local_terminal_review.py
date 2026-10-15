"""A CT detection cannot become confirmed connectivity through window matching."""

import pytest

from silicon_eye.local_terminal_review import _verified, assign_contact
from silicon_eye.registration_audit import digest


def test_distinct_ct_supports_can_propose_same_diffusion_without_electrical_proof():
    zones = [{'id': 'shared', 'xywh_poly_crop': [10, 10, 30, 10]}]
    for center in [[15, 15], [30, 15]]:
        decision = assign_contact(center, [center[0]-2, 12, 4, 6], [0, 0, 50, 50], zones)
        assert decision['candidate_zone'] == 'shared'
        assert decision['status'] == 'candidate'


def test_merged_ct_support_touching_two_terminals_is_conflict():
    zones = [{'id': 'gate', 'xywh_poly_crop': [10, 10, 10, 10]},
             {'id': 'diffusion', 'xywh_poly_crop': [25, 10, 10, 10]}]
    decision = assign_contact([15, 15], [12, 12, 20, 6], [0, 0, 50, 50], zones)
    assert decision['status'] == 'conflict'
    assert decision['candidate_zone'] is None
    assert decision['bbox_touches_windows'] == ['gate', 'diffusion']


def test_unassigned_and_clipped_support_cannot_be_forced_to_nearest_terminal():
    zones = [{'id': 'gate', 'xywh_poly_crop': [10, 10, 10, 10]}]
    unmatched = assign_contact([35, 15], [32, 12, 5, 5], [0, 0, 50, 50], zones)
    assert unmatched['status'] == 'unknown'
    clipped = assign_contact([15, 15], [12, 12, 6, 6], [0, 18, 50, 30], zones)
    assert clipped['status'] == 'cropped_boundary_unknown'
    assert clipped['candidate_zone'] is None


def test_modified_evidence_is_rejected_before_using_approval(tmp_path):
    source = tmp_path / 'approval.json'
    source.write_text('{"count": 2}')
    binding = {'path': source.name, 'sha256': digest(source)}
    assert _verified(tmp_path, binding) == source
    source.write_text('{"count": 1}')
    with pytest.raises(ValueError, match='Changed evidence'):
        _verified(tmp_path, binding)
