import cv2
import numpy as np
import pytest

from silicon_eye.guided_materials import ct_support, guided_mask, read_paint


def test_paint_import_uses_edits_not_original_photo_colors():
    original = np.full((40, 80, 3), 100, np.uint8)
    original[0:5, 0:5] = [0, 0, 255]
    marked = original.copy()
    marked[10:20, 10:20] = [0, 0, 255]
    marked[10:20, 50:60] = [240, 176, 0]
    result = read_paint(marked, original)
    assert np.count_nonzero(result["aa"]) == 100
    assert np.count_nonzero(result["poly"]) == 100
    assert not result["aa"][0, 0]


def test_mismatched_sheet_and_unexplained_edits_are_rejected():
    original = np.full((40, 80, 3), 100, np.uint8)
    with pytest.raises(ValueError, match="size"):
        read_paint(original[:20], original)
    changed = original.copy()
    changed[10, 10] = 255
    with pytest.raises(ValueError, match="unexplained"):
        read_paint(changed, original)


def test_aa_refinement_uses_raw_image_and_keeps_unpainted_unknown():
    raw = np.full((80, 120, 3), 40, np.uint8)
    raw[20:60, 30:90] = 170
    prompt = np.zeros((80, 120), np.uint8)
    prompt[25:55, 35:85] = 255
    old = raw.copy()
    result = guided_mask(raw, prompt, "aa", radius=8, iterations=3)
    np.testing.assert_array_equal(raw, old)
    assert result["visible"][40, 60]
    assert not result["visible"][2, 2]
    assert result["outside_search_unknown"][2, 2]
    assert not np.any(result["visible"] & ~result["search_domain"])
    # Conservative AA may shrink rather than grow. It must stay inside the known
    # synthetic material and retain the strong interior; growth is not a success metric.
    truth = np.zeros(prompt.shape, dtype=bool)
    truth[20:60, 30:90] = True
    assert not np.any(result["visible"] & ~truth)
    assert not np.array_equal(result["visible"], prompt > 0)


def test_ct_is_visible_occlusion_unknown_and_not_poly_material():
    raw = np.full((100, 140, 3), 70, np.uint8)
    raw[30:70, 20:120] = 110
    cv2.rectangle(raw, (64, 44), (75, 55), (250, 250, 250), -1)
    prompt = np.zeros((100, 140), np.uint8)
    prompt[35:65, 25:115] = 255
    assert ct_support(raw)[50, 70]
    result = guided_mask(raw, prompt, "poly", iterations=3)
    assert result["ct_unknown"][50, 70]
    assert not result["visible"][50, 70]
    assert not np.any(result["visible"] & result["ct_unknown"])


@pytest.mark.parametrize("radius,iterations", [(0, 5), (8, 0), (1.5, 5)])
def test_bad_refinement_parameters_rejected(radius, iterations):
    raw = np.full((30, 30, 3), 70, np.uint8)
    prompt = np.zeros((30, 30), np.uint8)
    prompt[10:20, 10:20] = 255
    with pytest.raises(ValueError):
        guided_mask(raw, prompt, "poly", radius, iterations)


def test_no_prompt_is_not_silently_treated_as_a_negative_example():
    raw = np.full((30, 30, 3), 70, np.uint8)
    with pytest.raises(ValueError, match="positive"):
        guided_mask(raw, np.zeros((30, 30), np.uint8), "aa")


def guided_fixture(tmp_path):
    import json

    from silicon_eye.registration_audit import digest

    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    original = np.full((74, 165, 3), 35, np.uint8)
    panels = {}
    hashes = {}
    for name, sx in [("aa", 0), ("poly", 85)]:
        raw = np.full((64, 80, 3), 60 if name == "aa" else 150, np.uint8)
        raw[12:52, 15:65] = 170 if name == "aa" else 90
        if name == "poly":
            raw[28:39, 35:46] = 250
        source = source_dir / (name + ".png")
        cv2.imwrite(str(source), raw)
        original[5:69, sx : sx + 80] = raw
        panels[name] = {
            "source_path": str(source),
            "source_sha256": digest(source),
            "source_crop_xywh": [0, 0, 80, 64],
            "sheet_panel_xywh": [sx, 5, 80, 64],
            "scale": 1,
            "resampling": False,
        }
        hashes["reference" if name == "aa" else "target"] = digest(source)
    marked = original.copy()
    marked[25:45, 25:55] = [0, 0, 255]
    marked[29:49, 105:140] = [240, 176, 0]
    cv2.imwrite(str(tmp_path / "original.png"), original)
    cv2.imwrite(str(tmp_path / "marked.png"), marked)
    meta = {"panels": panels, "sheet_sha256": digest(tmp_path / "original.png")}
    (tmp_path / "sample.json").write_text(json.dumps(meta))
    registration = {"source_sha256": hashes, "matrix_native": np.eye(3).tolist()}
    (tmp_path / "registration.json").write_text(json.dumps(registration))
    spec = {"schema_version": 1, "search_radius_px": 8, "iterations": 3}
    for key, name in [
        ("marked_sheet", "marked.png"),
        ("original_sheet", "original.png"),
        ("sample_manifest", "sample.json"),
        ("registration_manifest", "registration.json"),
    ]:
        spec[key] = str(tmp_path / name)
        spec[key + "_sha256"] = digest(tmp_path / name)
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    return path, spec


