"""Photo-path consistency must not be confused with accepted physical geometry."""
import pytest

from silicon_eye.conductive_quality import source_shape_audit


def audit(native, design):
    return source_shape_audit({'M2': [dict(id='branch', native_path=native,
                                          design_path=design)]})


def test_skew_and_collinear_sampling_do_not_create_a_false_turn():
    result = audit([[0, 0], [2, 40], [4, 80], [-20, 81]],
                   [[100, 100], [100, 180], [76, 180]])
    assert result['status'] == 'PASS'
    assert result['checks'][0]['native_turns'] == result['checks'][0]['design_turns']


def test_orthogonal_return_mirrored_to_other_side_fails():
    assert audit([[1210, 2917], [1210, 2950], [1187, 2950]],
                 [[548, 1230], [548, 1260], [570, 1260]])['status'] == 'FAIL'


def test_rigid_rotation_preserves_turn_handedness():
    assert audit([[0, 0], [0, 30], [-20, 30]],
                 [[100, 100], [70, 100], [70, 80]])['status'] == 'PASS'


def test_oblique_source_is_unqualified_instead_of_pass():
    result = audit([[0, 0], [10, 10], [5, 20]], [[0, 0], [0, 20], [10, 20]])
    assert result['status'] == 'PARTIAL'
    assert result['checks'][0]['status'] == 'NOT_EVALUATED'


def test_omitted_source_turn_is_not_a_straight_accepted_wire():
    assert audit([[0, 0], [0, 30], [-20, 30]], [[0, 0], [30, 0]])['status'] == 'FAIL'


@pytest.mark.parametrize('points', [[], [[0, 0]], [[0, float('nan')], [1, 0]]])
def test_invalid_source_paths_fail_clearly(points):
    with pytest.raises(ValueError, match='shape path'):
        audit(points, [[0, 0], [1, 0]])
