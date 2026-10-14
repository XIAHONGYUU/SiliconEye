import json

import cv2
import numpy as np
import pytest

from silicon_eye.material_contours import run_contours, threshold_candidates
from silicon_eye.registration_audit import digest


def ring_image():
    image = np.zeros((64, 80, 3), np.uint8)
    image[10:54, 15:65] = 220
    image[22:42, 27:53] = 0
    return image


def test_ring_holes_are_preserved_and_coordinates_are_native():
    record, masks = threshold_candidates(ring_image(), [101, 203])
    assert record["status"] == "candidate"
    assert masks["bright"][32, 40] == 0
    assert masks["bright"][16, 40] == 255
    np.testing.assert_array_equal(masks["bright"] + masks["dark"], np.full((64, 80), 255, np.uint8))
    bright = record["variants"]["bright"]
    assert any(c["hierarchy_next_prev_child_parent"][3] >= 0 for c in bright["contours"])
    assert bright["mask_area_px2"] == int(np.count_nonzero(masks["bright"]))
    assert min(x for c in bright["contours"] for x, y in c["xy_native"]) >= 116
    assert bright["closed_material_boundary_confirmed"] is False


def test_clipped_strip_is_not_claimed_as_closed_material_boundary():
    image = np.zeros((64, 80, 3), np.uint8)
    image[:, 20:40] = 220
    record, _ = threshold_candidates(image, [0, 0])
    assert any(c["touches_roi_border"] for c in record["variants"]["bright"]["contours"])
    assert record["variants"]["bright"]["closed_material_boundary_confirmed"] is False


def test_weak_texture_has_no_fabricated_alternative_mask():
    record, masks = threshold_candidates(np.full((64, 80, 3), 80, np.uint8), [0, 0])
    assert record["status"] == "unknown"
    assert masks == {}


@pytest.mark.parametrize("sigma,kernel", [(float("nan"), 7), (1.5, 4)])
def test_invalid_measurement_parameters_rejected(sigma, kernel):
    with pytest.raises(ValueError):
        threshold_candidates(ring_image(), [0, 0], sigma, kernel)


def make_spec(tmp_path, control=False):
    source = tmp_path / "source"
    source.mkdir()
    image = source / "aa.png"
    cv2.imwrite(str(image), ring_image())
    reference = tmp_path / "registration.json"
    reference.write_text(
        json.dumps({"status": "complete", "source_sha256": {"reference": digest(image)}})
    )
    annotations = {
        "schema_version": 1,
        "case_id": "test",
        "coordinate_frame": "native_source_pixel_xy_half_open",
        "physical_scale_status": "unknown",
        "physical_scale_px_per_um": None,
        "registration_manifest": str(reference),
        "registration_sha256": digest(reference),
        "sources": {
            "aa": {
                "path": str(image),
                "sha256": digest(image),
                "size_wh": [80, 64],
                "scope_xywh": [0, 0, 80, 64],
                "registration_side": "reference",
                "layer_label": "active_area",
                "layer_status": "unknown",
                "layer_review": None,
            }
        },
        "objects": [
            {
                "id": "aa-region",
                "source_id": "aa",
                "bbox_xywh": [5, 5, 70, 54],
                "role": "registration_control" if control else "region_candidate",
                "usage": "diagnostic" if control else "annotation_draft",
                "label": "region",
                "boundary_definition": "visual_roi_not_material_mask",
                "producer": "reasoning_model",
                "status": "candidate",
                "review": None,
                "uncertainty": "test only",
                "device_type": "unknown",
                "terminals": [],
            }
        ],
    }
    annotation_file = tmp_path / "annotations.json"
    annotation_file.write_text(json.dumps(annotations))
    spec = {
        "schema_version": 1,
        "annotations": str(annotation_file),
        "object_ids": ["aa-region"],
        "gaussian_sigma": 1.5,
        "gaussian_kernel": 7,
        "threshold_method": "otsu_dual_polarity",
        "semantic_status": "unknown",
        "morphology": "none",
        "coordinate_frame": "native_source_pixel_center_xy",
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    return path, image


def test_evidence_pack_masks_provenance_and_no_source_modification(tmp_path):
    spec, image = make_spec(tmp_path)
    before = digest(image)
    out = tmp_path / "out"
    result = run_contours(str(spec), str(out))
    assert digest(image) == before
    assert result["material_ground_truth_ready"] is False
    assert result["device_ground_truth_ready"] is False
    assert result["objects"]["aa-region"]["crop_native_xywh"] == [5, 5, 70, 54]
    assert cv2.imread(str(out / "aa-region/bright-mask.png"), 0).shape == (54, 70)
    with pytest.raises(ValueError, match="new directory"):
        run_contours(str(spec), str(out))
    with pytest.raises(ValueError, match="source images"):
        run_contours(str(spec), str(image.parent / "output"))


def test_control_objects_cannot_be_used_as_candidate_material_rois(tmp_path):
    spec, _ = make_spec(tmp_path, control=True)
    with pytest.raises(ValueError, match="region candidates"):
        run_contours(str(spec), str(tmp_path / "out"))
    assert not (tmp_path / "out").exists()
