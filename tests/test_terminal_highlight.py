"""Candidate highlighting must preserve evidence and existing electrical decisions."""
import json

import numpy as np
import pytest
from PIL import Image
from test_review_package import pack, ref, write  # noqa: F401

from silicon_eye.review_package import run_package


@pytest.fixture
def highlighted_pack(pack):  # noqa: F811
    root, request, _, _ = pack
    spec = dict(
        schema_version=1, document_kind="terminal_highlight_candidate", case_id="example",
        terminal_id="Q.G", frame_id="ref", native_source=ref(root, "ref.png"),
        window_xywh=[0, 0, 40, 40], segment_id="candidate", polygon_native_xy=[
            [5, 5], [15, 5], [15, 10], [5, 10]], anchor_native_xy=[8, 8],
        status="candidate", producer="reasoning_model", rationale="Visible local candidate",
        evidence=[ref(root, "human.json")], continuation="unknown_stop_at_declared_segment",
        contact_landing="unknown",
    )
    write(root / "highlight.json", spec)
    request["terminal_highlights"] = [ref(root, "highlight.json")]
    return pack


def run(bundle):
    root, request, path, out = bundle
    write(path, request)
    return run_package(path, out, root)


def test_native_highlight_is_local_candidate_and_does_not_union(highlighted_pack, tmp_path):
    first = run(highlighted_pack)
    root, request, path, out = highlighted_pack
    record = first["terminal_highlights"][0]
    assert record["terminal_to_segment_status"] == "candidate_not_human_confirmed"
    assert record["confirmed_net_id"] is None
    assert record["contact_landing"] == "unknown"
    assert record["electrical_state_changed"] is False
    raw = np.array(Image.open(out / "terminal-highlight-001-raw.png"))
    marked = np.array(Image.open(out / "terminal-highlight-001-overlay.png"))
    assert np.array_equal(raw, np.array(Image.open(root / "ref.png")))
    assert not np.array_equal(raw[6, 6], marked[6, 6])
    assert np.array_equal(raw[25:, :], marked[25:, :])
    request.pop("terminal_highlights")
    write(path, request)
    second = run_package(path, tmp_path / "baseline", root)
    assert first["block_state_id"] == second["block_state_id"]
    assert first["electrical_acceptance"] == second["electrical_acceptance"]


@pytest.mark.parametrize("fault", ["terminal", "source", "polygon", "anchor", "status", "hash"])
def test_bad_highlight_fails_before_output(highlighted_pack, fault):
    root, request, _, out = highlighted_pack
    doc = json.loads((root / "highlight.json").read_text())
    if fault == "terminal":
        doc["terminal_id"] = "missing.G"
    elif fault == "source":
        doc["native_source"] = ref(root, "target.png")
    elif fault == "polygon":
        doc["polygon_native_xy"][0] = [-1, 5]
    elif fault == "anchor":
        doc["anchor_native_xy"] = [30, 30]
    elif fault == "status":
        doc["status"] = "confirmed"
    else:
        doc["evidence"][0]["sha256"] = "0" * 64
    write(root / "highlight.json", doc)
    request["terminal_highlights"] = [ref(root, "highlight.json")]
    with pytest.raises(ValueError):
        run(highlighted_pack)
    assert not out.exists()


@pytest.fixture
def bridged_pack(highlighted_pack):
    root, request, _, _ = highlighted_pack
    case = json.loads((root / "case.json").read_text())
    case["geometry_observations"] = [dict(
        entity_id="Q", frame_id="ref", xywh=[8, 8, 10, 10], status="candidate",
        role="inspection_window_not_material_boundary", producer="AI",
    )]
    write(root / "case.json", case)
    request["case"] = ref(root, "case.json")
    profile = json.loads((root / "profile.json").read_text())
    profile["profile_id"] = "macro"
    write(root / "profile.json", profile)
    request["registrations"][0]["profile"] = ref(root, "profile.json")
    spec = json.loads((root / "highlight.json").read_text())
    spec.update(frame_id="target", native_source=ref(root, "target.png"), contact_bridge=dict(
        gate_frame_id="ref", source_context_xywh=[0, 0, 40, 40],
        ct_window_xywh=[9, 10, 4, 4], ct_center_native_xy=[11, 12],
        registration_profile_id="macro", target_search_radius_px=4,
        status="candidate", rationale="Explicit candidate CT at gate end",
    ))
    write(root / "highlight.json", spec)
    request["terminal_highlights"] = [ref(root, "highlight.json")]
    return highlighted_pack


def test_ct_bridge_uses_inverse_transform_and_keeps_both_links_candidate(bridged_pack):
    state = run(bridged_pack)
    bridge = state["terminal_highlights"][0]["contact_bridge"]
    assert bridge["projected_ct_native_xy"] == [9, 9]
    assert bridge["anchor_offset_px"] == pytest.approx(2 ** .5)
    assert bridge["search_radius_is_accuracy_bound"] is False
    assert bridge["ct_on_gate_status"] == bridge["ct_to_metal_status"] == "candidate"
    assert (bridged_pack[3] / "terminal-highlight-001-ct-bridge.png").is_file()
    assert state["precise_registration_accepted"] is False


@pytest.mark.parametrize("fault", ["center", "profile", "radius", "non_gate"])
def test_ct_bridge_cannot_skip_binding_and_proximity_checks(bridged_pack, fault):
    root, request, _, out = bridged_pack
    spec = json.loads((root / "highlight.json").read_text())
    if fault == "center":
        spec["contact_bridge"]["ct_center_native_xy"] = [30, 30]
    elif fault == "profile":
        spec["contact_bridge"]["registration_profile_id"] = "unknown"
    elif fault == "radius":
        spec["contact_bridge"]["target_search_radius_px"] = .2
    else:
        spec["terminal_id"] = "Q.A"
    write(root / "highlight.json", spec)
    request["terminal_highlights"] = [ref(root, "highlight.json")]
    with pytest.raises(ValueError):
        run(bridged_pack)
    assert not out.exists()
