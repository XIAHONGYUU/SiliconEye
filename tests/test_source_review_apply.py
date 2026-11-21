import pytest

from silicon_eye.source_review_apply import apply


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
