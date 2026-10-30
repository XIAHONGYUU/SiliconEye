"""Current ledger closeout must retain scope crossings, unknowns and review limits."""

import csv
import json
from pathlib import Path

import pytest

from silicon_eye.conductive_coverage import reconcile, run
from silicon_eye.geometry_reconstruction import digest

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "benchmarks/conductive-corridor-closeout-v2/request.json"


def request():
    return json.loads(REQUEST.read_text())


def test_current_scope_balances_without_claiming_photo_or_network_completion():
    data, _ = reconcile(ROOT, request())
    c = data["coverage"]
    assert (c["declared_metal_count"], c["reviewed_interfaces"], c["candidate_design_cuts"]) == (
        30,
        9,
        42,
    )
    assert c["source_endpoint_count"] == 60 and c["scope_exit_endpoints"] == 48
    assert c["retained_qualitative_geometries"] == 23
    assert len(c["revised_candidate_metal_ids"]) == 7
    assert c["M2_without_identified_interface"] == ["C-M2-08"]
    assert c["boundary_interface_ids"] == ["C06-V2"]
    assert c["fully_contained_source_interface_windows"] == 8
    assert c["actual_interface_total"] is None and c["photo_coverage_fraction"] is None
    assert not c["complete_network"] and not c["canonical_geometry_adopted"]
    assert c["M1_V1_continuous_scope"] == "NOT_EVALUATED"


@pytest.mark.parametrize(
    "change, message",
    [
        (lambda r: r.update(boundary_interfaces={}), "Boundary interface"),
        (lambda r: r["boundary_interfaces"]["C06-V2"].update(reason=""), "Boundary interface"),
        (lambda r: r.update(unresolved_metals={}), "Unreviewed M2"),
        (
            lambda r: r["unresolved_metals"]["C-M2-08"].update(physical_absence_confirmed=True),
            "physical absence",
        ),
    ],
)
def test_scope_and_ai_unknown_cannot_be_silently_promoted(change, message):
    r = request()
    change(r)
    with pytest.raises(ValueError, match=message):
        reconcile(ROOT, r)


def test_stale_workflow_cannot_be_presented_as_current_snapshot():
    r = request()
    p = ROOT / "benchmarks/n1-v2-local-reconstruction-v1/next-request.json"
    r["workflow_request"] = dict(path=str(p.relative_to(ROOT)), sha256=digest(p))
    with pytest.raises(ValueError, match="Current model replay differs"):
        reconcile(ROOT, r)


def test_boundary_reference_cannot_transfer_another_interfaces_approval():
    r = request()
    p = ROOT / "benchmarks/corridor-0506-joint-reviewed-v3/C05-V2-carrier-review.json"
    r["boundary_interfaces"]["C06-V2"]["human_review"] = dict(
        path=str(p.relative_to(ROOT)), sha256=digest(p)
    )
    with pytest.raises(ValueError, match="Boundary interface"):
        reconcile(ROOT, r)


def test_export_rows_and_manifest_replay_without_overwriting():
    # Output follows the project containment rule and can be read back deterministically.
    import tempfile

    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as directory:
        out = Path(directory) / "coverage"
        data = run(ROOT, REQUEST, out)
        with (out / "metals.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == len(data["metals"]) == 30
        assert len(json.loads((out / "interfaces.json").read_text())) == 9
        manifest = json.loads((out / "manifest.json").read_text())
        assert all(digest(out / p) == h for p, h in manifest["artifacts"].items())
        assert b"\r\n" not in (out / "metals.csv").read_bytes()
        with pytest.raises(ValueError, match="Output must be new"):
            run(ROOT, REQUEST, out)


def test_unqualified_layer_scope_is_rejected_before_claiming_coverage():
    import tempfile

    r = request()
    original = json.loads((ROOT / r["inventory"]["path"]).read_text())
    original["scope"]["frames"]["m1"] = original["scope"]["frames"]["m2"]
    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as directory:
        path = Path(directory) / "unsupported-scope.json"
        path.write_text(json.dumps(original))
        r["inventory"] = dict(path=str(path.relative_to(ROOT)), sha256=digest(path))
        with pytest.raises(ValueError, match="Only the M2/V2/M3 continuous scope"):
            reconcile(ROOT, r)
