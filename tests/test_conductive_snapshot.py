"""Work snapshots preserve reviewed records without merging unregistered canvases."""

import copy
import json
import tempfile
from pathlib import Path
from xml.etree import ElementTree

import pytest

from silicon_eye.conductive_snapshot import assemble, page, require_preserved
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/conductive-work-baseline-v1.json"


@pytest.fixture(scope="module")
def built():
    return assemble(ROOT, json.loads(CONFIG.read_text()))


def test_three_coordinate_spaces_keep_real_reviews_and_unmapped_terminal(built):
    work, report, _, _ = built
    assert set(work["coordinate_spaces"]) == {"materials", "medium", "independent"}
    assert len(work["objects"]) == len({o["key"] for o in work["objects"]}) == 41
    assert len(work["reviewed_interfaces"]) == 13
    assert len(work["accepted_groups"]) == 2
    assert len(work["material_unknowns"]["unknown_scopes"]) == 6
    assert work["reviewed_terminal_links"][0]["record"]["canonical_AA_object_ids"] is None
    assert report["work_snapshot_ready"] and not report["material_canvas_registration"]
    assert not work["canonical_geometry_adopted"] and not work["net_edges"]
    for field in ("source_to_design_transform", "placement_in_material_canvas"):
        assert work["coordinate_spaces"]["medium"][field] is None
    for domain in ("medium", "independent"):
        source = json.loads(
            (ROOT / "docs/assets/conductive-work-baseline-v1" / domain / "model.json").read_text()
        )
        retained = [
            r["record"] for r in work["reviewed_interfaces"] if r["coordinate_space"] == domain
        ]
        assert retained == source["reviewed_local_connections"]
        assert work["domains"][domain]["candidate_paths"] == source.get("path_hypotheses", [])
    assert report["domains"]["medium"]["metrics"]["V1_V2_overlap_area"] == 72
    q2 = report["domains"]["independent"]["metrics"]
    assert q2["V2_design_cuts"] == 6 and q2["V1_V2_overlap_area"] == 90
    assert 0.89 < q2["V2_M2_width_fraction"] < 0.90


@pytest.mark.parametrize(
    "flag",
    ["material_geometry_adoption", "cross_canvas_projection", "automatic_network_export_allowed"],
)
def test_request_cannot_self_authorize_physical_adoption(flag):
    request = json.loads(CONFIG.read_text())
    request[flag] = True
    with pytest.raises(ValueError, match="cannot enable"):
        assemble(ROOT, request)


@pytest.mark.parametrize("field", ["placement_in_material_canvas", "source_to_design_transform"])
def test_local_design_cannot_be_silently_treated_as_registered(field):
    request = json.loads(CONFIG.read_text())
    request["domains"][0][field] = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    with pytest.raises(ValueError, match="cannot claim a placement"):
        assemble(ROOT, request)


@pytest.mark.parametrize(
    "field", ["reviewed_interfaces", "accepted_groups", "reviewed_terminal_links", "objects"]
)
def test_next_snapshot_must_not_drop_existing_decisions_or_ids(built, field):
    work = built[0]
    changed = copy.deepcopy(work)
    changed[field].pop()
    with pytest.raises(ValueError, match="lost"):
        require_preserved(work, changed)


def test_next_snapshot_cannot_drop_unknowns_or_coordinate_domain(built):
    work = built[0]
    changed = copy.deepcopy(work)
    changed["material_unknowns"]["unknown_scopes"].pop()
    with pytest.raises(ValueError, match="unresolved material"):
        require_preserved(work, changed)
    changed = copy.deepcopy(work)
    changed["domains"].pop("independent")
    with pytest.raises(ValueError, match="lost a coordinate"):
        require_preserved(work, changed)


@pytest.mark.parametrize("tamper", ["connection", "geometry", "terminal"])
def test_rehashed_package_cannot_launder_changes_as_exact_continuation(tamper):
    request = json.loads(CONFIG.read_text())
    domain = request["domains"][0]
    source = ROOT / Path(domain["package"]["path"]).parent
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as tmp:
        target = Path(tmp)
        manifest = json.loads((source / "manifest.json").read_text())
        for name in manifest["artifacts"]:
            (target / name).write_bytes((source / name).read_bytes())
        model = json.loads((target / "model.json").read_text())
        if tamper == "connection":
            model["reviewed_local_connections"].pop()
        elif tamper == "geometry":
            model["objects_by_layer"]["M1"][0]["geometry"]["outer_xy"][0][0] += 1
        else:
            model["branch"].pop("reviewed_terminal_connection")
        (target / "model.json").write_text(json.dumps(model))
        manifest["artifacts"]["model.json"] = digest(target / "model.json")
        (target / "manifest.json").write_text(json.dumps(manifest))
        ref = dict(
            path=str((target / "manifest.json").relative_to(ROOT)),
            sha256=digest(target / "manifest.json"),
        )
        domain["package"] = ref
        next_request = json.loads((ROOT / domain["next_request"]["path"]).read_text())
        next_request["parent"] = ref
        (target / "next.json").write_text(json.dumps(next_request))
        domain["next_request"] = dict(
            path=str((target / "next.json").relative_to(ROOT)), sha256=digest(target / "next.json")
        )
        with pytest.raises(ValueError, match="exact no-change continuation"):
            assemble(ROOT, request)


def test_html_payload_roundtrips_svg_and_does_not_close_the_script(built):
    work, report, render, _ = built
    work = copy.deepcopy(work)
    work["domains"]["medium"]["limits"].append("</script><script>bad</script>")
    output = page(ROOT, ROOT / "runs/test-work-view", work, report, render)
    payload = output.split("const data = ", 1)[1].split(";\nconst escapeText", 1)[0]
    assert "</script>" not in payload
    data = json.loads(payload)
    for section in data["sections"]:
        ElementTree.fromstring(section["before"])
        ElementTree.fromstring(section["after"])
    assert data["work"] == work


def test_zoom_cannot_cut_off_the_old_or_current_array():
    request = json.loads(CONFIG.read_text())
    request["domains"][0]["focus"]["zoom_viewbox"] = [1355, 160, 20, 20]
    with pytest.raises(ValueError, match="Zoom view omits"):
        assemble(ROOT, request)
