import copy
import json

import cv2
import numpy as np
import pytest
from pydantic import ValidationError

from silicon_eye.pixel_annotations import review_annotations
from silicon_eye.registration_audit import digest
from silicon_eye.schemas.pixel_annotation import PixelAnnotationSet


def fixture_document(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    image = source_dir / "aa.png"
    cv2.imwrite(str(image), np.full((64, 64, 3), 80, np.uint8))
    registration = tmp_path / "registration.json"
    registration.write_text(
        json.dumps({"status": "complete", "source_sha256": {"reference": digest(image)}})
    )
    doc = {
        "schema_version": 1,
        "case_id": "fixture",
        "coordinate_frame": "native_source_pixel_xy_half_open",
        "physical_scale_status": "unknown",
        "physical_scale_px_per_um": None,
        "registration_manifest": str(registration),
        "registration_sha256": digest(registration),
        "sources": {
            "aa": {
                "path": str(image),
                "sha256": digest(image),
                "size_wh": [64, 64],
                "scope_xywh": [4, 4, 56, 56],
                "registration_side": "reference",
                "layer_label": "active_area",
                "layer_status": "confirmed",
                "layer_review": {
                    "reviewer": "test_fixture",
                    "actor": "human",
                    "decision": "confirm",
                    "evidence": "test record only",
                },
            }
        },
        "objects": [
            {
                "id": "aa-region",
                "source_id": "aa",
                "bbox_xywh": [12, 12, 20, 20],
                "role": "region_candidate",
                "usage": "annotation_draft",
                "label": "region",
                "boundary_definition": "visual_roi_not_material_mask",
                "producer": "reasoning_model",
                "status": "candidate",
                "review": None,
                "uncertainty": "test candidate, not device truth",
                "device_type": "unknown",
                "terminals": [],
            }
        ],
    }
    return doc


@pytest.mark.parametrize(
    "defect",
    [
        "nan",
        "outside",
        "empty",
        "duplicate",
        "source",
        "unsafe_id",
        "unreviewed_geometry",
        "unreviewed_layer",
        "control_holdout",
        "device",
        "scale",
    ],
)
def test_invalid_or_promoted_drafts_are_rejected(tmp_path, defect):
    doc = fixture_document(tmp_path)
    obj = doc["objects"][0]
    if defect == "nan":
        obj["bbox_xywh"][0] = float("nan")
    elif defect == "outside":
        obj["bbox_xywh"][0] = 59
    elif defect == "empty":
        obj["bbox_xywh"][2] = 0
    elif defect == "duplicate":
        doc["objects"].append(copy.deepcopy(obj))
    elif defect == "source":
        obj["source_id"] = "missing"
    elif defect == "unsafe_id":
        doc["sources"]["../aa"] = doc["sources"].pop("aa")
        obj["source_id"] = "../aa"
    elif defect == "unreviewed_geometry":
        obj["status"] = "confirmed"
    elif defect == "unreviewed_layer":
        doc["sources"]["aa"]["layer_review"] = None
    elif defect == "control_holdout":
        obj.update(role="registration_control", usage="holdout")
    elif defect == "device":
        obj["device_type"] = "nmos"
    elif defect == "scale":
        doc["physical_scale_px_per_um"] = 10
    with pytest.raises(ValidationError):
        PixelAnnotationSet.model_validate(doc)


def test_render_preserves_source_and_does_not_create_device_truth(tmp_path):
    doc = fixture_document(tmp_path)
    path = tmp_path / "input.json"
    path.write_text(json.dumps(doc))
    out = tmp_path / "review"
    result = review_annotations(str(path), str(out))
    assert result["geometry_status_counts"] == {"candidate": 1}
    assert result["layer_status"] == {"aa": "confirmed"}
    assert result["device_ground_truth_ready"] is False
    assert result["segmentation_ground_truth_ready"] is False
    assert digest(tmp_path / "source/aa.png") == doc["sources"]["aa"]["sha256"]
    assert cv2.imread(str(out / "aa-annotations.jpg")).shape == (56, 56, 3)
    assert not (out / "phase1_devices.json").exists()
    with pytest.raises(ValueError, match="new directory"):
        review_annotations(str(path), str(out))
    with pytest.raises(ValueError, match="source image directory"):
        review_annotations(str(path), str(tmp_path / "source/output"))


@pytest.mark.parametrize("defect", ["source_hash", "registration_hash", "image_size"])
def test_runtime_provenance_rejected_before_outputs(tmp_path, defect):
    doc = fixture_document(tmp_path)
    if defect == "source_hash":
        doc["sources"]["aa"]["sha256"] = "0" * 64
    elif defect == "registration_hash":
        doc["registration_sha256"] = "0" * 64
    else:
        doc["sources"]["aa"]["size_wh"] = [65, 64]
    path = tmp_path / "input.json"
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError):
        review_annotations(str(path), str(tmp_path / "review"))
    assert not (tmp_path / "review").exists()


def test_confirmed_roi_does_not_confirm_devices_or_material_masks(tmp_path):
    doc = fixture_document(tmp_path)
    doc["objects"][0]["status"] = "confirmed"
    doc["objects"][0]["review"] = doc["sources"]["aa"]["layer_review"]
    path = tmp_path / "input.json"
    path.write_text(json.dumps(doc))
    result = review_annotations(str(path), str(tmp_path / "review"))
    assert result["geometry_status_counts"] == {"confirmed": 1}
    assert result["device_ground_truth_ready"] is False
    assert result["segmentation_ground_truth_ready"] is False


@pytest.mark.parametrize("defect", ["missing", "same_source", "confirmed"])
def test_invalid_correspondence_does_not_use_confirmed_layer_as_identity(tmp_path, defect):
    doc = fixture_document(tmp_path)
    doc["correspondences"] = [
        {
            "id": "PAIR",
            "object_ids": ["aa-region", "aa-region"],
            "status": "candidate",
            "producer": "reasoning_model",
            "review": None,
            "uncertainty": "test uncertainty",
        }
    ]
    if defect == "missing":
        doc["correspondences"][0]["object_ids"][1] = "absent"
    elif defect == "confirmed":
        doc["correspondences"][0]["status"] = "confirmed"
    with pytest.raises(ValidationError):
        PixelAnnotationSet.model_validate(doc)
