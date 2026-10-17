"""Adapter must preserve human decisions, unknowns and independent native photo frames."""
import json

import pytest
from test_review_package import pack, ref, write  # noqa: F401

from silicon_eye.observation_adapter import run_adapter
from silicon_eye.review_package import run_package


@pytest.fixture
def example(pack):  # noqa: F811
    root, package, package_path, _ = pack
    case = json.loads((root / "case.json").read_text())
    case["entities"].append(dict(id="support", kind="physical_region"))
    write(root / "case.json", case)
    package["case"] = ref(root, "case.json")
    write(package_path, package)
    # Adapter inputs, including the original package, must be inside the evidence root.
    write(root / "package.json", package)
    task = dict(
        schema_version=1, document_kind="local_photo_task", task_id="task", case_id="example",
        same_chip_same_location="human_reviewed_local_identity",
        sources=dict(photo=ref(root, "ref.png"), other=ref(root, "target.png")),
        frames=case["frames"], subject_ids=[e["id"] for e in case["entities"]],
        regions=[dict(id="window", frame_id="ref", xywh=[0, 0, 40, 40],
                      role="inspection_window_not_material_boundary")],
        scopes=case["scopes"] + [dict(id="identity", domain="physical_identity",
                                     extent="material")],
        instructions="Review existing objects only",
    )
    write(root / "task.json", task)
    observations = [
        dict(id="material", predicate="material_identity", subject_ids=["support"],
             scope_id="identity", status="candidate", value="poly", evidence_refs=["photo"],
             rationale="Material body; precise edges unknown", boundary_status="unknown",
             location=dict(id="loc", frame_id="ref", xywh=[5, 5, 20, 20],
                           role="inspection_window_not_material_boundary")),
        dict(id="unknown", predicate="same_net", subject_ids=["Q.G", "Q.A"],
             scope_id="electrical", status="unknown", value=None, evidence_refs=[],
             rationale="Connection not visible"),
        dict(id="exists", predicate="device_exists", subject_ids=["Q"],
             scope_id="electrical", status="candidate", value=True, evidence_refs=["photo"],
             rationale="Reviewed device"),
    ]
    batch = dict(schema_version=1, document_kind="agent_observations", task_id="task",
                 input_packet=ref(root, "task.json"), run_id="fixture", purpose="synthetic_fixture",
                 producer="reasoning_model", model_id=None, prompt_version=None,
                 observations=observations)
    return root, batch, root / "adapted"


def run(example):
    root, batch, out = example
    write(root / "observations.json", batch)
    return run_adapter(root / "package.json", root / "observations.json", out, root)


def test_material_window_is_not_boundary_and_unknown_never_unions(example):
    state = run(example)
    root, _, out = example
    adapted = json.loads((out / "case.json").read_text())
    base = json.loads((root / "case.json").read_text())
    from silicon_eye.schemas.block_case import BlockCase

    base = BlockCase.model_validate(base).model_dump(mode="json", by_alias=True)
    assert adapted["review_events"] == base["review_events"]
    assert adapted["review_inventory"] == base["review_inventory"]
    assert len(adapted["claims"]) == len(base["claims"]) + 1
    assert adapted["geometry_observations"] == []
    cards = state["observation_adaptations"][0]["cards"]
    assert cards[0]["existing_review"]["status"] == "matches_human_review"
    assert cards[0]["boundary_polygon_xy"] is None
    assert cards[1]["case_claim_id"] is None
    assert cards[2]["existing_review"]["status"] == "matches_human_review"
    resolved = json.loads((out / "review/circuit/resolved-state.json").read_text())
    assert resolved["matrix"]["values"][0][1] == "?"
    assert resolved["confirmed_components"] == []
    assert "边界未知" in (out / "review/index.html").read_text()
    assert not list((out / "review").glob("*mask*"))
    replay = run_package(out / "package-request.json", root / "replay", root)
    assert replay["bundle_id"] == state["bundle_id"]
    first = json.loads((out / "review/manifest.json").read_text())
    second = json.loads((root / "replay/manifest.json").read_text())
    assert first["outputs"] == second["outputs"]


def test_ai_disagreement_is_visible_without_overwriting_human(example):
    example[1]["observations"][2]["value"] = False
    state = run(example)
    cards = state["observation_adaptations"][0]["cards"]
    assert cards[2]["existing_review"]["status"] == "differs_from_human_review"
    resolved = json.loads((example[2] / "review/circuit/resolved-state.json").read_text())
    assert resolved["devices"][0]["existence"] is True
    assert resolved["conflicts"] == []
    assert "与既有人审有差异" in (example[2] / "review/index.html").read_text()


