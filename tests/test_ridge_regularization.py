import numpy as np
import pytest

from silicon_eye.ridge_regularization import horizontal_candidate


def test_sloped_photo_becomes_local_rectangle_without_adopting_transform():
    image = np.full((120, 240), 25, dtype=np.uint8)
    for x in range(240):
        y = 50 + x // 60
        image[y - 5:y + 6, x] = 210
    fragments = [
        dict(fragment_id="a", points=[[x, 50 + x // 60] for x in range(20, 100, 4)]),
        dict(fragment_id="b", points=[[x, 50 + x // 60] for x in range(104, 224, 4)]),
    ]
    result = horizontal_candidate(image, fragments, [dict(fragments=["a", "b"])])
    assert result["photometric_width_px"] == 11
    assert result["local_polygon"] == [[0, 0], [200, 0], [200, 11], [0, 11]]
    assert result["source_y_excursion_px"] == 3
    assert result["source_to_design_transform"] is None
    assert result["physical_endpoints"] == "unknown"
    assert result["geometry_adopted"] is False
    with pytest.raises(ValueError, match="Unreviewed adjacent pair"):
        horizontal_candidate(image, fragments, [])


def test_no_width_is_invented_for_blank_or_source_clipped_path():
    fragments = [dict(fragment_id="a", points=[[20, 50], [70, 50]]),
                 dict(fragment_id="b", points=[[80, 50], [140, 50]])]
    with pytest.raises(ValueError, match="Insufficient ridge contrast"):
        horizontal_candidate(np.zeros((120, 200)), fragments, [dict(fragments=["a", "b"])])
    for f in fragments:
        f["points"] = [[x, 2] for x, _ in f["points"]]
    with pytest.raises(ValueError, match="source-clipped"):
        horizontal_candidate(np.zeros((120, 200)), fragments, [dict(fragments=["a", "b"])])


def test_wide_band_edge_cannot_be_silently_treated_as_a_narrow_metal_center():
    image = np.full((160, 200), 25, dtype=np.uint8)
    image[48:115, :] = 210
    fragments = [dict(fragment_id="a", points=[[20, 52], [70, 52]]),
                 dict(fragment_id="b", points=[[80, 52], [140, 52]])]
    with pytest.raises(ValueError, match="sampling limit"):
        horizontal_candidate(image, fragments, [dict(fragments=["a", "b"])])
