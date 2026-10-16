"""Behavioral checks for explicit review replay and one-state exports."""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path

import pytest

from silicon_eye.block_export import run_block
from silicon_eye.block_review import resolve_block
from silicon_eye.schemas.block_case import BlockCase

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def data():
    return json.loads((ROOT / "benchmarks/block-case-v1-v3.json").read_text())


def resolve(data):
    return resolve_block(BlockCase.model_validate(data))


def add_event(data, event):
    data["review_events"].append(event)
    data["review_inventory"]["event_ids"].append(event["id"])


def decision(data, claim, verdict="confirm", supersedes=None):
    event = deepcopy(next(e for e in data["review_events"] if e["actor"] == "human"))
    event.update(
        id="event_" + claim + "_" + verdict,
        claim_id=claim,
        verdict=verdict,
        supersedes_event_ids=supersedes or [],
    )
    return event


def new_claim(data, id, predicate, subjects):
    c = deepcopy(next(c for c in data["claims"] if c["predicate"] == "same_net"))
    c.update(id=id, predicate=predicate, subject_ids=subjects)
    data["claims"].append(c)
    add_event(data, decision(data, id))


def test_v3_replays_known_relations_without_merging_unknown_bodies(data):
    state = resolve(data)
    assert len(state["devices"]) == 2 and len(state["terminals"]) == 8
    assert len(state["confirmed_components"]) == 1
    assert set(state["confirmed_components"][0]["terminals"]) == {
        "V3_Q1.G",
        "V3_Q1.B",
        "V3_Q2.G",
        "V3_Q2.A",
    }
    assert [t["id"] for t in state["terminals"] if t["mapping_status"] == "confirmed"] == [
        "V3_Q1.A",
        "V3_Q2.B",
    ]
    assert all(t["confirmed_net_id"] is None for t in state["terminals"] if t["role"] == "Bulk")
    matrix = state["matrix"]["values"]
    assert sum(matrix[i][j] == "K" for i in range(8) for j in range(i + 1, 8)) == 6
    assert sum(matrix[i][j] == "?" for i in range(8) for j in range(i + 1, 8)) == 22
    assert all("D" not in row for row in matrix)
    assert state["status"] == "review_state_ready"
    assert state["acceptance"]["simulation_ready"] is False


def test_order_and_repeat_are_stable_and_input_is_not_mutated(data):
    original = deepcopy(data)
    first = resolve(data)
    assert data == original and resolve(data) == first
    for key in ["entities", "claims", "review_events", "scopes", "frames", "measurements"]:
        data[key].reverse()
    data["review_inventory"]["event_ids"].reverse()
    data["review_inventory"]["source_refs"].reverse()
    for c in data["claims"]:
        c["subject_ids"].reverse()
        c["evidence_refs"].reverse()
    for e in data["review_events"]:
        e["source_refs"].reverse()
    assert resolve(data) == first


def test_identity_physical_sharing_and_local_poly_gap_never_implicitly_union(data):
    # Removing the electrical assertion must remove the whole union, despite identity,
    # common physical M and local geometric records remaining confirmed.
    add_event(data, decision(data, "c_GM", "withdraw", ["e_GM_confirm"]))
    state = resolve(data)
    assert not state["confirmed_components"]
    assert not state["conflicts"]
    assert all("K" not in row for row in state["matrix"]["values"])
    claims = {c["id"]: c for c in state["claims"]}
    assert claims["c_P2_identity"]["status"] == "confirmed"
    assert claims["c_poly_local_open"]["value"] is False
    assert claims["c_GM"]["status"] == "unknown"


def test_parallel_decisions_conflict_and_explicit_replacement_resolves(data):
    e = decision(data, "c_GM", "reject")
    add_event(data, e)
    assert resolve(data)["status"] == "conflict"
    e["supersedes_event_ids"] = ["e_GM_confirm"]
    state = resolve(data)
    assert state["status"] == "review_state_ready" and not state["confirmed_components"]
    assert next(c for c in state["claims"] if c["id"] == "c_GM")["status"] == "rejected"


def test_transitive_isolation_conflict_is_detected(data):
    new_claim(data, "join_A", "same_net", ["V3_Q1.A", "V3_Q1.G"])
    new_claim(data, "isolate_A", "different_net", ["V3_Q1.A", "V3_Q2.A"])
    state = resolve(data)
    assert any(c["kind"] == "same_net_vs_different_net" for c in state["conflicts"])
    assert not state["acceptance"]["structure_draft_ready"]


def test_explicit_isolation_propagates_across_confirmed_component(data):
    new_claim(data, "isolate_A", "different_net", ["V3_Q1.A", "V3_Q2.A"])
    state = resolve(data)
    ids = state["matrix"]["terminals"]
    m = state["matrix"]["values"]
    assert m[ids.index("V3_Q1.A")][ids.index("V3_Q1.G")] == "D"
    assert m[ids.index("V3_Q1.A")][ids.index("V3_Q2.B")] == "?"
    assert state["status"] == "review_state_ready"


def test_missing_terminal_bad_predicate_and_inventory_fail(data):
    missing = deepcopy(data)
    missing["entities"] = [e for e in missing["entities"] if e["id"] != "V3_Q1.Bulk"]
    with pytest.raises(ValueError, match="G/A/B/Bulk"):
        resolve(missing)
    invalid = deepcopy(data)
    next(c for c in invalid["claims"] if c["id"] == "c_GM")["subject_ids"][0] = "M2_P2"
    with pytest.raises(ValueError, match="predicate types"):
        resolve(invalid)
    data["review_inventory"]["event_ids"].pop()
    with pytest.raises(ValueError, match="inventory"):
        resolve(data)