@pytest.mark.parametrize("fault", ["hash", "case", "scope", "frame", "unknown_types", "bounds"])
def test_bad_binding_fails_before_output(example, fault):
    root, batch, out = example
    if fault == "hash":
        batch["input_packet"]["sha256"] = "0" * 64
    elif fault in {"case", "scope", "frame"}:
        task = json.loads((root / "task.json").read_text())
        if fault == "case":
            task["case_id"] = "another"
        elif fault == "scope":
            task["scopes"][0]["extent"] = "changed extent"
        else:
            task["frames"][0]["source_ref"] = "other"
        write(root / "task.json", task)
        batch["input_packet"] = ref(root, "task.json")
    elif fault == "unknown_types":
        batch["observations"][1]["subject_ids"] = ["Q", "support"]
    else:
        batch["observations"][0]["location"]["xywh"] = [30, 30, 20, 20]
    with pytest.raises(ValueError):
        run(example)
    assert not out.exists()


def test_tampered_adapter_cards_are_rejected_by_package(example):
    run(example)
    root, _, out = example
    doc = json.loads((out / "adaptation.json").read_text())
    doc["cards"][0]["boundary_status"] = "confirmed"
    write(out / "adaptation.json", doc)
    request = json.loads((out / "package-request.json").read_text())
    request["observation_adaptations"] = [ref(root, "adapted/adaptation.json")]
    write(out / "package-request.json", request)
    with pytest.raises(ValueError, match="differ"):
        run_package(out / "package-request.json", root / "tampered", root)
    assert not (root / "tampered").exists()


def test_existing_adapter_directory_is_never_overwritten(example):
    example[2].mkdir()
    (example[2] / "keep").write_text("keep")
    with pytest.raises(ValueError, match="new directory"):
        run(example)
    assert (example[2] / "keep").read_text() == "keep"


def test_new_candidate_connection_does_not_join_accepted_network(example):
    obs = example[1]["observations"][1]
    obs.update(status="candidate", value=True, evidence_refs=["photo"])
    run(example)
    state = json.loads((example[2] / "review/circuit/resolved-state.json").read_text())
    assert state["confirmed_components"] == []
    assert state["matrix"]["values"][0][1] == "?"
    assert any(c["predicate"] == "same_net" and c["status"] == "candidate"
               for c in state["claims"])


def test_model_unknown_keeps_previously_confirmed_existence(example):
    example[1]["observations"][2].update(status="unknown", value=None)
    state = run(example)
    card = state["observation_adaptations"][0]["cards"][2]
    assert card["existing_review"]["status"] == "model_unknown_existing_decision_retained"
    assert card["case_claim_id"] is None
    resolved = json.loads((example[2] / "review/circuit/resolved-state.json").read_text())
    assert resolved["devices"][0]["existence"] is True


def test_material_identity_difference_keeps_approved_material_separate(example):
    example[1]["observations"][0]["value"] = "ct"
    state = run(example)
    card = state["observation_adaptations"][0]["cards"][0]
    assert card["existing_review"]["status"] == "differs_from_human_review"
    assert state["materials"][0]["observations"]["regions"][0]["material"] == "poly"
    assert "CT" in (example[2] / "review/index.html").read_text()


def test_explicit_polygon_is_only_candidate_and_stays_inside_window(example):
    material = example[1]["observations"][0]
    material.update(boundary_status="candidate",
                    boundary_polygon_xy=[[8, 8], [12, 8], [12, 14], [8, 14]])
    state = run(example)
    assert state["pixel_material_truth_accepted"] is False
    assert "橙线仅为候选轮廓" in (example[2] / "review/index.html").read_text()


def test_explicit_extra_photo_frame_is_bound_without_implying_alignment(example):
    root, batch, out = example
    from PIL import Image

    Image.new("RGB", (20, 30), "gray").save(root / "extra.png")
    task = json.loads((root / "task.json").read_text())
    task["sources"]["extra_photo"] = ref(root, "extra.png")
    task["frames"].append(dict(id="extra_native", source_ref="extra_photo", unit="px",
                               coordinates="xy_half_open", size_wh=[20, 30]))
    write(root / "task.json", task)
    batch["input_packet"] = ref(root, "task.json")
    state = run(example)
    case = json.loads((out / "case.json").read_text())
    assert any(f["id"] == "extra_native" for f in case["frames"])
    assert case["sources"]["extra_photo"] == ref(root, "extra.png")
    assert state["precise_registration_accepted"] is False
    assert case["geometry_observations"] == []


def test_adapter_and_device_view_share_one_package_and_block_state(example):
    root, _, out = example
    request = json.loads((root / "package.json").read_text())
    request["device_view"] = dict(windows=[dict(
        id="native", frame_id="ref", label="poly", xywh=[0, 0, 40, 40],
    )])
    write(root / "package.json", request)
    state = run(example)
    assert state["device_index"]["block_state_id"] == state["block_state_id"]
    assert 'href="device-index.html"' in (out / "review/index.html").read_text()
    assert (out / "review/device-index.html").is_file()
    assert state["device_index"]["windows"][0]["devices"][0]["status"] == "unknown"
