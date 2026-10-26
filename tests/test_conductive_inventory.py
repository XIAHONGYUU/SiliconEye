"""Visible-ledger accounting must not be confused with pixel exhaustiveness."""

import copy
import json
from pathlib import Path

import pytest

from silicon_eye.conductive_inventory import audit, run

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benchmarks/conductive-corridor-inventory-v1/inventory.json"


def inventory():
    return json.loads(SOURCE.read_text())


def test_inventory_accounts_for_visible_fragments_without_claiming_complete_geometry():
    report, _ = audit(ROOT, inventory())
    assert report["metal_fragment_observations"] == {"m2": 8, "m3": 22}
    assert report["existing_model_correspondences"] == {"m2": 3, "m3": 5}
    assert report["unmodeled_fragment_observations"] == 22
    assert report["inherited_interfaces"] == 4 and report["unresolved_observations"] == 5
    assert report["boundary_exits"] == 48
    assert report["actual_photo_coverage_fraction"] is None
    assert report["five_layer_coverage"] == "NOT_EVALUATED"
    assert not report["complete_network"] and report["baseline_full_model_exact"]


@pytest.mark.parametrize(
    "mutation, message",
    [
        ("tile_gap", "Scan tiles leave a gap"),
        ("unlisted_record", "omitted from scan ledger"),
        ("missing_survey", "M2 interface survey omitted"),
        ("carrier_swap", "Inherited interface identity or approval changed"),
        ("hide_exit", "Boundary exit omitted"),
        ("approve_unknown", "Unknown observation cannot manufacture"),
    ],
)
def test_inventory_rejects_accounting_and_approval_regressions(mutation, message):
    data = inventory()
    if mutation == "tile_gap":
        data["scan_tiles"].pop()
    elif mutation == "unlisted_record":
        for tile in data["scan_tiles"]:
            tile["recorded_observation_ids"] = [
                key for key in tile["recorded_observation_ids"] if key != "C-M3-T01"
            ]
    elif mutation == "missing_survey":
        data["interface_surveys"].pop()
    elif mutation == "carrier_swap":
        data["inherited_interfaces"][0]["upper_metal_id"] = "RT-M3-MID"
    elif mutation == "hide_exit":
        data["metal_observations"][0]["endpoints"][-1]["state"] = "visible_terminal"
    else:
        data["unknown_observations"][0]["connection_confirmed"] = True
    with pytest.raises(ValueError, match=message):
        audit(ROOT, data)


def test_unlisted_pixel_omission_cannot_be_certified_by_a_consistent_ledger():
    data = copy.deepcopy(inventory())
    data["metal_observations"] = [r for r in data["metal_observations"] if r["id"] != "C-M3-T01"]
    for tile in data["scan_tiles"]:
        tile["recorded_observation_ids"] = [
            key for key in tile["recorded_observation_ids"] if key != "C-M3-T01"
        ]
    report, _ = audit(ROOT, data)
    # No detector is run: a whole omitted, unlisted source line is not observable to this checker.
    assert report["all_listed_records_accounted"]
    assert report["physical_inventory_exhaustiveness"] == "AI_SCANNED_NOT_INDEPENDENTLY_VERIFIED"
    assert report["actual_photo_coverage_fraction"] is None
    assert "INCOMPLETE" in report["status"]


def test_render_uses_existing_raw_assets_and_refuses_overwriting(tmp_path):
    # The production output contract deliberately remains inside the repository.
    import tempfile

    with tempfile.TemporaryDirectory(dir=ROOT / "runs") as temporary:
        output = Path(temporary) / "review"
        report = run(ROOT, SOURCE, output)
        assert report["baseline_full_model_exact"]
        assert sorted(p.name for p in output.iterdir()) == [
            "index.html",
            "inventory.json",
            "manifest.json",
            "report.json",
        ]
        html = (output / "index.html").read_text()
        assert "$payload" not in html and "wide-raw.png" in html
        with pytest.raises(ValueError, match="Output must be new"):
            run(ROOT, SOURCE, output)