def test_guided_pack_uses_unpainted_raw_and_identity_context(tmp_path):
    from silicon_eye.guided_materials import run_guided
    from silicon_eye.registration_audit import digest

    path, _ = guided_fixture(tmp_path)
    before = digest(tmp_path / "sources/aa.png")
    out = tmp_path / "out"
    result = run_guided(str(path), str(out))
    assert result["material_status"] == "candidate"
    assert result["accuracy_evaluated"] is False
    assert result["aa_context"]["used_to_veto_poly"] is False
    np.testing.assert_array_equal(
        cv2.imread(str(out / "aa/raw.png")), cv2.imread(str(tmp_path / "sources/aa.png"))
    )
    np.testing.assert_array_equal(
        cv2.imread(str(out / "partial-aa-context-in-poly.png"), 0),
        cv2.imread(str(out / "aa/visible.png"), 0),
    )
    assert digest(tmp_path / "sources/aa.png") == before
    with pytest.raises(ValueError, match="new directory"):
        run_guided(str(path), str(out))


@pytest.mark.parametrize("defect", ["marked_hash", "mapping"])
def test_sheet_provenance_and_pixel_mapping_fail_before_output(tmp_path, defect):
    import json

    from silicon_eye.guided_materials import run_guided
    from silicon_eye.registration_audit import digest

    path, spec = guided_fixture(tmp_path)
    if defect == "marked_hash":
        spec["marked_sheet_sha256"] = "0" * 64
    else:
        meta = json.loads((tmp_path / "sample.json").read_text())
        meta["panels"]["aa"]["sheet_panel_xywh"][0] += 1
        (tmp_path / "sample.json").write_text(json.dumps(meta))
        spec["sample_manifest_sha256"] = digest(tmp_path / "sample.json")
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError):
        run_guided(str(path), str(tmp_path / "out"))
    assert not (tmp_path / "out").exists()


def test_unproven_ring_center_merge_is_removed_without_deleting_prompts():
    from silicon_eye.guided_materials import preserve_prompt_separation

    prompt = np.zeros((100, 140), np.uint8)
    cv2.rectangle(prompt, (20, 20), (120, 80), 255, 4)
    prompt[34:67, 36:105] = 255
    merged = np.zeros_like(prompt, dtype=bool)
    merged[18:83, 18:123] = True
    fixed, unknown, conflicts = preserve_prompt_separation(merged, prompt)
    _, labels = cv2.connectedComponents(fixed.astype(np.uint8))
    assert labels[50, 70] != labels[20, 70]
    assert labels[50, 70] > 0 and labels[20, 70] > 0
    assert np.all(fixed[prompt > 0])
    assert np.any(unknown)
    assert len(conflicts) == 1


def test_aa_refinement_retains_visible_gap_between_center_and_ring():
    raw = np.full((100, 140, 3), 40, np.uint8)
    cv2.rectangle(raw, (20, 20), (120, 80), (200, 200, 200), 5)
    raw[34:67, 36:105] = 200
    prompt = np.zeros((100, 140), np.uint8)
    cv2.rectangle(prompt, (20, 20), (120, 80), 255, 2)
    prompt[36:65, 38:103] = 255
    result = guided_mask(raw, prompt, "aa", radius=8, iterations=3)
    _, labels = cv2.connectedComponents(result["visible"].astype(np.uint8))
    assert labels[50, 70] > 0 and labels[20, 70] > 0
    assert labels[50, 70] != labels[20, 70]
    assert not result["visible"][29, 70]
    # The caller's old 8px radius cannot expand AA beyond its conservative limit.
    allowed = cv2.dilate(prompt, np.ones((5, 5), np.uint8)) > 0
    assert not np.any(result["visible"] & ~allowed)
