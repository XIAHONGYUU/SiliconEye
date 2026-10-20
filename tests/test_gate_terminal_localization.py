"""Contact positions must follow source peaks, not a two-cut array expectation."""

import copy
import runpy
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
localize = runpy.run_path(str(ROOT / "scripts/build_gate_terminal_review.py"))[
    "localize_bottom_contacts"
]


def fixture():
    model = dict(objects=[dict(id="gate", native_outline=[[30, 10], [60, 10], [60, 60], [30, 60]])])
    paths = dict(
        profile_rows=[
            dict(id="left", source_path=[[20, 0], [20, 80]]),
            dict(id="right", source_path=[[70, 0], [70, 80]]),
            dict(id="ring", source_path=[[10, 90], [80, 90]]),
        ]
    )
    recipe = dict(
        gates=[dict(gate_id="gate", left_column="left", right_column="right", lower_ring="ring")],
        column_inset=8,
        ring_margin=14,
        search_above=21,
        search_below=19,
        profile_min_gray=180,
        peak_min_distance=8,
        min_gray=225,
        min_residual=18,
    )
    return model, paths, recipe


@pytest.mark.parametrize("centers", [[], [43], [31, 55]])
def test_no_expected_count_filling_and_localization_corrects_prior_end_locator(centers):
    image = np.full((100, 100, 3), 100, np.uint8)
    for x in centers:
        cv2.rectangle(image, (x - 3, 52), (x + 3, 58), (255, 255, 255), -1)
    model, paths, recipe = fixture()
    old = copy.deepcopy((model, paths, recipe))
    row = localize(image, model, paths, recipe)[0]
    assert len(row["retained_peaks"]) == len(centers)
    if centers:
        assert all(abs(p["native_center"][1] - 55) <= 1 for p in row["retained_peaks"])
        assert row["prior_derived_endpoint_y"] == 60
    assert (model, paths, recipe) == old


def test_weaker_extra_peak_is_retained_as_evidence_not_promoted_into_ct():
    image = np.full((100, 100, 3), 100, np.uint8)
    for x, gray in [(31, 255), (43, 205), (55, 255)]:
        cv2.rectangle(image, (x - 3, 52), (x + 3, 58), (gray, gray, gray), -1)
    model, paths, recipe = fixture()
    row = localize(image, model, paths, recipe)[0]
    assert len(row["retained_peaks"]) == 2
    assert len(row["weaker_peaks_not_deleted"]) == 1
    assert row["weaker_peaks_not_deleted"][0]["supported"] is False


def test_upper_terminal_search_is_not_forced_to_use_the_previous_bottom_side():
    image = np.full((100, 100, 3), 100, np.uint8)
    for x in [31, 55]:
        cv2.rectangle(image, (x - 3, 24), (x + 3, 30), (255, 255, 255), -1)
    model, paths, recipe = fixture()
    model["objects"][0]["native_outline"] = [[30, 40], [60, 40], [60, 75], [30, 75]]
    paths["profile_rows"][-1]["source_path"] = [[10, 10], [80, 10]]
    recipe["gates"][0]["side"] = "top"
    row = localize(image, model, paths, recipe)[0]
    assert len(row["retained_peaks"]) == 2
    assert row["prior_derived_endpoint_y"] == 40
    assert all(abs(p["native_center"][1] - 27) <= 1 for p in row["retained_peaks"])


def test_common_design_row_phase_does_not_change_the_measured_source_observations():
    import json

    from silicon_eye.ct_joint_reconstruction import fit_family

    spec = json.loads((ROOT / "benchmarks/ct-upper-small-mos-v1/spec-v1.json").read_text())
    model = json.loads((ROOT / spec["inputs"]["materials"]["path"]).read_text())
    photo = cv2.imread(str(ROOT / spec["inputs"]["photo"]["path"]))
    family = copy.deepcopy(spec["families"][0])
    old = copy.deepcopy(model)
    first, fit1 = fit_family(photo, model, family, spec["budget"])
    family["layout_row_origin"] = 926
    family["layout_row_pitch"] = 10
    second, fit2 = fit_family(photo, model, family, spec["budget"])
    assert fit1["source_observations"] == fit2["source_observations"]
    assert [o["source_evidence"] for o in first] == [o["source_evidence"] for o in second]
    assert sorted({o["layout_center"][1] for o in second}) == [926, 936]
    assert model == old