def test_cycles_cross_claim_replacement_and_nonhuman_physical_decisions_fail(data):
    cyclic = deepcopy(data)
    next(e for e in cyclic["review_events"] if e["id"] == "e_GM_unknown")[
        "supersedes_event_ids"
    ] = ["e_GM_confirm"]
    with pytest.raises(ValueError, match="cycle"):
        resolve(cyclic)
    cross = deepcopy(data)
    next(e for e in cross["review_events"] if e["id"] == "e_GM_confirm")["supersedes_event_ids"] = [
        "e_map_A"
    ]
    with pytest.raises(ValueError, match="same claim"):
        resolve(cross)
    data["review_events"][0]["actor"] = "script"
    with pytest.raises(ValueError, match="human review"):
        resolve(data)


def test_equivalent_case_renaming_does_not_require_case_specific_rules(data):
    original = resolve(data)
    # Arbitrary IDs test portability, not new-photo accuracy.
    names = {
        r["id"]: "renamed_" + str(i)
        for i, r in enumerate(data["entities"] + data["claims"] + data["review_events"])
    }

    def rename(x):
        if isinstance(x, dict):
            return {k: rename(v) for k, v in x.items()}
        if isinstance(x, list):
            return [rename(v) for v in x]
        return names.get(x, x) if isinstance(x, str) else x

    state = resolve(rename(data))
    assert len(state["confirmed_components"][0]["terminals"]) == 4
    assert state["matrix"]["values"].count([]) == 0
    assert sum(row.count("K") for row in state["matrix"]["values"]) == sum(
        row.count("K") for row in original["matrix"]["values"]
    )
    assert state["status"] == "review_state_ready"


def test_one_state_export_ids_match_and_failed_source_writes_nothing(tmp_path, data):
    spec = tmp_path / "case.json"
    spec.write_text(json.dumps(data))
    out = tmp_path / "ok"
    state = run_block(str(spec), str(out), str(ROOT))
    assert state["evidence_integrity"] == "sources_checked"
    assert json.loads((out / "manifest.json").read_text())["state_id"] == state["state_id"]
    assert json.loads((out / "resolved-state.json").read_text())["state_id"] == state["state_id"]
    for name in ["local-schematic.svg", "report.md"]:
        assert state["state_id"] in (out / name).read_text()
    for name in ["terminals.csv", "connection-matrix.csv"]:
        with (out / name).open() as f:
            rows = list(csv.DictReader(f))
            assert rows
            assert all(row["state_id"] == state["state_id"] for row in rows)
    with pytest.raises(ValueError, match="already exists"):
        run_block(str(spec), str(out), str(ROOT))
    data["sources"]["checkpoint"]["sha256"] = "0" * 64
    spec.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="hash changed"):
        run_block(str(spec), str(tmp_path / "bad"), str(ROOT))
    assert not (tmp_path / "bad").exists()


def test_conflict_export_only_writes_diagnostics(tmp_path, data):
    add_event(data, decision(data, "c_GM", "reject"))
    spec = tmp_path / "case.json"
    spec.write_text(json.dumps(data))
    out = tmp_path / "conflict"
    state = run_block(str(spec), str(out), str(ROOT))
    assert state["status"] == "conflict"
    assert (out / "report.md").is_file()
    assert not (out / "local-schematic.svg").exists()
    assert not (out / "connection-matrix.csv").exists()


def test_opposite_scoped_geometry_claims_conflict_without_electrical_split(data):
    c = deepcopy(next(c for c in data["claims"] if c["id"] == "c_poly_local_open"))
    c.update(id="opposite_poly", value=True)
    data["claims"].append(c)
    add_event(data, decision(data, "opposite_poly"))
    state = resolve(data)
    assert any(c["kind"] == "contradictory_values" for c in state["conflicts"])
    assert len(state["confirmed_components"][0]["terminals"]) == 4


def test_bad_geometry_and_false_same_net_fail(data):
    bad = deepcopy(data)
    bad["geometry_observations"][0]["xywh"] = [5700, 10, 100, 20]
    with pytest.raises(ValueError, match="outside native"):
        resolve(bad)
    data["claims"][4]["value"] = False
    assert data["claims"][4]["predicate"] == "same_net"
    with pytest.raises(ValueError, match="predicate types/value"):
        resolve(data)


def test_cli_conflict_is_nonzero_and_does_not_render_accepted_outputs(tmp_path, data):
    from argparse import Namespace

    from silicon_eye.cli import cmd_annotate

    add_event(data, decision(data, "c_GM", "reject"))
    spec = tmp_path / "case.json"
    spec.write_text(json.dumps(data))
    out = tmp_path / "conflict"
    with pytest.raises(SystemExit) as error:
        cmd_annotate(Namespace(subcommand="block", spec=str(spec), output=str(out), root=str(ROOT)))
    assert error.value.code == 2 and not (out / "terminals.csv").exists()


def test_source_excerpt_mismatch_cannot_become_a_physical_confirmation(tmp_path, data):
    data["review_events"][0]["source_statement"] = "This statement is not in the bound source."
    spec = tmp_path / "case.json"
    spec.write_text(json.dumps(data))
    out = tmp_path / "not_created"
    with pytest.raises(ValueError, match="excerpt missing"):
        run_block(str(spec), str(out), str(ROOT))
    assert not out.exists()
