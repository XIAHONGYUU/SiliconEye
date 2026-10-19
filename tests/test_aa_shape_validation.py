"""Shape gates distinguish ring holes, real separation and prior-derived unknowns."""

import numpy as np

from silicon_eye.aa_shape_validation import candidate_states, prior_samples, topology


def settings():
    return dict(
        seed_margin=3,
        background_outer_margin=6,
        domain_margin=12,
        max_training_pixels_per_class=10000,
        seed=3,
    )


def test_ring_hole_and_center_island_are_not_confused():
    case = dict(
        native_bbox=[0, 0, 100, 100],
        objects=[
            dict(
                outer_native_xy=[[10, 10], [90, 10], [90, 90], [10, 90]],
                holes_native_xy=[[[25, 25], [75, 25], [75, 75], [25, 75]]],
            ),
            dict(outer_native_xy=[[40, 40], [60, 40], [60, 60], [40, 60]], holes_native_xy=[]),
        ],
    )
    prior, samples, _ = prior_samples(case, settings())
    result = topology(prior, 25)
    assert result["components"] == 2 and result["holes"] == 1
    assert samples[50, 50] == 1 and samples[50, 28] == 0


def test_concave_notch_is_not_replaced_by_a_bounding_rectangle():
    case = dict(
        native_bbox=[0, 0, 100, 100],
        objects=[
            dict(
                outer_native_xy=[[10, 10], [90, 10], [90, 40], [60, 40], [60, 70], [10, 70]],
                holes_native_xy=[],
            )
        ],
    )
    prior, samples, _ = prior_samples(case, settings())
    assert prior[25, 75] and not prior[50, 75]
    assert samples[50, 65] == 0 and samples[25, 75] == 1


def test_bridge_changes_topology_and_small_fragments_are_reported_separately():
    mask = np.zeros((60, 80), bool)
    mask[10:40, 10:30] = True
    mask[10:40, 40:60] = True
    mask[52, 70] = True
    result = topology(mask, 25)
    assert result["components"] == 2 and result["small_components"] == 1
    mask[20:25, 30:40] = True
    assert topology(mask, 25)["components"] == 1


def test_unknown_boundary_and_outside_domain_are_not_background():
    mask = np.zeros((60, 80), bool)
    mask[10:40, 10:60] = True
    domain = np.ones(mask.shape, bool)
    domain[:, 70:] = False
    states = candidate_states(mask, domain, 2)
    assert states[20, 20] == 1 and states[50, 20] == 0
    assert states[10, 20] == -1 and np.all(states[:, 70:] == -1)


def test_clipped_unmodeled_neighbor_is_not_counted_as_target_breakage():
    from silicon_eye.aa_shape_validation import scoped_topology

    domain = np.zeros((80, 80), bool)
    domain[5:75, 5:75] = True
    prior = np.zeros_like(domain)
    prior[20:60, 30:50] = True
    mask = prior.copy()
    mask[5:9, 15:35] = True
    scoped = scoped_topology(mask, domain, prior, 25)
    assert scoped["target"]["components"] == 1
    assert scoped["clipped_unmodeled_components"] == 1
    assert scoped["unexplained_interior_components"] == 0
    mask[35:42, 10:18] = True
    assert scoped_topology(mask, domain, prior, 25)["unexplained_interior_components"] == 1


def test_real_split_inside_target_prior_is_not_excused_as_scope_clipping():
    from silicon_eye.aa_shape_validation import scoped_topology

    domain = np.ones((80, 80), bool)
    prior = np.zeros_like(domain)
    prior[10:70, 20:60] = True
    broken = prior.copy()
    broken[38:42] = False
    result = scoped_topology(broken, domain, prior, 25)
    assert result["target"]["components"] == 2
    assert result["clipped_unmodeled_components"] == 0
