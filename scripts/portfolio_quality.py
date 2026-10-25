"""Audit the frozen portfolio task catalog, not AI accuracy.

Run: python scripts/portfolio_quality.py [--check-site] [--root PATH]
Catalog audit uses SHA-bound historical records. Site-only checks need stdlib and
only the lightweight public bundle, making them suitable for sparse-checkout CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_catalog(root):
    suite = json.loads((root / "benchmarks/portfolio-quality-v1/suite.json").read_text())
    documents = {}
    for name, ref in suite["evidence"].items():
        path = (root / ref["path"]).resolve()
        if not path.is_relative_to(root.resolve()) or sha(path) != ref["sha256"]:
            raise ValueError(f"Evidence changed: {name}")
        if path.suffix == ".json":
            documents[name] = json.loads(path.read_text())
    ids = set()
    for case in suite["cases"]:
        if case["id"] in ids or case["split"] != "historical_development":
            raise ValueError("Duplicate case or unsupported split")
        ids.add(case["id"])
        for name in case["input_refs"] + case["reference_refs"]:
            if name not in suite["evidence"]:
                raise ValueError(f"Unknown case evidence: {name}")
        if case["mode"] == "agent_evaluation" and not case["input_refs"]:
            raise ValueError("Scored task needs an input packet")
    aa = documents["aa_acceptance"]["tasks"]
    poly, metal = documents["poly_eval"], documents["metal_eval"]
    references = [documents["roi2_reference"], documents["v3_reference"]]
    known = sum(label["reference_status"] == "known" for r in references for label in r["labels"])
    unresolved = sum(
        label["reference_status"] == "unresolved" for r in references for label in r["labels"]
    )
    if suite["held_out_task_count"] != 0 or suite["new_model_runs"] != 0:
        raise ValueError("New runs or holdouts need a separately reviewed result, not this audit")
    return dict(
        schema_version=1,
        kind="historical_evidence_audit_not_agent_run",
        source_baseline=suite["source_baseline"],
        evidence_files_verified=len(suite["evidence"]),
        catalog_tasks=len(suite["cases"]),
        tasks_with_existing_machine_scorer=sum(
            c["mode"] == "agent_evaluation" for c in suite["cases"]
        ),
        manual_rubric_tasks=sum(c["mode"] == "manual_rubric" for c in suite["cases"]),
        partial_reference_assertions=dict(known=known, unresolved=unresolved),
        aa_historical_acceptance=aa,
        aa_historical_accepted_tasks=sum(v.startswith("PASS_") for v in aa.values()),
        poly_count=dict(
            initial=poly["previous_AI_count"],
            human=poly["human_confirmed_count"],
            initial_error=poly["count_error"],
        ),
        metal_carrier=dict(
            initial=metal["initial_q1_carrier"],
            human=metal["corrected_q1_carrier"],
            observed_cuts=metal["human_observed_cut_count"],
            recorded_corrections=metal["actual_human_carrier_corrections"],
            exact_array_geometry_approved=metal["array_geometry_human_approved"],
        ),
        work_layer_objects={k: documents["stage"][k + "_count"] for k in ("AA", "POLY", "CT")},
        unresolved_scopes=len(documents["unknown"]["unknown_scopes"]),
        held_out_task_count=0,
        new_model_runs=0,
        new_model_accuracy=None,
        global_unknown_rate=None,
        aggregate_human_effort=None,
        cases=suite["cases"],
        evidence=suite["evidence"],
        limits=[
            "One chip, historical development tasks; not blind or cross-chip accuracy.",
            "Six unresolved scopes are regions, not six unknown objects.",
            "Post-correction output is not first-attempt correctness.",
            "AA method tasks and relation assertions have different units; no pooled accuracy.",
            "H07/H08 separate input packets and references; H01-H06 use manual rubrics.",
        ],
    )


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        self.targets += [v for k, v in attrs if k in {"href", "src"} and v]


def check_site(root):
    site = root / "site"
    manifest = json.loads((site / "provenance.json").read_text())
    for name, expected in manifest["artifacts"].items():
        if sha(site / name) != expected:
            raise ValueError(f"Stale public artifact: {name}")
    for path in site.rglob("*.svg"):
        ElementTree.parse(path)
    parser = Links()
    parser.feed((site / "index.html").read_text())
    for target in parser.targets:
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        resolved = (site / parsed.path).resolve()
        if not resolved.is_relative_to(site.resolve()) or not resolved.is_file():
            raise ValueError(f"Missing local site target: {target}")
    report = json.loads((site / "quality-report.json").read_text())
    if report["new_model_runs"] != 0 or report["new_model_accuracy"] is not None:
        raise ValueError("Historical audit must not advertise new model accuracy")
    if report["global_unknown_rate"] is not None:
        raise ValueError("Region/object denominators do not support an unknown rate")
    if report["held_out_task_count"] != 0:
        raise ValueError("No holdout results are supplied")
    return dict(
        status="PASS", asset_hashes=len(manifest["artifacts"]), local_targets=len(parser.targets)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check-site", action="store_true")
    args = parser.parse_args()
    result = check_site(args.root) if args.check_site else audit_catalog(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
