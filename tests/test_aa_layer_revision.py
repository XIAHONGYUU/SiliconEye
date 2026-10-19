"""Scoped layer revision must preserve outside material and source extent."""

import numpy as np
import pytest
from shapely.geometry import Polygon

from silicon_eye.aa_completion import polygon_record, source_polygon
from silicon_eye.aa_layer_revision import edge_warp, revise_object
from silicon_eye.geometry_reconstruction import object_polygon


def example():
    material = Polygon(
        [(0, 0), (100, 0), (100, 80), (0, 80)],
        [[(10, 10), (90, 10), (90, 35), (10, 35)], [(10, 45), (90, 45), (90, 70), (10, 70)]],
    )
    obj = polygon_record("AA-test", material)
    obj.update(
        structure_group="group",
        source_geometry={
            "outer_xy": list(material.exterior.coords)[:-1],
            "holes_xy": [list(h.coords)[:-1] for h in material.interiors],
        },
    )
    group = dict(
        id="group",
        canonical_to_source=np.eye(3).tolist(),
        explicit_affine_layout=np.eye(3).tolist(),
    )
    base = dict(groups=[group])
    operation = dict(
        id="remove-false-crossbar",
        object_id="AA-test",
        kind="canonical_cut",
        cut_boxes=[[10, 35, 90, 45]],
        expected_components=1,
        allowed_native_bbox=[10, 35, 90, 45],
        reason="known false crossbar",
    )
    return obj, base, operation


def test_confirmed_crossbar_removal_keeps_outer_enclosure_and_only_joins_holes(tmp_path):
    obj, base, op = example()
    revised, audit = revise_object(tmp_path, obj, base, op, None, dict(domain_leak_area_px2=0.05))
    before = object_polygon(obj)
    after = object_polygon(revised[0])
    assert len(before.interiors) == 2 and len(after.interiors) == 1
    assert before.exterior.equals(after.exterior)
    assert before.area - after.area == 800
    assert audit["changed_outside_allowed_domain_px2"] == 0
    assert source_polygon(revised[0], base).equals(after)
    assert len(obj["source_geometry"]["holes_xy"]) == 2


def test_revision_cannot_remove_material_outside_declared_scope(tmp_path):
    obj, base, op = example()
    op["allowed_native_bbox"] = [10, 35, 50, 45]
    with pytest.raises(ValueError, match="leaves declared scope"):
        revise_object(tmp_path, obj, base, op, None, dict(domain_leak_area_px2=0.05))


def test_unexpected_component_split_is_rejected(tmp_path):
    obj, base, op = example()
    op["cut_boxes"] = [[0, 35, 100, 45]]
    with pytest.raises(ValueError, match="Unexpected component"):
        revise_object(tmp_path, obj, base, op, None, dict(domain_leak_area_px2=0.05))


def test_local_edge_warp_does_not_clamp_remote_source_geometry():
    locator = dict(
        canonical_anchor_y=[10, 20, 30, 40],
        curve_ids=[None, "top", "bottom", None],
        case=dict(native_bbox=[0, 0, 10, 50]),
    )
    details = dict(
        paths_native_y=dict(top=[22] * 10, bottom=[32] * 10), eligible_native_x=list(range(10))
    )
    mapper, valid = edge_warp(locator, details)
    warped = mapper([[0, 0], [9, 0], [9, 50], [0, 50]])
    assert valid == 10
    assert np.min(warped[:, 1]) == 0 and np.max(warped[:, 1]) == 50
    details["eligible_native_x"] = []
    mapper, valid = edge_warp(locator, details)
    assert valid == 0
    assert np.allclose(mapper([[0, 20], [9, 20], [9, 30], [0, 30]])[:, 1], [20, 20, 30, 30])


def test_ambiguous_edges_need_real_gradient_before_repair():
    from silicon_eye.aa_layer_revision import repair_local_edges

    raw = np.zeros((60, 10, 3), np.uint8)
    raw[20:25] = 220
    raw[35:40] = 220
    curves = [
        dict(id="a", kind="rise"),
        dict(id="b", kind="fall"),
        dict(id="c", kind="rise"),
        dict(id="d", kind="fall"),
    ]
    locator = dict(
        repair_radius_px=3, case=dict(native_bbox=[0, 0, 10, 60], x_span=[0, 10], curves=curves)
    )
    details = dict(
        eligible_native_x=[0, 1, 2, 3, 6, 7, 8, 9],
        paths_native_y={name: [y] * 10 for name, y in zip("abcd", [19, 24, 34, 39], strict=True)},
    )
    details["paths_native_y"]["a"][4:6] = [38, 38]
    settings = dict(blur_x=1, blur_y=1, min_evidence=1)
    found = repair_local_edges(raw, locator, details, settings)
    assert found["locally_repaired_columns"] == 2
    assert found["paths_native_y"]["a"][4] < found["paths_native_y"]["b"][4]
    blank = repair_local_edges(np.zeros_like(raw), locator, details, settings)
    assert blank["locally_repaired_columns"] == 0
    assert 4 not in blank["eligible_native_x"]
