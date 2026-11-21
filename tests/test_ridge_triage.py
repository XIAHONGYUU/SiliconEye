from silicon_eye.ridge_triage import classify, support


def test_support_preserves_gap_and_distinct_parallel_paths():
    points = [[x, 10] for x in range(31)]
    tracks = [dict(points=[[0, 10], [10, 10]]), dict(points=[[20, 10], [30, 10]])]
    mask = support(points, tracks)
    assert mask[:11].all() and mask[20:].all()
    assert not mask[11:20].any()
    assert not support([[0, 20], [10, 20]], tracks).any()
    assert not support([[-1, 10], [31, 10]], tracks).any()


def test_risk_overrides_stability_and_identity():
    fragment = dict(peripheral_edge_risk=False, branch_or_parallel_overlap=False)
    stable = {"8.0": 1, "12.0": 0.95}
    assert classify(fragment, stable, []) == "stable_new_source_candidate"
    assert classify(fragment, {"8.0": 1, "12.0": 0.8}, []) == "threshold_unstable_hold"
    assert classify(fragment, stable, [dict(id="A", fraction=0.5)]) == "partial_known_path_hold"
    assert classify(fragment, stable, [dict(id="A", fraction=0.95)]) == "known_path_context"
    assert (
        classify(fragment, stable, [dict(id="A", fraction=0.95), dict(id="B", fraction=0.93)])
        == "identity_conflict_hold"
    )
    fragment["branch_or_parallel_overlap"] = True
    assert classify(fragment, stable, [dict(id="A", fraction=1)]) == "branch_topology_hold"
    fragment["peripheral_edge_risk"] = True
    assert classify(fragment, stable, []) == "peripheral_edge_hold"
