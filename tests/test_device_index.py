"""Stable IDs, native coordinates and conservative macro projection behavior."""
import json

import pytest
from PIL import Image
from test_review_package import pack, ref, write  # noqa: F401

from silicon_eye.review_package import run_package


@pytest.fixture
def indexed_pack(pack):  # noqa: F811
    root, request, path, out = pack
    case = json.loads((root / "case.json").read_text())
    Image.new("RGB", (40, 40), "gray").save(root / "aa.png")
    case["sources"]["aa_photo"] = ref(root, "aa.png")
    case["frames"].append(dict(id="aa", source_ref="aa_photo", size_wh=[40, 40],
                               unit="px", coordinates="xy_half_open"))
    case["geometry_observations"] = [dict(
        entity_id="Q", frame_id="ref", xywh=[10, 12, 4, 6], status="candidate",
        role="inspection_window_not_material_boundary", producer="AI",
    )]
    write(root / "case.json", case)
    request["case"] = ref(root, "case.json")
    profile = json.loads((root / "profile.json").read_text())
    profile["profile_id"] = "macro"
    write(root / "profile.json", profile)
    request["registrations"][0]["profile"] = ref(root, "profile.json")
    request["device_view"] = dict(windows=[
        dict(id="aa", frame_id="aa", label="AA", xywh=[0, 0, 40, 40]),
        dict(id="poly", frame_id="ref", label="poly", xywh=[0, 0, 40, 40]),
        dict(id="m1", frame_id="target", label="M1", xywh=[0, 0, 40, 40],
             projection_profile_id="macro"),
    ])
    return pack


def run(bundle):
    root, request, path, out = bundle
    write(path, request)
    return run_package(path, out, root)


def test_id_binding_and_inverse_macro_projection_preserve_native_frames(indexed_pack):
    state = run(indexed_pack)
    index = state["device_index"]
    aa, poly, m1 = [w["devices"][0] for w in index["windows"]]
    assert [aa["device_id"], poly["device_id"], m1["device_id"]] == ["Q"] * 3
    assert aa["status"] == "unknown" and aa["polygon_native_xy"] is None
    assert poly["status"] == "native_candidate"
    assert m1["status"] == "macro_projection"
    assert m1["polygon_native_xy"] == [[8, 9], [12, 9], [12, 15], [8, 15]]
    assert index["metal_paths_inferred"] is False
    assert index["physical_boundary_accepted"] is False
    exported = json.loads((indexed_pack[3] / "device-index.json").read_text())
    assert exported["bundle_id"] == state["bundle_id"]
    assert "Q,M1,target,macro_projection" in (indexed_pack[3] / "device-index.csv").read_text()


def test_native_crop_is_byte_exact_and_does_not_draw_onto_raw_image(indexed_pack):
    run(indexed_pack)
    root, _, _, out = indexed_pack
    assert Image.open(root / "ref.png").tobytes() == Image.open(
        out / "device-layer-002-raw.png"
    ).tobytes()
    html = (out / "device-index.html").read_text()
    assert 'data-device="Q"' in html and 'data-select="Q"' in html
    assert 'stroke-dasharray="5 4"' in html
    assert "未定位" in html


def test_unreviewed_projection_area_is_unknown_not_extrapolated(indexed_pack):
    root, request, _, _ = indexed_pack
    case = json.loads((root / "case.json").read_text())
    case["geometry_observations"][0]["xywh"] = [0, 0, 4, 6]
    write(root / "case.json", case)
    request["case"] = ref(root, "case.json")
    state = run(indexed_pack)
    row = state["device_index"]["windows"][2]["devices"][0]
    assert row["status"] == "unknown"
    assert row["reason"] == "outside_reviewed_macro_scope"
    assert row["polygon_native_xy"] is None


@pytest.mark.parametrize("fault", ["missing_profile", "wrong_direction", "bad_crop", "frame"])
def test_bad_view_request_fails_before_output(indexed_pack, fault):
    _, request, _, out = indexed_pack
    windows = request["device_view"]["windows"]
    if fault == "missing_profile":
        windows[2]["projection_profile_id"] = "missing"
    elif fault == "wrong_direction":
        windows[1]["projection_profile_id"] = "macro"
    elif fault == "bad_crop":
        windows[0]["xywh"] = [0, 0, 41, 40]
    else:
        windows[0]["frame_id"] = "missing"
    with pytest.raises(ValueError):
        run(indexed_pack)
    assert not out.exists()


def test_ambiguous_source_geometry_cannot_silently_pick_a_window(indexed_pack):
    root, request, _, out = indexed_pack
    case = json.loads((root / "case.json").read_text())
    case["geometry_observations"].append(
        dict(case["geometry_observations"][0], xywh=[11, 12, 4, 6])
    )
    write(root / "case.json", case)
    request["case"] = ref(root, "case.json")
    with pytest.raises(ValueError, match="Multiple"):
        run(indexed_pack)
    assert not out.exists()


def test_device_view_does_not_change_block_state_or_confirmed_terminals(indexed_pack, tmp_path):
    first = run(indexed_pack)
    root, request, path, _ = indexed_pack
    request.pop("device_view")
    write(path, request)
    second = run_package(path, tmp_path / "without-index", root)
    assert first["block_state_id"] == second["block_state_id"]
    assert first["electrical_acceptance"] == second["electrical_acceptance"]
