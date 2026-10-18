"""Sparse stroke training preserves held checks and unknown material pixels."""

import numpy as np
import pytest

from silicon_eye.aa_scribble_eval import stroke_labels


def case():
    return dict(
        native_bbox=[100, 200, 140, 230],
        prompts=[dict(class_name="AA", native_xy=[103, 203], radius=1)],
        checks=[dict(class_name="AA", native_xy=[120, 210])],
    )


def test_strokes_leave_unknowns_and_protect_check_guard_and_invalid_pixels():
    valid = np.ones((30, 40), bool)
    valid[:, 30:] = False
    strokes = [dict(class_name="AA", native_points=[[105, 210], [135, 210]], thickness=1)]
    labels = stroke_labels(case(), strokes, valid, guard=3)
    assert labels[10, 10] == 1
    assert np.all(labels[7:14, 17:24] == -1)
    assert np.all(labels[:, 30:] == -1)
    assert labels[20, 10] == -1
    assert labels[3, 3] == 1


def test_conflicting_stroke_cannot_silently_change_confirmed_center():
    strokes = [dict(class_name="background", native_points=[[102, 203], [110, 203]], thickness=1)]
    with pytest.raises(ValueError, match="Conflicting"):
        stroke_labels(case(), strokes, np.ones((30, 40), bool), guard=2)


def test_outside_crop_and_unknown_class_are_rejected():
    strokes = [dict(class_name="AA", native_points=[[90, 203], [110, 203]], thickness=1)]
    with pytest.raises(ValueError, match="outside"):
        stroke_labels(case(), strokes, np.ones((30, 40), bool), guard=2)
    strokes[0]["class_name"] = "unknown"
    with pytest.raises(ValueError, match="Unknown"):
        stroke_labels(case(), strokes, np.ones((30, 40), bool), guard=2)
