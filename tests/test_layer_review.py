"""The common delivery must preserve context and reject unsafe adoption atomically."""

import copy
import json

import pytest
from PIL import Image

from silicon_eye.geometry_reconstruction import digest
from silicon_eye.joint_layers import load_snapshot
from silicon_eye.layer_review import ReviewRequest, deliver


def rect(lft, top, rgt, bottom):
    return [[lft, top], [rgt, top], [rgt, bottom], [lft, bottom]]


def save(root, name, value):
    path = root / name
    path.write_text(json.dumps(value))
    return dict(path=name, sha256=digest(path))


@pytest.fixture
def project(tmp_path):
    material = dict(
        AA_objects=[dict(id="A", outer_xyxy=[0, 10, 100, 110])],
        objects=[
            dict(
                id="G",
                kind="MOS_gate_body",
                AA_target="A",
                layout_outline=rect(40, 0, 50, 120),
                acceptance=dict(joint_geometry="AI_candidate"),
            )
        ],
        guard_AA_ids=[],
        canvas_wh=[150, 150],
        relative_budget=dict(gate_extension_px=8),
    )
    cut = dict(
        id="C",
        family="F",
        column=0,
        row=0,
        landing_material="AA",
        AA_target="A",
        layout_outline=rect(17.5, 27.5, 22.5, 32.5),
        source_frame="poly",
        source_evidence=dict(native_center=[20, 30], supported=True),
    )
    budget = dict(square_side=5, min_gap_px=3, enclosure_px=1, channel_clearance_px=1)
    values = dict(
        materials=material,
        contacts=dict(objects=[cut], envelope="retained"),
        parent_spec=dict(budget=budget),
        human_review=dict(approved_scope="identity_not_pixels"),
        unknown=dict(unknown_scopes=[dict(id="U", layout_bounds=[110, 0, 120, 10])]),
        use_contract=dict(automatic_network_export_allowed=False),
        stage=dict(whole_frame_complete=False),
    )
    inputs = {key: save(tmp_path, key + ".json", val) for key, val in values.items()}
    Image.new("RGB", (150, 150)).save(tmp_path / "photo.png")
    photo = dict(path="photo.png", sha256=digest(tmp_path / "photo.png"))
    manifest = dict(
        id="parent",
        canvas_wh=[150, 150],
        source_wh=[150, 150],
        inputs=inputs,
        budget=budget,
        source_photos=dict(poly=photo),
        retired_contact_ids=["RETIRED"],
    )
    request = dict(
        schema_version=1,
        document_kind="layer_reconstruction_review",
        id="test",
        target_layer="POLY",
        mode="inspect",
        snapshot=save(tmp_path, "snapshot.json", manifest),
        windows=[
            dict(
                id="one", layout_bounds=[0, 0, 150, 150], source_windows=dict(poly=[0, 0, 150, 150])
            )
        ],
    )
    return tmp_path, request, material, cut


def run(project, request=None):
    root, default, _, _ = project
    save(root, "request.json", request or default)
    return deliver(root, root / "request.json", root / "out")


def patch(project, layer="POLY"):
    _, request, material, cut = project
    request = copy.deepcopy(request)
    before = material["objects"][0] if layer == "POLY" else cut
    after = copy.deepcopy(before)
    request.update(
        mode="revise",
        authorized_ids={layer: [before["id"]]},
        changes=[
            dict(
                layer=layer,
                id=before["id"],
                before=before,
                after=after,
                reason="Source-supported local revision",
                evidence=[request["snapshot"]],
            )
        ],
    )
    return request, after


def test_inspect_keeps_parent_and_unknown_without_cloning_models(project):
    root, request, _, _ = project
    report = run(project)
    assert report["status"] == "PASS"
    package = json.loads((root / "out/manifest.json").read_text())
    assert package["next_snapshot"] == request["snapshot"]
    assert not (root / "out/joint-snapshot.json").exists()
    assert json.loads((root / "out/delta.json").read_text()) == []
    context = json.loads((root / "out/continuation-context.json").read_text())
    assert context["inherited_documents"]["unknown"]["unknown_scopes"][0]["id"] == "U"
    assert context["inherited_documents"]["human_review"]["approved_scope"] == "identity_not_pixels"
    for path, sha in package["artifacts"].items():
        assert digest(root / "out" / path) == sha


def test_scoped_revision_roundtrips_with_companions_and_envelope(project):
    root, _, material, cut = project
    request, after = patch(project)
    after["layout_outline"] = rect(40, 0, 50, 121)
    assert run(project, request)["status"] == "PASS"
    candidate = load_snapshot(root, root / "out/joint-snapshot.json")
    assert candidate["materials"]["AA_objects"] == material["AA_objects"]
    assert candidate["contacts"] == [cut]
    assert candidate["values"]["contacts"]["envelope"] == "retained"
    assert candidate["materials"]["objects"][0] == after
    assert candidate["manifest"]["adoption_status"] == "candidate_not_new_human_approval"


def test_joint_failure_writes_diagnostics_but_no_continuation(project):
    root = project[0]
    request, after = patch(project)
    after["layout_outline"] = rect(40, 0, 50, 90)
    report = run(project, request)
    assert report["status"] == "FAIL"
    assert not (root / "out/joint-snapshot.json").exists()
    assert json.loads((root / "out/manifest.json").read_text())["next_snapshot"] is None
    assert (root / "out/index.html").exists()


@pytest.mark.parametrize("error", ["scope", "stale", "approval", "window", "hash"])
def test_invalid_request_never_publishes_partial_package(project, error):
    root = project[0]
    request, after = patch(project)
    if error == "scope":
        request["authorized_ids"] = {}
    elif error == "stale":
        request["changes"][0]["before"] = {}
    elif error == "approval":
        after["acceptance"]["joint_geometry"] = "human_accepted"
    elif error == "window":
        request["windows"][0]["source_windows"]["poly"] = [0, 0, 151, 150]
    else:
        request["snapshot"]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        run(project, request)
    assert not (root / "out").exists()


def test_inspect_cannot_smuggle_changes_or_budget(project):
    request, _ = patch(project)
    request["mode"] = "inspect"
    with pytest.raises(ValueError):
        ReviewRequest.model_validate(request)
    request["mode"] = "revise"
    request["budget"] = dict(min_gap_px=0)
    with pytest.raises(ValueError):
        ReviewRequest.model_validate(request)


def test_retired_contact_cannot_return_even_if_geometry_is_valid(project):
    root, request, _, cut = project
    request = copy.deepcopy(request)
    new = copy.deepcopy(cut)
    new.update(id="RETIRED", family="new-family", layout_outline=rect(27.5, 27.5, 32.5, 32.5))
    new["source_evidence"]["native_center"] = [30, 30]
    request.update(
        mode="revise",
        target_layer="CT",
        authorized_ids=dict(CT=["RETIRED"]),
        changes=[
            dict(
                layer="CT",
                id="RETIRED",
                before=None,
                after=new,
                reason="Candidate addition",
                evidence=[request["snapshot"]],
            )
        ],
    )
    report = run(project, request)
    assert report["geometry_status"] == "PASS"
    assert report["status"] == "FAIL"
    assert report["retired_contact_ids_resurrected"] == ["RETIRED"]
    assert not (root / "out/joint-snapshot.json").exists()
