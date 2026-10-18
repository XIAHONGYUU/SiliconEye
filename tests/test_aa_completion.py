"""AA-only reconstruction checks: guard fields, crop edges, source mapping, locked geometry."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import Point, box

from silicon_eye.aa_completion import (
    part_polygon,
    polygon_record,
    revise,
    source_polygon,
    validate,
)


def test_guard_frame_keeps_inner_field_empty_and_crop_edge_open():
    ring = part_polygon(dict(kind="frame", bounds=[0, 0, 100, 100], width=10))
    assert ring.contains(Point(5, 50))
    assert not ring.contains(Point(50, 50))
    cropped = part_polygon(
        dict(kind="difference", bounds=[0, 0, 100, 100], holes=[[0, 10, 90, 90]])
    )
    assert not cropped.contains(Point(5, 50))
    assert cropped.contains(Point(95, 50))


def test_explicit_shared_guard_union_never_fills_its_device_field():
    material = part_polygon(
        dict(
            kind="union",
            parts=[
                dict(kind="frame", bounds=[0, 0, 100, 100], width=10),
                dict(kind="frame", bounds=[90, 0, 190, 100], width=10),
            ],
        )
    )
    assert material.contains(Point(95, 50))
    assert not material.contains(Point(50, 50))
    assert not material.contains(Point(140, 50))


def test_gate_detects_merge_and_diagonal_and_duplicate_but_not_missing_material():
    a = polygon_record("a", box(0, 0, 10, 10))
    b = polygon_record("b", box(9, 0, 20, 10))
    assert len(validate([a, b])) == 1
    assert validate([a]) == []  # Geometry success cannot certify unseen material coverage.
    with pytest.raises(ValueError, match="Duplicate"):
        validate([a, a])
    tilted = copy.deepcopy(a)
    tilted["outer_xy"][0][0] += 1
    with pytest.raises(ValueError, match="Nonorthogonal"):
        validate([tilted])


def test_source_observation_uses_explicit_boundaries_instead_of_global_projection():
    o = polygon_record("a", box(100, 100, 120, 120))
    o["source_geometry"] = dict(outer_xy=[[0, 0], [20, 0], [20, 20], [0, 20]], holes_xy=[])
    assert source_polygon(o, {}).equals(box(0, 0, 20, 20))


def test_real_revision_keeps_all_retained_aa_and_has_no_ct_or_intersections():
    root = Path(__file__).resolve().parents[1]
    spec = json.loads((root / "benchmarks/aa-completion-v1/spec-v9.json").read_text())
    base = json.loads((root / spec["base"]["path"]).read_text())
    retained = json.loads((root / spec["retained"]["path"]).read_text())
    before = copy.deepcopy(base)
    objects, _, _, superseded, groups = revise(base, retained, spec)
    assert base == before
    for o in retained["objects"]:
        if o["layer"] == "AA":
            assert o in objects
    assert all(o["layer"] == "AA" for o in objects)
    assert validate(objects) == []
    assert groups and superseded
    # All new source perimeters retain their holes and contain finite native coordinates.
    for o in objects:
        if "source_geometry" in o:
            p = source_polygon(o, {})
            assert p.is_valid and np.isfinite(p.bounds).all()
