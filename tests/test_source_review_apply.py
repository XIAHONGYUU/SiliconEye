import pytest

from silicon_eye.source_review_apply import apply, continue_pairs


def test_approval_does_not_spread_to_ai_neighbors_and_edge_is_not_join():
    groups = [
        dict(id="A", fragments=["a", "x"]),
        dict(id="B", fragments=["b"]),
        dict(id="C", fragments=["c", "y"]),
        dict(id="D", fragments=["d"]),
    ]
    rules = [
        dict(item_id="G1", action="same_source_path", fragments=["a", "b"]),
        dict(item_id="G2", action="wide_metal_edge", fragments=["c", "d"]),
    ]
    result = apply(groups, rules, {k: dict(verdict="accepted") for k in ["G1", "G2"]})
    assert result["reviewed_relations"][0]["fragments"] == ["a", "b"]
    assert len(result["reviewed_relations"]) == 1
    assert {f for g in result["groups"] for f in g["fragments"]} == {"a", "b", "x", "y"}
    assert all(not g["group_human_approved"] for g in result["groups"])
    assert groups[2]["fragments"] == ["c", "y"]


def test_uncertain_is_not_adopted_and_unknown_ids_fail():
    groups = [dict(id="A", fragments=["a"])]
    rules = [dict(item_id="G1", action="same_source_path", fragments=["a", "b"])]
    assert apply(groups, rules, {"G1": dict(verdict="uncertain")})["reviewed_relations"] == []
    with pytest.raises(ValueError):
        apply(groups, rules, {"G1": dict(verdict="accepted")})


def test_continuation_preserves_prior_evidence_without_approving_ai_neighbors():
    parent = dict(
        groups=[dict(id="A", fragments=["a", "b", "x"]), dict(id="C", fragments=["c"])],
        reviewed_relations=[dict(fragments=["a", "b"], review_item="OLD")],
        reviewed_edges=[dict(fragment_id="edge", review_item="EDGE")],
    )
    rules = [dict(item_id="BATCH", action="same_source_path", pairs=[
        dict(case="NEW", fragments=["b", "c"]),
    ])]
    result = continue_pairs(parent, rules, {"BATCH": dict(verdict="accepted")})
    assert result["reviewed_relations"][:1] == parent["reviewed_relations"]
    assert result["reviewed_edges"] == parent["reviewed_edges"]
    assert result["reviewed_relations"][1] == dict(
        fragments=["b", "c"], case_id="NEW", review_item="BATCH",
        status="human_confirmed_local_source_relation",
    )
    assert all(not g["group_human_approved"] for g in result["groups"])
    assert all("x" not in r["fragments"] for r in result["reviewed_relations"])
    assert parent["groups"][0]["fragments"] == ["a", "b", "x"]
    assert result["electrical_identity"] == "unknown"
    assert result["geometry_adopted"] is False


@pytest.mark.parametrize("pair", [["a", "b"], ["b", "edge"], ["b", "missing"]])
def test_continuation_rejects_repeated_and_excluded_pairs(pair):
    parent = dict(
        groups=[dict(id="A", fragments=["a", "b", "c"])],
        reviewed_relations=[dict(fragments=["a", "b"])],
        reviewed_edges=[dict(fragment_id="edge")],
    )
    rules = [dict(item_id="BATCH", action="same_source_path", pairs=[
        dict(case="NEW", fragments=pair),
    ])]
    with pytest.raises(ValueError):
        continue_pairs(parent, rules, {"BATCH": dict(verdict="accepted")})


def test_continuation_uncertain_and_accepted_notes_do_not_get_silently_applied():
    parent = dict(
        groups=[dict(id="A", fragments=["a"]), dict(id="B", fragments=["b"])],
        reviewed_relations=[], reviewed_edges=[],
    )
    rules = [dict(item_id="BATCH", action="same_source_path", pairs=[
        dict(case="NEW", fragments=["a", "b"]),
    ])]
    result = continue_pairs(parent, rules, {"BATCH": dict(verdict="uncertain")})
    assert result["reviewed_relations"] == []
    assert len(result["groups"]) == 2
    with pytest.raises(ValueError, match="semantic reconciliation"):
        continue_pairs(parent, rules, {"BATCH": dict(verdict="accepted", notes="Except NEW")})
