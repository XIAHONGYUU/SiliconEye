"""Topology repair must retire uncertain supports without inventing material."""

import numpy as np
import pytest

from silicon_eye.local_poly_repair import rectangle, repair_support


def example():
    poly = np.zeros((20, 32), bool)
    poly[3:6, 3:27] = True
    poly[14:17, 3:27] = True
    for start in [3, 14, 25]:
        poly[3:17, start:start+2] = True
    ct = np.zeros_like(poly)
    ct[9, 14] = True
    protected = rectangle(poly.shape, [3, 3, 24, 3])
    protected |= rectangle(poly.shape, [3, 14, 24, 3])
    return poly, ct, protected


def test_all_bridges_retired_as_unknown_and_gate_bands_preserved():
    poly, ct, protected = example()
    domain = rectangle(poly.shape, [3, 8, 24, 3])
    r = repair_support(poly, ct, domain, [[5, 4], [5, 15]], protected)
    assert r['before_seed_labels'][0] == r['before_seed_labels'][1]
    assert r['after_seed_labels'][0] != r['after_seed_labels'][1]
    assert np.array_equal(r['positive'][protected], poly[protected])
    assert np.array_equal(r['positive'][~domain], poly[~domain])
    assert not (r['positive'] & ~poly).any()
    assert r['ct_underlying_unknown'][9, 14]
    assert not (r['topology_unknown'] & r['ct_underlying_unknown']).any()
    assert np.array_equal(r['retired'], r['topology_unknown'] | r['ct_underlying_unknown'])


def test_cutting_only_one_end_cannot_hide_internal_bridge():
    poly, ct, protected = example()
    with pytest.raises(ValueError, match='failed to separate'):
        repair_support(poly, ct, rectangle(poly.shape, [3, 8, 2, 3]),
                       [[5, 4], [5, 15]], protected)


def test_global_bypass_outside_local_domain_still_rejects_repair():
    poly, ct, protected = example()
    poly[4, 26:31] = True
    poly[15, 26:31] = True
    poly[4:16, 30] = True
    with pytest.raises(ValueError, match='failed to separate'):
        repair_support(poly, ct, rectangle(poly.shape, [3, 8, 24, 3]),
                       [[5, 4], [5, 15]], protected)


def test_protected_gate_support_cannot_be_removed_to_force_separation():
    poly, ct, protected = example()
    with pytest.raises(ValueError, match='protected gate'):
        repair_support(poly, ct, rectangle(poly.shape, [3, 4, 24, 8]),
                       [[5, 4], [5, 15]], protected)
