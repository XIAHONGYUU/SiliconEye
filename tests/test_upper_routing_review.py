"""Upper-metal diagnostics cannot quietly promote identity into electrical joins."""
from copy import deepcopy

import cv2
import numpy as np
import pytest

from silicon_eye.upper_routing_review import (
    bright_center,
    structure_identities,
    translation_diagnostic,
)


def identity_case():
    decision = dict(id='M2_P2_V3_identity', status='human_confirmed', source_layer='m2',
                    observation_id='P2', observation_window_xywh_native=[10,20,30,40],
                    corresponding_devices=['V3_Q1','V3_Q2'], connectivity_changes=[],
                    terminal_to_segment_mapping='unknown')
    review = dict(actor='human', decisions=[decision])
    views = [dict(source='m2_source', observations=[dict(id='P2',xywh_native=[10,20,30,40])])]
    devices = [dict(id='V3_Q1'), dict(id='V3_Q2')]
    return review, views, devices


def test_identity_consumed_without_inventing_terminal_mapping_or_mutating_record():
    review, views, devices = identity_case()
    original = deepcopy(review)
    facts = structure_identities(review, views, devices)
    assert facts[0]['terminal_to_segment_mapping'] == 'unknown'
    assert facts[0]['connectivity_changes'] == []
    facts[0]['status'] = 'changed'
    assert review == original
    views[0]['observations'][0]['xywh_native'][0] += 1
    with pytest.raises(ValueError, match='window differs'):
        structure_identities(review, views, devices)


def test_identity_cannot_authorize_new_electrical_join_or_other_devices():
    review, views, devices = identity_case()
    review['decisions'][0]['connectivity_changes'] = [['N3_A','N3_GM']]
    with pytest.raises(ValueError, match='electrical change'):
        structure_identities(review, views, devices)
    review['decisions'][0]['connectivity_changes'] = []
    review['decisions'][0]['corresponding_devices'] = ['V1_Q1']
    with pytest.raises(ValueError, match='unexpected devices'):
        structure_identities(review, views, devices)
    review['actor'] = 'AI'
    with pytest.raises(ValueError, match='human record'):
        structure_identities(review, views, devices)


def test_translation_has_correct_direction_and_does_not_fit_held_out_error():
    fit = [dict(id='array',source_xy=[10,20],reference_xy=[15,18])]
    check = [dict(id='bar',source_xy=[30,40],reference_xy=[38,42])]
    result = translation_diagnostic(fit, check)
    assert np.allclose(np.array(result['matrix_source_to_reference'])[:2,2], [5,-2])
    assert result['held_out'][0]['residual_px'] == 5
    assert result['acceptance'] == 'unknown'
    check[0]['id'] = 'array'
    with pytest.raises(ValueError, match='disjoint'):
        translation_diagnostic(fit, check)


def test_bright_center_preserves_native_origin_and_rejects_weak_or_outside_windows():
    image = np.zeros((100,150,3),np.uint8)
    cv2.circle(image,(82,63),8,(255,255,255),-1)
    result = bright_center(image,[60,40,50,45],.8)
    assert np.allclose(result['xy_native'],[82,63],atol=.1)
    with pytest.raises(ValueError, match='contrast'):
        bright_center(np.zeros_like(image),[60,40,50,45],.8)
    with pytest.raises(ValueError, match='outside'):
        bright_center(image,[140,40,50,45],.8)
