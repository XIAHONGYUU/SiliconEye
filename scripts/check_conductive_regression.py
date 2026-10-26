"""Replay frozen conductive evidence and run its existing failure-path tests.

Run from the repository: .venv/bin/python scripts/check_conductive_regression.py
    --output runs/NEW_DIR/result.json
Requires the project dev environment. This does not run an AI or score photographs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from silicon_eye.conductive_snapshot import assemble
from silicon_eye.conductive_workflow import prepare

ROOT = Path(__file__).resolve().parents[1]
SUITE = "benchmarks/conductive-regression-v1/suite.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_suite(root, suite):
    verified = set()

    def document(ref):
        path = (root / ref["path"]).resolve()
        require(path.is_relative_to(root), f"Outside project: {ref['path']}")
        require(sha(path) == ref["sha256"], f"Changed evidence: {ref['path']}")
        verified.add(ref["path"])
        return json.loads(path.read_text())

    task_ids = [task["id"] for task in suite["agent_tasks"]]
    require(len(task_ids) == len(set(task_ids)) == 3, "Expected three unique fixed tasks")
    expected = {}
    for task in suite["agent_tasks"]:
        packet = document(task["input_packet"])
        require(packet["task_id"] == task["id"], "Input task identity mismatch")
        for frame in packet["frames"].values():
            photo = (root / frame["photo"]["path"]).resolve()
            require(photo.is_relative_to(root), "Photo outside project")
            require(sha(photo) == frame["photo"]["sha256"], "Changed source photograph")
            verified.add(frame["photo"]["path"])
        document(task["human_truth"])
        require(task["physical_count_truth"] is None, "No new physical count truth")
        for row in task["expected_interfaces"]:
            require(row["id"] not in expected, "Duplicate interface in task truth")
            expected[row["id"]] = row
    for ref in suite["historical_evidence"]:
        document(ref)

    replay = []
    seen = set()
    for packet in suite["replay_packages"]:
        request = document(packet["request"])
        frozen = document(packet["model"])
        document(packet["manifest"])
        model, report, _, _, files = prepare(root, request)
        verified.update(files)
        require(model == frozen, f"Continuation changed frozen model: {packet['id']}")
        require(not model["pending_interface_ids"], "Reviewed task became pending")
        require(not model["net_edges"] and not model["complete_network"]
                and not model["geometry_adopted"]
                and not model["automatic_network_export_allowed"], "Scope expanded")
        quality = report["quality"]
        require(quality["execution_checks"] == "PASS", "Execution checks failed")
        require(quality["proxy_interface_ids"] == packet["expected_proxy_ids"],
                "Proxy qualification changed")
        counts = [len(v["candidate_cut_bounds"])
                  for layer in ("V1", "V2") for v in model["objects_by_layer"].get(layer, [])
                  if "candidate_cut_bounds" in v]
        require(counts == packet["expected_design_cut_counts"], "Design array changed")
        for row in quality["interface_geometry"]:
            require(row["human_cut_count"] is None, "Carrier review became count truth")
            if row["id"] in packet["expected_proxy_ids"]:
                require(row["full_group_design_enclosure"] == "NOT_EVALUATED",
                        "Support proxy became complete group")
        for connection in model["reviewed_local_connections"]:
            target = expected[connection["id"]]
            require(all(connection[key] == target[key] for key in
                        ("layer", "lower_metal_id", "upper_metal_id")), "Carrier truth changed")
            require(connection["physical_cut_count"] is None, "Physical count became known")
            seen.add(connection["id"])
        replay.append(dict(id=packet["id"], status="PASS", full_model_exact=True,
                           reviewed_interfaces=len(model["reviewed_local_connections"])))
    require(seen == set(expected), "Not all fixed task interfaces replayed")

    joint = suite["joint_snapshot"]
    joint_request = document(joint["request"])
    work, _, _, files = assemble(root, joint_request)
    verified.update(files)
    frozen_work = document(joint["snapshot"])
    # A continuation names a new run; every other field must remain identical.
    frozen_work["id"] = joint_request["id"]
    require(work == frozen_work, "Joint working snapshot changed beyond declared run ID")
    closeout = document(joint["closeout"])
    require(closeout["status"] == "CLOSED_SCOPED_WORKING_BASELINE", "Joint stage reopened")
    protection = document(suite["showcase_protection"])
    for name, digest in protection["files"].items():
        require(sha(root / name) == digest, f"Showcase changed: {name}")
    actual_site = {str(path.relative_to(root)) for path in (root / "site").rglob("*")
                   if path.is_file()}
    require(actual_site == {p for p in protection["files"] if p.startswith("site/")},
            "Showcase file inventory changed")
    pages = subprocess.check_output(
        ["git", "rev-parse", "gh-pages"], cwd=root, text=True
    ).strip()
    require(pages == protection["gh_pages_ref"], "Local gh-pages ref changed")
    return dict(replay=replay, joint_content_exact_except_declared_run_id=True,
                joint_closeout_preserved=True,
                checked_evidence_paths=len(verified),
                showcase_files_unchanged=len(protection["files"]),
                gh_pages_unchanged=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / "runs"):
        parser.error("Output must be a new JSON file under runs/")
    output.parent.mkdir(parents=True, exist_ok=True)
    suite = json.loads((ROOT / SUITE).read_text())
    result = dict(kind="conductive_engineering_regression_not_agent_run",
                  timestamp_utc=datetime.now(UTC).isoformat(),
                  suite=dict(path=SUITE, sha256=sha(ROOT / SUITE)),
                  git_head=subprocess.check_output(
                      ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  dirty_worktree=bool(subprocess.check_output(
                      ["git", "status", "--porcelain"], cwd=ROOT, text=True)),
                  qualification="LIMITED_TRIAL_V2", new_agent_run=False,
                  new_agent_accuracy=None, browser_interaction_tested=False)
    code_paths = {Path(__file__).resolve()}
    code_paths.update(Path(module.__file__).resolve() for module in list(sys.modules.values())
                      if getattr(module, "__file__", None)
                      and Path(module.__file__).resolve().is_relative_to(ROOT / "silicon_eye"))
    code_paths.update(ROOT / name for name in suite["software_tests"])
    code_paths.update((ROOT / "silicon_eye").glob("conductive*.html"))
    code_paths.update(ROOT / "skills" / name / "SKILL.md" for name in
                      ("silicon-eye-metal-reconstruction", "silicon-eye-via-reconstruction"))
    result["execution_file_hashes"] = {
        str(path.relative_to(ROOT)): sha(path) for path in sorted(code_paths)
    }
    try:
        result.update(check_suite(ROOT, suite))
        tests = subprocess.run([sys.executable, "-m", "pytest", "-q",
                                *suite["software_tests"]], cwd=ROOT,
                               text=True, capture_output=True, check=False)
        result["software_tests"] = dict(command=[sys.executable, "-m", "pytest", "-q",
                                                 *suite["software_tests"]],
                                        returncode=tests.returncode,
                                        output=tests.stdout + tests.stderr)
        require(tests.returncode == 0, "Software regression failed; see captured output")
        result["status"] = "PASS_SCOPED_ENGINEERING_REGRESSION"
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        result.update(status="FAIL", error=str(error))
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(status=result["status"], output=str(output)), ensure_ascii=False))
    return 0 if result["status"] != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
