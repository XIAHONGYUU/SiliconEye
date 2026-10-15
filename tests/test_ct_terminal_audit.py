"""Review completeness and uncertainty must survive CT evidence export."""

import numpy as np
import pytest

from silicon_eye.ct_terminal_audit import support_evidence, validate_reviews


@pytest.mark.parametrize('ids', [[1], [1, 1]])
def test_missing_or_duplicate_contact_reviews_fail(ids):
    contacts = [{'roi_id': 'V3', 'ct_component_id': i, 'candidate_zone': 'M'} for i in [1, 2]]
    reviews = [{'roi_id': 'V3', 'ct_component_id': i, 'association_review': 'candidate',
                'candidate_terminal': 'M'} for i in ids]
    with pytest.raises(ValueError, match='Duplicate, missing or extra'):
        validate_reviews(reviews, contacts, {'M': {}})


def test_ai_window_matching_cannot_promote_to_human_confirmed():
    contacts = [{'roi_id': 'V3', 'ct_component_id': 1, 'candidate_zone': 'M'}]
    reviews = [dict(**contacts[0], association_review='confirmed', candidate_terminal='M')]
    with pytest.raises(ValueError, match='cannot be automatically confirmed'):
        validate_reviews(reviews, contacts, {'M': {}})


def test_contact_in_unknown_poly_is_not_negative_material_evidence():
    component = np.ones((4, 4), bool)
    empty = np.zeros_like(component)
    result = support_evidence(component, empty, component, component,
                              np.zeros((4, 4), int), {})
    assert result['poly_unknown_overlap_px'] == 16
    assert result['poly_positive_overlap_px'] == 0
    assert result['confirmed_material_absence'] is False
    assert result['electrical_connection'] == 'unknown'


def test_ct_mask_overlap_with_two_gate_domains_does_not_merge_gates():
    component = np.ones((4, 4), bool)
    labels = np.ones((4, 4), int)
    labels[:, 2:] = 2
    result = support_evidence(component, component, np.zeros_like(component),
                              component, labels, {'G1': 1, 'G2': 2})
    assert result['poly_gate_domains_touched'] == ['G1', 'G2']
    assert result['electrical_connection'] == 'unknown'
